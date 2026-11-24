"""Official Python client for the Realo REST API."""

from .client import (
    DEFAULT_USER_AGENT,
    ENVIRONMENTS,
    PRODUCTION_ENVIRONMENT,
    SANDBOX_ENVIRONMENT,
    RealoApi,
    Transport,
    TransportResponse,
)
from .exceptions import RealoApiException

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_USER_AGENT",
    "ENVIRONMENTS",
    "PRODUCTION_ENVIRONMENT",
    "SANDBOX_ENVIRONMENT",
    "RealoApi",
    "RealoApiException",
    "Transport",
    "TransportResponse",
    "__version__",
]
