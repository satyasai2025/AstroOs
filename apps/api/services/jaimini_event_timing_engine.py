"""
AstroOS — Jaimini Predictive Event Timing Engine
Classical Reference: K.N. Rao (Predicting through Jaimini's Chara Dasha), Jaimini Upadesha Sutras.
Synthesizes active Jaimini Dashas (Chara, Shoola, Mandooka), Chara Karakas, and Arudha Padas
to predict high-probability event timing windows.
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.jaimini import (
    CharaKarakaScheme,
    JaiminiDashaPeriod,
    JaiminiDashaResult,
    JaiminiEventTimingWindow,
)
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jaimini_shared import house_count, rashi_at, rashi_index, signs_from
from apps.api.services.jaimini_special_dashas import MandookaDashaEngine, ShoolaDashaEngine
from apps.api.services.rashi_aspect_engine import RashiAspectEngine


class JaiminiEventTimingEngine:
    """
    Synthesizes Jaimini dasha cycles with Chara Karakas and Arudhas for predictive timing.
    """

    def __init__(
        self,
        chara_karaka_engine: Optional[CharaKarakaEngine] = None,
        arudha_engine: Optional[ArudhaEngine] = None,
        rashi_aspect_engine: Optional[RashiAspectEngine] = None,
        shoola_engine: Optional[ShoolaDashaEngine] = None,
        mandooka_engine: Optional[MandookaDashaEngine] = None,
    ) -> None:
        self._karaka = chara_karaka_engine or CharaKarakaEngine()
        self._arudha = arudha_engine or ArudhaEngine()
        self._aspect = rashi_aspect_engine or RashiAspectEngine()
        self._shoola = shoola_engine or ShoolaDashaEngine()
        self._mandooka = mandooka_engine or MandookaDashaEngine()

    def generate_timing_windows(
        self,
        d1_chart: D1Chart,
        start_date: date,
        chara_dasha_res: JaiminiDashaResult,
        scheme: CharaKarakaScheme = "sapta_karaka",
    ) -> tuple[JaiminiEventTimingWindow, ...]:
        karakas = self._karaka.compute(d1_chart, scheme=scheme)
        arudhas = self._arudha.compute(d1_chart)
        aspects = self._aspect.compute(d1_chart)
        shoola_res = self._shoola.compute(d1_chart, start_date)

        ak = karakas.atmakaraka
        amk = karakas.by_name("Amatyakaraka")
        dk = karakas.darakaraka
        pk = karakas.by_name("Putrakaraka")

        al = arudhas.arudha_lagna.rashi
        ul = arudhas.upapada_lagna.rashi
        a11 = arudhas.by_house(11).rashi

        windows: list[JaiminiEventTimingWindow] = []

        # 1. Career & Professional Timing (Chara Dasha on AmK / AL)
        for p in chara_dasha_res.periods[:6]:
            d_rashi = p.rashi.lower()
            triggers: list[str] = []
            score = 0.0

            if d_rashi == amk.rashi:
                triggers.append(f"Dasha sign matches Amatyakaraka ({amk.planet.capitalize()} in {amk.rashi.capitalize()}).")
                score += 45.0
            elif aspects.does_aspect(d_rashi, amk.rashi):
                triggers.append(f"Dasha sign casts Rashi Drishti on Amatyakaraka ({amk.planet.capitalize()} in {amk.rashi.capitalize()}).")
                score += 35.0

            if d_rashi == al:
                triggers.append(f"Dasha sign is Arudha Lagna ({al.capitalize()}).")
                score += 40.0
            elif aspects.does_aspect(d_rashi, al):
                triggers.append(f"Dasha sign casts Rashi Drishti on Arudha Lagna ({al.capitalize()}).")
                score += 25.0

            if triggers:
                windows.append(JaiminiEventTimingWindow(
                    event_category="Career & Status Elevation",
                    dasha_system="chara",
                    dasha_sign=p.rashi.capitalize(),
                    antardasha_sign=None,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    probability_score=min(95.0, score),
                    trigger_reasons=tuple(triggers),
                    classical_sutra="KN Rao / Jaimini Sutras 2.3: Dasha of sign containing or aspecting AmK/AL triggers significant professional advancement.",
                ))

        # 2. Marriage & Relationship Timing (Chara Dasha on DK / UL)
        for p in chara_dasha_res.periods[:6]:
            d_rashi = p.rashi.lower()
            triggers = []
            score = 0.0

            if d_rashi == dk.rashi:
                triggers.append(f"Dasha sign holds Darakaraka ({dk.planet.capitalize()} in {dk.rashi.capitalize()}).")
                score += 45.0
            elif aspects.does_aspect(d_rashi, dk.rashi):
                triggers.append(f"Dasha sign casts Rashi Drishti on Darakaraka ({dk.planet.capitalize()}).")
                score += 30.0

            if d_rashi == ul:
                triggers.append(f"Dasha sign is Upapada Lagna ({ul.capitalize()}).")
                score += 45.0
            elif aspects.does_aspect(d_rashi, ul):
                triggers.append(f"Dasha sign casts Rashi Drishti on Upapada Lagna ({ul.capitalize()}).")
                score += 30.0

            if triggers:
                windows.append(JaiminiEventTimingWindow(
                    event_category="Marriage & Committed Relationship",
                    dasha_system="chara",
                    dasha_sign=p.rashi.capitalize(),
                    antardasha_sign=None,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    probability_score=min(95.0, score),
                    trigger_reasons=tuple(triggers),
                    classical_sutra="Jaimini Sutras 1.4 / KN Rao: Chara Dasha related to DK or Upapada marks prime windows for marriage and union.",
                ))

        # 3. Wealth & Financial Timing (Chara Dasha on A11 / PK)
        for p in chara_dasha_res.periods[:6]:
            d_rashi = p.rashi.lower()
            triggers = []
            score = 0.0

            if d_rashi == a11 or aspects.does_aspect(d_rashi, a11):
                triggers.append(f"Dasha sign activates Labhapada A11 ({a11.capitalize()}).")
                score += 45.0
            if d_rashi == pk.rashi or aspects.does_aspect(d_rashi, pk.rashi):
                triggers.append(f"Dasha sign activates Putrakaraka ({pk.planet.capitalize()}).")
                score += 35.0

            if triggers:
                windows.append(JaiminiEventTimingWindow(
                    event_category="Wealth & Financial Windfall",
                    dasha_system="chara",
                    dasha_sign=p.rashi.capitalize(),
                    antardasha_sign=None,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    probability_score=min(90.0, score),
                    trigger_reasons=tuple(triggers),
                    classical_sutra="Jaimini Sutras 1.3: Dasha of Labhapada (A11) or PK brings wealth, speculative gains, and prosperity.",
                ))

        # 4. Health & Maraka Vulnerability (Shoola Dasha)
        lagna_rashi = d1_chart.ascendant.rashi.lower() if d1_chart.ascendant else "aries"
        h8_from_lagna = signs_from(lagna_rashi, 7)
        for p in shoola_res.periods[:4]:
            d_rashi = p.rashi.lower()
            triggers = []
            score = 0.0

            if d_rashi == h8_from_lagna or aspects.does_aspect(d_rashi, h8_from_lagna):
                triggers.append(f"Shoola Dasha activates 8th Ayur/Randhra house ({h8_from_lagna.capitalize()}).")
                score += 40.0
            if d_rashi == ak.rashi or aspects.does_aspect(d_rashi, ak.rashi):
                triggers.append(f"Shoola Dasha aspects Atmakaraka ({ak.planet.capitalize()}).")
                score += 30.0

            if triggers:
                windows.append(JaiminiEventTimingWindow(
                    event_category="Health & Vitality Caution",
                    dasha_system="shoola",
                    dasha_sign=p.rashi.capitalize(),
                    antardasha_sign=None,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    probability_score=min(85.0, score),
                    trigger_reasons=tuple(triggers),
                    classical_sutra="Jaimini Sutras 2.1 (Shoola Dasha): Trishoola/8th house activation requires health caution and remedial pariharas.",
                ))

        return tuple(windows)
