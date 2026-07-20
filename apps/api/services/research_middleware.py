"""
AstroOS — Research Mode Middleware

Optional ASGI middleware that logs research-related requests when research
mode is enabled for the requesting user. This is the automatic logging
component of the "Research Mode" feature.

This is a lightweight, non-invasive middleware that does not modify any
existing business logic. Logging failure never breaks the request.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Optional

from fastapi import Request, Response
from sqlalchemy import select

from apps.api.dependencies import _async_session_factory
from apps.api.models.research import ResearchModeSettingModel, ResearchQueryLogModel
from apps.api.security.jwt import decode_access_token

logger = logging.getLogger(__name__)

# Research-related URL prefixes that should be logged when research mode is on.
_RESEARCH_PATHS = (
    "/api/v1/workflow/analyze",
    "/api/v1/research/",
    "/api/v1/research-tools/",
    "/api/v1/ai/research-query",
    "/api/v1/ai/generate-hypotheses",
    "/api/v1/ai/compare-charts",
    "/api/v1/ai/enhanced-qa",
    "/api/v1/export/",
)


async def _extract_user_id(request: Request) -> Optional[uuid.UUID]:
    """Extract user ID from the Authorization header without raising exceptions."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            return uuid.UUID(user_id)
    except Exception:
        return None
    return None


def _get_action(path: str, method: str) -> str:
    """Derive an action label from the request path and method."""
    if "/workflow/analyze" in path:
        return "workflow_analyze"
    if method == "POST" and "/snapshots/compare" in path:
        return "snapshot_compare"
    if method == "POST" and "/charts/compare" in path:
        return "snapshot_compare"
    if method == "POST" and "/snapshots" in path and "/projects/" in path:
        return "snapshot_capture"
    if method == "POST" and "/projects" in path and "snapshots" not in path:
        return "project_create"
    if "/research-query" in path:
        return "research_query"
    if "/generate-hypotheses" in path:
        return "hypothesis_generate"
    if "/export/" in path:
        return "export"
    if "/compare-charts" in path:
        return "chart_compare"
    if "/enhanced-qa" in path:
        return "enhanced_qa"
    if "/validations" in path:
        return "hypothesis_validate"
    if "/research-tools/mode" in path:
        return "research_mode_toggle"
    if "/research-tools/logs" in path:
        return "query_log_view"
    return "research_action"


async def research_mode_logging_middleware(request: Request, call_next):
    """
    ASGI middleware that logs research-related requests when research mode
    is enabled for the requesting user.

    Reads the request body before downstream handlers consume it, processes
    the request, then logs asynchronously (log failure never impacts the response).
    """
    path = request.url.path

    # Fast-path: only process research-related endpoints.
    is_research = any(path.startswith(prefix) for prefix in _RESEARCH_PATHS)
    if not is_research:
        return await call_next(request)

    # Extract user before processing.
    user_id = await _extract_user_id(request)
    if user_id is None:
        return await call_next(request)

    # Read body before downstream handlers consume it.
    body_bytes = await request.body()

    # Process the request.
    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = int((time.time() - start_time) * 1000)

    # Asynchronously log (failure is non-critical).
    try:
        async with _async_session_factory() as session:
            stmt = select(ResearchModeSettingModel).where(
                ResearchModeSettingModel.user_id == user_id,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row and row.enabled:
                action = _get_action(path, request.method)
                payload: dict = {}
                if body_bytes:
                    try:
                        payload = json.loads(body_bytes)
                    except Exception:
                        payload = {"raw_body": body_bytes.decode("utf-8", errors="replace")[:500]}

                log_entry = ResearchQueryLogModel(
                    user_id=user_id,
                    action=action,
                    request_payload=json.dumps({
                        "method": request.method,
                        "path": path,
                        "params": dict(request.query_params),
                        "body": payload,
                    }, default=str),
                    response_summary=f"{response.status_code} {path}",
                    duration_ms=duration_ms,
                )
                session.add(log_entry)
                await session.commit()
    except Exception as exc:
        logger.debug("Research mode logging skipped (non-critical): %s", exc)

    return response
