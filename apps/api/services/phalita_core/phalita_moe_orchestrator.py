"""
AstroOS — Phalita Mixture of Experts (MoE) Master Orchestrator

The Central Brain of AstroOS Predictive Intelligence:
1. Coordinates the 4 Specialized Shastric Experts from ExpertRegistry.
2. Applies Dynamic Gating Routing via ExpertRouter.
3. Computes the Evidence Fusion Matrix.
4. Arbitrates discrepancies through ConflictResolutionEngine.
5. Emits a definitive, calibrated PhalitaMoEConsultationVerdict with complete
   diagnostic explainability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from apps.api.services.intelligence.linked_system import LinkedChartGraph
from apps.api.services.intelligence.cognitive_reasoner import DashaPeriod5Level
from apps.api.services.phalita_core.expert_registry import (
    ExpertOutput,
    NatalStructuralExpert,
    DivisionalYogaExpert,
    TemporalDashaExpert,
    UpagrahaShadowExpert,
)
from apps.api.services.phalita_core.expert_router import ExpertRouter, GatingWeights
from apps.api.services.phalita_core.conflict_resolution import (
    ConflictResolutionEngine,
    ConflictResolutionResult,
)


@dataclass
class PhalitaMoEConsultationVerdict:
    domain: str
    final_cognitive_score: float     # 0.0 to 9.0 Cognitive Score
    is_probable: bool                # True if final score >= 5.0
    gating_weights: Dict[str, float]
    expert_breakdown: Dict[str, ExpertOutput]
    conflict_resolution: ConflictResolutionResult
    consensus_summary: str
    actionable_recommendation: str
    rule_traces: List[str] = field(default_factory=list)


class PhalitaMoEOrchestrator:
    """
    Master Orchestration Engine for Multi-Expert Astrological Synthesis.
    """

    @classmethod
    def synthesize(
        cls,
        graph: LinkedChartGraph,
        dasha: DashaPeriod5Level,
        domain: str = "general",
    ) -> PhalitaMoEConsultationVerdict:
        """
        Executes full multi-expert synthesis pipeline.
        """
        domain_clean = domain.lower()

        # 1. Evaluate all 4 Specialized Shastric Experts
        out_struct = NatalStructuralExpert.evaluate(graph, domain_clean)
        out_div = DivisionalYogaExpert.evaluate(graph, domain_clean)
        out_temp = TemporalDashaExpert.evaluate(graph, dasha, domain_clean)
        out_upa = UpagrahaShadowExpert.evaluate(graph, domain_clean)

        experts_map: Dict[str, ExpertOutput] = {
            out_struct.expert_name: out_struct,
            out_div.expert_name: out_div,
            out_temp.expert_name: out_temp,
            out_upa.expert_name: out_upa,
        }

        # 2. Compute Attention / Gating Weights
        weights: GatingWeights = ExpertRouter.route(domain_clean)

        # 3. Evidence Fusion Matrix
        fused_raw_score = (
            weights.structural * out_struct.expert_score
            + weights.divisional * out_div.expert_score
            + weights.temporal * out_temp.expert_score
            + weights.upagraha * out_upa.expert_score
        )

        # 4. Conflict Resolution & Precedence Arbitration
        conflict_res: ConflictResolutionResult = ConflictResolutionEngine.resolve_conflicts(
            expert_outputs=experts_map,
            fused_raw_score=fused_raw_score,
            domain=domain_clean,
        )

        final_score = max(0.0, min(9.0, conflict_res.adjusted_score))
        final_score = round(final_score, 2)
        is_probable = final_score >= 5.0

        # 5. Compile Rule Traces & Explainability Narrative
        rule_traces: List[str] = []
        for name, exp in experts_map.items():
            for f in exp.key_findings:
                rule_traces.append(f"[{name}] {f}")

        rule_traces.append(f"[ROUTER] Gating Weights: {weights.to_dict()}")
        rule_traces.append(f"[CONFLICT_RESOLUTION] {conflict_res.precedence_rule_applied}")

        consensus_summary = (
            f"Phalita MoE Verdict for {domain.upper()}: 0 to 9 Cognitive Score = {final_score}/9.0. "
            f"Gating primary: Temporal ({weights.temporal*100:.1f}%), Upagraha ({weights.upagraha*100:.1f}%). "
            f"{conflict_res.resolution_narrative}"
        )

        recommendation = (
            f"Event potential is HIGH (Score {final_score}/9.0)."
            if is_probable
            else f"Event potential is MODERATE/LOW (Score {final_score}/9.0); patience advised."
        )

        return PhalitaMoEConsultationVerdict(
            domain=domain_clean,
            final_cognitive_score=final_score,
            is_probable=is_probable,
            gating_weights=weights.to_dict(),
            expert_breakdown=experts_map,
            conflict_resolution=conflict_res,
            consensus_summary=consensus_summary,
            actionable_recommendation=recommendation,
            rule_traces=rule_traces,
        )
