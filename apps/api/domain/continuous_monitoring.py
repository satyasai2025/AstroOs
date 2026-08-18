"""
AstroOS — Continuous Benchmark Monitoring Domain Contracts

Defines contracts for continuous benchmark scheduling, regression alerts,
corpus version discovery events, and governance audit trail logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from apps.api.domain.production_governance import RegressionSeverity


class AuditEventType(str, Enum):
    SCHEDULED_BENCHMARK_RUN = "SCHEDULED_BENCHMARK_RUN"
    CORPUS_VERSION_DETECTED = "CORPUS_VERSION_DETECTED"
    REGRESSION_ALERT_TRIGGERED = "REGRESSION_ALERT_TRIGGERED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    BASELINE_PROMOTION = "BASELINE_PROMOTION"
    HUMAN_SIGNOFF = "HUMAN_SIGNOFF"


@dataclass(frozen=True)
class MonitoringSchedule:
    """Configuration for automated continuous benchmarking runs."""

    schedule_id: str
    benchmark_id: str
    interval_seconds: int = 86400  # Default 24 hours
    is_active: bool = True
    tolerance_days: int = 30
    split_seed: int = 42
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class RegressionAlert:
    """Prioritized alert emitted when automated regression checks detect degradation."""

    alert_id: str
    benchmark_id: str
    experiment_id: str
    severity: RegressionSeverity
    title: str
    description: str
    metrics_impact: dict[str, float]
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CorpusVersionEvent:
    """Event emitted when a new or updated benchmark corpus dataset is detected."""

    benchmark_id: str
    detected_version: str
    previous_version: Optional[str]
    content_hash_sha256: str
    verified_events_count: int
    is_new_version: bool
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class GovernanceAuditLogEntry:
    """Immutable audit record of system monitoring actions and human governance decisions."""

    audit_id: str
    event_type: AuditEventType
    benchmark_id: str
    experiment_id: Optional[str]
    actor: str                     # e.g. "CONTINUOUS_SCHEDULER_DAEMON" or user/reviewer ID
    details: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ContinuousRunResult:
    """Aggregated outcome of an automated continuous benchmark execution."""

    schedule_id: str
    benchmark_id: str
    experiment_id: str
    has_regression: bool
    regression_severity: RegressionSeverity
    alert_emitted: Optional[RegressionAlert]
    significance_verdict: str
    duration_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))