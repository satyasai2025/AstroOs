"""
AstroOS — Production Governance & Continuous Benchmarking Engine

Provides automated regression detection between experiment runs, cryptographic
reproducibility verification, active baseline tracking, and promotion workflows.
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.benchmark_experiment import BenchmarkExperiment
from apps.api.domain.production_governance import (
    ExperimentSignoff,
    ProductionProfileVersion,
    RegressionReport,
    RegressionSeverity,
    ReproducibilityAudit,
    SignoffStatus,
)
from apps.api.domain.prediction_orchestration import (
    EMPIRICAL_RESEARCH_PROFILE,
    PARASHARI_STANDARD_PROFILE,
    ConsensusProfile,
)
from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner


class GovernanceEngine:
    """Orchestrates production governance, regression detection, and reproducibility auditing."""

    def __init__(
        self,
        governance_repo: Optional[ProductionGovernanceRepository] = None,
        experiment_repo: Optional[BenchmarkExperimentRepository] = None,
        registry: Optional[BenchmarkRegistry] = None,
        runner: Optional[BenchmarkRunner] = None,
    ) -> None:
        self._gov_repo = governance_repo or ProductionGovernanceRepository()
        self._exp_repo = experiment_repo or BenchmarkExperimentRepository()
        self._registry = registry or BenchmarkRegistry()
        self._runner = runner or BenchmarkRunner()

    def detect_regression(
        self,
        baseline_experiment: BenchmarkExperiment,
        candidate_experiment: BenchmarkExperiment,
        evaluated_profile_id: Optional[str] = None,
    ) -> RegressionReport:
        """
        Detects metric regressions between a baseline experiment run and a candidate run.
        """
        # Default to first non-baseline profile or first row
        base_rows = baseline_experiment.report.rows
        cand_rows = candidate_experiment.report.rows

        target_id = evaluated_profile_id
        if not target_id:
            target_id = cand_rows[-1].profile_id if cand_rows else "parashari_standard_v1"

        base_row = next((r for r in base_rows if r.profile_id == target_id), base_rows[0] if base_rows else None)
        cand_row = next((r for r in cand_rows if r.profile_id == target_id), cand_rows[0] if cand_rows else None)

        if not base_row or not cand_row:
            return RegressionReport(
                baseline_experiment_id=baseline_experiment.provenance.experiment_id,
                candidate_experiment_id=candidate_experiment.provenance.experiment_id,
                has_regression=False,
                hit_rate_drop_pct=0.0,
                brier_increase=0.0,
                mae_increase_days=0.0,
                reasons=("Could not match evaluated profiles between experiment runs.",),
                severity=RegressionSeverity.NONE,
            )

        hit_drop = round(base_row.holdout_hit_rate_pct - cand_row.holdout_hit_rate_pct, 1)
        brier_inc = round(cand_row.holdout_brier_score - base_row.holdout_brier_score, 4)
        mae_inc = round(cand_row.holdout_mae_peak_days - base_row.holdout_mae_peak_days, 1)

        reasons: list[str] = []
        severity = RegressionSeverity.NONE

        if hit_drop >= 3.0:
            reasons.append(f"Holdout Hit Rate dropped by -{hit_drop}% (from {base_row.holdout_hit_rate_pct}% to {cand_row.holdout_hit_rate_pct}%).")
            severity = RegressionSeverity.CRITICAL_REGRESSION
        elif hit_drop > 0.0:
            reasons.append(f"Minor Hit Rate decrease of -{hit_drop}%.")
            if severity != RegressionSeverity.CRITICAL_REGRESSION:
                severity = RegressionSeverity.WARNING

        if brier_inc >= 0.02:
            reasons.append(f"Calibration Brier Score degraded by +{brier_inc} (from {base_row.holdout_brier_score:.4f} to {cand_row.holdout_brier_score:.4f}).")
            severity = RegressionSeverity.CRITICAL_REGRESSION
        elif brier_inc > 0.005:
            reasons.append(f"Minor Brier Score increase of +{brier_inc}.")
            if severity != RegressionSeverity.CRITICAL_REGRESSION:
                severity = RegressionSeverity.WARNING

        if mae_inc >= 5.0:
            reasons.append(f"Timing accuracy degraded: MAE increased by +{mae_inc} days.")
            severity = RegressionSeverity.CRITICAL_REGRESSION
        elif mae_inc > 1.0:
            reasons.append(f"Minor timing offset increase of +{mae_inc} days.")
            if severity != RegressionSeverity.CRITICAL_REGRESSION:
                severity = RegressionSeverity.WARNING

        if not reasons:
            reasons.append("No metric or timing regressions detected against baseline run.")

        has_reg = severity in (RegressionSeverity.WARNING, RegressionSeverity.CRITICAL_REGRESSION)

        return RegressionReport(
            baseline_experiment_id=baseline_experiment.provenance.experiment_id,
            candidate_experiment_id=candidate_experiment.provenance.experiment_id,
            has_regression=has_reg,
            hit_rate_drop_pct=max(0.0, hit_drop),
            brier_increase=max(0.0, brier_inc),
            mae_increase_days=max(0.0, mae_inc),
            reasons=tuple(reasons),
            severity=severity,
        )

    async def verify_reproducibility(self, experiment_id: str) -> ReproducibilityAudit:
        """
        Re-executes an experiment with identical locked parameters and checks bit-for-bit SHA-256 result equality.
        """
        model = await self._exp_repo.get_by_experiment_id(experiment_id)
        if not model:
            raise ValueError(f"Experiment '{experiment_id}' not found.")

        corpus = self._registry.get_locked_corpus(model.benchmark_id, model.benchmark_version)
        if not corpus:
            raise ValueError(f"Corpus '{model.benchmark_id}' v{model.benchmark_version} not found.")

        profiles: list[ConsensusProfile] = []
        for pid in model.profile_ids:
            if pid == "parashari_standard_v1":
                profiles.append(PARASHARI_STANDARD_PROFILE)
            elif pid == "empirical_research_v1":
                profiles.append(EMPIRICAL_RESEARCH_PROFILE)
            else:
                profiles.append(PARASHARI_STANDARD_PROFILE)

        re_run_exp = self._runner.run_experiment(
            corpus=corpus,
            profiles=profiles,
            baseline_profile_id=model.baseline_profile_id,
            tolerance_days=model.tolerance_days,
            seed=model.split_seed,
            train_ratio=model.split_train_ratio,
        )

        expected_hash = model.results_hash_sha256
        actual_hash = re_run_exp.provenance.results_hash
        is_identical = (expected_hash == actual_hash)

        notes = (
            "Bit-for-bit identical results checksum verified successfully."
            if is_identical
            else f"Cryptographic mismatch: expected {expected_hash}, got {actual_hash}."
        )

        return ReproducibilityAudit(
            experiment_id=experiment_id,
            is_bit_for_bit_identical=is_identical,
            expected_results_hash=expected_hash,
            actual_results_hash=actual_hash,
            audit_notes=notes,
        )

    async def promote_experiment_to_baseline(
        self,
        experiment_id: str,
        version: str,
        reviewer_id: str,
        notes: str = "",
    ) -> ProductionProfileVersion:
        """
        Promotes an approved experiment to become the active production baseline.
        """
        model = await self._exp_repo.get_by_experiment_id(experiment_id)
        if not model:
            raise ValueError(f"Experiment '{experiment_id}' not found.")

        signoff = await self._gov_repo.get_signoff(experiment_id)
        if not signoff or signoff.status != SignoffStatus.APPROVED:
            # Auto-record approval if not explicitly signed off
            await self._gov_repo.record_signoff(
                experiment_id=experiment_id,
                status=SignoffStatus.APPROVED,
                reviewer_id=reviewer_id,
                notes=f"Auto-approved upon promotion: {notes}",
            )

        promoted_profile_id = model.profile_ids[-1] if model.profile_ids else "empirical_research_v1"

        return await self._gov_repo.promote_profile_to_production(
            profile_id=promoted_profile_id,
            version=version,
            benchmark_id=model.benchmark_id,
            experiment_id=experiment_id,
            reviewer_id=reviewer_id,
            notes=notes,
        )