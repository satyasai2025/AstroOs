"""
AstroOS — Ghati, Dinamana & Kula-Muhurta Precision Engine

Implements classical Siddhantic time measurement based on exact local
Sunrise and Sunset, dynamic proportional Ghati-Pala-Vipala divisions,
the 30 diurnal/nocturnal Muhurtas (including Abhijit and Brahma Muhurta),
and Kula/Gotra-specific lineage electional rules.

References:
- Surya Siddhanta, Ch. 14 (Mana-Adhyaya: 9 types of Time Measures)
- Muhurta Chintamani & Muhurta Ganapati
- BPHS Ch. 3 & Ch. 4 (Time subdivisions from Truti to Ghati to Ahoratra)
- Vinay Jha's Kundalee software (frmHelpMuhurtas & Dinamana models)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import swisseph as swe

from apps.api.services.ephemeris_wrapper import EphemerisWrapper


# ---------------------------------------------------------------------------
# Classical Muhurta Lists (15 Diurnal + 15 Nocturnal)
# ---------------------------------------------------------------------------

DAY_MUHURTAS = [
    {"index": 1, "name": "Rudra", "nature": "ashubha", "deity": "Rudra", "benefic": False},
    {"index": 2, "name": "Ahi", "nature": "ashubha", "deity": "Sarpa", "benefic": False},
    {"index": 3, "name": "Mitra", "nature": "shubha", "deity": "Mitra", "benefic": True},
    {"index": 4, "name": "Pitru", "nature": "ashubha", "deity": "Pitaras", "benefic": False},
    {"index": 5, "name": "Vasu", "nature": "shubha", "deity": "Vasu", "benefic": True},
    {"index": 6, "name": "Varaha", "nature": "shubha", "deity": "Varaha", "benefic": True},
    {"index": 7, "name": "Vishvedeva", "nature": "shubha", "deity": "Vishvedevas", "benefic": True},
    {"index": 8, "name": "Abhijit", "nature": "atishubha", "deity": "Hari / Brahma", "benefic": True, "special": "Cancels 100,000 doshas (except Wednesday)"},
    {"index": 9, "name": "Vidhi", "nature": "shubha", "deity": "Brahma", "benefic": True},
    {"index": 10, "name": "Sutamukhi / Vijaya", "nature": "atishubha", "deity": "Indra", "benefic": True},
    {"index": 11, "name": "Puruhuta", "nature": "shubha", "deity": "Indra", "benefic": True},
    {"index": 12, "name": "Vahni", "nature": "ashubha", "deity": "Agni", "benefic": False},
    {"index": 13, "name": "Naktanchara", "nature": "ashubha", "deity": "Rakshasa", "benefic": False},
    {"index": 14, "name": "Varuna", "nature": "shubha", "deity": "Varuna", "benefic": True},
    {"index": 15, "name": "Aryama", "nature": "shubha", "deity": "Aryama", "benefic": True},
]

NIGHT_MUHURTAS = [
    {"index": 16, "name": "Girisha", "nature": "ashubha", "deity": "Shiva", "benefic": False},
    {"index": 17, "name": "Ajapada", "nature": "ashubha", "deity": "Ajaikapat", "benefic": False},
    {"index": 18, "name": "Ahirbudhnya", "nature": "shubha", "deity": "Ahirbudhnya", "benefic": True},
    {"index": 19, "name": "Pushya", "nature": "shubha", "deity": "Pushya", "benefic": True},
    {"index": 20, "name": "Ashvini", "nature": "shubha", "deity": "Ashvini Kumaras", "benefic": True},
    {"index": 21, "name": "Yama", "nature": "ashubha", "deity": "Yama", "benefic": False},
    {"index": 22, "name": "Agni", "nature": "shubha", "deity": "Agni", "benefic": True},
    {"index": 23, "name": "Vidhatri", "nature": "shubha", "deity": "Vidhatri", "benefic": True},
    {"index": 24, "name": "Kanda", "nature": "ashubha", "deity": "Chanda", "benefic": False},
    {"index": 25, "name": "Aditi", "nature": "shubha", "deity": "Aditi", "benefic": True},
    {"index": 26, "name": "Jiva", "nature": "shubha", "deity": "Brihaspati", "benefic": True},
    {"index": 27, "name": "Vishnu", "nature": "shubha", "deity": "Vishnu", "benefic": True},
    {"index": 28, "name": "Dyumani", "nature": "shubha", "deity": "Surya", "benefic": True},
    {"index": 29, "name": "Brahma Muhurta", "nature": "atishubha", "deity": "Brahma", "benefic": True, "special": "Supreme spiritual and mental clarity; 2 muhurtas before sunrise"},
    {"index": 30, "name": "Samudra", "nature": "shubha", "deity": "Samudra", "benefic": True},
]


@dataclass(frozen=True)
class MuhurtaWindow:
    index: int
    name: str
    nature: str
    deity: str
    benefic: bool
    start_dt: datetime
    end_dt: datetime
    duration_minutes: float
    special_note: Optional[str] = None


@dataclass(frozen=True)
class DinamanaResult:
    date_utc: datetime
    latitude: float
    longitude: float
    sunrise_dt: datetime
    sunset_dt: datetime
    next_sunrise_dt: datetime
    dinamana_hours: float
    ratrimana_hours: float
    day_ghati_minutes: float
    night_ghati_minutes: float
    day_muhurtas: tuple[MuhurtaWindow, ...]
    night_muhurtas: tuple[MuhurtaWindow, ...]
    abhijit_window: MuhurtaWindow
    brahma_muhurta_window: MuhurtaWindow
    rahu_kalam_window: tuple[datetime, datetime]


@dataclass(frozen=True)
class IshtaKala:
    ghatis: int
    palas: int
    vipalas: float
    total_ghatis: float
    local_time: datetime


class GhatiDinamanaEngine:
    """
    Engine for local dynamic solar divisions: Dinamana, Ratrimana,
    proportional Ghatis, 30 diurnal/nocturnal Muhurtas, and Ishtakala conversion.
    """

    def __init__(self, ephemeris_wrapper: Optional[EphemerisWrapper] = None):
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")

    def get_solar_times(
        self,
        target_date: datetime,
        latitude: float,
        longitude: float,
    ) -> tuple[datetime, datetime, datetime]:
        """
        Compute precise Sunrise, Sunset, and Next Sunrise for a given date and location.
        Guarantees: sunrise < sunset < next_sunrise.
        """
        target_utc = target_date.astimezone(timezone.utc) if target_date.tzinfo else target_date.replace(tzinfo=timezone.utc)
        
        # Local midnight anchor in UT
        local_midnight_jd = swe.julday(target_utc.year, target_utc.month, target_utc.day, 0.0) - (longitude / 360.0)

        # 1. Sunrise of target day (searched from local midnight)
        res_rise = swe.rise_trans(local_midnight_jd, swe.SUN, swe.CALC_RISE, (longitude, latitude, 0.0))
        rise_jd = res_rise[1][0]

        # 2. Sunset of target day (searched from sunrise)
        res_set = swe.rise_trans(rise_jd, swe.SUN, swe.CALC_SET, (longitude, latitude, 0.0))
        set_jd = res_set[1][0]

        # 3. Next Sunrise (searched from sunset)
        res_next_rise = swe.rise_trans(set_jd, swe.SUN, swe.CALC_RISE, (longitude, latitude, 0.0))
        next_rise_jd = res_next_rise[1][0]

        rise_dt = self._jd_to_utc(rise_jd)
        set_dt = self._jd_to_utc(set_jd)
        next_rise_dt = self._jd_to_utc(next_rise_jd)

        return rise_dt, set_dt, next_rise_dt

    def compute_dinamana(
        self,
        target_date: datetime,
        latitude: float,
        longitude: float,
    ) -> DinamanaResult:
        """
        Calculate full Dinamana, Ratrimana, 30 Muhurta spans, Abhijit, and Brahma Muhurta.
        """
        rise_dt, set_dt, next_rise_dt = self.get_solar_times(target_date, latitude, longitude)

        dinamana_sec = (set_dt - rise_dt).total_seconds()
        ratrimana_sec = (next_rise_dt - set_dt).total_seconds()

        dinamana_hours = dinamana_sec / 3600.0
        ratrimana_hours = ratrimana_sec / 3600.0

        day_ghati_min = (dinamana_sec / 30.0) / 60.0
        night_ghati_min = (ratrimana_sec / 30.0) / 60.0

        day_muhurta_sec = dinamana_sec / 15.0
        night_muhurta_sec = ratrimana_sec / 15.0

        day_windows: list[MuhurtaWindow] = []
        cur_t = rise_dt
        for m_info in DAY_MUHURTAS:
            nxt_t = cur_t + timedelta(seconds=day_muhurta_sec)
            day_windows.append(
                MuhurtaWindow(
                    index=m_info["index"],
                    name=m_info["name"],
                    nature=m_info["nature"],
                    deity=m_info["deity"],
                    benefic=m_info["benefic"],
                    start_dt=cur_t,
                    end_dt=nxt_t,
                    duration_minutes=day_muhurta_sec / 60.0,
                    special_note=m_info.get("special"),
                )
            )
            cur_t = nxt_t

        night_windows: list[MuhurtaWindow] = []
        cur_t = set_dt
        for m_info in NIGHT_MUHURTAS:
            nxt_t = cur_t + timedelta(seconds=night_muhurta_sec)
            night_windows.append(
                MuhurtaWindow(
                    index=m_info["index"],
                    name=m_info["name"],
                    nature=m_info["nature"],
                    deity=m_info["deity"],
                    benefic=m_info["benefic"],
                    start_dt=cur_t,
                    end_dt=nxt_t,
                    duration_minutes=night_muhurta_sec / 60.0,
                    special_note=m_info.get("special"),
                )
            )
            cur_t = nxt_t

        abhijit = day_windows[7]
        brahma = night_windows[13]

        weekday = rise_dt.weekday()
        rahu_segment_map = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7}
        seg_idx = rahu_segment_map[weekday]
        one_eighth_sec = dinamana_sec / 8.0
        rahu_start = rise_dt + timedelta(seconds=seg_idx * one_eighth_sec)
        rahu_end = rahu_start + timedelta(seconds=one_eighth_sec)

        return DinamanaResult(
            date_utc=target_date,
            latitude=latitude,
            longitude=longitude,
            sunrise_dt=rise_dt,
            sunset_dt=set_dt,
            next_sunrise_dt=next_rise_dt,
            dinamana_hours=round(dinamana_hours, 4),
            ratrimana_hours=round(ratrimana_hours, 4),
            day_ghati_minutes=round(day_ghati_min, 3),
            night_ghati_minutes=round(night_ghati_min, 3),
            day_muhurtas=tuple(day_windows),
            night_muhurtas=tuple(night_windows),
            abhijit_window=abhijit,
            brahma_muhurta_window=brahma,
            rahu_kalam_window=(rahu_start, rahu_end),
        )

    def ishta_to_datetime(
        self,
        target_date: datetime,
        latitude: float,
        longitude: float,
        ghatis: int,
        palas: int = 0,
        vipalas: float = 0.0,
    ) -> datetime:
        rise_dt, set_dt, next_rise_dt = self.get_solar_times(target_date, latitude, longitude)
        dinamana_sec = (set_dt - rise_dt).total_seconds()
        ratrimana_sec = (next_rise_dt - set_dt).total_seconds()

        total_ghatis = ghatis + (palas / 60.0) + (vipalas / 3600.0)

        if total_ghatis <= 30.0:
            day_ghati_sec = dinamana_sec / 30.0
            elapsed_sec = total_ghatis * day_ghati_sec
            return rise_dt + timedelta(seconds=elapsed_sec)
        else:
            day_ghati_sec = dinamana_sec / 30.0
            night_ghati_sec = ratrimana_sec / 30.0
            night_ghatis = total_ghatis - 30.0
            elapsed_sec = (30.0 * day_ghati_sec) + (night_ghatis * night_ghati_sec)
            return rise_dt + timedelta(seconds=elapsed_sec)

    def datetime_to_ishta(
        self,
        event_dt: datetime,
        latitude: float,
        longitude: float,
    ) -> IshtaKala:
        rise_dt, set_dt, next_rise_dt = self.get_solar_times(event_dt, latitude, longitude)
        
        if event_dt < rise_dt:
            prev_date = event_dt - timedelta(days=1)
            rise_dt, set_dt, next_rise_dt = self.get_solar_times(prev_date, latitude, longitude)

        dinamana_sec = (set_dt - rise_dt).total_seconds()
        ratrimana_sec = (next_rise_dt - set_dt).total_seconds()

        if event_dt <= set_dt:
            elapsed_sec = (event_dt - rise_dt).total_seconds()
            day_ghati_sec = dinamana_sec / 30.0
            total_ghatis = elapsed_sec / day_ghati_sec
        else:
            elapsed_night_sec = (event_dt - set_dt).total_seconds()
            night_ghati_sec = ratrimana_sec / 30.0
            total_ghatis = 30.0 + (elapsed_night_sec / night_ghati_sec)

        ghatis = int(total_ghatis)
        rem_palas = (total_ghatis - ghatis) * 60.0
        palas = int(rem_palas)
        vipalas = round((rem_palas - palas) * 60.0, 2)

        return IshtaKala(
            ghatis=ghatis,
            palas=palas,
            vipalas=vipalas,
            total_ghatis=round(total_ghatis, 4),
            local_time=event_dt,
        )

    def evaluate_kula_compatibility(
        self,
        samskara_name: str,
        gotra_user: Optional[str] = None,
        gotra_partner: Optional[str] = None,
        kula_devata: Optional[str] = None,
        varna: Optional[str] = None,
    ) -> dict[str, Any]:
        issues = []
        is_favorable = True
        
        if samskara_name.lower() in ("vivaha", "vivah", "marriage"):
            if gotra_user and gotra_partner:
                if gotra_user.strip().lower() == gotra_partner.strip().lower():
                    issues.append(f"Sagotra Dosha: Both belong to Gotra '{gotra_user}'. Classical Shastra strictly prohibits Sagotra marriage.")
                    is_favorable = False
                    
        return {
            "samskara": samskara_name,
            "gotra_user": gotra_user,
            "gotra_partner": gotra_partner,
            "is_favorable": is_favorable,
            "issues": issues,
            "classical_rule": "Gotra, Pravara, and Kula lineage integrity must be preserved in Vivaha and Upanayana Samskaras."
        }

    def _jd_to_utc(self, jd: float) -> datetime:
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
