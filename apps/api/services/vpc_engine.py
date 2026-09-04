"""
AstroOS — VPC (Varsha Pravesha / Solar Return) & SCD Entry Engine
================================================================
Implements the authentic annual Solar Return and Sudarshana Chakra Dasha (SCD)
entry chart calculations strictly per Vinay Jha's treatises:

  1. Solar Return (VPC) Computation:
     - Finds the exact moment (UT datetime) where sidereal Sun returns to its
       exact natal sidereal longitude: lambda_sun(T_VPC) == lambda_sun(birth).

  2. SCD (Sudarshana Chakra Dasha) Progressed House:
     - Year 1 of life (0 completed years): House 1 (Lagna)
     - Year 2 of life (1 completed year): House 2
     - General: SCD House = (completed_solar_years % 12) + 1

  3. Inception / Entry Chart Levels:
     - Level 1: Varsha Pravesha (Annual Sun return: 360°)
     - Level 2: Monthly SCD Entry (Sun advances +30° into each consecutive sign)
     - Level 3: Pratyantara / Vidashaa (Sun advances +2.5° = 1/12th of monthly span)

  4. Parashari Standard on VPC (No Tajik / Arabic Parts):
     - Casts Vishamabhava Bhaavachalita for the VPC moment.
     - Analyzes Sudarshana Chakra (SC) and Main Strengths (9 to 1) of the
       current active Vimshottari dasha lords in the VPC chart.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
from typing import Dict, List, Optional, Tuple

import swisseph as swe

from apps.api.services.bhavachalita_engine import VishamabhavaChart, VishamabhavaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.ishta_kashta_engine import IshtaKashtaEngine
from apps.api.services.sudarshana_chakra_engine import SudarshanaChakraEngine, SudarshanaChakraReport


def _normalize_deg(deg: float) -> float:
    return deg % 360.0


def _angular_diff(a: float, b: float) -> float:
    """Signed shortest distance from b to a in [-180, 180]."""
    diff = (a - b + 180.0) % 360.0 - 180.0
    return diff


@dataclass(frozen=True)
class SCDEntryMilestone:
    """An SCD entry / inception milestone (Varsha, Monthly, or Pratyantara)."""
    level: int                   # 1 = Varsha, 2 = Monthly, 3 = Pratyantara
    name: str                    # e.g. "Monthly SCD Month 4"
    sun_target_longitude: float  # Exact sidereal degree
    entry_datetime_utc: datetime
    scd_house: int               # Active house 1-12


@dataclass(frozen=True)
class VPCReport:
    """Comprehensive Varsha Pravesha Chakra & Tri-Chart Synthesis."""
    target_year: int
    birth_sun_longitude: float
    vpc_datetime_utc: datetime
    completed_years: int
    scd_annual_house: int
    vpc_chart: VishamabhavaChart
    vpc_sudarshana: SudarshanaChakraReport
    monthly_scd_entries: List[SCDEntryMilestone]
    pratyantara_entries: List[SCDEntryMilestone]
    dasha_lord_vpc_strengths: Dict[str, Dict[str, any]]


class VPCEngine:
    """High-precision Solar Return (VPC) and SCD Inception Engine."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        ephemeris_path: str = "data/ephemeris",
    ):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.bhava_engine = VishamabhavaEngine(ephemeris_wrapper=self.wrapper)
        self.sc_engine = SudarshanaChakraEngine(ephemeris_wrapper=self.wrapper)

    def _get_sidereal_sun(self, jd_ut: float, ayanamsa: str = "lahiri") -> float:
        ayan = swe.get_ayanamsa_ut(jd_ut) if ayanamsa.lower() == "lahiri" else 0.0
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        res, _ = swe.calc_ut(jd_ut, swe.SUN, flags)
        return _normalize_deg(res[0] - ayan)

    def find_solar_return_jd(
        self,
        target_sun_lon: float,
        approx_year: int,
        approx_month: int,
        approx_day: int,
        ayanamsa: str = "lahiri",
    ) -> float:
        """
        Finds exact Julian Day where sidereal Sun reaches target_sun_lon using Newton-Raphson/Bisection.
        """
        approx_jd = swe.julday(approx_year, approx_month, approx_day, 12.0)
        
        # Binary / Newton-Raphson search
        jd = approx_jd
        for _ in range(15):
            curr_sun = self._get_sidereal_sun(jd, ayanamsa)
            diff = _angular_diff(curr_sun, target_sun_lon)
            if abs(diff) < 1e-6:  # Less than 0.0036 arcsec precision
                break
            # Sun moves ~0.9856 deg/day
            jd -= (diff / 0.9856)
        return jd

    def compute_scd_house_at_date(self, birth_datetime_utc: datetime, target_datetime_utc: datetime) -> int:
        """
        Computes the active SCD house (1-12) for any target date per Jha:
        - Age 0-1 (Year 1): House 1
        - Age 1-2 (Year 2): House 2
        """
        birth_jd = swe.julday(
            birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
            birth_datetime_utc.hour + birth_datetime_utc.minute / 60.0 + birth_datetime_utc.second / 3600.0
        )
        target_jd = swe.julday(
            target_datetime_utc.year, target_datetime_utc.month, target_datetime_utc.day,
            target_datetime_utc.hour + target_datetime_utc.minute / 60.0 + target_datetime_utc.second / 3600.0
        )

        completed_years = int((target_jd - birth_jd) / 365.25636)  # Sidereal year duration
        if completed_years < 0:
            completed_years = 0
        return (completed_years % 12) + 1

    def compute_vpc(
        self,
        birth_datetime_utc: datetime,
        target_year: int,
        latitude: float,
        longitude: float,
        current_dasha_lords: Optional[List[str]] = None,
        ayanamsa: str = "lahiri",
    ) -> VPCReport:
        """
        Computes the full Varsha Pravesha Chakra and SCD entry hierarchy for target_year.
        """
        birth_jd = swe.julday(
            birth_datetime_utc.year, birth_datetime_utc.month, birth_datetime_utc.day,
            birth_datetime_utc.hour + birth_datetime_utc.minute / 60.0 + birth_datetime_utc.second / 3600.0
        )
        birth_sun_lon = self._get_sidereal_sun(birth_jd, ayanamsa)

        # 1. Exact Solar Return JD for target_year
        vpc_jd = self.find_solar_return_jd(
            target_sun_lon=birth_sun_lon,
            approx_year=target_year,
            approx_month=birth_datetime_utc.month,
            approx_day=birth_datetime_utc.day,
            ayanamsa=ayanamsa,
        )

        year, month, day, hour_float = swe.revjul(vpc_jd)
        hour = int(hour_float)
        minute = int((hour_float - hour) * 60.0)
        second = int((((hour_float - hour) * 60.0) - minute) * 60.0)
        vpc_dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)

        # Completed years at this Solar Return
        completed_years = target_year - birth_datetime_utc.year
        scd_annual_house = (completed_years % 12) + 1

        # 2. Cast Vishamabhava Bhaavachalita Chart for VPC
        vpc_chart = self.bhava_engine.compute_bhavachalita(
            birth_datetime=vpc_dt,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )

        # 3. Analyze Sudarshana Chakra in VPC
        vpc_ephem = self.wrapper.calculate(dt=vpc_dt, latitude=latitude, longitude=longitude)
        sun_p = next(p for p in vpc_ephem.planet_positions if p.planet.lower() == "sun")
        moon_p = next(p for p in vpc_ephem.planet_positions if p.planet.lower() == "moon")
        
        vpc_sc = self.sc_engine.analyze(
            lagna_deg=vpc_chart.lagna_madhya,
            sun_deg=sun_p.sidereal_longitude,
            moon_deg=moon_p.sidereal_longitude,
        )

        # 4. Generate Level 2 (12 Monthly SCD entries: +30° each)
        monthly_entries: List[SCDEntryMilestone] = []
        for m in range(12):
            m_target_sun = _normalize_deg(birth_sun_lon + m * 30.0)
            # Approximate month offset from VPC
            approx_m_jd = vpc_jd + m * 30.4375
            m_yr, m_mo, m_dy, _ = swe.revjul(approx_m_jd)
            m_exact_jd = self.find_solar_return_jd(
                target_sun_lon=m_target_sun,
                approx_year=m_yr,
                approx_month=m_mo,
                approx_day=m_dy,
                ayanamsa=ayanamsa,
            )
            y, mo, d, h_f = swe.revjul(m_exact_jd)
            h = int(h_f)
            mi = int((h_f - h) * 60.0)
            s = int((((h_f - h) * 60.0) - mi) * 60.0)
            m_dt = datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc)
            m_scd_house = ((scd_annual_house - 1 + m) % 12) + 1

            monthly_entries.append(
                SCDEntryMilestone(
                    level=2,
                    name=f"Monthly SCD Month {m + 1} (House {m_scd_house})",
                    sun_target_longitude=round(m_target_sun, 4),
                    entry_datetime_utc=m_dt,
                    scd_house=m_scd_house,
                )
            )

        # 5. Generate Level 3 (Pratyantara / Vidashaa entries: +2.5° each for the first month as sample)
        pratyantara_entries: List[SCDEntryMilestone] = []
        for p_idx in range(12):
            p_target_sun = _normalize_deg(birth_sun_lon + p_idx * 2.5)
            approx_p_jd = vpc_jd + p_idx * 2.536
            p_yr, p_mo, p_dy, _ = swe.revjul(approx_p_jd)
            p_exact_jd = self.find_solar_return_jd(
                target_sun_lon=p_target_sun,
                approx_year=p_yr,
                approx_month=p_mo,
                approx_day=p_dy,
                ayanamsa=ayanamsa,
            )
            y, mo, d, h_f = swe.revjul(p_exact_jd)
            h = int(h_f)
            mi = int((h_f - h) * 60.0)
            s = int((((h_f - h) * 60.0) - mi) * 60.0)
            p_dt = datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc)
            p_house = ((scd_annual_house - 1 + p_idx) % 12) + 1

            pratyantara_entries.append(
                SCDEntryMilestone(
                    level=3,
                    name=f"Pratyantara/Vidashaa {p_idx + 1} (+{p_idx * 2.5}°)",
                    sun_target_longitude=round(p_target_sun, 4),
                    entry_datetime_utc=p_dt,
                    scd_house=p_house,
                )
            )

        # 6. Evaluate Current Vimshottari Lords in VPC
        dasha_strengths: Dict[str, Dict[str, any]] = {}
        target_lords = current_dasha_lords or ["Jupiter", "Saturn", "Mercury", "Venus", "Mars"]
        for lord in target_lords:
            lord_cap = lord.capitalize()
            p_pos = next((p for p in vpc_ephem.planet_positions if p.planet.lower() == lord.lower()), None)
            if p_pos:
                dignity_val = p_pos.dignity.value if p_pos.dignity else "sama"
                m_str = IshtaKashtaEngine.get_main_strength(dignity_val, is_retrograde=p_pos.is_retrograde)
                vpc_house = vpc_chart.planet_bhava_placements.get(lord_cap, 1)

                dasha_strengths[lord_cap] = {
                    "vpc_house": vpc_house,
                    "dignity": dignity_val,
                    "main_strength_rank": m_str.main_strength_rank,
                    "main_strength_score": m_str.main_strength_score,
                    "is_retrograde": p_pos.is_retrograde,
                }

        return VPCReport(
            target_year=target_year,
            birth_sun_longitude=round(birth_sun_lon, 4),
            vpc_datetime_utc=vpc_dt,
            completed_years=completed_years,
            scd_annual_house=scd_annual_house,
            vpc_chart=vpc_chart,
            vpc_sudarshana=vpc_sc,
            monthly_scd_entries=monthly_entries,
            pratyantara_entries=pratyantara_entries,
            dasha_lord_vpc_strengths=dasha_strengths,
        )
