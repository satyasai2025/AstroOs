"""
AstroOS — Prediction Validation & Backtesting Pydantic Schemas (Module 22, Priority 7)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field

from apps.api.domain.prediction_validation import (
    OutcomeStatus,
    PredictionCategory,
    TemporalSplitType,
    ValidationVerdict,
)


class PredictionCreateRequest(BaseModel):
    prediction_id: Optional[str] = None
    chart_id: str
    subject_name: str
    technique: str
    category: PredictionCategory
    predicted_event: str
    expected_direction: str = "POSITIVE_FRUCTIFICATION"
    prediction_timestamp: datetime
    horizon_days: int = Field(default=90, ge=1)
    expected_date_start: datetime
    expected_date_end: datetime
    evidence_ids: list[str] = Field(default_factory=list)
    dasha_evidence: dict[str, Any] = Field(default_factory=dict)
    transit_evidence: dict[str, Any] = Field(default_factory=dict)
    kp_evidence: dict[str, Any] = Field(default_factory=dict)
    sbc_evidence: dict[str, Any] = Field(default_factory=dict)
    classical_rule_evidence: dict[str, Any] = Field(default_factory=dict)
    varga_evidence: dict[str, Any] = Field(default_factory=dict)
    ashtakavarga_evidence: dict[str, Any] = Field(default_factory=dict)
    calculation_snapshot: dict[str, Any] = Field(default_factory=dict)


class PredictionItemResponse(BaseModel):
    prediction_id: str
    chart_id: str
    subject_name: str
    technique: str
    category: PredictionCategory
    predicted_event: str
    expected_direction: str
    prediction_timestamp: datetime
    horizon_days: int
    expected_date_start: datetime
    expected_date_end: datetime
    evidence_ids: list[str]
    evidence_hash: str
    engine_version: str


class OutcomeCreateRequest(BaseModel):
    outcome_id: Optional[str] = None
    chart_id: str
    subject_name: str
    category: PredictionCategory
    observed_date: datetime
    actual_outcome_description: str
    observed_direction: str = "POSITIVE_FRUCTIFICATION"
    verification_status: OutcomeStatus = OutcomeStatus.VERIFIED_HISTORICAL
    source_reference: str
    notes: str = ""


class OutcomeItemResponse(BaseModel):
    outcome_id: str
    chart_id: str
    subject_name: str
    category: PredictionCategory
    observed_date: datetime
    actual_outcome_description: str
    observed_direction: str
    verification_status: OutcomeStatus
    source_reference: str
    notes: str
    outcome_hash: str


class MatchRequest(BaseModel):
    prediction_id: str
    outcome_id: Optional[str] = None


class MatchResponse(BaseModel):
    match_id: str
    prediction_id: str
    outcome_id: Optional[str]
    verdict: ValidationVerdict
    category_matched: bool
    temporal_error_days: Optional[int]
    direction_matched: bool
    predicate_traces: list[str]
    evidence_provenance_ids: list[str]


class BacktestRequest(BaseModel):
    dataset_name: str = "Canonical Research Dataset"
    technique_filter: Optional[str] = None
    category_filter: Optional[str] = None
    temporal_split: TemporalSplitType = TemporalSplitType.VALIDATION


class ConfusionMatrixResponse(BaseModel):
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    total: int
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]


class BacktestRunResponse(BaseModel):
    backtest_id: str
    dataset_name: str
    technique_filter: Optional[str]
    category_filter: Optional[str]
    temporal_split: TemporalSplitType
    total_predictions: int
    resolved_predictions: int
    unresolved_predictions: int
    matched_count: int
    partial_count: int
    missed_count: int
    contradicted_count: int
    inconclusive_count: int
    hit_rate: float
    confusion_matrix: ConfusionMatrixResponse
    confidence_interval_95: list[float]
    temporal_leakage_detected: bool
    leakage_reasons: list[str]
    result_hash: str
    evaluations: list[MatchResponse]


class TechniqueSummaryItem(BaseModel):
    technique: str
    total_predictions: int
    resolved_predictions: int
    matched_count: int
    partial_count: int
    missed_count: int
    contradicted_count: int
    hit_rate: float
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    ci_95_low: float
    ci_95_high: float
