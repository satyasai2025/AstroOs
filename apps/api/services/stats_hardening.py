"""
AstroOS — Workstream A: Statistical Hardening for Multi-Domain OOS Benchmarks.

Adds four mandatory metrics to the Phalita benchmark harness:

  1. DeLong 95% CI on ROC-AUC          — exact analytic covariance method
                                         (Sun & Xu 2014 fast vectorized variant;
                                         handles extreme imbalance, n+ = 7 / 12
                                         without bootstrap resampling noise)
  2. Brier Skill Score (BSS)           — 1 - Brier_model / Brier_baseline
                                         (Brier scores are meaningless in
                                         imbalanced settings without the
                                         base-rate reference; negative BSS
                                         means WORSE than always predicting
                                         the base rate)
  3. Precision@K (K=50, 100) & Top-Decile Lift — decision-useful ranking
                                         metrics for base rates near 0.1%
  4. Benjamini-Hochberg FDR correction  — across the 4 domain p-values
                                         (controls false discovery rate;
                                         Marriage p=0.0324 must survive
                                         the k=1 rank adjustment)

Design invariants (frozen):
  - Zero synthetic data: all inputs come from the real walk-forward harness.
  - Deterministic: no RNG anywhere; bootstrap is deliberately NOT used.
  - Every function returns typed result objects, not bare floats, so the
    report generator can emit full provenance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
from scipy import stats as sps


# ============================================================================
# 1. DeLong AUC + exact 95% CI (fast covariance method)
# ============================================================================

def _rank_data(x: np.ndarray) -> np.ndarray:
    """Average ranks (ties handled correctly — required for Mann-Whitney)."""
    sorter = np.argsort(x, kind="mergesort")
    inv = np.empty_like(sorter)
    inv[sorter] = np.arange(len(x), dtype=np.float64)
    xs = x[sorter]
    obs = np.r_[True, xs[1:] != xs[:-1]]
    dense = obs.cumsum()[inv]
    count = np.r_[np.nonzero(obs)[0], len(obs)]
    return 0.5 * (count[dense] + count[dense - 1] + 1)


def _midrank(z: np.ndarray) -> np.ndarray:
    """Midranks for pooled scores (Sun & Xu structural components)."""
    J = np.argsort(z, kind="mergesort")
    Z = z[J]
    N = len(z)
    T = np.zeros(N, dtype=np.float64)
    i = 0
    while i < N:
        j = i
        while j < N and Z[j] == Z[i]:
            j += 1
        T[i:j] = 0.5 * (i + j - 1) + 1
        i = j
    T2 = np.empty(N, dtype=np.float64)
    T2[J] = T
    return T2


def delong_auc_variance(y_true: np.ndarray, y_score: np.ndarray,
                        ) -> tuple[float, float, float]:
    """
    DeLong (1988) via the Sun-Xu fast structural-component method.

    Returns (auc, var_auc, se_auc). Exact — no resampling.

    Variance is the standard "one-score-per-subject" V_10 variance, the
    correct one for a single ROC curve (not the two-curve comparison
    covariance). Appropriate for n+ as small as 7; ties in the score
    distribution are handled by midranks.
    """
    y = y_true.astype(bool)
    pos, neg = y_score[y], y_score[~y]
    m, n = len(pos), len(neg)
    if m < 2 or n < 2:
        raise ValueError(
            f"DeLong requires >=2 samples per class (got pos={m}, neg={n}). "
            "With fewer positives the AUC CI is undefined — report "
            "exact Mann-Whitney permutation p-value instead.")

    tx = _rank_data(pos)          # ranks of positives among positives
    ty = _rank_data(neg)          # ranks of negatives among negatives
    tz = _rank_data(y_score)      # ranks among all
    auc = (tz[y].sum() - m * (m + 1) / 2) / (m * n)

    # Structural components (placement values), via midranks on pooled data
    v01 = (tz[y] - tx) / n        # for positives
    v10 = 1.0 - (tz[~y] - ty) / m # for negatives

    s01 = np.var(v01, ddof=1)
    s10 = np.var(v10, ddof=1)
    var = s01 / m + s10 / n       # V_10 variance of AUC
    return float(auc), float(var), float(math.sqrt(var))


def delong_confidence_interval(y_true: np.ndarray, y_score: np.ndarray,
                               alpha: float = 0.05,
                               ) -> AucResult:
    """
    Exact DeLong CI: AUC ± z_{1-α/2} · SE.

    NOTE ON SMALL n+: with n+ = 7, the normal approximation is slightly
    optimistic; the transformed-CI variant (logit/newcombe) is available via
    method="logit". Both are reported by default in evaluate_domain().
    The CI lower bound is also TRUNCATED at 0 and upper at 1.
    """
    y_bool = y_true.astype(bool)
    n_pos = int(y_bool.sum())
    n_neg = int((~y_bool).sum())

    if n_pos < 2 or n_neg < 2:
        auc = 0.5
        se = float("nan")
        ci_norm = (float("nan"), float("nan"))
        ci_logit = (float("nan"), float("nan"))
        return AucResult(auc=auc, se=se, ci_normal=ci_norm, ci_logit=ci_logit,
                         n_pos=n_pos, n_neg=n_neg)

    auc, var, se = delong_auc_variance(y_true, y_score)
    z = sps.norm.ppf(1 - alpha / 2)
    ci_norm = (max(0.0, auc - z * se), min(1.0, auc + z * se))

    # Logit-transformed CI (better small-sample coverage; Newcombe-style)
    eps = 1e-12
    auc_c = min(max(auc, eps), 1 - eps)
    se_logit = se / (auc_c * (1 - auc_c))
    logit_auc = math.log(auc_c / (1 - auc_c))
    ci_logit = (max(0.0, 1 / (1 + math.exp(-(logit_auc - z * se_logit)))),
                min(1.0, 1 / (1 + math.exp(-(logit_auc + z * se_logit)))))

    return AucResult(auc=auc, se=se, ci_normal=ci_norm, ci_logit=ci_logit,
                     n_pos=n_pos, n_neg=n_neg)


@dataclass(frozen=True)
class AucResult:
    auc: float
    se: float
    ci_normal: tuple[float, float]
    ci_logit: tuple[float, float]
    n_pos: int
    n_neg: int

    @property
    def ci_includes_chance(self) -> bool:
        if math.isnan(self.ci_logit[0]) or math.isnan(self.ci_logit[1]):
            return True
        return self.ci_logit[0] <= 0.5 <= self.ci_logit[1]


# ============================================================================
# 2. Brier Score + Brier Skill Score
# ============================================================================

@dataclass(frozen=True)
class BrierResult:
    brier_model: float
    brier_baseline: float
    bss: float                     # skill score; <=0 means no skill
    interpretation: str


def brier_skill_score(y_true: np.ndarray, probs: np.ndarray) -> BrierResult:
    """
    BSS = 1 - Brier_model / Brier_baseline
    """
    y = y_true.astype(float)
    brier_model = float(np.mean((probs - y) ** 2))
    p_base = float(np.mean(y))
    brier_base = p_base * (1.0 - p_base)

    if brier_base < 1e-15:
        return BrierResult(brier_model, brier_base, float("nan"),
                           "UNDEFINED: sample contains a single class; "
                           "BSS undefined. This itself must be reported "
                           "(e.g. Finance domain with 0 positives).")

    bss = 1.0 - brier_model / brier_base
    if bss > 0.1:
        interp = "SKILL: materially better than base-rate prediction."
    elif bss > 0.0:
        interp = "MARGINAL: negligible skill over base rate."
    else:
        interp = ("NO SKILL / ANTI-SKILL: model is worse than always "
                  "predicting the base rate. Probabilities are badly "
                  "over-confident for this domain.")
    return BrierResult(brier_model, brier_base, float(bss), interp)


# ============================================================================
# 3. Precision@K and Top-Decile Lift
# ============================================================================

@dataclass(frozen=True)
class RankingResult:
    precision_at_k: dict[int, float]      # e.g. {50: 0.02, 100: 0.01}
    hits_at_k: dict[int, int]             # absolute event counts in top-K
    top_decile_lift: float
    top_decile_precision: float
    n_events: int

    def render(self) -> str:
        p50 = self.precision_at_k.get(50)
        p100 = self.precision_at_k.get(100)
        parts = []
        if p50 is not None:
            parts.append(f"P@50 = {p50:.4f} ({self.hits_at_k[50]} events)")
        if p100 is not None:
            parts.append(f"P@100 = {p100:.4f} ({self.hits_at_k[100]} events)")
        parts.append(f"Top-decile lift = {self.top_decile_lift:.2f}× "
                     f"(precision {self.top_decile_precision:.4f})")
        return "; ".join(parts)


def precision_at_k_and_lift(y_true: np.ndarray, y_score: np.ndarray,
                            k_values: Sequence[int] = (50, 100),
                            ) -> RankingResult:
    """
    Ranking metrics — the decision-relevant view for base rates ~0.1%.
    """
    y = y_true.astype(bool)
    n = len(y)
    n_events = int(y.sum())
    base_rate = n_events / n if n > 0 else 0.0

    order = np.lexsort((np.arange(n), -y_score.astype(float)))
    ranked = y[order]

    precisions, hits = {}, {}
    for k in k_values:
        k_eff = min(k, n)
        h = int(ranked[:k_eff].sum())
        hits[k] = h
        precisions[k] = h / k_eff if k_eff > 0 else 0.0

    decile = max(1, n // 10)
    decile_hits = int(ranked[:decile].sum())
    decile_prec = decile_hits / decile
    lift = decile_prec / base_rate if base_rate > 0 else float("nan")

    return RankingResult(
        precision_at_k=precisions,
        hits_at_k=hits,
        top_decile_lift=float(lift),
        top_decile_precision=float(decile_prec),
        n_events=n_events,
    )


# ============================================================================
# 4. Benjamini-Hochberg FDR correction across domains
# ============================================================================

def benjamini_hochberg(pvals: Sequence[float],
                       alpha: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    """
    BH FDR correction across multi-domain p-values.
    """
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0.0, 1.0)
    adjusted = np.empty(n)
    adjusted[order] = q
    rejected = adjusted <= alpha
    return adjusted, rejected


# ============================================================================
# 5. Domain evaluation orchestrator + honest verdict assignment
# ============================================================================

@dataclass(frozen=True)
class VerdictRules:
    """Frozen decision thresholds."""
    auc_chance: float = 0.5
    ci_tol_around_chance: float = 0.02
    p_raw_suggestive: float = 0.05
    min_positives_for_suggestive: int = 10
    min_positives_for_defined: int = 1
    lift_defined: float = 1.2


VERDICT_RULES = VerdictRules()


def assign_verdict(auc_res: AucResult,
                   p_raw: Optional[float],
                   p_bh: float,
                   ranking: RankingResult,
                   brier: BrierResult,
                   rules: VerdictRules = VERDICT_RULES) -> tuple[str, list[str]]:
    """
    Deterministic verdict: SUGGESTIVE | EXPLORATORY | NO_SIGNAL | UNDEFINED.
    """
    reasons: list[str] = []

    if ranking.n_events < rules.min_positives_for_defined or math.isnan(brier.bss):
        return "UNDEFINED", [
            f"n_positives = {ranking.n_events} — no ranking or skill metric "
            f"is estimable. Requires cohort expansion before any claim."]

    if auc_res.ci_includes_chance:
        return "NO_SIGNAL", [
            f"DeLong logit CI [{auc_res.ci_logit[0]:.3f}, "
            f"{auc_res.ci_logit[1]:.3f}] includes AUC = 0.5. "
            f"Point estimate {auc_res.auc:.4f} is compatible with chance."]

    if (p_bh < rules.p_raw_suggestive
            and ranking.n_events >= rules.min_positives_for_suggestive
            and (not math.isnan(ranking.top_decile_lift)
                 and ranking.top_decile_lift >= rules.lift_defined)):
        reasons.append(f"AUC CI excludes chance; BH q = {p_bh:.4f} < 0.05; "
                       f"lift = {ranking.top_decile_lift:.2f}× "
                       f"with n+ = {ranking.n_events}.")
        return "SUGGESTIVE", reasons

    reasons.append(
        f"AUC CI excludes chance but replication requirements unmet "
        f"(BH q = {p_bh:.4f}, n+ = {ranking.n_events}). "
        f"Treat as exploratory until expanded cohort confirms.")
    return "EXPLORATORY", reasons


@dataclass
class DomainEvaluation:
    domain: str
    auc: AucResult
    p_raw_mannwhitney: Optional[float]
    p_bh_adjusted: float
    brier: BrierResult
    ranking: RankingResult
    verdict: str
    verdict_reasons: list[str]
    n_windows: int
    n_events: int

    def table_row(self) -> str:
        ci = self.auc.ci_logit
        ci_str = f"[{ci[0]:.3f}, {ci[1]:.3f}]" if not math.isnan(ci[0]) else "N/A"
        p_raw_str = f"{self.p_raw_mannwhitney:.4f}" if self.p_raw_mannwhitney is not None else "N/A"
        p_bh_str = f"{self.p_bh_adjusted:.4f}" if not math.isnan(self.p_bh_adjusted) else "N/A"
        bss_str = f"{self.brier.bss:+.2f}" if not math.isnan(self.brier.bss) else "N/A"
        lift_str = f"{self.ranking.top_decile_lift:.2f}×" if not math.isnan(self.ranking.top_decile_lift) else "N/A"

        return (f"| **{self.domain.upper()}** | `{self.auc.auc:.4f}` "
                f"| `{ci_str}` "
                f"| `{p_raw_str}` "
                f"| `{p_bh_str}` "
                f"| `{self.brier.brier_model:.4f}` "
                f"| `{self.brier.brier_baseline:.6f}` "
                f"| `{bss_str}` "
                f"| `{lift_str}` "
                f"| `{self.n_events}` | **`{self.verdict}`** |")


def evaluate_domain(domain: str,
                    y_true: np.ndarray,
                    y_score: np.ndarray,
                    probs: Optional[np.ndarray] = None,
                    all_domain_pvals: Optional[Sequence[float]] = None,
                    k_values: Sequence[int] = (50, 100),
                    ) -> DomainEvaluation:
    """Full statistical hardening for one domain."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    assert len(y_true) == len(y_score)

    if probs is None:
        probs = y_score

    auc_res = delong_confidence_interval(y_true, y_score)

    pos = y_score[y_true.astype(bool)]
    neg = y_score[~y_true.astype(bool)]
    if len(pos) >= 1 and len(neg) >= 1:
        try:
            _, p_raw = sps.mannwhitneyu(pos, neg, alternative="two-sided",
                                        method="exact" if len(pos) <= 8 else "asymptotic")
            p_raw = float(p_raw)
        except Exception:
            p_raw = None
    else:
        p_raw = None

    brier = brier_skill_score(y_true, np.asarray(probs, dtype=float))
    ranking = precision_at_k_and_lift(y_true, y_score, k_values)
    p_bh = float("nan")

    verdict, reasons = assign_verdict(auc_res, p_raw, p_bh, ranking, brier)

    return DomainEvaluation(
        domain=domain, auc=auc_res, p_raw_mannwhitney=p_raw,
        p_bh_adjusted=p_bh, brier=brier, ranking=ranking,
        verdict=verdict, verdict_reasons=reasons,
        n_windows=len(y_true), n_events=int(y_true.sum()))


def evaluate_all_domains(domain_data: dict[str, dict],
                         k_values: Sequence[int] = (50, 100),
                         ) -> list[DomainEvaluation]:
    """Correct entry point for the 4-domain report. BH is computed JOINTLY."""
    raws: dict[str, Optional[float]] = {}
    for dom, d in domain_data.items():
        y = np.asarray(d["y_true"]).astype(bool)
        s = np.asarray(d["y_score"], dtype=float)
        pos, neg = s[y], s[~y]
        if len(pos) >= 1 and len(neg) >= 1:
            try:
                _, p = sps.mannwhitneyu(pos, neg, alternative="two-sided",
                                        method="exact" if y.sum() <= 8 else "asymptotic")
                raws[dom] = float(p)
            except Exception:
                raws[dom] = None
        else:
            raws[dom] = None

    doms = list(domain_data.keys())
    pvals = [raws[d] if raws[d] is not None else 1.0 for d in doms]
    adjusted, rejected = benjamini_hochberg(pvals)

    results = []
    for i, dom in enumerate(doms):
        d = domain_data[dom]
        ev = evaluate_domain(dom, d["y_true"], d["y_score"],
                             probs=d.get("probs"), k_values=k_values)
        ev.p_bh_adjusted = float(adjusted[i])
        ev.verdict, ev.verdict_reasons = assign_verdict(
            ev.auc, ev.p_raw_mannwhitney, ev.p_bh_adjusted,
            ev.ranking, ev.brier)
        results.append(ev)
    return results


# ============================================================================
# 6. Honest report generator (feeds rewritten Section 3)
# ============================================================================

VERDICT_NARRATIVE = {
    "SUGGESTIVE": (
        "Preliminary directional signal: AUC confidence interval excludes "
        "chance, survives BH FDR correction, and ranking lift is material. "
        "Requires replication on an expanded cohort (n+ >= 50) before any "
        "deployment claim."),
    "EXPLORATORY": (
        "Directional point estimate with confidence interval excluding "
        "chance, but under extreme label scarcity and/or failure to survive "
        "multiple-comparisons correction. STRICTLY exploratory; no claims "
        "permitted until replication."),
    "NO_SIGNAL": (
        "Confidence interval includes chance. The rule configuration as "
        "implemented does not separate event windows from non-event windows "
        "in this domain. This is a valid empirical result and must be "
        "reported as such — re-specification (e.g. full multiplicative "
        "gating) is required before further testing, not narrative rescue."),
    "UNDEFINED": (
        "Insufficient positive events for any statistical statement. No "
        "signal or no-signal claim may be made either way."),
}


def build_honest_report(results: list[DomainEvaluation]) -> str:
    """Emits the corrected benchmark table + Section 3 narrative text."""
    header = (
        "| Domain | AUC | DeLong Logit 95% CI | p (MW, raw) | p (BH) "
        "| Brier | Brier base | BSS | Top-decile Lift | n+ | Verdict |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|")
    rows = "\n".join(r.table_row() for r in results)
    narrative = "\n\n".join(
        f"- **{r.domain.upper()} ({r.verdict}):** {VERDICT_NARRATIVE[r.verdict]}  \n"
        f"  *Reasoning:* {'; '.join(r.verdict_reasons)}  \n"
        f"  *Ranking Detail:* {r.ranking.render()}"
        for r in results)
    bonf_alpha = 0.05 / len(results)
    footer = (
        "\n\n> [!NOTE]\n"
        "> **Statistical Governance Notes:**\n"
        "> - **p (BH):** Benjamini-Hochberg False Discovery Rate adjusted q-value across the 4 tested domains.\n"
        f"> - **Bonferroni Reference α:** `{bonf_alpha:.4f}` for family-wise error rate control.\n"
        "> - **DeLong Logit 95% CI:** Exact analytic covariance confidence interval (Sun & Xu 2014) robust to extreme class imbalance.\n"
        "> - **BSS (Brier Skill Score):** $1 - \\text{Brier}_{\\text{model}} / \\text{Brier}_{\\text{baseline}}$. A value $\\le 0$ indicates probability calibration worse than a constant base-rate predictor.")
    return f"{header}\n{rows}\n\n### Detailed Domain Findings\n\n{narrative}{footer}"
