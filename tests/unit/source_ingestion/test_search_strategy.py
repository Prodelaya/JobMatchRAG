from __future__ import annotations

from jobmatchrag.source_ingestion.contracts import CanonicalLanguage
from jobmatchrag.source_ingestion import build_capture_profile as exported_build_capture_profile
from jobmatchrag.source_ingestion import load_curated_datasets as exported_load_curated_datasets
from jobmatchrag.source_ingestion.data_loader import load_curated_datasets
from jobmatchrag.source_ingestion.search_strategy import (
    build_capture_profile,
    evaluate_offer,
)


def test_capture_profile_exposes_three_canonical_families_and_provider_params_stay_non_authoritative() -> None:
    profile = build_capture_profile()
    ai_family = next(family for family in profile.search_families if family.family_key == "ai_automation")

    assert tuple(family.family_key for family in profile.search_families) == (
        "ai_automation",
        "automation",
        "adjacent_odoo",
    )
    assert profile.target_filters == (
        "geography_modality",
        "consultancy_body_shopping",
        "seniority_semantic",
        "freshness_reliable",
    )
    assert tuple(variant.language for variant in ai_family.language_variants) == (
        CanonicalLanguage.ES,
        CanonicalLanguage.EN,
        CanonicalLanguage.MIXED,
    )
    assert ai_family.language_variants[2].mixed_with == (CanonicalLanguage.ES, CanonicalLanguage.EN)
    assert ai_family.language_variants[2].rationale == "Cross-language tactical probe for mixed-market postings"
    assert tuple(reinforcement.key for reinforcement in ai_family.reinforcements) == (
        "python",
        "apis",
        "bots",
        "llm_tooling",
    )
    assert tuple(reinforcement.mode for reinforcement in ai_family.reinforcements) == (
        "reinforcement",
        "reinforcement",
        "tactical_probe",
        "tactical_probe",
    )
    assert not hasattr(ai_family, "provider_params")
    assert profile.profile_id == "source-search-strategy.v1"


def test_hybrid_city_dataset_supports_seeded_city_alias_lookup() -> None:
    datasets = load_curated_datasets()

    barcelona = datasets.hybrid_cities.lookup("barna")
    unknown = datasets.hybrid_cities.lookup("lugo")

    assert barcelona is not None
    assert barcelona.city_key == "barcelona"
    assert barcelona.dataset_version == datasets.hybrid_cities.dataset_version
    assert unknown is None


def test_package_exports_stable_strategy_helpers() -> None:
    assert exported_build_capture_profile().profile_id == "source-search-strategy.v1"
    assert exported_load_curated_datasets().hybrid_cities.dataset_version == "2026.04.1"


def test_hybrid_offer_passes_when_attendance_is_under_three_days_in_seeded_city() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-1",
            "title": "Backend Automation Engineer",
            "modality": "hybrid",
            "city": "Barcelona",
            "country": "Spain",
            "attendance_days_per_month": 2,
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    geography = next(item for item in outcome.outcomes if item.filter_key == "geography_modality")

    assert outcome.decision == "passed"
    assert geography.status == "passed"
    assert geography.evidence_refs[0].dataset_version == "2026.04.1"


def test_hybrid_curated_city_without_reliable_spain_evidence_stays_ambiguous() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-1b",
            "title": "Backend Automation Engineer",
            "modality": "hybrid",
            "city": "Barcelona",
            "attendance_days_per_month": 2,
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    geography = next(item for item in outcome.outcomes if item.filter_key == "geography_modality")

    assert outcome.decision == "ambiguous"
    assert geography.status == "ambiguous"
    assert geography.reason_code == "hybrid_city_country_unverified"


def test_onsite_madrid_with_explicit_non_spain_country_is_excluded() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-1c",
            "title": "Automation Engineer",
            "modality": "onsite",
            "city": "Madrid",
            "country": "Portugal",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    geography = next(item for item in outcome.outcomes if item.filter_key == "geography_modality")

    assert outcome.decision == "excluded"
    assert geography.status == "excluded"
    assert geography.reason_code == "onsite_madrid_outside_spain"


def test_hybrid_offer_stays_ambiguous_when_city_is_not_in_seeded_dataset() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-2",
            "title": "Automation Engineer",
            "modality": "hybrid",
            "city": "Lugo",
            "country": "Spain",
            "attendance_days_per_month": 2,
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    geography = next(item for item in outcome.outcomes if item.filter_key == "geography_modality")

    assert outcome.decision == "ambiguous"
    assert geography.status == "ambiguous"
    assert geography.reason_code == "hybrid_city_not_curated"


def test_hybrid_offer_without_attendance_stays_ambiguous() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-2b",
            "title": "Automation Engineer",
            "modality": "hybrid",
            "city": "Barcelona",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    geography = next(item for item in outcome.outcomes if item.filter_key == "geography_modality")

    assert outcome.decision == "ambiguous"
    assert geography.status == "ambiguous"
    assert geography.reason_code == "hybrid_attendance_missing"


def test_explicit_consultancy_language_triggers_exclusion() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-3",
            "title": "Consultor IA para clientes",
            "description": "Buscamos consultora para proyectos de clientes y staffing.",
            "company": "Boutique Delivery",
            "modality": "remote",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    consultancy = next(item for item in outcome.outcomes if item.filter_key == "consultancy_body_shopping")

    assert outcome.decision == "excluded"
    assert consultancy.status == "excluded"
    assert consultancy.reason_code == "explicit_consultancy_signal"


def test_negated_consultancy_phrase_does_not_trigger_hard_exclusion() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-3a",
            "title": "Automation Engineer",
            "description": "Rol de cliente final, no consultora. Plataforma interna.",
            "company": "Product Corp",
            "modality": "remote",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    consultancy = next(item for item in outcome.outcomes if item.filter_key == "consultancy_body_shopping")

    assert outcome.decision == "passed"
    assert consultancy.status == "passed"
    assert consultancy.reason_code == "no_consultancy_evidence"


def test_explicit_seniority_language_triggers_post_fetch_exclusion() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-3b",
            "title": "Senior Automation Engineer",
            "description": "Internal platform automation role.",
            "company": "Product Corp",
            "modality": "remote",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    seniority = next(item for item in outcome.outcomes if item.filter_key == "seniority_semantic")

    assert outcome.decision == "excluded"
    assert seniority.status == "excluded"
    assert seniority.reason_code == "explicit_seniority_signal"


def test_reliably_stale_offer_triggers_post_fetch_exclusion() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-3c",
            "title": "Automation Engineer",
            "description": "Internal platform automation role.",
            "company": "Product Corp",
            "modality": "remote",
            "country": "Spain",
            "published_at": "2026-03-20T10:00:00+00:00",
            "evaluated_at": "2026-04-16T10:00:00+00:00",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    freshness = next(item for item in outcome.outcomes if item.filter_key == "freshness_reliable")

    assert outcome.decision == "excluded"
    assert freshness.status == "excluded"
    assert freshness.reason_code == "published_more_than_15_days_ago"


def test_offer_older_than_fifteen_days_by_minutes_is_excluded() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-3d",
            "title": "Automation Engineer",
            "description": "Internal platform automation role.",
            "company": "Product Corp",
            "modality": "remote",
            "country": "Spain",
            "published_at": "2026-04-01T09:59:00+00:00",
            "evaluated_at": "2026-04-16T10:00:00+00:00",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    freshness = next(item for item in outcome.outcomes if item.filter_key == "freshness_reliable")

    assert outcome.decision == "excluded"
    assert freshness.status == "excluded"
    assert freshness.reason_code == "published_more_than_15_days_ago"


def test_update_only_timestamp_does_not_count_as_reliable_publication_evidence() -> None:
    outcome = evaluate_offer(
        {
            "source_offer_id": "offer-3e",
            "captures": {
                "list": {
                    "payload": {
                        "id": "offer-3e",
                        "title": "Automation Engineer",
                        "city": "Madrid",
                        "countryName": "Spain",
                        "teleworking": "remote",
                        "updatedAt": "2026-03-20T10:00:00+00:00",
                        "author": "Product Corp",
                    },
                    "observed_at": "2026-04-16T10:00:00+00:00",
                }
            },
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    freshness = next(item for item in outcome.outcomes if item.filter_key == "freshness_reliable")

    assert outcome.decision == "passed"
    assert freshness.status == "passed"
    assert freshness.reason_code == "freshness_not_reliable"


def test_known_consultancy_company_without_text_proof_stays_ambiguous() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-4",
            "title": "Automation Engineer",
            "description": "Plataforma interna de operaciones.",
            "company": "Accenture",
            "modality": "remote",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    consultancy = next(item for item in outcome.outcomes if item.filter_key == "consultancy_body_shopping")

    assert outcome.decision == "ambiguous"
    assert consultancy.status == "ambiguous"
    assert consultancy.reason_code == "known_company_signal_only"
    assert consultancy.evidence_refs[0].dataset_version == "2026.04.1"


def test_known_consultancy_lookup_falls_back_to_employer_when_company_is_missing() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-4b",
            "title": "Automation Engineer",
            "description": "Plataforma interna de operaciones.",
            "employer": "Accenture",
            "modality": "remote",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    consultancy = next(item for item in outcome.outcomes if item.filter_key == "consultancy_body_shopping")

    assert outcome.decision == "ambiguous"
    assert consultancy.status == "ambiguous"
    assert consultancy.reason_code == "known_company_signal_only"
    assert consultancy.evidence_refs[0].locator == "accenture"


def test_provider_shaped_raw_handoff_uses_real_infojobs_fields_for_freshness_and_company_signals() -> None:
    outcome = evaluate_offer(
        {
            "source_offer_id": "offer-5",
            "captures": {
                "list": {
                    "payload": {
                        "id": "offer-5",
                        "title": "Automation Engineer",
                        "city": "Barcelona",
                        "countryName": "Spain",
                        "teleworking": "hybrid",
                        "published": "2026-03-20T10:00:00+00:00",
                        "author": "Accenture",
                    },
                    "observed_at": "2026-04-16T10:00:00+00:00",
                },
                "detail": {
                    "payload": {
                        "id": "offer-5",
                        "description": "Plataforma interna para operaciones.",
                        "profile": {
                            "name": "Accenture",
                            "description": "Consultoría tecnológica global.",
                            "province": "Barcelona",
                            "country": "Spain",
                        },
                        "attendance_days_per_month": 2,
                    },
                    "observed_at": "2026-04-16T10:05:00+00:00",
                },
            },
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    geography = next(item for item in outcome.outcomes if item.filter_key == "geography_modality")
    consultancy = next(item for item in outcome.outcomes if item.filter_key == "consultancy_body_shopping")
    freshness = next(item for item in outcome.outcomes if item.filter_key == "freshness_reliable")

    assert outcome.decision == "excluded"
    assert geography.status == "passed"
    assert geography.reason_code == "hybrid_curated_city_allowed"
    assert consultancy.status == "excluded"
    assert consultancy.reason_code == "explicit_consultancy_signal"
    assert freshness.status == "excluded"
    assert freshness.reason_code == "published_more_than_15_days_ago"


def test_compound_negated_consultancy_terms_do_not_trigger_hard_exclusion() -> None:
    outcome = evaluate_offer(
        {
            "id": "offer-5b",
            "title": "Automation Engineer",
            "description": "Cliente final, no consultoría ni outsourcing. Producto interno.",
            "company": "Product Corp",
            "modality": "remote",
            "country": "Spain",
        },
        profile=build_capture_profile(),
        datasets=load_curated_datasets(),
    )

    consultancy = next(item for item in outcome.outcomes if item.filter_key == "consultancy_body_shopping")

    assert outcome.decision == "passed"
    assert consultancy.status == "passed"
    assert consultancy.reason_code == "no_consultancy_evidence"
