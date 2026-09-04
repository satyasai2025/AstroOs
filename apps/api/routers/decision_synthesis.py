"""
AstroOS — Research Decision & Evidence Synthesis Router (Priority 23)

Endpoints:
  - POST /api/v1/research/decision-synthesis/synthesize
  - GET  /api/v1/research/decision-synthesis/conclusions
  - GET  /api/v1/research/decision-synthesis/conclusions/{conclusion_id}
"""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.schemas.decision_synthesis import (
    EvidenceConflictResponse,
    ResearchDecisionConclusionResponse,
    SynthesizeDecisionRequest,
    TechniqueStrengthResponse,
)
from apps.api.services.decision_synthesis_engine import ResearchDecisionSynthesisEngine

router = APIRouter(prefix="/research/decision-synthesis", tags=["Research: Decision & Evidence Synthesis"])


def _map_conclusion(c) -> ResearchDecisionConclusionResponse:
    return ResearchDecisionConclusionResponse(
        conclusion_id=c.conclusion_id,
        target_objective=c.target_objective,
        synthesized_confidence_score=c.synthesized_confidence_score,
        confidence_tier=c.confidence_tier.value if hasattr(c.confidence_tier, "value") else str(c.confidence_tier),
        strongest_techniques=[
            TechniqueStrengthResponse(
                technique_name=t.technique_name,
                epistemic_type=t.epistemic_type.value if hasattr(t.epistemic_type, "value") else str(t.epistemic_type),
                evidence_grade=t.evidence_grade,
                holdout_replicated=t.holdout_replicated,
                prospective_supported=t.prospective_supported,
                empirical_lift=t.empirical_lift,
                brier_score=t.brier_score,
                usable_for_prediction=t.usable_for_prediction,
                arbitration_note=t.arbitration_note,
            )
            for t in c.strongest_techniques
        ],
        replicated_hypotheses_count=c.replicated_hypotheses_count,
        prospective_lifecycle_summary=c.prospective_lifecycle_summary,
        conflicts_detected=[
            EvidenceConflictResponse(
                conflict_id=cf.conflict_id,
                technique_a=cf.technique_a,
                technique_b=cf.technique_b,
                conflict_type=cf.conflict_type,
                conflict_description=cf.conflict_description,
                resolution_recommendation=cf.resolution_recommendation,
                epistemic_arbitration=cf.epistemic_arbitration,
            )
            for cf in c.conflicts_detected
        ],
        recommended_prediction_factors=c.recommended_prediction_factors,
        counterfactual_stability_rating=c.counterfactual_stability_rating,
        p1_to_p22_lineage_trace=c.p1_to_p22_lineage_trace,
        defensible_scientific_summary=c.defensible_scientific_summary,
        synthesized_at=c.synthesized_at,
    )


@router.post("/synthesize", response_model=ResearchDecisionConclusionResponse, status_code=status.HTTP_200_OK)
def synthesize_decision(req: SynthesizeDecisionRequest) -> ResearchDecisionConclusionResponse:
    """Synthesizes P1 through P22 evidence layers into an empirical, defensible research decision conclusion."""
    engine = ResearchDecisionSynthesisEngine.get_instance()
    conclusion = engine.synthesize_research_decision(
        target_objective=req.target_objective,
        include_lineage=req.include_lineage,
    )
    return _map_conclusion(conclusion)


@router.get("/conclusions", response_model=List[ResearchDecisionConclusionResponse], status_code=status.HTTP_200_OK)
def list_conclusions() -> List[ResearchDecisionConclusionResponse]:
    """Lists all synthesized research decision conclusions."""
    engine = ResearchDecisionSynthesisEngine.get_instance()
    return [_map_conclusion(c) for c in engine.list_conclusions()]


@router.get("/conclusions/{conclusion_id}", response_model=ResearchDecisionConclusionResponse, status_code=status.HTTP_200_OK)
def get_conclusion(conclusion_id: str) -> ResearchDecisionConclusionResponse:
    """Retrieves full details for a specific research decision conclusion."""
    engine = ResearchDecisionSynthesisEngine.get_instance()
    conclusion = engine.get_conclusion(conclusion_id)
    if not conclusion:
        raise HTTPException(status_code=404, detail=f"Conclusion '{conclusion_id}' not found.")
    return _map_conclusion(conclusion)
