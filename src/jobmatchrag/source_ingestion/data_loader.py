from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(value.casefold().split())


@dataclass(frozen=True, slots=True)
class HybridCityRecord:
    city_key: str
    display_name: str
    aliases: tuple[str, ...]
    station_name: str
    supports_monthly_hybrid: bool
    status: str
    dataset_version: str


@dataclass(frozen=True, slots=True)
class KnownCompanyRecord:
    company_key: str
    canonical_name: str
    aliases: tuple[str, ...]
    signal_kind: str
    confidence: str
    status: str
    dataset_version: str


@dataclass(frozen=True, slots=True)
class HybridCityDataset:
    dataset_version: str
    seed_source: str
    records: tuple[HybridCityRecord, ...]
    _lookup: dict[str, HybridCityRecord]

    def lookup(self, city: str | None) -> HybridCityRecord | None:
        return self._lookup.get(_normalize_text(city))


@dataclass(frozen=True, slots=True)
class KnownCompanyDataset:
    dataset_version: str
    seed_source: str
    records: tuple[KnownCompanyRecord, ...]
    _lookup: dict[str, KnownCompanyRecord]

    def lookup(self, company: str | None) -> KnownCompanyRecord | None:
        return self._lookup.get(_normalize_text(company))


@dataclass(frozen=True, slots=True)
class CuratedDatasets:
    hybrid_cities: HybridCityDataset
    known_consultancies: KnownCompanyDataset


def _data_path(filename: str) -> Path:
    return Path(__file__).with_name("data") / filename


def _load_json(filename: str) -> dict[str, Any]:
    with _data_path(filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_hybrid_city_dataset(payload: dict[str, Any]) -> HybridCityDataset:
    dataset_version = str(payload["dataset_version"])
    records = tuple(
        HybridCityRecord(
            city_key=str(item["city_key"]),
            display_name=str(item["display_name"]),
            aliases=tuple(str(alias) for alias in item.get("aliases", ())),
            station_name=str(item["station_name"]),
            supports_monthly_hybrid=bool(item["supports_monthly_hybrid"]),
            status=str(item.get("status", "active")),
            dataset_version=dataset_version,
        )
        for item in payload["cities"]
    )
    lookup: dict[str, HybridCityRecord] = {}
    for record in records:
        lookup[_normalize_text(record.display_name)] = record
        for alias in record.aliases:
            lookup[_normalize_text(alias)] = record
    return HybridCityDataset(
        dataset_version=dataset_version,
        seed_source=str(payload["seed_source"]),
        records=records,
        _lookup=lookup,
    )


def _build_known_company_dataset(payload: dict[str, Any]) -> KnownCompanyDataset:
    dataset_version = str(payload["dataset_version"])
    records = tuple(
        KnownCompanyRecord(
            company_key=str(item["company_key"]),
            canonical_name=str(item["canonical_name"]),
            aliases=tuple(str(alias) for alias in item.get("aliases", ())),
            signal_kind=str(item["signal_kind"]),
            confidence=str(item["confidence"]),
            status=str(item.get("status", "active")),
            dataset_version=dataset_version,
        )
        for item in payload["companies"]
    )
    lookup: dict[str, KnownCompanyRecord] = {}
    for record in records:
        lookup[_normalize_text(record.canonical_name)] = record
        for alias in record.aliases:
            lookup[_normalize_text(alias)] = record
    return KnownCompanyDataset(
        dataset_version=dataset_version,
        seed_source=str(payload["seed_source"]),
        records=records,
        _lookup=lookup,
    )


@lru_cache(maxsize=1)
def load_curated_datasets() -> CuratedDatasets:
    return CuratedDatasets(
        hybrid_cities=_build_hybrid_city_dataset(_load_json("ave_hybrid_cities.json")),
        known_consultancies=_build_known_company_dataset(_load_json("known_consultancies.json")),
    )


__all__ = [
    "CuratedDatasets",
    "HybridCityDataset",
    "HybridCityRecord",
    "KnownCompanyDataset",
    "KnownCompanyRecord",
    "load_curated_datasets",
]
