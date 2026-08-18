"""
AstroOS — Statistical Significance Testing & Confidence Analysis Engine

Implements inferential statistics for benchmark evaluations:
  1. McNemar's exact paired test for binary temporal classification on identical splits
  2. Paired permutation test for probabilistic Brier score differences
  3. Non-parametric bootstrap resampling (B=1000) for 95% metric confidence intervals
  4. Rigorous scientific superiority / equivalence verdicts
"""

from __future__ import annotations

import math
import random
import statistics
from typing import Optional, Sequence

from apps.api.domain.research_calibration import (
    BacktestOutcome,
    CalibrationModel,
    TemporalMatchStatus,
)
from apps.api.domain.statistical_testing import (
    McNemarTestResult,
    MetricBootstrapConfidenceInterval,
    ProfileSignificanceReport,
)
from apps.api.services.calibration_engine import CalibrationEngine


def _is_hit(status: TemporalMatchStatus) -> bool:
    return status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT)


def _exact_binomial_two_sided_p_value(n: int, k: int) -> float:
    """Computes exact two-sided binomial p-value under H0: p = 0.5."""
    if n == 0:
        return 1.0

    target_prob = math.comb(n, k) * (0.5 ** n)
    total_p = 0.0
    for i in range(n + 1):
        prob = math.comb(n, i) * (0.5 ** n)
        if prob <= target_prob + 1e-12:
            total_p += prob
    return min(1.0, round(total_p, 4))


class SignificanceEngine:
    """Statistical hypothesis testing and bootstrap confidence interval evaluator."""

    def __init__(self, calibration_engine: Optional[CalibrationEngine] = None) -> None:
        self._calibration = calibration_engine or CalibrationEngine()

    def compute_mcnemar_test(
        self,
        baseline_outcomes: Sequence[BacktestOutcome],
        candidate_outcomes: Sequence[BacktestOutcome],
    ) -> McNemarTestResult:
        """
        Executes McNemar's exact paired test on identical holdout event outcomes.
        """
        if len(baseline_outcomes) != len(candidate_outcomes):
            raise ValueError("Baseline and candidate outcomes must have identical sample length.")

        a, b, c, d = 0, 0, 0, 0
        for base_o, cand_o in zip(baseline_outcomes, candidate_outcomes):
            base_hit = _is_hit(base_o.match_status)
            cand_hit = _is_hit(cand_o.match_status)

            if base_hit and cand_hit:
                a += 1
            elif base_hit and not cand_hit:
                b += 1
            elif not base_hit and cand_hit:
                c += 1
            else:
                d += 1

        discordant_total = b + c
        if discordant_total > 0:
            # Chi-square with Yates' continuity correction
            statistic = round(((abs(b - c) - 1.0) ** 2) / discordant_total, 4)
            p_value = _exact_binomial_two_sided_p_value(discordant_total, c)
            odds_ratio = round(c / b, 4) if b > 0 else (999.0 if c > 0 else 1.0)
        else:
            statistic = 0.0
            p_value = 1.0
            odds_ratio = 1.0

        is_significant = p_value < 0.05

        return McNemarTestResult(
            contingency_table=(a, b, c, d),
            b_discordant_baseline_only=b,
            c_discordant_candidate_only=c,
            statistic=statistic,
            p_value=p_value,
            odds_ratio=odds_ratio,
            is_significant=is_significant,
        )

    def compute_brier_permutation_test(
        self,
        baseline_outcomes: Sequence[BacktestOutcome],
        candidate_outcomes: Sequence[BacktestOutcome],
        baseline_model: CalibrationModel,
        candidate_model: CalibrationModel,
        n_permutations: int = 2000,
        seed: int = 42,
    ) -> float:
        """
        Paired permutation test evaluating whether candidate Brier score is significantly lower than baseline.
        """
        n = len(baseline_outcomes)
        if n == 0:
            return 1.0

        diffs: list[float] = []
        for base_o, cand_o in zip(baseline_outcomes, candidate_outcomes):
            y_act = 1.0 if _is_hit(base_o.match_status) else 0.0
            p_base = self._calibration.predict_probability_for_score(base_o.deterministic_score, baseline_model)
            p_cand = self._calibration.predict_probability_for_score(cand_o.deterministic_score, candidate_model)
            diffs.append(((p_cand - y_act) ** 2) - ((p_base - y_act) ** 2))

        t_obs = statistics.mean(diffs)
        rng = random.Random(seed)

        count_extreme = 0
        for _ in range(n_permutations):
            perm_diffs = [d if rng.random() < 0.5 else -d for d in diffs]
            t_perm = statistics.mean(perm_diffs)
            if t_perm <= t_obs + 1e-12:
                count_extreme += 1

        return round(count_extreme / n_permutations, 4)

    def compute_bootstrap_cis(
        self,
        outcomes: Sequence[BacktestOutcome],
        calib_model: CalibrationModel,
        n_bootstraps: int = 1000,
        seed: int = 42,
    ) -> dict[str, MetricBootstrapConfidenceInterval]:
        """
        Calculates non-parametric 95% bootstrap confidence intervals for Hit Rate, Brier Score, and Timing MAE.
        """
        n = len(outcomes)
        if n == 0:
            return {}

        rng = random.Random(seed)
        hit_rates: list[float] = []
        brier_scores: list[float] = []
        maes: list[float] = []

        for _ in range(n_bootstraps):
            sample = [outcomes[rng.randrange(n)] for _ in range(n)]

            hits = sum(1 for o in sample if _is_hit(o.match_status))
            hit_rates.append((hits / n) * 100.0)

            brier_sum = 0.0
            for o in sample:
                p_cal = self._calibration.predict_probability_for_score(o.deterministic_score, calib_model)
                y_act = 1.0 if _is_hit(o.match_status) else 0.0
                brier_sum += (p_cal - y_act) ** 2
            brier_scores.append(brier_sum / n)

            offsets = [abs(o.peak_offset_days) for o in sample if o.peak_offset_days is not None]
            maes.append(statistics.mean(offsets) if offsets else 0.0)

        def _get_ci(vals: list[float], name: str, point_val: float) -> MetricBootstrapConfidenceInterval:
            sorted_v = sorted(vals)
            low_idx = int(0.025 * len(sorted_v))
            high_idx = int(0.975 * len(sorted_v)) - 1
            low = round(sorted_v[low_idx], 2)
            high = round(sorted_v[high_idx], 2)
            se = round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0
            return MetricBootstrapConfidenceInterval(
                metric_name=name,
                point_estimate=round(point_val, 2),
                ci_lower=low,
                ci_upper=high,
                confidence_level=0.95,
                standard_error=se,
            )

        # Point estimates
        actual_hits = sum(1 for o in outcomes if _is_hit(o.match_status))
        actual_hit_rate = (actual_hits / n) * 100.0
        actual_brier = sum(
            (self._calibration.predict_probability_for_score(o.deterministic_score, calib_model) - (1.0 if _is_hit(o.match_status) else 0.0)) ** 2
            for o in outcomes
        ) / n
        actual_offsets = [abs(o.peak_offset_days) for o in outcomes if o.peak_offset_days is not None]
        actual_mae = statistics.mean(actual_offsets) if actual_offsets else 0.0

        return {
            "hit_rate_pct": _get_ci(hit_rates, "hit_rate_pct", actual_hit_rate),
            "brier_score": _get_ci(brier_scores, "brier_score", actual_brier),
            "mae_peak_days": _get_ci(maes, "mae_peak_days", actual_mae),
        }

    def evaluate_profile_significance(
        self,
        candidate_profile_id: str,
        baseline_profile_id: str,
        candidate_outcomes: Sequence[BacktestOutcome],
        baseline_outcomes: Sequence[BacktestOutcome],
        candidate_model: CalibrationModel,
        baseline_model: CalibrationModel,
        n_bootstraps: int = 1000,
        n_permutations: int = 2000,
        seed: int = 42,
    ) -> ProfileSignificanceReport:
        """
        Synthesizes paired tests, permutation tests, and bootstrap CIs into a formal significance report.
        """
        mcnemar = self.compute_mcnemar_test(baseline_outcomes, candidate_outcomes)
        brier_p = self.compute_brier_permutation_test(
            baseline_outcomes=baseline_outcomes,
            candidate_outcomes=candidate_outcomes,
            baseline_model=baseline_model,
            candidate_model=candidate_model,
            n_permutations=n_permutations,
            seed=seed,
        )
        cis = self.compute_bootstrap_cis(candidate_outcomes, candidate_model, n_bootstraps=n_bootstraps, seed=seed)

        # Calculate deltas
        n = len(baseline_outcomes)
        base_hits = sum(1 for o in baseline_outcomes if _is_hit(o.match_status))
        cand_hits = sum(1 for o in candidate_outcomes if _is_hit(o.match_status))
        d_hit = round(((cand_hits - base_hits) / n) * 100.0, 1) if n > 0 else 0.0

        base_brier = sum(
            (self._calibration.predict_probability_for_score(o.deterministic_score, baseline_model) - (1.0 if _is_hit(o.match_status) else 0.0)) ** 2
            for o in baseline_outcomes
        ) / n if n > 0 else 0.0

        cand_brier = sum(
            (self._calibration.predict_probability_for_score(o.deterministic_score, candidate_model) - (1.0 if _is_hit(o.match_status) else 0.0)) ** 2
            for o in candidate_outcomes
        ) / n if n > 0 else 0.0
        d_brier = round(cand_brier - base_brier, 4)

        base_off = [abs(o.peak_offset_days) for o in baseline_outcomes if o.peak_offset_days is not None]
        cand_off = [abs(o.peak_offset_days) for o in candidate_outcomes if o.peak_offset_days is not None]
        base_mae = statistics.mean(base_off) if base_off else 0.0
        cand_mae = statistics.mean(cand_off) if cand_off else 0.0
        d_mae = round(cand_mae - base_mae, 1)

        # Verdict
        if mcnemar.p_value < 0.05 and d_hit > 0 and d_brier <= 0:
            verdict = "STATISTICALLY_SIGNIFICANT_SUPERIOR"
        elif d_hit < 0 and mcnemar.p_value < 0.05:
            verdict = "STATISTICALLY_INFERIOR"
        else:
            verdict = "EQUIVALENT_OR_INSUFFICIENT_EVIDENCE"

        return ProfileSignificanceReport(
            profile_id=candidate_profile_id,
            baseline_profile_id=baseline_profile_id,
            mcnemar_test=mcnemar,
            brier_permutation_p_value=brier_p,
            delta_hit_rate_pct=d_hit,
            delta_brier_score=d_brier,
            delta_mae_peak_days=d_mae,
            bootstrap_cis=cis,
            verdict=verdict,
        )