from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .contracts import (
    CanonicalLanguage,
    ErrorCategory,
    ErrorClassification,
    FetchContext,
    ProviderRequestPlanIdentity,
    RateLimitObservation,
    ReferenceDatasetSnapshot,
    SourceAdapter,
)
from .infojobs.mapping import map_canonical_handoff_to_provider_execution_plan
from .models import (
    CanonicalOfferSnapshot,
    CanonicalRunTrace,
    FilterIntent,
    IngestionJob,
    IngestionRun,
    ProviderQueryExecutionTrace,
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


@dataclass(frozen=True, slots=True)
class _ExecutionCursor:
    family_plan_index: int = 0
    adapter_checkpoint: str | None = None


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
        provider_filters = thaw_filter_value(job.filter_intent.provider_filters)
        if adapter.source_key == "infojobs":
            execution_plan = map_canonical_handoff_to_provider_execution_plan(
                profile,
                provider_filters=provider_filters,
                supported_filters=adapter.capabilities.supported_filters,
            )
        else:
            execution_plan = build_provider_execution_plan(
                profile=profile,
                provider_filters=provider_filters,
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
                canonical_handoff=profile,
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
        try:
            cursor = self._decode_execution_cursor(
                job.checkpoint_in if checkpoint_enabled else None,
                source_key=adapter.source_key,
                execution_plan=execution_plan,
            )
        except ValueError as error:
            run.error_summary = self._structured_checkpoint_error(
                source_key=adapter.source_key,
                error=error,
                checkpoint=job.checkpoint_in,
            )
            run.complete(RunStatus.FAILED, "terminal adapter error")
            return OrchestrationResult(run=run, raw_handoff=())
        exhausted = False
        max_fetch_calls = self._resolve_max_fetch_calls(job)
        forwarded_offer_ids: set[str] = set()

        while run.counters.fetch_calls < max_fetch_calls:
            if self._item_limit_reached(job, run):
                run.complete(RunStatus.PARTIAL if raw_handoff else RunStatus.FAILED, "bounded run scope reached")
                return OrchestrationResult(run=run, raw_handoff=tuple(raw_handoff))

            context = FetchContext(
                job_id=job.job_id,
                run_id=run.run_id,
                source_key=adapter.source_key,
                capability_snapshot=adapter.capabilities,
                requested_filters=self._requested_filters_for_cursor(execution_plan, cursor),
                requested_window_start=job.window_start,
                requested_window_end=job.window_end,
                checkpoint=cursor.adapter_checkpoint,
                retry_count=run.retry_count,
                remaining_fetch_budget=max_fetch_calls - run.counters.fetch_calls,
                remaining_item_budget=self._remaining_item_budget(job, run),
            )
            query_checkpoint_in = context.checkpoint
            query_requested_filters = dict(context.requested_filters)
            query_plan = self._request_plan_for_cursor(execution_plan, cursor)

            try:
                run.counters.fetch_calls += 1
                outcome = adapter.fetch(context)
            except Exception as error:  # pragma: no cover - adapter translation point
                classification = self._classify_error(adapter, error)
                run.error_summary = classification
                self._append_query_trace(
                    run,
                    requested_filters=query_requested_filters,
                    checkpoint_in=query_checkpoint_in,
                    checkpoint_out=None,
                    raw_items=(),
                    forwarded_items=(),
                    deduplicated_offer_ids=(),
                    request_plan=query_plan,
                    exhausted=False,
                    rate_limit_observations=(),
                    error_summary=classification,
                )
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
            deduplicated_offer_ids: list[str] = []
            for raw_item in outcome.raw_items:
                evaluation = evaluate_offer(raw_item, profile=profile, datasets=datasets)
                trace = run.canonical_trace
                trace_index = len(trace.offer_outcomes) if trace is not None else 0
                offer_id = self._source_offer_id(raw_item, default=trace_index)
                if trace is not None:
                    trace.offer_outcomes.append(
                        CanonicalOfferSnapshot(
                            source_offer_id=offer_id,
                            decision=evaluation.decision,
                            outcomes=evaluation.outcomes,
                        )
                    )
                if evaluation.decision != "excluded":
                    if offer_id in forwarded_offer_ids:
                        deduplicated_offer_ids.append(offer_id)
                        continue
                    forwarded_offer_ids.add(offer_id)
                    self._attach_request_plan_trace(raw_item, query_plan)
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
            checkpoint_out = outcome.next_checkpoint

            if checkpoint_enabled and not budget_truncated:
                cursor = _ExecutionCursor(
                    family_plan_index=cursor.family_plan_index,
                    adapter_checkpoint=outcome.next_checkpoint,
                )
                run.checkpoint_out = self._encode_execution_cursor(
                    cursor,
                    source_key=adapter.source_key,
                    execution_plan=execution_plan,
                )
                checkpoint_out = run.checkpoint_out

            self._append_query_trace(
                run,
                requested_filters=query_requested_filters,
                checkpoint_in=query_checkpoint_in,
                checkpoint_out=checkpoint_out,
                raw_items=outcome.raw_items,
                forwarded_items=forwarded_items,
                deduplicated_offer_ids=tuple(deduplicated_offer_ids),
                request_plan=query_plan,
                exhausted=outcome.exhausted,
                rate_limit_observations=outcome.rate_limit_observations,
                error_summary=outcome.error_summary,
            )

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
                if self._has_more_family_plans(execution_plan, cursor):
                    cursor = _ExecutionCursor(family_plan_index=cursor.family_plan_index + 1)
                    if checkpoint_enabled:
                        run.checkpoint_out = self._encode_execution_cursor(
                            cursor,
                            source_key=adapter.source_key,
                            execution_plan=execution_plan,
                        )
                    continue
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

    def _requested_filters_for_cursor(
        self,
        execution_plan: object,
        cursor: _ExecutionCursor,
    ) -> dict[str, object]:
        family_plans = getattr(execution_plan, "family_plans", ())
        if family_plans:
            return thaw_filter_value(family_plans[cursor.family_plan_index].provider_params)
        return thaw_filter_value(getattr(execution_plan, "derived_provider_params", {}))

    def _has_more_family_plans(self, execution_plan: object, cursor: _ExecutionCursor) -> bool:
        family_plans = getattr(execution_plan, "family_plans", ())
        return bool(family_plans) and cursor.family_plan_index + 1 < len(family_plans)

    def _request_plan_for_cursor(
        self,
        execution_plan: object,
        cursor: _ExecutionCursor,
    ) -> ProviderRequestPlanIdentity | None:
        family_plans = getattr(execution_plan, "family_plans", ())
        if not family_plans:
            return None
        family_plan = family_plans[cursor.family_plan_index]
        return ProviderRequestPlanIdentity(
            family_key=family_plan.family_key,
            language=CanonicalLanguage(family_plan.language),
            query_label=family_plan.query_label,
        )

    def _append_query_trace(
        self,
        run: IngestionRun,
        *,
        requested_filters: dict[str, object],
        checkpoint_in: str | None,
        checkpoint_out: str | None,
        raw_items: tuple[dict[str, Any], ...],
        forwarded_items: tuple[dict[str, object], ...],
        deduplicated_offer_ids: tuple[str, ...],
        request_plan: ProviderRequestPlanIdentity | None,
        exhausted: bool,
        rate_limit_observations: tuple[RateLimitObservation, ...],
        error_summary: ErrorClassification | None,
    ) -> None:
        if run.canonical_trace is None:
            return
        run.canonical_trace.query_executions.append(
            ProviderQueryExecutionTrace(
                requested_filters=requested_filters,
                checkpoint_in=checkpoint_in,
                checkpoint_out=checkpoint_out,
                raw_offer_ids=tuple(self._source_offer_id(item, default=index) for index, item in enumerate(raw_items)),
                forwarded_offer_ids=tuple(
                    self._source_offer_id(item, default=index) for index, item in enumerate(forwarded_items)
                ),
                deduplicated_offer_ids=deduplicated_offer_ids,
                request_plan=request_plan,
                exhausted=exhausted,
                rate_limit_observations=tuple(rate_limit_observations),
                error_summary=error_summary,
            )
        )

    def _source_offer_id(self, raw_item: dict[str, object], *, default: int) -> str:
        return str(raw_item.get("source_offer_id") or raw_item.get("id") or default)

    def _attach_request_plan_trace(
        self,
        raw_item: dict[str, object],
        request_plan: ProviderRequestPlanIdentity | None,
    ) -> None:
        trace = raw_item.get("trace")
        if not isinstance(trace, dict):
            return
        trace["request_plan"] = (
            {
                "family_key": request_plan.family_key,
                "language": request_plan.language.value,
                "query_label": request_plan.query_label,
            }
            if request_plan is not None
            else None
        )

    def _structured_checkpoint_error(
        self,
        *,
        source_key: str,
        error: ValueError,
        checkpoint: str | None,
    ) -> ErrorClassification:
        return ErrorClassification(
            category=ErrorCategory.CONFIGURATION,
            retryable=False,
            message=str(error),
            details={
                "provider": source_key,
                "endpoint": "checkpoint",
                "failure_kind": "checkpoint",
                "raw_body": checkpoint,
            },
        )

    def _decode_execution_cursor(
        self,
        checkpoint: str | None,
        *,
        source_key: str,
        execution_plan: object,
    ) -> _ExecutionCursor:
        if checkpoint is None:
            return _ExecutionCursor()

        family_plans = getattr(execution_plan, "family_plans", ())
        if source_key != "infojobs" or not family_plans:
            return _ExecutionCursor(adapter_checkpoint=checkpoint)

        try:
            payload = json.loads(checkpoint)
        except json.JSONDecodeError:
            return _ExecutionCursor(adapter_checkpoint=checkpoint)

        if payload.get("orchestrator") != "source_ingestion.execution_plan":
            return _ExecutionCursor(adapter_checkpoint=checkpoint)

        family_plan_index = payload.get("family_plan_index")
        adapter_checkpoint = payload.get("adapter_checkpoint")
        if not isinstance(family_plan_index, int) or isinstance(family_plan_index, bool):
            raise ValueError("execution-plan checkpoint family_plan_index must be an integer")
        if family_plan_index < 0 or family_plan_index >= len(family_plans):
            raise ValueError("execution-plan checkpoint family_plan_index is out of range")
        if adapter_checkpoint is not None and not isinstance(adapter_checkpoint, str):
            raise ValueError("execution-plan checkpoint adapter_checkpoint must be a string or null")

        return _ExecutionCursor(
            family_plan_index=family_plan_index,
            adapter_checkpoint=adapter_checkpoint,
        )

    def _encode_execution_cursor(
        self,
        cursor: _ExecutionCursor,
        *,
        source_key: str,
        execution_plan: object,
    ) -> str | None:
        family_plans = getattr(execution_plan, "family_plans", ())
        if source_key != "infojobs" or not family_plans:
            return cursor.adapter_checkpoint
        if cursor.family_plan_index == 0:
            return cursor.adapter_checkpoint
        return json.dumps(
            {
                "adapter_checkpoint": cursor.adapter_checkpoint,
                "family_plan_index": cursor.family_plan_index,
                "orchestrator": "source_ingestion.execution_plan",
            },
            sort_keys=True,
        )
