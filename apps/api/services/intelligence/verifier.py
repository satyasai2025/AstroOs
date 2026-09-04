"""
AstroOS — Verifier & Empirical Feedback Calibration Loop (Vinay Jha Cognitive Architecture)

Implements empirical validation and weight calibration against verified ground-truth cases:
- Evaluates prediction outputs (0-9 probability score) against actual historical outcomes.
- Calculates Diagnostic Metrics: Hit Rate %, Brier Score, Precision, Recall, F1 Score.
- Calibrates rule weights dynamically based on prospective / retrospective discrepancies.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Any
import math


@dataclass
class VerificationRecord:
    case_id: str
    event_type: str
    predicted_score: float  # 0.0 to 9.0
    predicted_boolean: bool
    actual_outcome: bool
    is_hit: bool
    brier_loss: float


@dataclass
class VerificationMetrics:
    total_cases: int
    hits: int
    hit_rate_pct: float
    brier_score: float
    precision: float
    recall: float
    f1_score: float
    average_score: float


class CognitiveVerifier:
    """
    Automated feedback and calibration engine for cognitive astrological predictions.
    """

    @staticmethod
    def verify_case(
        case_id: str,
        event_type: str,
        predicted_score: float,
        actual_outcome: bool,
        threshold: float = 5.0,
    ) -> VerificationRecord:
        predicted_bool = (predicted_score >= threshold)
        is_hit = (predicted_bool == actual_outcome)

        # Normalize 0..9 score to probability 0.0..1.0 for Brier Score calculation
        prob_norm = max(0.0, min(1.0, predicted_score / 9.0))
        target_val = 1.0 if actual_outcome else 0.0
        brier_loss = (prob_norm - target_val) ** 2

        return VerificationRecord(
            case_id=case_id,
            event_type=event_type,
            predicted_score=predicted_score,
            predicted_boolean=predicted_bool,
            actual_outcome=actual_outcome,
            is_hit=is_hit,
            brier_loss=brier_loss,
        )

    @classmethod
    def evaluate_batch(
        cls,
        cases: List[Dict[str, Any]],  # {"case_id": ..., "event_type": ..., "predicted_score": ..., "actual_outcome": ...}
        threshold: float = 5.0,
    ) -> tuple[VerificationMetrics, List[VerificationRecord]]:
        records: List[VerificationRecord] = []
        tp = fp = fn = tn = 0
        total_brier = 0.0
        total_score = 0.0

        for c in cases:
            rec = cls.verify_case(
                case_id=c.get("case_id", "unknown"),
                event_type=c.get("event_type", "general"),
                predicted_score=float(c.get("predicted_score", 0.0)),
                actual_outcome=bool(c.get("actual_outcome", False)),
                threshold=threshold,
            )
            records.append(rec)
            total_brier += rec.brier_loss
            total_score += rec.predicted_score

            if rec.predicted_boolean and rec.actual_outcome:
                tp += 1
            elif rec.predicted_boolean and not rec.actual_outcome:
                fp += 1
            elif not rec.predicted_boolean and rec.actual_outcome:
                fn += 1
            else:
                tn += 1

        total = len(cases)
        if total == 0:
            return (
                VerificationMetrics(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                [],
            )

        hits = tp + tn
        hit_rate = (hits / total) * 100.0
        brier_score = total_brier / total
        avg_score = total_score / total

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        metrics = VerificationMetrics(
            total_cases=total,
            hits=hits,
            hit_rate_pct=round(hit_rate, 2),
            brier_score=round(brier_score, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            average_score=round(avg_score, 2),
        )

        return metrics, records
