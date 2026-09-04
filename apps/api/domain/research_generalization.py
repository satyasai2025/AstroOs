"""
AstroOS — Research External Validity, Generalization & Domain Transportability Domain Models (Priority 35)

Defines domain dataclasses, enums, conservative precedence verdict logic,
distribution shift analysis, generalization matrix, boundary detection,
and non-causal epistemic disclosures for Priority 35.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

MANDATORY_GENERALIZATION_NON_CAUSAL_DISCLOSURE = (
    "RESEARCH_GENERALIZATION_DISCLOSURE: External generalization evaluates performance transportability "
    "and metric stability across population, temporal, and dataset dimensions. It does not establish "
    "astrological causation, predictive validity, or a physical mechanism."
)

GENERALIZATION_METHODOLOGY_VERSION = "P35-METHODOLOGY-1.0"


class GeneralizationVerdict(str, Enum):
    GENERALIZES = "GENERALIZES"
    LIMITED_GENERALIZATION = "LIMITED_GENERALIZATION"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    NON_GENERALIZABLE = "NON_GENERALIZABLE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class MatrixCellStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    LIMITED = "LIMITED"
    FAILED = "FAILED"
    NOT_TESTED = "NOT_TESTED"


class DistributionShiftType(str, Enum):
    NONE = "NONE"
    FEATURE_SHIFT = "FEATURE_SHIFT"
    OUTCOME_SHIFT = "OUTCOME_SHIFT"
    BASELINE_SHIFT = "BASELINE_SHIFT"
    COMPOUND_SHIFT = "COMPOUND_SHIFT"


class FailureRegionType(str, Enum):
    NONE = "NONE"
    PERFORMANCE_COLLAPSE = "PERFORMANCE_COLLAPSE"
    DIRECTION_REVERSAL = "DIRECTION_REVERSAL"
    CONTEXT_SPECIFIC_FAILURE = "CONTEXT_SPECIFIC_FAILURE"
    TEMPORAL_DEGRADATION = "TEMPORAL_DEGRADATION"


class TransportabilityStatus(str, Enum):
    HIGHLY_TRANSPORTABLE = "HIGHLY_TRANSPORTABLE"
    CONDITIONALLY_TRANSPORTABLE = "CONDITIONALLY_TRANSPORTABLE"
    NON_TRANSPORTABLE = "NON_TRANSPORTABLE"
    UNKNOWN = "UNKNOWN"


class GeneralizationAuditOperation(str, Enum):
    DOMAIN_REGISTERED = "DOMAIN_REGISTERED"
    SHIFT_ANALYZED = "SHIFT_ANALYZED"
    BOUNDARIES_DETECTED = "BOUNDARIES_DETECTED"
    MATRIX_COMPUTED = "MATRIX_COMPUTED"
    VERDICT_GENERATED = "VERDICT_GENERATED"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    ASSESSMENT_SUPERSEDED = "ASSESSMENT_SUPERSEDED"


@dataclass(frozen=True)
class ExternalDomain:
    domain_id: str
    domain_name: str
    is_source: bool
    population_dimension: str               # e.g., "INDIAN_SUBARRAY_18_50" vs "EUROPEAN_SUBARRAY_25_60"
    time_dimension: str                     # e.g., "1980_2000_HISTORICAL" vs "2020_2025_RECENT"
    dataset_dimension: str                  # e.g., "CIVIL_REGISTRY_CERTIFICATES" vs "PROSPECTIVE_MOBILE_APP"
    context_dimension: str                  # e.g., "TRADITIONAL_VEDIC_HOUSES" vs "WESTERN_EQUAL_HOUSES"
    created_at: datetime


@dataclass(frozen=True)
class DistributionShiftAnalysis:
    source_domain_id: str
    target_domain_id: str
    shift_type: DistributionShiftType
    feature_drift_score: float              # 0.0 (no drift) to 1.0 (severe drift)
    outcome_drift_score: float
    baseline_drift_score: float
    is_significant_shift: bool
    details: Dict[str, Any]


@dataclass(frozen=True)
class DomainBoundary:
    boundary_id: str
    dimension_name: str
    valid_range: str
    failure_threshold: str
    degradation_rate: float


@dataclass(frozen=True)
class FailureRegion:
    region_id: str
    region_type: FailureRegionType
    affected_dimension: str
    trigger_condition: str
    severity: str                           # "LOW", "MODERATE", "CRITICAL"


@dataclass(frozen=True)
class GeneralizationMatrixCell:
    source_domain_id: str
    target_domain_id: str
    target_domain_name: str
    status: MatrixCellStatus
    target_metric: float
    target_baseline: float
    baseline_lift: float
    is_baseline_superior: bool


@dataclass(frozen=True)
class TransportabilityAssessment:
    source_domain_id: str
    target_domain_id: str
    status: TransportabilityStatus
    transfer_loss: float                    # metric drop from source to target
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class GeneralizationSnapshot:
    snapshot_id: str
    assessment_id: str
    source_replication_id: str
    methodology_version: str
    canonical_payload_hash: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_GENERALIZATION_NON_CAUSAL_DISCLOSURE


@dataclass(frozen=True)
class GeneralizationAuditEvent:
    audit_event_id: str
    assessment_id: str
    operation: GeneralizationAuditOperation
    actor_type: str
    timestamp: datetime
    details_hash: str
    reason: str


@dataclass(frozen=True)
class GeneralizationAssessment:
    assessment_id: str
    target_objective: str
    source_domain: ExternalDomain
    target_domains: Tuple[ExternalDomain, ...]
    source_replication_id: str
    methodology_version: str
    shift_analyses: Tuple[DistributionShiftAnalysis, ...]
    boundaries: Tuple[DomainBoundary, ...]
    failure_regions: Tuple[FailureRegion, ...]
    matrix_cells: Tuple[GeneralizationMatrixCell, ...]
    transportability: TransportabilityAssessment
    overall_verdict: GeneralizationVerdict
    verdict_explanation: Tuple[str, ...]
    limitations: Tuple[str, ...]
    warnings: Tuple[str, ...]
    generalization_fingerprint: str
    generalization_snapshot_id: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_GENERALIZATION_NON_CAUSAL_DISCLOSURE
