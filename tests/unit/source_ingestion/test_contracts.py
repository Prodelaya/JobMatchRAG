from __future__ import annotations

from datetime import datetime

from jobmatchrag.source_ingestion.contracts import (
    ErrorCategory,
    ErrorClassification,
    PaginationSupport,
    RateLimitObservation,
    RateLimitSupport,
    SourceCapabilities,
    TimeWindowSupport,
)


def test_capabilities_can_declare_missing_checkpoint_support() -> None:
    capabilities = SourceCapabilities(
        pagination=PaginationSupport.CURSOR,
        time_windows=TimeWindowSupport.UPDATED_AT,
        supported_filters=frozenset({"keyword", "location"}),
        checkpoint_support=False,
        rate_limit_support=RateLimitSupport.EXPLICIT,
    )

    assert capabilities.pagination is PaginationSupport.CURSOR
    assert capabilities.time_windows is TimeWindowSupport.UPDATED_AT
    assert capabilities.supported_filters == frozenset({"keyword", "location"})
    assert capabilities.checkpoint_support is False
    assert capabilities.rate_limit_support is RateLimitSupport.EXPLICIT


def test_error_classification_preserves_non_retryable_failure() -> None:
    classification = ErrorClassification(
        category=ErrorCategory.CONFIGURATION,
        retryable=False,
        message="invalid credentials",
        details={"field": "api_key"},
    )

    assert classification.category is ErrorCategory.CONFIGURATION
    assert classification.retryable is False
    assert classification.message == "invalid credentials"
    assert classification.details == {"field": "api_key"}


def test_rate_limit_observation_keeps_structured_traceability() -> None:
    observed_at = datetime(2026, 4, 14, 12, 0, 0)
    observation = RateLimitObservation(
        observed_at=observed_at,
        scope="search",
        retry_after_seconds=30,
        remaining_quota=0,
        notes="provider asked for cooldown",
    )

    assert observation.observed_at is observed_at
    assert observation.scope == "search"
    assert observation.retry_after_seconds == 30
    assert observation.remaining_quota == 0
    assert observation.notes == "provider asked for cooldown"
