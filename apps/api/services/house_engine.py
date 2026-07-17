"""
AstroOS — House Engine (Module 6)

Independent service for bhava (house)-level analysis: classical house-type
classification (kendra/panapara/apoklima quadrants, trikona, dusthana,
upachaya), house lordship (which Graha rules a house's sign), and which
planets occupy each house.

This is new completion work, not an extraction — horoscope_engine.py
never computed house lordship or full quadrant classification; it only
used the kendra/trikona/dusthana sets internally for planet strength
scoring (see graha_engine.py). House cusps themselves (longitude, sign)
still come from EphemerisWrapper — this engine classifies and annotates
already-computed cusps, it does not calculate them.

Deliberately not wired into D1Chart/the API response — adding fields to
an existing response schema is a contract change outside the scope of
"complete this engine as an independent service." This engine is usable
standalone today; wiring its output into the D1 endpoint is a separate,
explicit decision for later.
"""

from __future__ import annotations

from apps.api.domain.ephemeris import HouseCusp, SiderealPosition
from apps.api.domain.house import HouseClassification, HouseInfo
from packages.shared.constants import SIGN_LORDS

KENDRA_HOUSES = {1, 4, 7, 10}
PANAPARA_HOUSES = {2, 5, 8, 11}
APOKLIMA_HOUSES = {3, 6, 9, 12}
TRIKONA_HOUSES = {1, 5, 9}
DUSTHANA_HOUSES = {6, 8, 12}
UPACHAYA_HOUSES = {3, 6, 10, 11}


class HouseEngine:
    """
    Stateless service for bhava classification, lordship, and occupancy.
    No Swiss Ephemeris or database dependency — operates purely on
    already-computed HouseCusp/SiderealPosition data.
    """

    def classify(self, house_number: int) -> HouseClassification:
        """Return the classical house-type classification for one bhava (1-12)."""
        if house_number in KENDRA_HOUSES:
            quadrant = "kendra"
        elif house_number in PANAPARA_HOUSES:
            quadrant = "panapara"
        else:
            quadrant = "apoklima"

        return HouseClassification(
            house_number=house_number,
            quadrant=quadrant,
            is_trikona=house_number in TRIKONA_HOUSES,
            is_dusthana=house_number in DUSTHANA_HOUSES,
            is_upachaya=house_number in UPACHAYA_HOUSES,
        )

    def get_house_lord(self, rashi: str) -> str:
        """The Graha that rules a house, based on the sign occupying its cusp."""
        return SIGN_LORDS[rashi]

    def build_house_summary(
        self,
        houses: list[HouseCusp],
        planets: list[SiderealPosition],
    ) -> list[HouseInfo]:
        """
        Combine house cusps with planet occupancy and classification into
        a full per-house analysis, one HouseInfo per bhava (1-12).
        """
        occupants_by_house: dict[int, list[str]] = {}
        for planet in planets:
            occupants_by_house.setdefault(planet.house_number, []).append(planet.planet)

        return [
            HouseInfo(
                house_number=house.house_number,
                rashi=house.rashi,
                lord=self.get_house_lord(house.rashi),
                occupants=occupants_by_house.get(house.house_number, []),
                classification=self.classify(house.house_number),
            )
            for house in houses
        ]
