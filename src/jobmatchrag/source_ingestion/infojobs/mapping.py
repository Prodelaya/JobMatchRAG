from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..contracts import (
    CanonicalFamilyIntent,
    CanonicalLanguage,
    CanonicalSearchHandoff,
    MappingDegradation,
    OriginSideExclusion,
    ParameterProjection,
    ProjectionTrustLevel,
    ProviderExecutionPlan,
    ProviderFamilyPlan,
    ProviderFilterMapping,
)


@dataclass(frozen=True, slots=True)
class InfoJobsExecutionPlan:
    canonical_profile_ref: str
    family_plans: tuple[ProviderFamilyPlan, ...]
    post_fetch_filters: tuple[str, ...]
    degradation_notes: tuple[str, ...]

    @property
    def derived_provider_params(self) -> dict[str, Any]:
        if not self.family_plans:
            return {}
        shared_params = dict(self.family_plans[0].provider_params)
        for family_plan in self.family_plans[1:]:
            shared_params = {
                key: value
                for key, value in shared_params.items()
                if family_plan.provider_params.get(key) == value
            }
        return shared_params

    @property
    def pushed_down_filters(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                projection.canonical_source
                for family_plan in self.family_plans
                for projection in family_plan.parameter_projections
            )
        )

    @property
    def provider_filter_mappings(self) -> tuple[ProviderFilterMapping, ...]:
        seen: set[tuple[str, str]] = set()
        mappings: list[ProviderFilterMapping] = []
        for family_plan in self.family_plans:
            for projection in family_plan.parameter_projections:
                key = (projection.canonical_source, projection.provider_param)
                if key in seen:
                    continue
                seen.add(key)
                mappings.append(
                    ProviderFilterMapping(
                        canonical_filter_key=projection.canonical_source,
                        provider_param=projection.provider_param,
                    )
                )
        return tuple(mappings)


def map_canonical_handoff_to_infojobs(
    handoff: CanonicalSearchHandoff,
    *,
    provider_filters: dict[str, Any],
    supported_filters: frozenset[str],
) -> InfoJobsExecutionPlan:
    family_plans = tuple(
        family_plan
        for family in handoff.search_families
        for family_plan in _family_plans_for_intent(family, provider_filters, supported_filters)
    )
    return InfoJobsExecutionPlan(
        canonical_profile_ref=handoff.profile_id,
        family_plans=family_plans,
        post_fetch_filters=(
            "geography_modality",
            "consultancy_body_shopping",
            "seniority_semantic",
            "freshness_reliable",
        ),
        degradation_notes=(
            "InfoJobs params remain projection artifacts; canonical meaning stays authoritative.",
        ),
    )


def map_canonical_handoff_to_provider_execution_plan(
    handoff: CanonicalSearchHandoff,
    *,
    provider_filters: dict[str, Any],
    supported_filters: frozenset[str],
) -> ProviderExecutionPlan:
    infojobs_plan = map_canonical_handoff_to_infojobs(
        handoff,
        provider_filters=provider_filters,
        supported_filters=supported_filters,
    )
    return ProviderExecutionPlan(
        canonical_profile_ref=infojobs_plan.canonical_profile_ref,
        derived_provider_params=infojobs_plan.derived_provider_params,
        family_plans=infojobs_plan.family_plans,
        pushed_down_filters=infojobs_plan.pushed_down_filters,
        provider_filter_mappings=infojobs_plan.provider_filter_mappings,
        post_fetch_filters=infojobs_plan.post_fetch_filters,
        degradation_notes=infojobs_plan.degradation_notes,
    )


def _family_plans_for_intent(
    family: CanonicalFamilyIntent,
    provider_filters: dict[str, Any],
    supported_filters: frozenset[str],
) -> tuple[ProviderFamilyPlan, ...]:
    return tuple(
        _build_family_plan(
            family,
            language_variant,
            provider_filters=provider_filters,
            supported_filters=supported_filters,
        )
        for language_variant in family.language_variants
    )


def _build_family_plan(
    family: CanonicalFamilyIntent,
    language_variant: Any,
    *,
    provider_filters: dict[str, Any],
    supported_filters: frozenset[str],
) -> ProviderFamilyPlan:
    q_terms = _build_q_terms(family, language_variant.language, baseline_terms=tuple(language_variant.baseline_terms))
    reinforcement_terms = _build_reinforcement_terms(family, language_variant.language)
    provider_params: dict[str, Any] = {}
    parameter_projections: list[ParameterProjection] = []
    degradations: list[MappingDegradation] = []
    pending_post_fetch_checks: list[str] = []

    if "q" in supported_filters:
        provider_params["q"] = " ".join((*q_terms, *reinforcement_terms)).strip()
        parameter_projections.append(
            ParameterProjection(
                canonical_source="family",
                provider_param="q",
                value=provider_params["q"],
                trust_level=ProjectionTrustLevel.PRIMARY,
                rationale="Role-intent phrases stay canonical and q is only a discovery hint.",
            )
        )

    _append_supported_projection(
        provider_filters,
        supported_filters,
        provider_params,
        parameter_projections,
        canonical_source="seniority_semantic",
        provider_param="experienceMin",
        trust_level=ProjectionTrustLevel.PARTIAL_STRONG,
        rationale="Experience remains a partial-but-strong hint; seniority stays canonical.",
    )
    if "experienceMin" in provider_params:
        pending_post_fetch_checks.append("seniority_semantic")
        degradations.append(
            MappingDegradation(
                semantic_key="seniority_semantic",
                reason_code="experience_hint_only",
                kept_post_fetch_as="seniority_semantic",
            )
        )

    _append_supported_projection(
        provider_filters,
        supported_filters,
        provider_params,
        parameter_projections,
        canonical_source="freshness",
        provider_param="sinceDate",
        trust_level=ProjectionTrustLevel.OPTIMIZATION_ONLY,
        rationale="Freshness pushdown is an optimization only.",
    )
    _append_supported_projection(
        provider_filters,
        supported_filters,
        provider_params,
        parameter_projections,
        canonical_source="geography_modality",
        provider_param="teleworking",
        trust_level=ProjectionTrustLevel.SUPPORT_ONLY,
        rationale="Teleworking narrows noise but never becomes decisive authority.",
    )
    if "teleworking" in provider_params:
        pending_post_fetch_checks.append("geography_modality")
        degradations.append(
            MappingDegradation(
                semantic_key="geography_modality",
                reason_code="teleworking_support_only",
                kept_post_fetch_as="geography_modality",
            )
        )

    for provider_param in ("category", "subcategory"):
        _append_supported_projection(
            provider_filters,
            supported_filters,
            provider_params,
            parameter_projections,
            canonical_source="family_context",
            provider_param=provider_param,
            trust_level=ProjectionTrustLevel.CONTEXTUAL,
            rationale="InfoJobs taxonomy only provides context around a canonical family.",
        )

    origin_exclusions: tuple[OriginSideExclusion, ...] = ()
    if family.family_key == "ai_automation":
        origin_exclusions = (
            OriginSideExclusion(token="odoo", reason="Reduce adjacent ERP noise in AI family queries"),
        )

    return ProviderFamilyPlan(
        family_key=family.family_key,
        language=language_variant.language,
        query_label=_query_label_for_language(language_variant.language),
        q_terms=q_terms,
        reinforcement_terms=reinforcement_terms,
        provider_params=provider_params,
        parameter_projections=tuple(parameter_projections),
        origin_exclusions=origin_exclusions,
        degradations=tuple(degradations),
        pending_post_fetch_checks=tuple(dict.fromkeys(pending_post_fetch_checks)),
    )


def _append_supported_projection(
    provider_filters: dict[str, Any],
    supported_filters: frozenset[str],
    provider_params: dict[str, Any],
    parameter_projections: list[ParameterProjection],
    *,
    canonical_source: str,
    provider_param: str,
    trust_level: ProjectionTrustLevel,
    rationale: str,
) -> None:
    value = provider_filters.get(provider_param)
    if provider_param not in supported_filters or value is None:
        return
    provider_params[provider_param] = value
    parameter_projections.append(
        ParameterProjection(
            canonical_source=canonical_source,
            provider_param=provider_param,
            value=value,
            trust_level=trust_level,
            rationale=rationale,
        )
    )


def _query_label_for_language(language: CanonicalLanguage) -> str:
    return {
        CanonicalLanguage.ES: "es-baseline",
        CanonicalLanguage.EN: "en-baseline",
        CanonicalLanguage.MIXED: "mixed-probe",
    }[language]


def _build_q_terms(
    family: CanonicalFamilyIntent,
    language: CanonicalLanguage,
    *,
    baseline_terms: tuple[str, ...],
) -> tuple[str, ...]:
    role_terms = _role_variants_for_language(family, language)
    return tuple(dict.fromkeys((*role_terms, *baseline_terms)))


def _build_reinforcement_terms(
    family: CanonicalFamilyIntent,
    language: CanonicalLanguage,
) -> tuple[str, ...]:
    allowed_modes = {"reinforcement"}
    if language is CanonicalLanguage.MIXED:
        allowed_modes.add("tactical_probe")
    return tuple(
        dict.fromkeys(
            term
            for reinforcement in family.reinforcements
            if reinforcement.mode in allowed_modes
            for term in reinforcement.terms[:1]
        )
    )


def _role_variants_for_language(
    family: CanonicalFamilyIntent,
    language: CanonicalLanguage,
) -> tuple[str, ...]:
    if language is CanonicalLanguage.MIXED:
        return family.role_variants

    language_tag = language.value
    matching = tuple(
        variant
        for variant in family.role_variants
        if _classify_role_variant_language(variant) in {language_tag, "unknown"}
    )
    if matching:
        return matching
    return family.role_variants


def _classify_role_variant_language(role_variant: str) -> str:
    normalized = role_variant.casefold()
    if any(token in normalized for token in ("desarrollador", "automatización", "consultor", "herramientas internas")):
        return "es"
    if any(token in normalized for token in ("engineer", "developer", "internal tools", "builder")):
        return "en"
    return "unknown"
