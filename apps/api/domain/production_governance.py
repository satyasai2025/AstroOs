"""
AstroOS — Production Governance & Continuous Benchmarking Domain Contracts

Defines domain contracts for production profile versioning, automated regression detection,
cryptographic reproducibility audits, and human reviewer sign-off workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class SignoffStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class RegressionSeverity(str, Enum):
    NONE = "NONE"
    WARNING = "WARNING"
    CRITICAL_REGRESSION = "CRITICAL_REGRESSION"


@dataclass(frozen=True)
class ProductionProfileVersion:
    """A versioned production consensus profile release."""

    profile_id: str
    version: str                   # e.g. "1.0.0", "1.1.0"
    benchmark_id: str
    is_active_baseline: bool
    promoted_from_experiment_id: Optional[str] = None
    approved_by: Optional[str] = None
    promoted_at: Optional[datetime] = None
    notes: Optional[str] = None
    config_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentSignoff:
    """Formal audit trail record of a human reviewer evaluating a benchmark experiment."""

    signoff_id: str
    experiment_id: str
    status: SignoffStatus
    reviewer_id: str
    notes: str
    signed_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True)
class RegressionReport:
    """Comparative regression analysis between a candidate run and the active production baseline."""

    baseline_experiment_id: str
    candidate_experiment_id: str
    has_regression: bool
    hit_rate_drop_pct: float       # Positive value indicates drop in hit rate (e.g. 5.0%)
    brier_increase: float          # Positive value indicates increase in error (e.g. 0.03)
    mae_increase_days: float       # Positive value indicates increase in timing offset
    reasons: tuple[str, ...]
    severity: RegressionSeverity


@dataclass(frozen=True)
class ReproducibilityAudit:
    """Cryptographic verification audit checking if an experiment re-run produces bit-for-bit results."""

    experiment_id: str
    is_bit_for_bit_identical: bool
    expected_results_hash: str
    actual_results_hash: str
    verified_at: datetime = field(default_factory=lambda: datetime.now())
    audit_notes: str = ""