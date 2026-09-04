"""
AstroOS — Continuous Monitoring Repository

Data access layer for monitoring schedules, regression alerts, and governance audit logs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.continuous_monitoring import (
    AuditEventType,
    GovernanceAuditLogEntry,
    MonitoringSchedule,
    RegressionAlert,
)
from apps.api.domain.production_governance import RegressionSeverity
from apps.api.models.continuous_monitoring import (
    GovernanceAuditLogModel,
    MonitoringScheduleModel,
    RegressionAlertModel,
)


class ContinuousMonitoringRepository:
    """Repository managing continuous schedules, regression alerts, and audit logs."""

    _in_memory_schedules: dict[str, MonitoringSchedule] = {}
    _in_memory_alerts: dict[str, RegressionAlert] = {}
    _in_memory_audit_logs: list[GovernanceAuditLogEntry] = []

    def __init__(self, session: Optional[AsyncSession] = None) -> None:
        self._session = session

    @classmethod
    def clear_in_memory(cls) -> None:
        cls._in_memory_schedules.clear()
        cls._in_memory_alerts.clear()
        cls._in_memory_audit_logs.clear()

    async def create_or_update_schedule(self, schedule: MonitoringSchedule) -> MonitoringSchedule:
        """Saves or updates a benchmark monitoring schedule."""
        if self._session is not None:
            stmt = select(MonitoringScheduleModel).where(
                MonitoringScheduleModel.schedule_id == schedule.schedule_id
            )
            res = await self._session.execute(stmt)
            model = res.scalar_one_or_none()

            if model:
                model.interval_seconds = schedule.interval_seconds
                model.is_active = schedule.is_active
                model.tolerance_days = schedule.tolerance_days
                model.split_seed = schedule.split_seed
                model.last_run_at = schedule.last_run_at
                model.next_run_at = schedule.next_run_at
            else:
                model = MonitoringScheduleModel(
                    schedule_id=schedule.schedule_id,
                    benchmark_id=schedule.benchmark_id,
                    interval_seconds=schedule.interval_seconds,
                    is_active=schedule.is_active,
                    tolerance_days=schedule.tolerance_days,
                    split_seed=schedule.split_seed,
                    last_run_at=schedule.last_run_at,
                    next_run_at=schedule.next_run_at,
                )
                self._session.add(model)
            await self._session.flush()

        self._in_memory_schedules[schedule.schedule_id] = schedule
        return schedule

    async def get_schedule(self, schedule_id: str) -> Optional[MonitoringSchedule]:
        """Retrieves a schedule by ID."""
        if self._session is not None:
            stmt = select(MonitoringScheduleModel).where(
                MonitoringScheduleModel.schedule_id == schedule_id
            )
            res = await self._session.execute(stmt)
            model = res.scalar_one_or_none()
            if model:
                return MonitoringSchedule(
                    schedule_id=model.schedule_id,
                    benchmark_id=model.benchmark_id,
                    interval_seconds=model.interval_seconds,
                    is_active=model.is_active,
                    tolerance_days=model.tolerance_days,
                    split_seed=model.split_seed,
                    last_run_at=model.last_run_at,
                    next_run_at=model.next_run_at,
                )

        return self._in_memory_schedules.get(schedule_id)

    async def list_schedules(self) -> list[MonitoringSchedule]:
        """Lists all active and inactive benchmark schedules."""
        if self._session is not None:
            stmt = select(MonitoringScheduleModel).order_by(MonitoringScheduleModel.benchmark_id)
            res = await self._session.execute(stmt)
            models = res.scalars().all()
            if models:
                return [
                    MonitoringSchedule(
                        schedule_id=m.schedule_id,
                        benchmark_id=m.benchmark_id,
                        interval_seconds=m.interval_seconds,
                        is_active=m.is_active,
                        tolerance_days=m.tolerance_days,
                        split_seed=m.split_seed,
                        last_run_at=m.last_run_at,
                        next_run_at=m.next_run_at,
                    )
                    for m in models
                ]

        return list(self._in_memory_schedules.values())

    async def record_alert(self, alert: RegressionAlert) -> RegressionAlert:
        """Records a new regression alert."""
        if self._session is not None:
            model = RegressionAlertModel(
                alert_id=alert.alert_id,
                benchmark_id=alert.benchmark_id,
                experiment_id=alert.experiment_id,
                severity=alert.severity.value,
                title=alert.title,
                description=alert.description,
                metrics_impact=alert.metrics_impact,
                is_acknowledged=alert.is_acknowledged,
                acknowledged_by=alert.acknowledged_by,
                acknowledged_at=alert.acknowledged_at,
            )
            self._session.add(model)
            await self._session.flush()

        self._in_memory_alerts[alert.alert_id] = alert
        return alert

    async def list_alerts(
        self,
        benchmark_id: Optional[str] = None,
        unacknowledged_only: bool = False,
    ) -> list[RegressionAlert]:
        """Lists alerts with optional filtering."""
        if self._session is not None:
            stmt = select(RegressionAlertModel)
            if benchmark_id:
                stmt = stmt.where(RegressionAlertModel.benchmark_id == benchmark_id)
            if unacknowledged_only:
                stmt = stmt.where(RegressionAlertModel.is_acknowledged.is_(False))
            stmt = stmt.order_by(RegressionAlertModel.created_at.desc())
            res = await self._session.execute(stmt)
            models = res.scalars().all()
            if models:
                return [
                    RegressionAlert(
                        alert_id=m.alert_id,
                        benchmark_id=m.benchmark_id,
                        experiment_id=m.experiment_id,
                        severity=RegressionSeverity(m.severity),
                        title=m.title,
                        description=m.description,
                        metrics_impact=m.metrics_impact,
                        is_acknowledged=m.is_acknowledged,
                        acknowledged_by=m.acknowledged_by,
                        acknowledged_at=m.acknowledged_at,
                        created_at=m.created_at,
                    )
                    for m in models
                ]

        alerts = list(self._in_memory_alerts.values())
        if benchmark_id:
            alerts = [a for a in alerts if a.benchmark_id == benchmark_id]
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.is_acknowledged]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    async def acknowledge_alert(self, alert_id: str, reviewer_id: str) -> Optional[RegressionAlert]:
        """Marks a regression alert as acknowledged."""
        now = datetime.now(timezone.utc)
        if self._session is not None:
            stmt = select(RegressionAlertModel).where(RegressionAlertModel.alert_id == alert_id)
            res = await self._session.execute(stmt)
            model = res.scalar_one_or_none()
            if model:
                model.is_acknowledged = True
                model.acknowledged_by = reviewer_id
                model.acknowledged_at = now
                await self._session.flush()

        if alert_id in self._in_memory_alerts:
            orig = self._in_memory_alerts[alert_id]
            updated = RegressionAlert(
                alert_id=orig.alert_id,
                benchmark_id=orig.benchmark_id,
                experiment_id=orig.experiment_id,
                severity=orig.severity,
                title=orig.title,
                description=orig.description,
                metrics_impact=orig.metrics_impact,
                is_acknowledged=True,
                acknowledged_by=reviewer_id,
                acknowledged_at=now,
                created_at=orig.created_at,
            )
            self._in_memory_alerts[alert_id] = updated
            return updated
        return None

    async def record_audit_log(self, entry: GovernanceAuditLogEntry) -> GovernanceAuditLogEntry:
        """Records an immutable entry in the governance audit timeline."""
        if self._session is not None:
            model = GovernanceAuditLogModel(
                audit_id=entry.audit_id,
                event_type=entry.event_type.value if isinstance(entry.event_type, AuditEventType) else str(entry.event_type),
                benchmark_id=entry.benchmark_id,
                experiment_id=entry.experiment_id,
                actor=entry.actor,
                details=entry.details,
                timestamp=entry.timestamp,
            )
            self._session.add(model)
            await self._session.flush()

        self._in_memory_audit_logs.append(entry)
        return entry

    async def list_audit_logs(
        self,
        benchmark_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[GovernanceAuditLogEntry]:
        """Lists recent governance audit log entries."""
        if self._session is not None:
            stmt = select(GovernanceAuditLogModel)
            if benchmark_id:
                stmt = stmt.where(GovernanceAuditLogModel.benchmark_id == benchmark_id)
            stmt = stmt.order_by(GovernanceAuditLogModel.timestamp.desc()).limit(limit)
            res = await self._session.execute(stmt)
            models = res.scalars().all()
            if models:
                return [
                    GovernanceAuditLogEntry(
                        audit_id=m.audit_id,
                        event_type=AuditEventType(m.event_type),
                        benchmark_id=m.benchmark_id,
                        experiment_id=m.experiment_id,
                        actor=m.actor,
                        details=m.details,
                        timestamp=m.timestamp,
                    )
                    for m in models
                ]

        logs = self._in_memory_audit_logs
        if benchmark_id:
            logs = [l for l in logs if l.benchmark_id == benchmark_id]
        return sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]