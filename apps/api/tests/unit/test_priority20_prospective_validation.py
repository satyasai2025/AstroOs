"""
Unit & Integration Tests for Priority 20 — Prospective Research Validation & Rule Lifecycle Engine
"""

import random
from datetime import date

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.prospective_validation import ProspectiveRuleLifecycleStatus
from apps.api.main import app
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine


def test_prospective_validation_insufficient_data_is_honest_not_fabricated():
    """
    An evaluated registration with no logged real subjects must report
    zero subjects and PROSPECTIVE_INCONCLUSIVE — this replaced a prior
    test that asserted on fully-fabricated metrics (fixed
    roc_auc=0.895/brier=0.042/etc. that ignored the total_subjects/
    positive_prevalence args entirely, the exact fake-fallback anti-
    pattern flagged elsewhere this session).
    """
    engine = ProspectiveValidationEngine()
    reg = engine.pre_register_hypothesis(
        hypothesis_id="hypo-empty-test",
        rule_name="Empty-state test rule",
        target_objective="marriage",
        formula_expression="X",
        thresholds={},
    )

    report = engine.evaluate_prospective_cohort(registration_id=reg.registration_id)

    assert report.total_prospective_subjects == 0
    assert report.final_lifecycle_status == ProspectiveRuleLifecycleStatus.PROSPECTIVE_INCONCLUSIVE
    assert "INSUFFICIENT_REAL_PROSPECTIVE_DATA" in report.epistemic_classification


def test_prospective_validation_engine_preregistration_and_evaluation():
    """
    Verify ProspectiveValidationEngine handles immutable pre-registration
    and evaluates a prospective cohort from REAL logged blind predictions
    and real recorded outcomes (not fabricated aggregate parameters).
    """
    engine = ProspectiveValidationEngine.get_instance()

    # 1. Pre-register hypothesis
    reg = engine.pre_register_hypothesis(
        hypothesis_id="hypo-19-top",
        rule_name="Prospective 7th Lord Dasha + Jupiter Aspect Rule",
        target_objective="marriage",
        formula_expression='DASHA == "7th_Lord" AND TRANSIT_ASPECT("Jupiter", 7) AND SAV_SCORE >= 30',
        thresholds={"min_lift": 1.35, "min_sav": 30.0},
        author="PrincipalAstrologicalScientist",
    )

    assert reg is not None
    assert len(reg.sha256_registration_hash) == 64
    assert len(reg.lineage_snapshot_id) > 0

    # 2. Log real blind predictions + real outcomes for a well-discriminating
    # synthetic cohort (high predicted probability strongly correlated with
    # a real positive outcome) so the evaluation genuinely earns SUPPORTED.
    rng = random.Random(7)
    for i in range(150):
        prob = rng.random()
        engine.log_blind_prediction(
            registration_id=reg.registration_id,
            subject_id=f"subj-{i:03d}",
            predicted_probability=prob,
            prediction_window_start=date(2026, 1, 1),
            prediction_window_end=date(2026, 6, 30),
        )
        outcome = rng.random() < (0.05 + 0.90 * prob)
        engine.record_subject_outcome(reg.registration_id, f"subj-{i:03d}", outcome)

    # 3. Evaluate prospective cohort — real computation from the logged data.
    report = engine.evaluate_prospective_cohort(registration_id=reg.registration_id)

    assert report is not None
    assert report.registration_id == reg.registration_id
    assert report.total_prospective_subjects == 150
    assert 0.0 <= report.roc_auc <= 1.0
    assert 0.0 <= report.brier_score <= 1.0
    assert report.statistical_lift > 0.0
    # A strongly-discriminating synthetic cohort should score well, but the
    # exact numbers are a real function of the logged data, not a fixed
    # constant — verify the metrics reflect genuine discrimination rather
    # than pinning brittle exact values.
    assert report.roc_auc >= 0.65


def test_prospective_validation_fastapi_endpoints():
    """Verify FastAPI router endpoints for pre-registration and prospective evaluation."""
    client = TestClient(app)

    # 1. Pre-register
    res_reg = client.post(
        "/api/v1/research/prospective/pre-register",
        json={
            "hypothesis_id": "hypo-19-top",
            "rule_name": "Prospective 7th Lord Dasha Rule",
            "target_objective": "marriage",
            "formula_expression": 'DASHA == "7th_Lord" AND SAV_SCORE >= 30',
            "thresholds": {"min_lift": 1.35},
            "author": "Tester",
        },
    )
    assert res_reg.status_code == 200
    data_reg = res_reg.json()
    reg_id = data_reg["registration_id"]
    assert len(data_reg["sha256_registration_hash"]) == 64

    # 2. List Registrations
    res_list = client.get("/api/v1/research/prospective/registrations")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert len(data_list) >= 1

    # 3. Log real blind predictions + real outcomes
    rng = random.Random(11)
    for i in range(60):
        prob = rng.random()
        client.post(
            "/api/v1/research/prospective/log-prediction",
            json={
                "registration_id": reg_id,
                "subject_id": f"subj-{i:03d}",
                "predicted_probability": prob,
                "prediction_window_start": "2026-01-01",
                "prediction_window_end": "2026-06-30",
            },
        )
        outcome = rng.random() < (0.05 + 0.90 * prob)
        client.post(
            "/api/v1/research/prospective/record-outcome",
            json={"registration_id": reg_id, "subject_id": f"subj-{i:03d}", "actual_outcome": outcome},
        )

    # 4. Evaluate Prospective
    res_eval = client.post(
        "/api/v1/research/prospective/evaluate",
        json={"registration_id": reg_id},
    )
    assert res_eval.status_code == 200
    data_eval = res_eval.json()
    eval_id = data_eval["evaluation_id"]
    assert data_eval["total_prospective_subjects"] == 60

    # 5. Get Evaluation Report
    res_get = client.get(f"/api/v1/research/prospective/evaluations/{eval_id}")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["evaluation_id"] == eval_id
    assert 0.0 <= data_get["roc_auc"] <= 1.0
