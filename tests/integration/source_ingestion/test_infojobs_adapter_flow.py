from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from jobmatchrag.source_ingestion import FilterIntent, IngestionGuardrails, IngestionJob, RunStatus
from jobmatchrag.source_ingestion.contracts import RawCaptureOrigin
from jobmatchrag.source_ingestion.infojobs.adapter import InfoJobsAdapter
from jobmatchrag.source_ingestion.infojobs.client import (
    InfoJobsClient,
    InfoJobsClientConfig,
    InfoJobsRequest,
    InfoJobsResponse,
)
from jobmatchrag.source_ingestion.infojobs.errors import InfoJobsAPIError
from jobmatchrag.source_ingestion.orchestrator import IngestionOrchestrator


class RecordingTransport:
    def __init__(self, responses: Sequence[dict[str, object] | Exception]) -> None:
        self._responses = list(responses)
        self.requests: list[InfoJobsRequest] = []

    def request_json(self, request: InfoJobsRequest) -> InfoJobsResponse:
        self.requests.append(request)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return InfoJobsResponse(payload=response)


class TrackingKnownOfferIndex:
    def __init__(self, new_offer_ids: set[str]) -> None:
        self._new_offer_ids = new_offer_ids

    def is_new(self, source_key: str, source_offer_id: str) -> bool:
        return source_offer_id in self._new_offer_ids


def test_job_run_handoff_keeps_list_detail_provenance_for_infojobs() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new", "title": "Python Engineer"},
                    {"id": "offer-known", "title": "Known Role"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {"id": "offer-new", "description": "Build ingestion systems"},
        ]
    )
    client = InfoJobsClient(
        config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
        transport=transport,
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=1, max_items=10))
    job = IngestionJob(
        job_id="job-infojobs-1",
        source_key="infojobs",
        filter_intent=FilterIntent(provider_filters={"q": "python", "sinceDate": "_24_HOURS"}),
        checkpoint_in='{"adapter": "infojobs", "offer_index": 0, "page": 1, "version": 1}',
        max_fetch_calls=1,
        max_items=10,
    )

    result = orchestrator.execute_job(
        job,
        InfoJobsAdapter(
            client=client,
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new"}),
        ),
    )

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert result.run.checkpoint_in == '{"adapter": "infojobs", "offer_index": 0, "page": 1, "version": 1}'
    assert result.run.counters.raw_items_forwarded == 2
    assert len(result.raw_handoff) == 2
    assert set(result.raw_handoff[0]["captures"]) == {RawCaptureOrigin.LIST, RawCaptureOrigin.DETAIL}
    assert set(result.raw_handoff[1]["captures"]) == {RawCaptureOrigin.LIST}
    assert result.raw_handoff[0]["trace"]["list_request"]["sinceDate"] == "_24_HOURS"


def test_infojobs_flow_closes_partial_when_detail_budget_stops_mid_page() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new-1", "title": "Needs Detail First"},
                    {"id": "offer-new-2", "title": "Needs Detail Second"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {"id": "offer-new-1", "description": "First detail"},
            {
                "items": [
                    {"id": "offer-new-1", "title": "Needs Detail First"},
                    {"id": "offer-new-2", "title": "Needs Detail Second"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {"id": "offer-new-2", "description": "Second detail"},
        ]
    )
    client = InfoJobsClient(
        config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
        transport=transport,
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=1, max_items=10))
    job = IngestionJob(job_id="job-infojobs-2", source_key="infojobs", max_fetch_calls=1, max_items=10)

    result = orchestrator.execute_job(
        job,
        InfoJobsAdapter(
            client=client,
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new-1", "offer-new-2"}),
            max_requests_per_fetch=2,
            max_detail_requests_per_fetch=1,
        ),
    )

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert result.run.counters.raw_items_forwarded == 2
    assert result.run.checkpoint_out == '{"adapter": "infojobs", "offer_index": 2, "page": 1, "version": 1}'
    assert [item["source_offer_id"] for item in result.raw_handoff] == ["offer-new-1", "offer-new-2"]
    assert result.raw_handoff[1]["trace"]["detail_context"] == {
        "status": "deferred",
        "reason": "request_budget_exhausted",
    }


def test_infojobs_flow_skips_detail_for_known_offer_and_records_rate_limit_observation() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-known", "title": "Known Role"},
                    {"id": "offer-new", "title": "Python Engineer"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            InfoJobsAPIError(
                status_code=429,
                endpoint="GET /offer/{offerId}",
                message="cool down",
                headers={"Retry-After": "90", "X-RateLimit-Remaining": "0"},
                observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
            ),
        ]
    )
    client = InfoJobsClient(
        config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
        transport=transport,
    )
    orchestrator = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=2, max_items=10))
    job = IngestionJob(job_id="job-infojobs-3", source_key="infojobs", max_fetch_calls=2, max_items=10)

    result = orchestrator.execute_job(
        job,
        InfoJobsAdapter(
            client=client,
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new"}),
        ),
    )

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "rate limit constrained execution"
    assert result.run.counters.raw_items_forwarded == 2
    assert [item["source_offer_id"] for item in result.raw_handoff] == ["offer-known", "offer-new"]
    assert len(result.run.rate_limit_observations) == 1
    assert result.run.rate_limit_observations[0].retry_after_seconds == 90
    assert result.raw_handoff[1]["trace"]["detail_context"] == {
        "status": "deferred",
        "reason": "rate_limited",
    }


def test_infojobs_flow_keeps_canonical_authority_and_effective_request_trace() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-known", "title": "Automation Builder"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
        ]
    )
    client = InfoJobsClient(
        config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
        transport=transport,
    )
    result = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=1, max_items=10)).execute_job(
        IngestionJob(
            job_id="job-infojobs-4",
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
            max_items=10,
        ),
        InfoJobsAdapter(
            client=client,
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
        ),
    )

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert result.run.canonical_trace is not None
    assert result.run.canonical_trace.canonical_handoff is not None
    assert result.run.canonical_trace.execution_plan.family_plans[0].parameter_projections[0].authority == "canonical"
    assert result.run.canonical_trace.execution_plan.family_plans[0].pending_post_fetch_checks == (
        "seniority_semantic",
        "geography_modality",
    )
    assert result.raw_handoff[0]["trace"]["list_request"] == {
        "q": "Desarrollador Python de automatización/IA automatización ia aplicada herramientas internas python apis",
        "experienceMin": "1",
        "sinceDate": "_24_HOURS",
        "teleworking": "remote",
        "category": "informatica-telecomunicaciones",
        "page": 1,
        "maxResults": 50,
    }
    assert result.raw_handoff[0]["trace"]["request_plan"] == {
        "family_key": "ai_automation",
        "language": "es",
        "query_label": "es-baseline",
    }


def test_infojobs_flow_executes_multiple_mapped_family_queries_before_guardrail_exhausts() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-es", "title": "Automation Builder"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {
                "items": [
                    {"id": "offer-en", "title": "AI Engineer"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
        ]
    )
    client = InfoJobsClient(
        config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
        transport=transport,
    )
    result = IngestionOrchestrator(guardrails=IngestionGuardrails(max_fetch_calls=2, max_items=10)).execute_job(
        IngestionJob(
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
            max_items=10,
        ),
        InfoJobsAdapter(
            client=client,
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
        ),
    )

    list_requests = [request.params for request in transport.requests if request.endpoint == "GET /offer"]

    assert result.run.status is RunStatus.PARTIAL
    assert result.run.outcome_reason == "fetch guardrail exhausted"
    assert len(list_requests) == 2
    assert list_requests[0]["q"] != list_requests[1]["q"]
    assert [item["source_offer_id"] for item in result.raw_handoff] == ["offer-es", "offer-en"]
