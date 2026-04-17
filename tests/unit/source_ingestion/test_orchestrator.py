from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import pytest

from jobmatchrag.source_ingestion.contracts import (
    ErrorCategory,
    ErrorClassification,
    FetchContext,
    FetchOutcome,
    PaginationSupport,
    ProjectionTrustLevel,
    RateLimitObservation,
    RateLimitSupport,
    SourceCapabilities,
    TimeWindowSupport,
)
from jobmatchrag.source_ingestion.models import FilterIntent, IngestionJob, RunStatus
from jobmatchrag.source_ingestion.orchestrator import IngestionGuardrails, IngestionOrchestrator


class FakeAdapter:
    source_key = "fake-source"

    def __init__(
        self,
        responses: Sequence[FetchOutcome | Exception],
        *,
        checkpoint_support: bool = True,
    ) -> None:
        self.capabilities = SourceCapabilities(
            pagination=PaginationSupport.CURSOR,
            time_windows=TimeWindowSupport.UPDATED_AT,
            supported_filters=frozenset({"keyword"}),
            checkpoint_support=checkpoint_support,
            rate_limit_support=RateLimitSupport.EXPLICIT,
        )
        self._responses = list(responses)
        self.contexts: list[FetchContext] = []

    def fetch(self, context: FetchContext) -> FetchOutcome:
        self.contexts.append(context)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def classify_error(self, error: Exception) -> ErrorClassification:
        if isinstance(error, TimeoutError):
            return ErrorClassification(
                category=ErrorCategory.NETWORK,
                retryable=True,
                message=str(error),
            )
        return ErrorClassification(
            category=ErrorCategory.CONFIGURATION,
            retryable=False,
            message=str(error),
        )


class MutatingAdapter(FakeAdapter):
    def fetch(self, context: FetchContext) -> FetchOutcome:
        context.requested_filters["keyword"] = "golang"
        nested = context.requested_filters.get("meta")
        if isinstance(nested, dict):
            nested["location"] = "onsite"
        return super().fetch(context)


class BrokenClassifierAdapter(FakeAdapter):
    def classify_error(self, error: Exception) -> ErrorClassification:
        raise RuntimeError("classifier exploded")


class InfoJobsLikeAdapter(FakeAdapter):
    source_key = "infojobs"

    def __init__(self, responses: Sequence[FetchOutcome | Exception]) -> None:
        super().__init__(responses)
        self.capabilities = SourceCapabilities(
            pagination=PaginationSupport.PAGE_NUMBER,
            time_windows=TimeWindowSupport.NONE,
            supported_filters=frozenset({"q", "experienceMin", "sinceDate", "teleworking", "category"}),
            checkpoint_support=True,
            rate_limit_support=RateLimitSupport.EXPLICIT,
        )


def build_job(**overrides: object) -> IngestionJob:
    defaults: dict[str, object] = {
        "job_id": "job-1",
        "source_key": "fake-source",
        "filter_intent": FilterIntent(provider_filters={"keyword": "python"}),
        "requested_by": "scheduler",
        "max_retries": 2,
        "max_fetch_calls": 5,
        "max_items": None,
    }
    defaults.update(overrides)
    return IngestionJob(**defaults)


def test_retries_only_retryable_errors_and_completes_after_recovery() -> None:
    adapter = FakeAdapter(
        responses=[
            TimeoutError("temporary timeout"),
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-1", exhausted=True),
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_retries=2, max_fetch_calls=3))

    result = orchestrator.execute_job(build_job(), adapter)

    assert result.run.status is RunStatus.COMPLETED
    assert result.run.retry_count == 1
    assert len(result.run.retry_history) == 1
    assert result.run.retry_history[0].classification.category is ErrorCategory.NETWORK
    assert result.run.counters.raw_items_forwarded == 1
    assert result.run.checkpoint_out == "cp-1"
    assert result.raw_handoff == ({"id": "1"},)
    assert len(adapter.contexts) == 2


def test_non_retryable_failure_stays_failed_without_retry() -> None:
    adapter = FakeAdapter(responses=[ValueError("invalid credentials")])
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(), adapter)

    assert result.run.status is RunStatus.FAILED
    assert result.run.retry_count == 0
    assert result.run.error_summary is not None
    assert result.run.error_summary.category is ErrorCategory.CONFIGURATION
    assert result.run.outcome_reason == "terminal adapter error"
    assert result.raw_handoff == ()


def test_fetch_guardrail_closes_partial_when_some_material_was_captured() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-1", exhausted=False),
            FetchOutcome(raw_items=({"id": "2"},), next_checkpoint="cp-2", exhausted=False),
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=2))

    result = orchestrator.execute_job(build_job(max_fetch_calls=4), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert result.run.counters.fetch_calls == 2
    assert result.run.counters.raw_items_forwarded == 2
    assert result.run.checkpoint_out == "cp-2"


def test_item_budget_truncates_forwarded_material_to_the_allowed_limit() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "1"}, {"id": "2"}, {"id": "3"}),
                next_checkpoint="cp-1",
                exhausted=False,
            ),
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_items=5))

    result = orchestrator.execute_job(build_job(max_items=1, checkpoint_in="cp-previous"), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "bounded run scope reached"
    assert result.run.counters.fetch_calls == 1
    assert result.run.counters.raw_items_seen == 3
    assert result.run.counters.raw_items_forwarded == 1
    assert result.run.checkpoint_in == "cp-previous"
    assert result.run.checkpoint_out == "cp-previous"
    assert result.raw_handoff == ({"id": "1"},)


def test_retryable_exceptions_consume_fetch_budget() -> None:
    adapter = FakeAdapter(
        responses=[
            TimeoutError("temporary timeout"),
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-1", exhausted=True),
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_retries=2, max_fetch_calls=1))

    result = orchestrator.execute_job(build_job(max_retries=2, max_fetch_calls=3), adapter)

    assert result.run.status is RunStatus.FAILED
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert result.run.retry_count == 1
    assert result.run.counters.fetch_calls == 1
    assert result.raw_handoff == ()
    assert len(adapter.contexts) == 1


def test_rate_limit_observation_can_close_partial_run() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-1", exhausted=False),
            FetchOutcome(
                raw_items=(),
                next_checkpoint="cp-1",
                exhausted=False,
                rate_limit_observations=(
                    RateLimitObservation(
                        observed_at=datetime(2026, 4, 14, 12, 0, 0),
                        scope="search",
                        retry_after_seconds=60,
                        remaining_quota=0,
                    ),
                ),
            ),
        ]
    )
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "rate limit constrained execution"
    assert len(result.run.rate_limit_observations) == 1
    assert result.run.rate_limit_observations[0].retry_after_seconds == 60


def test_partial_fetch_outcome_can_surface_terminal_error_summary() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "1"},),
                next_checkpoint="cp-1",
                exhausted=False,
                error_summary=ErrorClassification(
                    category=ErrorCategory.AUTHENTICATION,
                    retryable=False,
                    message="invalid credentials",
                    details={"provider": "infojobs", "endpoint": "GET /offer/{offerId}"},
                ),
            )
        ]
    )
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "terminal adapter error"
    assert result.run.error_summary is not None
    assert result.run.error_summary.category is ErrorCategory.AUTHENTICATION
    assert result.run.error_summary.retryable is False
    assert result.run.checkpoint_out == "cp-1"
    assert result.raw_handoff == ({"id": "1"},)


def test_retryable_error_summary_respects_retry_budget_and_keeps_progress() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "1"},),
                next_checkpoint="cp-1",
                exhausted=False,
                error_summary=ErrorClassification(
                    category=ErrorCategory.NETWORK,
                    retryable=True,
                    message="temporary detail failure",
                ),
            ),
            FetchOutcome(raw_items=({"id": "2"},), next_checkpoint="cp-2", exhausted=True),
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_retries=2, max_fetch_calls=3))

    result = orchestrator.execute_job(build_job(checkpoint_in="cp-previous"), adapter)

    assert result.run.status is RunStatus.COMPLETED
    assert result.run.retry_count == 1
    assert len(result.run.retry_history) == 1
    assert result.run.retry_history[0].classification.retryable is True
    assert result.run.error_summary is not None
    assert result.run.error_summary.message == "temporary detail failure"
    assert result.run.checkpoint_in == "cp-previous"
    assert result.run.checkpoint_out == "cp-2"
    assert result.raw_handoff == ({"id": "1"}, {"id": "2"})
    assert [context.checkpoint for context in adapter.contexts] == ["cp-previous", "cp-1"]


def test_retryable_error_summary_closes_run_when_retry_budget_is_exhausted() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "1"},),
                next_checkpoint="cp-1",
                exhausted=False,
                error_summary=ErrorClassification(
                    category=ErrorCategory.NETWORK,
                    retryable=True,
                    message="temporary detail failure",
                ),
            )
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_retries=0))

    result = orchestrator.execute_job(build_job(max_retries=0, checkpoint_in="cp-previous"), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "retry budget exhausted"
    assert result.run.retry_count == 0
    assert result.run.error_summary is not None
    assert result.run.error_summary.retryable is True
    assert result.run.checkpoint_in == "cp-previous"
    assert result.run.checkpoint_out == "cp-1"
    assert result.raw_handoff == ({"id": "1"},)


def test_repeated_job_execution_creates_distinct_runs() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-1", exhausted=True),
            FetchOutcome(raw_items=({"id": "2"},), next_checkpoint="cp-2", exhausted=True),
        ]
    )
    orchestrator = IngestionOrchestrator()
    job = build_job()

    first = orchestrator.execute_job(job, adapter)
    second = orchestrator.execute_job(job, adapter)

    assert first.run.run_id != second.run.run_id
    assert first.run.status is RunStatus.COMPLETED
    assert second.run.status is RunStatus.COMPLETED
    assert first.run.counters.raw_items_forwarded == 1
    assert second.run.counters.raw_items_forwarded == 1


def test_job_item_budget_is_shared_with_context() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "1"}, {"id": "2"}), next_checkpoint="cp-1", exhausted=False),
        ]
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_items=2))

    result = orchestrator.execute_job(build_job(max_items=3), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert adapter.contexts[0].remaining_item_budget == 2
    assert result.run.checkpoint_out == "cp-1"
    assert result.run.outcome_reason == "bounded run scope reached"


def test_job_checkpoint_is_seeded_into_run_and_fetch_context() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-2", exhausted=True),
        ]
    )
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(checkpoint_in="cp-1"), adapter)

    assert result.run.checkpoint_in == "cp-1"
    assert result.run.checkpoint_out == "cp-2"
    assert adapter.contexts[0].checkpoint == "cp-1"


def test_checkpoint_state_is_ignored_when_adapter_does_not_support_it() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "1"},), next_checkpoint="cp-2", exhausted=True),
        ],
        checkpoint_support=False,
    )
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(checkpoint_in="cp-1"), adapter)

    assert result.run.checkpoint_in is None
    assert result.run.checkpoint_out is None
    assert adapter.contexts[0].checkpoint is None


def test_retryable_failure_becomes_failed_when_retry_budget_is_zero() -> None:
    adapter = FakeAdapter(responses=[TimeoutError("temporary timeout")])
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_retries=0))

    result = orchestrator.execute_job(build_job(max_retries=0), adapter)

    assert result.run.status is RunStatus.FAILED
    assert result.run.outcome_reason == "retry budget exhausted"
    assert result.run.retry_count == 0


def test_classification_failure_falls_back_to_structured_terminal_error() -> None:
    adapter = BrokenClassifierAdapter(responses=[RuntimeError("boom")])
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(), adapter)

    assert result.run.status is RunStatus.FAILED
    assert result.run.outcome_reason == "terminal adapter error"
    assert result.run.error_summary is not None
    assert result.run.error_summary.category is ErrorCategory.UNKNOWN
    assert result.run.error_summary.retryable is False
    assert result.run.error_summary.message == "boom"
    assert result.run.error_summary.details == {
        "original_error_type": "RuntimeError",
        "classification_error_type": "RuntimeError",
        "classification_error_message": "classifier exploded",
    }


def test_infojobs_orchestration_persists_canonical_handoff_and_projection_trace() -> None:
    adapter = InfoJobsLikeAdapter(
        responses=[
            FetchOutcome(
                raw_items=(
                    {
                        "source_offer_id": "offer-1",
                        "title": "Automation Builder",
                        "modality": "remote",
                        "country": "Spain",
                    },
                ),
                next_checkpoint="cp-1",
                exhausted=True,
            )
        ]
    )
    job = IngestionJob(
        job_id="job-infojobs-trace",
        source_key="infojobs",
        filter_intent=FilterIntent(
            provider_filters={
                "experienceMin": "1",
                "sinceDate": "_24_HOURS",
                "teleworking": "remote",
                "category": "informatica-telecomunicaciones",
            }
        ),
        max_fetch_calls=1,
    )

    result = IngestionOrchestrator().execute_job(job, adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert result.run.canonical_trace is not None
    assert result.run.canonical_trace.canonical_handoff is not None
    assert tuple(family.family_key for family in result.run.canonical_trace.canonical_handoff.search_families) == (
        "ai_automation",
        "automation",
        "adjacent_odoo",
    )
    assert result.run.canonical_trace.execution_plan.family_plans[0].parameter_projections[0].authority == "canonical"
    assert result.run.canonical_trace.execution_plan.family_plans[0].parameter_projections[1].trust_level is ProjectionTrustLevel.PARTIAL_STRONG
    assert result.run.canonical_trace.execution_plan.post_fetch_filters == (
        "geography_modality",
        "consultancy_body_shopping",
        "seniority_semantic",
        "freshness_reliable",
    )
    assert result.run.canonical_trace.execution_plan.provider_filter_mappings[0].canonical_filter_key == "family"
    assert result.run.canonical_trace.query_executions[0].request_plan is not None
    assert result.run.canonical_trace.query_executions[0].request_plan.family_key == "ai_automation"
    assert result.run.canonical_trace.query_executions[0].forwarded_offer_ids == ("offer-1",)
    assert adapter.contexts[0].requested_filters == result.run.canonical_trace.execution_plan.family_plans[0].provider_params


def test_infojobs_orchestration_fans_out_across_multiple_family_plans_before_guardrail_exhausts() -> None:
    adapter = InfoJobsLikeAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "offer-es"},),
                next_checkpoint=None,
                exhausted=True,
            ),
            FetchOutcome(
                raw_items=({"id": "offer-en"},),
                next_checkpoint=None,
                exhausted=True,
            ),
        ]
    )
    job = IngestionJob(
        job_id="job-infojobs-fanout",
        source_key="infojobs",
        filter_intent=FilterIntent(
            provider_filters={
                "experienceMin": "1",
                "sinceDate": "_24_HOURS",
                "teleworking": "remote",
                "category": "informatica-telecomunicaciones",
            }
        ),
        max_fetch_calls=2,
    )

    result = IngestionOrchestrator().execute_job(job, adapter)

    family_plans = result.run.canonical_trace.execution_plan.family_plans
    assert len(family_plans) > 2
    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert [context.requested_filters for context in adapter.contexts] == [
        family_plans[0].provider_params,
        family_plans[1].provider_params,
    ]
    assert adapter.contexts[0].requested_filters["q"] != adapter.contexts[1].requested_filters["q"]
    assert [item["id"] for item in result.raw_handoff] == ["offer-es", "offer-en"]
    assert [trace.request_plan.query_label for trace in result.run.canonical_trace.query_executions] == [
        "es-baseline",
        "en-baseline",
    ]


def test_infojobs_fanout_deduplicates_forwarded_offers_but_keeps_per_query_trace() -> None:
    adapter = InfoJobsLikeAdapter(
        responses=[
            FetchOutcome(raw_items=({"id": "offer-1"},), next_checkpoint=None, exhausted=True),
            FetchOutcome(raw_items=({"id": "offer-1"},), next_checkpoint=None, exhausted=True),
        ]
    )
    job = IngestionJob(
        job_id="job-infojobs-dedup",
        source_key="infojobs",
        max_fetch_calls=2,
    )

    result = IngestionOrchestrator().execute_job(job, adapter)

    assert result.run.counters.raw_items_seen == 2
    assert result.run.counters.raw_items_forwarded == 1
    assert [item["id"] for item in result.raw_handoff] == ["offer-1"]
    assert [trace.raw_offer_ids for trace in result.run.canonical_trace.query_executions] == [
        ("offer-1",),
        ("offer-1",),
    ]
    assert result.run.canonical_trace.query_executions[1].forwarded_offer_ids == ()
    assert result.run.canonical_trace.query_executions[1].deduplicated_offer_ids == ("offer-1",)


def test_invalid_wrapped_execution_plan_checkpoint_uses_structured_failure() -> None:
    adapter = InfoJobsLikeAdapter(responses=[])
    job = IngestionJob(
        job_id="job-infojobs-invalid-checkpoint",
        source_key="infojobs",
        checkpoint_in='{"adapter_checkpoint": null, "family_plan_index": "bad", "orchestrator": "source_ingestion.execution_plan"}',
    )

    result = IngestionOrchestrator().execute_job(job, adapter)

    assert result.run.status is RunStatus.FAILED
    assert result.run.outcome_reason == "terminal adapter error"
    assert result.run.error_summary is not None
    assert result.run.error_summary.category is ErrorCategory.CONFIGURATION
    assert result.run.error_summary.details["provider"] == "infojobs"
    assert result.run.error_summary.details["failure_kind"] == "checkpoint"


def test_execute_job_fails_fast_when_job_source_key_does_not_match_adapter() -> None:
    adapter = FakeAdapter(responses=[])
    orchestrator = IngestionOrchestrator()

    with pytest.raises(ValueError, match="job source_key does not match adapter source_key"):
        orchestrator.execute_job(build_job(source_key="other-source"), adapter)


def test_fake_adapter_requires_scripted_responses() -> None:
    adapter = FakeAdapter(responses=[])

    with pytest.raises(IndexError):
        adapter.fetch(
            FetchContext(
                job_id="job",
                run_id="run",
                source_key="fake-source",
                capability_snapshot=adapter.capabilities,
            )
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [("max_retries", -1), ("max_fetch_calls", -1), ("max_items", -1)],
)
def test_ingestion_job_rejects_negative_guardrail_values(field: str, value: int) -> None:
    expected = rf"{field} must be >= 0" if field == "max_retries" else rf"{field} must be > 0"
    with pytest.raises(ValueError, match=expected):
        build_job(**{field: value})


@pytest.mark.parametrize(("field", "value"), [("max_fetch_calls", 0), ("max_items", 0)])
def test_ingestion_job_rejects_zero_scoped_budgets(field: str, value: int) -> None:
    with pytest.raises(ValueError, match=rf"{field} must be > 0"):
        build_job(**{field: value})


def test_ingestion_job_rejects_inverted_time_window() -> None:
    with pytest.raises(ValueError, match="window_start must be <= window_end"):
        build_job(
            window_start=datetime(2026, 4, 14, 12, 0, 0),
            window_end=datetime(2026, 4, 14, 11, 0, 0),
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_retries": -1}, "max_retries must be >= 0"),
        ({"max_fetch_calls": -1}, "max_fetch_calls must be > 0"),
        ({"max_fetch_calls": 0}, "max_fetch_calls must be > 0"),
        ({"max_items": -1}, "max_items must be > 0"),
        ({"max_items": 0}, "max_items must be > 0"),
    ],
)
def test_ingestion_guardrails_reject_negative_values(
    kwargs: dict[str, int], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        IngestionGuardrails(**kwargs)


def test_adapter_mutation_of_nested_requested_filters_does_not_leak_into_run_snapshot() -> None:
    adapter = MutatingAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "1"},),
                next_checkpoint="cp-1",
                exhausted=True,
            )
        ]
    )
    orchestrator = IngestionOrchestrator()
    job = build_job(
        filter_intent=FilterIntent(
            provider_filters={"keyword": "python", "meta": {"location": "remote"}}
        )
    )

    result = orchestrator.execute_job(job, adapter)

    assert result.run.status is RunStatus.COMPLETED
    assert result.run.filter_snapshot.provider_filters == {
        "keyword": "python",
        "meta": {"location": "remote"},
    }
    assert adapter.contexts[0].requested_filters == {"keyword": "golang"}


def test_run_captures_canonical_trace_with_dataset_versions_and_pushdown_boundaries() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=(
                    {
                        "id": "offer-1",
                        "title": "Automation Engineer",
                        "modality": "hybrid",
                        "city": "Barcelona",
                        "country": "Spain",
                        "attendance_days_per_month": 2,
                    },
                ),
                next_checkpoint="cp-1",
                exhausted=True,
            )
        ]
    )
    orchestrator = IngestionOrchestrator()

    result = orchestrator.execute_job(build_job(filter_intent=FilterIntent(provider_filters={"keyword": "python", "sinceDate": "_15_DAYS"})), adapter)

    assert result.run.canonical_trace is not None
    assert result.run.canonical_trace.capture_profile_ref == "source-search-strategy.v1"
    assert result.run.canonical_trace.execution_plan.derived_provider_params == {
        "keyword": "python",
    }
    assert result.run.canonical_trace.execution_plan.pushed_down_filters == ("search_terms",)
    assert [
        (mapping.canonical_filter_key, mapping.provider_param)
        for mapping in result.run.canonical_trace.execution_plan.provider_filter_mappings
    ] == [("search_terms", "keyword")]
    assert result.run.canonical_trace.execution_plan.post_fetch_filters == (
        "geography_modality",
        "consultancy_body_shopping",
        "seniority_semantic",
        "freshness_reliable",
    )
    assert result.run.canonical_trace.dataset_snapshots[0].dataset_version == "2026.04.1"
    assert result.run.canonical_trace.offer_outcomes[0].source_offer_id == "offer-1"
    assert result.run.canonical_trace.offer_outcomes[0].decision == "passed"


def test_context_requested_filters_use_execution_plan_pushdown_params_only() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=({"id": "offer-1"},),
                next_checkpoint="cp-1",
                exhausted=True,
            )
        ]
    )

    result = IngestionOrchestrator().execute_job(
        build_job(
            filter_intent=FilterIntent(
                provider_filters={
                    "keyword": "python",
                    "sinceDate": "_15_DAYS",
                    "consultancy_body_shopping": "explicit_only",
                }
            )
        ),
        adapter,
    )

    assert result.run.status is RunStatus.COMPLETED
    assert adapter.contexts[0].requested_filters == {"keyword": "python"}


def test_canonical_exclusions_do_not_fake_budget_truncation_or_block_checkpoint_progress() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=(
                    {
                        "id": "offer-excluded",
                        "title": "Consultor IA",
                        "description": "Consultora para proyectos de clientes y staffing.",
                        "modality": "remote",
                        "country": "Spain",
                    },
                    {
                        "id": "offer-kept",
                        "title": "Automation Engineer",
                        "modality": "remote",
                        "country": "Spain",
                    },
                ),
                next_checkpoint="cp-1",
                exhausted=True,
            )
        ]
    )

    result = IngestionOrchestrator().execute_job(build_job(checkpoint_in="cp-previous"), adapter)

    assert result.run.status is RunStatus.COMPLETED
    assert result.run.outcome_reason == "source exhausted"
    assert result.run.checkpoint_in == "cp-previous"
    assert result.run.checkpoint_out == "cp-1"
    assert result.run.counters.raw_items_seen == 2
    assert result.run.counters.raw_items_forwarded == 1
    assert result.raw_handoff == ({"id": "offer-kept", "title": "Automation Engineer", "modality": "remote", "country": "Spain"},)


def test_excluded_offers_stop_before_downstream_handoff_but_ambiguous_survive() -> None:
    adapter = FakeAdapter(
        responses=[
            FetchOutcome(
                raw_items=(
                    {
                        "id": "offer-1",
                        "title": "Automation Engineer",
                        "description": "Internal platform role.",
                        "company": "Accenture",
                        "modality": "remote",
                        "country": "Spain",
                    },
                    {
                        "id": "offer-2",
                        "title": "Consultor IA",
                        "description": "Consultora para proyectos de clientes y staffing.",
                        "company": "Delivery Partner",
                        "modality": "remote",
                        "country": "Spain",
                    },
                ),
                next_checkpoint="cp-1",
                exhausted=True,
            )
        ]
    )

    result = IngestionOrchestrator().execute_job(build_job(), adapter)

    assert [item["id"] for item in result.raw_handoff] == ["offer-1"]
    assert result.run.counters.raw_items_seen == 2
    assert result.run.counters.raw_items_forwarded == 1
    assert [snapshot.decision for snapshot in result.run.canonical_trace.offer_outcomes] == [
        "ambiguous",
        "excluded",
    ]
