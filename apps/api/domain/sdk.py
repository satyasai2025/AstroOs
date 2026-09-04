"""
AstroOS — SDK Domain Models (Module 25, Phase 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApiVersion:
    version: str
    status: str
    deprecated_at: str | None = None
    release_notes: str = ""


@dataclass(frozen=True)
class ApiError:
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


@dataclass
class Pagination:
    limit: int = 100
    offset: int = 0
    total: int | None = None


@dataclass
class ApiResponse:
    success: bool
    data: Any = None
    error: ApiError | None = None
    version: str = "v1"


@dataclass
class SdkConfig:
    base_url: str = "https://api.astroos.dev/v1"
    timeout: int = 30
    retry_count: int = 3
