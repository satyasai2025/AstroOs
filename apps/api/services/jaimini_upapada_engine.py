"""
AstroOS — Jaimini Native Upapada Analysis Engine
Classical Reference: Jaimini Upadesha Sutras (Adhyaya 1, Pada 4: Upapada Sutras 1.4.1-15).
Evaluates Upapada Lagna (UL / A12), 2nd from UL (longevity & harmony of partnership),
and 8th from UL (obstacles and divorce indicators).
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import UpapadaDeepAnalysis
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.jaimini_shared import house_count, rashi_at, rashi_index, signs_from
from apps.api.services.rashi_aspect_engine import RashiAspectEngine
from packages.shared.constants import SIGN_LORDS

_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
_MALEFICS = {"saturn", "mars", "rahu", "ketu", "sun"}


class JaiminiUpapadaAnalysisEngine:
    """
    Evaluates in-depth native Upapada Lagna (UL) dynamics.
    """

    def __init__(
        self,
        arudha_engine: Optional[ArudhaEngine] = None,
        rashi_aspect_engine: Optional[RashiAspectEngine] = None,
    ) -> None:
        self._arudha = arudha_engine or ArudhaEngine()
        self._aspect = rashi_aspect_engine or RashiAspectEngine()

    def analyze(self, chart: D1Chart) -> UpapadaDeepAnalysis:
        arudha_res = self._arudha.compute(chart)
        ul_pada = arudha_res.upapada_lagna  # A12
        ul_rashi = ul_pada.rashi
        ul_lord = ul_pada.lord
        ul_lord_rashi = ul_pada.lord_rashi

        # 2nd from UL
        h2_rashi = signs_from(ul_rashi, 1)  # +1 sign
        # 8th from UL
        h8_rashi = signs_from(ul_rashi, 7)  # +7 signs

        # Occupants in 2nd from UL
        h2_occupants = tuple(p.planet for p in chart.planets if p.rashi.lower() == h2_rashi)
        # Occupants in 8th from UL
        h8_occupants = tuple(p.planet for p in chart.planets if p.rashi.lower() == h8_rashi)

        # Rashi Drishti on 2nd from UL
        aspect_res = self._aspect.compute(chart)
        aspects_on_h2: list[str] = []
        for asp in aspect_res.aspects_on(h2_rashi):
            for pl in asp.aspecting_planets:
                aspects_on_h2.append(f"{pl.capitalize()} from {asp.from_rashi.capitalize()}")

        # Score calculations based on Jaimini Sutras 1.4.2-5
        score = 65.0  # baseline

        # Benefics in 2nd from UL give high stability
        for p in h2_occupants:
            if p.lower() in _BENEFICS:
                score += 15.0
            elif p.lower() in _MALEFICS:
                score -= 15.0

        # Aspects on 2nd from UL
        for asp in aspects_on_h2:
            p_name = asp.split()[0].lower()
            if p_name in _BENEFICS:
                score += 8.0
            elif p_name in _MALEFICS:
                score -= 8.0

        # 8th house malefic occupancy penalty
        for p in h8_occupants:
            if p.lower() in _MALEFICS:
                score -= 10.0

        score = min(100.0, max(15.0, score))

        if score >= 75.0:
            status = "Benefic / Highly Stable & Devoted Partnership"
            notes = "Benefic influence in 2nd from Upapada ensures mutual devotion, emotional longevity, and marital harmony (Jaimini Sutra 1.4.2)."
        elif score >= 50.0:
            status = "Moderate / Balanced Dynamics"
            notes = "Mixed planetary influences on Upapada 2nd house. Requires patience and constructive communication during testing transits."
        else:
            status = "Afflicted / Vulnerability to Friction or Obstacles"
            notes = "Malefic influence in 2nd/8th from Upapada indicates potential for domestic strain or differences requiring classical pariharas (Jaimini Sutra 1.4.4)."

        return UpapadaDeepAnalysis(
            upapada_rashi=ul_rashi.capitalize(),
            upapada_lord=ul_lord.capitalize(),
            upapada_lord_rashi=ul_lord_rashi.capitalize(),
            second_house_rashi=h2_rashi.capitalize(),
            second_house_occupants=h2_occupants,
            second_house_aspects=tuple(aspects_on_h2),
            second_house_status=status,
            eighth_house_rashi=h8_rashi.capitalize(),
            eighth_house_occupants=h8_occupants,
            relationship_longevity_score=round(score, 1),
            classical_notes=notes,
        )
