"""
AstroOS — Career & Professional Elevation Module (Vinay Jha Cognitive Architecture)

Evaluates professional breakthroughs, elevation of status, promotions, and achievements:
- Primary House: 10th (Karma / Rajya Bhava)
- Supporting Houses: 1st (Lagna/Identity), 5th (Purva Punya), 9th (Bhagya), 11th (Labha), 2nd (Dhana)
- Natural Karakas: Sun (Authority), Saturn (Profession/Labor), Mercury (Trade/Intellect), Jupiter (Advisory)
- Upagraha Modifiers: Gulika in Upachaya (3, 6, 10, 11) acts as a powerful benefic booster (+1.5).
"""

from __future__ import annotations
from typing import Dict
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.intelligence.cognitive_reasoner import CognitiveReasoner, DashaPeriod5Level, CognitivePredictionResult


class CareerPredictor:
    """
    Cognitive predictive engine for career milestones and status elevation.
    """

    @classmethod
    def evaluate(
        cls,
        graph: LinkedChartGraph,
        dasha: DashaPeriod5Level,
    ) -> CognitivePredictionResult:
        return CognitiveReasoner.evaluate_event_dasha(
            graph=graph,
            dasha=dasha,
            event_type="career",
        )

    @classmethod
    def analyze_from_positions(
        cls,
        lagna_rashi_idx: int,
        graha_positions: Dict[str, int],
        gulika_rashi_idx: int,
        mandi_rashi_idx: int,
        dasha: DashaPeriod5Level,
    ) -> CognitivePredictionResult:
        graph = LinkedSystemBuilder.build_graph(
            lagna_rashi_idx=lagna_rashi_idx,
            graha_positions=graha_positions,
            gulika_rashi_idx=gulika_rashi_idx,
            mandi_rashi_idx=mandi_rashi_idx,
        )
        return cls.evaluate(graph, dasha)
