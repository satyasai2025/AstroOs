"""
AstroOS — Event Analysis Repository

All database I/O for the EventAnalysisRecord aggregate, plus the
generated artifact snapshots. Returns domain objects
(domain/event_analysis.EventAnalysisRecord), never the ORM model directly —
same convention as EventRepository / UserRepository.

Two backing tables, both new:
  - `event_analyses`         — one analysis row (the aggregate root).
  - `event_chart_snapshots`  — generated artifacts (cast event chart,
    event-moment transit, active dasha chain), referenced by id. This is
    the "store references, not large chart JSON blobs" decision: the
    analysis row keeps only ids.

The creation flow is multi-step by design (create → run engine → persist
artifacts → mark complete), all within ONE request handled by the router —
this repository just exposes the granular steps.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.event_analysis import (
    EventAnalysisRecord,
    EventAnalysisStatus,
)
from apps.api.models.astrology import EventAnalysisModel, EventChartSnapshotModel


def _model_to_domain(model: EventAnalysisModel) -> EventAnalysisRecord:
    """Convert ORM row -> domain EventAnalysisRecord. Explicit, not magic —
    same convention as event_repository._model_to_domain()."""
    return EventAnalysisRecord(
        id=model.id,
        user_id=model.user_id,
        person_id=model.person_id,
        birth_chart_id=model.birth_chart_id,
        event_name=model.event_name,
        category=model.category,
        event_datetime_utc=model.event_datetime_utc,
        event_latitude=model.event_latitude,
        event_longitude=model.event_longitude,
        place_name=model.place_name,
        timezone_iana=model.timezone_iana,
        scope=frozenset(model.scope or []),
        status=EventAnalysisStatus(model.status),
        event_chart_id=model.event_chart_id,
        transit_chart_id=model.transit_chart_id,
        dasha_snapshot_id=model.dasha_snapshot_id,
        analysis_report_json=model.analysis_report_json,
        overall_score=model.overall_score,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class EventAnalysisRepository:
    """
    Data access for the EventAnalysisRecord aggregate + its artifact
    snapshots. Constructor accepts an AsyncSession injected by the DI
    layer, same shape as EventRepository. No global state; safe for
    concurrent requests.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Event analysis row ──────────────────────────────────────────────

    async def create_event(
        self,
        *,
        birth_chart_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        event_name: str,
        category: Optional[str],
        event_datetime_utc: datetime,
        event_latitude: Optional[float],
        event_longitude: Optional[float],
        place_name: Optional[str],
        timezone_iana: Optional[str],
        scope: frozenset[str],
        status: EventAnalysisStatus = EventAnalysisStatus.PENDING,
    ) -> EventAnalysisRecord:
        model = EventAnalysisModel(
            birth_chart_id=birth_chart_id,
            person_id=birth_chart_id,  # no separate Person table — the natal chart IS the person
            user_id=user_id,
            event_name=event_name.strip(),
            category=category,
            event_datetime_utc=event_datetime_utc,
            event_latitude=event_latitude,
            event_longitude=event_longitude,
            place_name=place_name,
            timezone_iana=timezone_iana,
            scope=sorted(scope),
            status=status.value,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_domain(model)

    async def get_by_id(self, event_id: uuid.UUID) -> Optional[EventAnalysisRecord]:
        stmt = (
            select(EventAnalysisModel)
            .where(EventAnalysisModel.id == event_id)
            .where(EventAnalysisModel.deleted_at.is_(None))
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _model_to_domain(row) if row else None

    async def list_for_chart(
        self,
        birth_chart_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventAnalysisRecord]:
        stmt = (
            select(EventAnalysisModel)
            .where(EventAnalysisModel.birth_chart_id == birth_chart_id)
            .where(EventAnalysisModel.deleted_at.is_(None))
            .order_by(EventAnalysisModel.event_datetime_utc.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [_model_to_domain(row) for row in result.scalars().all()]

    async def update_status(
        self,
        event_id: uuid.UUID,
        status: EventAnalysisStatus,
    ) -> Optional[EventAnalysisRecord]:
        stmt = (
            update(EventAnalysisModel)
            .where(EventAnalysisModel.id == event_id)
            .where(EventAnalysisModel.deleted_at.is_(None))
            .values(status=status.value)
            .returning(EventAnalysisModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_by_id(event_id)

    async def complete_event(
        self,
        event_id: uuid.UUID,
        *,
        event_chart_id: uuid.UUID,
        transit_chart_id: uuid.UUID,
        dasha_snapshot_id: uuid.UUID,
        analysis_report_json: dict,
        overall_score: Optional[float],
    ) -> Optional[EventAnalysisRecord]:
        stmt = (
            update(EventAnalysisModel)
            .where(EventAnalysisModel.id == event_id)
            .where(EventAnalysisModel.deleted_at.is_(None))
            .values(
                status=EventAnalysisStatus.COMPLETED.value,
                event_chart_id=event_chart_id,
                transit_chart_id=transit_chart_id,
                dasha_snapshot_id=dasha_snapshot_id,
                analysis_report_json=analysis_report_json,
                overall_score=overall_score,
            )
            .returning(EventAnalysisModel.id)
        )
        result = await self._session.execute(stmt)
        if result.scalar_one_or_none() is None:
            return None
        return await self.get_by_id(event_id)

    async def soft_delete(self, event_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        stmt = (
            update(EventAnalysisModel)
            .where(EventAnalysisModel.id == event_id)
            .where(EventAnalysisModel.deleted_at.is_(None))
            .values(deleted_at=now)
            .returning(EventAnalysisModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    # ── Artifact snapshots ──────────────────────────────────────────────

    async def create_snapshot(
        self,
        *,
        birth_chart_id: Optional[uuid.UUID],
        snapshot_type: str,
        label: Optional[str] = None,
    ) -> uuid.UUID:
        model = EventChartSnapshotModel(
            birth_chart_id=birth_chart_id,
            snapshot_type=snapshot_type,
            label=label,
        )
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def set_snapshot_payload(self, snapshot_id: uuid.UUID, payload: dict) -> None:
        await self._session.execute(
            update(EventChartSnapshotModel)
            .where(EventChartSnapshotModel.id == snapshot_id)
            .values(payload_json=payload)
        )

    async def get_snapshot_payload(self, snapshot_id: uuid.UUID) -> Optional[dict]:
        stmt = (
            select(EventChartSnapshotModel)
            .where(EventChartSnapshotModel.id == snapshot_id)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return row.payload_json if row else None