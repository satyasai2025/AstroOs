"""
AstroOS — Unit Tests for Priority 27: Longitudinal Outcome Tracking Engine
"""

from datetime import date, datetime, timezone
import pytest
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.longitudinal_tracking import (
    OutcomeVerificationStatus,
    PopulationDistributionDriftStatus,
)
from apps.api.main import app
from apps.api.services.experiment_service import ExperimentRegistry
from apps.api.services.longitudinal_tracking_engine import LongitudinalTrackingEngine
from apps.api.services.portfolio_planner_engine import ResearchPortfolioPlannerEngine
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "p27_tester", "role": "researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_record_and_evaluate_longitudinal_tracking():
    """
    Verifies that the longitudinal engine ingests prospective observations,
    calculates rolling hit rates, and computes both PSI distribution drift and two-proportion Z-tests.
    """
    prosp_engine = ProspectiveValidationEngine.get_instance()
    planner_engine = ResearchPortfolioPlannerEngine.get_instance()
    exp_reg = ExperimentRegistry.get_instance()

    engine = LongitudinalTrackingEngine(
        prospective_engine=prosp_engine,
        planner_engine=planner_engine,
        experiment_registry=exp_reg,
    )

    report = engine.evaluate_longitudinal_tracking(target_objective="marriage")

    assert report is not None
    assert report.target_objective == "marriage"
    assert report.total_subjects_tracked == 50
    assert report.confirmed_hits_count == 43
    assert report.confirmed_misses_count == 6
    assert report.cumulative_hit_rate >= 0.85
    assert report.cumulative_brier_score <= 0.15
    assert report.population_distribution_drift == PopulationDistributionDriftStatus.STABLE_CONGRUENT
    assert report.population_stability_index < 0.10

    # Verify Statistical Degradation Test separation
    stat_test = report.statistical_degradation_test
    assert stat_test.baseline_prospective_hit_rate > 0.0
    assert stat_test.longitudinal_rolling_hit_rate >= 0.85
    assert stat_test.is_degradation_statistically_significant is False
    assert "NO_DEGRADATION" in stat_test.test_interpretation or "NOT_SIGNIFICANT" in stat_test.test_interpretation

    # Verify Time-Series Intervals
    assert len(report.time_series_intervals) == 2
    assert report.time_series_intervals[0].interval_id == "2026-Q1"
    assert report.time_series_intervals[1].interval_id == "2026-Q2"
    assert len(report.report_provenance_hash) == 16
    assert "LONGITUDINAL_TRACKING_ONLY" in report.epistemic_non_causal_statement


def test_statistical_degradation_detection_on_deterioration():
    """
    Proves that when a prospective rule degrades severely in the real-world stream,
    the statistical degradation test flags the deterioration as statistically significant.
    """
    engine = LongitudinalTrackingEngine()
    rule_id = "hyp-degrading-test"

    # Inject 40 misses out of 50 records (only 10 hits -> 20% hit rate vs 82% baseline)
    for i in range(1, 51):
        status = OutcomeVerificationStatus.CONFIRMED_HIT if i <= 10 else OutcomeVerificationStatus.CONFIRMED_MISS
        engine.record_subject_outcome(
            subject_id=f"subj-deg-{i:03d}",
            target_objective="marriage",
            rule_id=rule_id,
            predicted_window_start=date(2026, 1, 1),
            predicted_window_end=date(2026, 6, 30),
            actual_event_date=date(2026, 3, 1) if status == OutcomeVerificationStatus.CONFIRMED_HIT else None,
            predicted_probability=0.85,
            verification_status=status,
            initialize_seed=False,
        )

    report = engine.evaluate_longitudinal_tracking(target_objective="marriage", rule_id=rule_id)

    assert report.cumulative_hit_rate == 0.20
    assert report.statistical_degradation_test.is_degradation_statistically_significant is True
    assert report.statistical_degradation_test.degradation_p_value < 0.001
    assert report.statistical_degradation_test.delta_hit_rate < -0.50
    assert "CRITICAL_DEGRADATION" in report.statistical_degradation_test.test_interpretation


def test_longitudinal_tracking_api_endpoints(api_client):
    """
    Verifies FastAPI endpoints for outcome recording and evaluation.
    """
    # POST /api/v1/research/longitudinal-tracking/record
    rec_resp = api_client.post(
        "/api/v1/research/longitudinal-tracking/record",
        json={
            "subject_id": "subj-live-api-001",
            "target_objective": "marriage",
            "rule_id": "hyp-m1",
            "predicted_window_start": "2026-07-01",
            "predicted_window_end": "2026-09-30",
            "actual_event_date": "2026-08-15",
            "predicted_probability": 0.88,
            "verification_status": "CONFIRMED_HIT",
            "verification_source": "MUNICIPAL_REGISTRY",
        },
    )
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["status"] == "RECORDED"
    assert rec_data["subject_id"] == "subj-live-api-001"

    # POST /api/v1/research/longitudinal-tracking/evaluate
    eval_resp = api_client.post(
        "/api/v1/research/longitudinal-tracking/evaluate",
        json={"target_objective": "marriage", "rule_id": None, "snapshot_id": None},
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["target_objective"] == "marriage"
    assert eval_data["total_subjects_tracked"] >= 50
    assert "statistical_degradation_test" in eval_data

    # GET /api/v1/research/longitudinal-tracking/latest
    latest_resp = api_client.get("/api/v1/research/longitudinal-tracking/latest?target_objective=marriage")
    assert latest_resp.status_code == 200
    latest_data = latest_resp.json()
    assert latest_data["target_objective"] == "marriage"
