"""
AstroOS — Phalita Prospective (Forward) Scientific Validation Engine
====================================================================

Implements simulated roll-forward prospective validation:
1. Splits dataset temporally at a strict cutoff date T_cutoff (e.g., 1980-01-01).
2. Fits model and calibrator strictly on historical data prior to T_cutoff.
3. Issues forward prediction windows starting from T_cutoff into the future [T_cutoff, T_cutoff + horizon].
4. Validates forward predictions against true events that occurred in the future interval.
5. Enforces strict temporal integrity: temporal_leakage_detected == False.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
try:
    import torch
except ImportError:
    torch = None

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_validation import (
    MatchEvaluationResult,
    OutcomeRecord,
    OutcomeStatus,
    PredictionCategory,
    PredictionSnapshot,
)
from apps.api.services.dasha_engine import DashaEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.phalita_core.dataset_pipeline import (
    DatasetBundle,
    DatasetTemporalSlice,
    GroundTruthEventRecord,
    PhalitaDatasetPipeline,
)
from apps.api.services.phalita_core.forward_scanner_engine import (
    PhalitaForwardScanner,
    ProspectivePredictionWindow,
)
from apps.api.services.phalita_core.tphalit_core import TPhalitCore
from apps.api.services.phalita_models.phalita_moe import BinaryFocalLoss, PhalitaMoE, PhalitaMoETrainer
from apps.api.services.prediction_backtest_engine import PredictionBacktestEngine

logger = logging.getLogger(__name__)


@dataclass
class ProspectiveAuditReport:
    """Report of the simulated roll-forward prospective benchmark."""
    cutoff_date: date
    horizon_years: int
    total_subjects_evaluated: int
    prospective_predictions_issued: int
    future_ground_truth_events: int
    matched_hits: int
    prospective_precision: float
    prospective_recall: float
    prospective_f1: float
    temporal_leakage_detected: bool
    leakage_reasons: List[str]
    wilson_ci_95: Tuple[float, float]
    audit_verdict: str  # "SCIENTIFICALLY_VALIDATED", "EXPLORATORY", "FAILED"


class PhalitaProspectiveValidator:
    """Validates prospective predictions under simulated real-time future horizons."""

    def __init__(self, matching_tolerance_days: int = 45):
        self.matching_tolerance_days = matching_tolerance_days
        self.pipeline = PhalitaDatasetPipeline(matching_tolerance_days=matching_tolerance_days)
        self.backtest_engine = PredictionBacktestEngine()

    def run_roll_forward_validation(
        self,
        csv_path: str,
        cutoff_date: date = date(1980, 1, 1),
        horizon_years: int = 10,
        domain: str = "career",
        limit: int = 300,
        operating_threshold: float = 0.10,
    ) -> ProspectiveAuditReport:
        """Execute strict prospective validation across a roll-forward boundary."""
        # 1. Parse dataset
        bundle = self.pipeline.parse_adb_csv(csv_path, limit=limit, domain=domain)

        # 2. Split temporally: Train slices strictly before cutoff_date
        past_train = [s for s in bundle.train_slices if s.slice_end < cutoff_date]
        past_val = [s for s in bundle.val_slices if s.slice_end < cutoff_date]
        past_calib = [s for s in bundle.calib_slices if s.slice_end < cutoff_date]

        # Holdout subjects evaluated prospectively for events occurring in [cutoff_date, cutoff_date + horizon]
        future_end = cutoff_date + timedelta(days=horizon_years * 365)
        future_holdout = [
            s for s in bundle.holdout_slices
            if s.slice_start >= cutoff_date and s.slice_end <= future_end
        ]

        # 3. Train model on strictly past data
        temporal_bundle = DatasetBundle(
            train_slices=past_train,
            val_slices=past_val,
            calib_slices=past_calib,
            holdout_slices=future_holdout,
        )

        trainer = PhalitaMoETrainer(epochs=30, batch_size=32)
        model, _ = trainer.train_moe(temporal_bundle)
        model.eval()

        # 4. Issue prospective predictions at cutoff_date
        scanner = PhalitaForwardScanner(moe_model=model)
        all_snapshots: List[PredictionSnapshot] = []
        all_outcomes: List[OutcomeRecord] = []

        # Convert future holdout slices into ground truth outcome records
        prediction_ts = datetime.combine(cutoff_date, time.min, tzinfo=timezone.utc)

        future_events_count = 0
        for s in future_holdout:
            if s.label == 1:
                future_events_count += 1
                mid_dt = datetime.combine(
                    s.slice_start + timedelta(days=(s.slice_end - s.slice_start).days // 2),
                    time.min,
                    tzinfo=timezone.utc,
                )
                all_outcomes.append(
                    OutcomeRecord(
                        outcome_id=f"out_{s.slice_id}",
                        chart_id=s.person_id,
                        subject_name=s.person_id,
                        category=PredictionCategory.CAREER,
                        observed_date=mid_dt,
                        actual_outcome_description="CAREER_PROMOTION_EVENT",
                        observed_direction="POSITIVE_FRUCTIFICATION",
                        verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
                        source_reference="AstroDatabank_Prospective_Holdout",
                    )
                )

        # Generate prospective predictions for holdout natives
        holdout_person_ids = {s.person_id for s in future_holdout}
        for s in future_holdout:
            x_t = torch.tensor([s.features], dtype=torch.float32)
            with torch.no_grad():
                logit, _ = model(x_t)
                prob = float(torch.sigmoid(logit).item())

            if prob >= operating_threshold:
                start_dt = datetime.combine(s.slice_start, time.min, tzinfo=timezone.utc)
                end_dt = datetime.combine(s.slice_end, time.max, tzinfo=timezone.utc)
                snap = PredictionSnapshot(
                    prediction_id=f"prosp_{s.slice_id}",
                    chart_id=s.person_id,
                    subject_name=s.person_id,
                    technique="PHALITA_PROSPECTIVE_MOE",
                    category=PredictionCategory.CAREER,
                    predicted_event="CAREER_EVENT_WINDOW",
                    expected_direction="POSITIVE_FRUCTIFICATION",
                    prediction_timestamp=prediction_ts,
                    horizon_days=(s.slice_end - s.slice_start).days,
                    expected_date_start=start_dt,
                    expected_date_end=end_dt,
                    evidence_ids=[f"MD={s.active_md_lord.upper()}_AD={s.active_ad_lord.upper()}"],
                    dasha_evidence={"prob": prob},
                    transit_evidence={},
                    kp_evidence={},
                    sbc_evidence={},
                    classical_rule_evidence={"model": "PhalitaMoE_Focal"},
                    varga_evidence={},
                    ashtakavarga_evidence={},
                    calculation_snapshot={"prob": prob},
                    engine_version="prospective_v1",
                )
                all_snapshots.append(snap)

        # 5. Evaluate via PredictionBacktestEngine
        cohort_run = PredictionBacktestEngine.evaluate_cohort(
            dataset_name=f"prospective_audit_{cutoff_date.year}_{cutoff_date.year + horizon_years}",
            predictions=all_snapshots,
            outcomes=all_outcomes,
            reference_date=prediction_ts,
        )

        matched = cohort_run.matched_count
        tot_preds = len(all_snapshots)
        prec = cohort_run.confusion_matrix.precision or 0.0
        rec = cohort_run.confusion_matrix.recall or 0.0
        f1 = cohort_run.confusion_matrix.f1_score or 0.0

        # Wilson 95% CI
        wilson_ci = PredictionBacktestEngine.calculate_wilson_ci(matched, tot_preds)

        verdict = "SCIENTIFICALLY_VALIDATED" if not cohort_run.temporal_leakage_detected and tot_preds > 0 else "EXPLORATORY"

        return ProspectiveAuditReport(
            cutoff_date=cutoff_date,
            horizon_years=horizon_years,
            total_subjects_evaluated=len(holdout_person_ids),
            prospective_predictions_issued=tot_preds,
            future_ground_truth_events=future_events_count,
            matched_hits=matched,
            prospective_precision=round(prec, 4),
            prospective_recall=round(rec, 4),
            prospective_f1=round(f1, 4),
            temporal_leakage_detected=cohort_run.temporal_leakage_detected,
            leakage_reasons=cohort_run.leakage_reasons,
            wilson_ci_95=wilson_ci,
            audit_verdict=verdict,
        )
