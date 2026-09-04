"""
AstroOS — Matched Negative Control Sampler & Case-Crossover Evaluator.

Governing Contract: NEGATIVE-CONTROL-CONTRACT-v1.1 (frozen & hashed).

Pre-flight Invariants Enforced:
1. Sampler Blindness: Zero imports from scoring engines or model outputs.
2. Exact Deterministic Seeding: SHA-256 HMAC over (base_seed || event_id).
3. Two-Layer Matching Composition (3 Within + 2 Cross):
   - 3 within-subject negatives outside the asymmetric forward-exclusion window -> AUC_temporal
   - 2 cross-subject negatives matched on (birth_decade × region × source_class) -> AUC_between
4. Case-Crossover Conditional Logistic Regression: Subject as stratum, computing
   Odds Ratio (OR) per 1 SD score with 95% Wald CI and p-value.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
from scipy.optimize import minimize
from scipy import stats as sps


@dataclass(frozen=True)
class NegativeControlContract:
    version: str = "NEGATIVE-CONTROL-CONTRACT-v1.1"
    base_seed: str = "ASTROOS-MATCHED-CONTROL-SEED-2026"
    ratio_within: int = 3
    ratio_cross: int = 2
    total_ratio: int = 5
    relaxation_order: Tuple[str, ...] = ("region", "birth_decade")
    asymmetric_forward_exclusion: bool = True

    def content_hash(self) -> str:
        blob = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


ACTIVE_NEGATIVE_CONTRACT = NegativeControlContract()


@dataclass(frozen=True)
class MatchedSlicePair:
    positive_slice_id: str
    subject_ref: str
    event_date: date
    within_negative_slice_ids: Tuple[str, ...]
    cross_negative_slice_ids: Tuple[str, ...]


@dataclass
class StratumCensusReport:
    total_cells: int
    cell_counts: Dict[str, int]
    underpopulated_cells: List[str]
    relaxation_counts: Dict[str, int] = field(default_factory=lambda: {"exact_cell": 0, "relaxed_region": 0, "relaxed_decade": 0})


class MatchedNegativeSampler:
    def __init__(self, contract: NegativeControlContract = ACTIVE_NEGATIVE_CONTRACT):
        self.contract = contract

    def sample_matched_negatives(
        self,
        positive_events: Sequence[dict],
        all_slices: Sequence[dict],
        subjects_strata: Dict[str, dict],
    ) -> Tuple[List[MatchedSlicePair], StratumCensusReport]:
        by_subject: Dict[str, List[dict]] = {}
        for sl in all_slices:
            s_id = sl["subject_ref"]
            by_subject.setdefault(s_id, []).append(sl)

        stratum_pool: Dict[str, List[str]] = {}
        for s_id, strata in subjects_strata.items():
            cell = f"{strata.get('birth_decade', 'unknown')}:{strata.get('region', 'unknown')}:{strata.get('source_class', 'AA')}"
            stratum_pool.setdefault(cell, []).append(s_id)

        census_counts = {cell: len(subj_list) for cell, subj_list in stratum_pool.items()}
        underpopulated = [cell for cell, count in census_counts.items() if count < self.contract.ratio_cross]
        census = StratumCensusReport(
            total_cells=len(stratum_pool),
            cell_counts=census_counts,
            underpopulated_cells=underpopulated,
        )

        matched_pairs: List[MatchedSlicePair] = []

        for pe in positive_events:
            s_id = pe["subject_ref"]
            ev_date = pe["event_date"]
            tol_days = pe.get("tolerance_days", 90)

            # Layer 1: Within-subject negatives (3 slices)
            candidate_within = []
            for sl in by_subject.get(s_id, []):
                if sl["label"] == 0:
                    # Asymmetric forward exclusion
                    if not (ev_date <= sl["slice_start"] <= ev_date + timedelta(days=tol_days)):
                        candidate_within.append(sl["slice_id"])

            # Deterministic hash seed
            h_seed_within = int(hashlib.sha256(f"{self.contract.base_seed}:{pe['event_id']}:within".encode()).hexdigest()[:8], 16)
            rng_within = np.random.RandomState(h_seed_within)
            if len(candidate_within) >= self.contract.ratio_within:
                selected_within = tuple(rng_within.choice(candidate_within, size=self.contract.ratio_within, replace=False))
            else:
                selected_within = tuple(candidate_within)

            # Layer 2: Cross-subject negatives (2 slices)
            s_strata = subjects_strata.get(s_id, {})
            cell = f"{s_strata.get('birth_decade', 'unknown')}:{s_strata.get('region', 'unknown')}:{s_strata.get('source_class', 'AA')}"
            eligible_subjects = [sub for sub in stratum_pool.get(cell, []) if sub != s_id]

            if len(eligible_subjects) >= self.contract.ratio_cross:
                census.relaxation_counts["exact_cell"] += 1
            else:
                # Relaxation 1: Region relaxed
                relaxed_cell_prefix = f"{s_strata.get('birth_decade', 'unknown')}:"
                eligible_subjects = [
                    sub for c_k, sub_list in stratum_pool.items()
                    if c_k.startswith(relaxed_cell_prefix)
                    for sub in sub_list if sub != s_id
                ]
                census.relaxation_counts["relaxed_region"] += 1

            selected_cross = []
            if eligible_subjects:
                h_seed_cross = int(hashlib.sha256(f"{self.contract.base_seed}:{pe['event_id']}:cross".encode()).hexdigest()[:8], 16)
                rng_cross = np.random.RandomState(h_seed_cross)
                chosen_subjects = rng_cross.choice(
                    eligible_subjects,
                    size=min(self.contract.ratio_cross, len(eligible_subjects)),
                    replace=False,
                )
                for c_sub in chosen_subjects:
                    neg_slices = [sl["slice_id"] for sl in by_subject.get(c_sub, []) if sl["label"] == 0]
                    if neg_slices:
                        selected_cross.append(neg_slices[0])

            matched_pairs.append(MatchedSlicePair(
                positive_slice_id=pe["slice_id"],
                subject_ref=s_id,
                event_date=ev_date,
                within_negative_slice_ids=selected_within,
                cross_negative_slice_ids=tuple(selected_cross),
            ))

        return matched_pairs, census


def evaluate_temporal_vs_between_auc(
    matched_pairs: Sequence[MatchedSlicePair],
    scores_map: Dict[str, float],
) -> Dict[str, float]:
    """
    Computes AUC_temporal, AUC_between, combined matched AUC, and
    Case-Crossover Conditional Logistic Regression Odds Ratio (OR).
    """
    within_wins, within_total = 0.0, 0
    cross_wins, cross_total = 0.0, 0

    # For Conditional Logistic Regression (1 case + M within-controls per stratum)
    strata_data = []

    for pair in matched_pairs:
        pos_s = scores_map.get(pair.positive_slice_id, 0.0)

        # Within comparisons
        within_stratum = [(1, pos_s)]
        for w_id in pair.within_negative_slice_ids:
            neg_s = scores_map.get(w_id, 0.0)
            within_total += 1
            if pos_s > neg_s:
                within_wins += 1.0
            elif pos_s == neg_s:
                within_wins += 0.5
            within_stratum.append((0, neg_s))

        if len(within_stratum) > 1:
            strata_data.append(within_stratum)

        # Cross comparisons
        for c_id in pair.cross_negative_slice_ids:
            neg_s = scores_map.get(c_id, 0.0)
            cross_total += 1
            if pos_s > neg_s:
                cross_wins += 1.0
            elif pos_s == neg_s:
                cross_wins += 0.5

    auc_temporal = within_wins / within_total if within_total > 0 else 0.5
    auc_between = cross_wins / cross_total if cross_total > 0 else 0.5
    combined_auc = (within_wins + cross_wins) / (within_total + cross_total) if (within_total + cross_total) > 0 else 0.5

    # Conditional Logistic Regression Estimation
    clogit_res = _fit_conditional_logistic(strata_data)

    return {
        "auc_temporal": round(auc_temporal, 4),
        "auc_between": round(auc_between, 4),
        "auc_combined_matched": round(combined_auc, 4),
        "within_comparisons": within_total,
        "cross_comparisons": cross_total,
        "clogit_odds_ratio": clogit_res["or"],
        "clogit_or_ci": clogit_res["ci"],
        "clogit_pvalue": clogit_res["pvalue"],
    }


def _fit_conditional_logistic(strata_data: List[List[Tuple[int, float]]]) -> Dict[str, any]:
    """
    Fits 1:M Conditional Logistic Regression via exact conditional log-likelihood maximization.
    Computes Odds Ratio per 1 SD of score.
    """
    if not strata_data:
        return {"or": 1.0, "ci": (1.0, 1.0), "pvalue": 1.0}

    # Gather all scores to standardize to 1 SD
    all_scores = [s for stratum in strata_data for _, s in stratum]
    std_s = float(np.std(all_scores)) if len(all_scores) > 1 and np.std(all_scores) > 1e-6 else 1.0

    def neg_loglik(beta):
        b = beta[0]
        nll = 0.0
        for stratum in strata_data:
            case_score = next(s for y, s in stratum if y == 1) / std_s
            exp_sum = sum(math.exp(s / std_s * b) for _, s in stratum)
            nll -= (case_score * b - math.log(max(1e-15, exp_sum)))
        return nll

    res = minimize(neg_loglik, [0.0], method="L-BFGS-B")
    beta_hat = float(res.x[0])

    # Numerical second derivative (Hessian) for SE
    h = 1e-4
    f0 = neg_loglik([beta_hat])
    fp = neg_loglik([beta_hat + h])
    fm = neg_loglik([beta_hat - h])
    d2 = (fp - 2 * f0 + fm) / (h * h)
    se = 1.0 / math.sqrt(d2) if d2 > 0 else float("inf")

    odds_ratio = math.exp(beta_hat)
    ci_lo = math.exp(beta_hat - 1.96 * se)
    ci_hi = math.exp(beta_hat + 1.96 * se)
    z = beta_hat / se if se > 0 and not math.isinf(se) else 0.0
    pval = 2.0 * (1.0 - sps.norm.cdf(abs(z)))

    return {
        "or": round(odds_ratio, 3),
        "ci": (round(ci_lo, 3), round(ci_hi, 3)),
        "pvalue": round(pval, 4),
    }
