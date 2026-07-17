"""
AstroOS — Kendradi Bala (SHADBALA-KENDRADI)

Sthana Bala's angular-house sub-component — a simple three-tier
discrete lookup based on which quadrant (from the lagna) the planet
occupies:
    Kendra   (1st/4th/7th/10th)  → 60 Shashtiamsas (full)
    Panapara (2nd/5th/8th/11th)  → 30 Shashtiamsas (half)
    Apoklima (3rd/6th/9th/12th)  → 15 Shashtiamsas (quarter)

Reuses the same quadrant classification HouseEngine already established
in Module 6.5 — this is not a new house-classification scheme, just a
different Shashtiamsa scale applied to the same three quadrant buckets.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.house_engine import HouseEngine

_COMPONENT_ID = "SHADBALA-KENDRADI"
_COMPONENT_NAME = "Kendradi Bala"
_RULE_VERSION = "1.0"

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

_QUADRANT_VALUES = {
    "kendra": 60.0,
    "panapara": 30.0,
    "apoklima": 15.0,
}


class KendradiBalaCalculator:
    """Stateless — needs only a planet's house number (via HouseEngine.classify())."""

    def __init__(self, house_engine: HouseEngine | None = None) -> None:
        self._house_engine = house_engine or HouseEngine()

    def calculate(self, position: SiderealPosition) -> BalaComponentResult:
        planet = position.planet
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Kendradi Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        classification = self._house_engine.classify(position.house_number)
        value = _QUADRANT_VALUES[classification.quadrant]

        trace = (
            f"Step 1: {planet} is in house {position.house_number} "
            f"→ quadrant = {classification.quadrant}",
            f"Step 2: value = {value:.4f} Shashtiamsas ({classification.quadrant} tier)",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=value, trace=trace,
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        return [self.calculate(p) for p in planets if p.planet in _CLASSICAL_SEVEN]
