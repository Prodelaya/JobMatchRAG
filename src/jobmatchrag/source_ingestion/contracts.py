from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, TypedDict, runtime_checkable


class PaginationSupport(StrEnum):
    NONE = "none"
    PAGE_NUMBER = "page_number"
    CURSOR = "cursor"


class TimeWindowSupport(StrEnum):
    NONE = "none"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RateLimitSupport(StrEnum):
    NONE = "none"
    PASSIVE = "passive"
    EXPLICIT = "explicit"


class ErrorCategory(StrEnum):
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    SOURCE_DATA = "source_data"
    UNKNOWN = "unknown"


class RawCaptureOrigin(StrEnum):
    LIST = "list"
    DETAIL = "detail"


@dataclass(frozen=True, slots=True)
class SourceCapabilities:
    pagination: PaginationSupport
    time_windows: TimeWindowSupport
    supported_filters: frozenset[str] = frozenset()
    checkpoint_support: bool = False
    rate_limit_support: RateLimitSupport = RateLimitSupport.NONE


@dataclass(frozen=True, slots=True)
class ErrorClassification:
    category: ErrorCategory
    retryable: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RateLimitObservation:
    observed_at: datetime
    scope: str
    retry_after_seconds: int | None = None
    remaining_quota: int | None = None
    notes: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class RawCapture(TypedDict):
    origin: RawCaptureOrigin
    endpoint: str
    api_version: str
    observed_at: str
    payload: dict[str, Any]


class RawTrace(TypedDict):
    job_id: str
    run_id: str
    checkpoint_in: str | None
    list_request: dict[str, Any]
    page_context: dict[str, Any]
    detail_context: dict[str, Any] | None


class RawOfferHandoff(TypedDict):
    source_key: str
    source_offer_id: str
    trace: RawTrace
    captures: dict[RawCaptureOrigin, RawCapture]


@dataclass(frozen=True, slots=True)
class FetchContext:
    job_id: str
    run_id: str
    source_key: str
    capability_snapshot: SourceCapabilities
    requested_filters: dict[str, Any] = field(default_factory=dict)
    requested_window_start: datetime | None = None
    requested_window_end: datetime | None = None
    checkpoint: str | None = None
    retry_count: int = 0
    remaining_fetch_budget: int | None = None
    remaining_item_budget: int | None = None


@dataclass(frozen=True, slots=True)
class FetchOutcome:
    raw_items: tuple[dict[str, Any], ...] = ()
    next_checkpoint: str | None = None
    exhausted: bool = True
    rate_limit_observations: tuple[RateLimitObservation, ...] = ()
    error_summary: ErrorClassification | None = None


@runtime_checkable
class SourceAdapter(Protocol):
    source_key: str
    capabilities: SourceCapabilities

    def fetch(self, context: FetchContext) -> FetchOutcome: ...

    def classify_error(self, error: Exception) -> ErrorClassification: ...


@runtime_checkable
class KnownOfferIndex(Protocol):
    def is_new(self, source_key: str, source_offer_id: str) -> bool: ...
