from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .errors import InfoJobsAPIError, InfoJobsTransportError


@dataclass(frozen=True, slots=True)
class InfoJobsClientConfig:
    client_id: str
    client_secret: str = field(repr=False)
    base_url: str = "https://api.infojobs.net"
    timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class InfoJobsRequest:
    url: str
    endpoint: str
    params: dict[str, Any]
    headers: dict[str, str] = field(repr=False)


@dataclass(frozen=True, slots=True)
class InfoJobsResponse:
    payload: dict[str, Any]
    headers: Mapping[str, str] = field(default_factory=dict)
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InfoJobsTransport(Protocol):
    def request_json(self, request: InfoJobsRequest) -> InfoJobsResponse: ...


class UrllibInfoJobsTransport:
    def __init__(self, *, timeout_seconds: float) -> None:
        self._timeout_seconds = timeout_seconds

    def request_json(self, request: InfoJobsRequest) -> InfoJobsResponse:
        url = request.url
        if request.params:
            url = f"{url}?{urlencode(request.params, doseq=True)}"

        http_request = Request(url=url, headers=request.headers, method="GET")
        try:
            with urlopen(http_request, timeout=self._timeout_seconds) as response:
                body = _decode_response_body(response.read(), response.headers)
                payload = _parse_success_payload(
                    body,
                    endpoint=request.endpoint,
                    status_code=getattr(response, "status", None),
                )
                headers = {key: value for key, value in response.headers.items()}
                return InfoJobsResponse(payload=payload, headers=headers)
        except HTTPError as error:
            error_headers = _headers_to_dict(error.headers)
            body = _decode_response_body(error.read(), error.headers) if error.fp is not None else ""
            payload = _parse_error_payload(body)
            error_code = payload.get("errorCode") or payload.get("code")
            message = (
                payload.get("message")
                or payload.get("errorDescription")
                or payload.get("raw_body")
                or str(error)
            )
            raise InfoJobsAPIError(
                status_code=error.code,
                endpoint=request.endpoint,
                message=str(message),
                error_code=str(error_code) if error_code is not None else None,
                payload=payload,
                headers=error_headers,
            ) from error
        except URLError as error:
            raise InfoJobsTransportError(str(error.reason), endpoint=request.endpoint) from error


def _headers_to_dict(headers: object | None) -> dict[str, str]:
    if headers is None:
        return {}
    try:
        items = cast(Any, headers).items()
        return {str(key): str(value) for key, value in items}
    except AttributeError:
        return {}


def _decode_response_body(body: bytes, headers: object | None) -> str:
    if not body:
        return ""

    content_type: str | None = None
    if headers is not None:
        try:
            raw_content_type = cast(Any, headers).get("Content-Type")
        except AttributeError:
            raw_content_type = None
        if raw_content_type is not None:
            content_type = str(raw_content_type)
    charset = "utf-8"
    if content_type is not None:
        for part in content_type.split(";"):
            attribute, separator, value = part.strip().partition("=")
            if separator and attribute.lower() == "charset":
                candidate = value.strip().strip('"')
                if candidate:
                    charset = candidate
                break

    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _parse_success_payload(body: str, *, endpoint: str, status_code: int | None) -> dict[str, Any]:
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as error:
        raise InfoJobsTransportError(
            message=f"InfoJobs returned an invalid JSON success body for {endpoint}",
            endpoint=endpoint,
            raw_body=body,
            status_code=status_code,
            failure_kind="payload",
        ) from error

    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed)

    raise InfoJobsTransportError(
        message=f"InfoJobs returned a non-object JSON success body for {endpoint}",
        endpoint=endpoint,
        raw_body=body,
        status_code=status_code,
        failure_kind="payload",
    )


def _parse_error_payload(body: str) -> dict[str, Any]:
    if not body:
        return {}

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return {"raw_body": body}

    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed)

    return {"raw_body": body}


class InfoJobsClient:
    def __init__(
        self,
        *,
        config: InfoJobsClientConfig,
        transport: InfoJobsTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or UrllibInfoJobsTransport(timeout_seconds=config.timeout_seconds)

    def list_offers(self, params: dict[str, Any]) -> InfoJobsResponse:
        request = InfoJobsRequest(
            url=f"{self._config.base_url}/api/9/offer",
            endpoint="GET /offer",
            params=dict(params),
            headers=self._build_headers(),
        )
        return self._transport.request_json(request)

    def get_offer_detail(self, offer_id: str) -> InfoJobsResponse:
        request = InfoJobsRequest(
            url=f"{self._config.base_url}/api/7/offer/{offer_id}",
            endpoint="GET /offer/{offerId}",
            params={},
            headers=self._build_headers(),
        )
        return self._transport.request_json(request)

    def _build_headers(self) -> dict[str, str]:
        token = base64.b64encode(
            f"{self._config.client_id}:{self._config.client_secret}".encode("utf-8")
        ).decode("ascii")
        return {
            "Accept": "application/json",
            "Authorization": f"Basic {token}",
        }
