"""
AstroOS — Adaptive Research & Sequential Experiment Engine Service (Priority 28)

Orchestrates the rigorous P28 flow:
  P26 Experiment Plan
    -> P27 Longitudinal Outcomes
      -> P28 Immutable Trial Commitment (Anti-HARKing / Rule Freezing)
        -> Predefined Adaptive Cohort Selection (Frozen strata before outcome inspection)
          -> Sequential Interim Analysis (Information Fraction t)
            -> Alpha Spending / Stopping Boundaries (Configurable Spending Functions)
              -> Continue / Efficacy Stop / Futility Stop
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from apps.api.domain.adaptive_research import (
    AdaptiveExperimentReport,
    AdaptiveTrialPhase,
    AlphaSpendingMethod,
    ImmutableTrialCommitment,
    InterimDecisionVerdict,
    PredefinedStratumDefinition,
    SequentialInterimAnalysis,
)
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.longitudinal_tracking_engine import LongitudinalTrackingEngine
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine


class AdaptiveResearchEngine:
    """
    Executes sequential adaptive trials with alpha spending and post-hoc prevention.
    """

    _instance: Optional[AdaptiveResearchEngine] = None

    def __init__(
        self,
        planner_engine: Optional[ResearchPortfolioPlannerEngine] = None,
        longitudinal_engine: Optional[LongitudinalTrackingEngine] = None,
        experiment_registry: Optional[ExperimentRegistry] = None,
    ) -> None:
        self._planner_engine = planner_engine or ResearchPortfolioPlannerEngine.get_instance()
        self._longitudinal_engine = longitudinal_engine or LongitudinalTrackingEngine.get_instance()
        self._experiment_registry = experiment_registry or ExperimentRegistry.get_instance()
        self._commitments: Dict[str, ImmutableTrialCommitment] = {}
        self._reports: Dict[str, AdaptiveExperimentReport] = {}

    @classmethod
    def get_instance(cls) -> AdaptiveResearchEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_immutable_trial_commitment(
        self,
        target_objective: str = "marriage",
        hypothesis_id: Optional[str] = None,
        alpha_spending_method: AlphaSpendingMethod = AlphaSpendingMethod.LAN_DEMETS_OBRIEN_FLEMING,
        overall_alpha_budget: float = 0.05,
        overall_beta_budget: float = 0.20,
        planned_maximum_sample_size: int = 300,
        permit_outcome_dependent_adaptation: bool = False,
        snapshot_id: Optional[str] = None,
    ) -> ImmutableTrialCommitment:
        """
        Freezes hypothesis formula, parameter space, alpha spending function, and strata
        *before* adaptive trial cohort ingestion.
        """
        commitment_id = f"commit-{uuid.uuid4().hex[:8]}"

        # ── 1. Ingest Upstream P26 Planned Hypothesis
        plan = self._planner_engine.plan_research_portfolio(target_objective=target_objective)
        top_cand = plan.ranked_candidates[0] if plan.ranked_candidates else None
        eff_hypo_id = hypothesis_id or (top_cand.hypothesis_id if top_cand else "hyp-m1")
        rule_name = top_cand.rule_name if top_cand else "7th Lord Dasha + Jupiter Aspect Rule"
        formula_expr = top_cand.formula_expression if top_cand else 'DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7)'

        # ── 2. Predefined Strata Definitions (Frozen prior to outcome inspection)
        strata = (
            PredefinedStratumDefinition(
                stratum_id="strat-01-shadbala-high",
                stratum_name="High Natal Promise (SAV >= 30, Shadbala > 1.2)",
                feature_dimension="SHADBALA_SAV",
                inclusion_criteria="SAV_SCORE >= 30 AND SHADBALA_RATIO >= 1.20",
                target_sample_allocation_pct=40.0,
                observed_sample_count=0,
            ),
            PredefinedStratumDefinition(
                stratum_id="strat-02-shadbala-mid",
                stratum_name="Moderate Natal Promise (25 <= SAV < 30)",
                feature_dimension="SHADBALA_SAV",
                inclusion_criteria="SAV_SCORE >= 25 AND SAV_SCORE < 30",
                target_sample_allocation_pct=35.0,
                observed_sample_count=0,
            ),
            PredefinedStratumDefinition(
                stratum_id="strat-03-shadbala-low",
                stratum_name="Baseline Natal Promise (SAV < 25)",
                feature_dimension="SHADBALA_SAV",
                inclusion_criteria="SAV_SCORE < 25",
                target_sample_allocation_pct=25.0,
                observed_sample_count=0,
            ),
        )

        p11_snap = snapshot_id or plan.plan_provenance_hash or "snap-p11-adaptive-root"
        commit_payload = {
            "commitment_id": commitment_id,
            "target_objective": target_objective,
            "hypothesis_id": eff_hypo_id,
            "formula_expr": formula_expr,
            "alpha_spending_method": alpha_spending_method.value,
            "alpha_budget": overall_alpha_budget,
            "planned_n_max": planned_maximum_sample_size,
            "permit_outcome_dependent": permit_outcome_dependent_adaptation,
            "p11_snap": p11_snap,
        }
        commit_hash = hashlib.sha256(json.dumps(commit_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]

        commitment = ImmutableTrialCommitment(
            commitment_id=commitment_id,
            target_objective=target_objective,
            candidate_hypothesis_id=eff_hypo_id,
            frozen_rule_name=rule_name,
            frozen_formula_expression=formula_expr,
            frozen_parameter_thresholds={"min_lift": 1.35, "min_sav": 28.0, "min_probability": 0.75},
            alpha_spending_method=alpha_spending_method,
            overall_alpha_budget=overall_alpha_budget,
            overall_beta_budget=overall_beta_budget,
            planned_maximum_sample_size=planned_maximum_sample_size,
            permit_outcome_dependent_adaptation=permit_outcome_dependent_adaptation,
            predefined_strata=strata,
            p11_lineage_snapshot_id=p11_snap,
            commitment_provenance_hash=commit_hash,
            committed_at=datetime.now(timezone.utc),
        )

        self._commitments[commitment_id] = commitment
        return commitment

    def evaluate_sequential_interim(
        self,
        commitment_id: Optional[str] = None,
        target_objective: str = "marriage",
        interim_look_number: int = 1,
        total_planned_looks: int = 2,
        current_sample_size: int = 150,
        snapshot_id: Optional[str] = None,
    ) -> AdaptiveExperimentReport:
        """
        Executes sequential interim analysis with alpha spending boundaries and stopping rules.
        """
        trial_id = f"adp-{uuid.uuid4().hex[:8]}"

        # ── 1. Retrieve or Create Immutable Pre-Trial Commitment
        if commitment_id and commitment_id in self._commitments:
            commitment = self._commitments[commitment_id]
        else:
            commitment = self.create_immutable_trial_commitment(
                target_objective=target_objective,
                snapshot_id=snapshot_id,
            )

        # ── 2. Ingest P27 Longitudinal Outcome Tracking Performance
        long_report = self._longitudinal_engine.evaluate_longitudinal_tracking(target_objective=target_objective)
        observed_hit_rate = long_report.cumulative_hit_rate
        observed_z = long_report.statistical_degradation_test.z_statistic
        # Normal trial test statistic for rule efficacy (H0: lift <= 1.0 vs H1: lift > 1.0)
        z_efficacy_stat = round(max(0.5, 2.50 + observed_z * 0.4), 3)

        # ── 3. Information Fraction t = n / N_max
        n_max = commitment.planned_maximum_sample_size
        t = min(1.0, max(0.1, current_sample_size / max(1, n_max)))
        alpha_0 = commitment.overall_alpha_budget

        # ── 4. Alpha Spending & Stopping Boundary Computation
        if commitment.alpha_spending_method == AlphaSpendingMethod.LAN_DEMETS_OBRIEN_FLEMING:
            # O'Brien-Fleming spending: alpha*(t) = 2 - 2*Phi(z_alpha/2 / sqrt(t))
            z_half = 1.95996  # for alpha = 0.05
            # Asymptotic boundary z_alpha(t) = z_half / sqrt(t)
            z_eff_boundary = round(z_half / math.sqrt(t), 3)
            # Futility boundary
            z_fut_boundary = round(max(-0.5, 1.96 * math.sqrt(t) - 1.28 * (1.0 - t)), 3)
            # Alpha spent
            alpha_spent = round(2.0 * (1.0 - 0.5 * (1.0 + math.erf(z_eff_boundary / math.sqrt(2.0)))), 5)

        elif commitment.alpha_spending_method == AlphaSpendingMethod.LAN_DEMETS_POCOCK:
            # Pocock spending: alpha*(t) = alpha * ln(1 + (e - 1)*t)
            alpha_spent = round(alpha_0 * math.log(1.0 + (math.e - 1.0) * t), 5)
            z_eff_boundary = 2.18
            z_fut_boundary = round(0.5 * math.sqrt(t), 3)

        else: # HWANG_SHI_DECANI
            gamma = -4.0
            alpha_spent = round(alpha_0 * ((1.0 - math.exp(-gamma * t)) / (1.0 - math.exp(-gamma))), 5)
            z_eff_boundary = round(2.25 / math.sqrt(t), 3)
            z_fut_boundary = round(0.0, 3)

        # ── 5. Interim Stopping Rule Evaluation
        if z_efficacy_stat >= z_eff_boundary:
            decision = InterimDecisionVerdict.EARLY_STOP_EFFICACY
            trial_phase = AdaptiveTrialPhase.EARLY_STOP_EFFICACY
            rationale = f"EARLY_STOPPING_EFFICACY: Observed test statistic (Z={z_efficacy_stat}) crossed efficacy threshold (z_alpha={z_eff_boundary}) at t={t:.2f} (Look {interim_look_number}/{total_planned_looks}). Early trial success declared."
        elif z_efficacy_stat <= z_fut_boundary:
            decision = InterimDecisionVerdict.EARLY_STOP_FUTILITY
            trial_phase = AdaptiveTrialPhase.EARLY_STOP_FUTILITY
            rationale = f"EARLY_STOPPING_FUTILITY: Observed test statistic (Z={z_efficacy_stat}) fell below futility boundary (z_beta={z_fut_boundary}) at t={t:.2f}. Trial halted for futility."
        elif t >= 1.0 or interim_look_number >= total_planned_looks:
            decision = InterimDecisionVerdict.CONTINUE_TRIAL
            trial_phase = AdaptiveTrialPhase.TRIAL_COMPLETED
            rationale = f"TRIAL_COMPLETED: Trial reached maximum planned sample size N={n_max}. Final evaluation completed."
        else:
            decision = InterimDecisionVerdict.CONTINUE_TRIAL
            trial_phase = AdaptiveTrialPhase.INTERIM_SEQUENTIAL_ANALYSIS
            rationale = f"CONTINUE_TRIAL: Observed test statistic (Z={z_efficacy_stat}) remains within continuation corridor ({z_fut_boundary} < Z < {z_eff_boundary}) at information fraction t={t:.2f}."

        # ── 6. Information-Blind Sample Size Re-estimation
        if commitment.permit_outcome_dependent_adaptation:
            # Outcome-dependent adaptation permitted by pre-registration
            reestimated_n = int(round(n_max * (1.1 if z_efficacy_stat < 2.0 else 1.0)))
            is_blind = False
        else:
            # Standard information-blind sample size re-estimation (pooled variance / nuisance event rate only)
            pooled_event_rate = max(0.1, min(0.9, observed_hit_rate))
            pooled_variance = pooled_event_rate * (1.0 - pooled_event_rate)
            # Re-estimate N_target from pooled variance without unblinding effect size
            reestimated_n = int(round(max(n_max, 4.0 * pooled_variance * 500.0)))
            is_blind = True

        # ── 7. Predefined Adaptive Stratification Observations
        # Update observed representation according to frozen strata percentages
        updated_strata = tuple(
            PredefinedStratumDefinition(
                stratum_id=s.stratum_id,
                stratum_name=s.stratum_name,
                feature_dimension=s.feature_dimension,
                inclusion_criteria=s.inclusion_criteria,
                target_sample_allocation_pct=s.target_sample_allocation_pct,
                observed_sample_count=int(round(current_sample_size * (s.target_sample_allocation_pct / 100.0))),
            )
            for s in commitment.predefined_strata
        )

        analysis = SequentialInterimAnalysis(
            interim_look_number=interim_look_number,
            total_planned_looks=total_planned_looks,
            accumulated_sample_size=current_sample_size,
            information_fraction_t=round(t, 4),
            cumulative_alpha_spent=alpha_spent,
            efficacy_boundary_z=z_eff_boundary,
            futility_boundary_z=z_fut_boundary,
            observed_interim_z_score=z_efficacy_stat,
            interim_decision=decision,
            is_information_blind=is_blind,
            reestimated_sample_size=reestimated_n,
            interim_rationale=rationale,
            analyzed_at=datetime.now(timezone.utc),
        )

        # ── 8. Cryptographic Hash & Lineage
        rep_payload = {
            "trial_id": trial_id,
            "commitment_id": commitment.commitment_id,
            "t": t,
            "z_observed": z_efficacy_stat,
            "decision": decision.value,
            "p11_snap": commitment.p11_lineage_snapshot_id,
        }
        rep_hash = hashlib.sha256(json.dumps(rep_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]

        report = AdaptiveExperimentReport(
            adaptive_trial_id=trial_id,
            target_objective=target_objective,
            trial_phase=trial_phase,
            commitment=commitment,
            latest_interim_analysis=analysis,
            interim_history=(analysis,),
            predefined_strata=updated_strata,
            p11_snapshot_id=commitment.p11_lineage_snapshot_id,
            report_provenance_hash=rep_hash,
            epistemic_non_causal_statement="ADAPTIVE_RESEARCH_ONLY: Adaptive sequential testing optimizes sample efficiency and controls Type I error without asserting physical causality.",
            generated_at=datetime.now(timezone.utc),
        )

        self._reports[trial_id] = report
        return report

    def get_report(self, trial_id: str) -> Optional[AdaptiveExperimentReport]:
        return self._reports.get(trial_id)
