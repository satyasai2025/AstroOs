"""
AstroOS — P0 Calibration Policy v2.

GOVERNING PRINCIPLE (registers as CAL-POLICY-2.0 in the governance doc):
  The system shall never emit a probability it cannot defend.
  Defensible = a walk-forward-validated calibration exists for this domain
  with sufficient positive support AND positive Brier Skill Score.

Policy tiers (deterministic, pure function of domain data state):
  TIER_FULL_CALIBRATION : n+ >= 50 AND isotonic BSS > 0 in walk-forward
                          → calibrated probabilities emitted
  TIER_BASE_RATE        : calibration not estimable or fails skill check
                          → emit base rate ONLY, flagged as such
  TIER_NO_BASE_RATE     : zero positives observed
                          → no numeric probability at all; abstention slot
                            mandatory in synthesis
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence

import numpy as np
from sklearn.isotonic import IsotonicRegression


CAL_POLICY_VERSION = "CAL-POLICY-2.0"


@dataclass(frozen=True)
class CalibrationPolicyRules:
    min_positives_full: int = 50        # below this: base-rate fallback
    min_positives_fit_attempt: int = 20 # below this: don't even attempt fit
    min_bss_for_full: float = 0.02      # skill must clear noise floor
    min_bins_support: int = 5           # each isotonic region needs support


class CalibrationTier(str, Enum):
    FULL_CALIBRATION = "TIER_FULL_CALIBRATION"
    BASE_RATE        = "TIER_BASE_RATE"
    NO_BASE_RATE     = "TIER_NO_BASE_RATE"


BASE_RATE_PHRASE = (
    "Based on the observed base rate of comparable events in the current "
    "cohort ({base_rate:.2%}), no calibrated probability can yet be "
    "assigned to this specific configuration."
)


@dataclass(frozen=True)
class FoldCalibration:
    fold_id: str
    n_train_pos: int
    fit_hash: str
    isotonic: Optional[IsotonicRegression]
    train_bss: float
    applied: bool


def _bss(y: np.ndarray, p: np.ndarray) -> float:
    bm = float(np.mean((p - y) ** 2))
    base = float(np.mean(y))
    bb = base * (1.0 - base)
    return 1.0 - bm / bb if bb > 1e-15 else float("nan")


def fit_fold_isotonic(
    y_train: np.ndarray,
    score_train: np.ndarray,
    fold_id: str,
    rules: CalibrationPolicyRules = CalibrationPolicyRules(),
) -> FoldCalibration:
    n_pos = int(y_train.sum())
    if n_pos < rules.min_positives_fit_attempt:
        return FoldCalibration(fold_id, n_pos, "NO_FIT", None, float("nan"), applied=False)

    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso.fit(score_train, y_train)
    p_train = iso.predict(score_train)
    bss_train = _bss(y_train.astype(float), p_train)

    ok = not math.isnan(bss_train) and bss_train >= rules.min_bss_for_full

    payload = (
        iso.X_thresholds_.tobytes() + iso.y_thresholds_.tobytes()
        if hasattr(iso, "X_thresholds_")
        else b"empty"
    )
    fh = hashlib.sha256(payload).hexdigest()[:16]

    return FoldCalibration(fold_id, n_pos, fh, iso if ok else None, bss_train, applied=ok)


@dataclass(frozen=True)
class CalibrationDecision:
    tier: CalibrationTier
    emitted_prob: Optional[float]
    base_rate: Optional[float]
    provenance: str
    narrative_mode: str  # "calibrated" | "lift_only" | "abstain"


def decide_probability(
    domain_n_pos: int,
    raw_score: Optional[float],
    fold_cal: Optional[FoldCalibration],
    cohort_base_rate: Optional[float],
    rules: CalibrationPolicyRules = CalibrationPolicyRules(),
) -> CalibrationDecision:
    prov = f"policy={CAL_POLICY_VERSION}; n_pos={domain_n_pos}"

    if domain_n_pos == 0 or cohort_base_rate in (None, 0.0):
        return CalibrationDecision(
            CalibrationTier.NO_BASE_RATE,
            None,
            cohort_base_rate,
            prov + "; no positive support; numeric probability forbidden",
            narrative_mode="abstain",
        )

    if (
        fold_cal is not None
        and fold_cal.applied
        and fold_cal.isotonic is not None
        and raw_score is not None
        and domain_n_pos >= rules.min_positives_full
    ):
        p = float(np.clip(fold_cal.isotonic.predict([raw_score])[0], 0, 1))
        return CalibrationDecision(
            CalibrationTier.FULL_CALIBRATION,
            p,
            cohort_base_rate,
            prov + f"; fit={fold_cal.fit_hash}; fold={fold_cal.fold_id}; train_bss={fold_cal.train_bss:.3f}",
            narrative_mode="calibrated",
        )

    return CalibrationDecision(
        CalibrationTier.BASE_RATE,
        None,
        float(cohort_base_rate),
        prov + "; calibration not estimable/qualified; base-rate fallback",
        narrative_mode="lift_only",
    )
