"""
AstroOS - Panchavargiya Bala (5-Fold Tajika Planetary Strength Engine)
Source: Tajika Neelakanthi (Panchavargiya Bala Chapter)
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from apps.api.domain.ephemeris import EphemerisResult
from apps.api.domain.varshaphal import PanchavargiyaBala
from apps.api.services.tajaka_constants import (
    DEEP_DEBILITATION,
    DEEP_EXALTATION,
    HADDA_TABLE,
)
from packages.shared.constants import SIGN_LORDS
from packages.shared.enums import Rashi

_RASHI_LIST: list[str] = [r.value for r in Rashi]
_TAJIKA_PLANETS: list[str] = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

_PLANET_RELATIONSHIPS: dict[str, dict[str, list[str]]] = {
    "sun": {"friends": ["moon", "mars", "jupiter"], "enemies": ["venus", "saturn"], "neutrals": ["mercury"]},
    "moon": {"friends": ["sun", "mercury"], "enemies": [], "neutrals": ["mars", "jupiter", "venus", "saturn"]},
    "mars": {"friends": ["sun", "moon", "jupiter"], "enemies": ["mercury"], "neutrals": ["venus", "saturn"]},
    "mercury": {"friends": ["sun", "venus"], "enemies": ["moon"], "neutrals": ["mars", "jupiter", "saturn"]},
    "jupiter": {"friends": ["sun", "moon", "mars"], "enemies": ["mercury", "venus"], "neutrals": ["saturn"]},
    "venus": {"friends": ["mercury", "saturn"], "enemies": ["sun", "moon"], "neutrals": ["mars", "jupiter"]},
    "saturn": {"friends": ["mercury", "venus"], "enemies": ["sun", "moon", "mars"], "neutrals": ["jupiter"]},
}


class TajakaBalaEngine:
    """Calculates Panchavargiya Bala for the 7 classical Grahas."""

    @classmethod
    def get_relationship(cls, planet: str, lord: str) -> str:
        if planet == lord:
            return "own"
        rel = _PLANET_RELATIONSHIPS.get(planet, {})
        if lord in rel.get("friends", []):
            return "friend"
        if lord in rel.get("enemies", []):
            return "enemy"
        return "neutral"

    @classmethod
    def get_hadda_lord(cls, rashi_index: int, rashi_deg: float) -> str:
        deg = max(0.0, min(30.0, rashi_deg))
        table = HADDA_TABLE.get(rashi_index % 12, HADDA_TABLE[0])
        for end_deg, lord in table:
            if deg <= end_deg:
                return lord
        return table[-1][1]

    @classmethod
    def get_drekkana_lord(cls, rashi_index: int, rashi_deg: float) -> str:
        deg = max(0.0, min(29.999999, rashi_deg))
        part = int(deg // 10.0)
        offset = part * 4
        target_rashi_idx = (rashi_index + offset) % 12
        return SIGN_LORDS[_RASHI_LIST[target_rashi_idx]]

    @classmethod
    def get_navamsha_lord(cls, rashi_index: int, rashi_deg: float) -> str:
        deg = max(0.0, min(29.999999, rashi_deg))
        pada = int(deg // (30.0 / 9.0))
        element = rashi_index % 4
        start_offsets = [0, 9, 6, 3]
        navamsha_idx = (start_offsets[element] + pada) % 12
        return SIGN_LORDS[_RASHI_LIST[navamsha_idx]]

    @classmethod
    def calculate_planet_bala(
        cls,
        planet: str,
        sidereal_longitude: float,
        rashi: str,
        rashi_degree: float,
    ) -> PanchavargiyaBala:
        rashi_idx = _RASHI_LIST.index(rashi)
        sign_lord = SIGN_LORDS[rashi]

        # 1. Kshetra Bala (Max 30 pts)
        kshetra_rel = cls.get_relationship(planet, sign_lord)
        if kshetra_rel == "own":
            kshetra_bala = 30.0
        elif kshetra_rel == "friend":
            kshetra_bala = 22.5
        elif kshetra_rel == "neutral":
            kshetra_bala = 15.0
        else:
            kshetra_bala = 7.5

        # 2. Uchcha Bala (Max 20 pts)
        deb_point = DEEP_DEBILITATION[planet]
        diff = abs(sidereal_longitude - deb_point) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        uchcha_bala = round((diff / 180.0) * 20.0, 4)

        # 3. Hadda Bala (Max 15 pts)
        hadda_lord = cls.get_hadda_lord(rashi_idx, rashi_degree)
        hadda_rel = cls.get_relationship(planet, hadda_lord)
        if hadda_rel == "own":
            hadda_bala = 15.0
        elif hadda_rel == "friend":
            hadda_bala = 11.25
        elif hadda_rel == "neutral":
            hadda_bala = 7.5
        else:
            hadda_bala = 3.75

        # 4. Drekkana Bala (Max 10 pts)
        drekkana_lord = cls.get_drekkana_lord(rashi_idx, rashi_degree)
        drekkana_rel = cls.get_relationship(planet, drekkana_lord)
        if drekkana_rel == "own":
            drekkana_bala = 10.0
        elif drekkana_rel == "friend":
            drekkana_bala = 7.5
        elif drekkana_rel == "neutral":
            drekkana_bala = 5.0
        else:
            drekkana_bala = 2.5

        # 5. Navamsha Bala (Max 5 pts)
        navamsha_lord = cls.get_navamsha_lord(rashi_idx, rashi_degree)
        navamsha_rel = cls.get_relationship(planet, navamsha_lord)
        if navamsha_rel == "own":
            navamsha_bala = 5.0
        elif navamsha_rel == "friend":
            navamsha_bala = 3.75
        elif navamsha_rel == "neutral":
            navamsha_bala = 2.5
        else:
            navamsha_bala = 1.25

        total_score = round(kshetra_bala + uchcha_bala + hadda_bala + drekkana_bala + navamsha_bala, 4)
        visheshika_bala = round(total_score / 4.0, 4)

        if visheshika_bala >= 15.0:
            category = "POORNA"
        elif visheshika_bala >= 10.0:
            category = "MADHYA"
        elif visheshika_bala >= 5.0:
            category = "ALPA"
        else:
            category = "HEENA"

        return PanchavargiyaBala(
            planet=planet,
            kshetra_bala=kshetra_bala,
            uchcha_bala=uchcha_bala,
            hadda_bala=hadda_bala,
            drekkana_bala=drekkana_bala,
            navamsha_bala=navamsha_bala,
            total_score=total_score,
            visheshika_bala=visheshika_bala,
            strength_category=category,
            hadda_lord=hadda_lord,
            drekkana_lord=drekkana_lord,
            navamsha_lord=navamsha_lord,
        )

    @classmethod
    def calculate_all(cls, varsha_chart: EphemerisResult) -> tuple[PanchavargiyaBala, ...]:
        balas: list[PanchavargiyaBala] = []
        positions = {p.planet: p for p in varsha_chart.planet_positions}

        for planet in _TAJIKA_PLANETS:
            pos = positions.get(planet)
            if pos is None:
                continue
            bala = cls.calculate_planet_bala(
                planet=planet,
                sidereal_longitude=pos.sidereal_longitude,
                rashi=pos.rashi,
                rashi_degree=pos.rashi_degree,
            )
            balas.append(bala)

        return tuple(balas)
