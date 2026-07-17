"""
AstroOS — SDK & Public API Domain Objects (Module 25, Phase 1)

API versioning, error standardization, pagination, response envelope,
and SDK configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ApiVersion:
    """A supported API version with deprecation metadata."""

    version: str
    status: str  # "current" | "deprecated" | "sunset"
    deprecated_at: Optional[str] = None
    sunset_at: Optional[str] = None
    release_notes: str = ""


@dataclass(frozen=True)
class ApiError:
    """Standardized error response."""

    code: str
    message: str
    details: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None
    docs_url: Optional[str] = None


@dataclass(frozen=True)
class Pagination:
    """Standard pagination for list endpoints."""

    limit: int = 100
    offset: int = 0
    total: Optional[int] = None


@dataclass(frozen=True)
class ApiResponse:
    """Standard response envelope for all endpoints."""

    success: bool
    data: Any = None
    error: Optional[ApiError] = None
    pagination: Optional[Pagination] = None
    version: str = "v1"
    request_id: str = ""


@dataclass(frozen=True)
class SdkConfig:
    """Configuration for SDK clients."""

    base_url: str = "https://api.astroos.dev/v1"
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    retry_backoff: float = 1.5
