"""
AstroOS — Multi-Ingress Synthesis Engine (Medini Jyotisha)
=========================================================

Canonical Shastric Architecture based on Vinay Jha & Classical Samhita texts:
Instead of a single naive trigger (e.g. Ardra alone), rainfall, droughts, and
mundane outcomes are synthesized from 4 distinct astronomical ingress moments:

1. Chaitra Shukla Pratipada (Annual Cosmic King/Minister & Cabinet alignment)
2. Mesha Sankranti (Meru-Centric World Chart: 0.0° Lat, 37.3° E Lon, India in Vrishabha)
3. Ardra Pravesha (Solar entry into 66°40' Gemini / Ardra Nakshatra)
4. Sapta-Nadi Chakra Planetary Configuration (Water Nadis vs Fire/Wind Nadis)
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

# Mount Meru / Kenya coordinates: 0.15° S, 37.3° E
MERU_LAT = -0.15
MERU_LON = 37.30

_WATER_NADIS = {"AMRITA", "JALA", "NEERA"}
_FIRE_NADIS = {"DAHANA", "CHANDA"}

# 28 Nakshatra to Nadi Mapping (Krishi Parashara / Yamala Swarodaya)
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
class IngressPillarScore:
    """Individual score from one of the 4 Medini pillars."""
    pillar_name: str
    raw_score: float                    # -1.0 (severe drought/malefic) to +1.0 (abundant deluge/benefic)
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MultiIngressSynthesisReport:
    """Complete synthesized multi-ingress prediction report for a given year."""
    year: int
    confluence_score: float             # -1.0 to +1.0
    predicted_monsoon_category: str     # "EXCESS_FLOOD", "NORMAL_BOUNTIFUL", "MODERATE_DEFICIENT", "SEVERE_DROUGHT"
    predicted_rainfall_pct_estimate: str
    chaitra_moment: datetime
    mesha_moment: datetime
    ardra_moment: datetime
    pillars: List[IngressPillarScore] = field(default_factory=list)
    astrometric_rationale: str = ""


class MultiIngressSynthesisEngine:
    """Synthesizes Chaitra + Mesha (Meru) + Ardra + Sapta-Nadi for robust Medini predictions."""

    def __init__(self, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.ingress_engine = MundaneIngressEngine(self.wrapper)
        self.horoscope_engine = HoroscopeEngine(self.wrapper)

    def _degree_to_nakshatra_28(self, longitude: float) -> str:
        deg = longitude % 360.0
        if 276.6667 <= deg < 280.9056:
            return "abhijit"
        idx = int(deg // (360.0 / 27.0)) % 27
        return _NAK_27_ORDER[idx]

    def _evaluate_nadi_occupancy(self, dt: datetime) -> Tuple[float, List[str], List[str]]:
        """Evaluates Sapta-Nadi water vs fire balance at given moment."""
        eph = self.wrapper.calculate(dt, 0.0, 0.0)
        water_grahas = []
        fire_grahas = []

        for p in eph.planet_positions:
            p_name = p.planet.upper()
            nak = self._degree_to_nakshatra_28(p.sidereal_longitude)
            nadi = _NAK_TO_NADI.get(nak, "SAUMYA")

            if nadi in _WATER_NADIS:
                water_grahas.append(p_name)
            elif nadi in _FIRE_NADIS:
                fire_grahas.append(p_name)

        # Net balance
        w_score = 0.0
        for p in water_grahas:
            if p in ["MOON", "VENUS", "JUPITER", "MERCURY"]:
                w_score += 0.25
            else:
                w_score += 0.10

        for p in fire_grahas:
            if p in ["MARS", "SUN", "SATURN", "RAHU"]:
                w_score -= 0.25
            else:
                w_score -= 0.10

        return max(-1.0, min(1.0, w_score)), water_grahas, fire_grahas

    def evaluate_year(self, year: int) -> MultiIngressSynthesisReport:
        """Computes synthesized Medini Confluence for a target year."""
        # 1. Pillar 1: Chaitra Shukla Pratipada (King & Minister)
        chaitra = self.ingress_engine.find_chaitra_shukla_pratipada(year)
        king_lord = chaitra.weekday_lord.lower()
        chaitra_score = 0.0
        if king_lord in ["moon", "venus", "jupiter", "mercury"]:
            chaitra_score += 0.35
        elif king_lord in ["saturn", "mars", "sun"]:
            chaitra_score -= 0.35

        p1 = IngressPillarScore(
            pillar_name="CHAITRA_PRATIPADA",
            raw_score=round(chaitra_score, 3),
            weight=0.20,
            details={"king_lord": king_lord, "weekday": chaitra.weekday, "timestamp": chaitra.timestamp_utc.isoformat()},
        )

        # 2. Pillar 2: Mesha Sankranti from Mt. Meru (World Chart)
        mesha = self.ingress_engine.find_solar_ingress(
            year=year,
            target_longitude=0.0,
            ingress_type=IngressType.MESHA_SANKRANTI,
            approx_month=4,
            approx_day=14,
        )
        meru_chart = self.horoscope_engine.generate_d1(mesha.timestamp_utc, MERU_LAT, MERU_LON)

        # In Meru chart, India falls in Vrishabha (Taurus). Check Venus condition and 4th house (Water)
        p_map = {p.planet.lower(): p for p in meru_chart.planets}
        venus_pos = p_map.get("venus")
        sat_pos = p_map.get("saturn")
        mars_pos = p_map.get("mars")
        jup_pos = p_map.get("jupiter")

        mesha_score = 0.0
        if venus_pos and venus_pos.dignity and venus_pos.dignity.value in ["exalted", "own", "moolatrikona", "friendly"]:
            mesha_score += 0.40
        elif venus_pos and venus_pos.dignity and venus_pos.dignity.value in ["debilitated", "enemy"]:
            mesha_score -= 0.30

        if jup_pos and not jup_pos.is_retrograde:
            mesha_score += 0.20

        if sat_pos and mars_pos:
            diff = abs(sat_pos.sidereal_longitude - mars_pos.sidereal_longitude) % 360.0
            if diff <= 15.0 or abs(diff - 180.0) <= 10.0:
                mesha_score -= 0.40  # Saturn-Mars planetary war / conjunction creates drought

        mesha_score = max(-1.0, min(1.0, mesha_score))
        p2 = IngressPillarScore(
            pillar_name="MESHA_MERU_CHART",
            raw_score=round(mesha_score, 3),
            weight=0.30,
            details={"mesha_timestamp": mesha.timestamp_utc.isoformat(), "lagna": meru_chart.ascendant.rashi},
        )

        # 3. Pillar 3: Ardra Pravesha Ingress (66°40' Gemini = 66.6667°)
        ardra = self.ingress_engine.find_solar_ingress(
            year=year,
            target_longitude=66.6667,
            ingress_type=IngressType.ARIDRA_PRAVESHA,
            approx_month=6,
            approx_day=21,
        )
        ardra_weekday_lord = ardra.weekday_lord.lower()
        ardra_score = 0.0
        if ardra_weekday_lord in ["moon", "venus", "mercury", "jupiter"]:
            ardra_score += 0.30
        elif ardra_weekday_lord in ["sun", "mars", "saturn"]:
            ardra_score -= 0.30

        p3 = IngressPillarScore(
            pillar_name="ARDRA_PRAVESHA",
            raw_score=round(ardra_score, 3),
            weight=0.20,
            details={"ardra_weekday_lord": ardra_weekday_lord, "ardra_timestamp": ardra.timestamp_utc.isoformat()},
        )

        # 4. Pillar 4: Sapta-Nadi at Ardra Moment
        nadi_score, water_g, fire_g = self._evaluate_nadi_occupancy(ardra.timestamp_utc)
        p4 = IngressPillarScore(
            pillar_name="SAPTA_NADI_CONFIGURATION",
            raw_score=round(nadi_score, 3),
            weight=0.30,
            details={"water_grahas": water_g, "fire_grahas": fire_g},
        )

        # Confluence Synthesis
        pillars = [p1, p2, p3, p4]
        confluence = sum(p.raw_score * p.weight for p in pillars)
        confluence = max(-1.0, min(1.0, confluence))

        # Classification Tiers
        if confluence >= 0.25:
            cat = "EXCESS_FLOOD"
            est_pct = "+12% to +25% (Excess Monsoon / Widespread Floods)"
            rat = "All 4 Medini pillars (Chaitra Benefic Lord, Meru Venus Strength, and Sapta-Nadi Water Grahas) converge towards heavy surplus precipitation."
        elif confluence >= 0.05:
            cat = "NORMAL_BOUNTIFUL"
            est_pct = "-5% to +10% (Normal Bountiful Monsoon)"
            rat = "Balanced planetary ingress with moderate water Nadi occupancy ensuring stable all-India agricultural rains."
        elif confluence >= -0.15:
            cat = "MODERATE_DEFICIENT"
            est_pct = "-6% to -15% (Deficient / Erratic Monsoon)"
            rat = "Mixed signals with partial malefic affliction on Mesha Meru chart and sporadic dry spells."
        else:
            cat = "SEVERE_DROUGHT"
            est_pct = "-16% to -30% (Severe National Drought / Acute Deficit)"
            rat = "Severe convergence of malefic King/Minister, Saturn-Mars mutual affliction in Meru World Chart, and fire Nadi dominance."

        return MultiIngressSynthesisReport(
            year=year,
            confluence_score=round(confluence, 3),
            predicted_monsoon_category=cat,
            predicted_rainfall_pct_estimate=est_pct,
            chaitra_moment=chaitra.timestamp_utc,
            mesha_moment=mesha.timestamp_utc,
            ardra_moment=ardra.timestamp_utc,
            pillars=pillars,
            astrometric_rationale=rat,
        )
