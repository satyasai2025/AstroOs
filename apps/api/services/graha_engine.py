"""
AstroOS — Graha Engine (Module 5)

Independent service for Graha (planet)-level classification and strength
scoring: dignity flags (own sign / exalted / debilitated / moolatrikona)
and a composite strength score per planet.

Extracted from horoscope_engine.py, which previously computed this inline.
The scoring logic itself is unchanged — this is a relocation with one
small addition (is_moolatrikona), not a rework of the algorithm.

This is a dignitary + positional assessment, not full Shadbala (that is
Module 9 — Shadbala Engine, not yet built).
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import PlanetStrength
from packages.shared.constants import (
    DEBILITATION_RASHIS,
    EXALTATION_DEGREES,
    MOOLATRIKONA_RASHIS,
    OWN_SIGNS,
)
from packages.shared.dignity import compute_dignity_value

# ---------------------------------------------------------------------------
# House-type sets used by strength scoring (re-exported from here since
# horoscope_engine.py imports them from this module for backward
# compatibility with existing tests).
# ---------------------------------------------------------------------------

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}

_STRENGTH_WEIGHTS = {
    "exalted":      10.0,
    "moolatrikona":  8.0,
    "own":           7.0,
    "friendly":      5.0,
    "neutral":       4.0,
    "enemy":         2.5,
    "debilitated":   1.0,
}
_RETROGRADE_BONUS = 0.5    # Retrograde often strengthens (controversial; classical view)
_COMBUST_PENALTY = -2.0
_KENDRA_BONUS = 1.0
_TRIKONA_BONUS = 1.5
_DUSTHANA_PENALTY = -1.0


class GrahaEngine:
    """
    Stateless service for Graha dignity classification and strength
    scoring. No Swiss Ephemeris or database dependency — operates purely
    on already-computed SiderealPosition data.
    """

    def is_own_sign(self, planet: str, rashi: str) -> bool:
        return planet in OWN_SIGNS and rashi in OWN_SIGNS.get(planet, [])

    def is_exalted(self, planet: str, rashi: str) -> bool:
        if planet not in EXALTATION_DEGREES:
            return False
        exalted_rashi, _ = EXALTATION_DEGREES[planet]
        return rashi == exalted_rashi

    def is_debilitated(self, planet: str, rashi: str) -> bool:
        return planet in DEBILITATION_RASHIS and rashi == DEBILITATION_RASHIS[planet]

    def is_moolatrikona(self, planet: str, rashi: str) -> bool:
        """
        Whether this planet is in its Moolatrikona sign — a dignity level
        between exaltation and own sign, not previously exposed as its own
        flag anywhere in the codebase (MOOLATRIKONA_RASHIS already existed
        in packages/shared/constants.py but had no caller). Only defined
        for the 7 classical grahas that have one (not Rahu/Ketu).
        """
        return planet in MOOLATRIKONA_RASHIS and rashi == MOOLATRIKONA_RASHIS[planet]

    def compute_dignity(
        self, planet: str, rashi: str, rashi_degree: float
    ) -> Optional[DignityType]:
        """
        Full classical dignity (exalted/own/moolatrikona/friendly/
        neutral/enemy/debilitated) for a planet in a sign, at a given
        degree within that sign.

        Added in Module 9 Phase 2 as the prerequisite for Saptavargaja
        Bala (Shadbala): this method works identically whether `rashi`/
        `rashi_degree` come from a D1 chart's own SiderealPosition or a
        divisional chart's VargaPosition (varga_rashi/varga_rashi_degree)
        — dignity is defined purely by (planet, sign, degree), not by
        which chart that placement came from. Delegates to
        packages.shared.dignity.compute_dignity_value(), which is also
        what EphemerisWrapper itself now uses for D1 dignity (previously
        a separate, duplicated implementation — consolidated here).

        This is the ONLY method on GrahaEngine that returns the full
        DignityType; is_own_sign()/is_exalted()/is_debilitated()/
        is_moolatrikona() remain as individual boolean checks for callers
        that only need one specific flag.
        """
        value = compute_dignity_value(planet, rashi, rashi_degree)
        return DignityType(value) if value is not None else None

    def compute_strength(
        self, planets: list[SiderealPosition]
    ) -> list[PlanetStrength]:
        """
        Compute a simplified strength score for each Graha.

        This is a dignitary + positional assessment, not full Shadbala.
        Score range: 0.0 - 10.0 (higher = stronger). Identical algorithm
        to horoscope_engine.py's previous _compute_planet_strengths —
        relocated here, not reworked.
        """
        strengths: list[PlanetStrength] = []

        for planet in planets:
            dignity = planet.dignity

            if dignity is not None:
                base = _STRENGTH_WEIGHTS.get(dignity.value, 4.0)
            else:
                base = 4.0  # neutral default for Rahu/Ketu

            score = base

            if planet.house_number in KENDRA_HOUSES:
                score += _KENDRA_BONUS
            if planet.house_number in TRIKONA_HOUSES:
                score += _TRIKONA_BONUS
            if planet.house_number in DUSTHANA_HOUSES:
                score += _DUSTHANA_PENALTY

            if planet.is_combust:
                score += _COMBUST_PENALTY
            if planet.is_retrograde:
                score += _RETROGRADE_BONUS

            score = round(max(0.0, min(10.0, score)), 2)

            strengths.append(PlanetStrength(
                planet=planet.planet,
                dignity=dignity,
                is_retrograde=planet.is_retrograde,
                is_combust=planet.is_combust,
                house_number=planet.house_number,
                is_in_own_sign=self.is_own_sign(planet.planet, planet.rashi),
                is_exalted=self.is_exalted(planet.planet, planet.rashi),
                is_debilitated=self.is_debilitated(planet.planet, planet.rashi),
                is_in_kendra=planet.house_number in KENDRA_HOUSES,
                is_in_trikona=planet.house_number in TRIKONA_HOUSES,
                is_in_dusthana=planet.house_number in DUSTHANA_HOUSES,
                strength_score=score,
            ))

        return sorted(strengths, key=lambda s: s.strength_score, reverse=True)
