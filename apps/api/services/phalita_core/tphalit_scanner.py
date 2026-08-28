"""
AstroOS — TPhalitScanner: Classical-Guided Predictive Backtesting Engine
========================================================================

Integrates TPhalitCore (Signed Numerical Features) into ForwardBacktestRunner
to evaluate event windows with classical precision.

Invariants:
- Zero Hallucination: 100% deterministic shastric calculations.
- Honest Auditing: Full disclosure of matches, misses, and precision metrics.
- Multi-factor scoring: Integrates Dignity (9-1), Tri-Lagna, Yogas, and Sadharmi Dasha confluence.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import List, Optional, Sequence, Tuple

from apps.api.domain.dasha import DashaTree
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_validation import (
    OutcomeRecord,
    OutcomeStatus,
    PredictionCategory,
    PredictionSnapshot,
)
from apps.api.services.forward_backtest_runner import (
    ForwardBacktestReport,
    ForwardBacktestRunner,
    HistoricalCohortMember,
)
from apps.api.services.phalita_core.tphalit_core import TPhalitCore, TPhalitFeatureVector
from apps.api.services.prediction_backtest_engine import PredictionBacktestEngine


class TPhalitScanner:
    """Enhanced predictive scanner utilizing TPhalitCore signed feature vectors."""

    def __init__(self, core: Optional[TPhalitCore] = None):
        self._core = core or TPhalitCore()
        self._engine = PredictionBacktestEngine()

    def scan_chart_windows(
        self,
        chart: D1Chart,
        dasha_tree: Optional[DashaTree],
        target_start: date,
        target_end: date,
        domain: str = "career",
        min_threshold: float = 0.25,
    ) -> List[Tuple[date, date, float, str]]:
        """Scan a chart for high-probability event windows in a domain."""
        if not dasha_tree:
            return []

        periods = getattr(dasha_tree, "mahadashas", getattr(dasha_tree, "periods", ()))
        windows: List[Tuple[date, date, float, str]] = []

        for md in periods:
            # Overlap with target window
            if md.end_date < target_start or md.start_date > target_end:
                continue

            for ad in md.sub_periods:
                if ad.end_date < target_start or ad.start_date > target_end:
                    continue

                # Sample the midpoint date of the sub-period
                mid_days = (ad.end_date - ad.start_date).days // 2
                from datetime import timedelta
                mid_date = ad.start_date + timedelta(days=mid_days)

                vec: TPhalitFeatureVector = self._core.extract_full_vector(
                    chart=chart,
                    dasha_tree=dasha_tree,
                    target_date=mid_date,
                )

                score = vec.domain_scores.get(domain, 0.0)
                if score >= min_threshold:
                    w_start = max(target_start, ad.start_date)
                    w_end = min(target_end, ad.end_date)
                    reason = f"MD={md.lord.upper()} AD={ad.lord.upper()} (Score: {score:.2f})"
                    windows.append((w_start, w_end, score, reason))

        return windows

    def run_cohort_backtest(
        self,
        cohort: Sequence[HistoricalCohortMember],
        dataset_name: str,
        target_start: date,
        target_end: date,
        domain: str = "career",
        min_threshold: float = 0.25,
    ) -> ForwardBacktestReport:
        """Execute deterministic backtest with TPhalitCore scoring."""
        prediction_timestamp = datetime.combine(target_start, time.min, tzinfo=timezone.utc)
        all_snapshots: list[PredictionSnapshot] = []
        all_outcomes: list[OutcomeRecord] = []
        total_subjects = 0

        cat_map = {
            "career": PredictionCategory.CAREER,
            "marriage": PredictionCategory.MARRIAGE,
            "finance": PredictionCategory.FINANCE,
            "health": PredictionCategory.HEALTH,
        }
        category = cat_map.get(domain, PredictionCategory.GENERAL)

        for member in cohort:
            total_subjects += 1
            in_window_outcomes = [
                o for o in member.outcomes
                if target_start <= o.observed_date.date() <= target_end
            ]
            all_outcomes.extend(in_window_outcomes)

            chart_id = (
                member.outcomes[0].chart_id if member.outcomes
                else getattr(member.chart, "chart_id", f"chart_{total_subjects}")
            )

            windows = self.scan_chart_windows(
                chart=member.chart,
                dasha_tree=member.dasha_tree,
                target_start=target_start,
                target_end=target_end,
                domain=domain,
                min_threshold=min_threshold,
            )

            import uuid
            for w_start, w_end, score, reason in windows:
                start_dt = datetime.combine(w_start, time.min, tzinfo=timezone.utc)
                end_dt = datetime.combine(w_end, time.max, tzinfo=timezone.utc)
                horizon = max(1, (w_end - w_start).days)

                snap = PredictionSnapshot(
                    prediction_id=f"tphalit_{uuid.uuid4().hex[:10]}",
                    chart_id=chart_id,
                    subject_name=member.subject_name,
                    technique="TPHALIT_CORE_V1",
                    category=category,
                    predicted_event=f"{domain.upper()}_EVENT_WINDOW",
                    expected_direction="POSITIVE_FRUCTIFICATION",
                    prediction_timestamp=prediction_timestamp,
                    horizon_days=horizon,
                    expected_date_start=start_dt,
                    expected_date_end=end_dt,
                    evidence_ids=[reason],
                    dasha_evidence={"score": score, "reason": reason},
                    transit_evidence={},
                    kp_evidence={},
                    sbc_evidence={},
                    classical_rule_evidence={"model": "TPhalitCore_v1"},
                    varga_evidence={},
                    ashtakavarga_evidence={},
                    calculation_snapshot={"score": score},
                    engine_version="tphalit_v1",
                )
                all_snapshots.append(snap)

        cohort_run = PredictionBacktestEngine.evaluate_cohort(
            dataset_name=dataset_name,
            predictions=all_snapshots,
            outcomes=all_outcomes,
            reference_date=prediction_timestamp,
        )

        matched_count = cohort_run.matched_count
        total_preds = len(all_snapshots)
        prec = cohort_run.confusion_matrix.precision or 0.0
        hit_rate = cohort_run.hit_rate

        return ForwardBacktestReport(
            report_id=f"tphalit_rep_{dataset_name}",
            dataset_name=dataset_name,
            total_subjects=total_subjects,
            total_predictions=total_preds,
            matched_count=matched_count,
            precision=prec,
            window_hit_rate=hit_rate,
            f1_score=cohort_run.confusion_matrix.f1_score,
            cohort_run=cohort_run,
            uncertainty_disclosure="Deterministic TPhalitCore evaluation against verified historical ground truth.",
        )
