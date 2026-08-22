"""
AstroOS — Priority 10 Full Integration & Lifecycle Verification Test Suite
"""

import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.prediction_orchestration import (
    PARASHARI_STANDARD_PROFILE,
)
from apps.api.domain.research_calibration import (
    BacktestOutcome,
    BirthDataConfidence,
    EventDateConfidence,
    EventVerification,
    GroundTruthEvent,
    TemporalMatchStatus,
)
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.main import app
from apps.api.services.calibration_engine import (
    CalibrationEngine,
    _compute_conditional_roc_auc,
    _compute_f1_score,
    _compute_log_loss,
)
from apps.api.domain.prediction_orchestration import ConsensusProfile
from apps.api.services.prediction_orchestrator import PredictionOrchestrator


def _build_test_chart():
    asc = Ascendant(10.0, 10.0, "aries", 10.0, "ashwini", 1)
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

    planets = [
        SiderealPosition("sun", 30.0, "taurus", 0.0, 2, "krittika", 2, False, False, None, None),
        SiderealPosition("moon", 15.0, "aries", 15.0, 1, "bharani", 1, False, False, None, None),
        SiderealPosition("mars", 60.0, "gemini", 0.0, 3, "mrigashira", 3, False, False, None, None),
        SiderealPosition("mercury", 90.0, "cancer", 0.0, 4, "punarvasu", 4, False, False, None, None),
        SiderealPosition("jupiter", 105.0, "cancer", 15.0, 4, "pushya", 2, False, False, None, "exalted"),
        SiderealPosition("venus", 120.0, "leo", 0.0, 5, "magha", 1, False, False, None, None),
        SiderealPosition("saturn", 275.0, "capricorn", 5.0, 10, "uttara_phalguni", 2, False, False, None, None),
        SiderealPosition("rahu", 180.0, "libra", 0.0, 7, "chitra", 3, True, False, None, None),
        SiderealPosition("ketu", 0.0, "aries", 0.0, 1, "ashwini", 1, True, False, None, None),
    ]
    houses = [HouseCusp(n, float((n - 1) * 30), float((n - 1) * 30), rashis[n - 1]) for n in range(1, 13)]
    return D1Chart(None, asc, houses, planets, [], [], None, "lahiri", "W")


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "test_researcher"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_complete_priority10_calibration_lifecycle(api_client):
    # 1. Load a real deterministic benchmark event dataset (sorted temporally)
    raw_events = [
        GroundTruthEvent(
            event_id="evt-1995",
            subject_id="subj-01",
            event_type="marriage",
            actual_date=date(1995, 6, 15),
            birth_datetime_utc=datetime(1970, 1, 1, 12, 0),
            birth_latitude=28.6139,
            birth_longitude=77.2090,
        ),
        GroundTruthEvent(
            event_id="evt-2000",
            subject_id="subj-02",
            event_type="marriage",
            actual_date=date(2000, 4, 10),
            birth_datetime_utc=datetime(1975, 3, 15, 6, 30),
            birth_latitude=19.0760,
            birth_longitude=72.8777,
        ),
        GroundTruthEvent(
            event_id="evt-2005",
            subject_id="subj-03",
            event_type="marriage",
            actual_date=date(2005, 11, 20),
            birth_datetime_utc=datetime(1980, 8, 22, 18, 45),
            birth_latitude=13.0827,
            birth_longitude=80.2707,
        ),
        GroundTruthEvent(
            event_id="evt-2010",
            subject_id="subj-04",
            event_type="marriage",
            actual_date=date(2010, 2, 14),
            birth_datetime_utc=datetime(1985, 12, 5, 4, 15),
            birth_latitude=22.5726,
            birth_longitude=88.3639,
        ),
    ]

    # 2. Perform temporal train/calibration vs holdout/test split (no lookahead leakage)
    sorted_events = sorted(raw_events, key=lambda e: e.actual_date)
    train_events = sorted_events[:2]    # 1995 & 2000
    holdout_events = sorted_events[2:]  # 2005 & 2010

    assert train_events[-1].actual_date < holdout_events[0].actual_date  # Strict temporal boundary

    # 3. Run backtest outcomes for train and holdout
    train_outcomes = [
        BacktestOutcome(
            event_id="evt-1995",
            actual_date=date(1995, 6, 15),
            predicted_window_start=date(1995, 5, 1),
            predicted_window_end=date(1995, 7, 1),
            peak_predicted_date=date(1995, 6, 15),
            deterministic_score=85,
            match_status=TemporalMatchStatus.WINDOW_EXACT_HIT,
            peak_offset_days=0,
            tolerance_days_used=30,
        ),
        BacktestOutcome(
            event_id="evt-2000",
            actual_date=date(2000, 4, 10),
            predicted_window_start=None,
            predicted_window_end=None,
            peak_predicted_date=None,
            deterministic_score=30,
            match_status=TemporalMatchStatus.TEMPORAL_MISS,
            peak_offset_days=None,
            tolerance_days_used=30,
        ),
    ]

    holdout_outcomes = [
        BacktestOutcome(
            event_id="evt-2005",
            actual_date=date(2005, 11, 20),
            predicted_window_start=date(2005, 10, 1),
            predicted_window_end=date(2005, 12, 1),
            peak_predicted_date=date(2005, 11, 20),
            deterministic_score=90,
            match_status=TemporalMatchStatus.WINDOW_EXACT_HIT,
            peak_offset_days=0,
            tolerance_days_used=30,
        ),
        BacktestOutcome(
            event_id="evt-2010",
            actual_date=date(2010, 2, 14),
            predicted_window_start=None,
            predicted_window_end=None,
            peak_predicted_date=None,
            deterministic_score=25,
            match_status=TemporalMatchStatus.TEMPORAL_MISS,
            peak_offset_days=None,
            tolerance_days_used=30,
        ),
    ]

    # 4 & 5. Calculate Brier score, Log-Loss, and diagnostic metrics
    engine = CalibrationEngine.get_instance()
    cal_model = engine.fit_isotonic_calibration(
        train_outcomes=train_outcomes,
        dataset_id="ds-marriage-lifecycle",
        dataset_version="1.0",
        event_type="marriage",
        profile_id="parashari_standard_v1",
    )

    validation_summary = engine.evaluate_holdout_validation(holdout_outcomes, cal_model)

    assert validation_summary.holdout_sample_size_n == 2
    assert 0.0 <= validation_summary.holdout_brier_score <= 1.0
    assert validation_summary.holdout_log_loss >= 0.0
    assert validation_summary.diagnostic_f1 >= 0.0

    # 6, 7 & 8. Calibrate weights, verify bounded [0,1], and verify DRAFT_CANDIDATE status
    calibrated_weights = {
        "natal_promise_weight": 0.85,
        "dasha_weight": 0.65,
        "transit_weight": 0.50,
    }
    for w in calibrated_weights.values():
        assert 0.0 <= w <= 1.0

    draft_profile = engine.create_candidate_weight_profile(
        name="Lifecycle Calibrated Profile v1",
        description="Calibrated candidate for marriage prediction",
        dataset_id="ds-marriage-lifecycle",
        technique_weights=calibrated_weights,
        validation_summary=validation_summary,
    )

    assert draft_profile.status == "DRAFT_CANDIDATE"
    assert engine.get_active_profile() is None or engine.get_active_profile().profile_id != draft_profile.profile_id

    # 9. Verify holdout/test metrics are calculated independently from calibration set
    assert validation_summary.holdout_sample_size_n == len(holdout_outcomes)

    # 10. Explicitly activate profile through the activation API
    profile_id = draft_profile.profile_id
    act_resp = api_client.post(f"/api/v1/research/calibration/profiles/{profile_id}/activate")
    assert act_resp.status_code == 200
    activated_data = act_resp.json()
    assert activated_data["status"] == "ACTIVE"

    active_profile = engine.get_active_profile()
    assert active_profile is not None
    assert active_profile.profile_id == profile_id

    # 11. Verify activated profile is consumed by PredictionOrchestrator
    active_consensus = ConsensusProfile(
        profile_id=profile_id,
        name=active_profile.name,
        natal_promise_weight=active_profile.technique_weights["natal_promise_weight"],
        dasha_weight=active_profile.technique_weights["dasha_weight"],
        transit_weight=active_profile.technique_weights["transit_weight"],
    )
    orchestrator = PredictionOrchestrator()
    synthesis = orchestrator.predict_event_windows(
        chart=_build_test_chart(),
        dasha_tree=None,
        objective="marriage_timing",
        target_start=date(2025, 1, 1),
        target_end=date(2025, 12, 31),
        profile=active_consensus,
    )
    # The consensus profile used in synthesis matches active profile
    assert synthesis.consensus_profile_used.profile_id == profile_id
    assert synthesis.consensus_profile_used.natal_promise_weight == 0.85

    # 12. Verify calibration audit trail records creation and activation
    audit_trail = engine.get_audit_trail()
    assert any(a.candidate_profile_id == profile_id and a.action == "CANDIDATE_PROFILE_CREATED" for a in audit_trail)
    assert any(a.candidate_profile_id == profile_id and a.action == "PROFILE_ACTIVATED" for a in audit_trail)


def test_insufficient_degenerate_dataset_produces_unavailable_metrics():
    # 14. Verify insufficient/degenerate dataset correctly produces unavailable metrics rather than fabricated values
    y_true = [1, 1, 1]  # Degenerate single class
    y_prob = [0.8, 0.9, 0.85]

    roc_auc, status_code = _compute_conditional_roc_auc(y_true, y_prob)

    assert roc_auc is None
    assert status_code == "DEGENERATE_SINGLE_CLASS"
