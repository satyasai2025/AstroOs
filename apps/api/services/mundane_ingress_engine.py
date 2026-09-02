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
        initiating Chaitra Masa (first Sun-Moon conjunction occurring while Sun is in sidereal Pisces / Meena).
        """
        t_start = datetime(year, 3, 1, 0, 0, tzinfo=timezone.utc)
        t_end = datetime(year, 4, 28, 0, 0, tzinfo=timezone.utc)
        cur = t_start
        step = timedelta(hours=3)
        best_dt = t_start

        while cur <= t_end:
            res1 = self._wrapper.calculate(cur, 0.0, 0.0, ayanamsa)
            s1 = next(p for p in res1.planet_positions if p.planet.lower() == "sun").sidereal_longitude
            m1 = next(p for p in res1.planet_positions if p.planet.lower() == "moon").sidereal_longitude
            diff1 = (m1 - s1) % 360.0

            nxt = cur + step
            res2 = self._wrapper.calculate(nxt, 0.0, 0.0, ayanamsa)
            s2 = next(p for p in res2.planet_positions if p.planet.lower() == "sun").sidereal_longitude
            m2 = next(p for p in res2.planet_positions if p.planet.lower() == "moon").sidereal_longitude
            diff2 = (m2 - s2) % 360.0

            # Conjunction occurs when diff crosses 0°/360° and Sun is in sidereal Pisces (>= 330°) or early Aries (<= 15°)
            in_pisces_or_aries = (s1 >= 330.0 or s1 <= 15.0)
            if (diff1 > 340.0 and diff2 < 20.0) and in_pisces_or_aries:
                left = cur
                right = nxt
                for _ in range(30):
                    mid = left + (right - left) / 2
                    s_m, m_m = self._get_sun_moon_longitudes(mid, ayanamsa)
                    d = (m_m - s_m) % 360.0
                    if d > 180.0:
                        d -= 360.0
                    if abs(d) < 0.00005:  # ~0.18 arcsecond precision
                        best_dt = mid
                        break
                    if d < 0:
                        left = mid
                    else:
                        right = mid
                best_dt = mid
                break
            cur = nxt

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
