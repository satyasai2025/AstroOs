"""
AstroOS — Research Query Log Service (Research Mode)

Logs all research queries/analyses when research mode is enabled, enabling
full reproducibility. Each log entry captures: timestamp, user, action type,
request parameters, response summary, and execution duration.

Research mode is a per-user toggle stored in a dedicated DB table so it
persists across sessions.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.research import ResearchModeSettingModel, ResearchQueryLogModel


class QueryLogService:
    """
    Service for research mode query logging.

    Constructed with a DB session. All methods are async.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Research Mode Toggle ───────────────────────────────────────────────

    async def is_research_mode(self, user_id: uuid.UUID) -> bool:
        """Check if research mode is enabled for a user."""
        stmt = select(ResearchModeSettingModel).where(
            ResearchModeSettingModel.user_id == user_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return row.enabled if row else False

    async def set_research_mode(self, user_id: uuid.UUID, enabled: bool) -> None:
        """Enable or disable research mode for a user."""
        stmt = select(ResearchModeSettingModel).where(
            ResearchModeSettingModel.user_id == user_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row:
            row.enabled = enabled
            row.updated_at = datetime.now(timezone.utc)
        else:
            self._session.add(
                ResearchModeSettingModel(user_id=user_id, enabled=enabled)
            )
        await self._session.flush()

    # ── Query Logging ─────────────────────────────────────────────────────

    async def log_query(
        self,
        user_id: uuid.UUID,
        action: str,
        request_payload: dict[str, Any],
        response_summary: str = "",
        duration_ms: int = 0,
    ) -> ResearchQueryLogModel:
        """
        Log a research query/action for reproducibility.

        Args:
            user_id: The user who performed the action.
            action: Action type (e.g. "workflow_analyze", "research_query",
                    "export", "hypothesis_generate", "snapshot_capture",
                    "snapshot_compare", "hypothesis_validate").
            request_payload: The full request parameters.
            response_summary: Brief summary of the response.
            duration_ms: Execution duration in milliseconds.

        Returns:
            The created ResearchQueryLogModel.
        """
        log = ResearchQueryLogModel(
            user_id=user_id,
            action=action,
            request_payload=json.dumps(request_payload, default=str),
            response_summary=response_summary[:500] if response_summary else "",
            duration_ms=duration_ms,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def get_logs(
        self,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple:
        """Retrieve query logs with optional filters."""
        stmt = select(ResearchQueryLogModel).order_by(
            ResearchQueryLogModel.created_at.desc()
        )
        if user_id:
            stmt = stmt.where(ResearchQueryLogModel.user_id == user_id)
        if action:
            stmt = stmt.where(ResearchQueryLogModel.action == action)
        stmt = stmt.offset(offset).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(rows)

    async def clear_logs(self, user_id: Optional[uuid.UUID] = None) -> int:
        """Clear query logs for a user (or all users if None)."""
        stmt = select(ResearchQueryLogModel)
        if user_id:
            stmt = stmt.where(ResearchQueryLogModel.user_id == user_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        for row in rows:
            await self._session.delete(row)
        await self._session.flush()
        return len(rows)

    async def count_logs(
        self,
        user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
    ) -> int:
        """Count query logs with optional filters."""
        stmt = select(ResearchQueryLogModel)
        if user_id:
            stmt = stmt.where(ResearchQueryLogModel.user_id == user_id)
        if action:
            stmt = stmt.where(ResearchQueryLogModel.action == action)
        rows = (await self._session.execute(stmt)).scalars().all()
        return len(rows)
