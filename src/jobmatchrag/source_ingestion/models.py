from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .contracts import (
    ErrorClassification,
    RateLimitObservation,
    SourceCapabilities,
)


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class FilterIntent:
    provider_filters: dict[str, Any] = field(default_factory=dict)
    canonical_filters_note: str = (
        "Provider/source filters are advisory optimization only; internal eligibility remains canonical."
    )


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
