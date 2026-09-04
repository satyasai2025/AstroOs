"""
AstroOS — Statistical Calibration Engine (v4)

Translates deterministic prediction evidence scores into empirical probabilities:
  1. Fits Isotonic Regression (piecewise pooled bins) OR Platt Scaling (logistic sigmoid)
  2. Evaluates out-of-sample Brier score and reliability strictly on unseen Holdout test data
  3. Augments candidate windows with model-specific provenance and Wilson rate CIs

CARDINAL RULE: Operates strictly as an external mapping layer; never modifies
the underlying deterministic TechniqueEngine or PredictionOrchestrator.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Optional, Sequence

from apps.api.domain.prediction_orchestration import PredictionWindowCandidate
from apps.api.domain.research_calibration import (
    BacktestOutcome,
    CalibratedPrediction,
    CalibrationAuditLog,
    CalibrationModel,
    CalibrationModelType,
    CalibrationPoolInterval,
    CalibrationProvenance,
    CandidateWeightProfile,
    PlattParameters,
    TemporalMatchStatus,
    ValidationSummary,
)


def _compute_wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Computes Wilson score confidence interval for a binomial proportion."""
    if n <= 0:
        return (max(0.0, p - 0.20), min(1.0, p + 0.20))
    denominator = 1.0 + (z ** 2) / n
    center_adj = p + (z ** 2) / (2.0 * n)
    spread = z * math.sqrt((p * (1.0 - p)) / n + (z ** 2) / (4.0 * (n ** 2)))
    lower = max(0.0, round((center_adj - spread) / denominator, 3))
    upper = min(1.0, round((center_adj + spread) / denominator, 3))
    return (lower, upper)


def _compute_log_loss(y_true: Sequence[int], y_prob: Sequence[float], eps: float = 1e-15) -> float:
    """Computes binary logarithmic loss."""
    if not y_true or len(y_true) != len(y_prob):
        return 0.0
    total = 0.0
    for y, p in zip(y_true, y_prob):
        p_clipped = max(eps, min(1.0 - eps, p))
        total += -(y * math.log(p_clipped) + (1 - y) * math.log(1.0 - p_clipped))
    return round(total / len(y_true), 4)


def _compute_f1_score(y_true: Sequence[int], y_prob: Sequence[float], threshold: float = 0.5) -> float:
    """Computes F1-score given truth labels and predicted probabilities."""
    tp = sum(1 for y, p in zip(y_true, y_prob) if y == 1 and p >= threshold)
    fp = sum(1 for y, p in zip(y_true, y_prob) if y == 0 and p >= threshold)
    fn = sum(1 for y, p in zip(y_true, y_prob) if y == 1 and p < threshold)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    if precision + recall == 0.0:
        return 0.0
    return round(2 * (precision * recall) / (precision + recall), 4)


def _compute_conditional_roc_auc(y_true: Sequence[int], y_prob: Sequence[float]) -> tuple[float | None, str]:
    """Computes ROC-AUC or flags degenerate single-class / insufficient conditions."""
    if not y_true or not y_prob or len(y_true) != len(y_prob):
        return (None, "INSUFFICIENT_DATA")
    pos_count = sum(1 for y in y_true if y == 1)
    neg_count = len(y_true) - pos_count
    if pos_count == 0 or neg_count == 0:
        return (None, "DEGENERATE_SINGLE_CLASS")
    pairs = sorted(zip(y_prob, y_true), key=lambda x: x[0], reverse=True)
    tp, fp = 0, 0
    tpr_list, fpr_list = [0.0], [0.0]
    for p, y in pairs:
        if y == 1:
            tp += 1
        else:
            fp += 1
        tpr_list.append(tp / pos_count)
        fpr_list.append(fp / neg_count)
    auc = 0.0
    for i in range(1, len(fpr_list)):
        auc += (fpr_list[i] - fpr_list[i - 1]) * (tpr_list[i] + tpr_list[i - 1]) / 2.0
    return (round(auc, 4), "CALCULATED_VALID")


class CalibrationEngine:
    """Independent statistical calibration service."""

    DEFAULT_SCORE_BINS: tuple[tuple[int, int], ...] = (
        (0, 49),
        (50, 59),
        (60, 69),
        (70, 79),
        (80, 89),
        (90, 100),
    )

    _instance: Optional[CalibrationEngine] = None

    def __init__(self) -> None:
        self._candidate_profiles: dict[str, CandidateWeightProfile] = {}
        self._active_profile: Optional[CandidateWeightProfile] = None
        self._audit_trail: list[CalibrationAuditLog] = []

    @classmethod
    def get_instance(cls) -> CalibrationEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_candidate_weight_profile(
        self,
        name: str,
        description: str,
        dataset_id: str,
        technique_weights: dict[str, float],
        validation_summary: ValidationSummary,
    ) -> CandidateWeightProfile:
        import uuid
        profile_id = f"cand-{uuid.uuid4().hex[:8]}"
        profile = CandidateWeightProfile(
            profile_id=profile_id,
            name=name,
            description=description,
            dataset_id=dataset_id,
            technique_weights=technique_weights,
            validation_summary=validation_summary,
            status="DRAFT_CANDIDATE",
        )
        self._candidate_profiles[profile_id] = profile
        self._audit_trail.append(
            CalibrationAuditLog(
                log_id=f"audit-{uuid.uuid4().hex[:8]}",
                candidate_profile_id=profile_id,
                action="CANDIDATE_PROFILE_CREATED",
                details={"name": name, "weights": technique_weights},
            )
        )
        return profile

    def activate_candidate_profile(self, profile_id: str) -> Optional[CandidateWeightProfile]:
        import uuid
        profile = self._candidate_profiles.get(profile_id)
        if not profile:
            return None
        activated = CandidateWeightProfile(
            profile_id=profile.profile_id,
            name=profile.name,
            description=profile.description,
            dataset_id=profile.dataset_id,
            technique_weights=profile.technique_weights,
            validation_summary=profile.validation_summary,
            status="ACTIVE",
            created_at=profile.created_at,
            activated_at=datetime.now(),
        )
        self._candidate_profiles[profile_id] = activated
        self._active_profile = activated
        self._audit_trail.append(
            CalibrationAuditLog(
                log_id=f"audit-{uuid.uuid4().hex[:8]}",
                candidate_profile_id=profile_id,
                action="PROFILE_ACTIVATED",
                details={"profile_id": profile_id, "status": "ACTIVE"},
            )
        )
        return activated

    def get_active_profile(self) -> Optional[CandidateWeightProfile]:
        return self._active_profile

    def get_candidate_profile(self, profile_id: str) -> Optional[CandidateWeightProfile]:
        return self._candidate_profiles.get(profile_id)

    def list_candidate_profiles(self) -> list[CandidateWeightProfile]:
        return list(self._candidate_profiles.values())

    def get_audit_trail(self) -> list[CalibrationAuditLog]:
        return list(self._audit_trail)

    def fit_isotonic_calibration(
        self,
        train_outcomes: Sequence[BacktestOutcome],
        dataset_id: str,
        dataset_version: str,
        event_type: str,
        profile_id: str,
        split_seed: int = 42,
        split_train_ratio: float = 0.70,
        tolerance_days: int = 30,
        bins: tuple[tuple[int, int], ...] = DEFAULT_SCORE_BINS,
    ) -> CalibrationModel:
        """Fits an Isotonic regression calibration model with pooled empirical hit rates."""
        pool_intervals: list[CalibrationPoolInterval] = []

        for min_s, max_s in bins:
            bin_outcomes = [
                o for o in train_outcomes if min_s <= o.deterministic_score <= max_s
            ]
            n_k = len(bin_outcomes)
            hits_k = sum(
                1 for o in bin_outcomes
                if o.match_status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT)
            )

            if n_k > 0:
                p_k = hits_k / n_k
                se_k = math.sqrt((p_k * (1.0 - p_k)) / n_k) if n_k > 1 else 0.10
            else:
                p_k = (min_s + max_s) / 200.0  # Linear prior
                se_k = 0.25

            ci = _compute_wilson_ci(p_k, n_k)

            pool_intervals.append(
                CalibrationPoolInterval(
                    min_score=min_s,
                    max_score=max_s,
                    bin_sample_size_n=n_k,
                    observed_hits=hits_k,
                    empirical_hit_rate=round(p_k, 4),
                    rate_standard_error=round(se_k, 4),
                    rate_ci_95=ci,
                    has_small_n_warning=(n_k < 30),
                )
            )

        prov = CalibrationProvenance(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            event_type=event_type,
            consensus_profile_id=profile_id,
            calibration_model_type=CalibrationModelType.ISOTONIC_REGRESSION,
            calibration_model_version="1.0",
            fit_timestamp=datetime.now(),
            split_seed=split_seed,
            split_train_ratio=split_train_ratio,
            tolerance_days=tolerance_days,
        )

        return CalibrationModel(
            provenance=prov,
            isotonic_pools=tuple(pool_intervals),
            platt_params=None,
        )

    def fit_platt_scaling(
        self,
        train_outcomes: Sequence[BacktestOutcome],
        dataset_id: str,
        dataset_version: str,
        event_type: str,
        profile_id: str,
        split_seed: int = 42,
        split_train_ratio: float = 0.70,
        tolerance_days: int = 30,
    ) -> CalibrationModel:
        """Fits Platt scaling logistic parameters: P(S) = 1 / (1 + exp(-(aS + b)))."""
        # Gradient descent on logistic log loss
        a = 0.05
        b = -3.0
        lr = 0.001
        epochs = 200

        n = len(train_outcomes)
        if n > 0:
            for _ in range(epochs):
                grad_a = 0.0
                grad_b = 0.0
                for o in train_outcomes:
                    s = o.deterministic_score
                    y = 1.0 if o.match_status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT) else 0.0
                    z = max(-15.0, min(15.0, a * s + b))
                    p = 1.0 / (1.0 + math.exp(-z))
                    err = p - y
                    grad_a += err * s
                    grad_b += err
                a -= lr * (grad_a / n)
                b -= lr * (grad_b / n)

        params = PlattParameters(
            slope_a=round(a, 4),
            intercept_b=round(b, 4),
            train_sample_size_n=n,
        )

        prov = CalibrationProvenance(
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            event_type=event_type,
            consensus_profile_id=profile_id,
            calibration_model_type=CalibrationModelType.PLATT_SCALING,
            calibration_model_version="1.0",
            fit_timestamp=datetime.now(),
            split_seed=split_seed,
            split_train_ratio=split_train_ratio,
            tolerance_days=tolerance_days,
        )

        return CalibrationModel(
            provenance=prov,
            isotonic_pools=(),
            platt_params=params,
        )

    def evaluate_holdout_validation(
        self,
        holdout_outcomes: Sequence[BacktestOutcome],
        calibration_model: CalibrationModel,
    ) -> ValidationSummary:
        """
        Evaluates out-of-sample Brier score and hit rate strictly on unseen holdout data.
        """
        n_holdout = len(holdout_outcomes)
        if n_holdout == 0:
            return ValidationSummary(
                holdout_sample_size_n=0,
                holdout_brier_score=0.0,
                holdout_hit_rate=0.0,
                mean_peak_offset_days=0.0,
            )

        brier_sum = 0.0
        hits_count = 0
        total_offset = 0

        for o in holdout_outcomes:
            prob = self.predict_probability_for_score(o.deterministic_score, calibration_model)
            y = 1.0 if o.match_status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT) else 0.0
            brier_sum += (prob - y) ** 2
            if y == 1.0:
                hits_count += 1
            if o.peak_offset_days is not None:
                total_offset += abs(o.peak_offset_days)

        brier = round(brier_sum / n_holdout, 4)
        hit_rate = round(hits_count / n_holdout, 4)
        mean_offset = round(total_offset / n_holdout, 1)

        y_true = [1 if o.match_status in (TemporalMatchStatus.WINDOW_EXACT_HIT, TemporalMatchStatus.WINDOW_TOLERANCE_HIT) else 0 for o in holdout_outcomes]
        y_prob = [self.predict_probability_for_score(o.deterministic_score, calibration_model) for o in holdout_outcomes]
        log_loss = _compute_log_loss(y_true, y_prob)
        f1 = _compute_f1_score(y_true, y_prob)
        roc_auc, _ = _compute_conditional_roc_auc(y_true, y_prob)

        return ValidationSummary(
            holdout_sample_size_n=n_holdout,
            holdout_brier_score=brier,
            holdout_hit_rate=hit_rate,
            mean_peak_offset_days=mean_offset,
            holdout_log_loss=log_loss,
            diagnostic_f1=f1,
            diagnostic_roc_auc=roc_auc or 0.0,
        )

    def predict_probability_for_score(
        self,
        score: int,
        calibration_model: CalibrationModel,
    ) -> float:
        """Calculates calibrated probability from score according to model type."""
        if calibration_model.provenance.calibration_model_type == CalibrationModelType.ISOTONIC_REGRESSION:
            for pool in calibration_model.isotonic_pools:
                if pool.min_score <= score <= pool.max_score:
                    return pool.empirical_hit_rate
            return score / 100.0

        if calibration_model.provenance.calibration_model_type == CalibrationModelType.PLATT_SCALING:
            params = calibration_model.platt_params
            if params:
                z = max(-15.0, min(15.0, params.slope_a * score + params.intercept_b))
                return round(1.0 / (1.0 + math.exp(-z)), 3)

        return score / 100.0

    def calibrate_candidate_window(
        self,
        candidate: PredictionWindowCandidate,
        calibration_model: CalibrationModel,
        validation_summary: ValidationSummary,
    ) -> CalibratedPrediction:
        """Augments a deterministic candidate window with complete calibration provenance."""
        model_type = calibration_model.provenance.calibration_model_type
        prob = self.predict_probability_for_score(candidate.peak_score, calibration_model)

        if model_type == CalibrationModelType.ISOTONIC_REGRESSION:
            matched_pool = None
            for p in calibration_model.isotonic_pools:
                if p.min_score <= candidate.peak_score <= p.max_score:
                    matched_pool = p
                    break

            if matched_pool:
                ci = matched_pool.rate_ci_95
                pool_min = matched_pool.min_score
                pool_max = matched_pool.max_score
                pool_n = matched_pool.bin_sample_size_n
                pool_hits = matched_pool.observed_hits
                small_n = matched_pool.has_small_n_warning
            else:
                ci = _compute_wilson_ci(prob, 0)
                pool_min, pool_max, pool_n, pool_hits, small_n = None, None, None, None, True

            return CalibratedPrediction(
                event_type=candidate.event_type,
                start_date=candidate.start_date,
                end_date=candidate.end_date,
                peak_date=candidate.peak_date,
                deterministic_score=candidate.peak_score,
                calibrated_probability=prob,
                calibration_rate_ci_95=ci,
                calibration_sample_size_n=pool_n if pool_n is not None else 0,
                holdout_sample_size_n=validation_summary.holdout_sample_size_n,
                holdout_brier_score=validation_summary.holdout_brier_score,
                calibration_model_type=model_type,
                calibration_bin_min_score=pool_min,
                calibration_bin_max_score=pool_max,
                calibration_bin_sample_size_n=pool_n,
                calibration_bin_observed_hits=pool_hits,
                has_small_n_warning=small_n,
                provenance=calibration_model.provenance,
                primary_drivers=candidate.primary_drivers,
                opposing_factors=candidate.opposing_factors,
                evidence_trace=candidate.evidence_trace,
            )

        # Platt Scaling
        params = calibration_model.platt_params
        slope_a = params.slope_a if params else 0.05
        intercept_b = params.intercept_b if params else -3.0
        train_n = params.train_sample_size_n if params else 0
        ci = _compute_wilson_ci(prob, train_n)

        return CalibratedPrediction(
            event_type=candidate.event_type,
            start_date=candidate.start_date,
            end_date=candidate.end_date,
            peak_date=candidate.peak_date,
            deterministic_score=candidate.peak_score,
            calibrated_probability=prob,
            calibration_rate_ci_95=ci,
            calibration_sample_size_n=train_n,
            holdout_sample_size_n=validation_summary.holdout_sample_size_n,
            holdout_brier_score=validation_summary.holdout_brier_score,
            calibration_model_type=model_type,
            platt_slope_a=slope_a,
            platt_intercept_b=intercept_b,
            has_small_n_warning=(train_n < 30),
            provenance=calibration_model.provenance,
            primary_drivers=candidate.primary_drivers,
            opposing_factors=candidate.opposing_factors,
            evidence_trace=candidate.evidence_trace,
        )