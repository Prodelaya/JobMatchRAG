from __future__ import annotations

from datetime import datetime

from jobmatchrag.source_ingestion.contracts import (
    FetchContext,
    FetchOutcome,
    PaginationSupport,
    RateLimitObservation,
    RateLimitSupport,
    SourceCapabilities,
    TimeWindowSupport,
)
from jobmatchrag.source_ingestion.models import FilterIntent, IngestionJob, RunStatus
from jobmatchrag.source_ingestion.orchestrator import IngestionGuardrails, IngestionOrchestrator


class TraceableFakeAdapter:
    source_key = "traceable-source"

    def __init__(self) -> None:
        self.capabilities = SourceCapabilities(
            pagination=PaginationSupport.CURSOR,
            time_windows=TimeWindowSupport.UPDATED_AT,
            supported_filters=frozenset({"keyword", "location"}),
            checkpoint_support=True,
            rate_limit_support=RateLimitSupport.EXPLICIT,
        )
        self.seen_contexts: list[FetchContext] = []

    def fetch(self, context: FetchContext) -> FetchOutcome:
        self.seen_contexts.append(context)
        return FetchOutcome(
            raw_items=({"id": "offer-1", "title": "Python Engineer"},),
            next_checkpoint="checkpoint-002",
            exhausted=False,
            rate_limit_observations=(
                RateLimitObservation(
                    observed_at=datetime(2026, 4, 14, 10, 0, 0),
                    scope="search",
                    retry_after_seconds=15,
                    remaining_quota=42,
                    notes="soft provider cooldown",
                ),
            ),
        )

    def classify_error(self, error: Exception):  # pragma: no cover - not used here
        raise AssertionError(f"unexpected error: {error}")


def test_job_run_raw_handoff_keeps_traceability_metadata() -> None:
    adapter = TraceableFakeAdapter()
    orchestrator = IngestionOrchestrator(
        guardrails=IngestionGuardrails(max_retries=2, max_fetch_calls=3, max_items=5)
    )
    job = IngestionJob(
        job_id="job-trace-1",
        source_key="traceable-source",
        filter_intent=FilterIntent(provider_filters={"keyword": "python", "location": "remote"}),
        requested_by="admin-ops",
        max_retries=2,
        max_fetch_calls=3,
        max_items=5,
    )

    result = orchestrator.execute_job(job, adapter)

    assert result.run.job_id == "job-trace-1"
    assert result.run.source_key == "traceable-source"
    assert result.run.status is RunStatus.PARTIAL
    assert result.run.capability_snapshot == adapter.capabilities
    assert result.run.filter_snapshot.provider_filters == {"keyword": "python", "location": "remote"}
    assert result.run.filter_snapshot.canonical_filters_note.startswith("Provider/source filters are advisory")
    assert result.run.counters.raw_items_seen == 1
    assert result.run.counters.raw_items_forwarded == 1
    assert result.run.checkpoint_out == "checkpoint-002"
    assert len(result.run.rate_limit_observations) == 1
    assert result.run.rate_limit_observations[0].remaining_quota == 42
    assert result.run.outcome_reason == "rate limit constrained execution"
    assert result.raw_handoff == ({"id": "offer-1", "title": "Python Engineer"},)
    assert len(adapter.seen_contexts) == 1
    assert adapter.seen_contexts[0].capability_snapshot == adapter.capabilities
    assert adapter.seen_contexts[0].requested_filters == {"keyword": "python", "location": "remote"}
    assert adapter.seen_contexts[0].remaining_fetch_budget == 3
    assert adapter.seen_contexts[0].remaining_item_budget == 5


def test_provider_filter_intent_is_not_treated_as_canonical_eligibility() -> None:
    adapter = TraceableFakeAdapter()
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=1, max_items=5))
    job = IngestionJob(
        job_id="job-filter-boundary-1",
        source_key="traceable-source",
        filter_intent=FilterIntent(provider_filters={"keyword": "python"}),
        checkpoint_in="checkpoint-001",
        max_fetch_calls=1,
        max_items=5,
    )

    result = orchestrator.execute_job(job, adapter)

    assert result.run.filter_snapshot.provider_filters == {"keyword": "python"}
    assert result.run.filter_snapshot.canonical_filters_note.endswith("internal eligibility remains canonical.")
    assert result.run.checkpoint_in == "checkpoint-001"
    assert result.raw_handoff == ({"id": "offer-1", "title": "Python Engineer"},)
    assert adapter.seen_contexts[0].checkpoint == "checkpoint-001"
