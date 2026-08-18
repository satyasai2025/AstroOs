"""
AstroOS — Benchmark Intelligence & Descriptive Trend Analytics Domain Contracts

Defines contracts for observational longitudinal performance trajectories,
mathematical stability index formulation, profile summary statistics,
and corpus demographic quality distributions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass(frozen=True)
class PerformanceTrendPoint:
    """Descriptive empirical observation of a single experiment run."""

    experiment_id: str
    timestamp: datetime
    profile_id: str
    profile_name: str
    tolerance_days: int
    split_seed: int
    holdout_sample_size_n: int
    holdout_hit_rate_pct: float
    holdout_brier_score: float
    holdout_mae_days: float
    holdout_f1_score: float
    delta_hit_rate_pct: float = 0.0
    delta_brier_score: float = 0.0
    p_value: Optional[float] = None
    verdict: Optional[str] = None


@dataclass(frozen=True)
class ProfileEvolutionSummary:
    """Descriptive statistical summary and longitudinal trajectory for a predictive profile."""

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
    trajectory: tuple[PerformanceTrendPoint, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CorpusEvolutionSummary:
    """Demographic and quality composition of a benchmark corpus."""

    benchmark_id: str
    current_version: str
    total_verified_events: int
    content_hash_sha256: str
    birth_confidence_distribution: dict[str, int]
    event_verification_distribution: dict[str, int]
    date_confidence_distribution: dict[str, int]


@dataclass(frozen=True)
class StabilityIndexBreakdown:
    """Mathematical formulation components of the System Stability Index (0.0 to 1.0)."""

    hit_rate_stability_component: float     # S_hit in [0.0, 1.0]
    brier_stability_component: float        # S_brier in [0.0, 1.0]
    regression_free_component: float        # S_clean in [0.0, 1.0]
    composite_stability_index: float        # 0.40 * S_hit + 0.30 * S_brier + 0.30 * S_clean in [0.0, 1.0]
    total_runs_evaluated: int
    std_hit_rate: float
    std_brier: float
    regression_free_runs_ratio: float


@dataclass(frozen=True)
class BenchmarkIntelligenceReport:
    """Comprehensive observational intelligence payload for a benchmark problem."""

    benchmark_id: str
    active_baseline_profile_id: str
    total_experiments: int
    stability: StabilityIndexBreakdown
    profile_summaries: dict[str, ProfileEvolutionSummary]
    corpus_demographics: CorpusEvolutionSummary
    alert_frequency_summary: dict[str, int]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))