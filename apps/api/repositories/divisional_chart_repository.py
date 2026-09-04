"""
AstroOS — Divisional Chart Repository

Persistence for the `divisional_charts` table (one row per computed varga,
e.g. D9, per birth chart).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models.astrology import DivisionalChartModel


class DivisionalChartRepository:
    """Data access for divisional chart identity rows. Takes an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_birth_chart(
        self,
        birth_chart_id: uuid.UUID,
        chart_type: str,
        *,
        lagna_rashi: Optional[str],
        lagna_degree: Optional[float],
    ) -> uuid.UUID:
        """
        Replace the divisional_charts row for (birth_chart_id, chart_type)
        and return its new id. Deleting the old row (if any) cascades to
        its divisional_planet_positions at the database level
        (ON DELETE CASCADE, defined in migration 0002) — no need to
        manually clear child rows first.
        """
        existing = await self._session.execute(
            select(DivisionalChartModel.id)
            .where(DivisionalChartModel.birth_chart_id == birth_chart_id)
            .where(DivisionalChartModel.chart_type == chart_type)
        )
        existing_id = existing.scalar_one_or_none()
        if existing_id is not None:
            await self._session.execute(
                delete(DivisionalChartModel).where(DivisionalChartModel.id == existing_id)
            )
            await self._session.flush()

        model = DivisionalChartModel(
            id=uuid.uuid4(),
            birth_chart_id=birth_chart_id,
            chart_type=chart_type,
            lagna_rashi=lagna_rashi,
            lagna_degree=Decimal(str(lagna_degree)) if lagna_degree is not None else None,
        )
        self._session.add(model)
        await self._session.flush()
        return model.id
