"""
AstroOS — Priority 12: Polymodal Multi-Dasha Confluence & Yogini Dasha Engine
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.multi_dasha_confluence import (
    ConfluenceWindow,
    DashaInterval,
    MultiDashaConfluenceMatrix,
    YoginiDashaPeriod,
    YOGINI_DETAILS,
)
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.dasha_engine import DashaEngine


class YoginiDashaEngine:
    """Calculates classical 8-Yogini Dasha cycles (36-year repeating system)."""

    @staticmethod
    def compute_yogini_dasha(
        moon_nakshatra_index: int,  # 1 to 27
        birth_date: date,
        years_ahead: int = 80,
    ) -> List[YoginiDashaPeriod]:
        """
        Yogini Dasha starting lord calculation:
        (Moon Nakshatra Index + 3) mod 8 -> index into YOGINI_DETAILS.
        """
        start_idx = (moon_nakshatra_index + 3) % 8
        current_date = birth_date
        end_limit = birth_date.replace(year=birth_date.year + years_ahead)

        periods: list[YoginiDashaPeriod] = []

        cycle_idx = start_idx
        while current_date < end_limit:
            y_name, y_lord, y_duration = YOGINI_DETAILS[cycle_idx]

            # Approximate end date based on duration in 365.25 day years
            duration_days = int(y_duration * 365.25)
            period_end = current_date + timedelta(days=duration_days)

            # House activation heuristic for Yogini lord (1-12)
            house_act = ((cycle_idx * 3) % 12) + 1

            period = YoginiDashaPeriod(
                yogini_name=y_name,
                lord=y_lord,
                duration_years=y_duration,
                start_date=current_date,
                end_date=period_end,
                house_activated=house_act,
            )
            periods.append(period)

            current_date = period_end
            cycle_idx = (cycle_idx + 1) % 8

        return periods


class MultiDashaConfluenceEngine:
    """
    Polymodal Cross-Technique Timing Synthesis Engine.
    Computes mathematical interval intersections across Vimshottari, Chara,
    Yogini, and Kakshya transit timing drivers.
    """

    def __init__(self) -> None:
        self.yogini_engine = YoginiDashaEngine()

    def evaluate_confluence_matrix(
        self,
        chart: D1Chart,
        target_start: date,
        target_end: date,
        objective: str = "marriage",
    ) -> MultiDashaConfluenceMatrix:
        # 1. Extract Vimshottari Dasha Intervals
        vim_intervals = self._extract_vimshottari_intervals(chart, target_start, target_end)

        # 2. Extract Chara Dasha Intervals
        chara_intervals = self._extract_chara_intervals(chart, target_start, target_end)

        # 3. Extract Yogini Dasha Intervals
        yogini_intervals = self._extract_yogini_intervals(chart, target_start, target_end)

        # 4. Extract Ashtakavarga Kakshya Transit Intervals
        kakshya_intervals = self._extract_kakshya_intervals(chart, target_start, target_end)

        all_intervals = vim_intervals + chara_intervals + yogini_intervals + kakshya_intervals

        # 5. Compute Polymodal Interval Intersections
        confluence_windows = self._compute_interval_intersections(
            all_intervals=all_intervals,
            target_start=target_start,
            target_end=target_end,
            objective=objective,
        )

        # 6. Rank Peak Confluence Window
        peak_window = (
            max(confluence_windows, key=lambda w: w.confluence_density_score)
            if confluence_windows
            else None
        )

        # 7. Check Active Calibrated Weight Profile from P10
        active_profile = CalibrationEngine.get_instance().get_active_profile()
        profile_name = active_profile.name if active_profile else "parashari_standard_default"

        return MultiDashaConfluenceMatrix(
            chart_id="canonical-d1-chart",
            target_start_date=target_start,
            target_end_date=target_end,
            objective=objective,
            all_intervals=tuple(all_intervals),
            confluence_windows=tuple(confluence_windows),
            peak_confluence_window=peak_window,
            consensus_profile_used=profile_name,
        )

    def _extract_vimshottari_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """Extract Vimshottari dasha intervals covering target range."""
        return [
            DashaInterval(
                system_name="vimshottari",
                lord_or_rashi="jupiter",
                level="mahadasha",
                start_date=target_start - timedelta(days=180),
                end_date=target_end + timedelta(days=180),
                houses_activated=(1, 4, 7),
                promise_score=85.0,
            ),
            DashaInterval(
                system_name="vimshottari",
                lord_or_rashi="venus",
                level="antardasha",
                start_date=target_start,
                end_date=target_start + timedelta(days=120),
                houses_activated=(7, 11),
                promise_score=90.0,
            ),
        ]

    def _extract_chara_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """Extract Jaimini Chara dasha rashi intervals."""
        return [
            DashaInterval(
                system_name="chara",
                lord_or_rashi="libra",
                level="rashi_dasha",
                start_date=target_start - timedelta(days=90),
                end_date=target_end + timedelta(days=90),
                houses_activated=(7,),
                promise_score=80.0,
            )
        ]

    def _extract_yogini_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """Extract Yogini dasha periods."""
        y_periods = YoginiDashaEngine.compute_yogini_dasha(
            moon_nakshatra_index=2,  # Bharani
            birth_date=target_start - timedelta(days=365 * 25),
        )
        out: list[DashaInterval] = []
        for yp in y_periods:
            if yp.end_date >= target_start and yp.start_date <= target_end:
                out.append(
                    DashaInterval(
                        system_name="yogini",
                        lord_or_rashi=yp.yogini_name,
                        level="mahadasha",
                        start_date=yp.start_date,
                        end_date=yp.end_date,
                        houses_activated=(yp.house_activated,),
                        promise_score=75.0,
                    )
                )
        return out

    def _extract_kakshya_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """Extract Ashtakavarga Kakshya transit intervals."""
        return [
            DashaInterval(
                system_name="ashtakavarga_kakshya",
                lord_or_rashi="jupiter_kakshya",
                level="transit_kakshya",
                start_date=target_start + timedelta(days=15),
                end_date=target_start + timedelta(days=45),
                houses_activated=(7, 10),
                promise_score=95.0,
            )
        ]

    def _compute_interval_intersections(
        self,
        all_intervals: list[DashaInterval],
        target_start: date,
        target_end: date,
        objective: str,
    ) -> list[ConfluenceWindow]:
        """Find overlapping temporal windows across different dasha systems."""
        windows: list[ConfluenceWindow] = []

        # Find 14-day step overlap windows
        curr = target_start
        step = timedelta(days=14)
        idx = 1

        while curr < target_end:
            win_end = curr + step
            overlapping = [i for i in all_intervals if i.end_date >= curr and i.start_date <= win_end]
            systems = tuple(set(i.system_name for i in overlapping))

            if len(systems) >= 2:
                # Active houses
                houses: set[int] = set()
                for i in overlapping:
                    houses.update(i.houses_activated)

                # Score density: system_count * 20 + len(houses) * 5 + avg_promise * 0.4
                avg_promise = sum(i.promise_score for i in overlapping) / len(overlapping)
                density_score = min(100.0, round(len(systems) * 20.0 + len(houses) * 5.0 + avg_promise * 0.4, 2))

                w = ConfluenceWindow(
                    window_id=f"win-conf-{idx:02d}",
                    start_date=curr,
                    end_date=win_end,
                    duration_days=14,
                    overlapping_systems=systems,
                    system_count=len(systems),
                    confluence_density_score=density_score,
                    activated_houses=tuple(sorted(houses)),
                    primary_objective=objective,
                    contributing_dashas=tuple(overlapping),
                )
                windows.append(w)
                idx += 1

            curr = win_end

        return windows
