"""
AstroOS — Classical Predictive Confluence Engine (Phase 8 - Step 1 & 2)
=======================================================================

Deterministic Classical Vedic Astrological Features:
1. Ashtakavarga:
   - Sarvashtakavarga (SAV) continuous sigmoid score of Domain Bhava centered at 28 bindus.
   - Bhinnashtakavarga (BAV) continuous normalized score of active Dasha / Antardasha lords.
2. Gochara (Multi-Point Double Transit Rule of Jupiter & Saturn):
   - Aspects across: (1) Domain Bhava, (2) Domain Lord, (3) Amatyakaraka (AmK).
   - Saturn aspects/occupies: 1st, 3rd, 7th, 10th.
   - Jupiter aspects/occupies: 1st, 5th, 7th, 9th.
3. Mutual Dasha Lord Geometry (Shadashtaka 6/8, Dwidwadasha 2/12 vs 1/4/5/7/9/10).
4. Continuous Confluence Synthesis ($C_{score} \in [0.0, 1.0]$) & Candidate Probability Synthesis Rule:
   - P_final = P_MoE * (0.50 + 0.50 * C_score)

Invariants:
- 100% Deterministic (Zero LLM / Zero Randomness).
- Shastric Alignment: BPHS, Phaladeepika, Jaimini Upadesha Sutras, and K.N. Rao principles.
- Frozen weights: 0.35 (SAV), 0.20 (BAV), 0.35 (Gochara), 0.10 (Geometry).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine

logger = logging.getLogger(__name__)

_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_RASHI_LORDS = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury", "cancer": "moon",
    "leo": "sun", "virgo": "mercury", "libra": "venus", "scorpio": "mars",
    "sagittarius": "jupiter", "capricorn": "saturn", "aquarius": "saturn", "pisces": "jupiter",
}


@dataclass(frozen=True)
class ContinuousConfluenceReport:
    """Detailed continuous confluence evaluation and candidate probability synthesis."""
    domain: str
    target_date: date
    # Raw Components
    sav_bindus: int
    sav_score: float                      # Continuous sigmoid score in [0.0, 1.0]
    md_bav_bindus: int
    ad_bav_bindus: int
    bav_score: float                      # Continuous normalized BAV score in [0.0, 1.0]
    # Multi-point Transit Aspects
    jupiter_aspects_house: bool
    jupiter_aspects_lord: bool
    jupiter_aspects_amk: bool
    saturn_aspects_house: bool
    saturn_aspects_lord: bool
    saturn_aspects_amk: bool
    gochara_score: float                  # Continuous double transit score in [0.0, 1.0]
    # Mutual Geometry
    dasha_mutual_houses: int
    dasha_geom_score: float               # 1.0 or 0.25 (for 6/8, 2/12)
    # Target Entities
    domain_bhava_rashi: str
    domain_lord: str
    domain_lord_rashi: str
    amatyakaraka: str
    amatyakaraka_rashi: str
    # Composite Confluence
    confluence_score: float               # Frozen composite scalar C_score in [0.0, 1.0]


@dataclass(frozen=True)
class ClassicalConfluenceReport:
    """Legacy binary report maintained for backwards-compatibility."""
    domain: str
    target_date: date
    domain_bhava_sav_bindus: int
    sav_pass: bool
    md_lord_bav_bindus: int
    ad_lord_bav_bindus: int
    bav_pass: bool
    transiting_jupiter_rashi: str
    transiting_saturn_rashi: str
    target_bhava_rashi: str
    jupiter_aspects_domain: bool
    saturn_aspects_domain: bool
    double_transit_pass: bool
    dasha_mutual_houses: int
    dasha_geometry_pass: bool
    confluence_score: float
    confluence_tier: str


class ClassicalFilterEngine:
    """Evaluates classical Ashtakavarga, Gochara, Jaimini Karakas, and Continuous Confluence."""

    def __init__(self, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.horoscope_engine = HoroscopeEngine(self.wrapper)
        self.ashtakavarga_engine = AshtakavargaEngine()

    def _house_rashi(self, lagna_rashi: str, house_num: int) -> str:
        idx = (_RASHI_ORDER.index(lagna_rashi.lower()) + house_num - 1) % 12
        return _RASHI_ORDER[idx]

    def _saturn_aspects(self, saturn_rashi: str, target_rashi: str) -> bool:
        """Saturn aspects 1st (conjunction), 3rd, 7th, and 10th houses from itself."""
        sat_idx = _RASHI_ORDER.index(saturn_rashi.lower())
        tgt_idx = _RASHI_ORDER.index(target_rashi.lower())
        diff = (tgt_idx - sat_idx) % 12 + 1
        return diff in (1, 3, 7, 10)

    def _jupiter_aspects(self, jupiter_rashi: str, target_rashi: str) -> bool:
        """Jupiter aspects 1st (conjunction), 5th, 7th, and 9th houses from itself."""
        jup_idx = _RASHI_ORDER.index(jupiter_rashi.lower())
        tgt_idx = _RASHI_ORDER.index(target_rashi.lower())
        diff = (tgt_idx - jup_idx) % 12 + 1
        return diff in (1, 5, 7, 9)

    def _get_amatyakaraka(self, chart: D1Chart) -> Tuple[str, str]:
        """
        Calculate Jaimini Amatyakaraka (AmK) — planet with 2nd highest degree within sign.
        7 classical grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn).
        """
        classical_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        valid_p = [p for p in chart.planets if p.planet.lower() in classical_planets]
        if len(valid_p) < 2:
            return "sun", chart.ascendant.rashi.lower()

        # Sort descending by rashi_degree
        sorted_p = sorted(valid_p, key=lambda x: x.rashi_degree, reverse=True)
        amk = sorted_p[1]  # 2nd highest degree
        return amk.planet.lower(), amk.rashi.lower()

    def _get_domain_lord_and_rashi(self, chart: D1Chart, domain: str) -> Tuple[str, str, str]:
        """Returns (domain_house_rashi, domain_lord, domain_lord_rashi)."""
        domain_house = 10 if domain.lower() == "career" else (7 if domain.lower() == "marriage" else 10)
        lagna_rashi = chart.ascendant.rashi.lower()
        house_rashi = self._house_rashi(lagna_rashi, domain_house)
        lord = _RASHI_LORDS.get(house_rashi, "mars")

        lord_rashi = house_rashi
        for p in chart.planets:
            if p.planet.lower() == lord.lower():
                lord_rashi = p.rashi.lower()
                break
        return house_rashi, lord, lord_rashi

    def compute_continuous_confluence(
        self,
        chart: D1Chart,
        target_date: date,
        mahadasha_lord: str,
        antardasha_lord: str,
        domain: str = "career",
    ) -> ContinuousConfluenceReport:
        """
        Computes deterministic, continuous confluence score C_score in [0.0, 1.0].
        Frozen formula: 0.35*S_SAV + 0.20*S_BAV + 0.35*S_Gochara + 0.10*S_Geom
        """
        lagna_rashi = chart.ascendant.rashi.lower()
        domain_house = 10 if domain.lower() == "career" else (7 if domain.lower() == "marriage" else 10)
        house_rashi, dom_lord, dom_lord_rashi = self._get_domain_lord_and_rashi(chart, domain)
        amk_planet, amk_rashi = self._get_amatyakaraka(chart)

        # 1. Continuous SAV Sigmoid Score
        sav_res = self.ashtakavarga_engine.compute_sarvashtakavarga(chart)
        sav_bindus = sav_res.bindus_from_lagna(lagna_rashi, domain_house)
        # Sigmoid centered at 28 with scale 3.0
        sav_score = 1.0 / (1.0 + math.exp(-(sav_bindus - 28.0) / 3.0))

        # 2. Continuous BAV Score
        md_lord = mahadasha_lord.lower()
        ad_lord = antardasha_lord.lower()
        planet_rashis = {p.planet.lower(): p.rashi.lower() for p in chart.planets}
        md_rashi = planet_rashis.get(md_lord, lagna_rashi)
        ad_rashi = planet_rashis.get(ad_lord, lagna_rashi)

        bhav_list = self.ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        bav_map = {b.target_planet.lower(): b for b in bhav_list}
        md_bav_bindus = bav_map[md_lord].bindus_in_rashi(md_rashi) if md_lord in bav_map else 4
        ad_bav_bindus = bav_map[ad_lord].bindus_in_rashi(ad_rashi) if ad_lord in bav_map else 4

        bav_score = (min(md_bav_bindus, 8) + min(ad_bav_bindus, 8)) / 16.0

        # 3. Continuous Multi-Point Double Transit Score
        target_dt = datetime.combine(target_date, time(12, 0), tzinfo=timezone.utc)
        eph = self.wrapper.calculate(target_dt, 0.0, 0.0)
        transit_map = {p.planet.lower(): p.rashi.lower() for p in eph.planet_positions}
        jup_rashi = transit_map.get("jupiter", "aries")
        sat_rashi = transit_map.get("saturn", "aries")

        jup_house = self._jupiter_aspects(jup_rashi, house_rashi)
        jup_lord = self._jupiter_aspects(jup_rashi, dom_lord_rashi)
        jup_amk = self._jupiter_aspects(jup_rashi, amk_rashi)

        sat_house = self._saturn_aspects(sat_rashi, house_rashi)
        sat_lord = self._saturn_aspects(sat_rashi, dom_lord_rashi)
        sat_amk = self._saturn_aspects(sat_rashi, amk_rashi)

        s_jup = 1.0 if (jup_house or jup_lord or jup_amk) else 0.0
        s_sat = 1.0 if (sat_house or sat_lord or sat_amk) else 0.0

        # Multi-point Double Transit formulation
        gochara_score = (s_jup * s_sat * 0.70) + (((s_jup + s_sat) / 2.0) * 0.30)

        # 4. Mutual Dasha Geometry
        md_idx = _RASHI_ORDER.index(md_rashi)
        ad_idx = _RASHI_ORDER.index(ad_rashi)
        mutual_dist = (ad_idx - md_idx) % 12 + 1
        dasha_geom_score = 0.25 if mutual_dist in (6, 8, 2, 12) else 1.0

        # 5. Composite Confluence Score (FROZEN WEIGHTS: 0.35, 0.20, 0.35, 0.10)
        c_score = (0.35 * sav_score) + (0.20 * bav_score) + (0.35 * gochara_score) + (0.10 * dasha_geom_score)
        c_score = max(0.0, min(1.0, c_score))

        return ContinuousConfluenceReport(
            domain=domain,
            target_date=target_date,
            sav_bindus=sav_bindus,
            sav_score=round(sav_score, 4),
            md_bav_bindus=md_bav_bindus,
            ad_bav_bindus=ad_bav_bindus,
            bav_score=round(bav_score, 4),
            jupiter_aspects_house=jup_house,
            jupiter_aspects_lord=jup_lord,
            jupiter_aspects_amk=jup_amk,
            saturn_aspects_house=sat_house,
            saturn_aspects_lord=sat_lord,
            saturn_aspects_amk=sat_amk,
            gochara_score=round(gochara_score, 4),
            dasha_mutual_houses=mutual_dist,
            dasha_geom_score=round(dasha_geom_score, 4),
            domain_bhava_rashi=house_rashi,
            domain_lord=dom_lord,
            domain_lord_rashi=dom_lord_rashi,
            amatyakaraka=amk_planet,
            amatyakaraka_rashi=amk_rashi,
            confluence_score=round(c_score, 4),
        )

    def synthesize_candidate_probability(self, p_moe: float, c_score: float) -> float:
        """
        Candidate Probability Synthesis Rule:
        P_final = P_MoE * (0.50 + 0.50 * C_score)
        """
        p_final = p_moe * (0.50 + 0.50 * c_score)
        return max(0.0, min(1.0, p_final))

    def evaluate_confluence(
        self,
        chart: D1Chart,
        target_date: date,
        mahadasha_lord: str,
        antardasha_lord: str,
        domain: str = "career",
    ) -> ClassicalConfluenceReport:
        """Legacy method for backward compatibility."""
        rep = self.compute_continuous_confluence(chart, target_date, mahadasha_lord, antardasha_lord, domain)
        sav_pass = rep.sav_bindus >= 28
        bav_pass = (rep.md_bav_bindus >= 4) and (rep.ad_bav_bindus >= 4)
        jup_pass = rep.jupiter_aspects_house
        sat_pass = rep.saturn_aspects_house
        dtr_pass = jup_pass and sat_pass
        geom_pass = rep.dasha_geom_score > 0.5

        tier = "HIGH_CONFLUENCE" if rep.confluence_score >= 0.70 else ("MODERATE_CONFLUENCE" if rep.confluence_score >= 0.45 else "BLOCKED_BY_GOCHARA_OR_ASHTAKAVARGA")

        return ClassicalConfluenceReport(
            domain=domain,
            target_date=target_date,
            domain_bhava_sav_bindus=rep.sav_bindus,
            sav_pass=sav_pass,
            md_lord_bav_bindus=rep.md_bav_bindus,
            ad_lord_bav_bindus=rep.ad_bav_bindus,
            bav_pass=bav_pass,
            transiting_jupiter_rashi="",
            transiting_saturn_rashi="",
            target_bhava_rashi=rep.domain_bhava_rashi,
            jupiter_aspects_domain=jup_pass,
            saturn_aspects_domain=sat_pass,
            double_transit_pass=dtr_pass,
            dasha_mutual_houses=rep.dasha_mutual_houses,
            dasha_geometry_pass=geom_pass,
            confluence_score=rep.confluence_score,
            confluence_tier=tier,
        )
