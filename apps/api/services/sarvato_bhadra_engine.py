"""
AstroOS — Sarvato-Bhadra Chakra (SBC) Engine
============================================

Canonical Shastric Implementation based on:
- Narapatijayacharya Swarodaya
- Vinay Jha (http://vedicastrology.wikidot.com/sarvato-bhadra-chakra)

Chakra Structure:
- 9x9 Grid (81 Squares) with 28 Nakshatras (including Abhijit between Uttara Ashadha and Shravana).
- Cardinal Directions: East (Top: Krittika to Ashlesha), South (Right: Magha to Vishakha),
  West (Bottom: Anuradha to Shravana), North (Left: Dhanishta to Bharani).
- 5 Types of Vedha Targets: Nakshatra, Varna (Akshara), Swara (Vowels), Rashi, Tithi.
- Crucial Nadi Nakshatras:
  1. Janma Nakshatra (1st from Moon)
  2. Karma Nakshatra (10th from Janma)
  3. Sanghatika Nakshatra (16th from Janma)
  4. Samudayika Nakshatra (18th from Janma)
  5. Adhana Nakshatra (19th from Janma)
  6. Vainashika Nakshatra (23rd from Janma)
  7. Manasa / Rajyabhisheka Nakshatra (26th from Janma)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

logger = logging.getLogger(__name__)

# 28 Nakshatras in SBC Order starting from Krittika
_SBC_28_NAKSHATRAS = [
    "krittika", "rohini", "mrigashira", "ardra", "punarvasu", "pushya", "ashlesha",          # East (1-7)
    "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "swati", "vishakha",    # South (8-14)
    "anuradha", "jyeshtha", "mula", "purva_ashadha", "uttara_ashadha", "abhijit", "shravana",# West (15-21)
    "dhanishta", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada", "revati", "ashwini", "bharani" # North (22-28)
]

# Standard 27 to 28 mapping
_NAK_27_ORDER = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
]


@dataclass(frozen=True)
class SpecialNadiVedha:
    """Status of special Nadi Nakshatra under transit Vedha."""
    nadi_type: str                      # "JANMA", "KARMA", "SANGHATIKA", "SAMUDAYIKA", "ADHANA", "VAINASHIKA", "MANASA"
    nakshatra_name: str
    benefic_vedhas: List[str] = field(default_factory=list)
    malefic_vedhas: List[str] = field(default_factory=list)
    vedha_status: str = "CLEAR"         # "BENEFIC_AFFIRMATION", "CRUEL_AFFLICTION", "MIXED", "CLEAR"


@dataclass(frozen=True)
class SarvatoBhadraReport:
    """Complete Sarvato-Bhadra Chakra Vedha analysis."""
    target_date: date
    janma_nakshatra_28: str
    total_benefic_vedhas_count: int
    total_malefic_vedhas_count: int
    sbc_composite_score: float          # -1.0 (severe afflictions) to +1.0 (supreme victory/elevation)
    overall_transit_shield: str         # "EXCELLENT", "AUSPICIOUS", "MIXED", "AFFLICTED", "SEVERE_VULNERABILITY"
    nadi_nakshatras: Dict[str, SpecialNadiVedha] = field(default_factory=dict)
    active_planet_positions_28: Dict[str, str] = field(default_factory=dict)


class SarvatoBhadraEngine:
    """Evaluates 28-Nakshatra Sarvato-Bhadra Chakra Vedhas and Nadi afflictions."""

    def __init__(self, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)

    def _degree_to_sbc_nakshatra(self, longitude: float) -> str:
        """Converts absolute sidereal longitude into 28-Nakshatra scheme with Abhijit."""
        # Abhijit is 6°40' of Capricorn (276°40' to 280°54'20")
        # In 28 nakshatra system:
        # Uttara Ashadha (266°40' to 276°40'), Abhijit (276°40' to 280°54'), Shravana (280°54' to 293°20')
        deg = longitude % 360.0
        if 276.6667 <= deg < 280.9056:
            return "abhijit"
        
        # Standard 27 conversion
        idx = int(deg // (360.0 / 27.0)) % 27
        return _NAK_27_ORDER[idx]

    def _get_vedha_nakshatras_28(self, planet_nak: str, is_retrograde: bool = False) -> List[str]:
        """
        Computes the three Vedha lines (Cross-Diagonal Left, Front Direct, and Right)
        in the 28-Nakshatra Sarvato-Bhadra Chakra.
        """
        if planet_nak not in _SBC_28_NAKSHATRAS:
            return []

        idx = _SBC_28_NAKSHATRAS.index(planet_nak)
        n = len(_SBC_28_NAKSHATRAS)

        # In 28-SBC:
        # Direct Front Vedha is opposite in grid (diff = 14)
        front_vedha = _SBC_28_NAKSHATRAS[(idx + 14) % n]
        
        # Cross diagonals depending on direction
        left_vedha = _SBC_28_NAKSHATRAS[(idx + 7) % n]
        right_vedha = _SBC_28_NAKSHATRAS[(idx - 7 + n) % n]

        # Conjunction itself is Purna-Drishti / Vedha
        return [planet_nak, front_vedha, left_vedha, right_vedha]

    def evaluate_sbc(self, chart: D1Chart, target_date: date) -> SarvatoBhadraReport:
        """Evaluates Sarvato-Bhadra Chakra Vedha on all Special Nadi Nakshatras."""
        # 1. Identify Natal Moon Janma Nakshatra in 28 system
        p_map = {p.planet.lower(): p for p in chart.planets}
        moon_pos = p_map.get("moon")
        janma_deg = moon_pos.sidereal_longitude if moon_pos else chart.ascendant.degree
        janma_nak = self._degree_to_sbc_nakshatra(janma_deg)

        j_idx = _SBC_28_NAKSHATRAS.index(janma_nak)
        n = len(_SBC_28_NAKSHATRAS)

        # 2. Identify 7 Key Nadi Nakshatras
        # (Janma: 1, Karma: 10, Sanghatika: 16, Samudayika: 18, Adhana: 19, Vainashika: 23, Manasa: 26)
        nadi_map = {
            "JANMA": janma_nak,
            "KARMA": _SBC_28_NAKSHATRAS[(j_idx + 9) % n],
            "SANGHATIKA": _SBC_28_NAKSHATRAS[(j_idx + 15) % n],
            "SAMUDAYIKA": _SBC_28_NAKSHATRAS[(j_idx + 17) % n],
            "ADHANA": _SBC_28_NAKSHATRAS[(j_idx + 18) % n],
            "VAINASHIKA": _SBC_28_NAKSHATRAS[(j_idx + 22) % n],
            "MANASA": _SBC_28_NAKSHATRAS[(j_idx + 25) % n],
        }

        # 3. Calculate Gochara Transits on target date
        target_dt = datetime.combine(target_date, time(12, 0), tzinfo=timezone.utc)
        eph = self.wrapper.calculate(target_dt, 0.0, 0.0)

        transit_naks: Dict[str, str] = {}
        vedha_hits: Dict[str, List[Tuple[str, bool]]] = {nak: [] for nak in _SBC_28_NAKSHATRAS}

        benefics = {"jupiter", "venus", "mercury", "moon"}
        malefics = {"sun", "mars", "saturn", "rahu", "ketu"}

        for p in eph.planet_positions:
            p_name = p.planet.lower()
            p_nak = self._degree_to_sbc_nakshatra(p.sidereal_longitude)
            transit_naks[p_name] = p_nak
            is_benefic = p_name in benefics

            vedhas = self._get_vedha_nakshatras_28(p_nak, is_retrograde=p.is_retrograde)
            for v_nak in vedhas:
                vedha_hits[v_nak].append((p_name, is_benefic))

        # 4. Assess Vedhas on Nadi Nakshatras
        nadi_reports: Dict[str, SpecialNadiVedha] = {}
        tot_ben = 0
        tot_mal = 0

        for n_type, nak_name in nadi_map.items():
            hits = vedha_hits.get(nak_name, [])
            ben_list = [h[0].upper() for h in hits if h[1]]
            mal_list = [h[0].upper() for h in hits if not h[1]]

            tot_ben += len(ben_list)
            tot_mal += len(mal_list)

            if ben_list and not mal_list:
                status = "BENEFIC_AFFIRMATION"
            elif mal_list and not ben_list:
                status = "CRUEL_AFFLICTION"
            elif ben_list and mal_list:
                status = "MIXED"
            else:
                status = "CLEAR"

            nadi_reports[n_type] = SpecialNadiVedha(
                nadi_type=n_type,
                nakshatra_name=nak_name.upper(),
                benefic_vedhas=ben_list,
                malefic_vedhas=mal_list,
                vedha_status=status,
            )

        # 5. Composite Score
        net_score = (tot_ben * 0.20) - (tot_mal * 0.25)
        # Extra weight if Janma or Karma is afflicted
        if nadi_reports["JANMA"].vedha_status == "CRUEL_AFFLICTION":
            net_score -= 0.30
        if nadi_reports["KARMA"].vedha_status == "CRUEL_AFFLICTION":
            net_score -= 0.25

        if nadi_reports["JANMA"].vedha_status == "BENEFIC_AFFIRMATION":
            net_score += 0.30
        if nadi_reports["KARMA"].vedha_status == "BENEFIC_AFFIRMATION":
            net_score += 0.25

        comp_score = max(-1.0, min(1.0, net_score))

        if comp_score >= 0.50:
            shield = "EXCELLENT"
        elif comp_score >= 0.15:
            shield = "AUSPICIOUS"
        elif comp_score >= -0.15:
            shield = "MIXED"
        elif comp_score >= -0.50:
            shield = "AFFLICTED"
        else:
            shield = "SEVERE_VULNERABILITY"

        return SarvatoBhadraReport(
            target_date=target_date,
            janma_nakshatra_28=janma_nak.upper(),
            total_benefic_vedhas_count=tot_ben,
            total_malefic_vedhas_count=tot_mal,
            sbc_composite_score=round(comp_score, 4),
            overall_transit_shield=shield,
            nadi_nakshatras=nadi_reports,
            active_planet_positions_28={k.upper(): v.upper() for k, v in transit_naks.items()},
        )
