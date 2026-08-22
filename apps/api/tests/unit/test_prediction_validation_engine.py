"""
Unit tests for Prediction Validation & Empirical Outcome Backtesting (Module 22, Priority 7)
"""

import pytest
from datetime import datetime, timedelta, timezone

from apps.api.domain.prediction_validation import (
    OutcomeStatus,
    PredictionCategory,
    PredictionSnapshot,
    TemporalSplitType,
    ValidationVerdict,
    compute_evidence_hash,
)
from apps.api.services.prediction_backtest_engine import PredictionBacktestEngine
from apps.api.services.prediction_outcome_matcher import PredictionOutcomeMatcher
from apps.api.services.prediction_validation_service import PredictionValidationService


class TestPredictionValidationEngine:
    @pytest.fixture(autouse=True)
    def clean_service(self):
        service = PredictionValidationService()
        service.reset_for_tests()
        return service

    def test_immutable_prediction_snapshot_and_evidence_hashing(self, clean_service):
        pred = clean_service.create_prediction(
            chart_id="chart_001",
            subject_name="Test Native",
            technique="KP_CSL",
            category=PredictionCategory.CAREER,
            predicted_event="Major Promotion",
            expected_direction="POSITIVE_FRUCTIFICATION",
            prediction_timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            horizon_days=90,
            expected_date_start=datetime(2025, 3, 1, tzinfo=timezone.utc),
            expected_date_end=datetime(2025, 5, 31, tzinfo=timezone.utc),
            evidence_ids=["ev_csl_10", "ev_dasha_rahu"],
            dasha_evidence={"major": "Rahu"},
            transit_evidence={"jupiter": "Aries"},
            kp_evidence={"10th_csl": "Jupiter"},
            sbc_evidence={},
            classical_rule_evidence={},
            varga_evidence={},
            ashtakavarga_evidence={},
            calculation_snapshot={},
        )
        assert pred.prediction_id.startswith("pred_")
        assert len(pred.evidence_hash) == 64  # SHA-256
        assert pred.category == PredictionCategory.CAREER

        # Immutability check
        with pytest.raises(Exception):
            pred.predicted_event = "Altered retroactively"  # Frozen dataclass

    def test_exact_and_window_matching(self, clean_service):
        pred = clean_service.create_prediction(
            chart_id="chart_002",
            subject_name="Test Native 2",
            technique="PARASHARI_DASHA_TRANSIT",
            category=PredictionCategory.MARRIAGE,
            predicted_event="Marriage Fructification",
            expected_direction="POSITIVE_FRUCTIFICATION",
            prediction_timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            horizon_days=180,
            expected_date_start=datetime(2024, 6, 1, tzinfo=timezone.utc),
            expected_date_end=datetime(2024, 11, 30, tzinfo=timezone.utc),
            evidence_ids=["ev_7th_lord_activation"],
            dasha_evidence={},
            transit_evidence={},
            kp_evidence={},
            sbc_evidence={},
            classical_rule_evidence={},
            varga_evidence={},
            ashtakavarga_evidence={},
            calculation_snapshot={},
        )

        # 1. Exact Match inside window
        outcome_matched = clean_service.register_outcome(
            chart_id="chart_002",
            subject_name="Test Native 2",
            category=PredictionCategory.MARRIAGE,
            observed_date=datetime(2024, 8, 15, tzinfo=timezone.utc),
            actual_outcome_description="Married in Bangalore",
            observed_direction="POSITIVE_FRUCTIFICATION",
            verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
            source_reference="Marriage Registry",
        )
        res1 = PredictionOutcomeMatcher.match(pred, outcome_matched)
        assert res1.verdict == ValidationVerdict.MATCHED
        assert res1.category_matched is True
        assert res1.direction_matched is True

        # 2. Contradicted Match inside window
        outcome_contradicted = clean_service.register_outcome(
            chart_id="chart_002",
            subject_name="Test Native 2",
            category=PredictionCategory.MARRIAGE,
            observed_date=datetime(2024, 8, 15, tzinfo=timezone.utc),
            actual_outcome_description="Engagement Broken / Bitter Separation",
            observed_direction="LOSS_VETO",
            verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
            source_reference="Court records",
        )
        res2 = PredictionOutcomeMatcher.match(pred, outcome_contradicted)
        assert res2.verdict == ValidationVerdict.CONTRADICTED

        # 3. Partial Match slightly out of window
        outcome_partial = clean_service.register_outcome(
            chart_id="chart_002",
            subject_name="Test Native 2",
            category=PredictionCategory.MARRIAGE,
            observed_date=datetime(2024, 12, 10, tzinfo=timezone.utc),  # 10 days after window end
            actual_outcome_description="Married on Dec 10",
            observed_direction="POSITIVE_FRUCTIFICATION",
            verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
            source_reference="Family records",
        )
        res3 = PredictionOutcomeMatcher.match(pred, outcome_partial)
        assert res3.verdict == ValidationVerdict.PARTIALLY_MATCHED

    def test_unresolved_and_missed_outcomes(self, clean_service):
        future_pred = clean_service.create_prediction(
            chart_id="chart_future",
            subject_name="Future Native",
            technique="KP_CSL",
            category=PredictionCategory.FINANCE,
            predicted_event="Windfall",
            expected_direction="POSITIVE_FRUCTIFICATION",
            prediction_timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            horizon_days=90,
            expected_date_start=datetime(2027, 1, 1, tzinfo=timezone.utc),
            expected_date_end=datetime(2027, 3, 31, tzinfo=timezone.utc),
            evidence_ids=[],
            dasha_evidence={},
            transit_evidence={},
            kp_evidence={},
            sbc_evidence={},
            classical_rule_evidence={},
            varga_evidence={},
            ashtakavarga_evidence={},
            calculation_snapshot={},
        )
        # Evaluated prior to window closure -> UNRESOLVED
        res = PredictionOutcomeMatcher.match(future_pred, None, as_of_date=datetime(2026, 6, 1, tzinfo=timezone.utc))
        assert res.verdict == ValidationVerdict.UNRESOLVED

        # Evaluated after window closure with no outcome -> MISSED
        res_expired = PredictionOutcomeMatcher.match(future_pred, None, as_of_date=datetime(2028, 1, 1, tzinfo=timezone.utc))
        assert res_expired.verdict == ValidationVerdict.MISSED

    def test_cohort_backtesting_and_temporal_leakage_detection(self, clean_service):
        run = clean_service.run_backtest(dataset_name="Canonical Seed Cohort", temporal_split=TemporalSplitType.VALIDATION)
        assert run.total_predictions >= 2
        assert run.matched_count >= 2
        assert run.hit_rate > 0.0
        assert len(run.confidence_interval_95) == 2
        assert run.temporal_leakage_detected is False

        # Now simulate a leakage: Prediction created in 1940 with an outcome in 1936
        leaked_pred = clean_service.create_prediction(
            chart_id="chart_leaked",
            subject_name="Leaked Subject",
            technique="KP_CSL",
            category=PredictionCategory.CAREER,
            predicted_event="Historical event back-predicted with future timestamp",
            expected_direction="POSITIVE_FRUCTIFICATION",
            prediction_timestamp=datetime(1940, 1, 1, tzinfo=timezone.utc),  # Created AFTER outcome!
            horizon_days=365,
            expected_date_start=datetime(1936, 1, 1, tzinfo=timezone.utc),
            expected_date_end=datetime(1936, 12, 31, tzinfo=timezone.utc),
            evidence_ids=[],
            dasha_evidence={},
            transit_evidence={},
            kp_evidence={},
            sbc_evidence={},
            classical_rule_evidence={},
            varga_evidence={},
            ashtakavarga_evidence={},
            calculation_snapshot={},
        )
        clean_service.register_outcome(
            chart_id="chart_leaked",
            subject_name="Leaked Subject",
            category=PredictionCategory.CAREER,
            observed_date=datetime(1936, 6, 1, tzinfo=timezone.utc),
            actual_outcome_description="Event in 1936",
            observed_direction="POSITIVE_FRUCTIFICATION",
            verification_status=OutcomeStatus.VERIFIED_HISTORICAL,
            source_reference="History",
        )

        run_leaked = clean_service.run_backtest(dataset_name="Leakage Cohort")
        assert run_leaked.temporal_leakage_detected is True
        assert any("Temporal Leakage" in reason for reason in run_leaked.leakage_reasons)

    def test_audit_trail_integrity(self, clean_service):
        audit = clean_service.get_prediction_audit_trail("pred_raman_1936")
        assert audit["prediction"]["subject_name"] == "Dr. B.V. Raman"
        assert audit["prediction"]["technique"] == "KP_CSL"
        assert len(audit["prediction"]["evidence_hash"]) == 64
        assert audit["outcome"]["actual_outcome"] is not None
        assert audit["verdict_trace"]["verdict"] == "MATCHED"
        assert len(audit["verdict_trace"]["predicate_traces"]) > 0
