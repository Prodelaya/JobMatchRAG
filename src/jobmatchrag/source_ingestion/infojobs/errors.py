from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Mapping

from ..contracts import ErrorCategory, ErrorClassification, RateLimitObservation


@dataclass(frozen=True, slots=True)
class InfoJobsAPIError(Exception):
    status_code: int
    endpoint: str
    message: str
    error_code: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __str__(self) -> str:
        return self.message


@dataclass(frozen=True, slots=True)
class InfoJobsTransportError(Exception):
    message: str
    endpoint: str | None = None
    raw_body: str | None = None
    status_code: int | None = None
    failure_kind: str = "network"

    def __str__(self) -> str:
        return self.message


def _get_header_value(headers: Mapping[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def _extract_request_id(error: InfoJobsAPIError) -> str | None:
    request_id = error.payload.get("requestId")
    return str(request_id) if request_id is not None else None


def _parse_retry_after_seconds(value: str | None, *, observed_at: datetime) -> int | None:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    try:
        seconds = int(stripped)
    except ValueError:
        try:
            retry_after_at = parsedate_to_datetime(stripped)
        except (TypeError, ValueError, IndexError, OverflowError):
            return None
        if retry_after_at.tzinfo is None:
            retry_after_at = retry_after_at.replace(tzinfo=UTC)
        delta = retry_after_at - observed_at
        return max(int(delta.total_seconds()), 0)

    return seconds if seconds >= 0 else None


def _parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None

    stripped = value.strip()
    if not stripped:
        return None

    try:
        parsed = int(stripped)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def classify_infojobs_error(error: Exception) -> ErrorClassification:
    if isinstance(error, InfoJobsTransportError):
        details: dict[str, Any] = {"provider": "infojobs"}
        if error.endpoint is not None:
            details["endpoint"] = error.endpoint
        if error.status_code is not None:
            details["status_code"] = error.status_code
        if error.raw_body is not None:
            details["raw_body"] = error.raw_body
        if error.failure_kind != "network":
            details["failure_kind"] = error.failure_kind
        if error.failure_kind == "checkpoint":
            return ErrorClassification(
                category=ErrorCategory.CONFIGURATION,
                retryable=False,
                message=str(error),
                details=details,
            )
        if error.failure_kind == "payload":
            return ErrorClassification(
                category=ErrorCategory.SOURCE_DATA,
                retryable=False,
                message=str(error),
                details=details,
            )
        return ErrorClassification(
            category=ErrorCategory.NETWORK,
            retryable=True,
            message=str(error),
            details=details,
        )

    if isinstance(error, InfoJobsAPIError):
        api_details: dict[str, Any] = {
            "provider": "infojobs",
            "endpoint": error.endpoint,
            "status_code": error.status_code,
        }
        if error.error_code is not None:
            api_details["error_code"] = error.error_code
        request_id = _extract_request_id(error)
        if request_id is not None:
            api_details["request_id"] = request_id

        if error.error_code == "101":
            return ErrorClassification(
                category=ErrorCategory.AUTHENTICATION,
                retryable=False,
                message=error.message,
                details=api_details,
            )

        if error.error_code == "102":
            return ErrorClassification(
                category=ErrorCategory.CONFIGURATION,
                retryable=False,
                message=error.message,
                details=api_details,
            )

        if error.status_code == 401:
            return ErrorClassification(
                category=ErrorCategory.AUTHENTICATION,
                retryable=False,
                message=error.message,
                details=api_details,
            )

        if error.status_code == 429:
            return ErrorClassification(
                category=ErrorCategory.RATE_LIMIT,
                retryable=True,
                message=error.message,
                details=api_details,
            )

        if error.status_code >= 500:
            return ErrorClassification(
                category=ErrorCategory.NETWORK,
                retryable=True,
                message=error.message,
                details=api_details,
            )

        if error.error_code in {"301", "302", "303", "304", "305", "306", "307", "308", "309", "311", "313", "318", "319", "820"}:
            return ErrorClassification(
                category=ErrorCategory.SOURCE_DATA,
                retryable=False,
                message=error.message,
                details=api_details,
            )

        return ErrorClassification(
            category=ErrorCategory.UNKNOWN,
            retryable=False,
            message=error.message,
            details=api_details,
        )

    return ErrorClassification(
        category=ErrorCategory.UNKNOWN,
        retryable=False,
        message=str(error),
        details={"provider": "infojobs", "error_type": type(error).__name__},
    )


def rate_limit_observation_from_error(error: InfoJobsAPIError, *, scope: str) -> RateLimitObservation:
    retry_after = _get_header_value(error.headers, "Retry-After")
    remaining = _get_header_value(error.headers, "X-RateLimit-Remaining")
    details = {"provider": "infojobs", "endpoint": error.endpoint}
    request_id = _extract_request_id(error)
    if request_id is not None:
        details["request_id"] = request_id
    return RateLimitObservation(
        observed_at=error.observed_at,
        scope=scope,
        retry_after_seconds=_parse_retry_after_seconds(retry_after, observed_at=error.observed_at),
        remaining_quota=_parse_optional_int(remaining),
        notes=f"InfoJobs rate limit while calling {error.endpoint}",
        details=details,
    )
