from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ..contracts import FetchContext, KnownOfferIndex
from .errors import InfoJobsTransportError


_CHECKPOINT_ADAPTER = "infojobs"
_CHECKPOINT_VERSION = 1


@dataclass(frozen=True, slots=True)
class InfoJobsCheckpointState:
    page: int = 1
    offer_index: int = 0
    next_offer_id: str | None = None


def build_listing_query(
    context: FetchContext,
    *,
    checkpoint_state: InfoJobsCheckpointState,
    supported_filters: frozenset[str],
    page_size: int,
) -> dict[str, Any]:
    # InfoJobs currently supports provider-native temporal filters such as sinceDate,
    # but the adapter does not translate canonical run windows into provider params.
    query = {
        key: value
        for key, value in context.requested_filters.items()
        if key in supported_filters and value is not None
    }
    query["page"] = checkpoint_state.page
    query["maxResults"] = page_size
    return query


def encode_checkpoint(state: InfoJobsCheckpointState) -> str:
    payload: dict[str, Any] = {
        "adapter": _CHECKPOINT_ADAPTER,
        "version": _CHECKPOINT_VERSION,
        "page": state.page,
        "offer_index": state.offer_index,
    }
    if state.next_offer_id is not None:
        payload["next_offer_id"] = state.next_offer_id
    return json.dumps(payload, sort_keys=True)


def decode_checkpoint(checkpoint: str | None) -> InfoJobsCheckpointState:
    if checkpoint is None:
        return InfoJobsCheckpointState()
    if not isinstance(checkpoint, str):
        raise InfoJobsTransportError(
            message="InfoJobs adapter checkpoint is invalid or not owned by this adapter",
            endpoint="checkpoint",
            raw_body=checkpoint,
            failure_kind="checkpoint",
        )
    try:
        payload = json.loads(checkpoint)
    except (TypeError, json.JSONDecodeError) as error:
        raise InfoJobsTransportError(
            message="InfoJobs adapter checkpoint is invalid or not owned by this adapter",
            endpoint="checkpoint",
            raw_body=checkpoint,
            failure_kind="checkpoint",
        ) from error

    try:
        if not isinstance(payload, dict):
            raise TypeError("checkpoint payload must be a JSON object")
        if payload["adapter"] != _CHECKPOINT_ADAPTER:
            raise ValueError("checkpoint adapter marker mismatch")
        version = _parse_checkpoint_int(payload["version"], field_name="version")
        if version != _CHECKPOINT_VERSION:
            raise ValueError("checkpoint version mismatch")
        page = _parse_checkpoint_int(payload["page"], field_name="page")
        offer_index = _parse_checkpoint_int(payload["offer_index"], field_name="offer_index")
        if page <= 0:
            raise ValueError("checkpoint page must be > 0")
        if offer_index < 0:
            raise ValueError("checkpoint offer_index must be >= 0")
        return InfoJobsCheckpointState(
            page=page,
            offer_index=offer_index,
            next_offer_id=_parse_checkpoint_offer_id(payload.get("next_offer_id")),
        )
    except (TypeError, ValueError, KeyError):
        raise InfoJobsTransportError(
            message="InfoJobs adapter checkpoint is invalid or not owned by this adapter",
            endpoint="checkpoint",
            raw_body=checkpoint,
            failure_kind="checkpoint",
        )


def _parse_checkpoint_offer_id(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("checkpoint next_offer_id must be a string")
    parsed = value.strip()
    return parsed or None


def _parse_checkpoint_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"checkpoint {field_name} must be an integer")
    return value


def should_enrich_offer_detail(
    known_offer_index: KnownOfferIndex,
    source_key: str,
    listing_offer: dict[str, Any],
) -> bool:
    offer_id = str(listing_offer["id"])
    return known_offer_index.is_new(source_key, offer_id)
