"""
AstroOS — Aspect Engine (Module 7)

Independent service computing Graha drishti (aspects) between planets.

Extracted verbatim from horoscope_engine.py's previous
_compute_aspects()/_classify_aspect() — same algorithm, relocated, not
reworked.

Vedic aspect rules implemented:
  - All grahas aspect the 7th house from their position (opposition).
  - Mars additionally aspects the 4th and 8th.
  - Jupiter additionally aspects the 5th and 9th.
  - Saturn additionally aspects the 3rd and 10th.
  - Rahu/Ketu aspect the 5th, 7th, 9th (by some traditions — same as
    Jupiter's special aspects).
"""

from __future__ import annotations

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import AspectInfo

# Special graha aspects in Vedic astrology (in addition to 7th house opposition)
# Graha -> set of house offsets it aspects (counted from its own house)
SPECIAL_ASPECTS: dict[str, set[int]] = {
    "mars":    {4, 7, 8},
    "jupiter": {5, 7, 9},
    "saturn":  {3, 7, 10},
    "rahu":    {5, 7, 9},   # Same as Jupiter by many traditions
    "ketu":    {5, 7, 9},
}

# All planets aspect the 7th from their position
UNIVERSAL_ASPECT = 7

# Orb for graha aspect (degrees within the aspected sign's cusp)
ASPECT_ORB = 5.0

_VALID_ASPECT_TYPES = {"conjunction", "opposition", "trine", "square", "special_graha"}


class AspectEngine:
    """
    Stateless service computing all pairwise Graha aspects (drishti) for
    a set of planet positions. No Swiss Ephemeris or database dependency.
    """

    def compute(self, planets: list[SiderealPosition]) -> list[AspectInfo]:
        """
        Compute all graha drishti (aspects) between planets.

        Identical algorithm to horoscope_engine.py's previous
        _compute_aspects() — relocated here, not reworked.
        """
        aspects: list[AspectInfo] = []

        for from_planet in planets:
            aspect_houses = {UNIVERSAL_ASPECT}
            aspect_houses.update(SPECIAL_ASPECTS.get(from_planet.planet, set()))

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

                    aspect_type = self.classify(house_offset)

                    aspects.append(AspectInfo(
                        from_planet=from_planet.planet,
                        to_planet=to_planet.planet,
                        aspect_type=aspect_type,
                        orb_degrees=round(orb, 4),
                        is_applying=False,  # Speed not stored in SiderealPosition
                    ))

        return aspects

    def classify(self, house_offset: int) -> str:
        """Classify a Vedic aspect by house offset."""
        if house_offset == 1:
            return "conjunction"
        if house_offset == 7:
            return "opposition"
        if house_offset in (5, 9):
            return "trine"
        if house_offset in (4, 10):
            return "square"
        return "special_graha"
