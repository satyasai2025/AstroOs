"""
AstroOS — Birth Chart Repository

Persistence for the `birth_charts` table — the anchor row that
planet_positions, houses, divisional_charts, and dashas all hang off via
foreign key.

None of the current API request schemas (D1ChartRequest, VargaChartRequest,
DashaRequest) collect a subject name or a UTC offset, but `birth_charts`
requires both (`subject_name` NOT NULL, `timezone_offset_minutes` NOT NULL).
This repository fills them with defensible, non-fabricated defaults:
  - subject_name: caller-supplied, defaulting to "Unnamed" if omitted.
  - timezone_offset_minutes: derived from the already-validated
    timezone-aware birth_datetime_utc's own UTC offset (0 for a true UTC
    timestamp) — not guessed, just read off the datetime the caller sent.

get_or_create() deduplicates on the natural key (birth moment + location +
ayanamsa + house system) so repeated requests for the same subject (e.g. a
D1 call followed by a divisional call followed by a dasha call) reuse one
birth_charts row instead of creating a new one each time.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.astrology import BirthChartModel

_DEFAULT_SUBJECT_NAME = "Unnamed"


def _utc_offset_minutes(dt: datetime) -> int:
    """Read the UTC offset already carried by a timezone-aware datetime."""
    offset = dt.utcoffset()
    return int(offset.total_seconds() // 60) if offset is not None else 0


class BirthChartRepository:
    """
    Data access for the BirthChart aggregate root.

    Constructor accepts an AsyncSession injected by the DI layer, following
    the same pattern as UserRepository — no global state, safe for
    concurrent requests.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        *,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str,
        house_system: str,
        user_id: Optional[uuid.UUID] = None,
        subject_name: str = _DEFAULT_SUBJECT_NAME,
        place_name: Optional[str] = None,
    ) -> uuid.UUID:
        """
        Find an existing birth_charts row for this exact birth input, or
        create one. Returns the row's id either way.

        place_name was previously accepted nowhere in this pipeline —
        WorkflowAnalysisRequest had no such field, so every saved chart's
        place_name column stayed NULL regardless of what place the user
        searched for on the frontend. Now: on create, it's stored. On a
        dedup match against an existing row, if that row's place_name is
        still NULL and this call supplies one, it's backfilled — so a
        chart saved before this fix gets its place filled in the next
        time it's recomputed with the same birth data, without ever
        overwriting a place_name some other call already set.
        """
        stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.birth_datetime_utc == birth_datetime_utc)
            .where(BirthChartModel.birth_latitude == Decimal(str(latitude)))
            .where(BirthChartModel.birth_longitude == Decimal(str(longitude)))
            .where(BirthChartModel.ayanamsa == ayanamsa)
            .where(BirthChartModel.house_system == house_system)
            .where(BirthChartModel.deleted_at.is_(None))
        )
        if user_id is not None:
            stmt = stmt.where(BirthChartModel.user_id == user_id)

        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            if place_name and not existing.place_name:
                existing.place_name = place_name
                await self._session.flush()
            return existing.id

        # A user's very first saved chart becomes their default automatically
        # — checked before insert so it only ever fires once per user, and
        # only on this dedup-miss branch (a request that reuses an existing
        # row via the dedup match above never re-evaluates "is this the
        # first chart").
        is_first_chart = user_id is not None and await self.count_for_user(user_id) == 0

        model = BirthChartModel(
            id=uuid.uuid4(),
            user_id=user_id,
            subject_name=subject_name,
            birth_datetime_utc=birth_datetime_utc,
            birth_latitude=Decimal(str(latitude)),
            birth_longitude=Decimal(str(longitude)),
            timezone_offset_minutes=_utc_offset_minutes(birth_datetime_utc),
            ayanamsa=ayanamsa,
            house_system=house_system,
            place_name=place_name,
            is_default=is_first_chart,
        )
        self._session.add(model)
        await self._session.flush()
        return model.id

    async def set_default(self, chart_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Mark one of user_id's charts as their default, unsetting whichever
        chart (if any) held that flag before. Both updates happen in one
        flush so the partial unique index (migration 0016) never sees two
        True rows for the same user at once.

        Returns False (not an exception) for "doesn't exist", "already
        deleted", or "belongs to someone else" — same convention as
        soft_delete — so the router can uniformly 404 without leaking
        which case it was.
        """
        target_stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.id == chart_id)
            .where(BirthChartModel.user_id == user_id)
            .where(BirthChartModel.deleted_at.is_(None))
        )
        target = (await self._session.execute(target_stmt)).scalar_one_or_none()
        if target is None:
            return False

        if not target.is_default:
            previous_default_stmt = (
                select(BirthChartModel)
                .where(BirthChartModel.user_id == user_id)
                .where(BirthChartModel.is_default.is_(True))
                .where(BirthChartModel.deleted_at.is_(None))
            )
            previous_default = (await self._session.execute(previous_default_stmt)).scalar_one_or_none()
            if previous_default is not None:
                previous_default.is_default = False
            target.is_default = True
            await self._session.flush()
        return True

    async def update_d1_summary(
        self,
        chart_id: uuid.UUID,
        *,
        ayanamsa_value_deg: float,
        lagna_rashi: str,
        lagna_degree: float,
        moon_nakshatra: str,
    ) -> None:
        """
        Fill in the D1-derived summary columns. Only HoroscopeEngine calls
        this — a divisional-only or dasha-only request creates the
        birth_charts row via get_or_create() above but has no D1 chart to
        summarise, so these columns stay NULL until (if ever) a D1 request
        for the same subject fills them in.
        """
        model = await self._session.get(BirthChartModel, chart_id)
        if model is None:
            raise ValueError(f"No birth_charts row with id={chart_id}")
        model.ayanamsa_value_deg = Decimal(str(ayanamsa_value_deg))
        model.lagna_rashi = lagna_rashi
        model.lagna_degree = Decimal(str(lagna_degree))
        model.moon_nakshatra = moon_nakshatra
        await self._session.flush()

    async def get_by_id(self, chart_id: uuid.UUID) -> Optional[BirthChartModel]:
        """Fetch a single birth_charts row by id, or None if missing/deleted."""
        stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.id == chart_id)
            .where(BirthChartModel.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[BirthChartModel]:
        """
        List a user's saved charts, most recently created first. Used by
        the "my saved charts" history endpoint.
        """
        stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.user_id == user_id)
            .where(BirthChartModel.deleted_at.is_(None))
            .order_by(BirthChartModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        """Total count of a user's saved charts, for pagination."""
        stmt = (
            select(func.count())
            .select_from(BirthChartModel)
            .where(BirthChartModel.user_id == user_id)
            .where(BirthChartModel.deleted_at.is_(None))
        )
        return (await self._session.execute(stmt)).scalar_one()

    async def soft_delete(self, chart_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Soft-delete a saved chart: sets deleted_at rather than removing the
        row, consistent with every other query in this repository already
        filtering `deleted_at.is_(None)` — the row (and everything hanging
        off it via FK: planet_positions, houses, divisional_charts, dashas)
        stays in the database, just excluded from all normal reads.

        Only deletes if the chart belongs to user_id — returns False (not
        an exception) for "doesn't exist", "already deleted", or "belongs
        to someone else", so the router can uniformly 404 on any of those
        without leaking which case it was.
        """
        stmt = (
            select(BirthChartModel)
            .where(BirthChartModel.id == chart_id)
            .where(BirthChartModel.user_id == user_id)
            .where(BirthChartModel.deleted_at.is_(None))
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        return True
