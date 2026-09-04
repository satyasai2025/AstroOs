"""
AstroOS — Research Validity & Statistical Integrity Domain Models (Priority 33)

Defines domain dataclasses, enums, conservative precedence verdict logic,
bias diagnostics, baseline comparison models, and epistemic disclosures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

MANDATORY_VALIDITY_NON_CAUSAL_DISCLOSURE = (
    "RESEARCH_VALIDITY_DISCLOSURE: Validity assessment evaluates statistical integrity, "
    "temporal ordering, baseline superiority, and methodological rigor. It does not establish "
    "astrological causation, predictive validity, or a physical mechanism."
)

METHODOLOGY_VERSION = "P33-METHODOLOGY-1.0"


class ValidityVerdict(str, Enum):
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    DATA_QUALITY_LIMITED = "DATA_QUALITY_LIMITED"
    TEMPORALLY_INVALID = "TEMPORALLY_INVALID"
    POTENTIAL_BIAS = "POTENTIAL_BIAS"
    POTENTIAL_LEAKAGE = "POTENTIAL_LEAKAGE"
    NOT_SUPERIOR_TO_BASELINE = "NOT_SUPERIOR_TO_BASELINE"
    PRELIMINARY_SUPPORT = "PRELIMINARY_SUPPORT"
    STATISTICALLY_SUPPORTED = "STATISTICALLY_SUPPORTED"
    ROBUST_SUPPORT = "ROBUST_SUPPORT"
    CONTRADICTED = "CONTRADICTED"
    INVALID_ANALYSIS = "INVALID_ANALYSIS"


class MissingDataClassification(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class LeakageDiagnosticStatus(str, Enum):
    NO_LEAKAGE_DETECTED = "NO_LEAKAGE_DETECTED"
    POTENTIAL_LEAKAGE = "POTENTIAL_LEAKAGE"
    CONFIRMED_LEAKAGE = "CONFIRMED_LEAKAGE"
    UNKNOWN = "UNKNOWN"


class TemporalValidityStatus(str, Enum):
    TEMPORALLY_VALID = "TEMPORALLY_VALID"
    TEMPORALLY_AMBIGUOUS = "TEMPORALLY_AMBIGUOUS"
    TEMPORALLY_INVALID = "TEMPORALLY_INVALID"


class SampleAdequacy(str, Enum):
    ADEQUATE = "ADEQUATE"
    MARGINAL = "MARGINAL"
    INSUFFICIENT = "INSUFFICIENT"


class DatasetRole(str, Enum):
    TRAINING = "TRAINING"
    VALIDATION = "VALIDATION"
    TEST = "TEST"
    PROSPECTIVE = "PROSPECTIVE"


class MultipleTestingMethod(str, Enum):
    NONE = "NONE"
    BONFERRONI = "BONFERRONI"
    BENJAMINI_HOCHBERG = "BENJAMINI_HOCHBERG"


class ValidityAuditOperation(str, Enum):
    ASSESSMENT_CREATED = "ASSESSMENT_CREATED"
    DATASET_MANIFEST_CREATED = "DATASET_MANIFEST_CREATED"
    BIAS_CHECK_COMPLETED = "BIAS_CHECK_COMPLETED"
    TEMPORAL_CHECK_COMPLETED = "TEMPORAL_CHECK_COMPLETED"
    LEAKAGE_CHECK_COMPLETED = "LEAKAGE_CHECK_COMPLETED"
    BASELINE_COMPUTED = "BASELINE_COMPUTED"
    STATISTICAL_ANALYSIS_COMPLETED = "STATISTICAL_ANALYSIS_COMPLETED"
    VERDICT_GENERATED = "VERDICT_GENERATED"
    ASSESSMENT_SUPERSEDED = "ASSESSMENT_SUPERSEDED"


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    confidence_level: float                 # e.g., 0.95 for 95% CI
    lower_bound: float
    upper_bound: float
    method: str                             # e.g., "WILSON_SCORE", "CLOPPER_PEARSON"


@dataclass(frozen=True)
class EffectSizeResult:
    metric_name: str
    value: float
    interpretation: str                      # e.g., "NEGLIGIBLE", "SMALL", "MEDIUM", "LARGE"
    is_practically_meaningful: bool


@dataclass(frozen=True)
class StatisticalResult:
    metric_name: str
    value: float
    method: str
    sample_size: int
    confidence_interval: Optional[ConfidenceInterval] = None
    p_value: Optional[float] = None
    adjusted_p_value: Optional[float] = None
    multiple_testing_method: MultipleTestingMethod = MultipleTestingMethod.NONE


@dataclass(frozen=True)
class BaselineComparison:
    metric_name: str
    model_metric: float
    majority_baseline: float
    random_baseline: float
    permutation_baseline: Optional[float]
    absolute_difference: float
    relative_difference: float
    is_superior_to_majority: bool
    is_superior_to_random: bool


@dataclass(frozen=True)
class BiasDiagnostic:
    diagnostic_name: str
    risk_level: str                         # "NONE", "LOW", "POTENTIAL_RISK", "CONFIRMED"
    reason: str
    evidence_details: Dict[str, Any]


@dataclass(frozen=True)
class TemporalIntegrityResult:
    status: TemporalValidityStatus
    predictions_registered_before_outcome: bool
    look_ahead_risk_detected: bool
    details: Dict[str, Any]


@dataclass(frozen=True)
class LeakageDiagnostic:
    status: LeakageDiagnosticStatus
    outcome_derived_features_detected: bool
    future_timestamps_detected: bool
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class DatasetManifest:
    manifest_id: str
    source_snapshot_id: str
    total_observations: int
    usable_observations: int
    excluded_observations: int
    missing_observations: int
    duplicate_count: int
    prospective_count: int
    retrospective_count: int
    unknown_timing_count: int
    verification_distribution: Dict[str, int]
    domain_distribution: Dict[str, int]
    methodology_version: str
    manifest_hash: str


@dataclass(frozen=True)
class ValiditySnapshot:
    snapshot_id: str
    assessment_id: str
    source_snapshot_id: str
    methodology_version: str
    canonical_payload_hash: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_VALIDITY_NON_CAUSAL_DISCLOSURE


@dataclass(frozen=True)
class ValidityAuditEvent:
    audit_event_id: str
    assessment_id: str
    operation: ValidityAuditOperation
    actor_type: str
    timestamp: datetime
    details_hash: str
    reason: str


@dataclass(frozen=True)
class ValidityAssessment:
    assessment_id: str
    target_objective: str
    source_snapshot_id: str
    methodology_version: str
    dataset_manifest: DatasetManifest
    sample_adequacy: SampleAdequacy
    missing_data_classification: MissingDataClassification
    temporal_integrity: TemporalIntegrityResult
    leakage_diagnostic: LeakageDiagnostic
    selection_bias_diagnostic: BiasDiagnostic
    cherry_picking_diagnostic: BiasDiagnostic
    baseline_comparison: BaselineComparison
    statistical_results: Tuple[StatisticalResult, ...]
    effect_sizes: Tuple[EffectSizeResult, ...]
    overall_verdict: ValidityVerdict
    verdict_explanation: Tuple[str, ...]
    limitations: Tuple[str, ...]
    warnings: Tuple[str, ...]
    analysis_fingerprint: str
    validity_snapshot_id: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_VALIDITY_NON_CAUSAL_DISCLOSURE
