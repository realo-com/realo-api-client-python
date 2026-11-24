"""Realo REST API client."""

import base64
import hashlib
import hmac
import json
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Mapping, NamedTuple, Optional, Union

from .exceptions import RealoApiException

PRODUCTION_ENVIRONMENT = "production"
SANDBOX_ENVIRONMENT = "sandbox"

ENVIRONMENTS: Dict[str, str] = {
    PRODUCTION_ENVIRONMENT: "https://api.realo.com/1.0/",
    SANDBOX_ENVIRONMENT: "https://api-sandbox.realo.com/1.0/",
}

_VERSION = "1.0.0"
DEFAULT_USER_AGENT = "RealoApiClient-Python/" + _VERSION


class TransportResponse(NamedTuple):
    """What a transport returns. A status >= 400 is not an error at this level."""

    status: int
    headers: Mapping[str, str]
    body: bytes


# A transport sends one request: (method, url, headers, body) -> TransportResponse.
# It may raise OSError for connection problems.
Transport = Callable[[str, str, Dict[str, str], Optional[bytes]], TransportResponse]


def urllib_transport(
    method: str, url: str, headers: Dict[str, str], body: Optional[bytes]
) -> TransportResponse:
    """Default transport built on :mod:`urllib.request` (no dependencies)."""
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return TransportResponse(resp.status, _lower(resp.headers.items()), resp.read())
    except urllib.error.HTTPError as e:
        return TransportResponse(e.code, _lower(e.headers.items()), e.read())


def _lower(items: Any) -> Dict[str, str]:
    return {k.lower(): v for k, v in items}


class RealoApi:
    """Client for the Realo REST API. Build it with :meth:`create` or :meth:`create_with_transport`."""

    def __init__(
        self, public_key: str, private_key: str, base_url: str, transport: Transport
    ) -> None:
        self.public_key = public_key
        self.private_key = private_key
        self.base_url = base_url
        self.transport = transport

    @classmethod
    def create(
        cls,
        public_key: str,
        private_key: str,
        environment: str = PRODUCTION_ENVIRONMENT,
    ) -> "RealoApi":
        if environment not in ENVIRONMENTS:
            raise ValueError(
                "Unsupported environment '%s', please use any of [%s]"
                % (environment, ", ".join(ENVIRONMENTS))
            )
        return cls(public_key, private_key, ENVIRONMENTS[environment], urllib_transport)

    @classmethod
    def create_with_transport(
        cls,
        public_key: str,
        private_key: str,
        transport: Transport,
        environment: str = PRODUCTION_ENVIRONMENT,
    ) -> "RealoApi":
        """Like :meth:`create` but sends requests through your own transport (e.g. a test fake)."""
        api = cls.create(public_key, private_key, environment)
        api.transport = transport
        return api

    def sign(self, method: str, url: str, body: str = "") -> str:
        """Return the Authorization header value for a request."""
        base_string = method.upper() + "&" + url + "&" + body
        digest = hmac.new(
            self.private_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha256
        ).digest()
        signature = base64.b64encode(digest).decode("ascii")
        return 'Realo key="%s", version="1.0", signature="%s"' % (self.public_key, signature)

    def request(
        self,
        path: str,
        method: str = "GET",
        payload: Optional[Any] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Union[Any, bytes]:
        """Send a signed request.

        Returns the parsed JSON when the response Content-Type starts with
        ``application/json``, otherwise the raw response body as ``bytes``.
        Raises :class:`RealoApiException` on status >= 400 or transport errors.
        """
        method = method.upper()
        url = self.base_url + path.lstrip("/")
        body_text = ""
        body: Optional[bytes] = None
        if payload is not None:
            body_text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
            body = body_text.encode("utf-8")

        all_headers: Dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
        all_headers.update(headers or {})
        all_headers["Content-Type"] = "application/json"
        all_headers["Authorization"] = self.sign(method, url, body_text)

        try:
            response = self.transport(method, url, all_headers, body)
        except (OSError, urllib.error.URLError) as e:
            raise RealoApiException(str(e)) from e

        content_type = _lower(response.headers.items()).get("content-type")
        if response.status >= 400:
            raise RealoApiException.from_response(
                response.status,
                content_type,
                response.body,
                "HTTP error %d" % response.status,
            )
        if content_type and content_type.startswith("application/json"):
            try:
                return json.loads(response.body.decode("utf-8"))
            except ValueError as e:
                raise RealoApiException(
                    "Invalid JSON in response: %s" % e, code=response.status
                ) from e
        return response.body
