"""
AstroOS — Hypothesis Validation Service

Manages the hypothesis validation workflow: flagging AI-generated hypotheses
for human review, and tracking confirmation/rejection decisions with
reviewer notes.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.research import HypothesisValidationModel


class HypothesisValidationService:
    """
    Service for hypothesis validation workflow.

    Constructed with a DB session. All methods are async.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def flag_hypothesis(
        self,
        hypothesis_id: str,
        chart_id: uuid.UUID,
        project_id: uuid.UUID,
        title: str,
        description: str,
        domain: str,
        hypothesis_data: dict[str, Any],
        ai_generated: bool = True,
    ) -> HypothesisValidationModel:
        """
        Flag a hypothesis for human review/confirmation.

        Args:
            hypothesis_id: The hypothesis template ID (e.g. 'HYP-001').
            chart_id: The chart this hypothesis was generated for.
            project_id: The research project this belongs to.
            title: Human-readable title.
            description: Full description of the hypothesis.
            domain: Knowledge domain (yoga, dignity, transit, etc.).
            hypothesis_data: The full hypothesis object as a dict.
            ai_generated: Whether this was AI-generated.

        Returns:
            The created HypothesisValidationModel.
        """
        validation = HypothesisValidationModel(
            hypothesis_id=hypothesis_id,
            chart_id=chart_id,
            project_id=project_id,
            title=title,
            description=description,
            domain=domain,
            hypothesis_data=json.dumps(hypothesis_data, default=str),
            ai_generated=ai_generated,
            status="pending",
        )
        self._session.add(validation)
        await self._session.flush()
        await self._session.refresh(validation)
        return validation

    async def confirm_hypothesis(
        self,
        validation_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Optional[HypothesisValidationModel]:
        """Mark a flagged hypothesis as confirmed by a human reviewer."""
        stmt = (
            select(HypothesisValidationModel)
            .where(HypothesisValidationModel.id == validation_id)
            .where(HypothesisValidationModel.deleted_at.is_(None))
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        row.status = "confirmed"
        row.reviewed_by = reviewer_id
        row.reviewed_at = datetime.now(timezone.utc)
        row.reviewer_notes = notes
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def reject_hypothesis(
        self,
        validation_id: uuid.UUID,
        reviewer_id: uuid.UUID,
        notes: Optional[str] = None,
    ) -> Optional[HypothesisValidationModel]:
        """Reject a flagged hypothesis with reviewer notes."""
        stmt = (
            select(HypothesisValidationModel)
            .where(HypothesisValidationModel.id == validation_id)
            .where(HypothesisValidationModel.deleted_at.is_(None))
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        row.status = "rejected"
        row.reviewed_by = reviewer_id
        row.reviewed_at = datetime.now(timezone.utc)
        row.reviewer_notes = notes
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_validation(
        self, validation_id: uuid.UUID,
    ) -> Optional[HypothesisValidationModel]:
        """Get a single validation record."""
        stmt = select(HypothesisValidationModel).where(
            HypothesisValidationModel.id == validation_id,
            HypothesisValidationModel.deleted_at.is_(None),
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_validations(
        self,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[HypothesisValidationModel, ...]:
        """
        List validation records with optional filters.

        Args:
            project_id: Filter by project.
            status: Filter by status (pending, confirmed, rejected).
            limit: Max results.
            offset: Pagination offset.

        Returns:
            Tuple of HypothesisValidationModel records.
        """
        stmt = (
            select(HypothesisValidationModel)
            .where(HypothesisValidationModel.deleted_at.is_(None))
            .order_by(HypothesisValidationModel.created_at.desc())
        )
        if project_id:
            stmt = stmt.where(HypothesisValidationModel.project_id == project_id)
        if status:
            stmt = stmt.where(HypothesisValidationModel.status == status)
        stmt = stmt.offset(offset).limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return tuple(rows)

    async def count_validations(
        self,
        project_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count validation records."""
        stmt = select(HypothesisValidationModel).where(
            HypothesisValidationModel.deleted_at.is_(None),
        )
        if project_id:
            stmt = stmt.where(HypothesisValidationModel.project_id == project_id)
        if status:
            stmt = stmt.where(HypothesisValidationModel.status == status)
        rows = (await self._session.execute(stmt)).scalars().all()
        return len(rows)

    async def delete_validation(self, validation_id: uuid.UUID) -> bool:
        """Soft-delete a validation record."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(HypothesisValidationModel)
            .where(HypothesisValidationModel.id == validation_id)
            .where(HypothesisValidationModel.deleted_at.is_(None))
            .values(deleted_at=now)
            .returning(HypothesisValidationModel.id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none() is not None
