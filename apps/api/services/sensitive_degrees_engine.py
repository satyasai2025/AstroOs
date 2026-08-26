"""
AstroOS — Sensitive Degrees & Khara Lords Engine

Implements:
1. 64th Navamsha (from Moon and Lagna) and Khara Lord (D9)
2. 22nd Drekkana (from Lagna) and Khara Lord (D3)
3. Mrityu Bhaga (Classical fatal degrees table & proximity checker)
4. Pushkara Bhaga & Pushkara Navamsha
"""

from __future__ import annotations

import math
from typing import Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.sensitive_degrees import (
    KharaLordsResult,
    MrityuBhagaEvaluation,
    PushkaraEvaluation,
    SensitiveDegreesSnapshot,
)
from apps.api.services.divisional_engine import compute_varga_sign
from packages.shared.constants import SIGN_LORDS
from packages.shared.enums import Rashi

_RASHI_LIST = [r.value for r in Rashi]

# Classical Mrityu Bhaga table (Jataka Parijata Ch. 5 / Sarvartha Chintamani)
# Degrees per sign (Aries=0 .. Pisces=11)
_MRITYU_BHAGA_TABLE: dict[str, list[float]] = {
    "sun": [20.0, 9.0, 12.0, 6.0, 8.0, 24.0, 16.0, 17.0, 22.0, 2.0, 3.0, 23.0],
    "moon": [26.0, 12.0, 13.0, 25.0, 24.0, 11.0, 26.0, 14.0, 13.0, 25.0, 5.0, 12.0],
    "mars": [19.0, 28.0, 25.0, 23.0, 29.0, 28.0, 14.0, 21.0, 2.0, 15.0, 11.0, 6.0],
    "mercury": [15.0, 14.0, 13.0, 12.0, 8.0, 18.0, 20.0, 10.0, 21.0, 22.0, 7.0, 5.0],
    "jupiter": [19.0, 29.0, 12.0, 27.0, 6.0, 4.0, 13.0, 10.0, 17.0, 11.0, 15.0, 28.0],
    "venus": [28.0, 15.0, 11.0, 17.0, 10.0, 13.0, 4.0, 6.0, 27.0, 12.0, 29.0, 19.0],
    "saturn": [10.0, 4.0, 7.0, 9.0, 12.0, 16.0, 3.0, 18.0, 28.0, 14.0, 13.0, 15.0],
    "rahu": [14.0, 13.0, 12.0, 11.0, 24.0, 23.0, 24.0, 11.0, 10.0, 8.0, 18.0, 20.0],
    "ketu": [8.0, 18.0, 20.0, 10.0, 21.0, 22.0, 7.0, 5.0, 14.0, 13.0, 12.0, 11.0],
    "lagna": [1.0, 9.0, 22.0, 22.0, 25.0, 2.0, 4.0, 23.0, 18.0, 20.0, 24.0, 10.0],
}

# Classical Pushkara Bhaga specific degrees per sign
_PUSHKARA_BHAGA_DEGREES: dict[str, float] = {
    "aries": 21.0,
    "taurus": 14.0,
    "gemini": 24.0,
    "cancer": 7.0,
    "leo": 19.0,
    "virgo": 12.0,
    "libra": 24.0,
    "scorpio": 13.0,
    "sagittarius": 9.0,
    "capricorn": 12.0,
    "aquarius": 21.0,
    "pisces": 19.0,
}

# 24 Pushkara Navamsha part indices (0-indexed 0..8 within sign)
_PUSHKARA_NAVAMSHA_PARTS: dict[str, tuple[int, ...]] = {
    # Fire signs: 7th (index 6) and 9th (index 8)
    "aries": (6, 8),
    "leo": (6, 8),
    "sagittarius": (6, 8),
    # Earth signs: 3rd (index 2) and 5th (index 4)
    "taurus": (2, 4),
    "virgo": (2, 4),
    "capricorn": (2, 4),
    # Air signs: 6th (index 5) and 8th (index 7)
    "gemini": (5, 7),
    "libra": (5, 7),
    "aquarius": (5, 7),
    # Water signs: 1st (index 0) and 3rd (index 2)
    "cancer": (0, 2),
    "scorpio": (0, 2),
    "pisces": (0, 2),
}


class SensitiveDegreesEngine:
    """Calculates Khara lords, Mrityu Bhaga, and Pushkara alignments."""

    def compute_khara_lords(self, chart: D1Chart) -> KharaLordsResult:
        moon_pos = next((p for p in chart.planets if p.planet.lower() == "moon"), None)
        moon_lon = moon_pos.sidereal_longitude if moon_pos else 0.0
        lagna_lon = chart.ascendant.sidereal_longitude

        # 64th Navamsha is at +210° (8th house cusp from source) in D9
        m64_lon = (moon_lon + 210.0) % 360.0
        m64_rashi, _ = compute_varga_sign("D9", m64_lon)
        m64_lord = SIGN_LORDS.get(m64_rashi.lower(), "")

        l64_lon = (lagna_lon + 210.0) % 360.0
        l64_rashi, _ = compute_varga_sign("D9", l64_lon)
        l64_lord = SIGN_LORDS.get(l64_rashi.lower(), "")

        # 22nd Drekkana is at +210° (8th house cusp from Lagna) in D3
        l22_lon = (lagna_lon + 210.0) % 360.0
        l22_rashi, _ = compute_varga_sign("D3", l22_lon)
        l22_lord = SIGN_LORDS.get(l22_rashi.lower(), "")

        return KharaLordsResult(
            moon_64th_navamsha_rashi=m64_rashi,
            moon_64th_navamsha_lord=m64_lord,
            moon_64th_navamsha_longitude=round(m64_lon, 6),
            lagna_64th_navamsha_rashi=l64_rashi,
            lagna_64th_navamsha_lord=l64_lord,
            lagna_64th_navamsha_longitude=round(l64_lon, 6),
            lagna_22nd_drekkana_rashi=l22_rashi,
            lagna_22nd_drekkana_lord=l22_lord,
            lagna_22nd_drekkana_longitude=round(l22_lon, 6),
        )

    def evaluate_mrityu_bhaga(
        self,
        point_name: str,
        rashi: str,
        rashi_deg: float,
        orb: float = 1.0,
    ) -> MrityuBhagaEvaluation:
        p_name = point_name.lower()
        r_name = rashi.lower()
        r_idx = _RASHI_LIST.index(r_name) if r_name in _RASHI_LIST else 0

        table = _MRITYU_BHAGA_TABLE.get(p_name, _MRITYU_BHAGA_TABLE["lagna"])
        mrityu_deg = table[r_idx]

        dist = abs(rashi_deg - mrityu_deg)
        is_active = dist <= orb

        return MrityuBhagaEvaluation(
            point=p_name,
            rashi=r_name,
            rashi_degree=round(rashi_deg, 4),
            mrityu_degree=mrityu_deg,
            orb_distance=round(dist, 4),
            is_in_mrityu_bhaga=is_active,
        )

    def evaluate_pushkara(
        self,
        point_name: str,
        sidereal_lon: float,
        rashi: str,
        rashi_deg: float,
        orb: float = 1.0,
    ) -> PushkaraEvaluation:
        r_name = rashi.lower()
        part_idx = min(8, int(rashi_deg / (30.0 / 9.0)))

        valid_parts = _PUSHKARA_NAVAMSHA_PARTS.get(r_name, ())
        is_pushk_nav = part_idx in valid_parts

        nav_rashi, _ = compute_varga_sign("D9", sidereal_lon)
        nav_lord = SIGN_LORDS.get(nav_rashi.lower(), "")

        pushk_bhaga_deg = _PUSHKARA_BHAGA_DEGREES.get(r_name, 15.0)
        dist_bhaga = abs(rashi_deg - pushk_bhaga_deg)
        is_pushk_bhaga = dist_bhaga <= orb

        return PushkaraEvaluation(
            point=point_name.lower(),
            rashi=r_name,
            rashi_degree=round(rashi_deg, 4),
            navamsha_rashi=nav_rashi,
            navamsha_lord=nav_lord,
            is_pushkara_navamsha=is_pushk_nav,
            pushkara_bhaga_degree=pushk_bhaga_deg,
            orb_distance_to_bhaga=round(dist_bhaga, 4),
            is_in_pushkara_bhaga=is_pushk_bhaga,
        )

    def compute_all(self, chart: D1Chart, orb: float = 1.0) -> SensitiveDegreesSnapshot:
        khara = self.compute_khara_lords(chart)

        mrityu_evals: list[MrityuBhagaEvaluation] = []
        pushkara_evals: list[PushkaraEvaluation] = []

        # Evaluate planets
        for p in chart.planets:
            p_name = p.planet.lower()
            mrityu_evals.append(
                self.evaluate_mrityu_bhaga(p_name, p.rashi, p.rashi_degree, orb=orb)
            )
            pushkara_evals.append(
                self.evaluate_pushkara(p_name, p.sidereal_longitude, p.rashi, p.rashi_degree, orb=orb)
            )

        # Evaluate Lagna
        asc_rashi = chart.ascendant.rashi
        asc_deg = chart.ascendant.rashi_degree
        asc_lon = chart.ascendant.sidereal_longitude
        mrityu_evals.append(
            self.evaluate_mrityu_bhaga("lagna", asc_rashi, asc_deg, orb=orb)
        )
        pushkara_evals.append(
            self.evaluate_pushkara("lagna", asc_lon, asc_rashi, asc_deg, orb=orb)
        )

        return SensitiveDegreesSnapshot(
            khara_lords=khara,
            mrityu_bhagas=tuple(mrityu_evals),
            pushkara_evaluations=tuple(pushkara_evals),
        )
