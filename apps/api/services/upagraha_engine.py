"""
AstroOS — Non-Luminous Upagrahas & Gulika/Mandi Engine
======================================================
Implements canonical calculations for:

  1. Five Arkadosha Upagrahas (calculated from Sun's longitude per BPHS Ch. 86):
     - Dhooma      = Sun + 133°20' (4s 13°20')
     - Vyatipata   = 360° - Dhooma (12s - Dhooma)
     - Parivesha   = Vyatipata + 180° (6s + Vyatipata)
     - Indrachapa  = 360° - Parivesha (12s - Parivesha)
     - Upaketu     = Indrachapa + 16°40' (0s 16°40')
     [Mathematical Verification: Upaketu + 30° == Sun's Longitude]

  2. Kalavela, Mrityu, Yamaghanta, and Gulika (Mandi):
     Calculated from the classical 8-part division (Yama) of Day and Night.

  3. BPHS Upachaya Rule for Gulika:
     - Auspicious ONLY in Upachaya houses (3, 6, 10, 11).
     - Malefic / Obstruction in all other houses (1, 2, 4, 5, 7, 8, 9, 12).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from apps.api.domain.upagraha import (
    SpecialLagna,
    UpagrahaPosition as DomainUpagrahaPosition,
    UpagrahaResult,
)
from apps.api.services.ephemeris_wrapper import (
    EphemerisWrapper,
    jd_to_datetime,
    longitude_to_nakshatra,
    longitude_to_rashi,
)
from packages.shared.constants import DEGREES_PER_RASHI

RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


def normalize_degrees(deg: float) -> float:
    """Normalize angle into [0, 360) range."""
    return deg % 360.0


def _build_upagraha_point(name: str, lon: float, lagna_lon: float) -> DomainUpagrahaPosition:
    rashi, rashi_deg = longitude_to_rashi(lon)
    nak_info = longitude_to_nakshatra(lon)
    rashi_idx = int(normalize_degrees(lon) / 30.0) % 12
    lagna_rashi_idx = int(normalize_degrees(lagna_lon) / 30.0) % 12
    house = ((rashi_idx - lagna_rashi_idx) % 12) + 1
    return DomainUpagrahaPosition(
        name=name,
        sidereal_longitude=round(normalize_degrees(lon), 6),
        rashi=rashi,
        rashi_degree=round(rashi_deg, 6),
        nakshatra=nak_info.nakshatra,
        pada=nak_info.pada,
        nakshatra_lord=nak_info.lord,
        house_number=house,
    )


def _build_special_lagna(name: str, lon: float, lagna_lon: float) -> SpecialLagna:
    rashi, rashi_deg = longitude_to_rashi(lon)
    nak_info = longitude_to_nakshatra(lon)
    rashi_idx = int(normalize_degrees(lon) / 30.0) % 12
    lagna_rashi_idx = int(normalize_degrees(lagna_lon) / 30.0) % 12
    house = ((rashi_idx - lagna_rashi_idx) % 12) + 1
    return SpecialLagna(
        name=name,
        sidereal_longitude=round(normalize_degrees(lon), 6),
        rashi=rashi,
        rashi_degree=round(rashi_deg, 6),
        nakshatra=nak_info.nakshatra,
        pada=nak_info.pada,
        nakshatra_lord=nak_info.lord,
        house_number=house,
    )


@dataclass(frozen=True)
class UpagrahaPosition:
    """Position of a single non-luminous sub-planet."""
    name: str
    longitude: float
    rashi: str
    rashi_idx: int
    degree_in_rashi: float
    house_from_lagna: int


@dataclass(frozen=True)
class UpagrahaReport:
    """Comprehensive Upagraha & Gulika status report."""
    sun_longitude: float
    dhooma: UpagrahaPosition
    vyatipata: UpagrahaPosition
    parivesha: UpagrahaPosition
    indrachapa: UpagrahaPosition
    upaketu: UpagrahaPosition
    gulika: UpagrahaPosition
    gulika_house: int
    gulika_is_upachaya: bool  # True if in 3, 6, 10, 11 (Auspicious per BPHS)
    vamsha_nasha_risk: bool   # Sun conjunct Arkadosha
    ayu_nasha_risk: bool      # Moon conjunct Arkadosha
    gyana_nasha_risk: bool    # Lagna conjunct Arkadosha


# 8-part daytime sequence of Saturn (Gulika) portion by weekday (0=Sunday..6=Saturday)
GULIKA_DAY_PORTIONS = {
    0: 7,  # Sunday (7th portion)
    1: 6,  # Monday (6th portion)
    2: 5,  # Tuesday (5th portion)
    3: 4,  # Wednesday (4th portion)
    4: 3,  # Thursday (3rd portion)
    5: 2,  # Friday (2nd portion)
    6: 1,  # Saturday (1st portion)
}

# 8-part night-time sequence of Saturn (Gulika) portion by weekday
GULIKA_NIGHT_PORTIONS = {
    0: 3,  # Sunday night
    1: 2,  # Monday night
    2: 1,  # Tuesday night
    3: 7,  # Wednesday night
    4: 6,  # Thursday night
    5: 5,  # Friday night
    6: 4,  # Saturday night
}


def _deg_to_pos(name: str, deg: float, lagna_deg: float) -> UpagrahaPosition:
    """Converts continuous degree into UpagrahaPosition dataclass."""
    norm_deg = normalize_degrees(deg)
    r_idx = int(norm_deg / 30.0) % 12
    r_name = RASHI_LIST[r_idx]
    deg_in_r = norm_deg % 30.0


    lagna_r_idx = int(normalize_degrees(lagna_deg) / 30.0) % 12
    house = ((r_idx - lagna_r_idx) % 12) + 1

    return UpagrahaPosition(
        name=name,
        longitude=round(norm_deg, 4),
        rashi=r_name.capitalize(),
        rashi_idx=r_idx,
        degree_in_rashi=round(deg_in_r, 4),
        house_from_lagna=house,
    )


class UpagrahaEngine:
    """Engine for computing Non-Luminous Upagrahas, Arkadoshas, and Gulika/Mandi."""

    def __init__(
        self,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        ephemeris_path: str = "data/ephemeris",
    ):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)


    def compute_upagrahas(
        self,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> UpagrahaReport:
        """
        Computes all 5 Arkadoshas and Gulika/Mandi with BPHS Upachaya validation.
        """
        result = self.wrapper.calculate(
            dt=birth_datetime,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )

        lagna_deg = result.ascendant.sidereal_longitude

        # Find Sun and Moon
        sun_p = next(p for p in result.planet_positions if p.planet.lower() == "sun")
        moon_p = next(p for p in result.planet_positions if p.planet.lower() == "moon")
        sun_lon = sun_p.sidereal_longitude
        moon_lon = moon_p.sidereal_longitude



        # ── 1. Five Arkadoshas (BPHS Ch. 86) ──────────────────────────────────
        dhooma_deg = normalize_degrees(sun_lon + 133.0 + 20.0 / 60.0)
        vyatipata_deg = normalize_degrees(360.0 - dhooma_deg)
        parivesha_deg = normalize_degrees(vyatipata_deg + 180.0)
        indrachapa_deg = normalize_degrees(360.0 - parivesha_deg)
        upaketu_deg = normalize_degrees(indrachapa_deg + 16.0 + 40.0 / 60.0)

        pos_dhooma = _deg_to_pos("Dhooma", dhooma_deg, lagna_deg)
        pos_vyatipata = _deg_to_pos("Vyatipata", vyatipata_deg, lagna_deg)
        pos_parivesha = _deg_to_pos("Parivesha", parivesha_deg, lagna_deg)
        pos_indrachapa = _deg_to_pos("Indrachapa", indrachapa_deg, lagna_deg)
        pos_upaketu = _deg_to_pos("Upaketu", upaketu_deg, lagna_deg)

        # ── 2. Gulika / Mandi (8-part Yama division) ──────────────────────────
        weekday = birth_datetime.weekday()
        # Python weekday: Monday=0..Sunday=6. Convert to Sunday=0..Saturday=6
        astro_weekday = (weekday + 1) % 7

        # Standard daylight estimate: approximate 06:00 to 18:00 if dynamic sun rise is unavailable
        birth_hour_frac = birth_datetime.hour + birth_datetime.minute / 60.0 + birth_datetime.second / 3600.0
        is_day = 6.0 <= birth_hour_frac < 18.0

        if is_day:
            portion_idx = GULIKA_DAY_PORTIONS[astro_weekday]  # 1 to 8
            # Day length 12 hours -> each portion = 1.5 hours
            start_hour = 6.0 + (portion_idx - 1) * 1.5
        else:
            portion_idx = GULIKA_NIGHT_PORTIONS[astro_weekday]
            # Night length 12 hours -> start at 18:00
            start_hour = (18.0 + (portion_idx - 1) * 1.5) % 24.0

        # Cast rising degree at Gulika onset
        dt_gulika = birth_datetime.replace(
            hour=int(start_hour),
            minute=int((start_hour % 1.0) * 60),
            second=0,
        )
        res_gulika = self.wrapper.calculate(
            dt=dt_gulika,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        gulika_deg = res_gulika.ascendant.sidereal_longitude
        pos_gulika = _deg_to_pos("Gulika", gulika_deg, lagna_deg)


        # ── 3. BPHS Upachaya Rule ─────────────────────────────────────────────
        # Upachaya houses = 3, 6, 10, 11
        gulika_upachaya = pos_gulika.house_from_lagna in (3, 6, 10, 11)

        # ── 4. Affliction Conjunction Checks (< 6° orb) ───────────────────────
        arkadosha_lons = [dhooma_deg, vyatipata_deg, parivesha_deg, indrachapa_deg, upaketu_deg]
        
        def is_conj(point_lon: float, target_lons: list[float], orb: float = 6.0) -> bool:
            return any(abs((point_lon - t + 180) % 360 - 180) <= orb for t in target_lons)

        vamsha_risk = is_conj(sun_lon, arkadosha_lons)
        ayu_risk = is_conj(moon_lon, arkadosha_lons)
        gyana_risk = is_conj(lagna_deg, arkadosha_lons)

        return UpagrahaReport(
            sun_longitude=round(sun_lon, 4),
            dhooma=pos_dhooma,
            vyatipata=pos_vyatipata,
            parivesha=pos_parivesha,
            indrachapa=pos_indrachapa,
            upaketu=pos_upaketu,
            gulika=pos_gulika,
            gulika_house=pos_gulika.house_from_lagna,
            gulika_is_upachaya=gulika_upachaya,
            vamsha_nasha_risk=vamsha_risk,
            ayu_nasha_risk=ayu_risk,
            gyana_nasha_risk=gyana_risk,
        )

    def compute(
        self,
        birth_datetime_utc: datetime,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> UpagrahaResult:
        """
        Compute Gulika, Maandi, and Special Lagnas (Bhava, Hora, Ghati Lagna)
        in UpagrahaResult domain format.
        """
        chart = self.wrapper.calculate(
            dt=birth_datetime_utc,
            latitude=latitude,
            longitude=longitude,
            ayanamsa=ayanamsa,
        )
        lagna_deg = chart.ascendant.sidereal_longitude

        sunrise_jd = chart.sunrise_jd
        sunset_jd = chart.sunset_jd
        is_daytime_birth = bool(chart.is_daytime_birth) if chart.is_daytime_birth is not None else True

        if sunrise_jd is None or sunset_jd is None:
            # Polar / circumpolar fallback
            sunrise_dt = birth_datetime_utc.replace(hour=6, minute=0, second=0, microsecond=0)
            sunset_dt = birth_datetime_utc.replace(hour=18, minute=0, second=0, microsecond=0)
            sunrise_res = self.wrapper.calculate(dt=sunrise_dt, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa)
            sunset_res = self.wrapper.calculate(dt=sunset_dt, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa)
            sunrise_jd = sunrise_res.julian_day
            sunset_jd = sunset_res.julian_day

        if is_daytime_birth:
            period_start_jd = sunrise_jd
            period_end_jd = sunset_jd
        else:
            period_start_jd = sunset_jd
            # Next sunrise approx 12h later if not directly paired
            period_end_jd = sunset_jd + 0.5

        total_duration_hours = max((period_end_jd - period_start_jd) * 24.0, 1.0)
        part_duration_hours = total_duration_hours / 8.0

        # Vedic Weekday
        jd_birth = chart.julian_day
        vara_info = self.wrapper.get_vara(sunrise_jd if sunrise_jd is not None else jd_birth)
        vara_str = vara_info.name
        w_idx = vara_info.number
        starting_lord = vara_info.lord

        # Gulika & Maandi onset
        if is_daytime_birth:
            gulika_portion = GULIKA_DAY_PORTIONS[w_idx]
        else:
            gulika_portion = GULIKA_NIGHT_PORTIONS[w_idx]

        gulika_jd = period_start_jd + (gulika_portion - 1) * (part_duration_hours / 24.0)
        maandi_jd = gulika_jd + 0.5 * (part_duration_hours / 24.0)

        gulika_dt = jd_to_datetime(gulika_jd)
        maandi_dt = jd_to_datetime(maandi_jd)

        gulika_res = self.wrapper.calculate(dt=gulika_dt, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa)
        maandi_res = self.wrapper.calculate(dt=maandi_dt, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa)

        pos_gulika = _build_upagraha_point("gulika", gulika_res.ascendant.sidereal_longitude, lagna_deg)
        pos_maandi = _build_upagraha_point("maandi", maandi_res.ascendant.sidereal_longitude, lagna_deg)

        # Special Lagnas: elapsed ghatis since sunrise
        sunrise_dt = jd_to_datetime(sunrise_jd)
        sun_sunrise_res = self.wrapper.calculate(dt=sunrise_dt, latitude=latitude, longitude=longitude, ayanamsa=ayanamsa)
        sun_sunrise_lon = next(p for p in sun_sunrise_res.planet_positions if p.planet.lower() == "sun").sidereal_longitude

        delta_hours = max((birth_datetime_utc - sunrise_dt).total_seconds() / 3600.0, 0.0)
        delta_ghatis = delta_hours * 2.5

        bhava_lagna_deg = normalize_degrees(sun_sunrise_lon + delta_ghatis * 6.0)
        hora_lagna_deg = normalize_degrees(sun_sunrise_lon + delta_ghatis * 12.0)
        ghati_lagna_deg = normalize_degrees(sun_sunrise_lon + delta_ghatis * 30.0)

        pos_bhava = _build_special_lagna("bhava_lagna", bhava_lagna_deg, lagna_deg)
        pos_hora = _build_special_lagna("hora_lagna", hora_lagna_deg, lagna_deg)
        pos_ghati = _build_special_lagna("ghati_lagna", ghati_lagna_deg, lagna_deg)

        return UpagrahaResult(
            upagrahas=(pos_gulika, pos_maandi),
            special_lagnas=(pos_bhava, pos_hora, pos_ghati),
            is_daytime_birth=is_daytime_birth,
            period_start_jd=period_start_jd,
            period_end_jd=period_end_jd,
            part_duration_hours=part_duration_hours,
            weekday=vara_str.capitalize(),
            starting_lord=starting_lord.capitalize(),
        )
