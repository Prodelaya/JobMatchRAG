from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from ..contracts import RawCapture, RawCaptureOrigin, RawOfferHandoff


def build_raw_handoff(
    *,
    source_key: str,
    source_offer_id: str,
    job_id: str,
    run_id: str,
    checkpoint_in: str | None,
    list_request: dict[str, Any],
    page_context: dict[str, Any],
    list_payload: dict[str, Any],
    list_observed_at: datetime,
    detail_payload: dict[str, Any] | None,
    detail_observed_at: datetime | None = None,
    detail_context: dict[str, Any] | None = None,
) -> RawOfferHandoff:
    captures: dict[RawCaptureOrigin, RawCapture] = {
        RawCaptureOrigin.LIST: {
            "origin": RawCaptureOrigin.LIST,
            "endpoint": "GET /offer",
            "api_version": "9",
            "observed_at": list_observed_at.isoformat(),
            "payload": deepcopy(list_payload),
        }
    }
    if detail_payload is not None:
        if detail_observed_at is None:
            raise ValueError("detail_observed_at is required when detail_payload is present")
        captures[RawCaptureOrigin.DETAIL] = {
            "origin": RawCaptureOrigin.DETAIL,
            "endpoint": "GET /offer/{offerId}",
            "api_version": "7",
            "observed_at": detail_observed_at.isoformat(),
            "payload": deepcopy(detail_payload),
        }

    return {
        "source_key": source_key,
        "source_offer_id": source_offer_id,
        "trace": {
            "job_id": job_id,
            "run_id": run_id,
            "checkpoint_in": checkpoint_in,
            "list_request": deepcopy(list_request),
            "page_context": deepcopy(page_context),
            "detail_context": deepcopy(detail_context) if detail_context is not None else None,
        },
        "captures": captures,
    }
