"""
AstroOS — Ayana Bala (SHADBALA-AYANA)

Kala Bala's declination-based sub-component. Graded by the planet's
equatorial declination (available since Module 9 Phase 0), scaled
against Earth's axial tilt (~23.4408°) and direction-weighted by
classical grouping:

    North-favoring (more bala with northern declination): Sun, Mars, Jupiter, Venus
    South-favoring (more bala with southern declination): Moon, Saturn
    Mercury: favors declination MAGNITUDE regardless of direction

**Explicitly an approximated formula, not verified classical fidelity —
same honesty treatment as Drik/Chesta/Saptavargaja/Tribhaga Bala.**
Classical Ayana Bala's exact formula (and which planets group which way)
varies somewhat across sources; this uses a linear scaling of
declination against the obliquity of the ecliptic, which is a
defensible, symmetric approximation but not independently verified
against a single primary source. Revisit if a verified formula becomes
available.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult

_COMPONENT_ID = "SHADBALA-AYANA"
_COMPONENT_NAME = "Ayana Bala"
_RULE_VERSION = "1.0"

_MAX_VALUE = 60.0
_OBLIQUITY_DEG = 23.4408  # Earth's axial tilt — the natural bound on solar declination

_NORTH_FAVORING = {"sun", "mars", "jupiter", "venus"}
_SOUTH_FAVORING = {"moon", "saturn"}
# mercury: favors magnitude regardless of direction

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class AyanaBalaCalculator:
    """Stateless — needs only a planet's declination_deg (available since Module 9 Phase 0)."""

    def calculate(self, position: SiderealPosition) -> BalaComponentResult:
        planet = position.planet
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Ayana Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        declination = position.declination_deg
        normalized = max(-1.0, min(1.0, declination / _OBLIQUITY_DEG))

        if planet == "mercury":
            value = 30.0 + abs(normalized) * 30.0
            trace_rule = "mercury favors declination magnitude regardless of direction"
        elif planet in _NORTH_FAVORING:
            value = 30.0 + normalized * 30.0
            trace_rule = f"{planet} favors northern declination"
        else:  # _SOUTH_FAVORING
            value = 30.0 - normalized * 30.0
            trace_rule = f"{planet} favors southern declination"

        value = max(0.0, min(60.0, value))

        trace = (
            f"Step 1: {planet} declination → {declination:.4f}°",
            f"Step 2: normalized against obliquity ({_OBLIQUITY_DEG}°) → {normalized:.4f}",
            f"Step 3: {trace_rule}",
            f"Step 4: value = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=trace,
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        return [self.calculate(p) for p in planets if p.planet in _CLASSICAL_SEVEN]
