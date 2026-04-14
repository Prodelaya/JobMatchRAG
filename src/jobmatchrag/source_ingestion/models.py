from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from .contracts import (
    ErrorClassification,
    RateLimitObservation,
    SourceCapabilities,
)


def _freeze_filter_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_filter_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_filter_value(item) for item in value)
    return deepcopy(value)


def thaw_filter_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: thaw_filter_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_filter_value(item) for item in value]
    return deepcopy(value)


def _validate_non_negative(name: str, value: int | None) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{name} must be >= 0")


def _validate_positive(name: str, value: int | None) -> None:
    if value is not None and value <= 0:
        raise ValueError(f"{name} must be > 0")


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class FilterIntent:
    provider_filters: Mapping[str, Any] = field(default_factory=dict)
    canonical_filters_note: str = (
        "Provider/source filters are advisory optimization only; internal eligibility remains canonical."
    )

    def __post_init__(self) -> None:
        detached_filters = MappingProxyType(
            {key: _freeze_filter_value(value) for key, value in dict(self.provider_filters).items()}
        )
        object.__setattr__(self, "provider_filters", detached_filters)


@dataclass(frozen=True, slots=True)
class IngestionJob:
    job_id: str
    source_key: str
    filter_intent: FilterIntent = field(default_factory=FilterIntent)
    window_start: datetime | None = None
    window_end: datetime | None = None
    checkpoint_in: str | None = None
    requested_by: str = "system"
    max_retries: int = 2
    max_fetch_calls: int = 10
    max_items: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_non_negative("max_retries", self.max_retries)
        _validate_positive("max_fetch_calls", self.max_fetch_calls)
        _validate_positive("max_items", self.max_items)
        if (
            self.window_start is not None
            and self.window_end is not None
            and self.window_start > self.window_end
        ):
            raise ValueError("window_start must be <= window_end")


@dataclass(slots=True)
class RetryRecord:
    attempt: int
    classification: ErrorClassification
    observed_at: datetime


@dataclass(slots=True)
class RunCounters:
    fetch_calls: int = 0
    raw_items_seen: int = 0
    raw_items_forwarded: int = 0


@dataclass(slots=True)
class IngestionRun:
    run_id: str
    job_id: str
    source_key: str
    status: RunStatus
    started_at: datetime
    capability_snapshot: SourceCapabilities
    filter_snapshot: FilterIntent
    requested_by: str
    checkpoint_in: str | None = None
    checkpoint_out: str | None = None
    ended_at: datetime | None = None
    counters: RunCounters = field(default_factory=RunCounters)
    retry_count: int = 0
    retry_history: list[RetryRecord] = field(default_factory=list)
    rate_limit_observations: list[RateLimitObservation] = field(default_factory=list)
    error_summary: ErrorClassification | None = None
    outcome_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def complete(self, status: RunStatus, reason: str | None = None) -> None:
        self.status = status
        self.ended_at = datetime.now(UTC)
        self.outcome_reason = reason
