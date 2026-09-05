"""
AstroOS — Vimshottari True-Tithi vs Solar Dasha Comparative Engine

Implements the canonical Siddhanta of Vinay Jha (Kundalee software) regarding
Dasha Year-Length and True-Tithi progression vs standard modern Solar (365.25)
and Savana (360-day) approximations.

Mathematical Principles (BPHS & Surya Siddhanta):
1. Modern Standard (Jagannatha Hora / Solar Year):
   - 1 Year = 365.24219 days
   - 120 Vimshottari Years = 43,829.06 solar days (~120.00 solar years)
2. Savana Year:
   - 1 Year = 360.00000 civil days (sunrise to sunrise)
   - 120 Vimshottari Years = 43,200.00 civil days (~118.28 solar years)
3. Mean Chaandra Year (360 Mean Tithis):
   - 1 Year = 354.36706 days
   - 120 Vimshottari Years = 42,524.05 solar days (~116.425 solar years, matching Chhandogya Upanishad 116 yrs)
4. True-Tithi Astronomical Engine (Kundalee / Phalit):
   - 1 Tithi = exactly 12.0° of true Moon-Sun angular elongation.
   - 1 Chandra Year = exactly 360 True Tithis (4320.0° of cumulative lunisolar elongation).
   - Period start/end boundaries are computed by exact root-finding against the Swiss Ephemeris.
   - Accounts for lunar speed variation (apogee/perigee) and solar speed variation (perihelion/aphelion).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import swisseph as swe

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from packages.shared.constants import (
    DEGREES_PER_NAKSHATRA,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
    VIMSHOTTARI_NAKSHATRA_LORDS,
)


def datetime_to_jd(dt: datetime) -> float:
    """Convert UTC datetime to Julian Day Number."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    hour_decimal = dt_utc.hour + dt_utc.minute / 60.0 + (dt_utc.second + dt_utc.microsecond / 1e6) / 3600.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_decimal)


def jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day Number to UTC datetime."""
    year, month, day, hour_dec = swe.revjul(jd)
    hours = int(hour_dec)
    rem_min = (hour_dec - hours) * 60.0
    minutes = int(rem_min)
    rem_sec = (rem_min - minutes) * 60.0
    seconds = int(rem_sec)
    microseconds = int(round((rem_sec - seconds) * 1e6))
    if microseconds >= 1_000_000:
        seconds += 1
        microseconds -= 1_000_000
    if seconds >= 60:
        minutes += 1
        seconds -= 60
    if minutes >= 60:
        hours += 1
        minutes -= 60
    return datetime(year, month, day, hours, minutes, seconds, microseconds, tzinfo=timezone.utc)


@dataclass(frozen=True)
class DashaBoundary:
    lord: str
    level: int  # 1 = Mahadasha, 2 = Antardasha, 3 = Pratyantar
    start_dt: datetime
    end_dt: datetime
    start_jd: float
    end_jd: float
    duration_days: float
    duration_years: float
    sub_periods: tuple["DashaBoundary", ...] = ()


@dataclass(frozen=True)
class DashaTimelineResult:
    mode: str
    mode_name: str
    birth_dt: datetime
    moon_longitude: float
    sun_longitude: float
    balance_lord: str
    balance_years: float
    balance_fraction: float
    mahadashas: tuple[DashaBoundary, ...]


@dataclass(frozen=True)
class DashaComparisonReport:
    birth_dt: datetime
    solar_timeline: DashaTimelineResult
    savana_timeline: DashaTimelineResult
    chaandra_mean_timeline: DashaTimelineResult
    true_tithi_timeline: DashaTimelineResult
    comparisons: list[dict[str, Any]]


class VimshottariTithiEngine:
    """
    Precision engine for calculating and comparing Vimshottari Dasha
    under 365.25 Solar, 360 Savana, 354.367 Mean Chandra, and Exact True-Tithi modes.
    """

    SOLAR_YEAR_DAYS = 365.24219
    SAVANA_YEAR_DAYS = 360.00000
    CHAANDRA_MEAN_DAYS = 354.36706

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")

    def get_lunisolar_longitudes(self, jd: float) -> tuple[float, float]:
        """Return (moon_sidereal_lon, sun_sidereal_lon) at given JD."""
        moon = self.wrapper.get_planet_position("moon", jd)
        sun = self.wrapper.get_planet_position("sun", jd)
        ayanamsa = self.wrapper.get_ayanamsa(jd)
        moon_sid = (moon.longitude - ayanamsa) % 360.0
        sun_sid = (sun.longitude - ayanamsa) % 360.0
        return (moon_sid, sun_sid)

    def get_instantaneous_elongation(self, jd: float) -> float:
        """Return instantaneous Moon - Sun elongation in degrees [0, 360)."""
        moon = self.wrapper.get_planet_position("moon", jd)
        sun = self.wrapper.get_planet_position("sun", jd)
        return (moon.longitude - sun.longitude) % 360.0

    def find_jd_for_cumulative_tithis(
        self,
        birth_jd: float,
        target_tithis_from_birth: float,
        tolerance_seconds: float = 0.5,
    ) -> float:
        """
        Root-finding function that computes the exact JD when target_tithis
        have elapsed since birth_jd.

        1 Tithi = 12.0° of lunisolar elongation.
        Target cumulative elongation = target_tithis * 12.0 degrees.
        Uses high-precision Newton-Raphson iteration on ephemeris elongation.
        """
        DAYS_PER_TITHI_MEAN = 29.530588853 / 30.0
        current_jd = birth_jd + (target_tithis_from_birth * DAYS_PER_TITHI_MEAN)
        target_total_deg = target_tithis_from_birth * 12.0
        
        max_iter = 25
        tol_days = tolerance_seconds / 86400.0
        
        for _ in range(max_iter):
            moon = self.wrapper.get_planet_position("moon", current_jd)
            sun = self.wrapper.get_planet_position("sun", current_jd)
            
            days_elapsed = current_jd - birth_jd
            approx_synodic_revs = math.floor((days_elapsed / 29.530588853))
            
            elong_now = (moon.longitude - sun.longitude) % 360.0
            elong_birth = self.get_instantaneous_elongation(birth_jd)
            
            delta_in_cycle = (elong_now - elong_birth) % 360.0
            current_total_deg = (approx_synodic_revs * 360.0) + delta_in_cycle
            
            while current_total_deg < (target_total_deg - 180.0):
                current_total_deg += 360.0
            while current_total_deg > (target_total_deg + 180.0):
                current_total_deg -= 360.0
                
            deg_error = target_total_deg - current_total_deg
            
            moon_speed = getattr(moon, "speed_deg_per_day", 13.1763) or 13.1763
            sun_speed = getattr(sun, "speed_deg_per_day", 0.9856) or 0.9856
            net_speed = moon_speed - sun_speed
            if net_speed <= 0:
                net_speed = 12.1907
                
            step_days = deg_error / net_speed
            current_jd += step_days
            
            if abs(step_days) < tol_days:
                break
                
        return current_jd

    def compute_timeline(
        self,
        birth_dt: datetime,
        mode: str = "true_tithi",
        max_depth: int = 2,
    ) -> DashaTimelineResult:
        birth_jd = datetime_to_jd(birth_dt)
        moon_lon, sun_lon = self.get_lunisolar_longitudes(birth_jd)
        
        nak_span = 360.0 / 27.0
        nak_idx = int(moon_lon / nak_span)
        deg_in_nak = moon_lon % nak_span
        frac_elapsed = deg_in_nak / nak_span
        frac_remaining = 1.0 - frac_elapsed
        
        first_lord = VIMSHOTTARI_NAKSHATRA_LORDS[nak_idx]
        first_total_years = VIMSHOTTARI_DASHA_YEARS[first_lord]
        balance_years = frac_remaining * first_total_years
        
        seq = VIMSHOTTARI_SEQUENCE
        start_idx = seq.index(first_lord)
        
        days_per_year_map = {
            "solar_365": self.SOLAR_YEAR_DAYS,
            "savana_360": self.SAVANA_YEAR_DAYS,
            "chaandra_mean_354": self.CHAANDRA_MEAN_DAYS,
        }
        
        mode_names = {
            "solar_365": "Solar Year (365.2422 days - Standard/JHora)",
            "savana_360": "Savana Year (360.0000 civil days)",
            "chaandra_mean_354": "Mean Chaandra Year (354.36706 days)",
            "true_tithi": "True-Tithi Lunisolar Year (360 True Tithis - Jha Canonical)",
        }
        
        mahadashas: list[DashaBoundary] = []
        cumulative_years_from_birth = 0.0
        
        for i in range(len(seq)):
            lord = seq[(start_idx + i) % len(seq)]
            total_lord_years = VIMSHOTTARI_DASHA_YEARS[lord]
            
            if i == 0:
                duration_years = balance_years
            else:
                duration_years = float(total_lord_years)
                
            start_years_offset = cumulative_years_from_birth
            end_years_offset = cumulative_years_from_birth + duration_years
            cumulative_years_from_birth = end_years_offset
            
            if mode == "true_tithi":
                start_tithis = start_years_offset * 360.0
                end_tithis = end_years_offset * 360.0
                
                md_start_jd = birth_jd if start_years_offset == 0.0 else self.find_jd_for_cumulative_tithis(birth_jd, start_tithis)
                md_end_jd = self.find_jd_for_cumulative_tithis(birth_jd, end_tithis)
            else:
                dpy = days_per_year_map[mode]
                md_start_jd = birth_jd + (start_years_offset * dpy)
                md_end_jd = birth_jd + (end_years_offset * dpy)
                
            md_start_dt = jd_to_datetime(md_start_jd)
            md_end_dt = jd_to_datetime(md_end_jd)
            duration_days = md_end_jd - md_start_jd
            
            sub_periods: list[DashaBoundary] = []
            if max_depth >= 2:
                sub_start_years = start_years_offset
                sub_seq_start = seq.index(lord)
                
                for j in range(len(seq)):
                    sub_lord = seq[(sub_seq_start + j) % len(seq)]
                    sub_lord_nominal_years = VIMSHOTTARI_DASHA_YEARS[sub_lord]
                    sub_nominal_span = (total_lord_years * sub_lord_nominal_years) / VIMSHOTTARI_TOTAL_YEARS
                    
                    if i == 0:
                        nominal_md_start_years = - (frac_elapsed * total_lord_years)
                        nom_sub_start = nominal_md_start_years + sum(
                            (total_lord_years * VIMSHOTTARI_DASHA_YEARS[seq[(sub_seq_start + k) % len(seq)]]) / VIMSHOTTARI_TOTAL_YEARS
                            for k in range(j)
                        )
                        nom_sub_end = nom_sub_start + sub_nominal_span
                        
                        if nom_sub_end <= 0.0:
                            continue
                        
                        effective_sub_start_years = max(0.0, nom_sub_start)
                        effective_sub_end_years = max(0.0, nom_sub_end)
                        effective_sub_years = effective_sub_end_years - effective_sub_start_years
                    else:
                        effective_sub_start_years = sub_start_years
                        effective_sub_years = sub_nominal_span
                        effective_sub_end_years = effective_sub_start_years + effective_sub_years
                        sub_start_years = effective_sub_end_years
                        
                    if mode == "true_tithi":
                        sub_s_tithis = effective_sub_start_years * 360.0
                        sub_e_tithis = effective_sub_end_years * 360.0
                        ad_start_jd = birth_jd if effective_sub_start_years == 0.0 else self.find_jd_for_cumulative_tithis(birth_jd, sub_s_tithis)
                        ad_end_jd = self.find_jd_for_cumulative_tithis(birth_jd, sub_e_tithis)
                    else:
                        dpy = days_per_year_map[mode]
                        ad_start_jd = birth_jd + (effective_sub_start_years * dpy)
                        ad_end_jd = birth_jd + (effective_sub_end_years * dpy)
                        
                    ad_start_dt = jd_to_datetime(ad_start_jd)
                    ad_end_dt = jd_to_datetime(ad_end_jd)
                    ad_days = ad_end_jd - ad_start_jd
                    
                    sub_periods.append(
                        DashaBoundary(
                            lord=sub_lord,
                            level=2,
                            start_dt=ad_start_dt,
                            end_dt=ad_end_dt,
                            start_jd=ad_start_jd,
                            end_jd=ad_end_jd,
                            duration_days=ad_days,
                            duration_years=effective_sub_years,
                        )
                    )
            
            mahadashas.append(
                DashaBoundary(
                    lord=lord,
                    level=1,
                    start_dt=md_start_dt,
                    end_dt=md_end_dt,
                    start_jd=md_start_jd,
                    end_jd=md_end_jd,
                    duration_days=duration_days,
                    duration_years=duration_years,
                    sub_periods=tuple(sub_periods),
                )
            )
            
        return DashaTimelineResult(
            mode=mode,
            mode_name=mode_names[mode],
            birth_dt=birth_dt,
            moon_longitude=moon_lon,
            sun_longitude=sun_lon,
            balance_lord=first_lord,
            balance_years=balance_years,
            balance_fraction=frac_remaining,
            mahadashas=tuple(mahadashas),
        )

    def compare_all_models(self, birth_dt: datetime) -> DashaComparisonReport:
        solar = self.compute_timeline(birth_dt, mode="solar_365")
        savana = self.compute_timeline(birth_dt, mode="savana_360")
        chaandra = self.compute_timeline(birth_dt, mode="chaandra_mean_354")
        true_tithi = self.compute_timeline(birth_dt, mode="true_tithi")
        
        comparisons = []
        for i, md_solar in enumerate(solar.mahadashas):
            md_savana = savana.mahadashas[i]
            md_ch = chaandra.mahadashas[i]
            md_tt = true_tithi.mahadashas[i]
            
            drift_savana_days = md_savana.end_jd - md_solar.end_jd
            drift_chaandra_days = md_ch.end_jd - md_solar.end_jd
            drift_true_tithi_days = md_tt.end_jd - md_solar.end_jd
            astronomical_jitter_days = md_tt.end_jd - md_ch.end_jd
            
            comparisons.append({
                "mahadasha": md_solar.lord.upper(),
                "duration_years": md_solar.duration_years,
                "solar_end": md_solar.end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "savana_end": md_savana.end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "chaandra_mean_end": md_ch.end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "true_tithi_end": md_tt.end_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "drift_true_tithi_vs_solar_days": round(drift_true_tithi_days, 2),
                "drift_true_tithi_vs_solar_months": round(drift_true_tithi_days / 30.4375, 2),
                "astronomical_jitter_vs_mean_hours": round(astronomical_jitter_days * 24.0, 2),
            })
            
        return DashaComparisonReport(
            birth_dt=birth_dt,
            solar_timeline=solar,
            savana_timeline=savana,
            chaandra_mean_timeline=chaandra,
            true_tithi_timeline=true_tithi,
            comparisons=comparisons,
        )
