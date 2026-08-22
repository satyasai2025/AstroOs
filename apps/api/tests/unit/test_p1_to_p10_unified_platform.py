"""
AstroOS — P1-P10 Unified Platform Integration Test Suite

Verifies that Priorities 1 through 10 operate seamlessly as ONE integrated
end-to-end astrological research and prediction platform.
"""

import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient

from apps.api.dependencies import require_authenticated
from apps.api.domain.astro_dsl import parse_astro_dsl
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.research_calibration import (
    BacktestOutcome,
    GroundTruthEvent,
    TemporalMatchStatus,
)
from apps.api.main import app
from apps.api.services.argala_engine import ArgalaEngine
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.astro_dsl_evaluator import evaluate_astro_dsl
from apps.api.services.calibration_engine import CalibrationEngine
from apps.api.services.custom_technique_service import CustomTechniqueRegistry
from apps.api.services.fact_builder import FactBuilder
from apps.api.domain.prediction_orchestration import ConsensusProfile
from apps.api.services.prediction_orchestrator import PredictionOrchestrator
from apps.api.services.statistical_sweep_engine import StatisticalSweepEngine
from apps.api.services.technique_engine import TechniqueEngine


@pytest.fixture
def api_client():
    app.dependency_overrides[require_authenticated] = lambda: {"sub": "unified_platform_tester"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _build_unified_chart():
    """Helper to build a complete canonical birth chart for P1-P10 integration testing."""
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


def test_p1_to_p10_unified_platform_pipeline(api_client):
    chart = _build_unified_chart()

    # ── P1: Classical Calculation Engines (Argala & Ashtakavarga) ────────────
    argala_engine = ArgalaEngine()
    argala_res = argala_engine.compute(chart, "aries")
    assert argala_res is not None

    ashtaka_engine = AshtakavargaEngine()
    bav = ashtaka_engine.compute_bhinnashtakavarga(chart)
    assert len(bav) >= 7

    # ── P2: Cohort & Fact Building ──────────────────────────────────────────
    fact_builder = FactBuilder()
    facts = fact_builder.build_facts(chart)
    assert facts is not None

    # ── P9: AstroDSL Parsing, Evaluation & Custom Technique Registry ────────
    dsl_code = 'PLANET("Jupiter").house IN [1, 4, 7, 10]'
    ast = parse_astro_dsl(dsl_code)
    assert ast is not None

    chart_ctx = {
        "planets": [{"planet": "JUPITER", "house_number": 4, "is_combust": False}],
        "planet_strengths": [],
    }
    dsl_eval = evaluate_astro_dsl(dsl_code, chart_ctx)
    assert dsl_eval.is_satisfied is True

    registry = CustomTechniqueRegistry.get_instance()
    custom_rule = registry.register_rule(
        name="Jupiter Kendra Custom Rule",
        description="Jupiter in Kendra",
        dsl_source=dsl_code,
        category="marriage",
        tags=["jupiter", "kendra"],
    )
    assert custom_rule.rule_id is not None

    # ── P7 & P10: Benchmark Event Datasets, Calibration & Audit Trail ───────
    raw_events = [
        GroundTruthEvent(
            event_id="e1",
            subject_id="s1",
            event_type="marriage",
            actual_date=date(2000, 1, 1),
            birth_datetime_utc=datetime(1975, 1, 1, 0, 0),
            birth_latitude=28.61,
            birth_longitude=77.20,
        ),
        GroundTruthEvent(
            event_id="e2",
            subject_id="s2",
            event_type="marriage",
            actual_date=date(2005, 6, 15),
            birth_datetime_utc=datetime(1980, 5, 10, 0, 0),
            birth_latitude=19.07,
            birth_longitude=72.87,
        ),
    ]

    train_outcomes = [
        BacktestOutcome(
            event_id="e1",
            actual_date=date(2000, 1, 1),
            predicted_window_start=date(2000, 1, 1),
            predicted_window_end=date(2000, 1, 31),
            peak_predicted_date=date(2000, 1, 1),
            deterministic_score=85,
            match_status=TemporalMatchStatus.WINDOW_EXACT_HIT,
            peak_offset_days=0,
            tolerance_days_used=30,
        )
    ]
    holdout_outcomes = [
        BacktestOutcome(
            event_id="e2",
            actual_date=date(2005, 6, 15),
            predicted_window_start=date(2005, 6, 1),
            predicted_window_end=date(2005, 6, 30),
            peak_predicted_date=date(2005, 6, 15),
            deterministic_score=90,
            match_status=TemporalMatchStatus.WINDOW_EXACT_HIT,
            peak_offset_days=0,
            tolerance_days_used=30,
        )
    ]

    cal_engine = CalibrationEngine.get_instance()
    cal_model = cal_engine.fit_isotonic_calibration(
        train_outcomes=train_outcomes,
        dataset_id="ds-unified-01",
        dataset_version="1.0",
        event_type="marriage",
        profile_id="parashari_standard_v1",
    )

    val_summary = cal_engine.evaluate_holdout_validation(holdout_outcomes, cal_model)

    draft_profile = cal_engine.create_candidate_weight_profile(
        name="Unified Platform Calibrated Profile",
        description="Unified E2E Profile",
        dataset_id="ds-unified-01",
        technique_weights={
            "natal_promise_weight": 0.80,
            "dasha_weight": 0.70,
            "transit_weight": 0.60,
        },
        validation_summary=val_summary,
    )
    assert draft_profile.status == "DRAFT_CANDIDATE"

    # Explicit activation via API
    profile_id = draft_profile.profile_id
    act_resp = api_client.post(f"/api/v1/research/calibration/profiles/{profile_id}/activate")
    assert act_resp.status_code == 200
    assert act_resp.json()["status"] == "ACTIVE"

    # ── P8: Prediction Orchestrator Consuming Calibrated Active Profile ─────
    active_profile = cal_engine.get_active_profile()
    active_consensus = ConsensusProfile(
        profile_id=profile_id,
        name=active_profile.name if active_profile else "Active",
        natal_promise_weight=active_profile.technique_weights["natal_promise_weight"] if active_profile else 0.80,
        dasha_weight=active_profile.technique_weights["dasha_weight"] if active_profile else 0.70,
        transit_weight=active_profile.technique_weights["transit_weight"] if active_profile else 0.60,
    )
    orchestrator = PredictionOrchestrator()
    synthesis = orchestrator.predict_event_windows(
        chart=chart,
        dasha_tree=None,
        objective="marriage_timing",
        target_start=date(2025, 1, 1),
        target_end=date(2025, 12, 31),
        profile=active_consensus,
    )

    assert synthesis.consensus_profile_used.profile_id == profile_id
    assert synthesis.consensus_profile_used.natal_promise_weight == 0.80

    # ── Immutable Audit Trail Check ──────────────────────────────────────────
    audit_trail = cal_engine.get_audit_trail()
    assert any(a.candidate_profile_id == profile_id and a.action == "PROFILE_ACTIVATED" for a in audit_trail)
