"""
AstroOS — Longitudinal Outcome Tracking Engine Domain Models (Priority 27)

Defines domain dataclasses for:
  - Real-World Event Outcome Verification Status (CONFIRMED_HIT, CONFIRMED_MISS, AMBIGUOUS_UNVERIFIED, OUTSIDE_WINDOW)
  - Population Distribution Drift via PSI (STABLE_CONGRUENT, MILD_DRIFT_MONITOR, CRITICAL_DEGRADATION_TRIGGER)
  - Statistical Degradation Test (Two-proportion Z-test / Binomial degradation p-value)
  - Chronological Time-Series Intervals & Rolling Calibration Tracking
  - Authoritative Longitudinal Tracking Reports with Complete Cryptographic Lineage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class OutcomeVerificationStatus(str, Enum):
    CONFIRMED_HIT = "CONFIRMED_HIT"                   # Event occurred strictly within predicted polymodal timing window
    CONFIRMED_MISS = "CONFIRMED_MISS"                 # Predicted timing window elapsed with zero event occurrence
    AMBIGUOUS_UNVERIFIED = "AMBIGUOUS_UNVERIFIED"     # Event occurred but timing precision is ambiguous or pending documentation
    OUTSIDE_WINDOW = "OUTSIDE_WINDOW"                 # Event occurred outside the predicted temporal interval


class PopulationDistributionDriftStatus(str, Enum):
    STABLE_CONGRUENT = "STABLE_CONGRUENT"                     # PSI < 0.10
    MILD_DRIFT_MONITOR = "MILD_DRIFT_MONITOR"                 # 0.10 <= PSI < 0.25
    CRITICAL_DEGRADATION_TRIGGER = "CRITICAL_DEGRADATION_TRIGGER" # PSI >= 0.25


@dataclass(frozen=True)
class StatisticalDegradationTest:
    """Formal hypothesis test comparing rolling longitudinal hit-rate against baseline prospective hit-rate."""
    baseline_prospective_hit_rate: float
    longitudinal_rolling_hit_rate: float
    delta_hit_rate: float                      # longitudinal - baseline
    sample_size_longitudinal: int
    z_statistic: float
    degradation_p_value: float                 # One-tailed p-value for H0: longitudinal >= baseline
    is_degradation_statistically_significant: bool # True if p < 0.05 and delta < 0
    test_interpretation: str


@dataclass(frozen=True)
class TrackedSubjectOutcomeRecord:
    """An individual real-world prospective subject outcome record."""
    subject_id: str
    target_objective: str
    rule_id: str
    predicted_window_start: date
    predicted_window_end: date
    actual_event_date: Optional[date]
    predicted_probability: float
    verification_status: OutcomeVerificationStatus
    verification_source: str
    recorded_at: datetime


@dataclass(frozen=True)
class LongitudinalTimeSeriesInterval:
    """A discrete chronological time-series monitoring interval (e.g. quarterly or monthly)."""
    interval_id: str                          # e.g. "2026-Q1", "2026-Q2"
    interval_start: date
    interval_end: date
    sample_size_n: int
    confirmed_hits: int
    confirmed_misses: int
    interval_hit_rate: float
    rolling_brier_score: float
    interval_psi: float
    distribution_drift_status: PopulationDistributionDriftStatus


@dataclass(frozen=True)
class LongitudinalTrackingReport:
    """Authoritative scientific report synthesizing continuous real-world prospective outcomes."""
    report_id: str
    rule_id: str
    rule_name: str
    target_objective: str
    total_subjects_tracked: int
    confirmed_hits_count: int
    confirmed_misses_count: int
    ambiguous_count: int
    outside_window_count: int
    cumulative_hit_rate: float
    cumulative_brier_score: float
    population_distribution_drift: PopulationDistributionDriftStatus
    population_stability_index: float
    statistical_degradation_test: StatisticalDegradationTest
    time_series_intervals: Tuple[LongitudinalTimeSeriesInterval, ...]
    p11_lineage_snapshot_id: str
    report_provenance_hash: str
    epistemic_non_causal_statement: str
    evaluated_at: datetime
