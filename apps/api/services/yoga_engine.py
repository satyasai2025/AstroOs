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
"""

from __future__ import annotations

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.services.house_engine import HouseEngine
from apps.api.services.yoga_predicates import YogaContext
from apps.api.services.yoga_registry import all_yogas

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
