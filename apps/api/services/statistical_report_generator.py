"""
AstroOS — Publication-Grade Statistical Report Generator

Compiles complete benchmark experiment results into self-contained Markdown
and structured JSON research reports with cryptographic provenance, inferential
statistics, bootstrap confidence intervals, and automated production decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from apps.api.domain.benchmark_experiment import BenchmarkExperiment
from apps.api.domain.statistical_reporting import (
    DecisionRecommendation,
    ProductionDecisionStatus,
    StatisticalResearchReport,
)
from apps.api.services.decision_engine import DecisionEngine


class StatisticalReportGenerator:
    """Generates standardized research reports from benchmark experiment runs."""

    def __init__(self, decision_engine: Optional[DecisionEngine] = None) -> None:
        self._decision_engine = decision_engine or DecisionEngine()

    def generate_markdown_report(
        self,
        experiment: BenchmarkExperiment,
        decision: DecisionRecommendation,
    ) -> str:
        """Generates a complete, publication-grade Markdown report."""
        p = experiment.provenance
        rep = experiment.report
        lines: list[str] = []

        lines.append(f"# AstroOS Scientific Research Report: `{p.benchmark_id}` (v{p.benchmark_version})")
        lines.append(f"**Experiment ID**: `{p.experiment_id}`  ")
        lines.append(f"**Generated At**: `{p.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}`  ")
        lines.append(f"**Software Engine**: `AstroOS v{p.software_version}`  ")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 1. Executive Summary & Decision
        status_badges = {
            ProductionDecisionStatus.PROMOTE_TO_PRODUCTION: "🟢 PROMOTE TO PRODUCTION",
            ProductionDecisionStatus.MAINTAIN_BASELINE: "🔵 MAINTAIN BASELINE",
            ProductionDecisionStatus.INCONCLUSIVE_NEEDS_MORE_DATA: "🟡 INCONCLUSIVE (NEEDS MORE DATA)",
            ProductionDecisionStatus.REJECT_REGRESSION: "🔴 REJECT (STATISTICAL REGRESSION)",
        }
        badge = status_badges.get(decision.status, str(decision.status))

        lines.append("## 1. Executive Decision Recommendation")
        lines.append("")
        lines.append(f"> ### Verdict: **{badge}**")
        lines.append(f"> **Recommended Profile**: `{decision.recommended_profile_id}` (Confidence: {int(decision.confidence_score * 100)}%)  ")
        lines.append(f"> **Human Signoff Required**: `{'YES' if decision.requires_human_signoff else 'NO'}`  ")
        lines.append("")
        lines.append("### Key Evidence Drivers:")
        for ev in decision.key_evidence_drivers:
            lines.append(f"- {ev}")
        lines.append("")

        if decision.risk_factors:
            lines.append("### Risk & Caution Factors:")
            for rf in decision.risk_factors:
                lines.append(f"- ⚠️ {rf}")
            lines.append("")

        # 2. Benchmark Problem & Provenance
        lines.append("## 2. Benchmark Problem & Dataset Provenance")
        lines.append("")
        lines.append(f"- **Benchmark ID**: `{p.benchmark_id}` (v{p.benchmark_version})")
        lines.append(f"- **Dataset Content SHA-256**: `{p.content_hash_sha256}`")
        lines.append(f"- **Results Signature SHA-256**: `{p.results_hash}`")
        lines.append(f"- **Partition Policy**: {int(p.train_ratio * 100)}% Train / {int((1 - p.train_ratio) * 100)}% Holdout (Seed: `{p.split_seed}`)")
        lines.append(f"- **Sample Counts**: Total N = {rep.total_benchmark_events} (Train N = {rep.train_events_count}, Holdout N = {rep.holdout_events_count})")
        lines.append(f"- **Evaluation Tolerance Window**: `±{p.tolerance_days} days`")
        lines.append("")

        # 3. Empirical Profile Comparison Matrix
        lines.append("## 3. Empirical Profile Comparison Matrix")
        lines.append("")
        lines.append("| Predictive Profile | Holdout N | Hit Rate % | Precision | Recall | F1 Score | Holdout Brier | MAE (Days) | Median (Days) | P90 (Days) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for r in rep.rows:
            lines.append(
                f"| `{r.profile_name}` | {r.holdout_sample_size_n} | **{r.holdout_hit_rate_pct}%** | {r.holdout_precision:.2f} | {r.holdout_recall:.2f} | {r.holdout_f1_score:.2f} | {r.holdout_brier_score:.4f} | {r.holdout_mae_peak_days:.1f}d | {r.holdout_median_peak_offset_days:.1f}d | {r.holdout_p90_peak_offset_days:.1f}d |"
            )
        lines.append("")

        # 4. Inferential Statistical Significance & Paired Tests
        lines.append("## 4. Inferential Statistical Significance & Paired Tests")
        lines.append("")
        for sig in experiment.significance_reports:
            lines.append(f"### Candidate `{sig.profile_id}` vs Baseline `{sig.baseline_profile_id}`")
            lines.append("")
            lines.append(f"- **McNemar's Exact Paired Test p-value**: `{sig.mcnemar_test.p_value:.4f}` ({'Statistically Significant (p < 0.05)' if sig.mcnemar_test.is_significant else 'Not Significant (p >= 0.05)'})")
            lines.append(f"- **Odds Ratio (Advantage)**: `{sig.mcnemar_test.odds_ratio:.2f}` (Chi-square: `{sig.mcnemar_test.statistic:.2f}`)")
            lines.append(f"- **2000-Permutation Brier Test p-value**: `{sig.brier_permutation_p_value:.4f}`")
            lines.append(f"- **Scientific Verdict**: `{sig.verdict}`")
            lines.append("")
            lines.append("#### Paired 2x2 Contingency Matrix")
            lines.append("")
            t = sig.mcnemar_test.contingency_table
            lines.append("| | Candidate Hit | Candidate Miss |")
            lines.append("| :--- | :---: | :---: |")
            lines.append(f"| **Baseline Hit** | {t[0]} (Both Hit) | {t[1]} (Baseline Only) |")
            lines.append(f"| **Baseline Miss** | {t[2]} (Candidate Only) | {t[3]} (Both Missed) |")
            lines.append("")

            # 5. Bootstrap Confidence Intervals
            if sig.bootstrap_cis:
                lines.append("#### 1000-Iteration Empirical Bootstrap 95% Confidence Intervals")
                lines.append("")
                lines.append("| Metric | Point Estimate | 95% CI Lower | 95% CI Upper | Standard Error |")
                lines.append("| :--- | :---: | :---: | :---: | :---: |")
                for k, ci in sig.bootstrap_cis.items():
                    unit = "%" if "pct" in k else (" days" if "days" in k else "")
                    lines.append(f"| `{ci.metric_name}` | {ci.point_estimate}{unit} | {ci.ci_lower}{unit} | {ci.ci_upper}{unit} | {ci.standard_error:.4f} |")
                lines.append("")

        lines.append("---")
        lines.append("*Report certified by AstroOS Research Benchmark Lab.*")

        return "\n".join(lines)

    def generate_json_report(
        self,
        experiment: BenchmarkExperiment,
        decision: DecisionRecommendation,
    ) -> dict[str, Any]:
        """Generates a structured JSON research report."""
        p = experiment.provenance
        rep = experiment.report

        return {
            "experiment_id": p.experiment_id,
            "benchmark_id": p.benchmark_id,
            "benchmark_version": p.benchmark_version,
            "software_version": p.software_version,
            "timestamp": p.timestamp.isoformat(),
            "decision": {
                "status": decision.status.value,
                "recommended_profile_id": decision.recommended_profile_id,
                "baseline_profile_id": decision.baseline_profile_id,
                "confidence_score": decision.confidence_score,
                "key_evidence_drivers": list(decision.key_evidence_drivers),
                "risk_factors": list(decision.risk_factors),
                "sample_size_adequate": decision.sample_size_adequate,
                "requires_human_signoff": decision.requires_human_signoff,
            },
            "dataset_provenance": {
                "content_hash_sha256": p.content_hash_sha256,
                "results_hash_sha256": p.results_hash,
                "split_seed": p.split_seed,
                "train_ratio": p.train_ratio,
                "tolerance_days": p.tolerance_days,
                "total_events": rep.total_benchmark_events,
                "train_events": rep.train_events_count,
                "holdout_events": rep.holdout_events_count,
            },
            "comparison_matrix": [
                {
                    "profile_id": r.profile_id,
                    "profile_name": r.profile_name,
                    "holdout_hit_rate_pct": r.holdout_hit_rate_pct,
                    "holdout_precision": r.holdout_precision,
                    "holdout_recall": r.holdout_recall,
                    "holdout_f1_score": r.holdout_f1_score,
                    "holdout_brier_score": r.holdout_brier_score,
                    "holdout_mae_peak_days": r.holdout_mae_peak_days,
                    "holdout_median_peak_offset_days": r.holdout_median_peak_offset_days,
                    "holdout_p90_peak_offset_days": r.holdout_p90_peak_offset_days,
                }
                for r in rep.rows
            ],
            "significance_reports": [
                {
                    "profile_id": s.profile_id,
                    "baseline_profile_id": s.baseline_profile_id,
                    "mcnemar_test": {
                        "contingency_table": list(s.mcnemar_test.contingency_table),
                        "b_discordant": s.mcnemar_test.b_discordant_baseline_only,
                        "c_discordant": s.mcnemar_test.c_discordant_candidate_only,
                        "statistic": s.mcnemar_test.statistic,
                        "p_value": s.mcnemar_test.p_value,
                        "odds_ratio": s.mcnemar_test.odds_ratio,
                        "is_significant": s.mcnemar_test.is_significant,
                    },
                    "brier_permutation_p_value": s.brier_permutation_p_value,
                    "bootstrap_cis": {
                        k: {
                            "metric_name": v.metric_name,
                            "point_estimate": v.point_estimate,
                            "ci_lower": v.ci_lower,
                            "ci_upper": v.ci_upper,
                            "standard_error": v.standard_error,
                        }
                        for k, v in s.bootstrap_cis.items()
                    },
                    "verdict": s.verdict,
                }
                for s in experiment.significance_reports
            ],
        }

    def build_full_report(
        self,
        experiment: BenchmarkExperiment,
        baseline_profile_id: str = "parashari_standard_v1",
    ) -> StatisticalResearchReport:
        """Constructs full StatisticalResearchReport domain object."""
        decision = self._decision_engine.evaluate_experiment_decision(
            experiment=experiment,
            baseline_profile_id=baseline_profile_id,
        )
        md = self.generate_markdown_report(experiment, decision)
        js = self.generate_json_report(experiment, decision)
        exec_summary = (
            f"Decision: {decision.status.value}. "
            f"Recommended profile: {decision.recommended_profile_id} (Confidence: {int(decision.confidence_score * 100)}%). "
            f"{' '.join(decision.key_evidence_drivers)}"
        )

        return StatisticalResearchReport(
            experiment_id=experiment.provenance.experiment_id,
            benchmark_id=experiment.provenance.benchmark_id,
            benchmark_version=experiment.provenance.benchmark_version,
            decision=decision,
            executive_summary=exec_summary,
            markdown_content=md,
            json_content=js,
        )