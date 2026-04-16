from __future__ import annotations

from datetime import datetime

from jobmatchrag.source_ingestion.contracts import (
    CanonicalFilterOutcome,
    ErrorCategory,
    ErrorClassification,
    EvidenceRef,
    KnownOfferIndex,
    PaginationSupport,
    ProviderExecutionPlan,
    ProviderFilterMapping,
    RawCaptureOrigin,
    ReferenceDatasetSnapshot,
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


def test_canonical_filter_outcome_keeps_dataset_evidence_and_explicit_rationale() -> None:
    snapshot = ReferenceDatasetSnapshot(dataset_key="hybrid_cities", dataset_version="2026.04.1")
    outcome = CanonicalFilterOutcome(
        filter_key="consultancy_body_shopping",
        status="ambiguous",
        reason_code="known_company_signal_only",
        evidence_refs=(
            EvidenceRef(
                evidence_type="company_signal",
                locator="accenture",
                dataset_version=snapshot.dataset_version,
                confidence="medium",
            ),
            EvidenceRef(
                evidence_type="consultancy_text",
                locator="description",
                confidence="explicit",
            ),
        ),
    )

    assert outcome.filter_key == "consultancy_body_shopping"
    assert outcome.status == "ambiguous"
    assert outcome.reason_code == "known_company_signal_only"
    assert outcome.evidence_refs[0].dataset_version == snapshot.dataset_version
    assert outcome.evidence_refs[1].confidence == "explicit"


def test_provider_execution_plan_separates_pushdown_from_post_fetch_filters() -> None:
    plan = ProviderExecutionPlan(
        canonical_profile_ref="source-search-strategy.v1",
        derived_provider_params={"q": "python automation", "sinceDate": "_15_DAYS"},
        pushed_down_filters=("search_terms", "freshness_window"),
        provider_filter_mappings=(
            ProviderFilterMapping(canonical_filter_key="search_terms", provider_param="q"),
            ProviderFilterMapping(canonical_filter_key="freshness_window", provider_param="sinceDate"),
        ),
        post_fetch_filters=("geography_modality", "consultancy_body_shopping", "seniority_semantic"),
        degradation_notes=("freshness remains advisory provider-side",),
    )

    assert plan.canonical_profile_ref == "source-search-strategy.v1"
    assert plan.derived_provider_params == {"q": "python automation", "sinceDate": "_15_DAYS"}
    assert plan.pushed_down_filters == ("search_terms", "freshness_window")
    assert plan.provider_filter_mappings == (
        ProviderFilterMapping(canonical_filter_key="search_terms", provider_param="q"),
        ProviderFilterMapping(canonical_filter_key="freshness_window", provider_param="sinceDate"),
    )
    assert plan.post_fetch_filters == (
        "geography_modality",
        "consultancy_body_shopping",
        "seniority_semantic",
    )
    assert plan.degradation_notes == ("freshness remains advisory provider-side",)
