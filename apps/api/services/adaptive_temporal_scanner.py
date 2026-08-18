"""
AstroOS — Adaptive Temporal Scanner Service

Implements the multi-scale temporal zoom hierarchy:
  1. Macro Scan: Dasha & Antardasha transition boundaries
  2. Meso Scan: Major planetary transit intervals (~30 days)
  3. Micro Scan: High-consensus weekly refinement (~7 days)

Ensures calculations snap to astronomical inflection points rather than brute force scanning.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.prediction_orchestration import TemporalResolution, TimeSlice


class AdaptiveTemporalScanner:
    """Generates and refines discrete temporal intervals across a target time range."""

    def generate_macro_slices(
        self,
        dasha_tree: Optional[DashaTree],
        target_start: date,
        target_end: date,
    ) -> list[TimeSlice]:
        """
        Generate macro-level slices by intersecting the target date range
        with Dasha/Antardasha boundaries. If no dasha tree is available,
        splits the range into quarterly (90-day) intervals.
        """
        if target_start >= target_end:
            return []

        if not dasha_tree or not dasha_tree.mahadashas:
            return self._generate_fixed_slices(
                target_start, target_end, timedelta(days=90), TemporalResolution.MACRO_DASHA, "Quarterly Macro Window"
            )

        boundaries: set[date] = {target_start, target_end}

        for md in dasha_tree.mahadashas:
            # If mahadasha overlaps with target range
            if md.end_date >= target_start and md.start_date <= target_end:
                if target_start <= md.start_date <= target_end:
                    boundaries.add(md.start_date)
                if target_start <= md.end_date <= target_end:
                    boundaries.add(md.end_date)

                # Antardashas
                for ad in md.sub_periods:
                    if ad.end_date >= target_start and ad.start_date <= target_end:
                        if target_start <= ad.start_date <= target_end:
                            boundaries.add(ad.start_date)
                        if target_start <= ad.end_date <= target_end:
                            boundaries.add(ad.end_date)

        sorted_bounds = sorted(boundaries)
        slices: list[TimeSlice] = []

        for i in range(len(sorted_bounds) - 1):
            s_date = sorted_bounds[i]
            e_date = sorted_bounds[i + 1]
            if s_date >= e_date:
                continue

            mid_days = (e_date - s_date).days // 2
            mid_date = s_date + timedelta(days=mid_days)
            mid_dt = datetime.combine(mid_date, time(12, 0), tzinfo=timezone.utc)

            slices.append(
                TimeSlice(
                    start_date=s_date,
                    end_date=e_date,
                    midpoint_datetime_utc=mid_dt,
                    resolution=TemporalResolution.MACRO_DASHA,
                    trigger_reason=f"Antardasha Boundary [{s_date} to {e_date}]",
                )
            )

        return slices

    def refine_to_meso_slices(
        self,
        macro_slice: TimeSlice,
        step_days: int = 30,
    ) -> list[TimeSlice]:
        """Refines an active macro slice into monthly (~30-day) Gochara evaluation intervals."""
        return self._generate_fixed_slices(
            macro_slice.start_date,
            macro_slice.end_date,
            timedelta(days=step_days),
            TemporalResolution.MESO_GOCHARA,
            f"Meso Gochara Scan in {macro_slice.trigger_reason}",
        )

    def refine_to_micro_slices(
        self,
        meso_slice: TimeSlice,
        step_days: int = 7,
    ) -> list[TimeSlice]:
        """Refines a high-scoring meso slice into weekly (~7-day) transit convergence intervals."""
        return self._generate_fixed_slices(
            meso_slice.start_date,
            meso_slice.end_date,
            timedelta(days=step_days),
            TemporalResolution.MICRO_INGRESS,
            f"Micro Refinement in {meso_slice.trigger_reason}",
        )

    def _generate_fixed_slices(
        self,
        start_date: date,
        end_date: date,
        step: timedelta,
        resolution: TemporalResolution,
        reason: str,
    ) -> list[TimeSlice]:
        slices: list[TimeSlice] = []
        cur_start = start_date

        while cur_start < end_date:
            cur_end = min(cur_start + step, end_date)
            mid_days = (cur_end - cur_start).days // 2
            mid_date = cur_start + timedelta(days=mid_days)
            mid_dt = datetime.combine(mid_date, time(12, 0), tzinfo=timezone.utc)

            slices.append(
                TimeSlice(
                    start_date=cur_start,
                    end_date=cur_end,
                    midpoint_datetime_utc=mid_dt,
                    resolution=resolution,
                    trigger_reason=reason,
                )
            )
            cur_start = cur_end

        return slices