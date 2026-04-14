from __future__ import annotations

from datetime import datetime

import pytest

from jobmatchrag.source_ingestion import FetchContext, PaginationSupport, RateLimitSupport, SourceCapabilities, TimeWindowSupport
from jobmatchrag.source_ingestion.infojobs.discovery import (
    InfoJobsCheckpointState,
    build_listing_query,
    decode_checkpoint,
    encode_checkpoint,
    should_enrich_offer_detail,
)
from jobmatchrag.source_ingestion.infojobs.errors import InfoJobsTransportError


class TrackingKnownOfferIndex:
    def __init__(self, new_offer_ids: set[str]) -> None:
        self._new_offer_ids = new_offer_ids
        self.calls: list[tuple[str, str]] = []

    def is_new(self, source_key: str, source_offer_id: str) -> bool:
        self.calls.append((source_key, source_offer_id))
        return source_offer_id in self._new_offer_ids


def build_context(**overrides: object) -> FetchContext:
    defaults: dict[str, object] = {
        "job_id": "job-1",
        "run_id": "run-1",
        "source_key": "infojobs",
        "capability_snapshot": SourceCapabilities(
            pagination=PaginationSupport.PAGE_NUMBER,
            time_windows=TimeWindowSupport.NONE,
            supported_filters=frozenset({"q", "province", "sinceDate", "order"}),
            checkpoint_support=True,
            rate_limit_support=RateLimitSupport.PASSIVE,
        ),
        "requested_filters": {
            "q": "python",
            "province": ["madrid", "barcelona"],
            "sinceDate": "_24_HOURS",
            "unsupported": "drop-me",
        },
        "requested_window_start": datetime(2026, 4, 14, 9, 0, 0),
        "checkpoint": None,
    }
    defaults.update(overrides)
    return FetchContext(**defaults)


def test_build_listing_query_keeps_supported_filters_and_since_date_as_advisory() -> None:
    query = build_listing_query(
        build_context(),
        checkpoint_state=InfoJobsCheckpointState(page=3, offer_index=0),
        supported_filters=frozenset({"q", "province", "sinceDate", "order"}),
        page_size=25,
    )

    assert query == {
        "q": "python",
        "province": ["madrid", "barcelona"],
        "sinceDate": "_24_HOURS",
        "page": 3,
        "maxResults": 25,
    }


def test_build_listing_query_does_not_claim_canonical_window_translation() -> None:
    query = build_listing_query(
        build_context(
            requested_filters={"q": "python"},
            requested_window_start=datetime(2026, 4, 14, 9, 0, 0),
            requested_window_end=datetime(2026, 4, 14, 11, 0, 0),
        ),
        checkpoint_state=InfoJobsCheckpointState(page=1, offer_index=0),
        supported_filters=frozenset({"q", "sinceDate"}),
        page_size=25,
    )

    assert query == {"q": "python", "page": 1, "maxResults": 25}


def test_checkpoint_round_trip_keeps_internal_continuation_separate_from_since_date() -> None:
    checkpoint = encode_checkpoint(
        InfoJobsCheckpointState(page=2, offer_index=4, next_offer_id="offer-5")
    )

    decoded = decode_checkpoint(checkpoint)

    assert decoded == InfoJobsCheckpointState(page=2, offer_index=4, next_offer_id="offer-5")
    assert '"adapter": "infojobs"' in checkpoint
    assert '"version": 1' in checkpoint
    assert "sinceDate" not in checkpoint


def test_decode_checkpoint_rejects_invalid_structured_checkpoint() -> None:
    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        decode_checkpoint('{"adapter": "infojobs", "version": 1, "page": "oops", "offer_index": 0}')

    assert exc_info.value.failure_kind == "checkpoint"


def test_decode_checkpoint_rejects_malformed_json_checkpoint() -> None:
    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        decode_checkpoint('{"page": 1')

    assert exc_info.value.failure_kind == "checkpoint"


@pytest.mark.parametrize(
    "checkpoint",
    [
        '{"adapter": "infojobs", "version": 1, "page": 1.9, "offer_index": 0}',
        '{"adapter": "infojobs", "version": 1, "page": 1, "offer_index": 1.9}',
        '{"adapter": "infojobs", "version": 1, "page": 1, "offer_index": true}',
        '{"adapter": "infojobs", "version": 1, "page": 1, "offer_index": 0, "next_offer_id": 99}',
    ],
)
def test_decode_checkpoint_rejects_structured_checkpoint_with_invalid_field_types(checkpoint: str) -> None:
    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        decode_checkpoint(checkpoint)

    assert exc_info.value.failure_kind == "checkpoint"


def test_decode_checkpoint_rejects_non_string_input() -> None:
    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        decode_checkpoint(123)  # type: ignore[arg-type]

    assert exc_info.value.failure_kind == "checkpoint"


@pytest.mark.parametrize("checkpoint", [b'{"adapter": "infojobs", "version": 1, "page": 1, "offer_index": 0}', bytearray(b'{"adapter": "infojobs", "version": 1, "page": 1, "offer_index": 0}')])
def test_decode_checkpoint_rejects_bytes_like_input(checkpoint: bytes | bytearray) -> None:
    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        decode_checkpoint(checkpoint)  # type: ignore[arg-type]

    assert exc_info.value.failure_kind == "checkpoint"


@pytest.mark.parametrize(
    "checkpoint",
    [
        '{"adapter": "infojobs", "version": true, "page": 1, "offer_index": 0}',
        '{"adapter": "infojobs", "version": 1.0, "page": 1, "offer_index": 0}',
        '{"adapter": "infojobs", "version": "1", "page": 1, "offer_index": 0}',
        '{"adapter": "infojobs", "version": 1, "page": 0, "offer_index": 0}',
        '{"adapter": "infojobs", "version": 1, "page": 1, "offer_index": -3}',
        '{"adapter": "other", "version": 1, "page": 1, "offer_index": 0}',
        '{"adapter": "infojobs", "version": 2, "page": 1, "offer_index": 0}',
        '{"page": 1, "offer_index": 0}',
    ],
)
def test_decode_checkpoint_rejects_foreign_or_invalid_structured_checkpoint(checkpoint: str) -> None:
    with pytest.raises(InfoJobsTransportError, match="checkpoint is invalid") as exc_info:
        decode_checkpoint(checkpoint)

    assert exc_info.value.failure_kind == "checkpoint"


def test_should_enrich_offer_detail_only_for_new_offers() -> None:
    known_offer_index = TrackingKnownOfferIndex(new_offer_ids={"offer-new"})

    assert should_enrich_offer_detail(known_offer_index, "infojobs", {"id": "offer-new"}) is True
    assert should_enrich_offer_detail(known_offer_index, "infojobs", {"id": "offer-known"}) is False
    assert known_offer_index.calls == [
        ("infojobs", "offer-new"),
        ("infojobs", "offer-known"),
    ]
