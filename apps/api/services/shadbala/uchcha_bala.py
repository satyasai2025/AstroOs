"""
AstroOS — Uchcha Bala (SHADBALA-UCHCHA)

Sthana Bala's exaltation sub-component — graded by angular distance from
the planet's EXACT exaltation degree (not just sign match, unlike
GrahaEngine.is_exalted()'s boolean check). Full strength (60
Shashtiamsas) exactly at the exaltation point, tapering to zero exactly
at the debilitation point — always 180° away from exaltation by
classical definition, so the same shorter-arc/3 formula as Dig Bala
applies here with the exaltation point as the reference instead of a
house cusp.

Scoped to the 7 classical grahas, consistent with every other Shadbala
component in this codebase — EXALTATION_DEGREES technically has entries
for Rahu/Ketu, but Shadbala itself is not classically computed for them.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from packages.shared.constants import EXALTATION_DEGREES

_COMPONENT_ID = "SHADBALA-UCHCHA"
_COMPONENT_NAME = "Uchcha Bala"
_RULE_VERSION = "1.0"

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def _absolute_longitude(rashi: str, degree: float) -> float:
    return _RASHI_LIST.index(rashi) * 30.0 + degree


def _shorter_arc_distance(a: float, b: float) -> float:
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


class UchchaBalaCalculator:
    """Stateless — needs only a planet's own sidereal longitude."""

    def calculate(self, position: SiderealPosition) -> BalaComponentResult:
        planet = position.planet
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Uchcha Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        exalt_rashi, exalt_degree = EXALTATION_DEGREES[planet]
        exalt_absolute = _absolute_longitude(exalt_rashi, exalt_degree)

        distance = _shorter_arc_distance(position.sidereal_longitude, exalt_absolute)
        value = (180.0 - distance) / 3.0

        trace = (
            f"Step 1: {planet}'s exaltation point → {exalt_degree}° {exalt_rashi} "
            f"(absolute {exalt_absolute:.4f}°)",
            f"Step 2: {planet}'s own sidereal longitude → {position.sidereal_longitude:.4f}°",
            f"Step 3: shorter-arc angular distance from exaltation point → {distance:.4f}°",
            f"Step 4: value = (180 - {distance:.4f}) / 3 = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=trace,
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        planets_by_name = {p.planet: p for p in planets}
        return [
            self.calculate(planets_by_name[planet])
            for planet in _CLASSICAL_SEVEN
            if planet in planets_by_name
        ]
