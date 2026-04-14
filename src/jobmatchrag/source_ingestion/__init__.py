"""Adapter-agnostic source ingestion framework boundary."""

from .contracts import (
    ErrorCategory,
    ErrorClassification,
    FetchContext,
    FetchOutcome,
    KnownOfferIndex,
    PaginationSupport,
    RawCapture,
    RawCaptureOrigin,
    RawOfferHandoff,
    RawTrace,
    RateLimitObservation,
    RateLimitSupport,
    SourceAdapter,
    SourceCapabilities,
    TimeWindowSupport,
)
from .models import (
    FilterIntent,
    IngestionJob,
    IngestionRun,
    RetryRecord,
    RunCounters,
    RunStatus,
)
from .orchestrator import (
    IngestionGuardrails,
    IngestionOrchestrator,
    OrchestrationResult,
)

__all__ = [
    "ErrorCategory",
    "ErrorClassification",
    "FetchContext",
    "FetchOutcome",
    "FilterIntent",
    "IngestionGuardrails",
    "IngestionJob",
    "IngestionOrchestrator",
    "IngestionRun",
    "KnownOfferIndex",
    "OrchestrationResult",
    "PaginationSupport",
    "RawCapture",
    "RawCaptureOrigin",
    "RawOfferHandoff",
    "RawTrace",
    "RateLimitObservation",
    "RateLimitSupport",
    "RetryRecord",
    "RunCounters",
    "RunStatus",
    "SourceAdapter",
    "SourceCapabilities",
    "TimeWindowSupport",
]
