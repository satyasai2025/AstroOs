"""
AstroOS — House Repository

Persistence for the `houses` table (D1 house cusps).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.ephemeris import HouseCusp
from apps.api.models.astrology import HouseModel


class HouseRepository:
    """Data access for D1 house cusps. Constructor takes an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_chart(
        self,
        chart_id: uuid.UUID,
        houses: Sequence[HouseCusp],
    ) -> None:
        """
        Replace all houses rows for this chart. Delete-then-insert, same
        idempotency rationale as PlanetPositionRepository.replace_for_chart.
        """
        await self._session.execute(
            delete(HouseModel).where(HouseModel.chart_id == chart_id)
        )

        rows = [
            HouseModel(
                id=uuid.uuid4(),
                chart_id=chart_id,
                house_number=h.house_number,
                rashi=h.rashi,
                cusp_degree=Decimal(str(h.longitude)),  # tropical cusp longitude
                mid_degree=None,  # no domain equivalent (house-width midpoint) computed
            )
            for h in houses
        ]
        self._session.add_all(rows)
        await self._session.flush()
