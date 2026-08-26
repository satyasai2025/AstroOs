"""
AstroOS — Mundane Ingress Engine (Medini Jyotisha)
Solves exact astronomical moments for:
  1. Chaitra Shukla Pratipada (Annual World/National Horoscope - Sun/Moon conjunction)
  2. Four Cardinal Solar Ingresses (Mesha, Karka, Tula, Makara Sankrantis)
  3. Secondary Ingresses (Aridra Pravesha, Simha, Mithuna, Dhanu Sankrantis for Cabinet)
And casts national horoscopes for country capitals.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from apps.api.domain.mundane import IngressType, MundaneIngressChart, MundaneIngressMoment
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.synastry_engine import _RASHI_LORDS, _RASHI_ORDER

_WEEKDAY_LORDS = ("moon", "mars", "mercury", "jupiter", "venus", "saturn", "sun")  # 0=Monday .. 6=Sunday


class MundaneIngressEngine:
    """
    High-precision solver for Mundane Ingresses and National Ingress Horoscopes.
    """

    def __init__(self, wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")
        self._horoscope = HoroscopeEngine(self._wrapper)

    def _get_sun_moon_longitudes(self, dt: datetime, ayanamsa: str) -> tuple[float, float]:
        res = self._wrapper.calculate(dt, 0.0, 0.0, ayanamsa)
        sun = next(p for p in res.planet_positions if p.planet.lower() == "sun")
        moon = next(p for p in res.planet_positions if p.planet.lower() == "moon")
        return sun.sidereal_longitude, moon.sidereal_longitude

    def _get_sun_longitude(self, dt: datetime, ayanamsa: str) -> float:
        res = self._wrapper.calculate(dt, 0.0, 0.0, ayanamsa)
        sun = next(p for p in res.planet_positions if p.planet.lower() == "sun")
        return sun.sidereal_longitude

    def find_chaitra_shukla_pratipada(self, year: int, ayanamsa: str = "lahiri") -> MundaneIngressMoment:
        """
        Solves the exact instant of the New Moon (Amavasya ending / Shukla Pratipada start)
        occurring in Pisces/Aries prior to or during the Sun's transit near 0° Aries.
        """
        # Initial search window: March 15 to April 25 of the given year
        t_start = datetime(year, 3, 10, 0, 0, tzinfo=timezone.utc)
        t_end = datetime(year, 4, 25, 0, 0, tzinfo=timezone.utc)

        best_dt = t_start
        min_diff = 360.0

        # Step 1: 12-hour coarse scan
        cur = t_start
        while cur <= t_end:
            s_long, m_long = self._get_sun_moon_longitudes(cur, ayanamsa)
            diff = (m_long - s_long) % 360.0

            # Near New Moon (diff close to 0 or 360) and Sun is in late Pisces or early Aries (330° to 30°)
            if (diff < 15.0 or diff > 345.0) and (s_long >= 325.0 or s_long <= 35.0):
                ang_diff = diff if diff < 180.0 else (360.0 - diff)
                if ang_diff < min_diff:
                    min_diff = ang_diff
                    best_dt = cur
            cur += timedelta(hours=12)

        # Step 2: Bisection / Newton refinement to sub-second precision
        left = best_dt - timedelta(hours=18)
        right = best_dt + timedelta(hours=18)

        for _ in range(30):
            mid = left + (right - left) / 2
            s_long, m_long = self._get_sun_moon_longitudes(mid, ayanamsa)
            diff = (m_long - s_long) % 360.0
            if diff > 180.0:
                diff -= 360.0

            if abs(diff) < 0.00005:  # ~0.18 arcsecond precision
                best_dt = mid
                break

            if diff < 0:
                left = mid
            else:
                right = mid

        s_final, m_final = self._get_sun_moon_longitudes(best_dt, ayanamsa)
        weekday_idx = best_dt.weekday()  # 0=Monday, 6=Sunday
        weekday_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday_idx]
        weekday_lord = _WEEKDAY_LORDS[weekday_idx]

        return MundaneIngressMoment(
            ingress_type=IngressType.CHAITRA_SHUKLA_PRATIPADA,
            timestamp_utc=best_dt,
            sun_longitude=round(s_final, 4),
            moon_longitude=round(m_final, 4),
            weekday=weekday_name,
            weekday_lord=weekday_lord,
        )

    def find_solar_ingress(
        self,
        year: int,
        target_longitude: float,
        ingress_type: IngressType,
        approx_month: int,
        approx_day: int = 14,
        ayanamsa: str = "lahiri",
    ) -> MundaneIngressMoment:
        """
        Finds the exact instant when the Sun reaches a target sidereal longitude.
        """
        center = datetime(year, approx_month, approx_day, 12, 0, tzinfo=timezone.utc)
        left = center - timedelta(days=10)
        right = center + timedelta(days=10)
        best_dt = center
        for _ in range(30):
            mid = left + (right - left) / 2
            s_long = self._get_sun_longitude(mid, ayanamsa)
            diff = (s_long - target_longitude + 180.0) % 360.0 - 180.0
            best_dt = mid

            if abs(diff) < 0.00005:
                break

            if diff < 0:
                left = mid
            else:
                right = mid

        s_final, m_final = self._get_sun_moon_longitudes(best_dt, ayanamsa)
        weekday_idx = best_dt.weekday()
        weekday_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][weekday_idx]
        weekday_lord = _WEEKDAY_LORDS[weekday_idx]

        return MundaneIngressMoment(
            ingress_type=ingress_type,
            timestamp_utc=best_dt,
            sun_longitude=round(s_final, 4),
            moon_longitude=round(m_final, 4),
            weekday=weekday_name,
            weekday_lord=weekday_lord,
        )

    def generate_ingress_chart(
        self,
        moment: MundaneIngressMoment,
        country_name: str,
        capital_city: str,
        latitude: float,
        longitude: float,
        ayanamsa: str = "lahiri",
    ) -> MundaneIngressChart:
        """
        Generates the Mundane Ingress Horoscope for a nation's capital.
        """
        chart = self._horoscope.generate_d1(
            moment.timestamp_utc,
            latitude,
            longitude,
            ayanamsa,
        )

        asc_rashi = chart.ascendant.rashi.lower() if chart.ascendant else "aries"
        asc_lord = _RASHI_LORDS.get(asc_rashi, "sun")

        # 10th house rashi
        asc_idx = _RASHI_ORDER.index(asc_rashi)
        h10_idx = (asc_idx + 9) % 12
        h10_rashi = _RASHI_ORDER[h10_idx]
        h10_lord = _RASHI_LORDS.get(h10_rashi, "sun")

        return MundaneIngressChart(
            ingress_moment=moment,
            country_name=country_name,
            capital_city=capital_city,
            latitude=latitude,
            longitude=longitude,
            chart=chart,
            ascendant_rashi=asc_rashi.capitalize(),
            ascendant_lord=asc_lord.capitalize(),
            tenth_house_rashi=h10_rashi.capitalize(),
            tenth_house_lord=h10_lord.capitalize(),
        )
