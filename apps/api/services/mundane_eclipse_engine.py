"""
AstroOS — Standalone Mundane Eclipse (Grahana) Engine
Classical Reference: Brihat Samhita (Varahamihira Ch. 5 Rahu Chara), Narada Samhita.
Calculates solar & lunar eclipses, duration of impact, afflicted signs/stars,
and directional vulnerability for mundane astrological forecasting.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.mundane import EclipseType, KurmaDirection, MundaneEclipse
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.synastry_engine import _NAKSHATRA_ORDER, _RASHI_ORDER

# Mapping from Nakshatras to Kurma Directions (9 sectors)
_NAKSHATRA_TO_DIRECTION: dict[str, KurmaDirection] = {
    "krittika": KurmaDirection.CENTER,
    "rohini": KurmaDirection.CENTER,
    "mrigashira": KurmaDirection.CENTER,
    "ardra": KurmaDirection.EAST,
    "punarvasu": KurmaDirection.EAST,
    "pushya": KurmaDirection.EAST,
    "ashlesha": KurmaDirection.SOUTH_EAST,
    "magha": KurmaDirection.SOUTH_EAST,
    "purva_phalguni": KurmaDirection.SOUTH_EAST,
    "uttara_phalguni": KurmaDirection.SOUTH,
    "hasta": KurmaDirection.SOUTH,
    "chitra": KurmaDirection.SOUTH,
    "swati": KurmaDirection.SOUTH_WEST,
    "vishakha": KurmaDirection.SOUTH_WEST,
    "anuradha": KurmaDirection.SOUTH_WEST,
    "jyeshtha": KurmaDirection.WEST,
    "mula": KurmaDirection.WEST,
    "purva_ashadha": KurmaDirection.WEST,
    "uttara_ashadha": KurmaDirection.NORTH_WEST,
    "shravana": KurmaDirection.NORTH_WEST,
    "dhanishta": KurmaDirection.NORTH_WEST,
    "shatabhisha": KurmaDirection.NORTH,
    "purva_bhadrapada": KurmaDirection.NORTH,
    "uttara_bhadrapada": KurmaDirection.NORTH,
    "revati": KurmaDirection.NORTH_EAST,
    "ashwini": KurmaDirection.NORTH_EAST,
    "bharani": KurmaDirection.NORTH_EAST,
}


class MundaneEclipseEngine:
    """
    Standalone engine for detecting and analyzing Mundane Eclipses (Grahanas).
    """

    def __init__(self, wrapper: Optional[EphemerisWrapper] = None) -> None:
        self._wrapper = wrapper or EphemerisWrapper(ephemeris_path="data/ephemeris")

    def _get_positions(self, dt: datetime, ayanamsa: str) -> tuple[float, float, float, float]:
        res = self._wrapper.calculate(dt, 0.0, 0.0, ayanamsa)
        sun = next(p for p in res.planet_positions if p.planet.lower() == "sun")
        moon = next(p for p in res.planet_positions if p.planet.lower() == "moon")
        rahu = next(p for p in res.planet_positions if p.planet.lower() == "rahu")
        ketu = next(p for p in res.planet_positions if p.planet.lower() == "ketu")
        return sun.sidereal_longitude, moon.sidereal_longitude, rahu.sidereal_longitude, ketu.sidereal_longitude

    def find_eclipses_for_year(self, year: int, ayanamsa: str = "lahiri") -> tuple[MundaneEclipse, ...]:
        """
        Scans the year for solar and lunar eclipses by detecting syzygies near lunar nodes.
        """
        eclipses: list[MundaneEclipse] = []
        cur = datetime(year, 1, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(year, 12, 31, 23, 59, tzinfo=timezone.utc)

        # Step through in 2-day increments
        while cur <= end:
            s_long, m_long, r_long, k_long = self._get_positions(cur, ayanamsa)

            # Node proximity
            dist_sun_rahu = min(abs(s_long - r_long) % 360.0, 360.0 - (abs(s_long - r_long) % 360.0))
            dist_sun_ketu = min(abs(s_long - k_long) % 360.0, 360.0 - (abs(s_long - k_long) % 360.0))
            near_node = min(dist_sun_rahu, dist_sun_ketu) <= 18.5

            if near_node:
                # Check New Moon (Solar Eclipse candidate) or Full Moon (Lunar Eclipse candidate)
                syzygy_diff = (m_long - s_long) % 360.0
                is_solar_cand = syzygy_diff <= 15.0 or syzygy_diff >= 345.0
                is_lunar_cand = abs(syzygy_diff - 180.0) <= 15.0

                if is_solar_cand or is_lunar_cand:
                    # Refine peak instant
                    peak_dt = self._refine_eclipse_peak(cur, is_solar_cand, ayanamsa)
                    if peak_dt and (not eclipses or abs((peak_dt - eclipses[-1].peak_utc).days) > 10):
                        ecl = self._build_eclipse_record(peak_dt, is_solar_cand, ayanamsa)
                        eclipses.append(ecl)
                        cur = peak_dt + timedelta(days=12)

            cur += timedelta(days=2)

        return tuple(eclipses)

    def _refine_eclipse_peak(self, approx_dt: datetime, is_solar: bool, ayanamsa: str) -> Optional[datetime]:
        left = approx_dt - timedelta(days=2)
        right = approx_dt + timedelta(days=2)
        target_diff = 0.0 if is_solar else 180.0
        best_dt = approx_dt

        for _ in range(25):
            mid = left + (right - left) / 2
            s_long, m_long, _, _ = self._get_positions(mid, ayanamsa)
            diff = (m_long - s_long - target_diff + 180.0) % 360.0 - 180.0
            best_dt = mid

            if abs(diff) < 0.0001:
                return mid
            if diff < 0:
                left = mid
            else:
                right = mid
        return best_dt

    def _build_eclipse_record(self, peak_dt: datetime, is_solar: bool, ayanamsa: str) -> MundaneEclipse:
        s_long, m_long, r_long, k_long = self._get_positions(peak_dt, ayanamsa)
        eclipsed_long = s_long if is_solar else m_long

        rashi_idx = int(eclipsed_long // 30.0) % 12
        rashi = _RASHI_ORDER[rashi_idx]

        nak_idx = int(eclipsed_long / (360.0 / 27.0)) % 27
        nakshatra = _NAKSHATRA_ORDER[nak_idx]

        dist_r = min(abs(eclipsed_long - r_long) % 360.0, 360.0 - (abs(eclipsed_long - r_long) % 360.0))
        node = "Rahu" if dist_r < 90.0 else "Ketu"

        duration_hours = round(3.5 if is_solar else 3.0, 1)
        # Classical rule (Brihat Samhita): Solar eclipse hours -> years (or 12 * duration_months); Lunar hours -> months
        impact_duration_months = round((duration_hours * 12.0) if is_solar else duration_hours, 1)

        direction = _NAKSHATRA_TO_DIRECTION.get(nakshatra, KurmaDirection.CENTER)

        ecl_type = EclipseType.SOLAR_TOTAL if is_solar else EclipseType.LUNAR_TOTAL

        summary = (
            f"{'Solar' if is_solar else 'Lunar'} Eclipse at {eclipsed_long:.2f}° {rashi.capitalize()} "
            f"in {nakshatra.capitalize()} Nakshatra (Node: {node}). "
            f"Eclipse duration: {duration_hours} hrs. Mundane influence window: {impact_duration_months} months. "
            f"Afflicts Kurma directional sector: {direction.value.upper()}."
        )

        return MundaneEclipse(
            eclipse_type=ecl_type,
            peak_utc=peak_dt,
            eclipsed_rashi=rashi.capitalize(),
            eclipsed_nakshatra=nakshatra.capitalize(),
            node_involved=node,
            duration_hours=duration_hours,
            impact_duration_months=impact_duration_months,
            afflicted_directions=(direction,),
            impact_summary=summary,
        )
