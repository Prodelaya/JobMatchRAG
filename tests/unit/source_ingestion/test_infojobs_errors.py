from __future__ import annotations

from datetime import UTC, datetime

import pytest

from jobmatchrag.source_ingestion import ErrorCategory
from jobmatchrag.source_ingestion.infojobs.errors import (
    InfoJobsAPIError,
    InfoJobsTransportError,
    classify_infojobs_error,
    rate_limit_observation_from_error,
)


def test_classify_infojobs_error_maps_authentication_validation_and_network_cases() -> None:
    authentication = classify_infojobs_error(
        InfoJobsAPIError(status_code=401, endpoint="GET /offer", message="invalid credentials")
    )
    source_data = classify_infojobs_error(
        InfoJobsAPIError(
            status_code=400,
            endpoint="GET /offer",
            error_code="301",
            message="invalid province",
        )
    )
    network = classify_infojobs_error(InfoJobsTransportError("timeout talking to InfoJobs"))

    assert authentication.category is ErrorCategory.AUTHENTICATION
    assert authentication.retryable is False
    assert source_data.category is ErrorCategory.SOURCE_DATA
    assert source_data.retryable is False
    assert network.category is ErrorCategory.NETWORK
    assert network.retryable is True


def test_classify_infojobs_error_maps_security_codes_101_and_102_explicitly() -> None:
    unauthenticated = classify_infojobs_error(
        InfoJobsAPIError(
            status_code=400,
            endpoint="GET /offer",
            error_code="101",
            message="user is not authenticated",
        )
    )
    invalid_client = classify_infojobs_error(
        InfoJobsAPIError(
            status_code=400,
            endpoint="GET /offer",
            error_code="102",
            message="invalid client credentials",
        )
    )

    assert unauthenticated.category is ErrorCategory.AUTHENTICATION
    assert unauthenticated.retryable is False
    assert invalid_client.category is ErrorCategory.CONFIGURATION
    assert invalid_client.retryable is False


def test_classify_infojobs_error_prefers_provider_code_102_over_generic_http_401() -> None:
    classification = classify_infojobs_error(
        InfoJobsAPIError(
            status_code=401,
            endpoint="GET /offer",
            error_code="102",
            message="invalid client credentials",
        )
    )

    assert classification.category is ErrorCategory.CONFIGURATION
    assert classification.retryable is False


def test_classify_infojobs_error_preserves_request_id_when_present() -> None:
    classification = classify_infojobs_error(
        InfoJobsAPIError(
            status_code=429,
            endpoint="GET /offer",
            message="cool down",
            payload={"requestId": "req-123"},
        )
    )

    assert classification.details["request_id"] == "req-123"


def test_rate_limit_translation_emits_structured_observation() -> None:
    error = InfoJobsAPIError(
        status_code=429,
        endpoint="GET /offer/{offerId}",
        message="cool down",
        headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
        observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
    )

    observation = rate_limit_observation_from_error(error, scope="detail")
    classification = classify_infojobs_error(error)

    assert observation.retry_after_seconds == 60
    assert observation.remaining_quota == 0
    assert observation.scope == "detail"
    assert observation.details == {"provider": "infojobs", "endpoint": "GET /offer/{offerId}"}
    assert classification.category is ErrorCategory.RATE_LIMIT
    assert classification.retryable is True


def test_rate_limit_translation_parses_http_date_and_preserves_request_id() -> None:
    error = InfoJobsAPIError(
        status_code=429,
        endpoint="GET /offer",
        message="cool down",
        headers={
            "Retry-After": "Tue, 14 Apr 2026 12:01:30 GMT",
            "X-RateLimit-Remaining": "not-a-number",
        },
        payload={"requestId": "req-456"},
        observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
    )

    observation = rate_limit_observation_from_error(error, scope="list")

    assert observation.retry_after_seconds == 90
    assert observation.remaining_quota is None
    assert observation.details["request_id"] == "req-456"


def test_rate_limit_translation_reads_headers_case_insensitively() -> None:
    error = InfoJobsAPIError(
        status_code=429,
        endpoint="GET /offer",
        message="cool down",
        headers={"retry-after": "15", "x-ratelimit-remaining": "2"},
        observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
    )

    observation = rate_limit_observation_from_error(error, scope="list")

    assert observation.retry_after_seconds == 15
    assert observation.remaining_quota == 2


def test_transport_error_preserves_endpoint_and_raw_body_context() -> None:
    classification = classify_infojobs_error(
        InfoJobsTransportError(
            message="InfoJobs returned an invalid JSON success body for GET /offer",
            endpoint="GET /offer",
            raw_body="<html>proxy error</html>",
            status_code=200,
        )
    )

    assert classification.category is ErrorCategory.NETWORK
    assert classification.retryable is True
    assert classification.details["endpoint"] == "GET /offer"
    assert classification.details["raw_body"] == "<html>proxy error</html>"


def test_payload_transport_error_is_terminal_source_data() -> None:
    classification = classify_infojobs_error(
        InfoJobsTransportError(
            message="InfoJobs returned malformed listing payload",
            endpoint="GET /offer",
            raw_body="{bad json}",
            status_code=200,
            failure_kind="payload",
        )
    )

    assert classification.category is ErrorCategory.SOURCE_DATA
    assert classification.retryable is False
    assert classification.details["failure_kind"] == "payload"


@pytest.mark.parametrize("retry_after", ["oops", ""])
def test_rate_limit_translation_ignores_unparseable_retry_after_values(retry_after: str) -> None:
    error = InfoJobsAPIError(
        status_code=429,
        endpoint="GET /offer",
        message="cool down",
        headers={"Retry-After": retry_after, "X-RateLimit-Remaining": "-1"},
        observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
    )

    observation = rate_limit_observation_from_error(error, scope="list")

    assert observation.retry_after_seconds is None
    assert observation.remaining_quota is None
