"""
AstroOS — Research & Calibration Domain Contract (v4)

Defines domain models for empirical evaluation and statistical calibration:
  - GroundTruthEvent & Provenance: Birth/Event confidence and verification ratings
  - CalibrationDatasetSplit: Strict Train (e.g. 70%) vs Holdout (e.g. 30%) separation
  - TemporalMatchStatus & BacktestOutcome: Window-centric temporal hit/miss classification
  - CalibrationModel: Polymodal representation for Isotonic Regression vs Platt Scaling
  - ValidationSummary: Out-of-sample metrics evaluated strictly on unseen holdout data
  - CalibratedPrediction: Statistically grounded prediction output with full provenance
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class BirthDataConfidence(str, Enum):
    AA = "AA"  # Birth Certificate / Hospital Record
    A = "A"    # Direct Memory / Family Record
    B = "B"    # Biography / Autobiography
    C = "C"    # Caution / Unverified
    DD = "DD"  # Dirty Data / Conflicting times


class EventDateConfidence(str, Enum):
    EXACT_DATE = "exact_date"
    APPROX_WEEK = "approx_week"
    APPROX_MONTH = "approx_month"
    APPROX_YEAR = "approx_year"


class EventVerification(str, Enum):
    OFFICIAL_DOCUMENT = "official_document"
    PRIMARY_BIOGRAPHY = "primary_biography"
    SECONDARY_REPORT = "secondary_report"
    COMMUNITY_SUBMISSION = "community_submission"


class TemporalMatchStatus(str, Enum):
    WINDOW_EXACT_HIT = "window_exact_hit"          # actual_date in [window_start, window_end]
    WINDOW_TOLERANCE_HIT = "window_tolerance_hit"  # actual_date in [window_start - tol, window_end + tol]
    TEMPORAL_MISS = "temporal_miss"                # outside window tolerance or no window predicted


class CalibrationModelType(str, Enum):
    ISOTONIC_REGRESSION = "isotonic_regression"
    PLATT_SCALING = "platt_scaling"


@dataclass(frozen=True)
class GroundTruthEvent:
    """A verified real-world historical event with multidimensional provenance metadata."""

    event_id: str
    subject_id: str
    event_type: str  # e.g. "career", "marriage_timing", "wealth"
    actual_date: date
    birth_datetime_utc: datetime
    birth_latitude: float
    birth_longitude: float
    birth_confidence: BirthDataConfidence = BirthDataConfidence.AA
    event_date_confidence: EventDateConfidence = EventDateConfidence.EXACT_DATE
    event_verification: EventVerification = EventVerification.OFFICIAL_DOCUMENT
    source_citation: str = ""
    notes: str = ""


@dataclass(frozen=True)
class BenchmarkDataset:
    """A curated benchmark corpus for backtesting and empirical calibration."""

    dataset_id: str
    name: str
    event_type: str
    version: str
    description: str
    events: tuple[GroundTruthEvent, ...]


@dataclass(frozen=True)
class CalibrationDatasetSplit:
    """Deterministic partition into calibration training set and unseen holdout test set."""

    dataset_id: str
    dataset_version: str
    train_events: tuple[GroundTruthEvent, ...]
    holdout_events: tuple[GroundTruthEvent, ...]
    split_seed: int
    split_train_ratio: float


@dataclass(frozen=True)
class BacktestOutcome:
    """Evaluation result of a single event in a backtest run."""

    event_id: str
    actual_date: date
    predicted_window_start: Optional[date]
    predicted_window_end: Optional[date]
    peak_predicted_date: Optional[date]
    deterministic_score: int  # 0 to 100
    match_status: TemporalMatchStatus
    peak_offset_days: Optional[int]  # (peak_predicted_date - actual_date) in days
    tolerance_days_used: int
    evidence_drivers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CalibrationPoolInterval:
    """Isotonic regression pooled score interval."""

    min_score: int
    max_score: int
    bin_sample_size_n: int
    observed_hits: int
    empirical_hit_rate: float
    rate_standard_error: float
    rate_ci_95: tuple[float, float]
    has_small_n_warning: bool


@dataclass(frozen=True)
class PlattParameters:
    """Platt scaling logistic parameters: P(S) = 1 / (1 + exp(-(aS + b)))."""

    slope_a: float
    intercept_b: float
    train_sample_size_n: int


@dataclass(frozen=True)
class CalibrationProvenance:
    """Full scientific reproducibility metadata."""

    dataset_id: str
    dataset_version: str
    event_type: str
    consensus_profile_id: str
    calibration_model_type: CalibrationModelType
    calibration_model_version: str
    fit_timestamp: datetime
    split_seed: int
    split_train_ratio: float
    tolerance_days: int


@dataclass(frozen=True)
class ValidationSummary:
    """Empirical performance metrics evaluated strictly on unseen holdout test data."""

    holdout_sample_size_n: int
    holdout_brier_score: float  # Mean((p - y)^2) on holdout
    holdout_hit_rate: float     # TP / Holdout N
    mean_peak_offset_days: float
    evaluated_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class CalibrationModel:
    """Polymodal calibration model holding either Isotonic pools or Platt coefficients."""

    provenance: CalibrationProvenance
    isotonic_pools: tuple[CalibrationPoolInterval, ...] = field(default_factory=tuple)
    platt_params: Optional[PlattParameters] = None


@dataclass(frozen=True)
class CalibratedPrediction:
    """Statistically grounded prediction output with model-specific provenance."""

    event_type: str
    start_date: date
    end_date: date
    peak_date: date
    deterministic_score: int  # 0 to 100
    calibrated_probability: float  # 0.0 to 1.0
    calibration_rate_ci_95: tuple[float, float]
    calibration_sample_size_n: int
    holdout_sample_size_n: int
    holdout_brier_score: float
    calibration_model_type: CalibrationModelType
    # Isotonic-specific provenance
    calibration_bin_min_score: Optional[int] = None
    calibration_bin_max_score: Optional[int] = None
    calibration_bin_sample_size_n: Optional[int] = None
    calibration_bin_observed_hits: Optional[int] = None
    # Platt-specific provenance
    platt_slope_a: Optional[float] = None
    platt_intercept_b: Optional[float] = None
    # Context
    has_small_n_warning: bool = False
    provenance: Optional[CalibrationProvenance] = None
    primary_drivers: tuple[str, ...] = field(default_factory=tuple)
    opposing_factors: tuple[str, ...] = field(default_factory=tuple)
    evidence_trace: tuple[str, ...] = field(default_factory=tuple)