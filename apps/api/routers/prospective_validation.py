"""
AstroOS — Prospective Research Validation & Rule Lifecycle Router (Priority 20)

Endpoints:
  - POST /api/v1/research/prospective/pre-register
  - POST /api/v1/research/prospective/log-prediction
  - POST /api/v1/research/prospective/record-outcome
  - POST /api/v1/research/prospective/evaluate
  - GET  /api/v1/research/prospective/registrations
  - GET  /api/v1/research/prospective/evaluations/{evaluation_id}
"""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.schemas.prospective_validation import (
    DriftAnalysisResponse,
    EvaluateProspectiveCohortRequest,
    LogBlindPredictionRequest,
    PreRegisterHypothesisRequest,
    PreRegistrationRecordResponse,
    ProspectiveEvaluationReportResponse,
    ProspectiveSubjectPredictionResponse,
    RecordProspectiveOutcomeRequest,
)
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine

router = APIRouter(prefix="/research/prospective", tags=["Research: Prospective Validation & Rule Lifecycle"])


def _map_registration(r) -> PreRegistrationRecordResponse:
    return PreRegistrationRecordResponse(
        registration_id=r.registration_id,
        hypothesis_id=r.hypothesis_id,
        rule_name=r.rule_name,
        target_objective=r.target_objective,
        frozen_formula=r.frozen_formula,
        frozen_thresholds=r.frozen_thresholds,
        sha256_registration_hash=r.sha256_registration_hash,
        registered_at=r.registered_at,
        lineage_snapshot_id=r.lineage_snapshot_id,
        author=r.author,
    )


def _map_prediction(p) -> ProspectiveSubjectPredictionResponse:
    return ProspectiveSubjectPredictionResponse(
        prediction_id=p.prediction_id,
        registration_id=p.registration_id,
        subject_id=p.subject_id,
        predicted_probability=p.predicted_probability,
        prediction_window_start=p.prediction_window_start,
        prediction_window_end=p.prediction_window_end,
        predicted_at=p.predicted_at,
        actual_outcome=p.actual_outcome,
        outcome_recorded_at=p.outcome_recorded_at,
    )


def _map_report(rep) -> ProspectiveEvaluationReportResponse:
    return ProspectiveEvaluationReportResponse(
        evaluation_id=rep.evaluation_id,
        registration_id=rep.registration_id,
        target_objective=rep.target_objective,
        total_prospective_subjects=rep.total_prospective_subjects,
        positive_outcomes_count=rep.positive_outcomes_count,
        brier_score=rep.brier_score,
        log_loss=rep.log_loss,
        roc_auc=rep.roc_auc,
        pr_auc=rep.pr_auc,
        precision=rep.precision,
        recall=rep.recall,
        statistical_lift=rep.statistical_lift,
        confidence_interval_95_roc=list(rep.confidence_interval_95_roc),
        drift_analysis=DriftAnalysisResponse(
            psi_drift_score=rep.drift_analysis.psi_drift_score,
            is_significant_drift=rep.drift_analysis.is_significant_drift,
            drift_diagnosis=rep.drift_analysis.drift_diagnosis,
        ),
        final_lifecycle_status=rep.final_lifecycle_status.value if hasattr(rep.final_lifecycle_status, "value") else str(rep.final_lifecycle_status),
        epistemic_classification=rep.epistemic_classification,
        evaluated_at=rep.evaluated_at,
    )


@router.post("/pre-register", response_model=PreRegistrationRecordResponse, status_code=status.HTTP_200_OK)
def pre_register_hypothesis(req: PreRegisterHypothesisRequest) -> PreRegistrationRecordResponse:
    """Pre-registers and immutably freezes an astrological rule before running prospective tests."""
    engine = ProspectiveValidationEngine.get_instance()
    record = engine.pre_register_hypothesis(
        hypothesis_id=req.hypothesis_id,
        rule_name=req.rule_name,
        target_objective=req.target_objective,
        formula_expression=req.formula_expression,
        thresholds=req.thresholds,
        author=req.author,
    )
    return _map_registration(record)


@router.post("/log-prediction", response_model=ProspectiveSubjectPredictionResponse, status_code=status.HTTP_200_OK)
def log_blind_prediction(req: LogBlindPredictionRequest) -> ProspectiveSubjectPredictionResponse:
    """Logs a real forward-only blind prediction for one subject, before the outcome is known."""
    engine = ProspectiveValidationEngine.get_instance()
    try:
        record = engine.log_blind_prediction(
            registration_id=req.registration_id,
            subject_id=req.subject_id,
            predicted_probability=req.predicted_probability,
            prediction_window_start=req.prediction_window_start,
            prediction_window_end=req.prediction_window_end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _map_prediction(record)


@router.post("/record-outcome", response_model=ProspectiveSubjectPredictionResponse, status_code=status.HTTP_200_OK)
def record_prospective_outcome(req: RecordProspectiveOutcomeRequest) -> ProspectiveSubjectPredictionResponse:
    """Records the real, unblinded outcome for a previously-logged blind prediction."""
    engine = ProspectiveValidationEngine.get_instance()
    try:
        record = engine.record_subject_outcome(
            registration_id=req.registration_id,
            subject_id=req.subject_id,
            actual_outcome=req.actual_outcome,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _map_prediction(record)


@router.post("/evaluate", response_model=ProspectiveEvaluationReportResponse, status_code=status.HTTP_200_OK)
def evaluate_prospective_cohort(req: EvaluateProspectiveCohortRequest) -> ProspectiveEvaluationReportResponse:
    """Executes a blinded forward prospective evaluation against real, unblinded subject outcomes and assesses rule lifecycle."""
    engine = ProspectiveValidationEngine.get_instance()
    try:
        report = engine.evaluate_prospective_cohort(registration_id=req.registration_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _map_report(report)


@router.get("/registrations", response_model=List[PreRegistrationRecordResponse], status_code=status.HTTP_200_OK)
def list_registrations() -> List[PreRegistrationRecordResponse]:
    """Lists all active pre-registration rule snapshots."""
    engine = ProspectiveValidationEngine.get_instance()
    return [_map_registration(r) for r in engine.list_registrations()]


@router.get("/evaluations/{evaluation_id}", response_model=ProspectiveEvaluationReportResponse, status_code=status.HTTP_200_OK)
def get_evaluation_report(evaluation_id: str) -> ProspectiveEvaluationReportResponse:
    """Retrieves full empirical evaluation metrics for a specific prospective run."""
    engine = ProspectiveValidationEngine.get_instance()
    report = engine.get_evaluation_report(evaluation_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Prospective evaluation '{evaluation_id}' not found.")
    return _map_report(report)
