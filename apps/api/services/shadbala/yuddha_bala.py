"""
AstroOS — Yuddha Bala (SHADBALA-YUDDHA)

Kala Bala's final sub-component — planetary war (Graha Yuddha). Two of
the 5 non-luminary grahas (Mars, Mercury, Jupiter, Venus, Saturn — Sun
and Moon are luminaries, not eligible; Rahu/Ketu are shadow points, also
not eligible) are considered "at war" when they occupy the same sign
and are within a tight orb (~1°) of each other. The winner gains a
strength bonus; the loser gets nothing from this component.

**Explicitly an approximated rule on two fronts, not verified classical
fidelity — same honesty treatment as every other non-trivial Kala Bala
component:**

1. Winner determination varies across classical sources. This uses the
   commonly-cited "more southern celestial latitude wins" convention
   (now computable via `SiderealPosition.latitude_deg`, available since
   Module 9 Phase 0) — other sources use different tie-breakers (e.g.
   greater longitude/degree). Not independently verified against a
   single primary source.
2. The winner's bonus magnitude (30 Shashtiamsas here) is a defensible
   round value consistent with this codebase's other binary Kala Bala
   components (Drekkana, Tribhaga), not derived from or verified against
   a classical coefficient table specific to Yuddha Bala.

A tie (identical latitude — vanishingly unlikely with real ephemeris
data, but handled explicitly rather than left to silently favor one
side) results in neither planet being declared a winner.
"""

from __future__ import annotations

from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.ephemeris import SiderealPosition
from packages.shared.degrees import shorter_arc_distance as _angular_distance

_COMPONENT_ID = "SHADBALA-YUDDHA"
_COMPONENT_NAME = "Yuddha Bala"
_RULE_VERSION = "1.0"

_WINNER_BONUS = 30.0
_WAR_ORB_DEG = 1.0

_ELIGIBLE_PLANETS = ["mars", "mercury", "jupiter", "venus", "saturn"]


def _find_war_opponent(
    planet: str, planets_by_name: dict[str, SiderealPosition]
) -> SiderealPosition | None:
    """Find the other eligible planet (if any) this planet is at war with."""
    this_position = planets_by_name[planet]
    for other_name, other_position in planets_by_name.items():
        if other_name == planet or other_name not in _ELIGIBLE_PLANETS:
            continue
        if this_position.rashi != other_position.rashi:
            continue
        distance = _angular_distance(this_position.sidereal_longitude, other_position.sidereal_longitude)
        if distance <= _WAR_ORB_DEG:
            return other_position
    return None


class YuddhaBalaCalculator:
    """Stateless — needs only sidereal_longitude, rashi, and latitude_deg (all on SiderealPosition)."""

    def calculate(
        self, planet: str, planets: list[SiderealPosition]
    ) -> BalaComponentResult:
        if planet not in _ELIGIBLE_PLANETS:
            raise ValueError(
                f"Yuddha Bala is only reported for the 5 non-luminary grahas "
                f"(Mars/Mercury/Jupiter/Venus/Saturn), got {planet!r}"
            )

        planets_by_name = {p.planet: p for p in planets}
        if planet not in planets_by_name:
            return BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=0.0, trace=(f"{planet} not found in chart",),
            )

        trace: list[str] = []
        opponent = _find_war_opponent(planet, planets_by_name)

        if opponent is None:
            trace.append(f"{planet}: no other eligible graha within {_WAR_ORB_DEG}° in the same sign — not at war")
            return BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=0.0, trace=tuple(trace),
            )

        this_position = planets_by_name[planet]
        distance = _angular_distance(this_position.sidereal_longitude, opponent.sidereal_longitude)
        trace.append(
            f"{planet} at war with {opponent.planet}: same sign ({this_position.rashi}), "
            f"orb {distance:.4f}° (within {_WAR_ORB_DEG}°)"
        )
        trace.append(
            f"Latitude: {planet}={this_position.latitude_deg:.4f}°, "
            f"{opponent.planet}={opponent.latitude_deg:.4f}° (more southern wins)"
        )

        if this_position.latitude_deg == opponent.latitude_deg:
            trace.append("Exact latitude tie — no winner declared")
            value = 0.0
        elif this_position.latitude_deg < opponent.latitude_deg:
            trace.append(f"{planet} is more southern — wins")
            value = _WINNER_BONUS
        else:
            trace.append(f"{opponent.planet} is more southern — {planet} loses")
            value = 0.0

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=value, trace=tuple(trace),
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        return [self.calculate(planet, planets) for planet in _ELIGIBLE_PLANETS]
