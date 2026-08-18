"""
AstroOS — Benchmark Intelligence & Trend Analytics API Router

Endpoints for longitudinal performance trajectories, composite stability indices,
profile statistics summaries, and corpus demographic compositions.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from apps.api.repositories.benchmark_experiment_repository import BenchmarkExperimentRepository
from apps.api.repositories.continuous_monitoring_repository import ContinuousMonitoringRepository
from apps.api.repositories.production_governance_repository import ProductionGovernanceRepository
from apps.api.services.benchmark_registry import BenchmarkRegistry
from apps.api.services.benchmark_runner import BenchmarkRunner
from apps.api.services.intelligence_analytics_service import IntelligenceAnalyticsService

router = APIRouter(prefix="/api/v1/intelligence", tags=["Benchmark Intelligence"])

_exp_repo = BenchmarkExperimentRepository()
_gov_repo = ProductionGovernanceRepository()
_mon_repo = ContinuousMonitoringRepository()
_registry = BenchmarkRegistry()
_runner = BenchmarkRunner()

_service = IntelligenceAnalyticsService(
    experiment_repo=_exp_repo,
    governance_repo=_gov_repo,
    monitoring_repo=_mon_repo,
    registry=_registry,
    runner=_runner,
)


class TrendPointSchema(BaseModel):
    experiment_id: str
    timestamp: str
    profile_id: str
    profile_name: str
    tolerance_days: int
    split_seed: int
    holdout_sample_size_n: int
    holdout_hit_rate_pct: float
    holdout_brier_score: float
    holdout_mae_days: float
    holdout_f1_score: float
    delta_hit_rate_pct: float
    delta_brier_score: float
    p_value: Optional[float]
    verdict: Optional[str]


class ProfileSummarySchema(BaseModel):
    profile_id: str
    profile_name: str
    total_evaluations: int
    mean_hit_rate_pct: float
    mean_brier_score: float
    mean_mae_days: float
    mean_f1_score: float
    std_hit_rate_pct: float
    std_brier_score: float
    min_hit_rate_pct: float
    max_hit_rate_pct: float
    min_brier_score: float
    max_brier_score: float
    trajectory: list[TrendPointSchema]


class CorpusDemographicsSchema(BaseModel):
    benchmark_id: str
    current_version: str
    total_verified_events: int
    content_hash_sha256: str
    birth_confidence_distribution: dict[str, int]
    event_verification_distribution: dict[str, int]
    date_confidence_distribution: dict[str, int]


class StabilityBreakdownSchema(BaseModel):
    hit_rate_stability_component: float
    brier_stability_component: float
    regression_free_component: float
    composite_stability_index: float
    total_runs_evaluated: int
    std_hit_rate: float
    std_brier: float
    regression_free_runs_ratio: float


class IntelligenceReportSchema(BaseModel):
    benchmark_id: str
    active_baseline_profile_id: str
    total_experiments: int
    stability: StabilityBreakdownSchema
    profile_summaries: dict[str, ProfileSummarySchema]
    corpus_demographics: CorpusDemographicsSchema
    alert_frequency_summary: dict[str, int]
    generated_at: str


@router.get("/benchmarks/{benchmark_id}/report", response_model=IntelligenceReportSchema)
async def get_benchmark_intelligence_report(benchmark_id: str) -> IntelligenceReportSchema:
    """Retrieves full descriptive intelligence and longitudinal trend analytics for a benchmark."""
    try:
        rep = await _service.generate_intelligence_report(benchmark_id)

        prof_dtos: dict[str, ProfileSummarySchema] = {}
        for p_id, p_sum in rep.profile_summaries.items():
            traj_dtos = [
                TrendPointSchema(
                    experiment_id=t.experiment_id,
                    timestamp=t.timestamp.isoformat(),
                    profile_id=t.profile_id,
                    profile_name=t.profile_name,
                    tolerance_days=t.tolerance_days,
                    split_seed=t.split_seed,
                    holdout_sample_size_n=t.holdout_sample_size_n,
                    holdout_hit_rate_pct=t.holdout_hit_rate_pct,
                    holdout_brier_score=t.holdout_brier_score,
                    holdout_mae_days=t.holdout_mae_days,
                    holdout_f1_score=t.holdout_f1_score,
                    delta_hit_rate_pct=t.delta_hit_rate_pct,
                    delta_brier_score=t.delta_brier_score,
                    p_value=t.p_value,
                    verdict=t.verdict,
                )
                for t in p_sum.trajectory
            ]

            prof_dtos[p_id] = ProfileSummarySchema(
                profile_id=p_sum.profile_id,
                profile_name=p_sum.profile_name,
                total_evaluations=p_sum.total_evaluations,
                mean_hit_rate_pct=p_sum.mean_hit_rate_pct,
                mean_brier_score=p_sum.mean_brier_score,
                mean_mae_days=p_sum.mean_mae_days,
                mean_f1_score=p_sum.mean_f1_score,
                std_hit_rate_pct=p_sum.std_hit_rate_pct,
                std_brier_score=p_sum.std_brier_score,
                min_hit_rate_pct=p_sum.min_hit_rate_pct,
                max_hit_rate_pct=p_sum.max_hit_rate_pct,
                min_brier_score=p_sum.min_brier_score,
                max_brier_score=p_sum.max_brier_score,
                trajectory=traj_dtos,
            )

        return IntelligenceReportSchema(
            benchmark_id=rep.benchmark_id,
            active_baseline_profile_id=rep.active_baseline_profile_id,
            total_experiments=rep.total_experiments,
            stability=StabilityBreakdownSchema(
                hit_rate_stability_component=rep.stability.hit_rate_stability_component,
                brier_stability_component=rep.stability.brier_stability_component,
                regression_free_component=rep.stability.regression_free_component,
                composite_stability_index=rep.stability.composite_stability_index,
                total_runs_evaluated=rep.stability.total_runs_evaluated,
                std_hit_rate=rep.stability.std_hit_rate,
                std_brier=rep.stability.std_brier,
                regression_free_runs_ratio=rep.stability.regression_free_runs_ratio,
            ),
            profile_summaries=prof_dtos,
            corpus_demographics=CorpusDemographicsSchema(
                benchmark_id=rep.corpus_demographics.benchmark_id,
                current_version=rep.corpus_demographics.current_version,
                total_verified_events=rep.corpus_demographics.total_verified_events,
                content_hash_sha256=rep.corpus_demographics.content_hash_sha256,
                birth_confidence_distribution=rep.corpus_demographics.birth_confidence_distribution,
                event_verification_distribution=rep.corpus_demographics.event_verification_distribution,
                date_confidence_distribution=rep.corpus_demographics.date_confidence_distribution,
            ),
            alert_frequency_summary=rep.alert_frequency_summary,
            generated_at=rep.generated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))