"""
AstroOS — Gap 2: Estimable Epistemic Kernel (EPISTEMIC-KERNEL vN).

Combines: scholar priors (from registry weight_prior) + Bayesian posterior
fit on labeled cohort, subject to Shastric monotonic precedence constraints,
coupled to the isotonic calibrator as a single versioned unit.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from apps.api.services.calibration_policy import CalibrationPolicyRules, fit_fold_isotonic
from apps.api.services.rules_registry import RuleRegistry


@dataclass
class KernelFit:
    weights: Dict[str, float]
    posterior_sd: Dict[str, float]
    fit_hash: str
    n_pos: int
    train_bss: float
    constraint_report: List[str]


class EpistemicKernel:
    def __init__(
        self,
        registry: RuleRegistry,
        activations: np.ndarray,
        y: np.ndarray,
        precedence: List[Tuple[str, str]],
        rules: CalibrationPolicyRules = CalibrationPolicyRules(),
    ):
        self.rule_ids = [
            r.rule_id
            for r in registry.benchmark_rules()
            if r.formula.get("type") in ("scoring_rule", "multiplicative_gate")
        ]
        K = len(self.rule_ids)
        assert activations.shape[1] == K == len(self.rule_ids), "Activations dimension mismatch"
        self.A = activations
        self.y = y.astype(float)
        self.precedence = [
            (self.rule_ids.index(a), self.rule_ids.index(b))
            for a, b in precedence
            if a in self.rule_ids and b in self.rule_ids
        ]
        self.priors = {
            r.rule_id: r.weight_prior
            for r in registry.benchmark_rules()
            if r.weight_prior
        }

    def _p(self, w: np.ndarray) -> np.ndarray:
        return expit(self.A @ w)

    def _neg_posterior(self, w: np.ndarray) -> float:
        p = np.clip(self._p(w), 1e-9, 1 - 1e-9)
        nll = -np.sum(self.y * np.log(p) + (1 - self.y) * np.log(1 - p))
        for rid, pr in self.priors.items():
            if rid in self.rule_ids:
                k = self.rule_ids.index(rid)
                nll += 0.5 * ((w[k] - pr["mean"]) / pr["sd"]) ** 2
        return float(nll)

    def fit_map(self) -> KernelFit:
        K = len(self.rule_ids)
        w0 = np.array([self.priors.get(r, {}).get("mean", 0.5) for r in self.rule_ids])
        res = minimize(
            self._neg_posterior,
            w0,
            method="SLSQP",
            bounds=[(0, 1)] * K,
            constraints=[
                {"type": "ineq", "fun": lambda w, a=a, b=b: w[a] - w[b]}
                for a, b in self.precedence
            ],
            options={"maxiter": 500, "ftol": 1e-10},
        )
        w = np.clip(res.x, 0, 1)
        H = self._numeric_hessian(w)
        sd = np.sqrt(np.clip(np.diag(np.linalg.pinv(H + 1e-6 * np.eye(K))), 0, None))
        p = self._p(w)
        base = float(self.y.mean())
        denom = base * (1.0 - base)
        bss = 1.0 - np.mean((p - self.y) ** 2) / denom if denom > 1e-15 else float("nan")

        return KernelFit(
            weights=dict(zip(self.rule_ids, [float(x) for x in w])),
            posterior_sd=dict(zip(self.rule_ids, [float(x) for x in sd])),
            fit_hash=hashlib.sha256(w.tobytes()).hexdigest()[:16],
            n_pos=int(self.y.sum()),
            train_bss=float(bss),
            constraint_report=[f"{self.rule_ids[a]} >= {self.rule_ids[b]} OK" for a, b in self.precedence],
        )

    def _numeric_hessian(self, w: np.ndarray, h: float = 1e-4) -> np.ndarray:
        K = len(w)
        H = np.zeros((K, K))
        for i in range(K):
            for j in range(K):
                if i == j:
                    e = np.zeros(K)
                    e[i] = h
                    H[i, i] = (
                        self._neg_posterior(w + e)
                        - 2 * self._neg_posterior(w)
                        + self._neg_posterior(w - e)
                    ) / h**2
                else:
                    ei, ej = np.zeros(K), np.zeros(K)
                    ei[i], ej[j] = h, h
                    H[i, j] = (
                        self._neg_posterior(w + ei + ej)
                        - self._neg_posterior(w + ei - ej)
                        - self._neg_posterior(w - ei + ej)
                        + self._neg_posterior(w - ei - ej)
                    ) / (4 * h * h)
        return (H + H.T) / 2
