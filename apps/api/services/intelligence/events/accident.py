"""
AstroOS — Accident & Sudden Trauma Prediction Module (Vinay Jha Cognitive Architecture)

Evaluates sudden shocks, accidents, surgical interventions, and physical trauma:
- Primary House: 8th (Sudden adversity / Randhra)
- Supporting Houses: 6th (Injuries/Vounds), 12th (Loss), 3rd (Bhratri/Travel accidents)
- Natural Karakas: Mars (Violent force, blood, surgery), Rahu (Sudden shocks), Ketu (Amputation/Cuts)
- Upagraha Modifiers: Gulika in 8th or on Lagna elevates sudden danger risk factor.
"""

from __future__ import annotations
from typing import Dict
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.intelligence.cognitive_reasoner import CognitiveReasoner, DashaPeriod5Level, CognitivePredictionResult


class AccidentPredictor:
    """
    Cognitive predictive engine for sudden accidents and physical trauma.
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
            event_type="accident",
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
