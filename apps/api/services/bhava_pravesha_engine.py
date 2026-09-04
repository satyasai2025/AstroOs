"""
AstroOS — 24-Hour Bhava Pravesha Engine (BhaavantKundalis / gochar.kkk)
======================================================================
Provenance: Kundalee Binary gochar.kkk / Bhaavaanta.VBP (Vinay Jha)
Title: 24-Hour Bhaava Praveshas Of Planets

Siddhantic Invariant Decoded from gochar.kkk:
  "भावप्रवेश कुण्डली का प्रभाव अगली भावप्रवेश कुण्डली तक रहता है।"
  (The transit chart cast at the exact second of a planet's Bhava-entry
   remains the governing seed chart until its subsequent Bhava-entry.)
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from apps.api.domain.bhava_pravesha import BhavaEntryEvent, DailyBhavaPraveshaSchedule
from apps.api.services.bhavachalita_engine import VishamabhavaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper

_CLASSICAL_EIGHT = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "ketu")
_ALL_TRACKED = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")


class BhavaPraveshaEngine:
    """Calculates high-precision 24-hour Bhava Pravesha schedules for planets."""

    def __init__(
        self,
        vishamabhava_engine: Optional[VishamabhavaEngine] = None,
        ephemeris_wrapper: Optional[EphemerisWrapper] = None,
        ephemeris_path: str = "data/ephemeris",
    ) -> None:
        self.wrapper = ephemeris_wrapper or EphemerisWrapper(ephemeris_path=ephemeris_path)
        self.vishamabhava = vishamabhava_engine or VishamabhavaEngine(ephemeris_wrapper=self.wrapper)

    def compute_daily_schedule(
        self,
        target_date: date,
        latitude: float,
        longitude: float,
        timezone_offset_hours: float = 5.5,
        timezone_name: str = "IST",
        ayanamsa: str = "lahiri",
        planets_to_track: Tuple[str, ...] = _ALL_TRACKED,
        coarse_step_minutes: int = 15,
        bisection_tolerance_seconds: float = 1.0,
    ) -> DailyBhavaPraveshaSchedule:
        """
        Computes the complete 24-hour timeline of Bhava ingress moments from local
        midnight to next local midnight.
        """
        tz_delta = timedelta(hours=timezone_offset_hours)
        start_local = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
        end_local = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)

        start_utc = (start_local - tz_delta).replace(tzinfo=timezone.utc)
        end_utc = (end_local - tz_delta).replace(tzinfo=timezone.utc)

        # 1. Coarse sample grid
        grid_times: List[datetime] = []
        curr = start_utc
        step = timedelta(minutes=coarse_step_minutes)
        while curr <= end_utc:
            grid_times.append(curr)
            curr += step
        if grid_times[-1] < end_utc:
            grid_times.append(end_utc)

        # 2. Compute placements at all grid points
        grid_placements: List[Dict[str, int]] = []
        for t in grid_times:
            chart = self.vishamabhava.compute_bhavachalita(t, latitude, longitude, ayanamsa=ayanamsa)
            p_map = {k.lower(): v for k, v in chart.planet_bhava_placements.items()}
            grid_placements.append(p_map)

        # 3. Detect transitions and bisect to exact second for each planet
        events_by_p: Dict[str, List[BhavaEntryEvent]] = {p: [] for p in planets_to_track}

        for p in planets_to_track:
            for i in range(1, len(grid_times)):
                h_prev = grid_placements[i - 1].get(p)
                h_curr = grid_placements[i].get(p)
                if h_prev is not None and h_curr is not None and h_prev != h_curr:
                    t_a = grid_times[i - 1]
                    t_b = grid_times[i]

                    # Bisection to pinpoint crossing moment
                    low_t = t_a
                    high_t = t_b
                    while (high_t - low_t).total_seconds() > bisection_tolerance_seconds:
                        mid_t = low_t + (high_t - low_t) / 2
                        chart_mid = self.vishamabhava.compute_bhavachalita(mid_t, latitude, longitude, ayanamsa=ayanamsa)
                        pl_mid = {k.lower(): v for k, v in chart_mid.planet_bhava_placements.items()}
                        if pl_mid.get(p) == h_prev:
                            low_t = mid_t
                        else:
                            high_t = mid_t

                    t_ingress = high_t
                    chart_ing = self.vishamabhava.compute_bhavachalita(t_ingress, latitude, longitude, ayanamsa=ayanamsa)
                    pl_ing = {k.lower(): v for k, v in chart_ing.planet_bhava_placements.items()}
                    actual_house = pl_ing.get(p, h_curr)

                    # Get planet sidereal longitude and boundary sandhi
                    eph_res = self.wrapper.calculate(t_ingress, latitude, longitude, ayanamsa=ayanamsa)
                    p_lon = next((pos.sidereal_longitude for pos in eph_res.planet_positions if pos.planet.lower() == p), 0.0)

                    sandhi_lon = 0.0
                    if 1 <= actual_house <= len(chart_ing.houses):
                        sandhi_lon = chart_ing.houses[actual_house - 1].start_sandhi

                    local_dt = t_ingress + tz_delta
                    time_str = local_dt.strftime("%H:%M:%S")

                    event = BhavaEntryEvent(
                        planet=p,
                        entered_house=actual_house,
                        ingress_datetime_utc=t_ingress,
                        ingress_time_local_str=time_str,
                        planet_sidereal_lon=round(p_lon, 4),
                        cusp_boundary_lon=round(sandhi_lon, 4),
                        active_until_utc=None,
                        duration_minutes=0.0,
                        is_vidisha_kendrika=False,
                    )
                    events_by_p[p].append(event)

        # 4. Chain active_until_utc per planet according to Jha's invariant
        all_chronological: List[BhavaEntryEvent] = []
        final_events_by_p: Dict[str, Tuple[BhavaEntryEvent, ...]] = {}

        for p, ev_list in events_by_p.items():
            ev_list.sort(key=lambda x: x.ingress_datetime_utc)
            chained_list: List[BhavaEntryEvent] = []
            for k in range(len(ev_list)):
                ev = ev_list[k]
                if k < len(ev_list) - 1:
                    next_t = ev_list[k + 1].ingress_datetime_utc
                else:
                    next_t = end_utc
                dur = max(0.0, (next_t - ev.ingress_datetime_utc).total_seconds() / 60.0)
                chained_ev = replace(ev, active_until_utc=next_t, duration_minutes=round(dur, 2))
                chained_list.append(chained_ev)
                all_chronological.append(chained_ev)
            final_events_by_p[p] = tuple(chained_list)

        all_chronological.sort(key=lambda x: x.ingress_datetime_utc)

        return DailyBhavaPraveshaSchedule(
            target_date=target_date,
            latitude=latitude,
            longitude=longitude,
            timezone_offset_hours=timezone_offset_hours,
            timezone_name=timezone_name,
            total_events_count=len(all_chronological),
            events_by_planet=final_events_by_p,
            chronological_events=tuple(all_chronological),
            provenance="kundalee-binary gochar.kkk (BhaavantKundalis)",
            rule_version="1.0",
        )
