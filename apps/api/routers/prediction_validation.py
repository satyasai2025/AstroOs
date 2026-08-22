"""
AstroOS — Prediction Validation & Backtesting API Router (Module 22, Priority 7)
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, status

from apps.api.domain.prediction_validation import PredictionCategory, TemporalSplitType
from apps.api.schemas.prediction_validation import (
    BacktestRequest,
    BacktestRunResponse,
    ConfusionMatrixResponse,
    MatchRequest,
    MatchResponse,
    OutcomeCreateRequest,
    OutcomeItemResponse,
    PredictionCreateRequest,
    PredictionItemResponse,
    TechniqueSummaryItem,
)
from apps.api.services.prediction_validation_service import PredictionValidationService

router = APIRouter(prefix="/prediction-validation", tags=["Prediction Validation & Backtesting"])


def get_service() -> PredictionValidationService:
    return PredictionValidationService()


@router.post("/predictions", response_model=PredictionItemResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(body: PredictionCreateRequest):
    service = get_service()
    pred = service.create_prediction(
        prediction_id=body.prediction_id,
        chart_id=body.chart_id,
        subject_name=body.subject_name,
        technique=body.technique,
        category=body.category,
        predicted_event=body.predicted_event,
        expected_direction=body.expected_direction,
        prediction_timestamp=body.prediction_timestamp,
        horizon_days=body.horizon_days,
        expected_date_start=body.expected_date_start,
        expected_date_end=body.expected_date_end,
        evidence_ids=body.evidence_ids,
        dasha_evidence=body.dasha_evidence,
        transit_evidence=body.transit_evidence,
        kp_evidence=body.kp_evidence,
        sbc_evidence=body.sbc_evidence,
        classical_rule_evidence=body.classical_rule_evidence,
        varga_evidence=body.varga_evidence,
        ashtakavarga_evidence=body.ashtakavarga_evidence,
        calculation_snapshot=body.calculation_snapshot,
    )
    return PredictionItemResponse(
        prediction_id=pred.prediction_id,
        chart_id=pred.chart_id,
        subject_name=pred.subject_name,
        technique=pred.technique,
        category=pred.category,
        predicted_event=pred.predicted_event,
        expected_direction=pred.expected_direction,
        prediction_timestamp=pred.prediction_timestamp,
        horizon_days=pred.horizon_days,
        expected_date_start=pred.expected_date_start,
        expected_date_end=pred.expected_date_end,
        evidence_ids=pred.evidence_ids,
        evidence_hash=pred.evidence_hash,
        engine_version=pred.engine_version,
    )


@router.get("/predictions", response_model=list[PredictionItemResponse])
def list_predictions(
    technique: Optional[str] = Query(default=None),
    category: Optional[PredictionCategory] = Query(default=None),
):
    service = get_service()
    preds = service.list_predictions(technique=technique, category=category)
    return [
        PredictionItemResponse(
            prediction_id=p.prediction_id,
            chart_id=p.chart_id,
            subject_name=p.subject_name,
            technique=p.technique,
            category=p.category,
            predicted_event=p.predicted_event,
            expected_direction=p.expected_direction,
            prediction_timestamp=p.prediction_timestamp,
            horizon_days=p.horizon_days,
            expected_date_start=p.expected_date_start,
            expected_date_end=p.expected_date_end,
            evidence_ids=p.evidence_ids,
            evidence_hash=p.evidence_hash,
            engine_version=p.engine_version,
        )
        for p in preds
    ]


@router.get("/predictions/{prediction_id}", response_model=PredictionItemResponse)
def get_prediction(prediction_id: str):
    service = get_service()
    pred = service.get_prediction(prediction_id)
    if not pred:
        raise HTTPException(status_code=404, detail=f"Prediction '{prediction_id}' not found.")
    return PredictionItemResponse(
        prediction_id=pred.prediction_id,
        chart_id=pred.chart_id,
        subject_name=pred.subject_name,
        technique=pred.technique,
        category=pred.category,
        predicted_event=pred.predicted_event,
        expected_direction=pred.expected_direction,
        prediction_timestamp=pred.prediction_timestamp,
        horizon_days=pred.horizon_days,
        expected_date_start=pred.expected_date_start,
        expected_date_end=pred.expected_date_end,
        evidence_ids=pred.evidence_ids,
        evidence_hash=pred.evidence_hash,
        engine_version=pred.engine_version,
    )


@router.post("/outcomes", response_model=OutcomeItemResponse, status_code=status.HTTP_201_CREATED)
def register_outcome(body: OutcomeCreateRequest):
    service = get_service()
    out = service.register_outcome(
        outcome_id=body.outcome_id,
        chart_id=body.chart_id,
        subject_name=body.subject_name,
        category=body.category,
        observed_date=body.observed_date,
        actual_outcome_description=body.actual_outcome_description,
        observed_direction=body.observed_direction,
        verification_status=body.verification_status,
        source_reference=body.source_reference,
        notes=body.notes,
    )
    return OutcomeItemResponse(
        outcome_id=out.outcome_id,
        chart_id=out.chart_id,
        subject_name=out.subject_name,
        category=out.category,
        observed_date=out.observed_date,
        actual_outcome_description=out.actual_outcome_description,
        observed_direction=out.observed_direction,
        verification_status=out.verification_status,
        source_reference=out.source_reference,
        notes=out.notes,
        outcome_hash=out.outcome_hash,
    )


@router.get("/outcomes", response_model=list[OutcomeItemResponse])
def list_outcomes(category: Optional[PredictionCategory] = Query(default=None)):
    service = get_service()
    outs = service.list_outcomes(category=category)
    return [
        OutcomeItemResponse(
            outcome_id=o.outcome_id,
            chart_id=o.chart_id,
            subject_name=o.subject_name,
            category=o.category,
            observed_date=o.observed_date,
            actual_outcome_description=o.actual_outcome_description,
            observed_direction=o.observed_direction,
            verification_status=o.verification_status,
            source_reference=o.source_reference,
            notes=o.notes,
            outcome_hash=o.outcome_hash,
        )
        for o in outs
    ]


@router.post("/match", response_model=MatchResponse)
def evaluate_match(body: MatchRequest):
    service = get_service()
    try:
        res = service.evaluate_match(prediction_id=body.prediction_id, outcome_id=body.outcome_id)
        return MatchResponse(
            match_id=res.match_id,
            prediction_id=res.prediction_id,
            outcome_id=res.outcome_id,
            verdict=res.verdict,
            category_matched=res.category_matched,
            temporal_error_days=res.temporal_error_days,
            direction_matched=res.direction_matched,
            predicate_traces=res.predicate_traces,
            evidence_provenance_ids=res.evidence_provenance_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/backtest", response_model=BacktestRunResponse)
def run_backtest(body: BacktestRequest):
    service = get_service()
    run = service.run_backtest(
        dataset_name=body.dataset_name,
        technique_filter=body.technique_filter,
        category_filter=body.category_filter,
        temporal_split=body.temporal_split,
    )
    return BacktestRunResponse(
        backtest_id=run.backtest_id,
        dataset_name=run.dataset_name,
        technique_filter=run.technique_filter,
        category_filter=run.category_filter,
        temporal_split=run.temporal_split,
        total_predictions=run.total_predictions,
        resolved_predictions=run.resolved_predictions,
        unresolved_predictions=run.unresolved_predictions,
        matched_count=run.matched_count,
        partial_count=run.partial_count,
        missed_count=run.missed_count,
        contradicted_count=run.contradicted_count,
        inconclusive_count=run.inconclusive_count,
        hit_rate=run.hit_rate,
        confusion_matrix=ConfusionMatrixResponse(
            true_positive=run.confusion_matrix.true_positive,
            false_positive=run.confusion_matrix.false_positive,
            true_negative=run.confusion_matrix.true_negative,
            false_negative=run.confusion_matrix.false_negative,
            total=run.confusion_matrix.total,
            precision=run.confusion_matrix.precision,
            recall=run.confusion_matrix.recall,
            f1_score=run.confusion_matrix.f1_score,
        ),
        confidence_interval_95=list(run.confidence_interval_95),
        temporal_leakage_detected=run.temporal_leakage_detected,
        leakage_reasons=run.leakage_reasons,
        result_hash=run.result_hash,
        evaluations=[
            MatchResponse(
                match_id=e.match_id,
                prediction_id=e.prediction_id,
                outcome_id=e.outcome_id,
                verdict=e.verdict,
                category_matched=e.category_matched,
                temporal_error_days=e.temporal_error_days,
                direction_matched=e.direction_matched,
                predicate_traces=e.predicate_traces,
                evidence_provenance_ids=e.evidence_provenance_ids,
            )
            for e in run.evaluations
        ],
    )


@router.get("/backtest/{backtest_id}", response_model=BacktestRunResponse)
def get_backtest(backtest_id: str):
    service = get_service()
    run = service.get_backtest_run(backtest_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Backtest run '{backtest_id}' not found.")
    return BacktestRunResponse(
        backtest_id=run.backtest_id,
        dataset_name=run.dataset_name,
        technique_filter=run.technique_filter,
        category_filter=run.category_filter,
        temporal_split=run.temporal_split,
        total_predictions=run.total_predictions,
        resolved_predictions=run.resolved_predictions,
        unresolved_predictions=run.unresolved_predictions,
        matched_count=run.matched_count,
        partial_count=run.partial_count,
        missed_count=run.missed_count,
        contradicted_count=run.contradicted_count,
        inconclusive_count=run.inconclusive_count,
        hit_rate=run.hit_rate,
        confusion_matrix=ConfusionMatrixResponse(
            true_positive=run.confusion_matrix.true_positive,
            false_positive=run.confusion_matrix.false_positive,
            true_negative=run.confusion_matrix.true_negative,
            false_negative=run.confusion_matrix.false_negative,
            total=run.confusion_matrix.total,
            precision=run.confusion_matrix.precision,
            recall=run.confusion_matrix.recall,
            f1_score=run.confusion_matrix.f1_score,
        ),
        confidence_interval_95=list(run.confidence_interval_95),
        temporal_leakage_detected=run.temporal_leakage_detected,
        leakage_reasons=run.leakage_reasons,
        result_hash=run.result_hash,
        evaluations=[
            MatchResponse(
                match_id=e.match_id,
                prediction_id=e.prediction_id,
                outcome_id=e.outcome_id,
                verdict=e.verdict,
                category_matched=e.category_matched,
                temporal_error_days=e.temporal_error_days,
                direction_matched=e.direction_matched,
                predicate_traces=e.predicate_traces,
                evidence_provenance_ids=e.evidence_provenance_ids,
            )
            for e in run.evaluations
        ],
    )


@router.get("/techniques", response_model=list[TechniqueSummaryItem])
def list_techniques():
    service = get_service()
    return [TechniqueSummaryItem(**item) for item in service.list_techniques_summary()]


@router.get("/audit/{prediction_id}")
def get_prediction_audit_trail(prediction_id: str):
    service = get_service()
    try:
        return service.get_prediction_audit_trail(prediction_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
