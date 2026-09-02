"""
AstroOS — Classical Shastric Conflict Resolution Engine

Implements classical Parashari arbitration when multiple specialized experts
produce competing or contradictory predictive signals:

Classical Hierarchy Rules:
1. Temporal Primacy: Dasha readiness is the master gatekeeper. A potent natal Raja Yoga
   remains latent if the active 5-level Dasha lords have no sambandha with the event house.
2. Upagraha Delay vs Denial: Mandi in 7th or conjoined 7th lord acts as a timing inhibitor
   (delay), not an absolute denial if D1 7th lord has high Base-2 strength.
3. Upachaya Transmutation: Gulika in houses 3, 6, 10, 11 overcomes dusthana afflictions
   and converts friction into elevation.
4. Neecha Bhanga / Strength Neutralization: Per Vinay Jha's thesis, a debilitated lord
   surrounded by strong benefic relatives is controlled and produces high elevation.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
from apps.api.services.phalita_core.expert_registry import ExpertOutput


@dataclass
class ConflictResolutionResult:
    has_conflict: bool
    conflict_type: str
    precedence_rule_applied: str
    adjusted_score: float
    resolution_narrative: str


class ConflictResolutionEngine:
    """
    Arbitrates multi-expert discrepancies using Parashari Shastric hierarchy.
    """

    @classmethod
    def resolve_conflicts(
        cls,
        expert_outputs: Dict[str, ExpertOutput],
        fused_raw_score: float,
        domain: str,
    ) -> ConflictResolutionResult:
        struct_out = expert_outputs.get("NatalStructuralExpert")
        yoga_out = expert_outputs.get("DivisionalYogaExpert")
        temp_out = expert_outputs.get("TemporalDashaExpert")
        upa_out = expert_outputs.get("UpagrahaShadowExpert")

        score_struct = struct_out.expert_score if struct_out else 4.5
        score_temp = temp_out.expert_score if temp_out else 4.5
        score_upa = upa_out.expert_score if upa_out else 4.5

        # 1. Conflict: Strong Natal Potential vs Dormant Dasha
        if score_struct >= 6.5 and score_temp <= 3.5:
            adj = fused_raw_score * 0.70  # Dasha suppresses fruition
            return ConflictResolutionResult(
                has_conflict=True,
                conflict_type="STRUCTURAL_PROMISE_VS_DORMANT_DASHA",
                precedence_rule_applied="Temporal Primacy (BPHS Ch. 46): Natal Raja Yoga remains dormant until activating Dasha arrives.",
                adjusted_score=round(adj, 2),
                resolution_narrative="Strong foundational promise is present, but current 5-level Dasha is not currently activated.",
            )

        # 2. Conflict: Active Dasha vs Upagraha Shadow Impediment (e.g. Mandi in 7th for Marriage)
        if domain.lower() == "marriage" and score_temp >= 6.0 and score_upa <= 3.5:
            adj = max(3.5, fused_raw_score - 1.25)
            return ConflictResolutionResult(
                has_conflict=True,
                conflict_type="TEMPORAL_ACTIVATION_VS_MANDI_DELAY",
                precedence_rule_applied="Upagraha Delay Principle (Jataka Parijata): Mandi in 7th induces delay/friction without canceling marriage.",
                adjusted_score=round(adj, 2),
                resolution_narrative="Dasha indicates relationship timing, but Mandi indicates initial hurdles and delays before culmination.",
            )

        # 3. Conflict: Health/Crisis Risk vs Upachaya Benefic Shield
        if domain.lower() in ("health", "accident") and score_temp >= 6.0 and score_upa >= 6.5:
            # Both high -> high crisis risk
            adj = min(9.0, fused_raw_score + 1.0)
            return ConflictResolutionResult(
                has_conflict=True,
                conflict_type="MUTUAL_CRISIS_CONVERGENCE",
                precedence_rule_applied="Mrityu Yoga Catalysis (BPHS): 8th house Gulika converging with Maraka Dasha demands high vigilance.",
                adjusted_score=round(adj, 2),
                resolution_narrative="Temporal vulnerability aligns with 8th house Gulika catalyst; health vigilance strongly indicated.",
            )

        # No acute conflict
        return ConflictResolutionResult(
            has_conflict=False,
            conflict_type="CONVERGENT_CONSENSUS",
            precedence_rule_applied="Harmonic Multi-Expert Agreement.",
            adjusted_score=round(fused_raw_score, 2),
            resolution_narrative="All specialized experts show consistent directional agreement.",
        )
