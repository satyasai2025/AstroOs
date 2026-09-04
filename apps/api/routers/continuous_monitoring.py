"""
AstroOS — Continuous Monitoring API Router

Endpoints for automated benchmark schedules, regression alerts feed,
corpus version discovery, and governance audit history.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from apps.api.domain.continuous_monitoring import (
    AuditEventType,
    MonitoringSchedule,
)
from apps.api.domain.production_governance import RegressionSeverity
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.continuous_monitoring_repository import ContinuousMonitoringRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.continuous_scheduler import ContinuousSchedulerService
from apps.api.services.governance_engine import GovernanceEngine

router = APIRouter(prefix="/api/v1/monitoring", tags=["Continuous Monitoring"])

_mon_repo = ContinuousMonitoringRepository()
_gov_repo = ProductionGovernanceRepository()
_exp_repo = BenchmarkExperimentRepository()
_registry = BenchmarkRegistry()
_runner = BenchmarkRunner()
_gov_engine = GovernanceEngine(
    governance_repo=_gov_repo,
    experiment_repo=_exp_repo,
    registry=_registry,
    runner=_runner,
)
_service = ContinuousSchedulerService(
    monitoring_repo=_mon_repo,
    governance_repo=_gov_repo,
    experiment_repo=_exp_repo,
    registry=_registry,
    runner=_runner,
    governance_engine=_gov_engine,
)


class ScheduleSchema(BaseModel):
    schedule_id: str
    benchmark_id: str
    interval_seconds: int = 86400
    is_active: bool = True
    tolerance_days: int = 30
    split_seed: int = 42
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None


class ScheduleCreateSchema(BaseModel):
    benchmark_id: str
    interval_seconds: int = 86400
    is_active: bool = True
    tolerance_days: int = 30
    split_seed: int = 42


class AlertSchema(BaseModel):
    alert_id: str
    benchmark_id: str
    experiment_id: str
    severity: str
    title: str
    description: str
    metrics_impact: dict[str, float]
    is_acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[str]
    created_at: str


class AcknowledgeRequest(BaseModel):
    reviewer_id: str


class AuditLogSchema(BaseModel):
    audit_id: str
    event_type: str
    benchmark_id: str
    experiment_id: Optional[str]
    actor: str
    details: dict[str, Any]
    timestamp: str


class ContinuousRunResponseSchema(BaseModel):
    schedule_id: str
    benchmark_id: str
    experiment_id: str
    has_regression: bool
    regression_severity: str
    alert_emitted: Optional[AlertSchema]
    significance_verdict: str
    duration_ms: float
    timestamp: str


class CorpusVersionEventSchema(BaseModel):
    benchmark_id: str
    detected_version: str
    previous_version: Optional[str]
    content_hash_sha256: str
    verified_events_count: int
    is_new_version: bool
    detected_at: str


@router.get("/schedules", response_model=list[ScheduleSchema])
async def list_monitoring_schedules() -> list[ScheduleSchema]:
    """Lists all automated continuous benchmark schedules."""
    schedules = await _mon_repo.list_schedules()
    if not schedules:
        # Auto-seed canonical benchmarks
        await _service.run_all_active_schedules()
        schedules = await _mon_repo.list_schedules()

    return [
        ScheduleSchema(
            schedule_id=s.schedule_id,
            benchmark_id=s.benchmark_id,
            interval_seconds=s.interval_seconds,
            is_active=s.is_active,
            tolerance_days=s.tolerance_days,
            split_seed=s.split_seed,
            last_run_at=s.last_run_at.isoformat() if s.last_run_at else None,
            next_run_at=s.next_run_at.isoformat() if s.next_run_at else None,
        )
        for s in schedules
    ]


@router.post("/schedules", response_model=ScheduleSchema)
async def create_or_update_schedule(payload: ScheduleCreateSchema) -> ScheduleSchema:
    """Creates or updates a benchmark monitoring schedule."""
    sched_id = f"SCHED-{payload.benchmark_id}"
    sched = MonitoringSchedule(
        schedule_id=sched_id,
        benchmark_id=payload.benchmark_id,
        interval_seconds=payload.interval_seconds,
        is_active=payload.is_active,
        tolerance_days=payload.tolerance_days,
        split_seed=payload.split_seed,
    )
    saved = await _mon_repo.create_or_update_schedule(sched)
    return ScheduleSchema(
        schedule_id=saved.schedule_id,
        benchmark_id=saved.benchmark_id,
        interval_seconds=saved.interval_seconds,
        is_active=saved.is_active,
        tolerance_days=saved.tolerance_days,
        split_seed=saved.split_seed,
        last_run_at=saved.last_run_at.isoformat() if saved.last_run_at else None,
        next_run_at=saved.next_run_at.isoformat() if saved.next_run_at else None,
    )


@router.post("/schedules/{schedule_id}/trigger", response_model=ContinuousRunResponseSchema)
async def trigger_scheduled_run(schedule_id: str) -> ContinuousRunResponseSchema:
    """Manually triggers immediate execution of a scheduled continuous benchmark."""
    sched = await _mon_repo.get_schedule(schedule_id)
    if not sched:
        b_id = schedule_id.replace("SCHED-", "")
        sched = MonitoringSchedule(
            schedule_id=schedule_id,
            benchmark_id=b_id,
        )

    res = await _service.execute_scheduled_benchmark_run(
        benchmark_id=sched.benchmark_id,
        tolerance_days=sched.tolerance_days,
        seed=sched.split_seed,
        schedule_id=sched.schedule_id,
        actor="HUMAN_ON_DEMAND_TRIGGER",
    )

    alert_dto = (
        AlertSchema(
            alert_id=res.alert_emitted.alert_id,
            benchmark_id=res.alert_emitted.benchmark_id,
            experiment_id=res.alert_emitted.experiment_id,
            severity=res.alert_emitted.severity.value,
            title=res.alert_emitted.title,
            description=res.alert_emitted.description,
            metrics_impact=res.alert_emitted.metrics_impact,
            is_acknowledged=res.alert_emitted.is_acknowledged,
            acknowledged_by=res.alert_emitted.acknowledged_by,
            acknowledged_at=res.alert_emitted.acknowledged_at.isoformat() if res.alert_emitted.acknowledged_at else None,
            created_at=res.alert_emitted.created_at.isoformat(),
        )
        if res.alert_emitted
        else None
    )

    return ContinuousRunResponseSchema(
        schedule_id=res.schedule_id,
        benchmark_id=res.benchmark_id,
        experiment_id=res.experiment_id,
        has_regression=res.has_regression,
        regression_severity=res.regression_severity.value,
        alert_emitted=alert_dto,
        significance_verdict=res.significance_verdict,
        duration_ms=res.duration_ms,
        timestamp=res.timestamp.isoformat(),
    )


@router.post("/corpus/detect-changes", response_model=list[CorpusVersionEventSchema])
async def detect_corpus_changes() -> list[CorpusVersionEventSchema]:
    """Scans canonical corpora on disk, verifies cryptographic hashes, and detects updates."""
    events = await _service.discover_and_detect_corpus_changes()
    return [
        CorpusVersionEventSchema(
            benchmark_id=e.benchmark_id,
            detected_version=e.detected_version,
            previous_version=e.previous_version,
            content_hash_sha256=e.content_hash_sha256,
            verified_events_count=e.verified_events_count,
            is_new_version=e.is_new_version,
            detected_at=e.detected_at.isoformat(),
        )
        for e in events
    ]


@router.get("/alerts", response_model=list[AlertSchema])
async def list_regression_alerts(
    benchmark_id: Optional[str] = Query(None),
    unacknowledged_only: bool = Query(False),
) -> list[AlertSchema]:
    """Lists regression alerts with filtering options."""
    alerts = await _mon_repo.list_alerts(benchmark_id=benchmark_id, unacknowledged_only=unacknowledged_only)
    return [
        AlertSchema(
            alert_id=a.alert_id,
            benchmark_id=a.benchmark_id,
            experiment_id=a.experiment_id,
            severity=a.severity.value,
            title=a.title,
            description=a.description,
            metrics_impact=a.metrics_impact,
            is_acknowledged=a.is_acknowledged,
            acknowledged_by=a.acknowledged_by,
            acknowledged_at=a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            created_at=a.created_at.isoformat(),
        )
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertSchema)
async def acknowledge_regression_alert(alert_id: str, payload: AcknowledgeRequest) -> AlertSchema:
    """Acknowledges a regression alert with reviewer ID."""
    updated = await _mon_repo.acknowledge_alert(alert_id=alert_id, reviewer_id=payload.reviewer_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")

    # Record Acknowledged in Audit Log
    await _mon_repo.record_audit_log(
        GovernanceAuditLogEntry(
            audit_id=f"AUDIT-ACK-{alert_id}",
            event_type=AuditEventType.ALERT_ACKNOWLEDGED,
            benchmark_id=updated.benchmark_id,
            experiment_id=updated.experiment_id,
            actor=payload.reviewer_id,
            details={"alert_id": alert_id},
        )
    )

    return AlertSchema(
        alert_id=updated.alert_id,
        benchmark_id=updated.benchmark_id,
        experiment_id=updated.experiment_id,
        severity=updated.severity.value,
        title=updated.title,
        description=updated.description,
        metrics_impact=updated.metrics_impact,
        is_acknowledged=updated.is_acknowledged,
        acknowledged_by=updated.acknowledged_by,
        acknowledged_at=updated.acknowledged_at.isoformat() if updated.acknowledged_at else None,
        created_at=updated.created_at.isoformat(),
    )


@router.get("/audit-logs", response_model=list[AuditLogSchema])
async def list_governance_audit_logs(
    benchmark_id: Optional[str] = Query(None),
    limit: int = Query(50),
) -> list[AuditLogSchema]:
    """Retrieves recent governance and continuous monitoring audit log entries."""
    logs = await _mon_repo.list_audit_logs(benchmark_id=benchmark_id, limit=limit)
    return [
        AuditLogSchema(
            audit_id=l.audit_id,
            event_type=l.event_type.value if isinstance(l.event_type, AuditEventType) else str(l.event_type),
            benchmark_id=l.benchmark_id,
            experiment_id=l.experiment_id,
            actor=l.actor,
            details=l.details,
            timestamp=l.timestamp.isoformat(),
        )
        for l in logs
    ]