from __future__ import annotations

from datetime import UTC, datetime

import pytest

from jobmatchrag.source_ingestion.contracts import RawCaptureOrigin
from jobmatchrag.source_ingestion.infojobs.raw_handoff import build_raw_handoff


def test_raw_handoff_keeps_list_and_detail_payloads_as_distinct_sibling_captures() -> None:
    handoff = build_raw_handoff(
        source_key="infojobs",
        source_offer_id="offer-1",
        job_id="job-1",
        run_id="run-1",
        checkpoint_in="opaque-checkpoint",
        list_request={"page": 1, "maxResults": 50, "sinceDate": "_24_HOURS"},
        page_context={"current_page": 1, "total_pages": 3},
        list_payload={"id": "offer-1", "title": "Python Engineer", "published": "2026-04-14"},
        list_observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
        detail_payload={"id": "offer-1", "description": "Build data products"},
        detail_observed_at=datetime(2026, 4, 14, 12, 0, 5, tzinfo=UTC),
    )

    assert handoff["source_offer_id"] == "offer-1"
    assert handoff["trace"]["list_request"]["sinceDate"] == "_24_HOURS"
    assert set(handoff["captures"]) == {RawCaptureOrigin.LIST, RawCaptureOrigin.DETAIL}
    assert handoff["captures"][RawCaptureOrigin.LIST]["payload"] == {
        "id": "offer-1",
        "title": "Python Engineer",
        "published": "2026-04-14",
    }
    assert handoff["captures"][RawCaptureOrigin.DETAIL]["payload"] == {
        "id": "offer-1",
        "description": "Build data products",
    }
    assert handoff["captures"][RawCaptureOrigin.LIST]["observed_at"] == "2026-04-14T12:00:00+00:00"
    assert handoff["captures"][RawCaptureOrigin.DETAIL]["observed_at"] == "2026-04-14T12:00:05+00:00"


def test_raw_handoff_omits_detail_capture_when_offer_is_already_known() -> None:
    handoff = build_raw_handoff(
        source_key="infojobs",
        source_offer_id="offer-1",
        job_id="job-1",
        run_id="run-1",
        checkpoint_in=None,
        list_request={"page": 2, "maxResults": 50},
        page_context={"current_page": 2, "total_pages": 2},
        list_payload={"id": "offer-1", "title": "Known Offer"},
        list_observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
        detail_payload=None,
    )

    assert set(handoff["captures"]) == {RawCaptureOrigin.LIST}
    assert RawCaptureOrigin.DETAIL not in handoff["captures"]


def test_raw_handoff_requires_detail_timestamp_when_detail_capture_exists() -> None:
    with pytest.raises(ValueError, match="detail_observed_at is required"):
        build_raw_handoff(
            source_key="infojobs",
            source_offer_id="offer-1",
            job_id="job-1",
            run_id="run-1",
            checkpoint_in=None,
            list_request={"page": 1, "maxResults": 50},
            page_context={"current_page": 1, "total_pages": 1},
            list_payload={"id": "offer-1", "title": "Python Engineer"},
            list_observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
            detail_payload={"id": "offer-1", "description": "Build data products"},
        )


def test_raw_handoff_deep_copies_trace_and_capture_payloads() -> None:
    list_request = {"page": 1, "filters": {"sinceDate": "_24_HOURS"}}
    page_context = {"current_page": 1, "meta": {"total_pages": 2}}
    list_payload = {"id": "offer-1", "meta": {"tags": ["python"]}}
    detail_payload = {"id": "offer-1", "meta": {"skills": ["etl"]}}
    detail_context = {"status": "captured", "meta": {"attempt": 1}}

    handoff = build_raw_handoff(
        source_key="infojobs",
        source_offer_id="offer-1",
        job_id="job-1",
        run_id="run-1",
        checkpoint_in="opaque-checkpoint",
        list_request=list_request,
        page_context=page_context,
        list_payload=list_payload,
        list_observed_at=datetime(2026, 4, 14, 12, 0, 0, tzinfo=UTC),
        detail_payload=detail_payload,
        detail_observed_at=datetime(2026, 4, 14, 12, 0, 5, tzinfo=UTC),
        detail_context=detail_context,
    )

    list_request["filters"]["sinceDate"] = "_7_DAYS"
    page_context["meta"]["total_pages"] = 99
    list_payload["meta"]["tags"].append("mutated")
    detail_payload["meta"]["skills"].append("mutated")
    detail_context["meta"]["attempt"] = 2

    assert handoff["trace"]["list_request"] == {"page": 1, "filters": {"sinceDate": "_24_HOURS"}}
    assert handoff["trace"]["page_context"] == {"current_page": 1, "meta": {"total_pages": 2}}
    assert handoff["trace"]["detail_context"] == {"status": "captured", "meta": {"attempt": 1}}
    assert handoff["captures"][RawCaptureOrigin.LIST]["observed_at"] == "2026-04-14T12:00:00+00:00"
    assert handoff["captures"][RawCaptureOrigin.DETAIL]["observed_at"] == "2026-04-14T12:00:05+00:00"
    assert handoff["captures"][RawCaptureOrigin.LIST]["payload"] == {
        "id": "offer-1",
        "meta": {"tags": ["python"]},
    }
    assert handoff["captures"][RawCaptureOrigin.DETAIL]["payload"] == {
        "id": "offer-1",
        "meta": {"skills": ["etl"]},
    }
