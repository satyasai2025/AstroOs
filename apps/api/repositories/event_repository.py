"""
AstroOS — Event Repository (Module 14, Phase 3)

All database I/O for the EventRecord aggregate lives here. Returns
domain objects (apps.api.domain.events.EventRecord), never the ORM
model directly — same convention as UserRepository. Service layer
(EventEngine) never imports SQLAlchemy directly; EventEngine's own
domain/service code (domain/events.py, services/event_engine.py,
services/dasha_lookup.py) is UNCHANGED by this module — this file only
adds persistence for the already-existing EventRecord domain object
against the already-existing `events` table (migration 0002) via the
already-existing EventModel (apps/api/models/astrology.py).

Uses the EXISTING `events` table/EventModel as-is — no new column, no
schema change. `fts_vector` is DB/trigger-managed and intentionally
never written by this repository, same reasoning as any other
DB-computed column this codebase leaves alone.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.events import EventRecord
from apps.api.models.astrology import EventModel

# Sentinel distinguishing "field not supplied" from "field explicitly
# set to None" in update() — needed because description/category/user_id
# are legitimately nullable fields a caller may want to clear.
_UNSET = object()


def _model_to_domain(model: EventModel) -> EventRecord:
    """Convert ORM row -> domain EventRecord. Explicit, not magic — same
    convention as user_repository.py's _model_to_domain()."""
    return EventRecord(
        id=model.id,
        chart_id=model.chart_id,
        event_date=model.event_date,
        title=model.title,
        user_id=model.user_id,
        description=model.description,
        category=model.category,
        is_verified=model.is_verified,
    )


class EventRepository:
    """
    Data access for the EventRecord aggregate.

    Constructor accepts an AsyncSession injected by the DI layer, same
    shape as UserRepository. No global state; safe for concurrent
    requests.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        chart_id: uuid.UUID,
        event_date: date,
        title: str,
        user_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        is_verified: bool = False,
    ) -> EventRecord:
        model = EventModel(
            chart_id=chart_id,
            user_id=user_id,
            event_date=event_date,
            title=title.strip(),
            description=description,
            category=category,
            is_verified=is_verified,
        )
        self._session.add(model)
        await self._session.flush()  # populate id + timestamps from DB
        await self._session.refresh(model)
        return _model_to_domain(model)

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[EventRecord]:
        stmt = (
            select(EventModel)
            .where(EventModel.id == event_id)
            .where(EventModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_domain(row) if row else None

    async def list_for_chart(
        self,
        chart_id: uuid.UUID,
        *,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventRecord]:
        """
        All non-deleted events for one chart, ordered by event_date
        (oldest first — a stable, predictable order for a timeline-
        shaped consumer without this repository knowing anything about
        timelines). `category` is an optional exact-match filter; no
        FK/enum enforcement, matching category's own free-string,
        "starting vocabulary, not exhaustive" status (Module 12).
        """
        stmt = (
            select(EventModel)
            .where(EventModel.chart_id == chart_id)
            .where(EventModel.deleted_at.is_(None))
        )
        if category is not None:
            stmt = stmt.where(EventModel.category == category)
        stmt = stmt.order_by(EventModel.event_date.asc()).limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return [_model_to_domain(row) for row in result.scalars().all()]

    async def update(
        self,
        event_id: uuid.UUID,
        *,
        title=_UNSET,
        description=_UNSET,
        category=_UNSET,
        is_verified=_UNSET,
        event_date=_UNSET,
    ) -> Optional[EventRecord]:
        """
        Partial update — only fields explicitly passed are changed;
        omitted fields (still `_UNSET`) are left untouched. This is why
        `_UNSET`, not `None`, is the default: `description=None` is a
        valid, meaningful "clear this field" request, not "don't touch
        this field."

        `chart_id` is deliberately NOT updatable — an event's chart
        association is immutable in this design; moving an event to a
        different chart is not a supported operation (create a new
        EventRecord on the correct chart instead).

        Returns the updated EventRecord, or None if no non-deleted
        event exists with this id (nothing to update).
        """
        values = {}
        if title is not _UNSET:
            values["title"] = title.strip()
        if description is not _UNSET:
            values["description"] = description
        if category is not _UNSET:
            values["category"] = category
        if is_verified is not _UNSET:
            values["is_verified"] = is_verified
        if event_date is not _UNSET:
            values["event_date"] = event_date

        if not values:
            return await self.get_by_id(event_id)

        stmt = (
            update(EventModel)
            .where(EventModel.id == event_id)
            .where(EventModel.deleted_at.is_(None))
            .values(**values)
            .returning(EventModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_by_id(event_id)

    async def soft_delete(self, event_id: uuid.UUID) -> bool:
        """
        Atomically marks an event as soft-deleted (WHERE deleted_at IS
        NULL + RETURNING id) — same atomic conditional-update pattern
        as UserRepository.revoke_session_by_jti(), so only one
        concurrent caller can succeed.

        Returns:
            True  — event was active and has now been soft-deleted by
                    this call.
            False — event was already deleted or does not exist.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(EventModel)
            .where(EventModel.id == event_id)
            .where(EventModel.deleted_at.is_(None))
            .values(deleted_at=now)
            .returning(EventModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
