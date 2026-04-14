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
    RateLimitObservation,
    RateLimitSupport,
    SourceCapabilities,
    TimeWindowSupport,
)
from jobmatchrag.source_ingestion.models import FilterIntent, IngestionJob, RunStatus
from jobmatchrag.source_ingestion.orchestrator import IngestionGuardrails, IngestionOrchestrator


class FakeAdapter:
    source_key = "fake-source"

    def __init__(self, responses: Sequence[FetchOutcome | Exception]) -> None:
        self.capabilities = SourceCapabilities(
            pagination=PaginationSupport.CURSOR,
            time_windows=TimeWindowSupport.UPDATED_AT,
            supported_filters=frozenset({"keyword"}),
            checkpoint_support=True,
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

    result = orchestrator.execute_job(build_job(max_items=1), adapter)

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "bounded run scope reached"
    assert result.run.counters.fetch_calls == 1
    assert result.run.counters.raw_items_seen == 3
    assert result.run.counters.raw_items_forwarded == 1
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


def test_retryable_failure_becomes_failed_when_retry_budget_is_zero() -> None:
    adapter = FakeAdapter(responses=[TimeoutError("temporary timeout")])
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_retries=0))

    result = orchestrator.execute_job(build_job(max_retries=0), adapter)

    assert result.run.status is RunStatus.FAILED
    assert result.run.outcome_reason == "retry budget exhausted"
    assert result.run.retry_count == 0


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
