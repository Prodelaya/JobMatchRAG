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


class CanonicalLanguage(StrEnum):
    ES = "es"
    EN = "en"
    MIXED = "mixed"


class ProjectionTrustLevel(StrEnum):
    PRIMARY = "primary"
    PARTIAL_STRONG = "partial_strong"
    CONTEXTUAL = "contextual"
    SUPPORT_ONLY = "support_only"
    OPTIMIZATION_ONLY = "optimization_only"


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


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_type: str
    locator: str
    dataset_version: str | None = None
    confidence: str | None = None


@dataclass(frozen=True, slots=True)
class ReferenceDatasetSnapshot:
    dataset_key: str
    dataset_version: str
    loaded_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CanonicalFilterOutcome:
    filter_key: str
    status: str
    reason_code: str
    evidence_refs: tuple[EvidenceRef, ...] = ()
    applied_stage: str = "post_fetch"
    policy_version: str = "source-search-strategy.v1"


@dataclass(frozen=True, slots=True)
class ProviderFilterMapping:
    canonical_filter_key: str
    provider_param: str


@dataclass(frozen=True, slots=True)
class ProviderRequestPlanIdentity:
    family_key: str
    language: CanonicalLanguage
    query_label: str


@dataclass(frozen=True, slots=True)
class LanguageVariant:
    language: CanonicalLanguage
    baseline_terms: tuple[str, ...]
    mixed_with: tuple[CanonicalLanguage, ...] = ()
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class TechnologyReinforcement:
    key: str
    terms: tuple[str, ...]
    mode: str = "reinforcement"
    optional: bool = True


@dataclass(frozen=True, slots=True)
class CanonicalFamilyIntent:
    family_key: str
    intent_label: str
    role_variants: tuple[str, ...]
    language_variants: tuple[LanguageVariant, ...]
    reinforcements: tuple[TechnologyReinforcement, ...] = ()
    target_filters: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CanonicalSearchHandoff:
    profile_id: str
    search_families: tuple[CanonicalFamilyIntent, ...]
    target_filters: tuple[str, ...]
    ambiguity_policy: str


@dataclass(frozen=True, slots=True)
class ParameterProjection:
    canonical_source: str
    provider_param: str
    value: Any
    trust_level: ProjectionTrustLevel
    rationale: str
    authority: str = "canonical"


@dataclass(frozen=True, slots=True)
class MappingDegradation:
    semantic_key: str
    reason_code: str
    kept_post_fetch_as: str
    severity: str = "expected"


@dataclass(frozen=True, slots=True)
class OriginSideExclusion:
    token: str
    reason: str
    aggressiveness: str = "light"


@dataclass(frozen=True, slots=True)
class ProviderFamilyPlan:
    family_key: str
    language: CanonicalLanguage
    query_label: str
    q_terms: tuple[str, ...]
    reinforcement_terms: tuple[str, ...] = ()
    provider_params: dict[str, Any] = field(default_factory=dict)
    parameter_projections: tuple[ParameterProjection, ...] = ()
    origin_exclusions: tuple[OriginSideExclusion, ...] = ()
    degradations: tuple[MappingDegradation, ...] = ()
    pending_post_fetch_checks: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProviderExecutionPlan:
    canonical_profile_ref: str
    derived_provider_params: dict[str, Any] = field(default_factory=dict)
    family_plans: tuple[ProviderFamilyPlan, ...] = ()
    pushed_down_filters: tuple[str, ...] = ()
    provider_filter_mappings: tuple[ProviderFilterMapping, ...] = ()
    post_fetch_filters: tuple[str, ...] = ()
    degradation_notes: tuple[str, ...] = ()


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
    request_plan: dict[str, str] | None
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
