"""
AstroOS — Intelligent Timeline Predictor (Vinay Jha Cognitive Architecture)

Scans multi-year dasha periods across candidate time windows and evaluates
fructification probabilities using Cognitive Reasoner and Upagraha Modifiers.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.intelligence.cognitive_reasoner import (
    CognitiveReasoner,
    DashaPeriod5Level,
    CognitivePredictionResult,
)


class IntelligentPredictor:
    """
    Timeline event scanner evaluating multi-level dasha sequences.
    """

    def __init__(self, graph: LinkedChartGraph):
        self.graph = graph

    @classmethod
    def from_chart_coordinates(
        cls,
        lagna_rashi_idx: int,
        graha_positions: Dict[str, int],
        gulika_rashi_idx: int,
        mandi_rashi_idx: int,
    ) -> "IntelligentPredictor":
        graph = LinkedSystemBuilder.build_graph(
            lagna_rashi_idx=lagna_rashi_idx,
            graha_positions=graha_positions,
            gulika_rashi_idx=gulika_rashi_idx,
            mandi_rashi_idx=mandi_rashi_idx,
        )
        return cls(graph)

    def scan_timeline_for_event(
        self,
        event_type: str,
        dasha_periods: List[DashaPeriod5Level],
        score_threshold: float = 5.0,
    ) -> List[CognitivePredictionResult]:
        """
        Scans a sequence of 5-level dasha periods and returns predictions that meet or exceed score_threshold.
        """
        results: List[CognitivePredictionResult] = []
        for period in dasha_periods:
            res = CognitiveReasoner.evaluate_event_dasha(
                graph=self.graph,
                dasha=period,
                event_type=event_type,
            )
            if res.cognitive_score >= score_threshold:
                results.append(res)
        return results

