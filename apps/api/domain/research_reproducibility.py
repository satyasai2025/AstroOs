"""
AstroOS — Research Reproducibility & Independent Validation Domain Models (Priority 22)

Defines domain dataclasses for:
  - Immutable Research-Run Manifests (dataset hash, config hash, seeds, engine versions)
  - Reproducibility Drift Classification (REPRODUCED, NUMERICALLY_DRIFTED, LOGIC_DRIFTED, NOT_REPRODUCIBLE)
  - Metric Result-Diff Engine Output (ROC-AUC, Brier, Lift, p-value diffs)
  - Independent Execution Audit Reports & P11 Snapshot DAG Lineage
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple


class ReproducibilityStatus(str, Enum):
    REPRODUCED = "REPRODUCED"
    NUMERICALLY_DRIFTED = "NUMERICALLY_DRIFTED"
    LOGIC_DRIFTED = "LOGIC_DRIFTED"
    NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"


@dataclass(frozen=True)
class ImmutableRunManifest:
    """Tamper-evident frozen execution manifest containing all inputs needed for 100% independent replication."""
    manifest_id: str
    target_engine_priority: str  # e.g., "P15_COHORT", "P19_MINING", "P20_PROSPECTIVE", "P21_BENCHMARK"
    target_objective: str
    dataset_id: str
    dataset_sha256_hash: str
    engine_version: str
    astrological_formula: str
    frozen_thresholds: Dict[str, float]
    random_seed: int
    monte_carlo_iterations: int
    baseline_metrics: Dict[str, float]
    manifest_sha256_hash: str
    created_at: datetime
    parent_lineage_snapshot_id: str
    author: str = "ResearchReproducibilityEngine"


@dataclass(frozen=True)
class MetricDiffItem:
    """Individual metric baseline vs reproduced delta."""
    metric_name: str
    baseline_value: float
    reproduced_value: float
    absolute_delta: float
    is_exact_match: bool


@dataclass(frozen=True)
class IndependentValidationAuditReport:
    """Publication-grade independent execution reproducibility report."""
    audit_id: str
    manifest_id: str
    target_engine_priority: str
    reproduced_at: datetime
    execution_duration_ms: float
    metric_diffs: List[MetricDiffItem]
    status: ReproducibilityStatus
    reproducibility_score_percent: float
    independent_repro_snapshot_id: str
    audit_summary: str
