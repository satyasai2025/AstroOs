"""
AstroOS — Adaptive Research & Sequential Experiment Router (Priority 28)

Endpoints for:
  - Freezing immutable pre-trial commitments with explicit alpha spending methods.
  - Executing sequential interim analysis with stopping boundaries and blinded sample-size re-estimation.
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import require_authenticated
from apps.api.domain.adaptive_research import AlphaSpendingMethod
from apps.api.schemas.adaptive_research import (
    AdaptiveExperimentReportResponse,
    CreateCommitmentRequest,
    EvaluateInterimRequest,
    ImmutableTrialCommitmentSchema,
)
from apps.api.services.adaptive_research_engine import AdaptiveResearchEngine

router = APIRouter(
    prefix="/api/v1/research/adaptive-experiment",
    tags=["Research Adaptive Experiments"],
    dependencies=[Depends(require_authenticated)],
)


@router.post("/commit", response_model=ImmutableTrialCommitmentSchema)
def create_immutable_trial_commitment(request: CreateCommitmentRequest):
    """
    Freeze hypothesis formula, parameter space, alpha spending function, and predefined strata.
    """
    spending_enum = AlphaSpendingMethod(request.alpha_spending_method)
    commit = AdaptiveResearchEngine.get_instance().create_immutable_trial_commitment(
        target_objective=request.target_objective,
        hypothesis_id=request.hypothesis_id,
        alpha_spending_method=spending_enum,
        overall_alpha_budget=request.overall_alpha_budget,
        overall_beta_budget=request.overall_beta_budget,
        planned_maximum_sample_size=request.planned_maximum_sample_size,
        permit_outcome_dependent_adaptation=request.permit_outcome_dependent_adaptation,
        snapshot_id=request.snapshot_id,
    )

    return ImmutableTrialCommitmentSchema(
        commitment_id=commit.commitment_id,
        target_objective=commit.target_objective,
        candidate_hypothesis_id=commit.candidate_hypothesis_id,
        frozen_rule_name=commit.frozen_rule_name,
        frozen_formula_expression=commit.frozen_formula_expression,
        frozen_parameter_thresholds=commit.frozen_parameter_thresholds,
        alpha_spending_method=commit.alpha_spending_method.value,
        overall_alpha_budget=commit.overall_alpha_budget,
        overall_beta_budget=commit.overall_beta_budget,
        planned_maximum_sample_size=commit.planned_maximum_sample_size,
        permit_outcome_dependent_adaptation=commit.permit_outcome_dependent_adaptation,
        predefined_strata=[
            {
                "stratum_id": s.stratum_id,
                "stratum_name": s.stratum_name,
                "feature_dimension": s.feature_dimension,
                "inclusion_criteria": s.inclusion_criteria,
                "target_sample_allocation_pct": s.target_sample_allocation_pct,
                "observed_sample_count": s.observed_sample_count,
            }
            for s in commit.predefined_strata
        ],
        p11_lineage_snapshot_id=commit.p11_lineage_snapshot_id,
        commitment_provenance_hash=commit.commitment_provenance_hash,
        committed_at=commit.committed_at.isoformat(),
    )


@router.post("/interim-evaluate", response_model=AdaptiveExperimentReportResponse)
def evaluate_sequential_interim(request: EvaluateInterimRequest):
    """
    Execute sequential interim look against alpha spending stopping boundaries.
    """
    rep = AdaptiveResearchEngine.get_instance().evaluate_sequential_interim(
        commitment_id=request.commitment_id,
        target_objective=request.target_objective,
        interim_look_number=request.interim_look_number,
        total_planned_looks=request.total_planned_looks,
        current_sample_size=request.current_sample_size,
        snapshot_id=request.snapshot_id,
    )

    return AdaptiveExperimentReportResponse(
        adaptive_trial_id=rep.adaptive_trial_id,
        target_objective=rep.target_objective,
        trial_phase=rep.trial_phase.value,
        commitment=ImmutableTrialCommitmentSchema(
            commitment_id=rep.commitment.commitment_id,
            target_objective=rep.commitment.target_objective,
            candidate_hypothesis_id=rep.commitment.candidate_hypothesis_id,
            frozen_rule_name=rep.commitment.frozen_rule_name,
            frozen_formula_expression=rep.commitment.frozen_formula_expression,
            frozen_parameter_thresholds=rep.commitment.frozen_parameter_thresholds,
            alpha_spending_method=rep.commitment.alpha_spending_method.value,
            overall_alpha_budget=rep.commitment.overall_alpha_budget,
            overall_beta_budget=rep.commitment.overall_beta_budget,
            planned_maximum_sample_size=rep.commitment.planned_maximum_sample_size,
            permit_outcome_dependent_adaptation=rep.commitment.permit_outcome_dependent_adaptation,
            predefined_strata=[
                {
                    "stratum_id": s.stratum_id,
                    "stratum_name": s.stratum_name,
                    "feature_dimension": s.feature_dimension,
                    "inclusion_criteria": s.inclusion_criteria,
                    "target_sample_allocation_pct": s.target_sample_allocation_pct,
                    "observed_sample_count": s.observed_sample_count,
                }
                for s in rep.commitment.predefined_strata
            ],
            p11_lineage_snapshot_id=rep.commitment.p11_lineage_snapshot_id,
            commitment_provenance_hash=rep.commitment.commitment_provenance_hash,
            committed_at=rep.commitment.committed_at.isoformat(),
        ),
        latest_interim_analysis={
            "interim_look_number": rep.latest_interim_analysis.interim_look_number,
            "total_planned_looks": rep.latest_interim_analysis.total_planned_looks,
            "accumulated_sample_size": rep.latest_interim_analysis.accumulated_sample_size,
            "information_fraction_t": rep.latest_interim_analysis.information_fraction_t,
            "cumulative_alpha_spent": rep.latest_interim_analysis.cumulative_alpha_spent,
            "efficacy_boundary_z": rep.latest_interim_analysis.efficacy_boundary_z,
            "futility_boundary_z": rep.latest_interim_analysis.futility_boundary_z,
            "observed_interim_z_score": rep.latest_interim_analysis.observed_interim_z_score,
            "interim_decision": rep.latest_interim_analysis.interim_decision.value,
            "is_information_blind": rep.latest_interim_analysis.is_information_blind,
            "reestimated_sample_size": rep.latest_interim_analysis.reestimated_sample_size,
            "interim_rationale": rep.latest_interim_analysis.interim_rationale,
            "analyzed_at": rep.latest_interim_analysis.analyzed_at.isoformat(),
        },
        interim_history=[
            {
                "interim_look_number": a.interim_look_number,
                "total_planned_looks": a.total_planned_looks,
                "accumulated_sample_size": a.accumulated_sample_size,
                "information_fraction_t": a.information_fraction_t,
                "cumulative_alpha_spent": a.cumulative_alpha_spent,
                "efficacy_boundary_z": a.efficacy_boundary_z,
                "futility_boundary_z": a.futility_boundary_z,
                "observed_interim_z_score": a.observed_interim_z_score,
                "interim_decision": a.interim_decision.value,
                "is_information_blind": a.is_information_blind,
                "reestimated_sample_size": a.reestimated_sample_size,
                "interim_rationale": a.interim_rationale,
                "analyzed_at": a.analyzed_at.isoformat(),
            }
            for a in rep.interim_history
        ],
        predefined_strata=[
            {
                "stratum_id": s.stratum_id,
                "stratum_name": s.stratum_name,
                "feature_dimension": s.feature_dimension,
                "inclusion_criteria": s.inclusion_criteria,
                "target_sample_allocation_pct": s.target_sample_allocation_pct,
                "observed_sample_count": s.observed_sample_count,
            }
            for s in rep.predefined_strata
        ],
        p11_snapshot_id=rep.p11_snapshot_id,
        report_provenance_hash=rep.report_provenance_hash,
        epistemic_non_causal_statement=rep.epistemic_non_causal_statement,
        generated_at=rep.generated_at.isoformat(),
    )


@router.get("/latest", response_model=AdaptiveExperimentReportResponse)
def get_latest_adaptive_trial_report(target_objective: str = Query("marriage")):
    """
    Get or execute the latest adaptive sequential trial report for the target objective.
    """
    rep = AdaptiveResearchEngine.get_instance().evaluate_sequential_interim(
        target_objective=target_objective
    )

    return evaluate_sequential_interim(
        EvaluateInterimRequest(
            target_objective=target_objective,
            interim_look_number=rep.latest_interim_analysis.interim_look_number,
            total_planned_looks=rep.latest_interim_analysis.total_planned_looks,
            current_sample_size=rep.latest_interim_analysis.accumulated_sample_size,
            snapshot_id=rep.p11_snapshot_id,
        )
    )
