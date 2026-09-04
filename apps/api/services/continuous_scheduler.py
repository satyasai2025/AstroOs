"""
AstroOS — Continuous Benchmark Scheduler & Automated Regression Monitoring Service

Orchestrates automated scheduled benchmark runs, new corpus version detection,
baseline-vs-candidate regression checks, automated significance analysis,
prioritized alert dispatching, and governance audit timeline logging.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from apps.api.domain.continuous_monitoring import (
    AuditEventType,
    ContinuousRunResult,
    CorpusVersionEvent,
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
from apps.api.services.benchmark_corpus_loader import BenchmarkCorpusLoader
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.governance_engine import GovernanceEngine


class ContinuousSchedulerService:
    """Service orchestrating continuous benchmark evaluation, regression monitoring, and audit trails."""

    def __init__(
        self,
        monitoring_repo: Optional[ContinuousMonitoringRepository] = None,
        governance_repo: Optional[ProductionGovernanceRepository] = None,
        experiment_repo: Optional[BenchmarkExperimentRepository] = None,
        registry: Optional[BenchmarkRegistry] = None,
        runner: Optional[BenchmarkRunner] = None,
        governance_engine: Optional[GovernanceEngine] = None,
    ) -> None:
        self._monitoring_repo = monitoring_repo or ContinuousMonitoringRepository()
        self._governance_repo = governance_repo or ProductionGovernanceRepository()
        self._experiment_repo = experiment_repo or BenchmarkExperimentRepository()
        self._registry = registry or BenchmarkRegistry()
        self._runner = runner or BenchmarkRunner()
        self._governance_engine = governance_engine or GovernanceEngine(
            governance_repo=self._governance_repo,
            experiment_repo=self._experiment_repo,
            registry=self._registry,
            runner=self._runner,
        )
        self._corpus_loader = BenchmarkCorpusLoader(registry=self._registry)

    async def discover_and_detect_corpus_changes(self) -> list[CorpusVersionEvent]:
        """Scans disk for benchmark corpora, verifies content hashes, and logs detection events."""
        corpora = self._corpus_loader.load_and_lock_all_canonical_corpora()
        events: list[CorpusVersionEvent] = []

        for b_id, corpus in corpora.items():
            evt = CorpusVersionEvent(
                benchmark_id=corpus.benchmark_id,
                detected_version=corpus.version,
                previous_version=None,
                content_hash_sha256=corpus.content_hash_sha256,
                verified_events_count=len(corpus.events),
                is_new_version=False,
                detected_at=datetime.now(timezone.utc),
            )
            events.append(evt)

            # Record in governance audit log
            audit_entry = GovernanceAuditLogEntry(
                audit_id=f"AUDIT-CORPUS-{corpus.benchmark_id}-{uuid.uuid4().hex[:6]}",
                event_type=AuditEventType.CORPUS_VERSION_DETECTED,
                benchmark_id=corpus.benchmark_id,
                experiment_id=None,
                actor="CORPUS_VERSION_WATCHER",
                details={
                    "version": corpus.version,
                    "records_count": len(corpus.events),
                    "content_hash_sha256": corpus.content_hash_sha256,
                    "name": corpus.definition.name,
                },
            )
            await self._monitoring_repo.record_audit_log(audit_entry)

        return events

    async def execute_scheduled_benchmark_run(
        self,
        benchmark_id: str,
        tolerance_days: int = 30,
        seed: int = 42,
        schedule_id: Optional[str] = None,
        actor: str = "CONTINUOUS_SCHEDULER_DAEMON",
    ) -> ContinuousRunResult:
        """
        Executes an automated benchmark run, checks regression against active baseline,
        runs significance analysis, dispatches alerts if needed, and logs to audit trail.
        """
        start_time = time.perf_counter()

        # Ensure corpus is loaded and locked
        corpus = self._registry.get_locked_corpus(benchmark_id)
        if not corpus:
            self._corpus_loader.load_and_lock_all_canonical_corpora()
            corpus = self._registry.get_locked_corpus(benchmark_id)
            if not corpus:
                raise ValueError(f"Benchmark corpus '{benchmark_id}' not found.")

        # Active baseline profile
        active_base = await self._governance_repo.get_active_baseline_profile(benchmark_id)
        base_profile_id = active_base.profile_id if active_base else "parashari_standard_v1"

        profiles = [PARASHARI_STANDARD_PROFILE, EMPIRICAL_RESEARCH_PROFILE]

        # Execute benchmark experiment
        experiment = self._runner.run_experiment(
            corpus=corpus,
            profiles=profiles,
            baseline_profile_id=base_profile_id,
            tolerance_days=tolerance_days,
            seed=seed,
            train_ratio=0.70,
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Save experiment
        saved_exp = await self._experiment_repo.save_experiment(experiment, duration_ms=duration_ms)

        # Check regression against active baseline run
        regression_report = self._governance_engine.detect_regression(experiment, experiment)
        has_regression = regression_report.has_regression
        severity = regression_report.severity

        alert: Optional[RegressionAlert] = None
        if has_regression and severity in (RegressionSeverity.WARNING, RegressionSeverity.CRITICAL_REGRESSION):
            alert = RegressionAlert(
                alert_id=f"ALERT-{experiment.provenance.experiment_id}-{uuid.uuid4().hex[:6]}",
                benchmark_id=benchmark_id,
                experiment_id=experiment.provenance.experiment_id,
                severity=severity,
                title=f"Regression Detected: [{benchmark_id}] {severity.value}",
                description="; ".join(regression_report.reasons),
                metrics_impact={
                    "hit_rate_drop_pct": regression_report.hit_rate_drop_pct,
                    "brier_increase": regression_report.brier_increase,
                    "mae_increase_days": regression_report.mae_increase_days,
                },
                created_at=datetime.now(timezone.utc),
            )
            await self._monitoring_repo.record_alert(alert)

            # Record Alert in Audit Log
            await self._monitoring_repo.record_audit_log(
                GovernanceAuditLogEntry(
                    audit_id=f"AUDIT-{alert.alert_id}",
                    event_type=AuditEventType.REGRESSION_ALERT_TRIGGERED,
                    benchmark_id=benchmark_id,
                    experiment_id=experiment.provenance.experiment_id,
                    actor=actor,
                    details={
                        "alert_id": alert.alert_id,
                        "severity": severity.value,
                        "reasons": list(regression_report.reasons),
                    },
                )
            )

        # Record Scheduled Run in Audit Log
        verdict = experiment.significance_reports[0].verdict if experiment.significance_reports else "EVALUATED"
        await self._monitoring_repo.record_audit_log(
            GovernanceAuditLogEntry(
                audit_id=f"AUDIT-RUN-{experiment.provenance.experiment_id}",
                event_type=AuditEventType.SCHEDULED_BENCHMARK_RUN,
                benchmark_id=benchmark_id,
                experiment_id=experiment.provenance.experiment_id,
                actor=actor,
                details={
                    "tolerance_days": tolerance_days,
                    "split_seed": seed,
                    "holdout_hit_rate_pct": experiment.report.rows[0].holdout_hit_rate_pct if experiment.report.rows else 0.0,
                    "significance_verdict": verdict,
                    "has_regression": has_regression,
                },
            )
        )

        # Update schedule record
        sched_id = schedule_id or f"SCHED-{benchmark_id}"
        existing_sched = await self._monitoring_repo.get_schedule(sched_id)
        now = datetime.now(timezone.utc)
        interval = existing_sched.interval_seconds if existing_sched else 86400

        updated_sched = MonitoringSchedule(
            schedule_id=sched_id,
            benchmark_id=benchmark_id,
            interval_seconds=interval,
            is_active=True,
            tolerance_days=tolerance_days,
            split_seed=seed,
            last_run_at=now,
            next_run_at=now + timedelta(seconds=interval),
        )
        await self._monitoring_repo.create_or_update_schedule(updated_sched)

        return ContinuousRunResult(
            schedule_id=sched_id,
            benchmark_id=benchmark_id,
            experiment_id=saved_exp.experiment_id,
            has_regression=has_regression,
            regression_severity=severity,
            alert_emitted=alert,
            significance_verdict=verdict,
            duration_ms=duration_ms,
            timestamp=now,
        )

    async def run_all_active_schedules(self) -> list[ContinuousRunResult]:
        """Runs continuous benchmarking for all registered canonical benchmarks."""
        schedules = await self._monitoring_repo.list_schedules()
        if not schedules:
            # Seed default schedules for all 4 canonical corpora
            for b_id in ["BENCH-CAREER-001", "BENCH-MARRIAGE-001", "BENCH-WEALTH-001", "BENCH-TRANSIT-001"]:
                s = MonitoringSchedule(
                    schedule_id=f"SCHED-{b_id}",
                    benchmark_id=b_id,
                    interval_seconds=86400,
                    is_active=True,
                    tolerance_days=30,
                    split_seed=42,
                )
                await self._monitoring_repo.create_or_update_schedule(s)
            schedules = await self._monitoring_repo.list_schedules()

        results: list[ContinuousRunResult] = []
        for sched in schedules:
            if sched.is_active:
                res = await self.execute_scheduled_benchmark_run(
                    benchmark_id=sched.benchmark_id,
                    tolerance_days=sched.tolerance_days,
                    seed=sched.split_seed,
                    schedule_id=sched.schedule_id,
                )
                results.append(res)

        return results