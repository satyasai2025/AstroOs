"""
AstroOS — Horoscope Engine (Task 4)

Generates a D1 (Rashi / Janma Kundali) birth chart from:
  - A UTC datetime
  - Geographic coordinates
  - Ayanamsa system
  - House system

Responsibilities:
  - Orchestrates EphemerisWrapper calls
  - Computes graha aspects (drishti)
  - Calculates planet strength summary
  - Returns a D1Chart domain object

No database I/O here — persistence is the repository's concern.
"""

import logging
from datetime import datetime
from typing import Optional

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import AspectInfo, D1Chart, PlanetStrength
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import (
    DEBILITATION_RASHIS,
    EXALTATION_DEGREES,
    OWN_SIGNS,
)
from packages.shared.enums import AyanamsaSystem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KENDRA_HOUSES = {1, 4, 7, 10}
_TRIKONA_HOUSES = {1, 5, 9}
_DUSTHANA_HOUSES = {6, 8, 12}

# Special graha aspects in Vedic astrology (in addition to 7th house opposition)
# Graha → set of house numbers it aspects (counted from its own house)
_SPECIAL_ASPECTS: dict[str, set[int]] = {
    "mars":    {4, 7, 8},
    "jupiter": {5, 7, 9},
    "saturn":  {3, 7, 10},
    "rahu":    {5, 7, 9},   # Same as Jupiter by many traditions
    "ketu":    {5, 7, 9},
}

# All planets aspect the 7th from their position
_UNIVERSAL_ASPECT = 7

# Orb for graha aspect (degrees within the aspected sign's cusp)
_ASPECT_ORB = 5.0

# ---------------------------------------------------------------------------
# Strength scoring weights
# ---------------------------------------------------------------------------

_STRENGTH_WEIGHTS = {
    "exalted":     10.0,
    "moolatrikona": 8.0,
    "own":          7.0,
    "friendly":     5.0,
    "neutral":      4.0,
    "enemy":        2.5,
    "debilitated":  1.0,
}
_RETROGRADE_BONUS = 0.5    # Retrograde often strengthens (controversial; classical view)
_COMBUST_PENALTY = -2.0
_KENDRA_BONUS = 1.0
_TRIKONA_BONUS = 1.5
_DUSTHANA_PENALTY = -1.0


# ---------------------------------------------------------------------------
# HoroscopeEngine
# ---------------------------------------------------------------------------

class HoroscopeEngine:
    """
    Service that generates a complete D1 chart from birth data.

    Designed to be instantiated once per request (stateless per-request logic)
    and share the underlying EphemerisWrapper singleton across requests.
    """

    def __init__(self, wrapper: EphemerisWrapper) -> None:
        self._wrapper = wrapper

    def generate_d1(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = AyanamsaSystem.LAHIRI.value,
        house_system: str = "W",
    ) -> D1Chart:
        """
        Generate a complete D1 (Rashi) birth chart.

        Args:
            birth_datetime_utc: UTC birth datetime (must be timezone-aware).
            latitude: Geographic latitude (+N, -S).
            longitude: Geographic longitude (+E, -W).
            ayanamsa: Ayanamsa key (default: 'lahiri').
            house_system: House system code ('W'=Whole Sign, 'P'=Placidus).

        Returns:
            D1Chart with all positions, aspects, and strength assessments.
        """
        logger.info(
            "Generating D1 chart",
            extra={
                "datetime": birth_datetime_utc.isoformat(),
                "lat": latitude,
                "lon": longitude,
                "ayanamsa": ayanamsa,
                "house_system": house_system,
            },
        )

        ephe_result = self._wrapper.calculate(
            dt=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
            house_system=house_system,
        )

        aspects = self._compute_aspects(ephe_result.planet_positions)
        strengths = self._compute_planet_strengths(ephe_result.planet_positions)

        return D1Chart(
            ephemeris=ephe_result,
            ascendant=ephe_result.ascendant,
            houses=ephe_result.house_cusps,
            planets=ephe_result.planet_positions,
            aspects=aspects,
            planet_strengths=strengths,
            panchanga=ephe_result.panchanga,
            ayanamsa_system=ayanamsa,
            house_system=house_system,
        )

    # ── Aspects ───────────────────────────────────────────────────────────────

    def _compute_aspects(
        self, planets: list[SiderealPosition]
    ) -> list[AspectInfo]:
        """
        Compute all graha drishti (aspects) between planets.

        In Vedic astrology:
        - All grahas aspect the 7th house from their position (opposition).
        - Mars additionally aspects 4th and 8th.
        - Jupiter additionally aspects 5th and 9th.
        - Saturn additionally aspects 3rd and 10th.
        - Rahu/Ketu aspect 5th, 7th, 9th (by some traditions).
        """
        aspects: list[AspectInfo] = []
        planet_map = {p.planet: p for p in planets}

        for from_planet in planets:
            aspect_houses = {_UNIVERSAL_ASPECT}
            aspect_houses.update(_SPECIAL_ASPECTS.get(from_planet.planet, set()))

            for house_offset in aspect_houses:
                aspected_house = (
                    (from_planet.house_number - 1 + house_offset - 1) % 12
                ) + 1

                for to_planet in planets:
                    if to_planet.planet == from_planet.planet:
                        continue
                    if to_planet.house_number != aspected_house:
                        continue

                    # Calculate orb within the aspected sign
                    from_deg = from_planet.rashi_degree
                    to_deg = to_planet.rashi_degree
                    orb = abs(from_deg - to_deg)
                    if orb > 15:
                        orb = 30 - orb

                    aspect_type = self._classify_aspect(house_offset, from_planet.planet)
                    is_applying = from_planet.speed_deg_per_day > to_planet.speed_deg_per_day \
                        if hasattr(from_planet, 'speed_deg_per_day') else False

                    aspects.append(AspectInfo(
                        from_planet=from_planet.planet,
                        to_planet=to_planet.planet,
                        aspect_type=aspect_type,
                        orb_degrees=round(orb, 4),
                        is_applying=False,   # Speed not stored in SiderealPosition
                    ))

        return aspects

    def _classify_aspect(self, house_offset: int, planet: str) -> str:
        """Classify a Vedic aspect by house offset and planet."""
        if house_offset == 1:
            return "conjunction"
        if house_offset == 7:
            return "opposition"
        if house_offset in (5, 9):
            return "trine"
        if house_offset in (4, 10):
            return "square"
        return "special_graha"

    # ── Planet Strength ───────────────────────────────────────────────────────

    def _compute_planet_strengths(
        self, planets: list[SiderealPosition]
    ) -> list[PlanetStrength]:
        """
        Compute a simplified strength score for each Graha.

        This is a dignitary + positional assessment, not full Shadbala.
        Score range: 0.0 – 10.0 (higher = stronger).
        """
        strengths: list[PlanetStrength] = []

        for planet in planets:
            dignity = planet.dignity

            # Base score from dignity
            if dignity is not None:
                base = _STRENGTH_WEIGHTS.get(dignity.value, 4.0)
            else:
                base = 4.0   # neutral default for Rahu/Ketu

            score = base

            # Positional modifiers
            if planet.house_number in _KENDRA_HOUSES:
                score += _KENDRA_BONUS
            if planet.house_number in _TRIKONA_HOUSES:
                score += _TRIKONA_BONUS
            if planet.house_number in _DUSTHANA_HOUSES:
                score += _DUSTHANA_PENALTY

            # Status modifiers
            if planet.is_combust:
                score += _COMBUST_PENALTY
            if planet.is_retrograde:
                score += _RETROGRADE_BONUS

            score = round(max(0.0, min(10.0, score)), 2)

            is_own_sign = self._is_own_sign(planet.planet, planet.rashi)
            is_exalted = self._is_exalted(planet.planet, planet.rashi)
            is_debilitated = self._is_debilitated(planet.planet, planet.rashi)

            strengths.append(PlanetStrength(
                planet=planet.planet,
                dignity=dignity,
                is_retrograde=planet.is_retrograde,
                is_combust=planet.is_combust,
                house_number=planet.house_number,
                is_in_own_sign=is_own_sign,
                is_exalted=is_exalted,
                is_debilitated=is_debilitated,
                is_in_kendra=planet.house_number in _KENDRA_HOUSES,
                is_in_trikona=planet.house_number in _TRIKONA_HOUSES,
                is_in_dusthana=planet.house_number in _DUSTHANA_HOUSES,
                strength_score=score,
            ))

        return sorted(strengths, key=lambda s: s.strength_score, reverse=True)

    def _is_own_sign(self, planet: str, rashi: str) -> bool:
        return planet in OWN_SIGNS and rashi in OWN_SIGNS.get(planet, [])

    def _is_exalted(self, planet: str, rashi: str) -> bool:
        if planet not in EXALTATION_DEGREES:
            return False
        ex_rashi, _ = EXALTATION_DEGREES[planet]
        return rashi == ex_rashi

    def _is_debilitated(self, planet: str, rashi: str) -> bool:
        return planet in DEBILITATION_RASHIS and rashi == DEBILITATION_RASHIS[planet]
