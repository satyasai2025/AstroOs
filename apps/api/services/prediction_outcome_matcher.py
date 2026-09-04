"""
AstroOS — Deterministic Prediction-Outcome Matcher (Module 22, Priority 7)

Evaluates a PredictionSnapshot against an OutcomeRecord using explicit,
reproducible predicates (category matching, date-window checks, directional consistency).
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from apps.api.domain.prediction_validation import (
    MatchEvaluationResult,
    OutcomeRecord,
    OutcomeStatus,
    PredictionSnapshot,
    ValidationVerdict,
)


class PredictionOutcomeMatcher:
    """
    Evaluates individual predictions against ground truth observed outcomes.
    """

    @staticmethod
    def match(
        prediction: PredictionSnapshot,
        outcome: Optional[OutcomeRecord] = None,
        as_of_date: Optional[datetime] = None,
    ) -> MatchEvaluationResult:
        match_id = str(uuid.uuid4())
        ref_date = as_of_date or datetime.now(timezone.utc)

        # 1. Handle Unresolved / No Outcome Recorded Yet
        if outcome is None:
            if ref_date < prediction.expected_date_end:
                return MatchEvaluationResult(
                    match_id=match_id,
                    prediction_id=prediction.prediction_id,
                    outcome_id=None,
                    verdict=ValidationVerdict.UNRESOLVED,
                    category_matched=False,
                    temporal_error_days=None,
                    direction_matched=False,
                    predicate_traces=[
                        f"Target window [{prediction.expected_date_start.date()} to {prediction.expected_date_end.date()}] has not yet closed.",
                        f"Current evaluation date ({ref_date.date()}) is prior to window expiration.",
                        "Verdict: UNRESOLVED (Awaiting Ground-Truth Event Observation).",
                    ],
                    evidence_provenance_ids=list(prediction.evidence_ids),
                )
            else:
                return MatchEvaluationResult(
                    match_id=match_id,
                    prediction_id=prediction.prediction_id,
                    outcome_id=None,
                    verdict=ValidationVerdict.MISSED,
                    category_matched=False,
                    temporal_error_days=None,
                    direction_matched=False,
                    predicate_traces=[
                        f"Target window [{prediction.expected_date_start.date()} to {prediction.expected_date_end.date()}] has expired.",
                        "No verified outcome recorded for this timeframe.",
                        "Verdict: MISSED (Event did not manifest within predicted window).",
                    ],
                    evidence_provenance_ids=list(prediction.evidence_ids),
                )

        # 2. Check Verification Status of the Outcome
        traces: list[str] = []
        if outcome.verification_status == OutcomeStatus.UNVERIFIED:
            traces.append("Warning: Outcome is marked UNVERIFIED; verdict is provisional.")

        # 3. Category Match Predicate
        cat_match = prediction.category == outcome.category
        traces.append(f"Category Check: Predicted '{prediction.category.value}' vs Observed '{outcome.category.value}' -> {'MATCH' if cat_match else 'MISMATCH'}")

        # 4. Temporal Window Predicate
        obs_date = outcome.observed_date
        window_start = prediction.expected_date_start
        window_end = prediction.expected_date_end
        in_window = window_start <= obs_date <= window_end

        midpoint_ts = (window_start.timestamp() + window_end.timestamp()) / 2.0
        error_days = int(round((obs_date.timestamp() - midpoint_ts) / 86400.0))

        days_outside = 0
        if obs_date > window_end:
            days_outside = int(round((obs_date.timestamp() - window_end.timestamp()) / 86400.0))
        elif obs_date < window_start:
            days_outside = int(round((window_start.timestamp() - obs_date.timestamp()) / 86400.0))

        traces.append(
            f"Temporal Check: Observed date {obs_date.date()} in window [{window_start.date()} to {window_end.date()}] -> "
            f"{'IN_WINDOW' if in_window else f'OUT_OF_WINDOW (Outside Margin: {days_outside} days, Midpoint Delta: {error_days} days)'}"
        )

        # 5. Directional / Fructification Consistency
        pred_dir = prediction.expected_direction
        obs_dir = outcome.observed_direction
        dir_match = (pred_dir == obs_dir)

        traces.append(f"Directional Check: Predicted '{pred_dir}' vs Observed '{obs_dir}' -> {'CONGRUENT' if dir_match else 'DIVERGENT'}")

        # 6. Synthesize Verdict
        verdict: ValidationVerdict
        if not cat_match:
            verdict = ValidationVerdict.MISSED
            traces.append("Final Verdict: MISSED — Life domain / event category did not correspond.")
        elif in_window and dir_match:
            verdict = ValidationVerdict.MATCHED
            traces.append("Final Verdict: MATCHED — Category, timing window, and outcome direction all verified.")
        elif in_window and not dir_match:
            if (pred_dir in ("POSITIVE_FRUCTIFICATION") and obs_dir in ("LOSS_VETO", "OBSTRUCTION_DELAY")) or \
               (pred_dir in ("LOSS_VETO") and obs_dir in ("POSITIVE_FRUCTIFICATION")):
                verdict = ValidationVerdict.CONTRADICTED
                traces.append("Final Verdict: CONTRADICTED — Timing coincided but manifest outcome directly contradicted prediction.")
            else:
                verdict = ValidationVerdict.PARTIALLY_MATCHED
                traces.append("Final Verdict: PARTIALLY_MATCHED — Timing coincided with partial directional resonance.")
        elif not in_window and days_outside <= 45 and dir_match:
            verdict = ValidationVerdict.PARTIALLY_MATCHED
            traces.append(f"Final Verdict: PARTIALLY_MATCHED — Manifested within 45-day window boundary margin ({days_outside} days outside).")
        else:
            verdict = ValidationVerdict.MISSED
            traces.append(f"Final Verdict: MISSED — Event manifested outside acceptable temporal tolerance ({days_outside} days outside).")

        return MatchEvaluationResult(
            match_id=match_id,
            prediction_id=prediction.prediction_id,
            outcome_id=outcome.outcome_id,
            verdict=verdict,
            category_matched=cat_match,
            temporal_error_days=error_days,
            direction_matched=dir_match,
            predicate_traces=traces,
            evidence_provenance_ids=list(prediction.evidence_ids),
        )
