"""
AstroOS — Research Reproducibility, Replication & Falsification Domain Models (Priority 34)

Defines domain dataclasses, enums, conservative precedence verdict logic,
falsification experiment models, replication protocols, stress test structures,
and non-causal disclosures for Priority 34.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

MANDATORY_REPLICATION_NON_CAUSAL_DISCLOSURE = (
    "RESEARCH_REPLICATION_DISCLOSURE: Successful replication strengthens the evidentiary record "
    "and verifies computational reproducibility, but does not establish astrological causation, "
    "predictive validity, or a physical mechanism."
)

REPLICATION_METHODOLOGY_VERSION = "P34-METHODOLOGY-1.0"


class ReproductionStatus(str, Enum):
    REPRODUCED_EXACTLY = "REPRODUCED_EXACTLY"
    REPRODUCED_WITH_TOLERANCE = "REPRODUCED_WITH_TOLERANCE"
    REPRODUCTION_DRIFT = "REPRODUCTION_DRIFT"
    REPRODUCTION_FAILED = "REPRODUCTION_FAILED"
    REPRODUCTION_NOT_COMPUTABLE = "REPRODUCTION_NOT_COMPUTABLE"


class DatasetIndependenceStatus(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    PARTIALLY_OVERLAPPING = "PARTIALLY_OVERLAPPING"
    DEPENDENT = "DEPENDENT"
    UNKNOWN = "UNKNOWN"


class ReplicationVerdict(str, Enum):
    SUCCESSFUL_REPLICATION = "SUCCESSFUL_REPLICATION"
    PARTIAL_REPLICATION = "PARTIAL_REPLICATION"
    FAILED_REPLICATION = "FAILED_REPLICATION"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_REPLICABLE = "NOT_REPLICABLE"
    INVALID_REPLICATION = "INVALID_REPLICATION"


class FalsificationResult(str, Enum):
    CLAIM_SURVIVED_TESTS = "CLAIM_SURVIVED_TESTS"
    CLAIM_WEAKENED = "CLAIM_WEAKENED"
    CLAIM_CONTRADICTED = "CLAIM_CONTRADICTED"
    CLAIM_FALSIFIED = "CLAIM_FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class NegativeControlStatus(str, Enum):
    NEGATIVE_CONTROL_PASSED = "NEGATIVE_CONTROL_PASSED"
    NEGATIVE_CONTROL_FAILED = "NEGATIVE_CONTROL_FAILED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_DEFINED = "NOT_DEFINED"


class ProtocolStatus(str, Enum):
    DRAFT = "DRAFT"
    FROZEN = "FROZEN"
    EXECUTED = "EXECUTED"
    SUPERSEDED = "SUPERSEDED"


class ParameterSensitivityStatus(str, Enum):
    STABLE = "STABLE"
    MODERATELY_SENSITIVE = "MODERATELY_SENSITIVE"
    HIGHLY_SENSITIVE = "HIGHLY_SENSITIVE"
    UNSTABLE = "UNSTABLE"


class TemporalStabilityStatus(str, Enum):
    TEMPORALLY_STABLE = "TEMPORALLY_STABLE"
    TEMPORALLY_VARIABLE = "TEMPORALLY_VARIABLE"
    TEMPORALLY_UNSTABLE = "TEMPORALLY_UNSTABLE"


class EffectDirectionStatus(str, Enum):
    CONSISTENT_DIRECTION = "CONSISTENT_DIRECTION"
    MIXED_DIRECTION = "MIXED_DIRECTION"
    REVERSED_DIRECTION = "REVERSED_DIRECTION"


class ReplicationAuditOperation(str, Enum):
    CLAIM_CREATED = "CLAIM_CREATED"
    CLAIM_VERSIONED = "CLAIM_VERSIONED"
    PROTOCOL_CREATED = "PROTOCOL_CREATED"
    PROTOCOL_FROZEN = "PROTOCOL_FROZEN"
    REPRODUCTION_STARTED = "REPRODUCTION_STARTED"
    REPRODUCTION_COMPLETED = "REPRODUCTION_COMPLETED"
    REPLICATION_CREATED = "REPLICATION_CREATED"
    REPLICATION_COMPLETED = "REPLICATION_COMPLETED"
    FALSIFICATION_STARTED = "FALSIFICATION_STARTED"
    FALSIFICATION_COMPLETED = "FALSIFICATION_COMPLETED"
    STRESS_TEST_COMPLETED = "STRESS_TEST_COMPLETED"
    VERDICT_GENERATED = "VERDICT_GENERATED"
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    ASSESSMENT_SUPERSEDED = "ASSESSMENT_SUPERSEDED"


@dataclass(frozen=True)
class ResearchClaim:
    claim_id: str
    claim_version: str                       # e.g., "v1.0"
    research_question: str
    hypothesis: str
    predictor_definition: str
    outcome_definition: str
    population_definition: str
    evaluation_metric: str
    baseline_definition: str
    original_assessment_id: str
    created_at: datetime
    claim_hash: str


@dataclass(frozen=True)
class ReplicationProtocol:
    protocol_id: str
    claim_id: str
    claim_version: str
    dataset_requirements: str
    inclusion_criteria: Tuple[str, ...]
    exclusion_criteria: Tuple[str, ...]
    predictors: Tuple[str, ...]
    outcome: str
    statistical_methodology: str
    baseline_definition: str
    replication_metric: str
    stopping_conditions: str
    falsification_criteria: Tuple[str, ...]
    methodology_version: str
    status: ProtocolStatus
    created_at: datetime
    protocol_hash: str


@dataclass(frozen=True)
class ReproductionAssessment:
    assessment_id: str
    source_validity_assessment_id: str
    source_snapshot_id: str
    source_manifest_id: str
    methodology_version: str
    software_version: str
    analysis_definition_hash: str
    input_fingerprint: str
    output_fingerprint: str
    expected_metrics: Dict[str, float]
    reproduced_metrics: Dict[str, float]
    metric_deltas: Dict[str, float]
    reproduction_status: ReproductionStatus
    created_at: datetime


@dataclass(frozen=True)
class ReplicationDatasetManifest:
    dataset_id: str
    source_snapshot_id: str
    evidence_count: int
    usable_count: int
    excluded_count: int
    prospective_count: int
    retrospective_count: int
    verification_distribution: Dict[str, int]
    outcome_distribution: Dict[str, int]
    time_range: str
    geographic_scope: str
    population_scope: str
    dataset_fingerprint: str
    independence_status: DatasetIndependenceStatus


@dataclass(frozen=True)
class NegativeControlResult:
    status: NegativeControlStatus
    control_target: str
    observed_effect: float
    expected_effect: float
    reason: str


@dataclass(frozen=True)
class NullModelResult:
    null_model_type: str                     # e.g., "LABEL_PERMUTATION"
    iterations: int
    seed: int
    observed_metric: float
    mean_null_metric: float
    median_null_metric: float
    null_percentile: float
    p_value: float
    extreme_count: int


@dataclass(frozen=True)
class SensitivityVariantResult:
    variant_name: str
    variant_definition: str
    variant_result: float
    metric_delta: float
    verdict_changed: bool


@dataclass(frozen=True)
class FalsificationExperiment:
    experiment_id: str
    claim_id: str
    negative_control: NegativeControlResult
    null_model: NullModelResult
    sensitivity_variants: Tuple[SensitivityVariantResult, ...]
    falsification_result: FalsificationResult
    tests_passed: Tuple[str, ...]
    tests_failed: Tuple[str, ...]
    created_at: datetime


@dataclass(frozen=True)
class StressTestResults:
    test_id: str
    parameter_sensitivity: ParameterSensitivityStatus
    subgroup_stability: str                 # e.g., "STABLE"
    temporal_stability: TemporalStabilityStatus
    dataset_stability: str                  # e.g., "STABLE"
    metric_stability: str                   # e.g., "STABLE"
    effect_direction: EffectDirectionStatus
    details: Dict[str, Any]


@dataclass(frozen=True)
class ReplicationSnapshot:
    snapshot_id: str
    claim_id: str
    protocol_id: str
    source_assessment_id: str
    replication_manifest_id: str
    falsification_results: Dict[str, Any]
    stress_test_results: Dict[str, Any]
    verdict: ReplicationVerdict
    methodology_version: str
    canonical_payload_hash: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_REPLICATION_NON_CAUSAL_DISCLOSURE


@dataclass(frozen=True)
class ReplicationAuditEvent:
    audit_event_id: str
    replication_id: str
    operation: ReplicationAuditOperation
    actor_type: str
    timestamp: datetime
    details_hash: str
    reason: str


@dataclass(frozen=True)
class ReplicationStudyAssessment:
    replication_id: str
    claim: ResearchClaim
    protocol: ReplicationProtocol
    reproduction: ReproductionAssessment
    replication_dataset: ReplicationDatasetManifest
    falsification: FalsificationExperiment
    stress_tests: StressTestResults
    original_metric: float
    replication_metric: float
    absolute_delta: float
    relative_delta: float
    baseline_delta: float
    overall_verdict: ReplicationVerdict
    verdict_explanation: Tuple[str, ...]
    limitations: Tuple[str, ...]
    warnings: Tuple[str, ...]
    replication_fingerprint: str
    replication_snapshot_id: str
    created_at: datetime
    non_causal_disclosure: str = MANDATORY_REPLICATION_NON_CAUSAL_DISCLOSURE
