"""
AstroOS — Research & Calibration API Router (v4)

Provides empirical research endpoints:
  POST /api/v1/research/split-dataset
  POST /api/v1/research/backtest
  POST /api/v1/research/calibrate
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.research_calibration import (
    BenchmarkDataset,
    BirthDataConfidence,
    CalibrationModelType,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
)
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.research_engine import ResearchEngine

router = APIRouter(prefix="/research", tags=["Research & Calibration"])


class GroundTruthEventSchema(BaseModel):
    event_id: str
    subject_id: str
    event_type: str
    actual_date: date
    birth_datetime_utc: str
    birth_latitude: float
    birth_longitude: float
    birth_confidence: str = "AA"
    event_date_confidence: str = "exact_date"
    event_verification: str = "official_document"
    source_citation: Optional[str] = ""
    notes: Optional[str] = ""


class DatasetSplitRequest(BaseModel):
    dataset_id: str
    dataset_name: str
    dataset_version: str = "1.0"
    event_type: str
    events: list[GroundTruthEventSchema]
    train_ratio: float = 0.70
    split_seed: int = 42


class DatasetSplitResponse(BaseModel):
    dataset_id: str
    dataset_version: str
    total_events: int
    train_events_count: int
    holdout_events_count: int
    split_seed: int
    split_train_ratio: float
    train_event_ids: list[str]
    holdout_event_ids: list[str]


class BacktestRequest(BaseModel):
    events: list[GroundTruthEventSchema]
    profile_id: Optional[str] = "parashari_standard_v1"
    tolerance_days: int = 30


class BacktestOutcomeSchema(BaseModel):
    event_id: str
    actual_date: str
    predicted_window_start: Optional[str]
    predicted_window_end: Optional[str]
    peak_predicted_date: Optional[str]
    deterministic_score: int
    match_status: str
    peak_offset_days: Optional[int]


class BacktestResponse(BaseModel):
    total_events: int
    exact_hits: int
    tolerance_hits: int
    misses: int
    hit_rate: float
    outcomes: list[BacktestOutcomeSchema]


class CalibrationPoolSchema(BaseModel):
    score_range: str
    sample_size_n: int
    observed_hits: int
    empirical_hit_rate_pct: float
    rate_ci_95: list[float]
    has_small_n_warning: bool


class CalibrationResponse(BaseModel):
    model_type: str
    dataset_id: str
    dataset_version: str
    profile_id: str
    calibration_sample_size_n: int
    holdout_sample_size_n: int
    holdout_brier_score: float
    holdout_hit_rate: float
    mean_peak_offset_days: float
    isotonic_pools: list[CalibrationPoolSchema]
    platt_slope_a: Optional[float] = None
    platt_intercept_b: Optional[float] = None


def _to_domain_event(e: GroundTruthEventSchema) -> GroundTruthEvent:
    return GroundTruthEvent(
        event_id=e.event_id,
        subject_id=e.subject_id,
        event_type=e.event_type,
        actual_date=e.actual_date,
        birth_datetime_utc=datetime.fromisoformat(e.birth_datetime_utc),
        birth_latitude=e.birth_latitude,
        birth_longitude=e.birth_longitude,
        birth_confidence=BirthDataConfidence(e.birth_confidence) if e.birth_confidence in BirthDataConfidence.__members__ else BirthDataConfidence.AA,
        event_date_confidence=EventDateConfidence(e.event_date_confidence) if e.event_date_confidence in EventDateConfidence.__members__ else EventDateConfidence.EXACT_DATE,
        event_verification=EventVerification(e.event_verification) if e.event_verification in EventVerification.__members__ else EventVerification.OFFICIAL_DOCUMENT,
        source_citation=e.source_citation or "",
        notes=e.notes or "",
    )


@router.post("/split-dataset", response_model=DatasetSplitResponse)
async def split_dataset(body: DatasetSplitRequest) -> DatasetSplitResponse:
    """Deterministically partitions a dataset into Train and Holdout sets."""
    domain_events = [_to_domain_event(e) for e in body.events]
    dataset = BenchmarkDataset(
        dataset_id=body.dataset_id,
        name=body.dataset_name,
        event_type=body.event_type,
        version=body.dataset_version,
        description="",
        events=tuple(domain_events),
    )

    engine = ResearchEngine()
    split = engine.split_dataset(dataset, train_ratio=body.train_ratio, seed=body.split_seed)

    return DatasetSplitResponse(
        dataset_id=split.dataset_id,
        dataset_version=split.dataset_version,
        total_events=len(body.events),
        train_events_count=len(split.train_events),
        holdout_events_count=len(split.holdout_events),
        split_seed=split.split_seed,
        split_train_ratio=split.split_train_ratio,
        train_event_ids=[e.event_id for e in split.train_events],
        holdout_event_ids=[e.event_id for e in split.holdout_events],
    )


@router.post("/backtest", response_model=BacktestResponse)
async def run_backtest(body: BacktestRequest) -> BacktestResponse:
    """Runs backtesting with window-centric temporal matching."""
    profile = (
        EMPIRICAL_RESEARCH_PROFILE
        if body.profile_id == "empirical_research_v1"
        else PARASHARI_STANDARD_PROFILE
    )

    domain_events = [_to_domain_event(e) for e in body.events]
    engine = ResearchEngine()
    outcomes = engine.run_backtest(domain_events, profile=profile, tolerance_days=body.tolerance_days)

    exact_hits = sum(1 for o in outcomes if o.match_status.value == "window_exact_hit")
    tol_hits = sum(1 for o in outcomes if o.match_status.value == "window_tolerance_hit")
    misses = sum(1 for o in outcomes if o.match_status.value == "temporal_miss")
    total = len(outcomes)
    hit_rate = round((exact_hits + tol_hits) / total, 4) if total > 0 else 0.0

    return BacktestResponse(
        total_events=total,
        exact_hits=exact_hits,
        tolerance_hits=tol_hits,
        misses=misses,
        hit_rate=hit_rate,
        outcomes=[
            BacktestOutcomeSchema(
                event_id=o.event_id,
                actual_date=o.actual_date.isoformat(),
                predicted_window_start=o.predicted_window_start.isoformat() if o.predicted_window_start else None,
                predicted_window_end=o.predicted_window_end.isoformat() if o.predicted_window_end else None,
                peak_predicted_date=o.peak_predicted_date.isoformat() if o.peak_predicted_date else None,
                deterministic_score=o.deterministic_score,
                match_status=o.match_status.value,
                peak_offset_days=o.peak_offset_days,
            )
            for o in outcomes
        ],
    )


class CalibrateRequest(BaseModel):
    dataset_id: str
    dataset_name: str
    dataset_version: str = "1.0"
    event_type: str
    events: list[GroundTruthEventSchema]
    model_type: str = "isotonic_regression"
    profile_id: Optional[str] = "parashari_standard_v1"
    tolerance_days: int = 30
    train_ratio: float = 0.70
    split_seed: int = 42


@router.post("/calibrate", response_model=CalibrationResponse)
async def calibrate_dataset(body: CalibrateRequest) -> CalibrationResponse:
    """Fits calibration model on Train split and validates strictly on Holdout split."""
    profile = (
        EMPIRICAL_RESEARCH_PROFILE
        if body.profile_id == "empirical_research_v1"
        else PARASHARI_STANDARD_PROFILE
    )

    domain_events = [_to_domain_event(e) for e in body.events]
    dataset = BenchmarkDataset(
        dataset_id=body.dataset_id,
        name=body.dataset_name,
        event_type=body.event_type,
        version=body.dataset_version,
        description="",
        events=tuple(domain_events),
    )

    research = ResearchEngine()
    split = research.split_dataset(dataset, train_ratio=body.train_ratio, seed=body.split_seed)

    # 1. Backtest Train split
    train_outcomes = research.run_backtest(split.train_events, profile=profile, tolerance_days=body.tolerance_days)

    # 2. Backtest Holdout split
    holdout_outcomes = research.run_backtest(split.holdout_events, profile=profile, tolerance_days=body.tolerance_days)

    calib = CalibrationEngine()
    if body.model_type == "platt_scaling":
        model = calib.fit_platt_scaling(
            train_outcomes=train_outcomes,
            dataset_id=body.dataset_id,
            dataset_version=body.dataset_version,
            event_type=body.event_type,
            profile_id=profile.profile_id,
            split_seed=body.split_seed,
            split_train_ratio=body.train_ratio,
            tolerance_days=body.tolerance_days,
        )
    else:
        model = calib.fit_isotonic_calibration(
            train_outcomes=train_outcomes,
            dataset_id=body.dataset_id,
            dataset_version=body.dataset_version,
            event_type=body.event_type,
            profile_id=profile.profile_id,
            split_seed=body.split_seed,
            split_train_ratio=body.train_ratio,
            tolerance_days=body.tolerance_days,
        )

    # 3. Validate on Holdout split
    validation = calib.evaluate_holdout_validation(holdout_outcomes, model)

    pools_schema = [
        CalibrationPoolSchema(
            score_range=f"{p.min_score}-{p.max_score}",
            sample_size_n=p.bin_sample_size_n,
            observed_hits=p.observed_hits,
            empirical_hit_rate_pct=round(p.empirical_hit_rate * 100, 1),
            rate_ci_95=list(p.rate_ci_95),
            has_small_n_warning=p.has_small_n_warning,
        )
        for p in model.isotonic_pools
    ]

    platt_a = model.platt_params.slope_a if model.platt_params else None
    platt_b = model.platt_params.intercept_b if model.platt_params else None

    return CalibrationResponse(
        model_type=model.provenance.calibration_model_type.value,
        dataset_id=model.provenance.dataset_id,
        dataset_version=model.provenance.dataset_version,
        profile_id=model.provenance.consensus_profile_id,
        calibration_sample_size_n=len(split.train_events),
        holdout_sample_size_n=validation.holdout_sample_size_n,
        holdout_brier_score=validation.holdout_brier_score,
        holdout_hit_rate=validation.holdout_hit_rate,
        mean_peak_offset_days=validation.mean_peak_offset_days,
        isotonic_pools=pools_schema,
        platt_slope_a=platt_a,
        platt_intercept_b=platt_b,
    )


@router.get("/calibration/profiles")
def list_calibration_profiles():
    engine = CalibrationEngine.get_instance()
    profiles = engine.list_candidate_profiles()
    return [
        {
            "profile_id": p.profile_id,
            "name": p.name,
            "description": p.description,
            "dataset_id": p.dataset_id,
            "technique_weights": p.technique_weights,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
            "activated_at": p.activated_at.isoformat() if p.activated_at else None,
        }
        for p in profiles
    ]


@router.post("/calibration/profiles/{profile_id}/activate")
def activate_calibration_profile(profile_id: str):
    engine = CalibrationEngine.get_instance()
    activated = engine.activate_candidate_profile(profile_id)
    if not activated:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found.")
    return {
        "profile_id": activated.profile_id,
        "name": activated.name,
        "status": activated.status,
        "activated_at": activated.activated_at.isoformat() if activated.activated_at else None,
    }


@router.get("/calibration/audit-trail")
def get_calibration_audit_trail():
    engine = CalibrationEngine.get_instance()
    logs = engine.get_audit_trail()
    return [
        {
            "log_id": l.log_id,
            "candidate_profile_id": l.candidate_profile_id,
            "action": l.action,
            "timestamp": l.timestamp.isoformat(),
            "details": l.details,
        }
        for l in logs
    ]