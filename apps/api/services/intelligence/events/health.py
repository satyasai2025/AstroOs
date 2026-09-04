"""
AstroOS — Health & Longevity Crisis Module (Vinay Jha Cognitive Architecture)

Evaluates physical health crises, acute illness timing, and longevity vulnerabilities:
- Primary Houses: 6th (Roga/Disease), 8th (Mrityu/Vulnerability)
- Supporting Houses: 12th (Hospitalization/Loss), 2nd/7th (Maraka lords), 1st (Deha/Physical body)
- Natural Karakas: Saturn (Ayushya/Chronic suffering), Mars (Acute flareups), Rahu (Toxic/obscure conditions)
- Upagraha Modifiers: Gulika/Mandi in 8th house directly activates Mrityu/Crisis vulnerability (+2.5).
"""

from __future__ import annotations
from typing import Dict
from apps.api.services.intelligence.linked_system import LinkedChartGraph, LinkedSystemBuilder
from apps.api.services.intelligence.cognitive_reasoner import CognitiveReasoner, DashaPeriod5Level, CognitivePredictionResult


class HealthPredictor:
    """
    Cognitive predictive engine for health crises and illness vulnerability.
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
            event_type="health",
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
