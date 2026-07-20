"""
AstroOS — Yoga Engine (Module 8)

Independent service that evaluates every registered yoga against a D1
chart. Deliberately NOT wired into any router/API response and NOT given
a persistence layer in this pass — same scope discipline as HouseEngine
in Module 6.5: this engine is usable standalone today; wiring its output
into an endpoint or a database table is a separate, explicit decision for
later.

Evaluates and returns a result for EVERY registered yoga, including ones
that did not fire (is_present=False) — see the Yoga Engine Design Audit
§4 for why: a research platform comparing yogas across charts benefits
from "how close did this chart come," not just "did it fire." Filtering
down to only is_present=True results, if wanted, is the caller's choice.

Phase 2 extensions (v2.1.0 "Vistara"):
  - evaluate_with_strength(): returns results with 0-100 numerical scores.
  - get_activation_timeline(): correlates yogas with Dasha periods.
  - get_yogas_by_category(): filtered/category-grouped query.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from apps.api.domain.dasha import DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.services.house_engine import HouseEngine
from apps.api.services.yoga_predicates import YogaContext
from apps.api.services.yoga_registry import all_yogas
from apps.api.services.yoga_strength import compute_strength_score_for_all
from apps.api.services.yoga_timeline import (
    YogaTimeline,
    build_all_timelines,
    build_yoga_timeline,
)

# Importing this triggers every yoga module's @register_yoga decorators.
from apps.api.services import yogas as _yogas  # noqa: F401


class YogaEngine:
    """
    Stateless service evaluating all registered yogas against a chart.
    No Swiss Ephemeris or database dependency — operates purely on an
    already-computed D1Chart.
    """

    def __init__(self, house_engine: HouseEngine | None = None) -> None:
        self._house_engine = house_engine or HouseEngine()

    def evaluate_all(self, chart: D1Chart) -> list[YogaResult]:
        """
        Evaluate every registered yoga against this chart. Returns one
        YogaResult per registered yoga (present or not).
        """
        ctx = YogaContext.build(chart, self._house_engine)
        results: list[YogaResult] = []
        for definition in all_yogas():
            result = definition.evaluator(ctx)
            if result is not None:
                results.append(result)
        return results

    def evaluate_one(self, chart: D1Chart, yoga_id: str) -> YogaResult | None:
        """Evaluate a single yoga by its stable ID, for targeted debugging/research."""
        from apps.api.services.yoga_registry import get_yoga

        definition = get_yoga(yoga_id)
        if definition is None:
            raise ValueError(f"No yoga registered with id {yoga_id!r}")
        ctx = YogaContext.build(chart, self._house_engine)
        return definition.evaluator(ctx)

    # ------------------------------------------------------------------
    # Phase 2: Strength-scored evaluation
    # ------------------------------------------------------------------

    def evaluate_with_strength(self, chart: D1Chart) -> list[YogaResult]:
        """
        Evaluate every registered yoga AND compute a 0-100 numerical
        strength score for each one. The score is based on:
          - Planetary dignity (exalted, own sign, debilitated, etc.)
          - House placement (kendra, trikona, dusthana)
          - Benefic/malefic aspects on involved planets
          - Conjunction quality
          - Combustion and retrograde status

        Returns one YogaResult per registered yoga with strength_score
        populated. Only present yogas get a non-zero score.
        """
        results = self.evaluate_all(chart)
        ctx = YogaContext.build(chart, self._house_engine)
        return compute_strength_score_for_all(ctx, results)

    # ------------------------------------------------------------------
    # Phase 2: Yoga activation timeline
    # ------------------------------------------------------------------

    def get_activation_timeline(
        self,
        chart: D1Chart,
        dasha_tree: DashaTree,
        today: date,
        max_depth: int = 3,
    ) -> list[YogaTimeline]:
        """
        Correlate all present yogas with Dasha periods to determine when
        each yoga activates. A yoga activates when any of its involved
        planets rule the current Mahadasha or Antardasha period.

        Args:
            chart: The D1 chart to evaluate yogas against.
            dasha_tree: The computed DashaTree for the native.
            today: Today's date (used to mark current activation).
            max_depth: Maximum dasha depth (1=Mahadasha, 2=+Antardasha, 3=+Pratyantar).

        Returns:
            List of YogaTimeline objects, one per present yoga, sorted by
            next activation date.
        """
        results = self.evaluate_all(chart)
        timelines = build_all_timelines(results, dasha_tree, today, max_depth)
        return sorted(
            timelines,
            key=lambda t: t.current_activation.start_date if t.current_activation else date.max,
        )

    def get_yoga_timeline(
        self,
        chart: D1Chart,
        yoga_id: str,
        dasha_tree: DashaTree,
        today: date,
        max_depth: int = 3,
    ) -> Optional[YogaTimeline]:
        """
        Get the activation timeline for a single yoga by ID.
        """
        result = self.evaluate_one(chart, yoga_id)
        if result is None or not result.is_present:
            return None
        return build_yoga_timeline(result, dasha_tree, today, max_depth)

    # ------------------------------------------------------------------
    # Phase 2: Query helpers
    # ------------------------------------------------------------------

    def get_yogas_by_category(
        self,
        chart: D1Chart,
        category: str,
        present_only: bool = False,
    ) -> list[YogaResult]:
        """
        Filter yoga results by category (e.g. "Chandra Yoga", "Nabhasa Yoga").
        If present_only=True, only returns yogas that fired.
        """
        results = self.evaluate_all(chart)
        filtered = [r for r in results if r.category == category]
        if present_only:
            filtered = [r for r in filtered if r.is_present]
        return filtered

    def get_present_yogas(self, chart: D1Chart) -> list[YogaResult]:
        """Return only the yogas that are present (is_present=True)."""
        return [r for r in self.evaluate_all(chart) if r.is_present]
