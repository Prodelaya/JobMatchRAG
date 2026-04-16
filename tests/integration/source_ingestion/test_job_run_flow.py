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


class CanonicalBoundaryAdapter(TraceableFakeAdapter):
    def __init__(self, raw_items: tuple[dict[str, object], ...]) -> None:
        super().__init__()
        self._raw_items = raw_items

    def fetch(self, context: FetchContext) -> FetchOutcome:
        self.seen_contexts.append(context)
        return FetchOutcome(raw_items=self._raw_items, next_checkpoint="checkpoint-003", exhausted=True)


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


def test_run_filter_snapshot_is_detached_from_later_caller_mutation() -> None:
    adapter = TraceableFakeAdapter()
    orchestrator = IngestionOrchestrator()
    provider_filters = {"keyword": "python", "meta": {"location": "remote"}}
    job = IngestionJob(
        job_id="job-filter-snapshot-1",
        source_key="traceable-source",
        filter_intent=FilterIntent(provider_filters=provider_filters),
    )

    result = orchestrator.execute_job(job, adapter)
    provider_filters["keyword"] = "golang"
    provider_filters["meta"]["location"] = "onsite"

    assert result.run.filter_snapshot.provider_filters == {
        "keyword": "python",
        "meta": {"location": "remote"},
    }


def test_seeded_city_hybrid_and_known_company_ambiguity_survive_before_downstream_handoff() -> None:
    adapter = CanonicalBoundaryAdapter(
        raw_items=(
            {
                "id": "offer-seeded-city",
                "title": "Automation Engineer",
                "modality": "hybrid",
                "city": "Barcelona",
                "country": "Spain",
                "attendance_days_per_month": 2,
            },
            {
                "id": "offer-known-company",
                "title": "Internal Automation Engineer",
                "description": "Plataforma interna para operaciones.",
                "company": "Accenture",
                "modality": "remote",
                "country": "Spain",
            },
        )
    )

    result = IngestionOrchestrator().execute_job(
        IngestionJob(job_id="job-canonical-1", source_key="traceable-source"),
        adapter,
    )

    assert [item["id"] for item in result.raw_handoff] == ["offer-seeded-city", "offer-known-company"]
    assert result.run.canonical_trace is not None
    assert result.run.canonical_trace.dataset_snapshots[0].dataset_version == "2026.04.1"
    assert [snapshot.decision for snapshot in result.run.canonical_trace.offer_outcomes] == ["passed", "ambiguous"]


def test_explicit_consultancy_exclusion_happens_before_later_handoff() -> None:
    adapter = CanonicalBoundaryAdapter(
        raw_items=(
            {
                "id": "offer-explicit-consultancy",
                "title": "Consultor IA",
                "description": "Consultora para proyectos de clientes y staffing.",
                "company": "Delivery Partner",
                "modality": "remote",
                "country": "Spain",
            },
            {
                "id": "offer-survivor",
                "title": "Automation Engineer",
                "modality": "remote",
                "country": "Spain",
            },
        )
    )

    result = IngestionOrchestrator().execute_job(
        IngestionJob(job_id="job-canonical-2", source_key="traceable-source"),
        adapter,
    )

    assert [item["id"] for item in result.raw_handoff] == ["offer-survivor"]
    assert result.run.counters.raw_items_seen == 2
    assert result.run.counters.raw_items_forwarded == 1
    assert [snapshot.decision for snapshot in result.run.canonical_trace.offer_outcomes] == ["excluded", "passed"]


def test_ai_preference_remains_downstream_ranking_only_behavior() -> None:
    adapter = CanonicalBoundaryAdapter(
        raw_items=(
            {
                "id": "offer-ai",
                "title": "AI Automation Engineer",
                "description": "Internal platform automation with LLM tooling.",
                "modality": "remote",
                "country": "Spain",
            },
            {
                "id": "offer-no-ai",
                "title": "Automation Engineer",
                "description": "Internal platform automation for operations.",
                "modality": "remote",
                "country": "Spain",
            },
        )
    )

    result = IngestionOrchestrator().execute_job(
        IngestionJob(job_id="job-canonical-3", source_key="traceable-source"),
        adapter,
    )

    assert [item["id"] for item in result.raw_handoff] == ["offer-ai", "offer-no-ai"]
    assert [snapshot.decision for snapshot in result.run.canonical_trace.offer_outcomes] == ["passed", "passed"]


def test_framework_excludes_ineligible_item_when_provider_filters_miss_it() -> None:
    adapter = CanonicalBoundaryAdapter(
        raw_items=(
            {
                "id": "offer-senior",
                "title": "Senior Automation Engineer",
                "description": "Internal platform automation role.",
                "modality": "remote",
                "country": "Spain",
            },
            {
                "id": "offer-stale",
                "title": "Automation Engineer",
                "description": "Internal platform automation role.",
                "modality": "remote",
                "country": "Spain",
                "published_at": "2026-03-20T10:00:00+00:00",
                "evaluated_at": "2026-04-16T10:00:00+00:00",
            },
            {
                "id": "offer-survivor",
                "title": "Automation Engineer",
                "description": "Internal platform automation role.",
                "modality": "remote",
                "country": "Spain",
                "published_at": "2026-04-12T10:00:00+00:00",
                "evaluated_at": "2026-04-16T10:00:00+00:00",
            },
        )
    )

    result = IngestionOrchestrator().execute_job(
        IngestionJob(
            job_id="job-canonical-4",
            source_key="traceable-source",
            filter_intent=FilterIntent(provider_filters={"keyword": "automation", "sinceDate": "_15_DAYS"}),
        ),
        adapter,
    )

    assert [item["id"] for item in result.raw_handoff] == ["offer-survivor"]
    assert [snapshot.decision for snapshot in result.run.canonical_trace.offer_outcomes] == [
        "excluded",
        "excluded",
        "passed",
    ]


def test_exclusion_only_page_still_advances_checkpoint_without_bounded_partial() -> None:
    adapter = CanonicalBoundaryAdapter(
        raw_items=(
            {
                "id": "offer-excluded",
                "title": "Senior Automation Engineer",
                "description": "Internal platform automation role.",
                "modality": "remote",
                "country": "Spain",
            },
        )
    )

    result = IngestionOrchestrator().execute_job(
        IngestionJob(job_id="job-canonical-5", source_key="traceable-source", checkpoint_in="checkpoint-001"),
        adapter,
    )

    assert result.run.status is RunStatus.COMPLETED
    assert result.run.outcome_reason == "source exhausted"
    assert result.run.checkpoint_out == "checkpoint-003"
    assert result.run.counters.raw_items_seen == 1
    assert result.run.counters.raw_items_forwarded == 0
    assert result.raw_handoff == ()
