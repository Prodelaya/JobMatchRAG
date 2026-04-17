from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import re
from typing import Any

from .contracts import (
    CanonicalFamilyIntent,
    CanonicalFilterOutcome,
    CanonicalLanguage,
    CanonicalSearchHandoff,
    EvidenceRef,
    LanguageVariant,
    ProviderExecutionPlan,
    ProviderFilterMapping,
    ReferenceDatasetSnapshot,
    TechnologyReinforcement,
)
from .data_loader import CuratedDatasets


CaptureProfile = CanonicalSearchHandoff


@dataclass(frozen=True, slots=True)
class OfferEvaluation:
    decision: str
    outcomes: tuple[CanonicalFilterOutcome, ...]
    dataset_snapshots: tuple[ReferenceDatasetSnapshot, ...]


_CONSULTANCY_SIGNALS = (
    "consultor",
    "consultora",
    "consultoría",
    "consultancy",
    "body shopping",
    "staffing",
    "outsourcing",
    "proyectos de clientes",
)

_CONSULTANCY_NEGATION_SIGNALS = (
    "cliente final, no consultora",
    "cliente final no consultora",
    "cliente final - no consultora",
    "no consultora",
    "no consultoría",
    "no consultancy",
)

_SENIORITY_SIGNALS = (
    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "staff engineer",
    "architect",
)

_FRESHNESS_MAX_AGE_DAYS = 15
_FRESHNESS_MAX_AGE = timedelta(days=_FRESHNESS_MAX_AGE_DAYS)

_CONSULTANCY_SIGNAL_PATTERN = re.compile(
    "|".join(re.escape(signal) for signal in sorted(_CONSULTANCY_SIGNALS, key=len, reverse=True))
)
_NEGATED_CONSULTANCY_SEQUENCE_PATTERN = re.compile(
    r"\bno\s+(?:"
    + "|".join(re.escape(signal) for signal in sorted(_CONSULTANCY_SIGNALS, key=len, reverse=True))
    + r")(?:\s*(?:ni|y|,|/)\s*(?:"
    + "|".join(re.escape(signal) for signal in sorted(_CONSULTANCY_SIGNALS, key=len, reverse=True))
    + r"))*",
)


def build_capture_profile() -> CaptureProfile:
    return CaptureProfile(
        profile_id="source-search-strategy.v1",
        search_families=(
            CanonicalFamilyIntent(
                family_key="ai_automation",
                intent_label="Internal automation with explicit AI/LLM/agent intent",
                role_variants=(
                    "AI Engineer",
                    "AI Automation Engineer",
                    "Desarrollador Python de automatización/IA",
                ),
                language_variants=(
                    LanguageVariant(
                        language=CanonicalLanguage.ES,
                        baseline_terms=("automatización", "ia aplicada", "herramientas internas"),
                        rationale="Spanish baseline for the local market",
                    ),
                    LanguageVariant(
                        language=CanonicalLanguage.EN,
                        baseline_terms=("automation", "applied ai", "internal tools"),
                        rationale="English baseline for internationally posted roles",
                    ),
                    LanguageVariant(
                        language=CanonicalLanguage.MIXED,
                        baseline_terms=("ai automation engineer", "automatización"),
                        mixed_with=(CanonicalLanguage.ES, CanonicalLanguage.EN),
                        rationale="Cross-language tactical probe for mixed-market postings",
                    ),
                ),
                reinforcements=(
                    TechnologyReinforcement(key="python", terms=("python", "python3")),
                    TechnologyReinforcement(key="apis", terms=("apis", "integraciones api")),
                    TechnologyReinforcement(key="bots", terms=("bots", "chatbots"), mode="tactical_probe"),
                    TechnologyReinforcement(
                        key="llm_tooling",
                        terms=("llm", "agents", "ai tooling"),
                        mode="tactical_probe",
                    ),
                ),
                target_filters=(
                    "geography_modality",
                    "consultancy_body_shopping",
                    "seniority_semantic",
                    "freshness_reliable",
                ),
            ),
            CanonicalFamilyIntent(
                family_key="automation",
                intent_label="Internal automation without explicit AI semantics",
                role_variants=(
                    "Automation Builder",
                    "Internal Tools Developer",
                    "Automation Engineer",
                ),
                language_variants=(
                    LanguageVariant(
                        language=CanonicalLanguage.ES,
                        baseline_terms=("automatización", "integraciones", "procesos internos"),
                        rationale="Spanish baseline for non-AI automation roles",
                    ),
                    LanguageVariant(
                        language=CanonicalLanguage.EN,
                        baseline_terms=("automation", "workflow", "internal tools"),
                        rationale="English baseline for non-AI automation roles",
                    ),
                ),
                reinforcements=(
                    TechnologyReinforcement(key="python", terms=("python",)),
                    TechnologyReinforcement(key="apis", terms=("api", "rest")),
                ),
                target_filters=(
                    "geography_modality",
                    "consultancy_body_shopping",
                    "seniority_semantic",
                    "freshness_reliable",
                ),
            ),
            CanonicalFamilyIntent(
                family_key="adjacent_odoo",
                intent_label="Adjacent Odoo opportunities kept separate from core automation",
                role_variants=("Odoo Developer", "Odoo Technical Consultant"),
                language_variants=(
                    LanguageVariant(
                        language=CanonicalLanguage.ES,
                        baseline_terms=("odoo", "erp"),
                        rationale="Spanish adjacent baseline",
                    ),
                    LanguageVariant(
                        language=CanonicalLanguage.EN,
                        baseline_terms=("odoo", "erp"),
                        rationale="English adjacent baseline",
                    ),
                ),
                reinforcements=(
                    TechnologyReinforcement(key="python", terms=("python",)),
                ),
                target_filters=(
                    "geography_modality",
                    "consultancy_body_shopping",
                    "seniority_semantic",
                    "freshness_reliable",
                ),
            ),
        ),
        target_filters=(
            "geography_modality",
            "consultancy_body_shopping",
            "seniority_semantic",
            "freshness_reliable",
        ),
        ambiguity_policy="preserve unless incompatibility is explicit/reliable",
    )


def evaluate_offer(
    offer: dict[str, Any], *, profile: CaptureProfile, datasets: CuratedDatasets
) -> OfferEvaluation:
    del profile
    normalized_offer = _extract_offer_view(offer)
    outcomes = (
        _evaluate_geography(normalized_offer, datasets),
        _evaluate_consultancy(normalized_offer, datasets),
        _evaluate_seniority(normalized_offer),
        _evaluate_freshness(normalized_offer),
    )
    decision = "passed"
    if any(item.status == "excluded" for item in outcomes):
        decision = "excluded"
    elif any(item.status == "ambiguous" for item in outcomes):
        decision = "ambiguous"
    return OfferEvaluation(
        decision=decision,
        outcomes=outcomes,
        dataset_snapshots=(
            ReferenceDatasetSnapshot(
                dataset_key="hybrid_cities",
                dataset_version=datasets.hybrid_cities.dataset_version,
            ),
            ReferenceDatasetSnapshot(
                dataset_key="known_consultancies",
                dataset_version=datasets.known_consultancies.dataset_version,
            ),
        ),
    )


def build_provider_execution_plan(
    *, profile: CaptureProfile, provider_filters: dict[str, Any], supported_filters: frozenset[str]
) -> ProviderExecutionPlan:
    derived_provider_params = {
        key: value for key, value in provider_filters.items() if key in supported_filters and value is not None
    }
    provider_filter_mappings = tuple(
        ProviderFilterMapping(
            canonical_filter_key=_canonical_filter_for_provider_param(key),
            provider_param=key,
        )
        for key in derived_provider_params
    )
    return ProviderExecutionPlan(
        canonical_profile_ref=profile.profile_id,
        derived_provider_params=derived_provider_params,
        pushed_down_filters=_dedupe_preserving_order(
            mapping.canonical_filter_key for mapping in provider_filter_mappings
        ),
        provider_filter_mappings=provider_filter_mappings,
        post_fetch_filters=(
            "geography_modality",
            "consultancy_body_shopping",
            "seniority_semantic",
            "freshness_reliable",
        ),
        degradation_notes=(
            "provider params remain execution details; unsupported canonical filters stay post-fetch",
        ),
    )


def _evaluate_geography(offer: dict[str, Any], datasets: CuratedDatasets) -> CanonicalFilterOutcome:
    modality = str(offer.get("modality", "")).casefold()
    city = offer.get("city")
    country = str(offer.get("country", "")).casefold()
    attendance = offer.get("attendance_days_per_month")
    if modality == "remote" and country == "spain":
        return CanonicalFilterOutcome(filter_key="geography_modality", status="passed", reason_code="remote_spain")
    if modality == "onsite":
        if str(city).casefold() == "madrid":
            if _is_reliable_spain(country):
                return CanonicalFilterOutcome(
                    filter_key="geography_modality", status="passed", reason_code="onsite_madrid"
                )
            if _is_explicitly_non_spain(country):
                return CanonicalFilterOutcome(
                    filter_key="geography_modality",
                    status="excluded",
                    reason_code="onsite_madrid_outside_spain",
                )
            return CanonicalFilterOutcome(
                filter_key="geography_modality",
                status="ambiguous",
                reason_code="onsite_madrid_country_unverified",
            )
        return CanonicalFilterOutcome(filter_key="geography_modality", status="excluded", reason_code="onsite_outside_madrid")
    if modality == "hybrid":
        if str(city).casefold() == "madrid":
            if isinstance(attendance, int) and attendance < 3:
                if _is_reliable_spain(country):
                    return CanonicalFilterOutcome(
                        filter_key="geography_modality",
                        status="passed",
                        reason_code="hybrid_madrid_low_attendance",
                    )
                if _is_explicitly_non_spain(country):
                    return CanonicalFilterOutcome(
                        filter_key="geography_modality",
                        status="excluded",
                        reason_code="hybrid_madrid_outside_spain",
                    )
                return CanonicalFilterOutcome(
                    filter_key="geography_modality",
                    status="ambiguous",
                    reason_code="hybrid_madrid_country_unverified",
                )
            if isinstance(attendance, int):
                return CanonicalFilterOutcome(filter_key="geography_modality", status="excluded", reason_code="hybrid_attendance_too_high")
            return CanonicalFilterOutcome(filter_key="geography_modality", status="ambiguous", reason_code="hybrid_attendance_missing")
        if isinstance(attendance, int) and attendance < 3:
            if _is_explicitly_non_spain(country):
                return CanonicalFilterOutcome(
                    filter_key="geography_modality",
                    status="excluded",
                    reason_code="hybrid_city_outside_spain",
                )
            if not _is_reliable_spain(country):
                return CanonicalFilterOutcome(
                    filter_key="geography_modality",
                    status="ambiguous",
                    reason_code="hybrid_city_country_unverified",
                )
            record = datasets.hybrid_cities.lookup(city if isinstance(city, str) else None)
            if record is not None:
                return CanonicalFilterOutcome(
                    filter_key="geography_modality",
                    status="passed",
                    reason_code="hybrid_curated_city_allowed",
                    evidence_refs=(
                        EvidenceRef(
                            evidence_type="hybrid_city_dataset",
                            locator=record.city_key,
                            dataset_version=record.dataset_version,
                            confidence="curated",
                        ),
                    ),
                )
            return CanonicalFilterOutcome(
                filter_key="geography_modality",
                status="ambiguous",
                reason_code="hybrid_city_not_curated",
            )
        if isinstance(attendance, int):
            return CanonicalFilterOutcome(filter_key="geography_modality", status="excluded", reason_code="hybrid_attendance_too_high")
        return CanonicalFilterOutcome(filter_key="geography_modality", status="ambiguous", reason_code="hybrid_attendance_missing")
    return CanonicalFilterOutcome(filter_key="geography_modality", status="ambiguous", reason_code="modality_not_reliable")


def _extract_offer_view(offer: dict[str, Any]) -> dict[str, Any]:
    if "captures" not in offer:
        return offer
    captures = offer.get("captures")
    if not isinstance(captures, dict):
        return offer
    detail_capture = captures.get("detail") or captures.get("DETAIL")
    list_capture = captures.get("list") or captures.get("LIST")
    detail_payload = _capture_payload(detail_capture)
    list_payload = _capture_payload(list_capture)
    payload = {**list_payload, **detail_payload}
    profile_candidate = payload.get("profile")
    profile_payload: dict[str, Any] = profile_candidate if isinstance(profile_candidate, dict) else {}
    company_value = (
        payload.get("company")
        or payload.get("companyName")
        or payload.get("author")
        or profile_payload.get("name")
    )
    city_value = payload.get("city") or payload.get("cityPD") or payload.get("province") or profile_payload.get("province")
    modality_value = payload.get("modality")
    if modality_value is None and isinstance(payload.get("teleworking"), str):
        modality_value = payload["teleworking"]
    return {
        "id": offer.get("source_offer_id") or payload.get("id"),
        "title": payload.get("title"),
        "description": payload.get("description"),
        "company": _extract_named_value(company_value),
        "company_description": payload.get("company_description") or profile_payload.get("description"),
        "employer": payload.get("employer") or profile_payload.get("name"),
        "city": _extract_named_value(city_value),
        "country": _extract_named_value(payload.get("country")) or payload.get("countryName") or profile_payload.get("country"),
        "modality": modality_value,
        "attendance_days_per_month": payload.get("attendance_days_per_month"),
        "published_at": _first_present_value(
            payload,
            "published_at",
            "publishedAt",
            "published",
            "creationDate",
        ),
        "updated_at": _first_present_value(payload, "updatedAt", "updateDate", "updated"),
        "evaluated_at": offer.get("evaluated_at")
        or offer.get("fetched_at")
        or offer.get("observed_at")
        or payload.get("evaluated_at")
        or payload.get("fetched_at")
        or payload.get("observed_at")
        or _capture_observed_at(detail_capture)
        or _capture_observed_at(list_capture),
    }


def _capture_payload(capture: Any) -> dict[str, Any]:
    if not isinstance(capture, dict):
        return {}
    payload = capture.get("payload")
    return payload if isinstance(payload, dict) else {}


def _extract_named_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("value") or value.get("name") or value.get("key")
    return value


def _capture_observed_at(capture: Any) -> Any:
    if not isinstance(capture, dict):
        return None
    return capture.get("observed_at")


def _first_present_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return None


def _evaluate_consultancy(offer: dict[str, Any], datasets: CuratedDatasets) -> CanonicalFilterOutcome:
    combined_text = " ".join(
        str(offer.get(key, ""))
        for key in ("title", "description", "company", "company_description", "employer")
    ).casefold()
    normalized_text = _strip_consultancy_negations(combined_text)
    if _CONSULTANCY_SIGNAL_PATTERN.search(normalized_text):
        return CanonicalFilterOutcome(
            filter_key="consultancy_body_shopping",
            status="excluded",
            reason_code="explicit_consultancy_signal",
            evidence_refs=(
                EvidenceRef(
                    evidence_type="consultancy_text",
                    locator="title_description",
                    confidence="explicit",
                ),
            ),
        )
    company_candidate = offer.get("company") if isinstance(offer.get("company"), str) else None
    employer_candidate = offer.get("employer") if isinstance(offer.get("employer"), str) else None
    record = datasets.known_consultancies.lookup(company_candidate or employer_candidate)
    if record is not None:
        return CanonicalFilterOutcome(
            filter_key="consultancy_body_shopping",
            status="ambiguous",
            reason_code="known_company_signal_only",
            evidence_refs=(
                EvidenceRef(
                    evidence_type="company_signal",
                    locator=record.company_key,
                    dataset_version=record.dataset_version,
                    confidence=record.confidence,
                ),
            ),
        )
    return CanonicalFilterOutcome(filter_key="consultancy_body_shopping", status="passed", reason_code="no_consultancy_evidence")


def _strip_consultancy_negations(text: str) -> str:
    normalized = _NEGATED_CONSULTANCY_SEQUENCE_PATTERN.sub(" ", text)
    for signal in _CONSULTANCY_NEGATION_SIGNALS:
        normalized = normalized.replace(signal, " ")
    return normalized


def _evaluate_seniority(offer: dict[str, Any]) -> CanonicalFilterOutcome:
    combined_text = " ".join(str(offer.get(key, "")) for key in ("title", "description")).casefold()
    if any(signal in combined_text for signal in _SENIORITY_SIGNALS):
        return CanonicalFilterOutcome(
            filter_key="seniority_semantic",
            status="excluded",
            reason_code="explicit_seniority_signal",
            evidence_refs=(
                EvidenceRef(
                    evidence_type="seniority_text",
                    locator="title_description",
                    confidence="explicit",
                ),
            ),
        )
    return CanonicalFilterOutcome(
        filter_key="seniority_semantic",
        status="passed",
        reason_code="seniority_not_explicit",
    )


def _evaluate_freshness(offer: dict[str, Any]) -> CanonicalFilterOutcome:
    published_at = _parse_datetime(offer.get("published_at"))
    if published_at is None:
        return CanonicalFilterOutcome(
            filter_key="freshness_reliable",
            status="passed",
            reason_code="freshness_not_reliable",
        )

    evaluated_at = _parse_datetime(offer.get("evaluated_at")) or datetime.now(UTC)
    age = evaluated_at - published_at
    if age > _FRESHNESS_MAX_AGE:
        return CanonicalFilterOutcome(
            filter_key="freshness_reliable",
            status="excluded",
            reason_code="published_more_than_15_days_ago",
            evidence_refs=(
                EvidenceRef(
                    evidence_type="published_at",
                    locator=published_at.isoformat(),
                    confidence="reliable",
                ),
            ),
        )
    return CanonicalFilterOutcome(
        filter_key="freshness_reliable",
        status="passed",
        reason_code="fresh_enough",
    )


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _is_reliable_spain(country: str) -> bool:
    return country == "spain"


def _is_explicitly_non_spain(country: str) -> bool:
    return bool(country) and country != "spain"


def _canonical_filter_for_provider_param(provider_param: str) -> str:
    if provider_param in {"q", "keyword"}:
        return "search_terms"
    if provider_param == "sinceDate":
        return "freshness_window"
    if provider_param in {"province", "city", "cityIds", "location", "teleworking"}:
        return "geography_modality"
    return f"provider_param::{provider_param}"


def _dedupe_preserving_order(values: Any) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return tuple(ordered)


__all__ = [
    "CaptureProfile",
    "OfferEvaluation",
    "build_capture_profile",
    "build_provider_execution_plan",
    "evaluate_offer",
]
