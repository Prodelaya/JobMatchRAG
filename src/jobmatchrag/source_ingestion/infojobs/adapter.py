from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ..contracts import (
    ErrorClassification,
    FetchContext,
    FetchOutcome,
    RateLimitObservation,
    PaginationSupport,
    RateLimitSupport,
    SourceCapabilities,
    TimeWindowSupport,
)
from typing import cast
from .client import InfoJobsClient
from .discovery import (
    InfoJobsCheckpointState,
    build_listing_query,
    decode_checkpoint,
    encode_checkpoint,
    should_enrich_offer_detail,
)
from .errors import InfoJobsAPIError, InfoJobsTransportError, classify_infojobs_error, rate_limit_observation_from_error
from .raw_handoff import build_raw_handoff
from ..contracts import KnownOfferIndex


INFOJOBS_SUPPORTED_FILTERS = frozenset(
    {
        "q",
        "category",
        "subcategory",
        "province",
        "provinceIds",
        "city",
        "cityIds",
        "country",
        "countryIds",
        "salaryMin",
        "salaryMax",
        "salaryPeriod",
        "contractType",
        "workday",
        "teleworking",
        "experienceMin",
        "study",
        "order",
        "sinceDate",
        "employerId",
    }
)


@dataclass(slots=True)
class InfoJobsAdapter:
    client: InfoJobsClient
    known_offer_index: KnownOfferIndex
    page_size: int = 50
    max_requests_per_fetch: int = 10
    max_detail_requests_per_fetch: int = 5
    source_key: str = "infojobs"
    capabilities: SourceCapabilities = field(init=False)

    def __post_init__(self) -> None:
        if self.page_size <= 0:
            raise ValueError("page_size must be > 0")
        if self.page_size > 50:
            raise ValueError("page_size must be <= 50 for the current InfoJobs operating contract")
        if self.max_requests_per_fetch <= 0:
            raise ValueError("max_requests_per_fetch must be > 0")
        if self.max_detail_requests_per_fetch <= 0:
            raise ValueError("max_detail_requests_per_fetch must be > 0")
        if self.max_detail_requests_per_fetch > self.max_requests_per_fetch - 1:
            raise ValueError(
                "max_detail_requests_per_fetch must fit within the remaining request budget after the listing call"
            )
        self.capabilities = SourceCapabilities(
            pagination=PaginationSupport.PAGE_NUMBER,
            time_windows=TimeWindowSupport.NONE,
            supported_filters=INFOJOBS_SUPPORTED_FILTERS,
            checkpoint_support=True,
            rate_limit_support=RateLimitSupport.EXPLICIT,
        )

    def fetch(self, context: FetchContext) -> FetchOutcome:
        checkpoint_state = decode_checkpoint(context.checkpoint)
        query = build_listing_query(
            context,
            checkpoint_state=checkpoint_state,
            supported_filters=INFOJOBS_SUPPORTED_FILTERS,
            page_size=self.page_size,
        )
        try:
            list_response = self.client.list_offers(query)
        except InfoJobsAPIError as error:
            if error.status_code == 429:
                return FetchOutcome(
                    raw_items=(),
                    next_checkpoint=encode_checkpoint(checkpoint_state),
                    exhausted=False,
                    rate_limit_observations=(
                        rate_limit_observation_from_error(error, scope="list"),
                    ),
                )
            raise
        request_budget = max(self.max_requests_per_fetch - 1, 0)
        detail_budget = self.max_detail_requests_per_fetch
        item_budget = context.remaining_item_budget

        payload = list_response.payload
        offers, current_page, total_pages = _parse_listing_payload(payload, checkpoint_state=checkpoint_state)
        offer_index = _resolve_offer_index(offers, checkpoint_state=checkpoint_state)
        raw_items: list[dict[str, Any]] = []
        rate_limit_observations: list[RateLimitObservation] = []

        for offer_index in range(offer_index, len(offers)):
            if item_budget is not None and len(raw_items) >= item_budget:
                return FetchOutcome(
                    raw_items=tuple(raw_items),
                    next_checkpoint=encode_checkpoint(_build_resume_checkpoint(current_page, offers, offer_index)),
                    exhausted=False,
                    rate_limit_observations=tuple(rate_limit_observations),
                )

            listing_offer = dict(offers[offer_index])
            offer_id = _parse_offer_id(listing_offer, offer_index=offer_index)
            detail_payload: dict[str, Any] | None = None
            detail_context: dict[str, Any] | None = None

            if should_enrich_offer_detail(self.known_offer_index, self.source_key, listing_offer):
                if request_budget <= 0 or detail_budget <= 0:
                    detail_context = {"status": "deferred", "reason": "request_budget_exhausted"}
                    raw_items.append(
                        cast(
                            dict[str, Any],
                            build_raw_handoff(
                                source_key=self.source_key,
                                source_offer_id=offer_id,
                                job_id=context.job_id,
                                run_id=context.run_id,
                                checkpoint_in=context.checkpoint,
                                list_request=query,
                                request_plan=None,
                                page_context={"current_page": current_page, "total_pages": total_pages},
                                list_payload=listing_offer,
                                list_observed_at=list_response.observed_at,
                                detail_payload=None,
                                detail_context=detail_context,
                            ),
                        )
                    )
                    return FetchOutcome(
                        raw_items=tuple(raw_items),
                        next_checkpoint=encode_checkpoint(
                            _build_checkpoint_after_current_offer(current_page, total_pages, offers, offer_index)
                        ),
                        exhausted=False,
                        rate_limit_observations=tuple(rate_limit_observations),
                    )
                try:
                    detail_response = self.client.get_offer_detail(offer_id)
                except InfoJobsAPIError as error:
                    if error.status_code == 429:
                        rate_limit_observations.append(
                            rate_limit_observation_from_error(error, scope="detail")
                        )
                        detail_context = {"status": "deferred", "reason": "rate_limited"}
                        raw_items.append(
                            cast(
                                dict[str, Any],
                                build_raw_handoff(
                                    source_key=self.source_key,
                                    source_offer_id=offer_id,
                                    job_id=context.job_id,
                                    run_id=context.run_id,
                                    checkpoint_in=context.checkpoint,
                                    list_request=query,
                                    request_plan=None,
                                    page_context={"current_page": current_page, "total_pages": total_pages},
                                    list_payload=listing_offer,
                                    list_observed_at=list_response.observed_at,
                                    detail_payload=None,
                                    detail_context=detail_context,
                                ),
                            )
                        )
                        return FetchOutcome(
                            raw_items=tuple(raw_items),
                            next_checkpoint=encode_checkpoint(
                                _build_checkpoint_after_current_offer(current_page, total_pages, offers, offer_index)
                            ),
                            exhausted=False,
                            rate_limit_observations=tuple(rate_limit_observations),
                        )
                    if raw_items:
                        return FetchOutcome(
                            raw_items=tuple(raw_items),
                            next_checkpoint=encode_checkpoint(_build_resume_checkpoint(current_page, offers, offer_index)),
                            exhausted=False,
                            rate_limit_observations=tuple(rate_limit_observations),
                            error_summary=classify_infojobs_error(error),
                        )
                    raise
                except Exception as error:
                    if raw_items:
                        return FetchOutcome(
                            raw_items=tuple(raw_items),
                            next_checkpoint=encode_checkpoint(_build_resume_checkpoint(current_page, offers, offer_index)),
                            exhausted=False,
                            rate_limit_observations=tuple(rate_limit_observations),
                            error_summary=classify_infojobs_error(error),
                        )
                    raise
                request_budget -= 1
                detail_budget -= 1
                detail_payload = detail_response.payload

            raw_items.append(
                cast(
                    dict[str, Any],
                    build_raw_handoff(
                    source_key=self.source_key,
                    source_offer_id=offer_id,
                    job_id=context.job_id,
                    run_id=context.run_id,
                    checkpoint_in=context.checkpoint,
                    list_request=query,
                    request_plan=None,
                    page_context={"current_page": current_page, "total_pages": total_pages},
                    list_payload=listing_offer,
                    list_observed_at=list_response.observed_at,
                    detail_payload=detail_payload,
                    detail_observed_at=detail_response.observed_at if detail_payload is not None else None,
                    detail_context=detail_context,
                    ),
                )
            )

        next_checkpoint = None
        exhausted = current_page >= total_pages
        if not exhausted:
            next_checkpoint = encode_checkpoint(InfoJobsCheckpointState(page=current_page + 1, offer_index=0))

        return FetchOutcome(
            raw_items=tuple(raw_items),
            next_checkpoint=next_checkpoint,
            exhausted=exhausted,
            rate_limit_observations=tuple(rate_limit_observations),
        )

    def classify_error(self, error: Exception) -> ErrorClassification:
        return classify_infojobs_error(error)


def _parse_listing_payload(
    payload: Mapping[str, Any], *, checkpoint_state: InfoJobsCheckpointState
) -> tuple[tuple[Mapping[str, Any], ...], int, int]:
    offers = _parse_offers(payload)
    del checkpoint_state
    current_page = _parse_positive_int(_require_payload_field(payload, "currentPage"), field_name="currentPage")
    total_pages = _parse_positive_int(_require_payload_field(payload, "totalPages"), field_name="totalPages")
    if total_pages < current_page:
        raise _listing_payload_error(
            message="InfoJobs returned totalPages lower than currentPage in listing response",
            payload=payload,
        )
    return offers, current_page, total_pages


def _parse_offers(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    raw_offers = payload.get("items")
    if raw_offers is None:
        raw_offers = payload.get("offers")
    if raw_offers is None:
        raise _listing_payload_error(
            message="InfoJobs listing response is missing items/offers",
            payload=payload,
        )
    if not isinstance(raw_offers, list):
        raise _listing_payload_error(
            message="InfoJobs listing response items/offers must be a JSON array",
            payload=payload,
        )

    parsed_offers: list[Mapping[str, Any]] = []
    for offer_index, raw_offer in enumerate(raw_offers):
        if not isinstance(raw_offer, Mapping):
            raise _listing_payload_error(
                message=f"InfoJobs listing response offer at index {offer_index} must be a JSON object",
                payload=payload,
            )
        _parse_offer_id(raw_offer, offer_index=offer_index)
        parsed_offers.append(raw_offer)
    return tuple(parsed_offers)


def _parse_positive_int(value: Any, *, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise InfoJobsTransportError(
            message=f"InfoJobs listing response field {field_name} must be an integer",
            endpoint="GET /offer",
            raw_body=repr(value),
            failure_kind="payload",
        ) from error
    if parsed <= 0:
        raise InfoJobsTransportError(
            message=f"InfoJobs listing response field {field_name} must be > 0",
            endpoint="GET /offer",
            raw_body=repr(value),
            failure_kind="payload",
        )
    return parsed


def _parse_offer_id(offer: Mapping[str, Any], *, offer_index: int) -> str:
    offer_id = offer.get("id")
    if offer_id is None:
        raise InfoJobsTransportError(
            message=f"InfoJobs listing response offer at index {offer_index} is missing id",
            endpoint="GET /offer",
            raw_body=repr(dict(offer)),
            failure_kind="payload",
        )
    parsed_offer_id = str(offer_id).strip()
    if not parsed_offer_id:
        raise InfoJobsTransportError(
            message=f"InfoJobs listing response offer at index {offer_index} has an empty id",
            endpoint="GET /offer",
            raw_body=repr(dict(offer)),
            failure_kind="payload",
        )
    return parsed_offer_id


def _require_payload_field(payload: Mapping[str, Any], field_name: str) -> Any:
    if field_name not in payload:
        raise _listing_payload_error(
            message=f"InfoJobs listing response is missing {field_name}",
            payload=payload,
        )
    return payload[field_name]


def _listing_payload_error(*, message: str, payload: Mapping[str, Any]) -> InfoJobsTransportError:
    return InfoJobsTransportError(
        message=message,
        endpoint="GET /offer",
        raw_body=repr(dict(payload)),
        failure_kind="payload",
    )


def _resolve_offer_index(
    offers: tuple[Mapping[str, Any], ...], *, checkpoint_state: InfoJobsCheckpointState
) -> int:
    if checkpoint_state.next_offer_id is not None:
        for offer_index, offer in enumerate(offers):
            if str(offer.get("id", "")).strip() == checkpoint_state.next_offer_id:
                return offer_index
        if checkpoint_state.offer_index > 0:
            return 0

    if checkpoint_state.offer_index >= len(offers) and checkpoint_state.offer_index > 0:
        return len(offers)
    return checkpoint_state.offer_index


def _build_resume_checkpoint(
    current_page: int,
    offers: tuple[Mapping[str, Any], ...],
    offer_index: int,
) -> InfoJobsCheckpointState:
    return InfoJobsCheckpointState(
        page=current_page,
        offer_index=offer_index,
        next_offer_id=_parse_offer_id(offers[offer_index], offer_index=offer_index),
    )


def _build_checkpoint_after_current_offer(
    current_page: int,
    total_pages: int,
    offers: tuple[Mapping[str, Any], ...],
    offer_index: int,
) -> InfoJobsCheckpointState:
    next_offer_index = offer_index + 1
    if next_offer_index < len(offers):
        return _build_resume_checkpoint(current_page, offers, next_offer_index)
    if current_page < total_pages:
        return InfoJobsCheckpointState(page=current_page + 1, offer_index=0)
    return InfoJobsCheckpointState(page=current_page, offer_index=len(offers))
