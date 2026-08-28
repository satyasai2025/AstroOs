"""
AstroOS — Bhrigu Bindu (Destiny Trigger Point) Engine
=====================================================

Shastric Principles (from Vinay Jha & Nadi Astrology):
- Bhrigu Bindu (BB) is the exact mathematical midpoint between Rahu and Moon,
  measured in the direction from Rahu to Moon along the zodiac.
- BB represents the native's destiny trigger / karmic fulcrum.
- In transit (Gochara):
  - Benefic transits (Jupiter, Venus) conjunct or aspecting BB activate destiny,
    fame, elevation, and landmark auspicious events (Bhagya Udaya).
  - Malefic transits (Saturn, Mars, Rahu, Ketu) conjunct or aspecting BB trigger
    sudden karmic tests, health crisis, or decisive transformation.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.domain.horoscope import D1Chart
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

logger = logging.getLogger(__name__)

_RASHI_NAMES = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

_NAKSHATRA_NAMES = [
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purva_phalguni", "uttara_phalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha",
    "purva_bhadrapada", "uttara_bhadrapada", "revati",
]


@dataclass(frozen=True)
class BhriguBinduReport:
    """Detailed calculation and transit evaluation of Bhrigu Bindu."""
    bb_degree_absolute: float            # 0.0 to 360.0 degrees
    bb_rashi: str                        # Sign name
    bb_rashi_degree: float               # 0.0 to 30.0 degrees in sign
    bb_nakshatra: str                    # 1 of 27 Nakshatras
    bb_nakshatra_pada: int               # 1 to 4
    bb_house_from_lagna: int             # 1 to 12
    # Transit activations on target date
    target_date: Optional[date] = None
    transiting_planets_conjunct: List[str] = None
    transiting_planets_aspecting: List[str] = None
    activation_status: str = "INACTIVE"  # "BENEFIC_TRIGGER", "MALEFIC_TRIGGER", "MIXED_TRIGGER", "INACTIVE"
    destiny_impact_score: float = 0.0    # -1.0 (severe karmic test) to +1.0 (major elevation)


class BhriguBinduEngine:
    """Calculates Bhrigu Bindu and monitors Gochara transit activations."""

    def __init__(self, ephemeris_path: str = "data/ephemeris"):
        self.wrapper = EphemerisWrapper(ephemeris_path=ephemeris_path)

    def calculate_bhrigu_bindu(self, chart: D1Chart) -> Tuple[float, str, float, str, int, int]:
        """
        Calculates the exact Bhrigu Bindu longitude from natal Rahu and Moon.
        Midpoint from Rahu to Moon along zodiac:
        dist = (moon - rahu) % 360
        BB = (rahu + dist / 2) % 360
        """
        p_map = {p.planet.lower(): p for p in chart.planets}
        moon_pos = p_map.get("moon")
        rahu_pos = p_map.get("rahu")

        if not moon_pos or not rahu_pos:
            # Fallback to lagna
            bb_deg = chart.ascendant.degree
        else:
            moon_deg = moon_pos.sidereal_longitude
            rahu_deg = rahu_pos.sidereal_longitude
            dist = (moon_deg - rahu_deg) % 360.0
            bb_deg = (rahu_deg + (dist / 2.0)) % 360.0

        rashi_idx = int(bb_deg // 30) % 12
        rashi_name = _RASHI_NAMES[rashi_idx]
        rashi_deg = bb_deg % 30.0

        # Nakshatra calculation (13 deg 20 min = 13.333333 deg)
        nak_span = 360.0 / 27.0
        nak_idx = int(bb_deg // nak_span) % 27
        nak_name = _NAKSHATRA_NAMES[nak_idx]
        pada = int((bb_deg % nak_span) // (nak_span / 4.0)) + 1

        # House from Lagna
        lagna_rashi_idx = _RASHI_NAMES.index(chart.ascendant.rashi.lower())
        house_num = ((rashi_idx - lagna_rashi_idx) % 12) + 1

        return bb_deg, rashi_name, rashi_deg, nak_name, pada, house_num

    def evaluate_transit(self, chart: D1Chart, target_date: date) -> BhriguBinduReport:
        """Evaluates live planetary transit activations on the Bhrigu Bindu."""
        bb_deg, rashi_name, rashi_deg, nak_name, pada, house_num = self.calculate_bhrigu_bindu(chart)

        target_dt = datetime.combine(target_date, time(12, 0), tzinfo=timezone.utc)
        eph = self.wrapper.calculate(target_dt, 0.0, 0.0)

        conjunct_planets = []
        aspecting_planets = []
        score = 0.0

        for p in eph.planet_positions:
            p_name = p.planet.lower()
            p_deg = p.sidereal_longitude
            diff = (bb_deg - p_deg) % 360.0
            angular_dist = min(diff, 360.0 - diff)

            # Conjunction within 5 degrees orb
            is_conjunct = angular_dist <= 5.0
            # Special aspects
            is_aspect = False
            # 7th aspect (opposite sign within 5 deg)
            if abs(angular_dist - 180.0) <= 5.0:
                is_aspect = True
            # Jupiter 5th and 9th aspect (120 deg)
            elif p_name == "jupiter" and (abs(diff - 120.0) <= 5.0 or abs(diff - 240.0) <= 5.0):
                is_aspect = True
            # Saturn 3rd (60 deg) and 10th (270 deg)
            elif p_name == "saturn" and (abs(diff - 60.0) <= 5.0 or abs(diff - 270.0) <= 5.0):
                is_aspect = True
            # Mars 4th (90 deg) and 8th (210 deg)
            elif p_name == "mars" and (abs(diff - 90.0) <= 5.0 or abs(diff - 210.0) <= 5.0):
                is_aspect = True

            if is_conjunct:
                conjunct_planets.append(p_name.upper())
                if p_name in ("jupiter", "venus", "mercury", "moon"):
                    score += 0.40
                elif p_name in ("saturn", "rahu", "ketu", "mars"):
                    score -= 0.40

            if is_aspect and not is_conjunct:
                aspecting_planets.append(p_name.upper())
                if p_name in ("jupiter", "venus"):
                    score += 0.25
                elif p_name in ("saturn", "mars", "rahu"):
                    score -= 0.25

        score = max(-1.0, min(1.0, score))
        if score >= 0.25:
            status = "BENEFIC_TRIGGER"
        elif score <= -0.25:
            status = "MALEFIC_TRIGGER"
        elif conjunct_planets or aspecting_planets:
            status = "MIXED_TRIGGER"
        else:
            status = "INACTIVE"

        return BhriguBinduReport(
            bb_degree_absolute=round(bb_deg, 4),
            bb_rashi=rashi_name.upper(),
            bb_rashi_degree=round(rashi_deg, 4),
            bb_nakshatra=nak_name.upper(),
            bb_nakshatra_pada=pada,
            bb_house_from_lagna=house_num,
            target_date=target_date,
            transiting_planets_conjunct=conjunct_planets,
            transiting_planets_aspecting=aspecting_planets,
            activation_status=status,
            destiny_impact_score=round(score, 4),
        )
