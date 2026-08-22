"""
Unit & Integration Tests for Priority 20 — Prospective Research Validation & Rule Lifecycle Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.domain.prospective_validation import ProspectiveRuleLifecycleStatus
from apps.api.main import app
from apps.api.services.prospective_validation_engine import ProspectiveValidationEngine


def test_prospective_validation_engine_preregistration_and_evaluation():
    """Verify ProspectiveValidationEngine handles immutable pre-registration and evaluates prospective cohort."""
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

    # 2. Evaluate prospective cohort
    report = engine.evaluate_prospective_cohort(
        registration_id=reg.registration_id,
        total_subjects=150,
        positive_prevalence=0.52,
    )

    assert report is not None
    assert report.registration_id == reg.registration_id
    assert report.total_prospective_subjects == 150
    assert report.roc_auc >= 0.75
    assert report.brier_score <= 0.15
    assert report.statistical_lift >= 1.30
    assert report.drift_analysis.is_significant_drift is False
    assert report.final_lifecycle_status == ProspectiveRuleLifecycleStatus.PROSPECTIVELY_SUPPORTED
    assert "EMPIRICALLY_SUPPORTED" in report.epistemic_classification


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

    # 3. Evaluate Prospective
    res_eval = client.post(
        "/api/v1/research/prospective/evaluate",
        json={
            "registration_id": reg_id,
            "total_subjects": 150,
            "positive_prevalence": 0.52,
        },
    )
    assert res_eval.status_code == 200
    data_eval = res_eval.json()
    eval_id = data_eval["evaluation_id"]
    assert data_eval["final_lifecycle_status"] == "PROSPECTIVELY_SUPPORTED"

    # 4. Get Evaluation Report
    res_get = client.get(f"/api/v1/research/prospective/evaluations/{eval_id}")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["evaluation_id"] == eval_id
    assert data_get["roc_auc"] >= 0.75
