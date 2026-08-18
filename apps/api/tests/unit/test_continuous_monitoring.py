"""
AstroOS — Continuous Benchmark Scheduler & Regression Monitoring Test Suite

Proves:
  1. Automated scheduled benchmark execution & active baseline regression checks.
  2. Corpus version discovery & cryptographic hash watcher.
  3. Regression alert dispatch, triage, and acknowledgement workflows.
  4. Immutable governance audit log timeline.
  5. Cardinal Invariance Guarantee: TechniqueEngine and PredictionOrchestrator remain 100% untouched.
"""

from datetime import date, datetime
import importlib
import pytest

from apps.api.domain.continuous_monitoring import (
    AuditEventType,
    GovernanceAuditLogEntry,
    MonitoringSchedule,
    RegressionAlert,
)
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.production_governance import RegressionSeverity
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.continuous_monitoring_repository import ContinuousMonitoringRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.continuous_scheduler import ContinuousSchedulerService
from apps.api.services.governance_engine import GovernanceEngine
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()
    BenchmarkExperimentRepository.clear_in_memory()
    ProductionGovernanceRepository.clear_in_memory()
    ContinuousMonitoringRepository.clear_in_memory()

    import apps.api.services.techniques.timing_events as _te
    import apps.api.services.techniques.panch_mahapurusha as _pm
    import apps.api.services.techniques.marriage_timing as _mt
    import apps.api.services.techniques.wealth_dhana as _wd
    import apps.api.services.techniques.gajakesari_yoga as _gj
    import apps.api.services.techniques.eye_health as _eye
    import apps.api.services.techniques.event_timing_migrated as _et

    importlib.reload(_te)
    importlib.reload(_pm)
    importlib.reload(_mt)
    importlib.reload(_wd)
    importlib.reload(_gj)
    importlib.reload(_eye)
    importlib.reload(_et)
    yield


# ── 1. Continuous Scheduled Benchmark Execution ───────────────────────────────


@pytest.mark.asyncio
async def test_scheduled_benchmark_execution():
    """ContinuousSchedulerService executes automated runs, updates schedules, and logs audits."""
    service = ContinuousSchedulerService()
    benchmark_id = "BENCH-CAREER-001"

    result = await service.execute_scheduled_benchmark_run(
        benchmark_id=benchmark_id,
        tolerance_days=30,
        seed=42,
    )

    assert result.benchmark_id == benchmark_id
    assert result.experiment_id.startswith("EXP-")
    assert result.duration_ms > 0
    assert not result.has_regression  # Clean baseline comparison

    # Verify schedule updated
    sched = await ContinuousMonitoringRepository().get_schedule(f"SCHED-{benchmark_id}")
    assert sched is not None
    assert sched.last_run_at is not None
    assert sched.next_run_at is not None


# ── 2. Corpus Version Discovery & Watcher ──────────────────────────────────────


@pytest.mark.asyncio
async def test_corpus_version_discovery():
    """ContinuousSchedulerService scans canonical corpora and emits detection audit events."""
    service = ContinuousSchedulerService()
    events = await service.discover_and_detect_corpus_changes()

    assert len(events) >= 4
    b_ids = {e.benchmark_id for e in events}
    assert "BENCH-CAREER-001" in b_ids
    assert "BENCH-MARRIAGE-001" in b_ids
    assert "BENCH-WEALTH-001" in b_ids
    assert "BENCH-TRANSIT-001" in b_ids

    # Verify audit logs created
    audit_logs = await ContinuousMonitoringRepository().list_audit_logs(benchmark_id="BENCH-CAREER-001")
    corpus_logs = [l for l in audit_logs if l.event_type == AuditEventType.CORPUS_VERSION_DETECTED]
    assert len(corpus_logs) > 0


# ── 3. Regression Alerts & Triage Workflow ────────────────────────────────────


@pytest.mark.asyncio
async def test_regression_alert_dispatch_and_acknowledgement():
    """Alerts are recorded on regression and can be acknowledged by reviewers."""
    repo = ContinuousMonitoringRepository()
    alert_id = "ALERT-TEST-001"

    alert = RegressionAlert(
        alert_id=alert_id,
        benchmark_id="BENCH-CAREER-001",
        experiment_id="EXP-REG-001",
        severity=RegressionSeverity.CRITICAL_REGRESSION,
        title="Critical Regression Detected",
        description="Holdout Hit Rate dropped by 12.5% below baseline.",
        metrics_impact={"hit_rate_drop_pct": 12.5, "brier_increase": 0.04},
    )

    saved = await repo.record_alert(alert)
    assert not saved.is_acknowledged

    # Verify list unacknowledged
    unack = await repo.list_alerts(unacknowledged_only=True)
    assert any(a.alert_id == alert_id for a in unack)

    # Acknowledge alert
    ack = await repo.acknowledge_alert(alert_id, reviewer_id="Senior Astrologer Reviewer")
    assert ack is not None
    assert ack.is_acknowledged
    assert ack.acknowledged_by == "Senior Astrologer Reviewer"

    # Verify filtered out of unacknowledged
    unack_after = await repo.list_alerts(unacknowledged_only=True)
    assert not any(a.alert_id == alert_id for a in unack_after)


# ── 4. Governance Audit Log Timeline ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_governance_audit_timeline():
    """Audit repository records and returns chronological event timeline."""
    repo = ContinuousMonitoringRepository()
    entry = GovernanceAuditLogEntry(
        audit_id="AUDIT-TEST-001",
        event_type=AuditEventType.BASELINE_PROMOTION,
        benchmark_id="BENCH-CAREER-001",
        experiment_id="EXP-PROMOTE-001",
        actor="Lead Reviewer",
        details={"promoted_version": "1.1.0"},
    )
    await repo.record_audit_log(entry)

    logs = await repo.list_audit_logs(benchmark_id="BENCH-CAREER-001")
    assert len(logs) > 0
    assert logs[0].audit_id == "AUDIT-TEST-001"
    assert logs[0].actor == "Lead Reviewer"


# ── 5. Cardinal Invariance Guarantee ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_continuous_monitoring_leaves_deterministic_engines_untouched():
    """Asserts bit-for-bit invariance of TechniqueEngine and PredictionOrchestrator."""
    from apps.api.tests.unit.test_prediction_orchestration import _build_test_chart, _build_test_dasha_tree

    chart = _build_test_chart(tenth_lord_house=10)
    dasha_tree = _build_test_dasha_tree()

    orchestrator = PredictionOrchestrator()
    start_d = date(2026, 1, 1)
    end_d = date(2027, 1, 1)

    res_before = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    # Run continuous monitoring schedule run
    service = ContinuousSchedulerService()
    _ = await service.execute_scheduled_benchmark_run("BENCH-CAREER-001", tolerance_days=30, seed=42)

    res_after = orchestrator.predict_event_windows(chart, dasha_tree, "career", start_d, end_d, PARASHARI_STANDARD_PROFILE)

    assert res_before.deterministic_signature == res_after.deterministic_signature
    assert len(res_before.candidate_windows) == len(res_after.candidate_windows)
    for c1, c2 in zip(res_before.candidate_windows, res_after.candidate_windows):
        assert c1.peak_score == c2.peak_score
        assert c1.deterministic_hash == c2.deterministic_hash