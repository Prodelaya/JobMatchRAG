from __future__ import annotations

from datetime import datetime

from jobmatchrag.source_ingestion.contracts import (
    ErrorCategory,
    ErrorClassification,
    KnownOfferIndex,
    PaginationSupport,
    RawCaptureOrigin,
    RateLimitObservation,
    RateLimitSupport,
    RawOfferHandoff,
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


def test_infojobs_adapter_seam_names_known_offer_lookup_and_raw_handoff_shape() -> None:
    class StaticKnownOfferIndex:
        def is_new(self, source_key: str, source_offer_id: str) -> bool:
            return source_key == "infojobs" and source_offer_id == "offer-1"

    known_offer_index: KnownOfferIndex = StaticKnownOfferIndex()
    handoff: RawOfferHandoff = {
        "source_key": "infojobs",
        "source_offer_id": "offer-1",
        "trace": {
            "job_id": "job-1",
            "run_id": "run-1",
            "checkpoint_in": "opaque-checkpoint",
            "list_request": {"page": 1, "maxResults": 50, "sinceDate": "_24_HOURS"},
            "page_context": {"current_page": 1, "total_pages": 3},
        },
        "captures": {
            RawCaptureOrigin.LIST: {
                "origin": RawCaptureOrigin.LIST,
                "endpoint": "GET /offer",
                "api_version": "9",
                "payload": {"id": "offer-1", "title": "Python Engineer"},
            }
        },
    }

    assert known_offer_index.is_new("infojobs", "offer-1") is True
    assert handoff["captures"][RawCaptureOrigin.LIST]["origin"] is RawCaptureOrigin.LIST
    assert handoff["captures"][RawCaptureOrigin.LIST]["payload"]["title"] == "Python Engineer"
