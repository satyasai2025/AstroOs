"""AstroOS — Forward Prediction Backtest Runner (Phase 3 Validation).

Wraps ForwardScanner and PredictionBacktestEngine to run deterministic
cohort backtesting against historical charts with known life event outcomes.

The runner is a *thin driver*: it owns cohort iteration, candidate to
snapshot conversion, and advisory disclosure. All statistical machinery
(Wilson-CI, confusion matrix, temporal-leakage audit) is delegated to
PredictionBacktestEngine.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Optional, Sequence

from apps.api.domain.dasha import DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_validation import (
    BacktestCohortRun,
    OutcomeRecord,
    OutcomeStatus,
    PredictionCategory,
    PredictionSnapshot,
    TemporalSplitType,
)
from apps.api.services.forward_scanner import (
    ForwardCandidate,
    ForwardScanner,
    ForwardScanResult,
)
from apps.api.services.prediction_backtest_engine import PredictionBacktestEngine

# ---------------------------------------------------------------------------
# Mapping + cohort data
# ---------------------------------------------------------------------------

EVENT_TYPE_TO_CATEGORY: dict[str, PredictionCategory] = {
    "marriage": PredictionCategory.MARRIAGE,
    "job_change": PredictionCategory.CAREER,
    "financial_gain": PredictionCategory.FINANCE,
    "relocation": PredictionCategory.RELOCATION,
    "health": PredictionCategory.HEALTH,
    "progeny": PredictionCategory.GENERAL,
    "property": PredictionCategory.FINANCE,
}

#: Synthetic labeled cohort for Phase 1 validation.  All metrics from this
#: corpus are labeled "synthetic Phase 1 cohort" (n small) and are NOT
#: production-grade.
SYNTHETIC_COHORT: list[dict] = [
    {"subject_name": "Albert Einstein (synth)", "birth_dt_iso": "1879-03-14T11:00:00+00:00",
     "lat": 48.1372, "lon": 11.5755, "event_type": "financial_gain",
     "observed_date_iso": "1921-11-09T00:00:00+00:00", "observed_direction": "POSITIVE_FRUCTIFICATION",
     "source_reference": "Nobel Prize in Physics 1921 (synthetic)"},
    {"subject_name": "Synthetic Marriage Subject A", "birth_dt_iso": "1985-07-22T06:30:00+00:00",
     "lat": 28.6139, "lon": 77.2090, "event_type": "marriage",
     "observed_date_iso": "2012-12-12T00:00:00+00:00", "observed_direction": "POSITIVE_FRUCTIFICATION",
     "source_reference": "Synthetic ground-truth event"},
    {"subject_name": "Synthetic Job-Change Subject B", "birth_dt_iso": "1990-01-05T14:15:00+00:00",
     "lat": 19.0760, "lon": 72.8777, "event_type": "job_change",
     "observed_date_iso": "2015-03-15T00:00:00+00:00", "observed_direction": "POSITIVE_FRUCTIFICATION",
     "source_reference": "Synthetic ground-truth event"},
]


@dataclass(frozen=True)
class HistoricalCohortMember:
    """A chart with its dasha tree and ground-truth historical life outcomes."""

    chart: D1Chart
    dasha_tree: DashaTree
    subject_name: str
    outcomes: tuple[OutcomeRecord, ...]


@dataclass(frozen=True)
class ForwardBacktestReport:
    """Summary of forward prediction backtest metrics across a cohort."""

    report_id: str
    dataset_name: str
    total_subjects: int
    total_predictions: int
    matched_count: int
    precision: float
    window_hit_rate: float
    f1_score: Optional[float]
    cohort_run: BacktestCohortRun
    evaluation_timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    uncertainty_disclosure: str = (
        "Backtest evaluated against historical synthetic/classical cohort; "
        "prospective outcomes may vary based on birth time precision."
    )


class ForwardBacktestRunner:
    """Executes ForwardScanner across a cohort of charts and computes backtest metrics."""

    def __init__(self, scanner: Optional[ForwardScanner] = None):
        self._scanner = scanner or ForwardScanner()

    @staticmethod
    def load_synthetic_cohort() -> list[dict]:
        """Returns the synthetic Phase 1 labeled cohort (no external file)."""
        return list(SYNTHETIC_COHORT)

    @staticmethod
    def candidate_to_snapshot(
        candidate: ForwardCandidate,
        chart_id: str,
        subject_name: str,
        prediction_timestamp: datetime,
    ) -> PredictionSnapshot:
        """Convert a ForwardCandidate into the canonical PredictionSnapshot."""
        cat = EVENT_TYPE_TO_CATEGORY.get(candidate.event_type, PredictionCategory.GENERAL)
        start_dt = datetime.combine(candidate.timing_window_start, time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(candidate.timing_window_end, time.max, tzinfo=timezone.utc)
        horizon_days = max(1, (candidate.timing_window_end - candidate.timing_window_start).days)
        return PredictionSnapshot(
            prediction_id=f"fwd_pred_{uuid.uuid4().hex[:10]}",
            chart_id=chart_id,
            subject_name=subject_name,
            technique=f"FORWARD_{candidate.signature_id}",
            category=cat,
            predicted_event=f"{candidate.event_type.upper()}_WINDOW",
            expected_direction="POSITIVE_FRUCTIFICATION",
            prediction_timestamp=prediction_timestamp,
            horizon_days=horizon_days,
            expected_date_start=start_dt,
            expected_date_end=end_dt,
            evidence_ids=list(candidate.evidence_fact_keys),
            dasha_evidence={"primary_drivers": list(candidate.primary_drivers)},
            transit_evidence={"supporting_factors": list(candidate.supporting_factors)},
            kp_evidence={},
            sbc_evidence={},
            classical_rule_evidence={"source": candidate.classical_source},
            varga_evidence={},
            ashtakavarga_evidence={},
            calculation_snapshot={"peak_score": candidate.peak_score, "confidence": candidate.confidence},
            engine_version="forward_v1",
        )


    def run_backtest(
        self,
        cohort: Sequence[HistoricalCohortMember],
        dataset_name: str,
        target_start: date,
        target_end: date,
        event_types: Optional[Sequence[str]] = None,
        min_confidence: float = 0.0,
    ) -> ForwardBacktestReport:
        """Run ForwardScanner across a labeled cohort and score it.

        Thin driver: cohort iteration + snapshot conversion live here; all
        statistical machinery (Wilson-CI, confusion matrix, leakage audit)
        is delegated to PredictionBacktestEngine.
        """
        prediction_timestamp = datetime.now(timezone.utc)
        all_snapshots: list[PredictionSnapshot] = []
        all_outcomes: list[OutcomeRecord] = []
        total_subjects = 0
        window_hits = 0

        for member in cohort:
            total_subjects += 1

            # Bind this member's snapshots to the same chart_id namespace as
            # its ground-truth outcomes so the engine can pair them.
            if member.outcomes:
                chart_id = member.outcomes[0].chart_id
            else:
                chart_id = getattr(member.chart, "chart_id", None) or (
                    f"chart_fwd_{uuid.uuid5(uuid.NAMESPACE_OID, member.subject_name).hex[:10]}"
                )

            scan = self._scanner.scan(
                chart=member.chart,
                dasha_tree=member.dasha_tree,
                event_types=event_types,
                target_start=target_start,
                target_end=target_end,
            )

            for cand in scan.candidates:
                if cand.confidence < min_confidence:
                    continue
                snapshot = self.candidate_to_snapshot(
                    candidate=cand,
                    chart_id=chart_id,
                    subject_name=member.subject_name,
                    prediction_timestamp=prediction_timestamp,
                )
                all_snapshots.append(snapshot)

                # Honest window-hit check: does any same-category verified
                # outcome for this chart fall inside the predicted window?
                hit = any(
                    o.chart_id == chart_id
                    and o.category == snapshot.category
                    and snapshot.expected_date_start
                    <= o.observed_date
                    <= snapshot.expected_date_end
                    for o in member.outcomes
                )
                if hit:
                    window_hits += 1

            all_outcomes.extend(member.outcomes)

        cohort_run = PredictionBacktestEngine.evaluate_cohort(
            dataset_name=dataset_name,
            predictions=all_snapshots,
            outcomes=all_outcomes,
        )

        total_predictions = cohort_run.total_predictions
        precision = (
            round(cohort_run.matched_count / total_predictions, 4)
            if total_predictions > 0
            else 0.0
        )
        window_hit_rate = (
            round(window_hits / total_predictions, 4)
            if total_predictions > 0
            else 0.0
        )

        cm = cohort_run.confusion_matrix
        denom_p = cm.true_positive + cm.false_positive
        denom_r = cm.true_positive + cm.false_negative
        if denom_p > 0 and denom_r > 0:
            p = cm.true_positive / denom_p
            r = cm.true_positive / denom_r
            f1_score: Optional[float] = (
                round(2 * p * r / (p + r), 4) if (p + r) > 0 else None
            )
        else:
            f1_score = None

        return ForwardBacktestReport(
            report_id=f"fwd_bkt_{uuid.uuid4().hex[:12]}",
            dataset_name=dataset_name,
            total_subjects=total_subjects,
            total_predictions=total_predictions,
            matched_count=cohort_run.matched_count,
            precision=precision,
            window_hit_rate=window_hit_rate,
            f1_score=f1_score,
            cohort_run=cohort_run,
        )


DEFAULT_SCAN_START = date(2000, 1, 1)
DEFAULT_SCAN_START = date(2000, 1, 1)
DEFAULT_SCAN_END = date(2030, 12, 31)
