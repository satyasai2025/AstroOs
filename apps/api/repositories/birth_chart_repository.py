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
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
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
    ) -> uuid.UUID:
        """
        Find an existing birth_charts row for this exact birth input, or
        create one. Returns the row's id either way.
        """
        stmt = (
            select(BirthChartModel.id)
            .where(BirthChartModel.birth_datetime_utc == birth_datetime_utc)
            .where(BirthChartModel.birth_latitude == Decimal(str(latitude)))
            .where(BirthChartModel.birth_longitude == Decimal(str(longitude)))
            .where(BirthChartModel.ayanamsa == ayanamsa)
            .where(BirthChartModel.house_system == house_system)
            .where(BirthChartModel.deleted_at.is_(None))
        )
        if user_id is not None:
            stmt = stmt.where(BirthChartModel.user_id == user_id)

        existing_id = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing_id is not None:
            return existing_id

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
        )
        self._session.add(model)
        await self._session.flush()
        return model.id

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
