"""
AstroOS — Statistical Testing & Benchmark Confidence Domain Models

Defines domain contracts for paired hypothesis testing (McNemar exact test),
permutation tests, bootstrap confidence intervals, and statistical superiority verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class McNemarTestResult:
    """Paired contingency analysis for binary temporal classification."""

    # Table layout: (a: both hit, b: baseline hit only, c: candidate hit only, d: both missed)
    contingency_table: tuple[int, int, int, int]
    b_discordant_baseline_only: int
    c_discordant_candidate_only: int
    statistic: float               # Chi-square with Yates' continuity correction
    p_value: float                 # Exact two-sided binomial p-value
    odds_ratio: float              # c / b (candidate advantage ratio)
    is_significant: bool           # p_value < 0.05


@dataclass(frozen=True)
class MetricBootstrapConfidenceInterval:
    """Empirical bootstrap confidence interval for a benchmark metric."""

    metric_name: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence_level: float = 0.95
    standard_error: float = 0.0


@dataclass(frozen=True)
class ProfileSignificanceReport:
    """Comprehensive statistical significance analysis of a profile vs baseline."""

    profile_id: str
    baseline_profile_id: str
    mcnemar_test: McNemarTestResult
    brier_permutation_p_value: float
    delta_hit_rate_pct: float
    delta_brier_score: float
    delta_mae_peak_days: float
    bootstrap_cis: dict[str, MetricBootstrapConfidenceInterval]
    verdict: str  # STATISTICALLY_SIGNIFICANT_SUPERIOR | EQUIVALENT_OR_INSUFFICIENT_EVIDENCE | STATISTICALLY_INFERIOR