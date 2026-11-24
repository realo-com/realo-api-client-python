"""Exceptions raised by the Realo API client."""

import json
from typing import Any, List, Optional


class RealoApiException(Exception):
    """Raised when a request fails or the server answers with a status >= 400.

    Attributes:
        code: HTTP status code (0 when no response was received).
        errors: the ``errors`` list of a JSON error body, otherwise ``None``.
        type: ``errors[0]["type"]`` when present, otherwise ``None``.
    """

    def __init__(
        self,
        message: str,
        code: int = 0,
        errors: Optional[List[Any]] = None,
        type: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.errors = errors
        self.type = type

    @classmethod
    def from_response(
        cls,
        code: int,
        content_type: Optional[str],
        body: bytes,
        default_message: str,
    ) -> "RealoApiException":
        errors: Optional[List[Any]] = None
        if content_type and content_type.startswith("application/json"):
            try:
                parsed = json.loads(body.decode("utf-8"))
            except ValueError:
                parsed = None
            if isinstance(parsed, dict) and isinstance(parsed.get("errors"), list):
                errors = parsed["errors"]

        error_type: Optional[str] = None
        message = default_message
        if errors and isinstance(errors[0], dict):
            first = errors[0]
            error_type = first.get("type")
            if error_type is not None or first.get("message") is not None:
                message = "%s: %s" % (error_type, first.get("message"))
        return cls(message, code=code, errors=errors, type=error_type)
