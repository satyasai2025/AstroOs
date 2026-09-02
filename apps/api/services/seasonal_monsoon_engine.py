"""
AstroOS — Seasonal Dynamic Monsoon Tracking Engine (Medini Phase 3)
===================================================================

Addresses the Mid-Season Atmospheric Collapse Discovery:
An annual snapshot (Ardra/Mesha alone) can detect floods (>90%), but misses
"Monsoon Break Droughts" (e.g. 1987, 2002) where June begins normally and
total collapse occurs in July/August.

5-Stage Rolling Seasonal Progression:
  Stage 1: Chaitra Shukla Pratipada (Annual Cosmic Alignment)
  Stage 2: Mesha Sankranti (Meru World Chart 0° Lat, 37.3° E Lon)
  Stage 3: Ardra Pravesha (June Ingress 66°40' - Early Monsoon Outlook)
  Stage 4: Karka Sankranti (July Ingress 90° - Mid-Season July Break/Sustenance)
  Stage 5: Simha Sankranti (August Ingress 120° - Peak Season Agricultural Delivery)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.mundane import IngressType, MundaneIngressMoment
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.mundane_ingress_engine import MundaneIngressEngine

logger = logging.getLogger(__name__)

MERU_LAT = -0.15
MERU_LON = 37.30

_WATER_NADIS = {"AMRITA", "JALA", "NEERA"}
_FIRE_NADIS = {"DAHANA", "CHANDA"}

_NAK_TO_NADI = {
    "ashlesha": "AMRITA", "magha": "AMRITA", "jyeshtha": "AMRITA", "mula": "AMRITA",
    "pushya": "JALA", "purva_phalguni": "JALA", "anuradha": "JALA", "purva_ashadha": "JALA",
    "punarvasu": "NEERA", "uttara_phalguni": "NEERA", "vishakha": "NEERA", "uttara_ashadha": "NEERA",
    "ardra": "SAUMYA", "hasta": "SAUMYA", "swati": "SAUMYA", "abhijit": "SAUMYA",
    "mrigashira": "DAHANA", "chitra": "DAHANA", "dhanishta": "DAHANA", "shravana": "DAHANA",
    "rohini": "VAYU", "bharani": "VAYU", "shatabhisha": "VAYU", "purva_bhadrapada": "VAYU",
    "krittika": "CHANDA", "ashwini": "CHANDA", "revati": "CHANDA", "uttara_bhadrapada": "CHANDA",
}

_NAK_27_ORDER = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
]


@dataclass(frozen=True)
class SeasonalStageResult:
    """Evaluation at a specific seasonal ingress stage."""
    stage_name: str                      # "CHAITRA", "MESHA_MERU", "ARDRA_JUNE", "KARKA_JULY", "SIMHA_AUGUST"
    timestamp_utc: datetime
    raw_moisture_score: float            # -1.0 (drought/fire/malefic) to +1.0 (flood/water/benefic)
    malefic_affliction_flag: bool        # True if Mars-Saturn / Sun-Mars conflict active
    water_grahas: List[str]
    fire_grahas: List[str]
    stage_notes: str


@dataclass(frozen=True)
class SeasonalMonsoonReport:
    """Full 5-stage seasonal dynamic monsoon tracking report."""
    year: int
    early_season_score: float            # Stage 1 + 2 + 3 score
    mid_season_collapse_score: float     # Stage 4 (Karka) + Stage 5 (Simha) score
    rolling_confluence_score: float      # Synthesized multi-stage score (-1.0 to +1.0)
    predicted_category: str              # "EXCESS_FLOOD", "NORMAL_BOUNTIFUL", "MODERATE_DEFICIENT", "SEVERE_DROUGHT"
    monsoon_break_detected: bool         # True if early season was normal/high but mid-season collapsed
    stages: List[SeasonalStageResult] = field(default_factory=list)
    astrometric_synthesis: str = ""


class SeasonalMonsoonTrackingEngine:
    """Dynamic 5-stage seasonal tracking engine for Indian Monsoon forecasting."""

    def __init__(self, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.ingress_engine = MundaneIngressEngine(self.wrapper)
        self.horoscope_engine = HoroscopeEngine(self.wrapper)

    def _get_nakshatra_28(self, longitude: float) -> str:
        deg = longitude % 360.0
        if 276.6667 <= deg < 280.9056:
            return "abhijit"
        idx = int(deg // (360.0 / 27.0)) % 27
        return _NAK_27_ORDER[idx]

    def _evaluate_moment_nadi_and_afflictions(self, dt: datetime) -> Tuple[float, bool, List[str], List[str]]:
        eph = self.wrapper.calculate(dt, 0.0, 0.0)
        p_map = {p.planet.lower(): p for p in eph.planet_positions}

        water_g = []
        fire_g = []

        for p in eph.planet_positions:
            p_name = p.planet.upper()
            nak = self._get_nakshatra_28(p.sidereal_longitude)
            nadi = _NAK_TO_NADI.get(nak, "SAUMYA")
            if nadi in _WATER_NADIS:
                water_g.append(p_name)
            elif nadi in _FIRE_NADIS:
                fire_g.append(p_name)

        # Moisture score
        score = 0.0
        for p in water_g:
            if p in ["MOON", "VENUS", "JUPITER", "MERCURY"]:
                score += 0.25
            else:
                score += 0.10

        for p in fire_g:
            if p in ["MARS", "SUN", "SATURN", "RAHU"]:
                score -= 0.25
            else:
                score -= 0.10

        # Check malefic conflict (Mars-Saturn conjunction/opposition or Mars-Sun combustion)
        sat = p_map.get("saturn")
        mars = p_map.get("mars")
        sun = p_map.get("sun")

        affliction = False
        if sat and mars:
            diff = abs(sat.sidereal_longitude - mars.sidereal_longitude) % 360.0
            if diff <= 12.0 or abs(diff - 180.0) <= 10.0:
                score -= 0.35
                affliction = True

        if sun and mars:
            diff = abs(sun.sidereal_longitude - mars.sidereal_longitude) % 360.0
            if diff <= 8.0:
                score -= 0.20
                affliction = True

        score = max(-1.0, min(1.0, score))
        return score, affliction, water_g, fire_g

    def evaluate_year_seasonally(self, year: int) -> SeasonalMonsoonReport:
        """Executes full 5-stage seasonal progression analysis."""
        stages: List[SeasonalStageResult] = []

        # Stage 1: Chaitra Shukla Pratipada
        chaitra = self.ingress_engine.find_chaitra_shukla_pratipada(year)
        c_score, c_affl, c_w, c_f = self._evaluate_moment_nadi_and_afflictions(chaitra.timestamp_utc)
        k_lord = chaitra.weekday_lord.lower()
        if k_lord in ["moon", "venus", "jupiter", "mercury"]:
            c_score += 0.25
        elif k_lord in ["saturn", "mars", "sun"]:
            c_score -= 0.25
        c_score = max(-1.0, min(1.0, c_score))

        stages.append(SeasonalStageResult(
            stage_name="CHAITRA",
            timestamp_utc=chaitra.timestamp_utc,
            raw_moisture_score=round(c_score, 3),
            malefic_affliction_flag=c_affl,
            water_grahas=c_w,
            fire_grahas=c_f,
            stage_notes=f"King: {chaitra.weekday_lord.upper()}, Weekday: {chaitra.weekday}",
        ))

        # Stage 2: Mesha Sankranti (Meru World Chart)
        mesha = self.ingress_engine.find_solar_ingress(
            year=year, target_longitude=0.0, ingress_type=IngressType.MESHA_SANKRANTI, approx_month=4, approx_day=14
        )
        m_score, m_affl, m_w, m_f = self._evaluate_moment_nadi_and_afflictions(mesha.timestamp_utc)
        stages.append(SeasonalStageResult(
            stage_name="MESHA_MERU",
            timestamp_utc=mesha.timestamp_utc,
            raw_moisture_score=round(m_score, 3),
            malefic_affliction_flag=m_affl,
            water_grahas=m_w,
            fire_grahas=m_f,
            stage_notes=f"Solar Ingress 0° Aries, Meru Lagna evaluated",
        ))

        # Stage 3: Ardra Pravesha (June Ingress 66°40')
        ardra = self.ingress_engine.find_solar_ingress(
            year=year, target_longitude=66.6667, ingress_type=IngressType.ARIDRA_PRAVESHA, approx_month=6, approx_day=21
        )
        a_score, a_affl, a_w, a_f = self._evaluate_moment_nadi_and_afflictions(ardra.timestamp_utc)
        stages.append(SeasonalStageResult(
            stage_name="ARDRA_JUNE",
            timestamp_utc=ardra.timestamp_utc,
            raw_moisture_score=round(a_score, 3),
            malefic_affliction_flag=a_affl,
            water_grahas=a_w,
            fire_grahas=a_f,
            stage_notes=f"Ardra Ingress 66°40' Gemini, Weekday Lord: {ardra.weekday_lord.upper()}",
        ))

        # Stage 4: Karka Sankranti (July Ingress 90° Cancer - Mid-Season Test)
        karka = self.ingress_engine.find_solar_ingress(
            year=year, target_longitude=90.0, ingress_type=IngressType.KARKA_SANKRANTI, approx_month=7, approx_day=16
        )
        k_score, k_affl, k_w, k_f = self._evaluate_moment_nadi_and_afflictions(karka.timestamp_utc)
        stages.append(SeasonalStageResult(
            stage_name="KARKA_JULY",
            timestamp_utc=karka.timestamp_utc,
            raw_moisture_score=round(k_score, 3),
            malefic_affliction_flag=k_affl,
            water_grahas=k_w,
            fire_grahas=k_f,
            stage_notes=f"Karka Ingress 90° Cancer (July Peak Transition)",
        ))

        # Stage 5: Simha Sankranti (August Ingress 120° Leo - Late Season Delivery)
        simha = self.ingress_engine.find_solar_ingress(
            year=year, target_longitude=120.0, ingress_type=IngressType.MESHA_SANKRANTI, approx_month=8, approx_day=16
        )
        s_score, s_affl, s_w, s_f = self._evaluate_moment_nadi_and_afflictions(simha.timestamp_utc)
        stages.append(SeasonalStageResult(
            stage_name="SIMHA_AUGUST",
            timestamp_utc=simha.timestamp_utc,
            raw_moisture_score=round(s_score, 3),
            malefic_affliction_flag=s_affl,
            water_grahas=s_w,
            fire_grahas=s_f,
            stage_notes=f"Simha Ingress 120° Leo (August Monsoon Delivery)",
        ))

        # Rolling Confluence Synthesis
        # Early season weight = 40% (Chaitra 10%, Mesha 15%, Ardra 15%)
        # Mid-Season July/August weight = 60% (Karka 35%, Simha 25%)
        early_score = (c_score * 0.25) + (m_score * 0.35) + (a_score * 0.40)
        mid_score = (k_score * 0.60) + (s_score * 0.40)

        rolling_confluence = (early_score * 0.40) + (mid_score * 0.60)
        rolling_confluence = max(-1.0, min(1.0, rolling_confluence))

        # Detect Monsoon Break
        monsoon_break = (early_score >= 0.10) and (mid_score <= -0.15 or k_affl or s_affl)

        # Classification Tiers
        if rolling_confluence >= 0.25:
            cat = "EXCESS_FLOOD"
            rat = "Continuous multi-stage moisture sustenance across June, July and August with strong water Nadi dominance."
        elif rolling_confluence >= 0.05 and not monsoon_break:
            cat = "NORMAL_BOUNTIFUL"
            rat = "Stable seasonal progression with adequate July/August rainfall distribution."
        elif monsoon_break or (-0.15 <= rolling_confluence < 0.05):
            cat = "MODERATE_DEFICIENT"
            rat = "Monsoon break detected in July/August due to mid-season malefic ingress affliction."
        else:
            cat = "SEVERE_DROUGHT"
            rat = "Severe continuous moisture suppression from early season through July/August."

        return SeasonalMonsoonReport(
            year=year,
            early_season_score=round(early_score, 3),
            mid_season_collapse_score=round(mid_score, 3),
            rolling_confluence_score=round(rolling_confluence, 3),
            predicted_category=cat,
            monsoon_break_detected=bool(monsoon_break),
            stages=stages,
            astrometric_synthesis=rat,
        )
