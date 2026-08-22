"""
AstroOS — Research & Prediction Explainability Router (Priority 17)

Endpoints:
  - POST /api/v1/research/explain/prediction
  - POST /api/v1/research/explain/counterfactual
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.explainability import (
    AtomicEvidenceFactorItem,
    CounterfactualScenarioItem,
    CounterfactualSimulationRequest,
    ExplainPredictionRequest,
    PredictionExplanationResponse,
)
from apps.api.services.explainability_engine import PredictionExplainabilityEngine

router = APIRouter(prefix="/research/explain", tags=["Research: Prediction Explainability & Reasoning Engine"])


def _map_factor(f) -> AtomicEvidenceFactorItem:
    return AtomicEvidenceFactorItem(
        factor_id=f.factor_id,
        name=f.name,
        layer=f.layer.value if hasattr(f.layer, "value") else str(f.layer),
        raw_value=f.raw_value,
        calibrated_weight=f.calibrated_weight,
        contribution_percent=f.contribution_percent,
        attribution_type=f.attribution_type,
        direction=f.direction,
        classical_citation=f.classical_citation,
        citation_verified=f.citation_verified,
        epistemic_grade=f.epistemic_grade,
        description=f.description,
    )


def _map_counterfactual(c) -> CounterfactualScenarioItem:
    return CounterfactualScenarioItem(
        scenario_id=c.scenario_id,
        perturbed_parameter=c.perturbed_parameter,
        parameter_value=c.parameter_value,
        baseline_score=c.baseline_score,
        simulated_score=c.simulated_score,
        score_delta_percent=c.score_delta_percent,
        divergence_reason=c.divergence_reason,
        recalculation_engine_used=c.recalculation_engine_used,
    )


@router.post("/prediction", response_model=PredictionExplanationResponse, status_code=status.HTTP_200_OK)
def explain_prediction(req: ExplainPredictionRequest) -> PredictionExplanationResponse:
    """Generates a complete multi-modal reasoning and explainability report with P1-P16 lineage provenance."""
    engine = PredictionExplainabilityEngine()
    explanation = engine.explain_prediction(
        target_objective=req.target_objective,
        event_window_start=req.event_window_start,
        event_window_end=req.event_window_end,
    )

    return PredictionExplanationResponse(
        explanation_id=explanation.explanation_id,
        target_objective=explanation.target_objective,
        event_window_start=explanation.event_window_start,
        event_window_end=explanation.event_window_end,
        composite_confidence_score=explanation.composite_confidence_score,
        plain_summary=explanation.plain_summary,
        classical_justification=explanation.classical_justification,
        empirical_synthesis=explanation.empirical_synthesis,
        provenance_lineage=list(explanation.provenance_lineage),
        atomic_factors=[_map_factor(f) for f in explanation.atomic_factors],
        counterfactuals=[_map_counterfactual(c) for c in explanation.counterfactuals],
        generated_at=explanation.generated_at,
    )


@router.post("/counterfactual", response_model=CounterfactualScenarioItem, status_code=status.HTTP_200_OK)
def simulate_counterfactual(req: CounterfactualSimulationRequest) -> CounterfactualScenarioItem:
    """Evaluates an interactive what-if counterfactual scenario by actual engine recalculation."""
    engine = PredictionExplainabilityEngine()
    base_explanation = engine.explain_prediction(target_objective=req.target_objective)
    scenario = engine.evaluate_counterfactual(
        base_explanation=base_explanation,
        perturbation_parameter=req.perturbed_parameter,
        perturbation_value=req.parameter_value,
    )
    return _map_counterfactual(scenario)
