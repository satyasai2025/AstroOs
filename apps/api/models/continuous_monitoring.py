"""
AstroOS — Continuous Monitoring SQLAlchemy ORM Models

Defines persistence schema for benchmark schedules, regression alerts, and governance audit logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class MonitoringScheduleModel(AstroBase):
    """Stores automated benchmark execution schedules."""

    __tablename__ = "monitoring_schedules"

    schedule_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=86400)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    tolerance_days: Mapped[int] = mapped_column(Integer, default=30)
    split_seed: Mapped[int] = mapped_column(Integer, default=42)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class RegressionAlertModel(AstroBase):
    """Stores prioritized regression alerts raised during automated benchmarking."""

    __tablename__ = "regression_alerts"

    alert_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    experiment_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_impact: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GovernanceAuditLogModel(AstroBase):
    """Stores immutable audit log records of continuous evaluations and governance actions."""

    __tablename__ = "governance_audit_logs"

    audit_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    benchmark_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    experiment_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)