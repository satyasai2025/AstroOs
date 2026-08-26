"""
AstroOS — Jaimini Upapada Lagna & D9 Navamsha Synastry Engine
Classical References: Jaimini Upadesha Sutras, Brihat Parashara Hora Shastra.
Evaluates Upapada Lagna (A12) alignment, 2nd house marital sustenance,
and D9 Navamsha harmonic cross-chart resonance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.ephemeris import SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.synastry import NavamshaSynastryResult, UpapadaCompatibility
from apps.api.services.synastry_engine import _RASHI_LORDS, _RASHI_ORDER


class JaiminiNavamshaSynastry:
    """
    Calculates Jaimini Upapada Lagna (UL) and D9 Navamsha Synastry compatibility.
    """

    @classmethod
    def calculate_upapada_rashi(cls, chart: D1Chart) -> str:
        """
        Computes Upapada Lagna (Arudha of 12th house, A12) with classical exceptions.
        """
        asc_rashi = chart.ascendant.rashi.lower() if chart.ascendant else "aries"
        asc_idx = _RASHI_ORDER.index(asc_rashi)

        # 12th house rashi
        h12_idx = (asc_idx + 11) % 12
        h12_rashi = _RASHI_ORDER[h12_idx]
        h12_lord = _RASHI_LORDS.get(h12_rashi, "sun")

        # Find 12th lord in chart
        lord_planet = next((p for p in chart.planets if p.planet.lower() == h12_lord), None)
        if not lord_planet:
            return h12_rashi

        lord_rashi = lord_planet.rashi.lower()
        lord_idx = _RASHI_ORDER.index(lord_rashi)

        # Distance from 12th house to 12th lord
        dist = ((lord_idx - h12_idx) % 12 + 12) % 12

        # Raw Arudha
        raw_arudha_idx = (lord_idx + dist) % 12

        # Classical Jaimini Exceptions: If Arudha is same house or 7th house, move 10 signs forward
        if raw_arudha_idx == h12_idx or raw_arudha_idx == (h12_idx + 6) % 12:
            raw_arudha_idx = (raw_arudha_idx + 9) % 12

        return _RASHI_ORDER[raw_arudha_idx]

    @classmethod
    def evaluate_upapada_compatibility(
        cls,
        chart_a: D1Chart,
        chart_b: D1Chart,
    ) -> UpapadaCompatibility:
        ul_a = cls.calculate_upapada_rashi(chart_a)
        ul_b = cls.calculate_upapada_rashi(chart_b)

        lagna_a = chart_a.ascendant.rashi.lower() if chart_a.ascendant else "aries"
        lagna_b = chart_b.ascendant.rashi.lower() if chart_b.ascendant else "aries"

        moon_a_p = next((p for p in chart_a.planets if p.planet.lower() == "moon"), None)
        moon_b_p = next((p for p in chart_b.planets if p.planet.lower() == "moon"), None)
        moon_a = moon_a_p.rashi.lower() if moon_a_p else "aries"
        moon_b = moon_b_p.rashi.lower() if moon_b_p else "aries"

        # Distance between UL of A and Lagna/Moon of B
        ul_a_idx = _RASHI_ORDER.index(ul_a)
        lagna_b_idx = _RASHI_ORDER.index(lagna_b)
        dist_ul_a_to_lagna_b = ((lagna_b_idx - ul_a_idx) % 12 + 12) % 12 + 1

        ul_b_idx = _RASHI_ORDER.index(ul_b)
        lagna_a_idx = _RASHI_ORDER.index(lagna_a)
        dist_ul_b_to_lagna_a = ((lagna_a_idx - ul_b_idx) % 12 + 12) % 12 + 1

        # Check alignment type
        if dist_ul_a_to_lagna_b in (1, 7) or dist_ul_b_to_lagna_a in (1, 7):
            align_type = "1/7 Axis (High Affinity)"
            score = 95.0
            harmonious = True
        elif dist_ul_a_to_lagna_b in (5, 9) or dist_ul_b_to_lagna_a in (5, 9):
            align_type = "Trinal 1/5/9 (Dharmic Resonance)"
            score = 85.0
            harmonious = True
        elif dist_ul_a_to_lagna_b in (4, 10) or dist_ul_b_to_lagna_a in (4, 10):
            align_type = "Mutual Kendra 1/4/10 (Active Engagement)"
            score = 75.0
            harmonious = True
        elif dist_ul_a_to_lagna_b in (3, 11) or dist_ul_b_to_lagna_a in (3, 11):
            align_type = "Sextile/Upachaya 3/11 (Growth)"
            score = 65.0
            harmonious = True
        else:
            align_type = "Shadashtaka/Dwirdwadasha 6/8/2/12 (Karmic Friction)"
            score = 40.0
            harmonious = False

        status_2nd_a = f"2nd from UL ({_RASHI_ORDER[(ul_a_idx + 1) % 12].capitalize()}) promotes sustenance of marriage."
        status_2nd_b = f"2nd from UL ({_RASHI_ORDER[(ul_b_idx + 1) % 12].capitalize()}) supports marital durability."

        explanation = (
            f"Upapada Lagna (UL) of Chart A is {ul_a.capitalize()} (aligned with Chart B Lagna {lagna_b.capitalize()} "
            f"in {dist_ul_a_to_lagna_b}th house relationship). "
            f"UL of Chart B is {ul_b.capitalize()} (aligned with Chart A Lagna {lagna_a.capitalize()} in {dist_ul_b_to_lagna_a}th house). "
            f"Alignment: {align_type} with Jaimini Confluence Score of {score:.1f}/100."
        )

        return UpapadaCompatibility(
            ul_rashi_a=ul_a.capitalize(),
            ul_rashi_b=ul_b.capitalize(),
            lagna_rashi_a=lagna_a.capitalize(),
            lagna_rashi_b=lagna_b.capitalize(),
            moon_rashi_a=moon_a.capitalize(),
            moon_rashi_b=moon_b.capitalize(),
            alignment_type=align_type,
            is_harmonious=harmonious,
            second_from_ul_status_a=status_2nd_a,
            second_from_ul_status_b=status_2nd_b,
            jaimini_compatibility_score=score,
            explanation=explanation,
        )

    @classmethod
    def calculate_navamsha_rashi(cls, longitude: float) -> str:
        """Computes the D9 Navamsha sign for a given sidereal longitude."""
        total_padas = int(longitude / (30.0 / 9.0)) % 108
        rashi_idx = total_padas % 12
        return _RASHI_ORDER[rashi_idx]

    @classmethod
    def evaluate_navamsha_synastry(
        cls,
        chart_a: D1Chart,
        chart_b: D1Chart,
    ) -> NavamshaSynastryResult:
        asc_a = chart_a.ascendant.sidereal_longitude if chart_a.ascendant else 0.0
        asc_b = chart_b.ascendant.sidereal_longitude if chart_b.ascendant else 0.0

        d9_lagna_a = cls.calculate_navamsha_rashi(asc_a)
        d9_lagna_b = cls.calculate_navamsha_rashi(asc_b)

        moon_a = next((p for p in chart_a.planets if p.planet.lower() == "moon"), None)
        moon_b = next((p for p in chart_b.planets if p.planet.lower() == "moon"), None)
        d9_moon_a = cls.calculate_navamsha_rashi(moon_a.sidereal_longitude) if moon_a else "aries"
        d9_moon_b = cls.calculate_navamsha_rashi(moon_b.sidereal_longitude) if moon_b else "aries"

        venus_a = next((p for p in chart_a.planets if p.planet.lower() == "venus"), None)
        venus_b = next((p for p in chart_b.planets if p.planet.lower() == "venus"), None)
        d9_venus_a = cls.calculate_navamsha_rashi(venus_a.sidereal_longitude) if venus_a else "aries"
        d9_venus_b = cls.calculate_navamsha_rashi(venus_b.sidereal_longitude) if venus_b else "aries"

        idx_la = _RASHI_ORDER.index(d9_lagna_a)
        idx_lb = _RASHI_ORDER.index(d9_lagna_b)
        dist = ((idx_lb - idx_la) % 12 + 12) % 12 + 1

        trines: list[str] = []
        if dist in (1, 7):
            rel = "Conjoined / 1/7 Axis (Soul Recognition)"
            score = 90.0
            trines.append(f"D9 Lagna Axis ({d9_lagna_a.capitalize()} & {d9_lagna_b.capitalize()})")
        elif dist in (5, 9):
            rel = "Trinal 5/9 (Dharmic Subconscious Harmony)"
            score = 85.0
            trines.append(f"D9 Lagna Trine ({d9_lagna_a.capitalize()} trine {d9_lagna_b.capitalize()})")
        elif dist in (4, 10):
            rel = "Kendra 1/4/10 (Constructive Private Dynamic)"
            score = 75.0
        elif dist in (3, 11):
            rel = "Upachaya 3/11 (Favorable Growth)"
            score = 70.0
        else:
            rel = "Shadashtaka 6/8 (Karmic Adjustments Needed)"
            score = 45.0

        # Check D9 Venus resonance
        idx_va = _RASHI_ORDER.index(d9_venus_a)
        idx_vb = _RASHI_ORDER.index(d9_venus_b)
        v_dist = ((idx_vb - idx_va) % 12 + 12) % 12 + 1
        if v_dist in (1, 5, 9, 7):
            score = min(100.0, score + 10.0)
            trines.append(f"D9 Venus Harmony ({d9_venus_a.capitalize()} with {d9_venus_b.capitalize()})")

        verdict = "EXCELLENT" if score >= 80 else "GOOD" if score >= 65 else "MODERATE"
        explanation = (
            f"D9 Navamsha Lagna relationship: {d9_lagna_a.capitalize()} to {d9_lagna_b.capitalize()} ({rel}). "
            f"D9 Moon alignment: {d9_moon_a.capitalize()} vs {d9_moon_b.capitalize()}. "
            f"D9 Venus alignment: {d9_venus_a.capitalize()} vs {d9_venus_b.capitalize()}."
        )

        return NavamshaSynastryResult(
            d9_lagna_a=d9_lagna_a.capitalize(),
            d9_lagna_b=d9_lagna_b.capitalize(),
            lagna_relationship=rel,
            d9_moon_a=d9_moon_a.capitalize(),
            d9_moon_b=d9_moon_b.capitalize(),
            d9_venus_a=d9_venus_a.capitalize(),
            d9_venus_b=d9_venus_b.capitalize(),
            mutual_d9_trines=tuple(trines),
            navamsha_harmony_score=round(score, 1),
            verdict=verdict,
            explanation=explanation,
        )
