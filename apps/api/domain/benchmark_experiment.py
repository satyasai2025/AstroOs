"""
AstroOS — Benchmark Experiment Domain Contract

Defines domain models for immutable benchmark versioning, locked dataset splits,
baseline comparisons, and full experiment provenance for scientific reproducibility.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from apps.api.domain.benchmark_dataset import (
    BenchmarkComparisonReport,
    BenchmarkProfileComparisonRow,
)
from apps.api.domain.statistical_testing import ProfileSignificanceReport


@dataclass(frozen=True)
class BenchmarkVersion:
    """An immutable versioned release of a benchmark problem dataset."""

    benchmark_id: str
    version: str
    content_hash_sha256: str
    total_events: int
    locked_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class LockedDatasetSplit:
    """Deterministic partition of an immutable benchmark into Train and Holdout IDs."""

    benchmark_id: str
    version: str
    content_hash_sha256: str
    split_seed: int
    train_ratio: float
    train_event_ids: tuple[str, ...]
    holdout_event_ids: tuple[str, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class BaselineComparison:
    """Relative performance improvement of a profile against a baseline profile."""

    profile_id: str
    baseline_profile_id: str
    delta_hit_rate_pct: float     # profile_hit_rate - baseline_hit_rate
    delta_brier_score: float      # profile_brier - baseline_brier (lower is better)
    delta_f1_score: float         # profile_f1 - baseline_f1
    delta_mae_peak_days: float    # profile_mae - baseline_mae
    is_statistically_superior: bool
    p_value: float = 1.0
    odds_ratio: float = 1.0
    verdict: str = "EQUIVALENT_OR_INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ExperimentProvenance:
    """Full scientific reproducibility metadata for a benchmark experiment run."""

    experiment_id: str
    benchmark_id: str
    benchmark_version: str
    content_hash_sha256: str
    split_seed: int
    train_ratio: float
    tolerance_days: int
    profile_ids: tuple[str, ...]
    calibration_method: str
    software_version: str
    timestamp: datetime
    results_hash: str


@dataclass(frozen=True)
class BenchmarkExperiment:
    """Complete record of an executed benchmark experiment with baseline comparisons."""

    provenance: ExperimentProvenance
    split: LockedDatasetSplit
    report: BenchmarkComparisonReport
    baseline_comparisons: tuple[BaselineComparison, ...] = field(default_factory=tuple)
    significance_reports: tuple[ProfileSignificanceReport, ...] = field(default_factory=tuple)

    @staticmethod
    def compute_results_hash(report: BenchmarkComparisonReport) -> str:
        """Computes deterministic SHA-256 hash of the comparison rows."""
        summary = [
            {
                "profile_id": r.profile_id,
                "hit_rate": r.holdout_hit_rate_pct,
                "brier": r.holdout_brier_score,
                "f1": r.holdout_f1_score,
                "mae": r.holdout_mae_peak_days,
            }
            for r in report.rows
        ]
        raw_bytes = json.dumps(summary, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()