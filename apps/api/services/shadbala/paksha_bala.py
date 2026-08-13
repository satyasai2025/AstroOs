"""
AstroOS — Paksha Bala (SHADBALA-PAKSHA)

One of Kala Bala's six classical sub-components — built standalone here
rather than bundled into a single "Kala Bala" calculator, since the
other five sub-components (Nathonnata, Tribhaga, Varsha-Masa-Dina-Hora,
Ayana, Yuddha) are explicitly deferred (see shadbala_engine.py) pending
verification of their exact classical Shashtiamsa scales — Paksha Bala
is confident enough to implement now on its own.

Benefics gain strength as the Moon waxes toward full (Shukla Paksha);
malefics gain strength as the Moon wanes toward new (Krishna Paksha).
Graded continuously by the Moon-Sun angular separation (elongation),
not a binary waxing/waning flag — 0° elongation (new moon) to 180°
(full moon), then symmetrically back down to 0° at the next new moon.
This symmetric-distance-from-full-moon interpretation is consistent
with the commonly-cited qualitative description ("benefic strength
rises through Shukla Paksha, falls through Krishna Paksha") but, as
with Drik/Chesta Bala's caveats, exact coefficients can vary slightly
across classical sources — flagged here rather than assumed settled.

Benefic/malefic classification reused directly from
`yoga_predicates.NATURAL_BENEFICS`/`NATURAL_MALEFICS` (same simplified
static classification and Mercury/Moon caveat as elsewhere in this
codebase).
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.yoga_predicates import is_natural_benefic
from packages.shared.degrees import shorter_arc_distance as _shorter_arc_distance

_COMPONENT_ID = "SHADBALA-PAKSHA"
_COMPONENT_NAME = "Paksha Bala"
_RULE_VERSION = "1.0"

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


class PakshaBalaCalculator:
    """Stateless — needs only Moon and Sun's sidereal longitude."""

    def calculate(
        self, planet: str, planets: list[SiderealPosition]
    ) -> BalaComponentResult:
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Paksha Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        planets_by_name = {p.planet: p for p in planets}
        moon = planets_by_name.get("moon")
        sun = planets_by_name.get("sun")
        if moon is None or sun is None:
            return BalaComponentResult(
                component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
                rule_version=_RULE_VERSION, planet=planet,
                value_shashtiamsas=0.0,
                trace=("moon or sun not found in chart — cannot compute elongation",),
            )

        elongation = _shorter_arc_distance(moon.sidereal_longitude, sun.sidereal_longitude)
        is_benefic = is_natural_benefic(planet)

        trace = [
            f"Step 1: Moon-Sun elongation → {elongation:.4f}° (0=new moon, 180=full moon)",
            f"Step 2: {planet} classified as {'benefic' if is_benefic else 'malefic'}",
        ]

        if is_benefic:
            value = elongation / 180.0 * 60.0
            trace.append(f"Step 3: benefic → value = elongation/180 * 60 = {value:.4f}")
        else:
            value = (180.0 - elongation) / 180.0 * 60.0
            trace.append(f"Step 3: malefic → value = (180 - elongation)/180 * 60 = {value:.4f}")

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=round(value, 4), trace=tuple(trace),
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        return [self.calculate(planet, planets) for planet in _CLASSICAL_SEVEN]
