"""
AstroOS — Workstream B: Health Gate Ablation Runner & Pre-Registered Evaluation
================================================================================

Single-pass evaluation of the full 4-step multiplicative gate + leave-one-stage-out ablations.
Evaluates the 124-positive Health cohort from data/kundalee/kundalee_clean.csv.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.divisional_vimshottari_engine import DivisionalVimshottariEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.health_gate import (
    ChartFactProvider,
    D30Confirmation,
    HealthGateConfig,
    HealthGateEngine,
    MarakaActivation,
    TriLifespanWindow,
)
from apps.api.services.lifespan_engine import LifespanEngine
from apps.api.services.multi_domain_cohort_validator import MultiDomainCohortValidator, RealPersonSubject
from apps.api.services.stats_hardening import build_honest_report, evaluate_all_domains
from packages.shared.enums import AyanamsaSystem, Rashi

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
KUNDALEE_CSV = REPO_ROOT / "data" / "kundalee" / "kundalee_clean.csv"
_RASHI_NAMES = [r.value for r in Rashi]


class AstroOSChartFactProvider(ChartFactProvider):
    """
    Adapter linking frozen AstroOS engines (LifespanEngine, DashaEngine, DivisionalVimshottariEngine)
    to HealthGateEngine.
    """

    def __init__(self, wrapper: EphemerisWrapper, subjects_map: Dict[str, RealPersonSubject]):
        self._wrapper = wrapper
        self._subjects = subjects_map
        self._lifespan_engine = LifespanEngine(wrapper)
        self._dasha_engine = DashaEngine(wrapper)
        self._div_dasha = DivisionalVimshottariEngine(wrapper)

        # Precompute charts, tri-lifespans, and dasha trees
        self._charts = {}
        self._tri_results = {}
        self._d1_dashas = {}
        self._d30_dashas = {}

        for pid, s in self._subjects.items():
            try:
                chart = self._wrapper.calculate(
                    dt=s.birth_dt_utc,
                    latitude=s.latitude,
                    longitude=s.longitude,
                    ayanamsa=AyanamsaSystem.LAHIRI.value,
                    house_system="W",
                )
                self._charts[pid] = chart
                self._tri_results[pid] = self._lifespan_engine.calculate_tri_lifespan_synthesis(chart)
                self._d1_dashas[pid] = self._dasha_engine.compute_vimshottari(
                    birth_datetime_utc=s.birth_dt_utc,
                    latitude=s.latitude,
                    longitude=s.longitude,
                    ayanamsa=AyanamsaSystem.LAHIRI.value,
                    house_system="W",
                    max_depth=2,
                )
            except Exception as e:
                logger.warning(f"Error computing facts for {pid}: {e}")

    def tri_lifespan_windows(self, subject_id: str) -> Sequence[TriLifespanWindow]:
        s = self._subjects.get(subject_id)
        tri = self._tri_results.get(subject_id)
        if not s or not tri:
            return []

        b_date = s.birth_dt_utc.date()
        # Mean lifespan target year
        target_age = tri.mean_lifespan_years
        # Vulnerable window: target_age ± 6 years
        start_date = b_date + timedelta(days=int(max(0, target_age - 6.0) * 365.25))
        end_date = b_date + timedelta(days=int((target_age + 6.0) * 365.25))

        # Methods concurring based on consistency of pindayu, amshayu, nisargayu
        concurring = set()
        p_yr = tri.pindayu.total_years
        a_yr = tri.amshayu.total_years
        n_yr = tri.nisargayu.total_years

        if abs(p_yr - target_age) <= 10.0:
            concurring.add("vpc")
        if abs(a_yr - target_age) <= 10.0:
            concurring.add("mpc")
        if abs(n_yr - target_age) <= 10.0:
            concurring.add("tridasha")

        if not concurring:
            concurring.add("vpc")

        return [TriLifespanWindow(start=start_date, end=end_date, methods_concurring=frozenset(concurring))]

    def maraka_activations(self, subject_id: str, window: tuple[date, date]) -> Sequence[MarakaActivation]:
        tri = self._tri_results.get(subject_id)
        d1_tree = self._d1_dashas.get(subject_id)
        if not tri or not d1_tree:
            return []

        maraka_eval = tri.maraka_assessment
        high_risk = set(maraka_eval.high_risk_dasha_lords)
        activations = []

        ws, we = window
        for md in d1_tree.mahadashas:
            for ad in md.sub_periods:
                if ad.end_date < ws or ad.start_date > we:
                    continue
                # Map operator
                op = None
                if ad.lord in maraka_eval.primary_maraka_lords:
                    op = "lord2" if ad.lord == maraka_eval.primary_maraka_lords[0] else "lord7"
                elif ad.lord == "saturn" and maraka_eval.is_saturn_maraka_absorber:
                    op = "saturn"
                elif ad.lord == "rahu" and "rahu" in high_risk:
                    op = "rahu"
                elif ad.lord in maraka_eval.secondary_maraka_lords:
                    op = "lord8_afflicted"

                if op:
                    activations.append(MarakaActivation(
                        operator=op,
                        dasha_span=(ad.start_date, ad.end_date),
                        is_primary=op in ("lord2", "lord7"),
                    ))

        return activations

    def d30_confirmations(self, subject_id: str, window: tuple[date, date]) -> Sequence[D30Confirmation]:
        tri = self._tri_results.get(subject_id)
        chart = self._charts.get(subject_id)
        if not tri or not chart:
            return []

        maraka_eval = tri.maraka_assessment
        confirmations = []

        # 1. Maraka lords afflicted in D30
        for p in maraka_eval.d30_afflicted_planets:
            if p in maraka_eval.primary_maraka_lords:
                confirmations.append(D30Confirmation(channel="maraka_lord_in_d30_affliction", strength=0.9))
            elif p == "saturn":
                confirmations.append(D30Confirmation(channel="d30_8th_transit_hit", strength=0.8))
            else:
                confirmations.append(D30Confirmation(channel="d30_6th_activation", strength=0.7))

        if not confirmations:
            confirmations.append(D30Confirmation(channel="d30_6th_activation", strength=0.2))

        return confirmations

    def sub_period_lords(self, subject_id: str, window: tuple[date, date]) -> Sequence[str]:
        d1_tree = self._d1_dashas.get(subject_id)
        if not d1_tree:
            return []
        ws, we = window
        lords = []
        for md in d1_tree.mahadashas:
            for ad in md.sub_periods:
                if not (ad.end_date < ws or ad.start_date > we):
                    lords.append(ad.lord)
        return lords


NEUTRALIZER = {
    "gate_full": None,
    "ablate_tri": ("w_tri", 1.0),
    "ablate_d1": ("w_d1", 1.0),
    "ablate_d30": ("w_d30", 1.0),
    "ablate_antikill": ("w_antikill", 1.0),
}


def run_health_ablation_benchmark():
    print("=" * 70)
    print("ASTROOS WORKSTREAM B: HEALTH 4-STEP MULTIPLICATIVE GATE ABLATION")
    print("=" * 70)

    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    validator = MultiDomainCohortValidator(wrapper)

    print(f"Loading authentic Health cohort from {KUNDALEE_CSV}...")
    subjects = validator.load_authentic_cohort_from_csv(KUNDALEE_CSV, max_persons=120, min_confidence="high")
    subjects_map = {s.person_id: s for s in subjects}
    print(f"Loaded {len(subjects)} verified real subjects.\n")

    provider = AstroOSChartFactProvider(wrapper, subjects_map)
    engine = HealthGateEngine(provider, HealthGateConfig())

    # Generate slices for health domain
    all_slices = []
    for s in subjects:
        slices = validator.generate_domain_slices_for_subject(s, domain="HEALTH")
        all_slices.extend(slices)

    sorted_slices = sorted(all_slices, key=lambda sl: sl.slice_start)
    y_true = np.array([sl.label for sl in sorted_slices], dtype=int)
    positives = int(y_true.sum())
    total = len(y_true)
    print(f"Total Slices: {total} | Positives: {positives} (Base Rate: {positives/total:.2%})\n")

    # Evaluate each gate variant
    print(f"{'VARIANT':<18} | {'AUC':<7} | {'DeLong 95% CI':<16} | {'p (MW)':<8} | {'p (BH)':<8} | {'BSS':<8} | {'Lift':<6} | {'VERDICT'}")
    print("-" * 95)

    results_dict = {}
    ablation_payloads = {}

    for name, neutralize in NEUTRALIZER.items():
        gate_scores = []
        for sl in sorted_slices:
            res = engine.evaluate(sl.person_id, (sl.slice_start, sl.slice_end))
            if neutralize:
                attr, val = neutralize
                w_tri = res.w_tri if attr != "w_tri" else val
                w_d1 = res.w_d1 if attr != "w_d1" else val
                w_d30 = res.w_d30 if attr != "w_d30" else val
                w_ak = res.w_antikill if attr != "w_antikill" else val
                score = w_tri * w_d1 * w_d30 * w_ak
            else:
                score = res.gate_score
            gate_scores.append(score)

        y_score = np.array(gate_scores, dtype=float)
        ablation_payloads[name] = {
            "y_true": y_true,
            "y_score": y_score,
            "probs": y_score,
        }

    eval_results = evaluate_all_domains(ablation_payloads, k_values=(50, 100))

    for ev in eval_results:
        ci = ev.auc.ci_logit
        ci_str = f"[{ci[0]:.3f}, {ci[1]:.3f}]" if not np.isnan(ci[0]) else "N/A"
        p_mw_str = f"{ev.p_raw_mannwhitney:.4f}" if ev.p_raw_mannwhitney is not None else "N/A"
        p_bh_str = f"{ev.p_bh_adjusted:.4f}" if not np.isnan(ev.p_bh_adjusted) else "N/A"
        bss_str = f"{ev.brier.bss:+.2f}" if not np.isnan(ev.brier.bss) else "N/A"
        lift_str = f"{ev.ranking.top_decile_lift:.2f}x"

        print(f"{ev.domain:<18} | {ev.auc.auc:.4f}  | {ci_str:<16} | {p_mw_str:<8} | {p_bh_str:<8} | {bss_str:<8} | {lift_str:<6} | {ev.verdict}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_health_ablation_benchmark()
