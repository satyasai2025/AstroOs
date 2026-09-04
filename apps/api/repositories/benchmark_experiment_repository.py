"""
AstroOS — Benchmark Experiment Repository

Data access layer for saving, retrieving, and querying persisted benchmark experiment records.
Supports database persistence with an in-memory fallback for testing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.domain.benchmark_experiment import BenchmarkExperiment
from apps.api.models.benchmark_experiment import BenchmarkExperimentModel


class BenchmarkExperimentRepository:
    """Repository for persisting and querying benchmark experiments."""

    _in_memory_store: dict[str, BenchmarkExperimentModel] = {}

    def __init__(self, session: Optional[AsyncSession] = None) -> None:
        self._session = session

    async def save_experiment(
        self,
        experiment: BenchmarkExperiment,
        duration_ms: float = 0.0,
    ) -> BenchmarkExperimentModel:
        """Persists a completed benchmark experiment record."""
        p = experiment.provenance
        report = experiment.report

        rows_dict = [
            {
                "profile_id": r.profile_id,
                "profile_name": r.profile_name,
                "calibration_sample_size_n": r.calibration_sample_size_n,
                "holdout_sample_size_n": r.holdout_sample_size_n,
                "holdout_precision": r.holdout_precision,
                "holdout_recall": r.holdout_recall,
                "holdout_f1_score": r.holdout_f1_score,
                "holdout_hit_rate_pct": r.holdout_hit_rate_pct,
                "holdout_brier_score": r.holdout_brier_score,
                "holdout_mae_peak_days": r.holdout_mae_peak_days,
                "holdout_median_peak_offset_days": r.holdout_median_peak_offset_days,
                "holdout_p90_peak_offset_days": r.holdout_p90_peak_offset_days,
                "calibration_method": r.calibration_method,
            }
            for r in report.rows
        ]

        baseline_dict = [
            {
                "profile_id": b.profile_id,
                "baseline_profile_id": b.baseline_profile_id,
                "delta_hit_rate_pct": b.delta_hit_rate_pct,
                "delta_brier_score": b.delta_brier_score,
                "delta_f1_score": b.delta_f1_score,
                "delta_mae_peak_days": b.delta_mae_peak_days,
                "is_statistically_superior": b.is_statistically_superior,
                "p_value": b.p_value,
                "odds_ratio": b.odds_ratio,
                "verdict": b.verdict,
            }
            for b in experiment.baseline_comparisons
        ]

        sig_dict = [
            {
                "profile_id": s.profile_id,
                "baseline_profile_id": s.baseline_profile_id,
                "mcnemar_test": {
                    "contingency_table": list(s.mcnemar_test.contingency_table),
                    "b_discordant_baseline_only": s.mcnemar_test.b_discordant_baseline_only,
                    "c_discordant_candidate_only": s.mcnemar_test.c_discordant_candidate_only,
                    "statistic": s.mcnemar_test.statistic,
                    "p_value": s.mcnemar_test.p_value,
                    "odds_ratio": s.mcnemar_test.odds_ratio,
                    "is_significant": s.mcnemar_test.is_significant,
                },
                "brier_permutation_p_value": s.brier_permutation_p_value,
                "delta_hit_rate_pct": s.delta_hit_rate_pct,
                "delta_brier_score": s.delta_brier_score,
                "delta_mae_peak_days": s.delta_mae_peak_days,
                "bootstrap_cis": {
                    k: {
                        "metric_name": v.metric_name,
                        "point_estimate": v.point_estimate,
                        "ci_lower": v.ci_lower,
                        "ci_upper": v.ci_upper,
                        "confidence_level": v.confidence_level,
                        "standard_error": v.standard_error,
                    }
                    for k, v in s.bootstrap_cis.items()
                },
                "verdict": s.verdict,
            }
            for s in experiment.significance_reports
        ]

        model = BenchmarkExperimentModel(
            id=uuid.uuid4(),
            experiment_id=p.experiment_id,
            benchmark_id=p.benchmark_id,
            benchmark_version=p.benchmark_version,
            content_hash_sha256=p.content_hash_sha256,
            status="COMPLETED",
            split_seed=p.split_seed,
            split_train_ratio=p.train_ratio,
            tolerance_days=p.tolerance_days,
            profile_ids=list(p.profile_ids),
            baseline_profile_id=baseline_dict[0]["baseline_profile_id"] if baseline_dict else "parashari_standard_v1",
            train_event_ids=list(experiment.split.train_event_ids),
            holdout_event_ids=list(experiment.split.holdout_event_ids),
            results_summary={"rows": rows_dict, "significance_reports": sig_dict},
            baseline_comparisons=baseline_dict,
            calibration_models={},
            results_hash_sha256=p.results_hash,
            duration_ms=duration_ms,
            completed_at=datetime.now(timezone.utc),
        )

        if self._session is not None:
            self._session.add(model)
            await self._session.flush()

        self._in_memory_store[model.experiment_id] = model
        return model

    async def get_by_experiment_id(self, experiment_id: str) -> Optional[BenchmarkExperimentModel]:
        """Retrieves an experiment by its human-readable experiment ID."""
        if self._session is not None:
            stmt = select(BenchmarkExperimentModel).where(
                BenchmarkExperimentModel.experiment_id == experiment_id,
                BenchmarkExperimentModel.deleted_at.is_(None),
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()
            if model is not None:
                return model

        return self._in_memory_store.get(experiment_id)

    async def list_by_benchmark_id(
        self,
        benchmark_id: str,
        limit: int = 50,
    ) -> Sequence[BenchmarkExperimentModel]:
        """Lists archived experiments for a specific benchmark."""
        if self._session is not None:
            stmt = (
                select(BenchmarkExperimentModel)
                .where(
                    BenchmarkExperimentModel.benchmark_id == benchmark_id,
                    BenchmarkExperimentModel.deleted_at.is_(None),
                )
                .order_by(BenchmarkExperimentModel.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())

        return [
            m for m in self._in_memory_store.values()
            if m.benchmark_id == benchmark_id
        ][:limit]

    @classmethod
    def clear_in_memory(cls) -> None:
        """Clears in-memory cache (for test isolation)."""
        cls._in_memory_store.clear()