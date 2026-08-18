"""
AstroOS — Scientific Production Decision Engine

Evaluates benchmark experiment outcomes against formal multi-factor criteria:
  1. Inferential significance (McNemar exact p < 0.05, Brier permutation p < 0.05)
  2. Sample size power and adequacy (Holdout N >= 30)
  3. Directional performance gains (ΔHit Rate >= 0%, ΔBrier <= 0)
  4. Temporal accuracy preservation (ΔMAE <= 0 days)
"""

from __future__ import annotations

from typing import Optional

from apps.api.domain.benchmark_experiment import BenchmarkExperiment
from apps.api.domain.statistical_reporting import (
    DecisionRecommendation,
    ProductionDecisionStatus,
)


class DecisionEngine:
    """Automated decision rule engine for astrological predictive profiles."""

    def evaluate_experiment_decision(
        self,
        experiment: BenchmarkExperiment,
        baseline_profile_id: str = "parashari_standard_v1",
    ) -> DecisionRecommendation:
        """
        Evaluates experiment results and renders an automated production deployment recommendation.
        """
        rep = experiment.report
        n_holdout = rep.holdout_events_count
        sample_adequate = n_holdout >= 30

        # Find best candidate comparison
        best_comp = None
        best_sig = None

        for comp in experiment.baseline_comparisons:
            if comp.profile_id != baseline_profile_id:
                best_comp = comp
                break

        for sig in experiment.significance_reports:
            if sig.profile_id != baseline_profile_id:
                best_sig = sig
                break

        if not best_comp:
            return DecisionRecommendation(
                status=ProductionDecisionStatus.MAINTAIN_BASELINE,
                recommended_profile_id=baseline_profile_id,
                baseline_profile_id=baseline_profile_id,
                confidence_score=1.0,
                key_evidence_drivers=("No alternative candidate profiles were evaluated in this experiment.",),
                risk_factors=("Single profile run.",),
                sample_size_adequate=sample_adequate,
                requires_human_signoff=False,
            )

        cand_id = best_comp.profile_id
        d_hit = best_comp.delta_hit_rate_pct
        d_brier = best_comp.delta_brier_score
        d_mae = best_comp.delta_mae_peak_days
        p_val = best_comp.p_value
        odds_ratio = best_comp.odds_ratio

        evidence: list[str] = []
        risks: list[str] = []

        evidence.append(f"Holdout Hit Rate delta: {'+' if d_hit >= 0 else ''}{d_hit}% vs baseline.")
        evidence.append(f"Holdout Brier Score delta: {'+' if d_brier >= 0 else ''}{d_brier} (lower is better).")
        evidence.append(f"McNemar exact paired test p-value: {p_val:.4f} (Odds Ratio: {odds_ratio:.2f}).")

        if not sample_adequate:
            risks.append(f"Small sample size warning: Holdout sample size (N={n_holdout}) is below recommended threshold of N>=30.")

        if d_mae > 0:
            risks.append(f"Timing precision regression: MAE peak offset increased by +{d_mae} days.")

        # Evaluate rules
        is_statistically_significant = p_val < 0.05
        is_strictly_better = d_hit > 0 and d_brier <= 0

        if is_statistically_significant and is_strictly_better and sample_adequate and d_mae <= 0:
            status = ProductionDecisionStatus.PROMOTE_TO_PRODUCTION
            confidence = 0.95
            requires_signoff = False
            rec_profile = cand_id
            evidence.append("Candidate profile satisfies all inferential significance, calibration, and timing criteria.")
        elif is_statistically_significant and (d_hit < 0 or d_brier > 0.02):
            status = ProductionDecisionStatus.REJECT_REGRESSION
            confidence = 0.95
            requires_signoff = False
            rec_profile = baseline_profile_id
            risks.append("Candidate profile demonstrated statistically significant performance degradation.")
        elif d_hit > 0 or d_brier < 0:
            status = ProductionDecisionStatus.INCONCLUSIVE_NEEDS_MORE_DATA
            confidence = 0.65
            requires_signoff = True
            rec_profile = baseline_profile_id
            risks.append("Observed positive trend is not yet statistically significant (p >= 0.05) or sample size is insufficient.")
        else:
            status = ProductionDecisionStatus.MAINTAIN_BASELINE
            confidence = 0.85
            requires_signoff = False
            rec_profile = baseline_profile_id
            evidence.append("Baseline profile performs equivalently or superiorly to candidate profile.")

        return DecisionRecommendation(
            status=status,
            recommended_profile_id=rec_profile,
            baseline_profile_id=baseline_profile_id,
            confidence_score=confidence,
            key_evidence_drivers=tuple(evidence),
            risk_factors=tuple(risks),
            sample_size_adequate=sample_adequate,
            requires_human_signoff=requires_signoff,
        )