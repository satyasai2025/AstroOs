"""
AstroOS — Longitudinal Resonance & Cohort Statistical Validation Domain Models (Priority 15)

Defines domain dataclasses for:
  - Cohort Subjects & Longitudinal Benchmark Datasets
  - Monte Carlo Permutation Null Distributions
  - Hypothesis Testing (p-values, z-scores, 95% Confidence Intervals)
  - Cohort Validation Evaluation Reports
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional


@dataclass(frozen=True)
class CohortSubject:
    """Individual subject in a longitudinal research cohort."""
    subject_id: str
    birth_datetime_utc: datetime
    latitude: float
    longitude: float
    event_occurred: bool
    event_date: Optional[date]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CohortDataset:
    """A curated longitudinal dataset for mass statistical benchmarking."""
    dataset_id: str
    name: str
    target_objective: str
    total_subjects: int
    positive_count: int
    negative_count: int
    description: str


@dataclass(frozen=True)
class HypothesisTestResult:
    """Statistical significance test against randomized Monte Carlo permutations."""
    metric_name: str
    observed_value: float
    null_mean: float
    null_std: float
    z_score: float
    p_value: float
    is_statistically_significant: bool  # True if p < 0.05
    confidence_interval_95: tuple[float, float]
    methodology: str


@dataclass(frozen=True)
class CohortValidationReport:
    """Comprehensive publication-grade cohort statistical validation report."""
    report_id: str
    dataset_id: str
    dataset_name: str
    target_objective: str
    total_subjects_evaluated: int
    positive_prevalence: float
    brier_score: float
    log_loss: float
    roc_auc: float
    pr_auc: float
    monte_carlo_iterations: int
    permutation_p_value: float
    null_roc_distribution: tuple[float, ...]
    hypothesis_tests: tuple[HypothesisTestResult, ...]
    executive_summary: str
    publication_provenance: str
