from __future__ import annotations

from jobmatchrag.source_ingestion.search_strategy import build_capture_profile
from jobmatchrag.source_ingestion.contracts import CanonicalLanguage, ProjectionTrustLevel
from jobmatchrag.source_ingestion.infojobs.mapping import map_canonical_handoff_to_infojobs


def test_mapper_builds_bilingual_family_plans_and_explicit_mixed_probe() -> None:
    plan = map_canonical_handoff_to_infojobs(
        build_capture_profile(),
        provider_filters={"sinceDate": "_24_HOURS", "experienceMin": "1", "teleworking": "remote"},
        supported_filters=frozenset({"q", "sinceDate", "experienceMin", "teleworking"}),
    )

    ai_plans = [family_plan for family_plan in plan.family_plans if family_plan.family_key == "ai_automation"]

    assert [family_plan.query_label for family_plan in ai_plans] == ["es-baseline", "en-baseline", "mixed-probe"]
    assert [family_plan.language for family_plan in ai_plans] == [
        CanonicalLanguage.ES,
        CanonicalLanguage.EN,
        CanonicalLanguage.MIXED,
    ]
    assert ai_plans[0].q_terms[:2] == (
        "Desarrollador Python de automatización/IA",
        "automatización",
    )
    assert ai_plans[0].reinforcement_terms == ("python", "apis")
    assert ai_plans[2].q_terms[:3] == (
        "AI Engineer",
        "AI Automation Engineer",
        "Desarrollador Python de automatización/IA",
    )
    assert ai_plans[2].reinforcement_terms == ("python", "apis", "bots", "llm")
    assert ai_plans[2].provider_params["q"].startswith("AI Engineer AI Automation Engineer")


def test_mapper_assigns_trust_levels_and_keeps_degraded_semantics_post_fetch() -> None:
    plan = map_canonical_handoff_to_infojobs(
        build_capture_profile(),
        provider_filters={
            "experienceMin": "1",
            "sinceDate": "_7_DAYS",
            "teleworking": "hybrid",
            "category": "informatica-telecomunicaciones",
        },
        supported_filters=frozenset({"q", "experienceMin", "sinceDate", "teleworking", "category"}),
    )

    es_plan = next(
        family_plan
        for family_plan in plan.family_plans
        if family_plan.family_key == "automation" and family_plan.query_label == "es-baseline"
    )
    projections = {projection.provider_param: projection for projection in es_plan.parameter_projections}

    assert projections["q"].trust_level is ProjectionTrustLevel.PRIMARY
    assert projections["experienceMin"].trust_level is ProjectionTrustLevel.PARTIAL_STRONG
    assert projections["sinceDate"].trust_level is ProjectionTrustLevel.OPTIMIZATION_ONLY
    assert projections["teleworking"].trust_level is ProjectionTrustLevel.SUPPORT_ONLY
    assert projections["category"].trust_level is ProjectionTrustLevel.CONTEXTUAL
    assert es_plan.pending_post_fetch_checks == ("seniority_semantic", "geography_modality")
    assert [degradation.semantic_key for degradation in es_plan.degradations] == [
        "seniority_semantic",
        "geography_modality",
    ]
    assert [(mapping.canonical_filter_key, mapping.provider_param) for mapping in plan.provider_filter_mappings] == [
        ("family", "q"),
        ("seniority_semantic", "experienceMin"),
        ("freshness", "sinceDate"),
        ("geography_modality", "teleworking"),
        ("family_context", "category"),
    ]


def test_mapper_uses_light_origin_exclusions_only_for_known_noise_combinations() -> None:
    plan = map_canonical_handoff_to_infojobs(
        build_capture_profile(),
        provider_filters={},
        supported_filters=frozenset({"q"}),
    )

    ai_es_plan = next(
        family_plan
        for family_plan in plan.family_plans
        if family_plan.family_key == "ai_automation" and family_plan.query_label == "es-baseline"
    )
    adjacent_plan = next(
        family_plan
        for family_plan in plan.family_plans
        if family_plan.family_key == "adjacent_odoo" and family_plan.query_label == "es-baseline"
    )

    assert ai_es_plan.origin_exclusions[0].token == "odoo"
    assert ai_es_plan.origin_exclusions[0].aggressiveness == "light"
    assert adjacent_plan.origin_exclusions == ()
