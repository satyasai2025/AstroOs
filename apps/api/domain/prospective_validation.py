"""
AstroOS — Prospective Research Validation & Rule Lifecycle Domain Models (Priority 20)

Defines domain dataclasses for:
  - Epistemic Rule Lifecycle Status (DISCOVERED, REPLICATED, PROSPECTIVE_TESTING, PROSPECTIVELY_SUPPORTED, PROSPECTIVELY_REFUTED, PROSPECTIVE_INCONCLUSIVE)
  - Pre-Registration Records with immutable SHA-256 formula hashing
  - Prospective Blind Predictions & Outcome Logging
  - Statistical Drift Analysis (PSI & Kolmogorov-Smirnov)
  - Comprehensive Publication-Grade Prospective Evaluation Reports
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional, Sequence


class ProspectiveRuleLifecycleStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    REPLICATED = "REPLICATED"
    PROSPECTIVE_TESTING = "PROSPECTIVE_TESTING"
    PROSPECTIVELY_SUPPORTED = "PROSPECTIVELY_SUPPORTED"
    PROSPECTIVELY_REFUTED = "PROSPECTIVELY_REFUTED"
    PROSPECTIVE_INCONCLUSIVE = "PROSPECTIVE_INCONCLUSIVE"


@dataclass(frozen=True)
class PreRegistrationRecord:
    """Immutable pre-registration snapshot of a candidate rule before prospective testing."""
    registration_id: str
    hypothesis_id: str
    rule_name: str
    target_objective: str
    frozen_formula: str
    frozen_thresholds: dict[str, float]
    sha256_registration_hash: str
    registered_at: datetime
    lineage_snapshot_id: str
    author: str = "ResearchValidationEngine"


@dataclass(frozen=True)
class ProspectiveSubjectPrediction:
    """Individual subject forward-only blind prediction record."""
    prediction_id: str
    registration_id: str
    subject_id: str
    predicted_probability: float
    prediction_window_start: date
    prediction_window_end: date
    predicted_at: datetime
    actual_outcome: Optional[bool] = None
    outcome_recorded_at: Optional[datetime] = None


@dataclass(frozen=True)
class DriftAnalysisResult:
    """Population and temporal stability index (PSI) between discovery and prospective cohort."""
    psi_drift_score: float
    is_significant_drift: bool
    drift_diagnosis: str


@dataclass(frozen=True)
class ProspectiveEvaluationReport:
    """Publication-grade prospective empirical evaluation report."""
    evaluation_id: str
    registration_id: str
    target_objective: str
    total_prospective_subjects: int
    positive_outcomes_count: int
    brier_score: float
    log_loss: float
    roc_auc: float
    pr_auc: float
    precision: float
    recall: float
    statistical_lift: float
    confidence_interval_95_roc: tuple[float, float]
    drift_analysis: DriftAnalysisResult
    final_lifecycle_status: ProspectiveRuleLifecycleStatus
    epistemic_classification: str
    evaluated_at: datetime
