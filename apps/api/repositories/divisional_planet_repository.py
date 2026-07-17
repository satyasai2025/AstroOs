"""
AstroOS — Divisional Planet Repository

Persistence for the `divisional_planet_positions` table (the 9 Graha
placements inside one computed varga chart).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.divisional import VargaPosition
from apps.api.models.astrology import DivisionalPlanetPositionModel


class DivisionalPlanetRepository:
    """Data access for varga planet placements. Constructor takes an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert(
        self,
        divisional_chart_id: uuid.UUID,
        planets: Sequence[VargaPosition],
    ) -> None:
        """
        Insert all planet placements for a freshly-created divisional chart
        row. No delete-then-insert needed here — the caller
        (DivisionalChartRepository.replace_for_birth_chart) always creates
        a brand new divisional_charts row first, so there is never a
        pre-existing set of divisional_planet_positions to clear for it.
        """
        rows = [
            DivisionalPlanetPositionModel(
                id=uuid.uuid4(),
                divisional_chart_id=divisional_chart_id,
                graha=p.planet,
                rashi=p.varga_rashi,
                house_number=p.varga_house_number,
                rashi_degree=Decimal(str(p.varga_rashi_degree)),
                dignity=None,  # not computed for varga charts by DivisionalEngine
            )
            for p in planets
        ]
        self._session.add_all(rows)
        await self._session.flush()
