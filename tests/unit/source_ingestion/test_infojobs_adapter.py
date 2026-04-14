from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

from unittest.mock import patch

import pytest

from jobmatchrag.source_ingestion import (
    ErrorCategory,
    FetchContext,
    PaginationSupport,
    RateLimitSupport,
    SourceCapabilities,
    TimeWindowSupport,
)
from jobmatchrag.source_ingestion.contracts import RawCaptureOrigin
from jobmatchrag.source_ingestion.infojobs.adapter import InfoJobsAdapter
from jobmatchrag.source_ingestion.infojobs.client import (
    InfoJobsClient,
    InfoJobsClientConfig,
    InfoJobsRequest,
    InfoJobsResponse,
)
from jobmatchrag.source_ingestion.infojobs.errors import InfoJobsAPIError, InfoJobsTransportError


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
        self.calls: list[tuple[str, str]] = []

    def is_new(self, source_key: str, source_offer_id: str) -> bool:
        self.calls.append((source_key, source_offer_id))
        return source_offer_id in self._new_offer_ids


def build_context(**overrides: object) -> FetchContext:
    defaults: dict[str, object] = {
        "job_id": "job-1",
        "run_id": "run-1",
        "source_key": "infojobs",
        "capability_snapshot": SourceCapabilities(
            pagination=PaginationSupport.PAGE_NUMBER,
            time_windows=TimeWindowSupport.NONE,
            supported_filters=frozenset({"q", "province", "sinceDate", "order"}),
            checkpoint_support=True,
            rate_limit_support=RateLimitSupport.EXPLICIT,
        ),
        "requested_filters": {"q": "python", "sinceDate": "_24_HOURS"},
        "remaining_fetch_budget": 3,
        "remaining_item_budget": 10,
    }
    defaults.update(overrides)
    return FetchContext(**defaults)


def test_infojobs_client_builds_basic_auth_requests_for_list_and_detail() -> None:
    transport = RecordingTransport(
        responses=[
            {"items": [], "currentPage": 1, "totalPages": 1},
            {"id": "offer-1", "description": "Build systems"},
        ]
    )
    client = InfoJobsClient(
        config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
        transport=transport,
    )

    client.list_offers({"q": "python", "page": 1, "maxResults": 50})
    client.get_offer_detail("offer-1")

    assert [request.endpoint for request in transport.requests] == ["GET /offer", "GET /offer/{offerId}"]
    assert transport.requests[0].url == "https://api.infojobs.net/api/9/offer"
    assert transport.requests[1].url == "https://api.infojobs.net/api/7/offer/offer-1"
    assert transport.requests[0].params == {"q": "python", "page": 1, "maxResults": 50}
    assert transport.requests[0].headers["Authorization"] == "Basic Y2xpZW50OnNlY3JldA=="


def test_infojobs_request_and_config_repr_do_not_expose_secrets() -> None:
    config = InfoJobsClientConfig(client_id="client", client_secret="secret")
    request = InfoJobsRequest(
        url="https://api.infojobs.net/api/9/offer",
        endpoint="GET /offer",
        params={"page": 1},
        headers={"Accept": "application/json", "Authorization": "Basic Y2xpZW50OnNlY3JldA=="},
    )

    assert "secret" not in repr(config)
    assert "Authorization" not in repr(request)


def test_urllib_transport_wraps_non_json_http_errors_in_infojobs_api_error() -> None:
    client = InfoJobsClient(config=InfoJobsClientConfig(client_id="client", client_secret="secret"))
    headers = Message()
    headers.add_header("Content-Type", "text/plain")
    http_error = HTTPError(
        url="https://api.infojobs.net/api/9/offer",
        code=502,
        msg="Bad Gateway",
        hdrs=headers,
        fp=BytesIO(b"upstream proxy exploded"),
    )

    with patch("jobmatchrag.source_ingestion.infojobs.client.urlopen", side_effect=http_error):
        with pytest.raises(InfoJobsAPIError) as exc_info:
            client.list_offers({"q": "python"})

    error = exc_info.value
    assert error.status_code == 502
    assert error.message == "upstream proxy exploded"
    assert error.payload == {"raw_body": "upstream proxy exploded"}


def test_urllib_transport_tolerates_http_errors_without_headers() -> None:
    client = InfoJobsClient(config=InfoJobsClientConfig(client_id="client", client_secret="secret"))
    http_error = HTTPError(
        url="https://api.infojobs.net/api/9/offer",
        code=502,
        msg="Bad Gateway",
        hdrs=None,
        fp=BytesIO(b"upstream proxy exploded"),
    )

    with patch("jobmatchrag.source_ingestion.infojobs.client.urlopen", side_effect=http_error):
        with pytest.raises(InfoJobsAPIError) as exc_info:
            client.list_offers({"q": "python"})

    assert exc_info.value.headers == {}


def test_urllib_transport_wraps_invalid_json_success_bodies_in_transport_error() -> None:
    client = InfoJobsClient(config=InfoJobsClientConfig(client_id="client", client_secret="secret"))

    class FakeSuccessResponse:
        def __init__(self) -> None:
            self.status = 200
            self.headers = Message()

        def read(self) -> bytes:
            return b"not-json"

        def __enter__(self) -> FakeSuccessResponse:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    with patch(
        "jobmatchrag.source_ingestion.infojobs.client.urlopen",
        return_value=FakeSuccessResponse(),
    ):
        with pytest.raises(InfoJobsTransportError) as exc_info:
            client.list_offers({"q": "python"})

    error = exc_info.value
    assert error.endpoint == "GET /offer"
    assert error.raw_body == "not-json"
    assert error.status_code == 200


def test_urllib_transport_decodes_non_utf8_success_bodies_with_replacement() -> None:
    client = InfoJobsClient(config=InfoJobsClientConfig(client_id="client", client_secret="secret"))

    class FakeSuccessResponse:
        def __init__(self) -> None:
            self.status = 200
            self.headers = Message()
            self.headers.add_header("Content-Type", "application/json; charset=latin-1")

        def read(self) -> bytes:
            return '{"title": "caf\xe9"}'.encode("latin-1")

        def __enter__(self) -> FakeSuccessResponse:
            return self

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    with patch(
        "jobmatchrag.source_ingestion.infojobs.client.urlopen",
        return_value=FakeSuccessResponse(),
    ):
        response = client.list_offers({"q": "python"})

    assert response.payload == {"title": "caf\u00e9"}


def test_urllib_transport_decodes_non_utf8_error_bodies_with_replacement() -> None:
    client = InfoJobsClient(config=InfoJobsClientConfig(client_id="client", client_secret="secret"))
    headers = Message()
    headers.add_header("Content-Type", "text/plain; charset=latin-1")
    http_error = HTTPError(
        url="https://api.infojobs.net/api/9/offer",
        code=502,
        msg="Bad Gateway",
        hdrs=headers,
        fp=BytesIO("proxy caf\xe9 exploded".encode("latin-1")),
    )

    with patch("jobmatchrag.source_ingestion.infojobs.client.urlopen", side_effect=http_error):
        with pytest.raises(InfoJobsAPIError) as exc_info:
            client.list_offers({"q": "python"})

    assert exc_info.value.message == "proxy caf\u00e9 exploded"
    assert exc_info.value.payload == {"raw_body": "proxy caf\u00e9 exploded"}


def test_adapter_fetches_detail_only_for_new_offers_and_advances_to_next_page() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new", "title": "Python Engineer"},
                    {"id": "offer-known", "title": "Known Role"},
                ],
                "currentPage": 1,
                "totalPages": 2,
            },
            {"id": "offer-new", "description": "Build ingestion systems"},
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new"}),
    )

    outcome = adapter.fetch(build_context())

    assert outcome.exhausted is False
    assert len(outcome.raw_items) == 2
    assert outcome.next_checkpoint == '{"adapter": "infojobs", "offer_index": 0, "page": 2, "version": 1}'
    assert outcome.raw_items[0]["captures"][RawCaptureOrigin.DETAIL]["payload"]["description"] == "Build ingestion systems"
    assert set(outcome.raw_items[1]["captures"]) == {RawCaptureOrigin.LIST}
    assert [request.endpoint for request in transport.requests] == ["GET /offer", "GET /offer/{offerId}"]


def test_adapter_rejects_page_size_above_documented_operational_ceiling() -> None:
    with pytest.raises(ValueError, match="page_size must be <= 50"):
        InfoJobsAdapter(
            client=InfoJobsClient(
                config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
                transport=RecordingTransport(responses=[]),
            ),
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
            page_size=51,
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_requests_per_fetch": 0}, "max_requests_per_fetch must be > 0"),
        ({"max_detail_requests_per_fetch": 0}, "max_detail_requests_per_fetch must be > 0"),
        (
            {"max_requests_per_fetch": 2, "max_detail_requests_per_fetch": 2},
            "max_detail_requests_per_fetch must fit within the remaining request budget",
        ),
    ],
)
def test_adapter_rejects_invalid_request_budget_configuration(
    kwargs: dict[str, int], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        InfoJobsAdapter(
            client=InfoJobsClient(
                config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
                transport=RecordingTransport(responses=[]),
            ),
            known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
            **kwargs,
        )


def test_adapter_stops_before_unenriched_new_offer_when_request_budget_is_spent() -> None:
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
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new-1", "offer-new-2"}),
        max_requests_per_fetch=2,
        max_detail_requests_per_fetch=1,
    )

    outcome = adapter.fetch(build_context())

    assert outcome.exhausted is False
    assert outcome.next_checkpoint == '{"adapter": "infojobs", "offer_index": 2, "page": 1, "version": 1}'
    assert [item["source_offer_id"] for item in outcome.raw_items] == ["offer-new-1", "offer-new-2"]
    assert outcome.raw_items[1]["trace"]["detail_context"] == {
        "status": "deferred",
        "reason": "request_budget_exhausted",
    }
    assert set(outcome.raw_items[1]["captures"]) == {RawCaptureOrigin.LIST}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"currentPage": 1, "totalPages": 1}, "missing items/offers"),
        ({"items": {}, "currentPage": 1, "totalPages": 1}, "items/offers must be a JSON array"),
        ({"items": [{}], "currentPage": 1, "totalPages": 1}, "missing id"),
        ({"items": [{"id": "offer-1"}], "totalPages": 1}, "missing currentPage"),
        ({"items": [{"id": "offer-1"}], "currentPage": 1}, "missing totalPages"),
        ({"items": [{"id": "offer-1"}], "currentPage": "oops", "totalPages": 1}, "currentPage must be an integer"),
        ({"items": [{"id": "offer-1"}], "currentPage": 0, "totalPages": 1}, "currentPage must be > 0"),
        ({"items": [{"id": "offer-1"}], "currentPage": 2, "totalPages": 1}, "totalPages lower than currentPage"),
    ],
)
def test_adapter_wraps_malformed_listing_payloads_in_transport_error(
    payload: dict[str, object], message: str
) -> None:
    transport = RecordingTransport(responses=[payload])
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
    )

    with pytest.raises(InfoJobsTransportError, match=message):
        adapter.fetch(build_context())


def test_adapter_accepts_offers_key_for_listing_payload() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "offers": [{"id": "offer-1", "title": "Python Engineer"}],
                "currentPage": 1,
                "totalPages": 1,
            }
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
    )

    outcome = adapter.fetch(build_context())

    assert outcome.exhausted is True
    assert [item["source_offer_id"] for item in outcome.raw_items] == ["offer-1"]


def test_adapter_returns_partial_with_rate_limit_observation_when_detail_is_throttled() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [{"id": "offer-new", "title": "Python Engineer"}],
                "currentPage": 1,
                "totalPages": 1,
            },
            InfoJobsAPIError(
                status_code=429,
                endpoint="GET /offer/{offerId}",
                message="cool down",
                headers={"Retry-After": "120", "X-RateLimit-Remaining": "0"},
                observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
            ),
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new"}),
    )

    outcome = adapter.fetch(build_context())

    assert [item["source_offer_id"] for item in outcome.raw_items] == ["offer-new"]
    assert outcome.exhausted is False
    assert outcome.next_checkpoint == '{"adapter": "infojobs", "offer_index": 1, "page": 1, "version": 1}'
    assert len(outcome.rate_limit_observations) == 1
    assert outcome.rate_limit_observations[0].retry_after_seconds == 120
    assert outcome.raw_items[0]["trace"]["detail_context"] == {
        "status": "deferred",
        "reason": "rate_limited",
    }
    assert set(outcome.raw_items[0]["captures"]) == {RawCaptureOrigin.LIST}


def test_adapter_preserves_collected_items_when_later_detail_call_fails() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new-1", "title": "First"},
                    {"id": "offer-new-2", "title": "Second"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {"id": "offer-new-1", "description": "First detail"},
            InfoJobsAPIError(status_code=500, endpoint="GET /offer/{offerId}", message="boom"),
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new-1", "offer-new-2"}),
    )

    outcome = adapter.fetch(build_context())

    assert outcome.exhausted is False
    assert [item["source_offer_id"] for item in outcome.raw_items] == ["offer-new-1"]
    assert outcome.next_checkpoint == '{"adapter": "infojobs", "next_offer_id": "offer-new-2", "offer_index": 1, "page": 1, "version": 1}'
    assert outcome.error_summary is not None
    assert outcome.error_summary.category is ErrorCategory.NETWORK
    assert outcome.error_summary.retryable is True
    assert outcome.error_summary.message == "boom"


def test_adapter_surfaces_terminal_detail_failures_after_partial_progress() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new-1", "title": "First"},
                    {"id": "offer-new-2", "title": "Second"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {"id": "offer-new-1", "description": "First detail"},
            InfoJobsAPIError(
                status_code=401,
                endpoint="GET /offer/{offerId}",
                message="invalid credentials",
            ),
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new-1", "offer-new-2"}),
    )

    outcome = adapter.fetch(build_context())

    assert outcome.exhausted is False
    assert [item["source_offer_id"] for item in outcome.raw_items] == ["offer-new-1"]
    assert outcome.next_checkpoint == '{"adapter": "infojobs", "next_offer_id": "offer-new-2", "offer_index": 1, "page": 1, "version": 1}'
    assert outcome.error_summary is not None
    assert outcome.error_summary.category is ErrorCategory.AUTHENTICATION
    assert outcome.error_summary.retryable is False
    assert outcome.error_summary.message == "invalid credentials"


def test_adapter_finishes_terminal_page_without_replaying_full_page_after_deferred_last_offer() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new-1", "title": "First"},
                    {"id": "offer-new", "title": "Needs Detail"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
            {"id": "offer-new-1", "description": "First detail"},
            {
                "items": [
                    {"id": "offer-new-1", "title": "First"},
                    {"id": "offer-new", "title": "Needs Detail"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            },
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids={"offer-new-1", "offer-new"}),
        max_requests_per_fetch=2,
        max_detail_requests_per_fetch=1,
    )

    first_outcome = adapter.fetch(build_context())
    second_outcome = adapter.fetch(build_context(checkpoint=first_outcome.next_checkpoint))

    assert first_outcome.next_checkpoint == '{"adapter": "infojobs", "offer_index": 2, "page": 1, "version": 1}'
    assert first_outcome.exhausted is False
    assert [item["source_offer_id"] for item in first_outcome.raw_items] == ["offer-new-1", "offer-new"]
    assert second_outcome.exhausted is True
    assert [item["source_offer_id"] for item in second_outcome.raw_items] == []


def test_adapter_uses_checkpoint_offer_anchor_when_page_order_changes() -> None:
    transport = RecordingTransport(
        responses=[
            {
                "items": [
                    {"id": "offer-new-2", "title": "Moved Up"},
                    {"id": "offer-new-1", "title": "Already Seen"},
                ],
                "currentPage": 1,
                "totalPages": 1,
            }
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
    )

    outcome = adapter.fetch(
        build_context(
            checkpoint='{"adapter": "infojobs", "next_offer_id": "offer-new-2", "offer_index": 1, "page": 1, "version": 1}'
        )
    )

    assert outcome.exhausted is True
    assert [item["source_offer_id"] for item in outcome.raw_items] == ["offer-new-2", "offer-new-1"]


def test_adapter_rejects_invalid_checkpoint_as_non_retryable_configuration_issue() -> None:
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=RecordingTransport(responses=[]),
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
    )

    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        adapter.fetch(build_context(checkpoint='{"adapter": "infojobs", "version": 1, "page": "oops", "offer_index": 0}'))

    classification = adapter.classify_error(exc_info.value)

    assert classification.category is ErrorCategory.CONFIGURATION
    assert classification.retryable is False


def test_adapter_classifies_malformed_listing_payload_as_terminal_source_data() -> None:
    transport = RecordingTransport(
        responses=[{"items": [{"id": "offer-1"}], "currentPage": 1, "totalPages": "oops"}]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
    )

    with pytest.raises(InfoJobsTransportError) as exc_info:
        adapter.fetch(build_context())

    classification = adapter.classify_error(exc_info.value)

    assert classification.category is ErrorCategory.SOURCE_DATA
    assert classification.retryable is False


def test_adapter_returns_partial_with_rate_limit_observation_when_listing_is_throttled() -> None:
    transport = RecordingTransport(
        responses=[
            InfoJobsAPIError(
                status_code=429,
                endpoint="GET /offer",
                message="cool down",
                headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
                observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
            )
        ]
    )
    adapter = InfoJobsAdapter(
        client=InfoJobsClient(
            config=InfoJobsClientConfig(client_id="client", client_secret="secret"),
            transport=transport,
        ),
        known_offer_index=TrackingKnownOfferIndex(new_offer_ids=set()),
    )

    outcome = adapter.fetch(build_context())

    assert outcome.raw_items == ()
    assert outcome.exhausted is False
    assert outcome.next_checkpoint == '{"adapter": "infojobs", "offer_index": 0, "page": 1, "version": 1}'
    assert len(outcome.rate_limit_observations) == 1
    assert outcome.rate_limit_observations[0].scope == "list"
    assert outcome.rate_limit_observations[0].retry_after_seconds == 60
