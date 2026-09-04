"""
AstroOS - Tajika Annual Dasha Systems (Mudda Dasha & Patyayini Dasha)
Sources: Tajika Neelakanthi, PyJHora, B.V. Raman's Varshaphal
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from apps.api.domain.ephemeris import EphemerisResult
from apps.api.domain.varshaphal import MuddaDashaPeriod, PatyayiniDashaPeriod
from apps.api.services.ephemeris_wrapper import jd_to_datetime
from apps.api.services.tajaka_constants import (
    NAKSHATRA_LORDS,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
)

DEGREES_PER_NAKSHATRA = 360.0 / 27.0  # 13.333333333333334°


class TajakaDashaEngine:
    """Computes Mudda Dasha and Patyayini Dasha for the Varsha year."""

    @classmethod
    def calculate_mudda_dasha(
        cls,
        varsha_chart: EphemerisResult,
        solar_return_jd: float,
        year_duration_days: float = 365.2425,
    ) -> tuple[MuddaDashaPeriod, ...]:
        """
        Computes Vimshottari Mudda Dasha (Annual Dasha) starting from the Varsha Moon's
        Nakshatra position and balance of dasha.
        """
        moon_pos = next((p for p in varsha_chart.planet_positions if p.planet == "moon"), None)
        if moon_pos is None:
            return ()

        moon_long = moon_pos.sidereal_longitude % 360.0
        nak_idx = int(moon_long // DEGREES_PER_NAKSHATRA)  # 0..26
        deg_in_nak = moon_long % DEGREES_PER_NAKSHATRA
        fraction_remaining = 1.0 - (deg_in_nak / DEGREES_PER_NAKSHATRA)

        first_lord = NAKSHATRA_LORDS[nak_idx]
        start_order_idx = VIMSHOTTARI_ORDER.index(first_lord)

        current_jd = solar_return_jd
        periods: list[MuddaDashaPeriod] = []

        # First dasha has fractional balance
        full_first_duration = (VIMSHOTTARI_YEARS[first_lord] / 120.0) * year_duration_days
        first_duration = full_first_duration * fraction_remaining

        end_jd = current_jd + first_duration
        start_dt = jd_to_datetime(current_jd)
        end_dt = jd_to_datetime(end_jd)

        periods.append(cls._build_mudda_period(
            planet=first_lord,
            start_jd=current_jd,
            end_jd=end_jd,
            duration_days=round(first_duration, 4),
            start_dt=start_dt,
            end_dt=end_dt,
        ))
        current_jd = end_jd

        # Subsequent dashas in Vimshottari sequence until total year is covered
        accumulated_days = first_duration
        idx = (start_order_idx + 1) % len(VIMSHOTTARI_ORDER)

        while accumulated_days < (year_duration_days - 1e-4):
            lord = VIMSHOTTARI_ORDER[idx]
            lord_duration = (VIMSHOTTARI_YEARS[lord] / 120.0) * year_duration_days

            if accumulated_days + lord_duration > year_duration_days:
                lord_duration = year_duration_days - accumulated_days

            end_jd = current_jd + lord_duration
            start_dt = jd_to_datetime(current_jd)
            end_dt = jd_to_datetime(end_jd)

            periods.append(cls._build_mudda_period(
                planet=lord,
                start_jd=current_jd,
                end_jd=end_jd,
                duration_days=round(lord_duration, 4),
                start_dt=start_dt,
                end_dt=end_dt,
            ))
            current_jd = end_jd
            accumulated_days += lord_duration
            idx = (idx + 1) % len(VIMSHOTTARI_ORDER)

        return tuple(periods)

    @classmethod
    def _build_mudda_period(
        cls,
        planet: str,
        start_jd: float,
        end_jd: float,
        duration_days: float,
        start_dt: datetime,
        end_dt: datetime,
    ) -> MuddaDashaPeriod:
        # Build Antardashas
        antardashas: list[MuddaDashaPeriod] = []
        p_idx = VIMSHOTTARI_ORDER.index(planet)
        sub_current_jd = start_jd

        for i in range(len(VIMSHOTTARI_ORDER)):
            sub_lord = VIMSHOTTARI_ORDER[(p_idx + i) % len(VIMSHOTTARI_ORDER)]
            sub_duration = duration_days * (VIMSHOTTARI_YEARS[sub_lord] / 120.0)
            sub_end_jd = sub_current_jd + sub_duration
            sub_start_dt = jd_to_datetime(sub_current_jd)
            sub_end_dt = jd_to_datetime(sub_end_jd)

            antardashas.append(MuddaDashaPeriod(
                planet=sub_lord,
                start_jd=sub_current_jd,
                end_jd=sub_end_jd,
                duration_days=round(sub_duration, 4),
                start_date=sub_start_dt.isoformat(),
                end_date=sub_end_dt.isoformat(),
                antardashas=(),
            ))
            sub_current_jd = sub_end_jd

        return MuddaDashaPeriod(
            planet=planet,
            start_jd=start_jd,
            end_jd=end_jd,
            duration_days=duration_days,
            start_date=start_dt.isoformat(),
            end_date=end_dt.isoformat(),
            antardashas=tuple(antardashas),
        )

    @classmethod
    def calculate_patyayini_dasha(
        cls,
        varsha_chart: EphemerisResult,
        solar_return_jd: float,
        year_duration_days: float = 365.2425,
    ) -> tuple[PatyayiniDashaPeriod, ...]:
        """
        Computes Patyayini Dasha based on planetary Krishnamshas (degrees in sign).
        Points considered: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, and Ascendant.
        """
        items: list[tuple[str, float]] = []
        for p in varsha_chart.planet_positions:
            if p.planet in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"):
                items.append((p.planet, p.rashi_degree))

        asc_deg = varsha_chart.ascendant.rashi_degree
        items.append(("ascendant", asc_deg))

        # Sort by Krishnamsha (degree in sign)
        sorted_items = sorted(items, key=lambda x: x[1])

        # Compute differences (spans)
        periods: list[PatyayiniDashaPeriod] = []
        current_jd = solar_return_jd
        prev_deg = 0.0

        for i, (name, deg) in enumerate(sorted_items):
            span_deg = deg - prev_deg
            if span_deg <= 0.0:
                span_deg = 0.0001
            # Proportion of year = span_deg / 30.0
            duration = (span_deg / 30.0) * year_duration_days
            end_jd = current_jd + duration
            start_dt = jd_to_datetime(current_jd)
            end_dt = jd_to_datetime(end_jd)

            periods.append(PatyayiniDashaPeriod(
                planet=name,
                start_jd=current_jd,
                end_jd=end_jd,
                duration_days=round(duration, 4),
                krishnamsha_deg=round(deg, 4),
                start_date=start_dt.isoformat(),
                end_date=end_dt.isoformat(),
            ))
            current_jd = end_jd
            prev_deg = deg

        # Remaining span up to 30°
        rem_span = 30.0 - prev_deg
        if rem_span > 0.001 and periods:
            rem_duration = (rem_span / 30.0) * year_duration_days
            # Add to the last period or distribute
            last = periods[-1]
            end_jd = last.end_jd + rem_duration
            periods[-1] = PatyayiniDashaPeriod(
                planet=last.planet,
                start_jd=last.start_jd,
                end_jd=end_jd,
                duration_days=round(last.duration_days + rem_duration, 4),
                krishnamsha_deg=last.krishnamsha_deg,
                start_date=last.start_date,
                end_date=jd_to_datetime(end_jd).isoformat(),
            )

        return tuple(periods)
