"""
AstroOS — Digital Twin Repository

Async persistence for DigitalTwinModel and TwinModificationModel.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.models.digital_twin import DigitalTwinModel, TwinModificationModel

class DigitalTwinRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_twin(self, twin_data: dict) -> DigitalTwinModel:
        """Create a new digital twin."""
        twin = DigitalTwinModel(**twin_data)
        self._session.add(twin)
        await self._session.flush()
        return twin

    async def get_twin(self, twin_id: uuid.UUID) -> Optional[DigitalTwinModel]:
        """
        Get a digital twin by ID with modifications loaded.

        populate_existing=True forces a fresh reload (including the
        `modifications` relationship) even if this twin is already
        tracked in the session's identity map — without it, callers that
        fetch the same twin twice in one request (e.g. add_modification's
        existence check, then its post-write reload) get back the same
        cached object with a stale, pre-write `modifications` collection.
        """
        result = await self._session.execute(
            select(DigitalTwinModel)
            .options(selectinload(DigitalTwinModel.modifications))
            .where(DigitalTwinModel.id == twin_id, DigitalTwinModel.deleted_at.is_(None))
            .execution_options(populate_existing=True)
        )
        return result.scalar_one_or_none()

    async def update_twin(self, twin_id: uuid.UUID, **kwargs) -> Optional[DigitalTwinModel]:
        """Update a digital twin."""
        await self._session.execute(
            update(DigitalTwinModel)
            .where(DigitalTwinModel.id == twin_id, DigitalTwinModel.deleted_at.is_(None))
            .values(**kwargs)
        )
        return await self.get_twin(twin_id)

    async def delete_twin(self, twin_id: uuid.UUID) -> bool:
        """Soft-delete a digital twin."""
        result = await self._session.execute(
            update(DigitalTwinModel)
            .where(DigitalTwinModel.id == twin_id, DigitalTwinModel.deleted_at.is_(None))
            .values(deleted_at=func.now())
        )
        return result.rowcount > 0

    async def add_modification(self, twin_id: uuid.UUID, modification_data: dict) -> TwinModificationModel:
        """Add a modification to a digital twin."""
        mod = TwinModificationModel(twin_id=twin_id, **modification_data)
        self._session.add(mod)
        await self._session.flush()
        return mod

    async def get_twins_by_user(self, user_id: uuid.UUID) -> list[DigitalTwinModel]:
        """Get all non-deleted digital twins for a user."""
        result = await self._session.execute(
            select(DigitalTwinModel)
            .where(DigitalTwinModel.user_id == user_id, DigitalTwinModel.deleted_at.is_(None))
            .order_by(DigitalTwinModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_twins_by_chart(self, chart_id: uuid.UUID) -> list[DigitalTwinModel]:
        """Get all digital twins for a specific birth chart."""
        result = await self._session.execute(
            select(DigitalTwinModel)
            .where(
                DigitalTwinModel.original_chart_id == chart_id,
                DigitalTwinModel.deleted_at.is_(None)
            )
            .order_by(DigitalTwinModel.created_at.desc())
        )
        return list(result.scalars().all())
