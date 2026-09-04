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
from apps.api.services.dasha_engine import (
    DashaEngine,
    _jaimini_sign_sequence,
    _jaimini_sign_years,
    _nakshatra_balance,
)
from apps.api.services.ephemeris_wrapper import jd_to_datetime, longitude_to_nakshatra
from packages.shared.constants import (
    SIGN_LORDS,
    VIMSHOTTARI_DASHA_YEARS,
    VIMSHOTTARI_SEQUENCE,
    VIMSHOTTARI_TOTAL_YEARS,
)

# Classical natural benefic / malefic classification (Parashari), used only
# as a simple, disclosed, real-but-crude promise_score signal for Vimshottari
# and Chara periods below — NOT a substitute for a full Shadbala/Ishta-Kashta
# scoring system. Mercury and the Moon are context-dependent classically
# (Mercury by association, Moon by paksha/waxing-waning); here they are
# treated as neutral rather than guessing an unverified refinement.
_NATURAL_BENEFICS = frozenset({"jupiter", "venus"})
_NATURAL_MALEFICS = frozenset({"saturn", "mars", "sun", "rahu", "ketu"})
_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


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
        # _build_full_cycle / _build_sign_full_cycle are pure period-tree
        # builders on DashaEngine that don't touch self._wrapper — no real
        # ephemeris wrapper is needed here since this engine reuses the
        # chart's already-computed sidereal positions instead of
        # re-running ephemeris.
        self._dasha_period_builder = DashaEngine(ephemeris_wrapper=None)

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

        chart_id = self._resolve_chart_id(chart)

        return MultiDashaConfluenceMatrix(
            chart_id=chart_id,
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
        """
        Extract real Vimshottari Mahadasha/Antardasha intervals overlapping
        the target range, computed from the chart's own Moon sidereal
        longitude and real birth date (derived from the chart's Julian Day —
        no separate birth_datetime is stored on D1Chart, so the JD it was
        already built from is the only honest source of the birth moment).

        Reuses the same pure period-tree math DashaEngine.compute_vimshottari
        uses internally (_nakshatra_balance / _build_full_cycle) rather than
        re-deriving the dasha formula, without re-running ephemeris (chart
        already carries the sidereal Moon position).
        """
        if chart is None:
            return []

        moon = self._find_planet(chart, "moon")
        if moon is None:
            return []

        birth_date = self._chart_birth_date(chart)

        first_lord, _balance, first_start = _nakshatra_balance(
            moon.sidereal_longitude, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, birth_date,
        )
        mahadashas = self._dasha_period_builder._build_full_cycle(
            first_lord, first_start,
            VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_DASHA_YEARS,
            VIMSHOTTARI_TOTAL_YEARS, max_depth=2,
        )

        out: list[DashaInterval] = []
        for md in mahadashas:
            self._collect_overlapping_periods(
                md, "vimshottari", chart, target_start, target_end, out,
            )
        return out

    def _extract_chara_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """
        Extract real Jaimini Chara Dasha rashi intervals overlapping the
        target range, computed from the chart's own D1 planet placements and
        Lagna rashi (Neelakantha's rule), reusing the same pure sign-period
        math DashaEngine.compute_chara() uses internally.
        """
        if chart is None:
            return []

        planet_signs = {p.planet: p.rashi for p in chart.planets}
        lagna_rashi = chart.ascendant.rashi
        birth_date = self._chart_birth_date(chart)

        sign_years = {s: _jaimini_sign_years(s, planet_signs) for s in _RASHI_ORDER}
        total_years = sum(sign_years.values())
        sign_sequence = _jaimini_sign_sequence(lagna_rashi)

        mahadashas = self._dasha_period_builder._build_sign_full_cycle(
            sign_sequence[0], birth_date, sign_sequence, sign_years, total_years, max_depth=1,
        )

        out: list[DashaInterval] = []
        asc_rashi_idx = _RASHI_ORDER.index(lagna_rashi)
        for md in mahadashas:
            if md.end_date < target_start or md.start_date > target_end:
                continue
            rashi_idx = _RASHI_ORDER.index(md.lord)
            house = ((rashi_idx - asc_rashi_idx) % 12) + 1
            out.append(
                DashaInterval(
                    system_name="chara",
                    lord_or_rashi=md.lord,
                    level="rashi_dasha",
                    start_date=md.start_date,
                    end_date=md.end_date,
                    houses_activated=(house,),
                    promise_score=self._sign_lord_promise_score(md.lord),
                )
            )
        return out

    def _extract_yogini_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """
        Extract Yogini dasha periods using the chart's REAL Moon nakshatra
        (derived from its real sidereal longitude) and REAL birth date,
        instead of a fabricated Bharani / 25-years-ago placeholder.
        """
        if chart is None:
            return []

        moon = self._find_planet(chart, "moon")
        if moon is None:
            return []

        nak_info = longitude_to_nakshatra(moon.sidereal_longitude)
        birth_date = self._chart_birth_date(chart)

        y_periods = YoginiDashaEngine.compute_yogini_dasha(
            moon_nakshatra_index=nak_info.nakshatra_number,
            birth_date=birth_date,
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
                        promise_score=self._sign_lord_promise_score(yp.lord),
                    )
                )
        return out

    def _extract_kakshya_intervals(
        self, chart: D1Chart, target_start: date, target_end: date
    ) -> list[DashaInterval]:
        """
        Ashtakavarga Kakshya (the 8-planet unequal subdivision of each sign,
        used for fine-grained transit timing) confluence is NOT YET
        IMPLEMENTED anywhere in this codebase — a grep across
        apps/api/services (including ashtakavarga_engine.py) found no real
        Kakshya computation to wire in, only this engine's own prior
        hardcoded placeholder. Rather than fabricate a Kakshya calculation
        here, this system is disclosed-excluded from the confluence matrix
        (returns an empty list) until a real Ashtakavarga Kakshya engine
        exists. `evaluate_confluence_matrix` simply concatenates this list
        into `all_intervals`, so an empty result here does not break the
        rest of the matrix — it only means "ashtakavarga_kakshya" will never
        appear as a contributing system in confluence_windows for now.
        """
        return []

    @staticmethod
    def _find_planet(chart: D1Chart, planet_name: str):
        return next((p for p in chart.planets if p.planet.lower() == planet_name), None)

    @staticmethod
    def _chart_birth_date(chart: D1Chart) -> date:
        """
        Real birth date derived from the chart's own Julian Day (D1Chart
        does not separately store birth_datetime_utc). This is the only
        honest source of "when this chart was born" available on the
        object — never a fabricated offset from the analysis window.
        """
        if chart.ephemeris is not None and chart.ephemeris.julian_day:
            return jd_to_datetime(chart.ephemeris.julian_day).date()
        # No ephemeris on chart (should not happen for a real D1Chart) —
        # fail loudly rather than silently fabricating a birth date.
        raise ValueError("Chart has no ephemeris.julian_day; cannot derive a real birth date.")

    @staticmethod
    def _sign_lord_promise_score(lord: str) -> float:
        """
        Simple, disclosed promise_score signal based on classical natural
        benefic/malefic classification of the period lord — not a full
        Shadbala/strength computation. Benefic lord periods score higher,
        malefic lower, everything else neutral.
        """
        lord = lord.lower()
        if lord in _NATURAL_BENEFICS:
            return 65.0
        if lord in _NATURAL_MALEFICS:
            return 40.0
        return 50.0

    def _collect_overlapping_periods(
        self,
        period,
        system_name: str,
        chart: D1Chart,
        target_start: date,
        target_end: date,
        out: list[DashaInterval],
    ) -> None:
        """Flatten a DashaPeriod tree (Mahadasha + Antardasha) into DashaIntervals overlapping the target window."""
        level_name = "mahadasha" if period.level == 1 else "antardasha"
        if period.end_date >= target_start and period.start_date <= target_end:
            out.append(
                DashaInterval(
                    system_name=system_name,
                    lord_or_rashi=period.lord,
                    level=level_name,
                    start_date=period.start_date,
                    end_date=period.end_date,
                    houses_activated=self._houses_activated_for_planet(chart, period.lord),
                    promise_score=self._sign_lord_promise_score(period.lord),
                )
            )
        for sub in period.sub_periods:
            self._collect_overlapping_periods(sub, system_name, chart, target_start, target_end, out)

    @staticmethod
    def _houses_activated_for_planet(chart: D1Chart, planet: str) -> tuple[int, ...]:
        """
        Houses activated by a Vimshottari lord: houses it rules from the
        real Lagna (sign lordship) plus the house it actually occupies in
        the natal chart — same "ruled houses + occupied house" pattern
        RectificationEngine._score_dasha_activation uses for dasha lord
        activation, applied here to derive real houses_activated instead of
        a fixed placeholder tuple.
        """
        asc_rashi_idx = _RASHI_ORDER.index(chart.ascendant.rashi)
        ruled_houses = {
            ((r_idx - asc_rashi_idx) % 12) + 1
            for r_idx, r_name in enumerate(_RASHI_ORDER)
            if SIGN_LORDS.get(r_name, "") == planet
        }
        occ = next((p for p in chart.planets if p.planet.lower() == planet), None)
        if occ is not None:
            ruled_houses.add(occ.house_number)
        return tuple(sorted(ruled_houses)) if ruled_houses else ()

    def _resolve_chart_id(self, chart: Optional[D1Chart]) -> str:
        """
        Real, deterministic chart identifier derived from the chart's own
        Julian Day + Ascendant sidereal longitude (D1Chart carries no
        explicit id/chart_id field), instead of the previous hardcoded
        "canonical-d1-chart" placeholder. Falls back to a clearly-labeled
        "no-chart-supplied" id only when no chart was passed at all.
        """
        if chart is None:
            return "no-chart-supplied"
        jd = chart.ephemeris.julian_day if chart.ephemeris is not None else 0.0
        asc = chart.ascendant.sidereal_longitude if chart.ascendant is not None else 0.0
        return f"d1-jd{jd:.6f}-asc{asc:.4f}"

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
