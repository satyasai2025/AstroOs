"""
AstroOS — SDK Service (Module 25, Phase 1)

API version metadata and helpers for the public API surface.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from apps.api.domain.sdk import ApiResponse, ApiVersion, Pagination


def _new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


_VERSIONS: dict[str, ApiVersion] = {
    "v1": ApiVersion(
        version="v1",
        status="current",
        release_notes="Initial release. Auth, Horoscope, Divisional, Dasha, Events APIs.",
    ),
}


class SdkService:
    """Utilities for API versioning, response envelope, and pagination."""

    @staticmethod
    def get_versions() -> dict[str, ApiVersion]:
        return dict(_VERSIONS)

    @staticmethod
    def get_version(version: str) -> Optional[ApiVersion]:
        return _VERSIONS.get(version)

    @staticmethod
    def success(
        data: Any = None,
        pagination: Optional[Pagination] = None,
        version: str = "v1",
    ) -> ApiResponse:
        return ApiResponse(
            success=True,
            data=data,
            pagination=pagination,
            version=version,
            request_id=_new_request_id(),
        )

    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
        version: str = "v1",
    ) -> ApiResponse:
        return ApiResponse(
            success=False,
            error=type("ApiError", (), {
                "code": code, "message": message, "details": details,
                "request_id": _new_request_id(), "docs_url": None,
            })(),
            version=version,
            request_id=_new_request_id(),
        )
