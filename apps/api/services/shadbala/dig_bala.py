"""
AstroOS — Dig Bala (SHADBALA-DIG)

Directional strength — graded by angular distance from each planet's
"digbala point" (the cusp of its classically strongest house):

  Sun, Mars       — strongest at the 10th cusp (MC),  weakest at the 4th
  Moon, Venus     — strongest at the 4th cusp (IC),   weakest at the 10th
  Jupiter, Mercury — strongest at the 1st cusp (Asc),  weakest at the 7th
  Saturn          — strongest at the 7th cusp (Desc),  weakest at the 1st

Full strength (60 Shashtiamsas) exactly at the digbala point, tapering
linearly to zero at the exactly opposite point (180° away):
    Dig Bala = (180 - angular_distance) / 3
where angular_distance is the shorter-arc angular separation (0-180°)
between the planet and its digbala point's cusp — same "shorter arc"
convention already used elsewhere in this codebase (combustion orb,
AspectEngine's orb wraparound).

Needs only house cusp longitudes and planet longitude — both already
available from D1Chart, no Module 9 Phase 0 data required. Built second
in Phase 1 per the Design Audit's ordering.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import HouseCusp, SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult

_COMPONENT_ID = "SHADBALA-DIG"
_COMPONENT_NAME = "Dig Bala"
_RULE_VERSION = "1.0"

# planet -> digbala house number (the house whose cusp is this planet's digbala point)
_DIGBALA_HOUSE: dict[str, int] = {
    "sun": 10, "mars": 10,
    "moon": 4, "venus": 4,
    "jupiter": 1, "mercury": 1,
    "saturn": 7,
}


def _shorter_arc_distance(a: float, b: float) -> float:
    """Shorter-arc angular distance (0-180°) between two ecliptic longitudes."""
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


class DigBalaCalculator:
    """Stateless — needs only house cusps and a planet's own position."""

    def calculate(
        self,
        planet: str,
        position: SiderealPosition,
        houses: list[HouseCusp],
    ) -> BalaComponentResult:
        if planet not in _DIGBALA_HOUSE:
            raise ValueError(
                f"Dig Bala is only defined for the 7 classical grahas, got {planet!r}"
            )

        digbala_house_number = _DIGBALA_HOUSE[planet]
        digbala_cusp = next(h for h in houses if h.house_number == digbala_house_number)

        distance = _shorter_arc_distance(position.sidereal_longitude, digbala_cusp.sidereal_longitude)
        value = (180.0 - distance) / 3.0

        trace = (
            f"Step 1: {planet}'s digbala point is the {digbala_house_number}th house cusp "
            f"(sidereal longitude {digbala_cusp.sidereal_longitude:.4f}°)",
            f"Step 2: {planet}'s own sidereal longitude → {position.sidereal_longitude:.4f}°",
            f"Step 3: shorter-arc angular distance → {distance:.4f}°",
            f"Step 4: value = (180 - {distance:.4f}) / 3 = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=trace,
        )

    def calculate_all(
        self,
        planets: list[SiderealPosition],
        houses: list[HouseCusp],
    ) -> list[BalaComponentResult]:
        planets_by_name = {p.planet: p for p in planets}
        return [
            self.calculate(planet, planets_by_name[planet], houses)
            for planet in _DIGBALA_HOUSE
            if planet in planets_by_name
        ]
