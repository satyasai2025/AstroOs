"""
AstroOS — Prediction Validation & Empirical Outcome Backtesting Domain (Module 22, Priority 7)

Pure domain models for:
1. Immutable Prediction Snapshots with Frozen Evidence Hashing
2. Actual Ground-Truth Outcome Registry
3. Deterministic Prediction-to-Outcome Match Evaluation & Predicate Traces
4. Empirical Backtesting Engine with Confusion Matrices & Confidence Intervals
5. Temporal Stratification (Train / Validation / Test) & Temporal Leakage Detection
6. Comprehensive Evidence Provenance & Audit Trails
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class PredictionCategory(str, Enum):
    CAREER = "career"
    MARRIAGE = "marriage"
    FINANCE = "finance"
    HEALTH = "health"
    RELOCATION = "relocation"
    EDUCATION = "education"
    SPIRITUAL = "spiritual"
    GENERAL = "general"


class OutcomeStatus(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED_HISTORICAL = "VERIFIED_HISTORICAL"
    OBSERVED_PROSPECTIVE = "OBSERVED_PROSPECTIVE"


class ValidationVerdict(str, Enum):
    MATCHED = "MATCHED"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MISSED = "MISSED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNRESOLVED = "UNRESOLVED"


class TemporalSplitType(str, Enum):
    RESEARCH_TRAIN = "RESEARCH_TRAIN"
    VALIDATION = "VALIDATION"
    TEST_OUT_OF_SAMPLE = "TEST_OUT_OF_SAMPLE"


def compute_evidence_hash(evidence_dict: dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 checksum over frozen prediction evidence."""
    canonical_json = json.dumps(evidence_dict, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PredictionSnapshot:
    """
    Immutable frozen snapshot of an astrological prediction and all supporting evidence.
    Once created, this snapshot cannot be retroactively modified.
    """
    prediction_id: str
    chart_id: str
    subject_name: str
    technique: str  # e.g., "KP_CSL", "PARASHARI_DASHA_TRANSIT", "SBC_VEDHA", "CLASSICAL_YOGA"
    category: PredictionCategory
    predicted_event: str
    expected_direction: str  # "POSITIVE_FRUCTIFICATION", "OBSTRUCTION_DELAY", "LOSS_VETO", "NEUTRAL"
    prediction_timestamp: datetime
    horizon_days: int
    expected_date_start: datetime
    expected_date_end: datetime
    evidence_ids: list[str]
    dasha_evidence: dict[str, Any]
    transit_evidence: dict[str, Any]
    kp_evidence: dict[str, Any]
    sbc_evidence: dict[str, Any]
    classical_rule_evidence: dict[str, Any]
    varga_evidence: dict[str, Any]
    ashtakavarga_evidence: dict[str, Any]
    calculation_snapshot: dict[str, Any]
    engine_version: str = "2.0.0"
    evidence_hash: str = ""

    def __post_init__(self):
        if not self.evidence_hash:
            # Package all evidence items into a single dict for hashing
            evidence_blob = {
                "prediction_id": self.prediction_id,
                "chart_id": self.chart_id,
                "technique": self.technique,
                "category": self.category.value,
                "predicted_event": self.predicted_event,
                "expected_direction": self.expected_direction,
                "horizon_days": self.horizon_days,
                "expected_date_start": self.expected_date_start.isoformat(),
                "expected_date_end": self.expected_date_end.isoformat(),
                "evidence_ids": sorted(self.evidence_ids),
                "dasha": self.dasha_evidence,
                "transit": self.transit_evidence,
                "kp": self.kp_evidence,
                "sbc": self.sbc_evidence,
                "classical": self.classical_rule_evidence,
                "varga": self.varga_evidence,
                "ashtakavarga": self.ashtakavarga_evidence,
            }
            object.__setattr__(self, "evidence_hash", compute_evidence_hash(evidence_blob))


@dataclass(frozen=True)
class OutcomeRecord:
    """
    Ground-truth observed life event record.
    """
    outcome_id: str
    chart_id: str
    subject_name: str
    category: PredictionCategory
    observed_date: datetime
    actual_outcome_description: str
    observed_direction: str  # "POSITIVE_FRUCTIFICATION", "OBSTRUCTION_DELAY", "LOSS_VETO", "NEUTRAL"
    verification_status: OutcomeStatus
    source_reference: str
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    outcome_hash: str = ""

    def __post_init__(self):
        if not self.outcome_hash:
            blob = {
                "outcome_id": self.outcome_id,
                "chart_id": self.chart_id,
                "category": self.category.value,
                "observed_date": self.observed_date.isoformat(),
                "actual_outcome": self.actual_outcome_description,
                "observed_direction": self.observed_direction,
                "source": self.source_reference,
            }
            object.__setattr__(self, "outcome_hash", compute_evidence_hash(blob))


@dataclass(frozen=True)
class MatchEvaluationResult:
    """
    Result of comparing a PredictionSnapshot against an OutcomeRecord.
    Contains explicit mathematical and logical predicate traces.
    """
    match_id: str
    prediction_id: str
    outcome_id: Optional[str]
    verdict: ValidationVerdict
    category_matched: bool
    temporal_error_days: Optional[int]  # observed_date - expected_center_date
    direction_matched: bool
    predicate_traces: list[str]
    evidence_provenance_ids: list[str]
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ConfusionMatrix:
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int

    @property
    def total(self) -> int:
        return self.true_positive + self.false_positive + self.true_negative + self.false_negative

    @property
    def precision(self) -> Optional[float]:
        denom = self.true_positive + self.false_positive
        return round(self.true_positive / denom, 4) if denom > 0 else None

    @property
    def recall(self) -> Optional[float]:
        denom = self.true_positive + self.false_negative
        return round(self.true_positive / denom, 4) if denom > 0 else None

    @property
    def f1_score(self) -> Optional[float]:
        p = self.precision
        r = self.recall
        if p and r and (p + r) > 0:
            return round(2 * (p * r) / (p + r), 4)
        return None


@dataclass(frozen=True)
class BacktestCohortRun:
    """
    Complete statistical backtest evaluation over a cohort of predictions and outcomes.
    """
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
    confusion_matrix: ConfusionMatrix
    confidence_interval_95: tuple[float, float]  # (lower_bound, upper_bound)
    temporal_leakage_detected: bool
    leakage_reasons: list[str]
    evaluations: list[MatchEvaluationResult]
    result_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
