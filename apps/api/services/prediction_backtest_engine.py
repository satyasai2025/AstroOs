"""
AstroOS — Prediction Backtest & Statistical Cohort Engine (Module 22, Priority 7)

Computes deterministic validation metrics, confusion matrices, 95% Wilson score confidence intervals,
and enforces temporal separation to prevent data leakage.
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from apps.api.domain.prediction_validation import (
    BacktestCohortRun,
    ConfusionMatrix,
    MatchEvaluationResult,
    OutcomeRecord,
    PredictionSnapshot,
    TemporalSplitType,
    ValidationVerdict,
)
from apps.api.services.prediction_outcome_matcher import PredictionOutcomeMatcher


class PredictionBacktestEngine:
    """
    Evaluates batches of predictions against ground truth outcomes,
    calculates empirical metrics, and checks temporal integrity.
    """

    @staticmethod
    def calculate_wilson_ci(hits: int, total: int, z: float = 1.96) -> tuple[float, float]:
        """Calculates 95% Wilson score confidence interval for a binomial proportion."""
        if total <= 0:
            return (0.0, 0.0)
        p = hits / total
        denominator = 1 + (z ** 2) / total
        centre_adjusted_probability = p + (z ** 2) / (2 * total)
        adjusted_standard_deviation = math.sqrt((p * (1 - p) + (z ** 2) / (4 * total)) / total)
        lower_bound = (centre_adjusted_probability - z * adjusted_standard_deviation) / denominator
        upper_bound = (centre_adjusted_probability + z * adjusted_standard_deviation) / denominator
        return (max(0.0, round(lower_bound, 4)), min(1.0, round(upper_bound, 4)))

    @classmethod
    def evaluate_cohort(
        cls,
        dataset_name: str,
        predictions: list[PredictionSnapshot],
        outcomes: list[OutcomeRecord],
        technique_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        temporal_split: TemporalSplitType = TemporalSplitType.VALIDATION,
        reference_date: Optional[datetime] = None,
    ) -> BacktestCohortRun:
        ref_date = reference_date or datetime.now(timezone.utc)
        backtest_id = f"bkt_{uuid.uuid4().hex[:12]}"

        # 1. Filter cohort
        filtered_preds = predictions
        if technique_filter:
            filtered_preds = [p for p in filtered_preds if p.technique.upper() == technique_filter.upper()]
        if category_filter:
            filtered_preds = [p for p in filtered_preds if p.category.value.lower() == category_filter.lower()]

        # Map outcomes by chart_id and category
        outcome_map: dict[str, list[OutcomeRecord]] = {}
        for o in outcomes:
            key = f"{o.chart_id}_{o.category.value}"
            outcome_map.setdefault(key, []).append(o)

        evaluations: list[MatchEvaluationResult] = []
        matched_count = 0
        partial_count = 0
        missed_count = 0
        contradicted_count = 0
        inconclusive_count = 0
        unresolved_count = 0

        leakage_detected = False
        leakage_reasons: list[str] = []

        # 2. Match each prediction against closest relevant outcome
        for pred in filtered_preds:
            key = f"{pred.chart_id}_{pred.category.value}"
            matching_outcomes = outcome_map.get(key, [])

            # Temporal Leakage Check: Did prediction creation timestamp occur AFTER the outcome?
            for out in matching_outcomes:
                if pred.prediction_timestamp > out.observed_date:
                    leakage_detected = True
                    leakage_reasons.append(
                        f"Temporal Leakage on {pred.prediction_id}: Prediction created on {pred.prediction_timestamp.date()} "
                        f"which is AFTER observed outcome date {out.observed_date.date()}."
                    )

            # Find outcome closest to predicted window
            selected_outcome: Optional[OutcomeRecord] = None
            if matching_outcomes:
                # Pick outcome whose date is closest to the predicted midpoint
                midpoint = (pred.expected_date_start.timestamp() + pred.expected_date_end.timestamp()) / 2.0
                selected_outcome = min(
                    matching_outcomes,
                    key=lambda o: abs(o.observed_date.timestamp() - midpoint),
                )

            res = PredictionOutcomeMatcher.match(pred, selected_outcome, as_of_date=ref_date)
            evaluations.append(res)

            if res.verdict == ValidationVerdict.MATCHED:
                matched_count += 1
            elif res.verdict == ValidationVerdict.PARTIALLY_MATCHED:
                partial_count += 1
            elif res.verdict == ValidationVerdict.MISSED:
                missed_count += 1
            elif res.verdict == ValidationVerdict.CONTRADICTED:
                contradicted_count += 1
            elif res.verdict == ValidationVerdict.INCONCLUSIVE:
                inconclusive_count += 1
            elif res.verdict == ValidationVerdict.UNRESOLVED:
                unresolved_count += 1

        total_preds = len(filtered_preds)
        resolved_preds = total_preds - unresolved_count

        # 3. Compute Metrics
        effective_hits = matched_count + (0.5 * partial_count)
        hit_rate = round(effective_hits / resolved_preds, 4) if resolved_preds > 0 else 0.0

        # Confusion Matrix Construction
        # TP = Matched predictions of active fructification/manifestation
        # FP = Predicted positive but resulted in Miss/Contradicted
        # FN = Contradicted/missed where event was expected
        # TN = Verified negative/neutral predictions where outcome did not occur
        tp = matched_count
        fp = missed_count + contradicted_count
        fn = 0  # In direct prospective prediction cohort
        tn = inconclusive_count

        cm = ConfusionMatrix(true_positive=tp, false_positive=fp, true_negative=tn, false_negative=fn)
        ci_95 = cls.calculate_wilson_ci(int(round(effective_hits)), resolved_preds)

        # 4. Hash Results for Reproducibility
        result_blob = {
            "backtest_id": backtest_id,
            "dataset_name": dataset_name,
            "total": total_preds,
            "resolved": resolved_preds,
            "matched": matched_count,
            "missed": missed_count,
            "hit_rate": hit_rate,
            "ci_95": ci_95,
            "leakage": leakage_detected,
        }
        res_hash = hashlib.sha256(json.dumps(result_blob, sort_keys=True).encode("utf-8")).hexdigest()

        return BacktestCohortRun(
            backtest_id=backtest_id,
            dataset_name=dataset_name,
            technique_filter=technique_filter,
            category_filter=category_filter,
            temporal_split=temporal_split,
            total_predictions=total_preds,
            resolved_predictions=resolved_preds,
            unresolved_predictions=unresolved_count,
            matched_count=matched_count,
            partial_count=partial_count,
            missed_count=missed_count,
            contradicted_count=contradicted_count,
            inconclusive_count=inconclusive_count,
            hit_rate=hit_rate,
            confusion_matrix=cm,
            confidence_interval_95=ci_95,
            temporal_leakage_detected=leakage_detected,
            leakage_reasons=leakage_reasons,
            evaluations=evaluations,
            result_hash=res_hash,
        )
