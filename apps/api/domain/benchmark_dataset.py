"""
AstroOS — Benchmark Dataset & Quality Engine Domain Contract

Defines domain models for benchmark corpus management, multi-tier QC,
auditable rejection logs, cryptographic locking, and profile comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from apps.api.domain.research_calibration import (
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
)


class DuplicateClassification(str, Enum):
    UNIQUE = "unique"
    HARD_DUPLICATE = "hard_duplicate"        # Exact subject + birth + event type + actual date
    CONFLICTING_RECORD = "conflicting_record"  # Same subject + same event + conflicting birth data
    POSSIBLE_DUPLICATE = "possible_duplicate"  # Near-duplicate with similar timestamps/locations


class RejectionCode(str, Enum):
    INVALID_COORDINATES = "INVALID_COORDINATES"
    INVALID_DATETIME = "INVALID_DATETIME"
    CHART_GENERATION_FAILED = "CHART_GENERATION_FAILED"
    HARD_DUPLICATE_COLLISION = "HARD_DUPLICATE_COLLISION"
    CONFLICTING_RECORD_COLLISION = "CONFLICTING_RECORD_COLLISION"
    BELOW_RODDEN_THRESHOLD = "BELOW_RODDEN_THRESHOLD"
    BELOW_DATE_PRECISION_THRESHOLD = "BELOW_DATE_PRECISION_THRESHOLD"


@dataclass(frozen=True)
class InclusionCriteria:
    """Explicit filtering rules for admitting events into a benchmark corpus."""

    min_birth_confidence: BirthDataConfidence = BirthDataConfidence.B
    allowed_date_confidences: tuple[EventDateConfidence, ...] = (
        EventDateConfidence.EXACT_DATE,
        EventDateConfidence.APPROX_WEEK,
        EventDateConfidence.APPROX_MONTH,
    )
    min_event_verification: EventVerification = EventVerification.SECONDARY_REPORT
    geographic_bounds: Optional[tuple[float, float, float, float]] = None  # (min_lat, max_lat, min_lon, max_lon)


@dataclass(frozen=True)
class RejectedEventRecord:
    """An auditable record of an event rejected during dataset validation."""

    event_id: str
    subject_id: str
    raw_payload: dict[str, Any]
    rejection_code: RejectionCode
    reason: str
    rejected_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class PossibleDuplicateWarning:
    """A flagged near-duplicate event kept in the dataset with a research warning."""

    primary_event_id: str
    flagged_event_id: str
    subject_id: str
    reason: str


@dataclass(frozen=True)
class DatasetValidationResult:
    """Comprehensive quality control and audit result for an ingested event corpus."""

    is_valid: bool
    total_submitted: int
    accepted_events: tuple[GroundTruthEvent, ...]
    rejected_records: tuple[RejectedEventRecord, ...]
    flagged_warnings: tuple[PossibleDuplicateWarning, ...]
    content_hash_sha256: str
    validated_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class BenchmarkDefinition:
    """Canonical specification and inclusion policy for a benchmark problem domain."""

    benchmark_id: str  # e.g. "BENCH-CAREER-001"
    name: str
    event_type: str
    description: str
    inclusion_criteria: InclusionCriteria
    standard_tolerance_days: int = 30


@dataclass(frozen=True)
class LockedBenchmarkCorpus:
    """An immutable, content-hashed ground truth benchmark corpus ready for evaluation."""

    benchmark_id: str
    version: str  # Semantic version, e.g. "1.0.0"
    content_hash_sha256: str
    event_type: str
    events: tuple[GroundTruthEvent, ...]
    definition: BenchmarkDefinition
    locked_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class BenchmarkProfileComparisonRow:
    """Evaluation metrics for a single predictive profile evaluated on the holdout split."""

    profile_id: str
    profile_name: str
    calibration_sample_size_n: int  # Train N
    holdout_sample_size_n: int      # Holdout N
    holdout_precision: float
    holdout_recall: float
    holdout_f1_score: float
    holdout_hit_rate_pct: float
    holdout_brier_score: float
    holdout_mae_peak_days: float
    holdout_median_peak_offset_days: float
    holdout_p90_peak_offset_days: float
    calibration_method: str


@dataclass(frozen=True)
class BenchmarkComparisonReport:
    """Scientific comparison matrix across multiple consensus profiles on locked split."""

    benchmark_id: str
    benchmark_version: str
    content_hash_sha256: str
    split_seed: int
    split_train_ratio: float
    tolerance_days: int
    total_benchmark_events: int
    train_events_count: int
    holdout_events_count: int
    rows: tuple[BenchmarkProfileComparisonRow, ...]
    executed_at: datetime = field(default_factory=lambda: datetime.now())