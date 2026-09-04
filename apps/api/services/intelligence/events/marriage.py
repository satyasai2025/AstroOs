"""
AstroOS — Marriage Prediction Module (Vinay Jha Cognitive Architecture)

Evaluates matrimonial timing, relationship fructification, and karmic delays:
- Primary House: 7th (Kalatra/Partner)
- Supporting Houses: 2nd (Kutumba/Family), 11th (Labha/Desires fulfilled)
- Natural Karakas: Venus (Shukra), Jupiter (Guru)
- Upagraha Modifiers: Mandi/Gulika in 7th or conjunct 7th lord / Venus creates delay/impediment.
- 5-Level Dasha Analysis via CognitiveReasoner
"""

from __future__ import annotations
from typing import Dict, List, Optional
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.intelligence.cognitive_reasoner import CognitiveReasoner, DashaPeriod5Level, CognitivePredictionResult


class MarriagePredictor:
    """
    Cognitive predictive engine for marriage timing.
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
            event_type="marriage",
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
