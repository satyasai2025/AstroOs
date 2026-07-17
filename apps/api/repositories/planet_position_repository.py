"""
AstroOS — Planet Position Repository

Persistence for the `planet_positions` table (D1 Graha placements).

Schema note (found during implementation, not a calculation change):
apps.api.domain.ephemeris.SiderealPosition — the object HoroscopeEngine
actually returns — carries only the sidereal longitude, not the raw
tropical longitude, even though `planet_positions.longitude_deg` is
NOT NULL. The tropical longitude is recovered algebraically from data the
engine already returns (sidereal_longitude + ayanamsa_value, wrapped to
0-360), since sidereal = tropical - ayanamsa. This is arithmetic on
existing output, not a new astrological calculation.

`latitude_deg`, `speed_deg_per_day`, and `distance_au` were unavailable
here when this repository was first written (SiderealPosition didn't
carry them). As of Module 9 Phase 0 (Foundation Extension), the
ephemeris wrapper threads this data through, so all three are now
populated directly rather than left NULL. `nakshatra_id` is a FK to the
`nakshatras` reference table; that table IS seeded (migration 0005), but
resolving nakshatra name -> id here is still deferred — left NULL, same
as before — since wiring that lookup wasn't part of either persistence
pass.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.models.astrology import PlanetPositionModel


def _tropical_longitude(sidereal_longitude: float, ayanamsa_value: float) -> float:
    """sidereal = tropical - ayanamsa  =>  tropical = sidereal + ayanamsa."""
    return (sidereal_longitude + ayanamsa_value) % 360.0


class PlanetPositionRepository:
    """Data access for D1 planet positions. Constructor takes an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_chart(
        self,
        chart_id: uuid.UUID,
        planets: Sequence[SiderealPosition],
        *,
        ayanamsa_value_deg: float,
    ) -> None:
        """
        Replace all planet_positions rows for this chart with the given
        set. Delete-then-insert makes re-persisting the same chart_id
        idempotent (e.g. the caller re-requests the same D1 chart) instead
        of accumulating duplicate rows.
        """
        await self._session.execute(
            delete(PlanetPositionModel).where(PlanetPositionModel.chart_id == chart_id)
        )

        rows = [
            PlanetPositionModel(
                id=uuid.uuid4(),
                chart_id=chart_id,
                graha=p.planet,
                longitude_deg=Decimal(
                    str(_tropical_longitude(p.sidereal_longitude, ayanamsa_value_deg))
                ),
                sidereal_longitude_deg=Decimal(str(p.sidereal_longitude)),
                rashi=p.rashi,
                rashi_degree=Decimal(str(p.rashi_degree)),
                house_number=p.house_number,
                nakshatra_id=None,  # nakshatra name -> reference-table id lookup still not wired
                pada_number=p.pada,
                is_retrograde=p.is_retrograde,
                is_combust=p.is_combust,
                combustion_orb_deg=(
                    Decimal(str(p.combustion_orb)) if p.combustion_orb is not None else None
                ),
                dignity=p.dignity.value if p.dignity is not None else None,
                latitude_deg=Decimal(str(p.latitude_deg)),
                speed_deg_per_day=Decimal(str(p.speed_deg_per_day)),
                distance_au=Decimal(str(p.distance_au)),
            )
            for p in planets
        ]
        self._session.add_all(rows)
        await self._session.flush()
