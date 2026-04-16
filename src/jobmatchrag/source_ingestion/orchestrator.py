from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from .contracts import ErrorCategory, ErrorClassification, FetchContext, ReferenceDatasetSnapshot, SourceAdapter
from .models import (
    CanonicalOfferSnapshot,
    CanonicalRunTrace,
    FilterIntent,
    IngestionJob,
    IngestionRun,
    RetryRecord,
    RunStatus,
    thaw_filter_value,
)
from .data_loader import load_curated_datasets
from .search_strategy import build_capture_profile, build_provider_execution_plan, evaluate_offer


@dataclass(frozen=True, slots=True)
class IngestionGuardrails:
    max_retries: int = 2
    max_fetch_calls: int = 10
    max_items: int | None = None

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.max_fetch_calls <= 0:
            raise ValueError("max_fetch_calls must be > 0")
        if self.max_items is not None and self.max_items <= 0:
            raise ValueError("max_items must be > 0")


@dataclass(frozen=True, slots=True)
class OrchestrationResult:
    run: IngestionRun
    raw_handoff: tuple[dict[str, object], ...]


class IngestionOrchestrator:
    """Shared job -> run execution without downstream domain concerns."""

    def __init__(self, guardrails: IngestionGuardrails | None = None) -> None:
        self._guardrails = guardrails or IngestionGuardrails()

    def execute_job(self, job: IngestionJob, adapter: SourceAdapter) -> OrchestrationResult:
        if job.source_key != adapter.source_key:
            raise ValueError(
                "job source_key does not match adapter source_key: "
                f"{job.source_key!r} != {adapter.source_key!r}"
            )

        checkpoint_enabled = adapter.capabilities.checkpoint_support
        profile = build_capture_profile()
        execution_plan = build_provider_execution_plan(
            profile=profile,
            provider_filters=thaw_filter_value(job.filter_intent.provider_filters),
            supported_filters=adapter.capabilities.supported_filters,
        )
        datasets = load_curated_datasets()
        run = IngestionRun(
            run_id=str(uuid4()),
            job_id=job.job_id,
            source_key=adapter.source_key,
            status=RunStatus.RUNNING,
            started_at=datetime.now(UTC),
            capability_snapshot=adapter.capabilities,
            filter_snapshot=self._snapshot_filter_intent(job),
            requested_by=job.requested_by,
            checkpoint_in=job.checkpoint_in if checkpoint_enabled else None,
            checkpoint_out=job.checkpoint_in if checkpoint_enabled else None,
            canonical_trace=CanonicalRunTrace(
                capture_profile_ref=profile.profile_id,
                execution_plan=execution_plan,
                dataset_snapshots=(
                    ReferenceDatasetSnapshot(
                        dataset_key="hybrid_cities",
                        dataset_version=datasets.hybrid_cities.dataset_version,
                    ),
                    ReferenceDatasetSnapshot(
                        dataset_key="known_consultancies",
                        dataset_version=datasets.known_consultancies.dataset_version,
                    ),
                ),
            ),
        )

        raw_handoff: list[dict[str, object]] = []
        checkpoint: str | None = job.checkpoint_in if checkpoint_enabled else None
        exhausted = False
        max_fetch_calls = self._resolve_max_fetch_calls(job)

        while run.counters.fetch_calls < max_fetch_calls:
            if self._item_limit_reached(job, run):
                run.complete(RunStatus.PARTIAL if raw_handoff else RunStatus.FAILED, "bounded run scope reached")
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

            context = FetchContext(
                job_id=job.job_id,
                run_id=run.run_id,
                source_key=adapter.source_key,
                capability_snapshot=adapter.capabilities,
                requested_filters=thaw_filter_value(execution_plan.derived_provider_params),
                requested_window_start=job.window_start,
                requested_window_end=job.window_end,
                checkpoint=checkpoint,
                retry_count=run.retry_count,
                remaining_fetch_budget=max_fetch_calls - run.counters.fetch_calls,
                remaining_item_budget=self._remaining_item_budget(job, run),
            )

            try:
                run.counters.fetch_calls += 1
                outcome = adapter.fetch(context)
            except Exception as error:  # pragma: no cover - adapter translation point
                classification = self._classify_error(adapter, error)
                run.error_summary = classification
                if classification.retryable and run.retry_count < self._resolve_max_retries(job):
                    run.retry_count += 1
                    run.retry_history.append(
                        RetryRecord(
                            attempt=run.retry_count,
                            classification=classification,
                            observed_at=datetime.now(UTC),
                        )
                    )
                    continue

                final_status = RunStatus.PARTIAL if raw_handoff else RunStatus.FAILED
                reason = "retry budget exhausted" if classification.retryable else "terminal adapter error"
                run.complete(final_status, reason)
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

            remaining_item_budget = self._remaining_item_budget(job, run)
            evaluated_items: list[dict[str, object]] = []
            for raw_item in outcome.raw_items:
                evaluation = evaluate_offer(raw_item, profile=profile, datasets=datasets)
                trace = run.canonical_trace
                trace_index = len(trace.offer_outcomes) if trace is not None else 0
                offer_id = str(raw_item.get("id") or raw_item.get("source_offer_id") or trace_index)
                if trace is not None:
                    trace.offer_outcomes.append(
                        CanonicalOfferSnapshot(
                            source_offer_id=offer_id,
                            decision=evaluation.decision,
                            outcomes=evaluation.outcomes,
                        )
                    )
                if evaluation.decision != "excluded":
                    evaluated_items.append(raw_item)

            forwarded_items = tuple(evaluated_items)
            budget_truncated = False
            if remaining_item_budget is not None:
                budget_truncated = len(forwarded_items) > remaining_item_budget
                forwarded_items = forwarded_items[:remaining_item_budget]

            raw_handoff.extend(forwarded_items)
            run.counters.raw_items_seen += len(outcome.raw_items)
            run.counters.raw_items_forwarded = len(raw_handoff)
            run.rate_limit_observations.extend(outcome.rate_limit_observations)
            exhausted = outcome.exhausted

            if checkpoint_enabled and not budget_truncated:
                run.checkpoint_out = outcome.next_checkpoint
                checkpoint = outcome.next_checkpoint

            if budget_truncated or self._item_limit_reached(job, run):
                run.complete(RunStatus.PARTIAL, "bounded run scope reached")
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

            if outcome.error_summary is not None:
                run.error_summary = outcome.error_summary
                if outcome.error_summary.retryable and run.retry_count < self._resolve_max_retries(job):
                    run.retry_count += 1
                    run.retry_history.append(
                        RetryRecord(
                            attempt=run.retry_count,
                            classification=outcome.error_summary,
                            observed_at=datetime.now(UTC),
                        )
                    )
                    continue

                reason = "retry budget exhausted" if outcome.error_summary.retryable else "terminal adapter error"
                run.complete(RunStatus.PARTIAL if raw_handoff else RunStatus.FAILED, reason)
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

            if outcome.rate_limit_observations and not exhausted:
                run.complete(RunStatus.PARTIAL if raw_handoff else RunStatus.FAILED, "rate limit constrained execution")
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

            if exhausted:
                run.complete(RunStatus.COMPLETED, "source exhausted")
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

        run.complete(RunStatus.PARTIAL if raw_handoff else RunStatus.FAILED, "fetch guardrail exhausted")
        return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

    def _resolve_max_retries(self, job: IngestionJob) -> int:
        return min(job.max_retries, self._guardrails.max_retries)

    def _resolve_max_fetch_calls(self, job: IngestionJob) -> int:
        return min(job.max_fetch_calls, self._guardrails.max_fetch_calls)

    def _resolve_max_items(self, job: IngestionJob) -> int | None:
        if job.max_items is None:
            return self._guardrails.max_items
        if self._guardrails.max_items is None:
            return job.max_items
        return min(job.max_items, self._guardrails.max_items)

    def _remaining_item_budget(self, job: IngestionJob, run: IngestionRun) -> int | None:
        max_items = self._resolve_max_items(job)
        if max_items is None:
            return None
        return max(max_items - run.counters.raw_items_forwarded, 0)

    def _item_limit_reached(self, job: IngestionJob, run: IngestionRun) -> bool:
        max_items = self._resolve_max_items(job)
        if max_items is None:
            return False
        return run.counters.raw_items_forwarded >= max_items

    def _snapshot_filter_intent(self, job: IngestionJob) -> FilterIntent:
        return job.filter_intent.__class__(
            provider_filters=job.filter_intent.provider_filters,
            canonical_filters_note=job.filter_intent.canonical_filters_note,
        )

    def _classify_error(self, adapter: SourceAdapter, error: Exception) -> ErrorClassification:
        try:
            return adapter.classify_error(error)
        except Exception as classification_error:  # pragma: no cover - defensive fallback
            return ErrorClassification(
                category=ErrorCategory.UNKNOWN,
                retryable=False,
                message=str(error),
                details={
                    "original_error_type": type(error).__name__,
                    "classification_error_type": type(classification_error).__name__,
                    "classification_error_message": str(classification_error),
                },
            )
