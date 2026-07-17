"""
AstroOS — Drekkana Bala (SHADBALA-DREKKANA)

Sthana Bala's decanate sub-component — a simple discrete rule based on
which third (10°) of a sign the planet occupies, and the planet's
classical gender:

    Male planets   (Sun, Mars, Jupiter)  — full bala in the 1st decanate (0-10°)
    Female planets (Moon, Venus)         — full bala in the 2nd decanate (10-20°)
    Neuter planets (Mercury, Saturn)     — full bala in the 3rd decanate (20-30°)

Full strength (15 Shashtiamsas) if the planet is in its matching
decanate for its gender, 0 otherwise — a binary rule, not graded,
consistent with Kendradi Bala's discrete-tier shape rather than Uchcha/
Dig Bala's continuous falloff.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.shadbala import BalaComponentResult

_COMPONENT_ID = "SHADBALA-DREKKANA"
_COMPONENT_NAME = "Drekkana Bala"
_RULE_VERSION = "1.0"

_MAX_VALUE = 15.0

_MALE_PLANETS = {"sun", "mars", "jupiter"}
_FEMALE_PLANETS = {"moon", "venus"}
_NEUTER_PLANETS = {"mercury", "saturn"}

# Which decanate index (0=1st, 1=2nd, 2=3rd) matches full strength, by gender.
_GENDER_TO_DECANATE = {"male": 0, "female": 1, "neuter": 2}

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def _gender_of(planet: str) -> str:
    if planet in _MALE_PLANETS:
        return "male"
    if planet in _FEMALE_PLANETS:
        return "female"
    return "neuter"  # mercury, saturn


class DrekkanaBalaCalculator:
    """Stateless — needs only a planet's own rashi_degree."""

    def calculate(self, position: SiderealPosition) -> BalaComponentResult:
        planet = position.planet
        if planet not in _CLASSICAL_SEVEN:
            raise ValueError(
                f"Drekkana Bala is only reported for the 7 classical grahas, got {planet!r}"
            )

        decanate = int(position.rashi_degree // 10)
        decanate = min(decanate, 2)  # guard against exactly 30.0 edge case
        gender = _gender_of(planet)
        expected_decanate = _GENDER_TO_DECANATE[gender]

        is_match = decanate == expected_decanate
        value = _MAX_VALUE if is_match else 0.0

        trace = (
            f"Step 1: {planet} classified as {gender} "
            f"(male: sun/mars/jupiter, female: moon/venus, neuter: mercury/saturn)",
            f"Step 2: {planet} at {position.rashi_degree:.4f}° within sign → decanate {decanate + 1} "
            f"(0-indexed {decanate})",
            f"Step 3: {gender} planets score full bala in decanate {expected_decanate + 1} "
            f"→ match={is_match}",
            f"Step 4: value = {value:.4f} Shashtiamsas",
        )

        return BalaComponentResult(
            component_id=_COMPONENT_ID, component_name=_COMPONENT_NAME,
            rule_version=_RULE_VERSION, planet=planet,
            value_shashtiamsas=value, trace=trace,
        )

    def calculate_all(self, planets: list[SiderealPosition]) -> list[BalaComponentResult]:
        return [self.calculate(p) for p in planets if p.planet in _CLASSICAL_SEVEN]
