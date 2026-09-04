"""
AstroOS — Research Decision & Evidence Action Router (Priority 25)

Endpoints for evaluating research action decisions, inspecting contributing factors,
and reviewing recommended scientific next-step policies.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.schemas.decision_action import (
    ActionableResearchDecisionResponse,
    DecisionEvaluateRequest,
)
from apps.api.services.decision_action_engine import ResearchDecisionActionEngine

router = APIRouter(
    prefix="/api/v1/research/decision-action",
    tags=["Research Decision Action"],
    dependencies=[Depends(require_authenticated)],
)


@router.post("/evaluate", response_model=ActionableResearchDecisionResponse)
def evaluate_research_action_decision(request: DecisionEvaluateRequest):
    """
    Evaluate empirical research readiness and generate an actionable research decision verdict.
    """
    decision = ResearchDecisionActionEngine.get_instance().evaluate_research_action_decision(
        target_objective=request.target_objective,
        snapshot_id=request.snapshot_id,
    )

    return ActionableResearchDecisionResponse(
        decision_id=decision.decision_id,
        target_objective=decision.target_objective,
        verdict=decision.verdict.value,
        readiness_level=decision.readiness_level.value,
        synthesized_confidence_score=decision.synthesized_confidence_score,
        empirical_readiness_score_percent=decision.empirical_readiness_score_percent,
        decision_factors=[
            {
                "factor_id": f.factor_id,
                "factor_name": f.factor_name,
                "source_priority": f.source_priority,
                "measured_metric": f.measured_metric,
                "raw_score": f.raw_score,
                "weight": f.weight,
                "is_criterion_satisfied": f.is_criterion_satisfied,
                "epistemic_rationale": f.epistemic_rationale,
            }
            for f in decision.decision_factors
        ],
        supporting_evidence_points=list(decision.supporting_evidence_points),
        risk_and_attenuation_factors=list(decision.risk_and_attenuation_factors),
        policy_recommendation={
            "recommended_action": decision.policy_recommendation.recommended_action,
            "experiment_planning_priority": decision.policy_recommendation.experiment_planning_priority,
            "target_sample_size_expansion": decision.policy_recommendation.target_sample_size_expansion,
            "longitudinal_tracking_enabled": decision.policy_recommendation.longitudinal_tracking_enabled,
            "suggested_experiment_budget_tier": decision.policy_recommendation.suggested_experiment_budget_tier,
            "policy_summary": decision.policy_recommendation.policy_summary,
        },
        p11_lineage_snapshot_id=decision.p11_lineage_snapshot_id,
        decision_provenance_hash=decision.decision_provenance_hash,
        epistemic_non_causal_statement=decision.epistemic_non_causal_statement,
        decided_at=decision.decided_at.isoformat(),
    )


@router.get("/latest", response_model=ActionableResearchDecisionResponse)
def get_latest_decision(target_objective: str = Query("marriage")):
    """
    Get or evaluate the latest research action decision for the target objective.
    """
    decision = ResearchDecisionActionEngine.get_instance().evaluate_research_action_decision(
        target_objective=target_objective
    )

    return ActionableResearchDecisionResponse(
        decision_id=decision.decision_id,
        target_objective=decision.target_objective,
        verdict=decision.verdict.value,
        readiness_level=decision.readiness_level.value,
        synthesized_confidence_score=decision.synthesized_confidence_score,
        empirical_readiness_score_percent=decision.empirical_readiness_score_percent,
        decision_factors=[
            {
                "factor_id": f.factor_id,
                "factor_name": f.factor_name,
                "source_priority": f.source_priority,
                "measured_metric": f.measured_metric,
                "raw_score": f.raw_score,
                "weight": f.weight,
                "is_criterion_satisfied": f.is_criterion_satisfied,
                "epistemic_rationale": f.epistemic_rationale,
            }
            for f in decision.decision_factors
        ],
        supporting_evidence_points=list(decision.supporting_evidence_points),
        risk_and_attenuation_factors=list(decision.risk_and_attenuation_factors),
        policy_recommendation={
            "recommended_action": decision.policy_recommendation.recommended_action,
            "experiment_planning_priority": decision.policy_recommendation.experiment_planning_priority,
            "target_sample_size_expansion": decision.policy_recommendation.target_sample_size_expansion,
            "longitudinal_tracking_enabled": decision.policy_recommendation.longitudinal_tracking_enabled,
            "suggested_experiment_budget_tier": decision.policy_recommendation.suggested_experiment_budget_tier,
            "policy_summary": decision.policy_recommendation.policy_summary,
        },
        p11_lineage_snapshot_id=decision.p11_lineage_snapshot_id,
        decision_provenance_hash=decision.decision_provenance_hash,
        epistemic_non_causal_statement=decision.epistemic_non_causal_statement,
        decided_at=decision.decided_at.isoformat(),
    )
