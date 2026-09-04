"""
AstroOS — Priority 11: Scientific Experiment Lineage & Snapshot Domain Contract
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Optional


@dataclass(frozen=True)
class DatasetProvenanceSnapshot:
    """Dataset version and SHA-256 hash provenance."""

    dataset_id: str
    dataset_version: str
    sha256_hash: str
    record_count: int
    temporal_start: Optional[date] = None
    temporal_end: Optional[date] = None


@dataclass(frozen=True)
class TechniqueProvenanceSnapshot:
    """AstroDSL and classical technique definitions and combined hash provenance."""

    dsl_rule_ids: tuple[str, ...]
    dsl_hashes: tuple[str, ...]
    classical_techniques: tuple[str, ...]
    combined_sha256_hash: str


@dataclass(frozen=True)
class CalibrationProvenanceSnapshot:
    """Calibration profile weights and hash provenance."""

    profile_id: str
    status: str  # DRAFT_CANDIDATE or ACTIVE
    technique_weights: dict[str, float]
    primary_brier_score: float
    primary_log_loss: float
    sha256_hash: str


@dataclass(frozen=True)
class OrchestratorConfigSnapshot:
    """PredictionOrchestrator configuration snapshot."""

    consensus_profile_id: str
    minimum_activation_threshold: int
    conflict_penalty_multiplier: float


@dataclass(frozen=True)
class ExperimentMetrics:
    """Empirical research metrics snapshot."""

    brier_score: float
    log_loss: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: Optional[float]
    roc_auc_status: str  # VALID, DEGENERATE_SINGLE_CLASS, UNIFORM_PREDICTIONS
    sample_size_n: int
    hit_rate: float


@dataclass(frozen=True)
class ExperimentSnapshot:
    """Immutable, reproducible experiment snapshot."""

    snapshot_id: str
    experiment_id: str
    parent_snapshot_id: Optional[str]
    timestamp: datetime
    schema_version: str
    dataset: DatasetProvenanceSnapshot
    techniques: TechniqueProvenanceSnapshot
    calibration: CalibrationProvenanceSnapshot
    orchestrator: OrchestratorConfigSnapshot
    metrics: ExperimentMetrics
    execution_params: dict[str, Any]
    snapshot_sha256_hash: str

    @staticmethod
    def compute_sha256(
        experiment_id: str,
        dataset: DatasetProvenanceSnapshot,
        techniques: TechniqueProvenanceSnapshot,
        calibration: CalibrationProvenanceSnapshot,
        metrics: ExperimentMetrics,
    ) -> str:
        """Computes deterministic SHA-256 payload hash for tamper verification."""
        payload = {
            "experiment_id": experiment_id,
            "dataset_hash": dataset.sha256_hash,
            "techniques_hash": techniques.combined_sha256_hash,
            "calibration_hash": calibration.sha256_hash,
            "brier": metrics.brier_score,
            "log_loss": metrics.log_loss,
        }
        raw_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw_str.encode()).hexdigest()


@dataclass(frozen=True)
class ExperimentMetadata:
    """Research experiment metadata."""

    experiment_id: str
    name: str
    description: str
    author: str
    created_at: datetime
    status: str = "ACTIVE"  # ACTIVE, ARCHIVED, FROZEN
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ExperimentLineage:
    """Lineage DAG representation of an experiment over time."""

    experiment_id: str
    snapshots: tuple[ExperimentSnapshot, ...]
    dag_edges: tuple[tuple[str, str], ...]  # (parent_snapshot_id, child_snapshot_id)


@dataclass(frozen=True)
class MetricDelta:
    """Metric comparison delta between two experiments/snapshots."""

    metric_name: str
    exp1_value: Any
    exp2_value: Any
    absolute_delta: Optional[float]
    percentage_delta: Optional[float]
    improvement_status: str  # IMPROVED, DEGRADED, UNCHANGED, NOT_APPLICABLE


@dataclass(frozen=True)
class ExperimentDiffResult:
    """Side-by-side comparative diff between two experiments/snapshots."""

    exp1_id: str
    exp2_id: str
    snapshot1_id: str
    snapshot2_id: str
    metric_deltas: tuple[MetricDelta, ...]
    dataset_changed: bool
    rules_changed: bool
    weights_changed: bool
    summary: str
