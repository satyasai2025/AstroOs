"""
Unit & Integration Tests for Priority 15 — Longitudinal Cohort Statistical Validation Engine
"""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.cohort_validation_engine import CohortValidationEngine


def test_cohort_validation_engine():
    """Verify CohortValidationEngine computes metrics and runs Monte Carlo permutation tests."""
    engine = CohortValidationEngine()
    report = engine.evaluate_cohort(
        dataset_id="ds-marriage-28",
        monte_carlo_iterations=50,
        random_seed=42,
    )

    assert report.total_subjects_evaluated == 250
    assert 0.70 <= report.roc_auc <= 1.0
    assert 0.0 <= report.brier_score <= 0.20
    assert report.monte_carlo_iterations == 50
    assert report.permutation_p_value <= 0.05
    assert len(report.hypothesis_tests) > 0
    assert report.hypothesis_tests[0].is_statistically_significant is True
    assert report.hypothesis_tests[0].z_score > 2.0


def test_cohort_validation_fastapi_endpoints():
    """Verify FastAPI router endpoints for Cohort benchmarks and evaluation."""
    client = TestClient(app)

    # 1. Test /api/v1/research/cohort/benchmarks
    b_res = client.get("/api/v1/research/cohort/benchmarks")
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert len(b_data) >= 3

    # 2. Test /api/v1/research/cohort/evaluate
    req = {
        "dataset_id": "ds-marriage-28",
        "monte_carlo_iterations": 30,
        "random_seed": 123,
    }
    e_res = client.post("/api/v1/research/cohort/evaluate", json=req)
    assert e_res.status_code == 200
    e_data = e_res.json()
    assert e_data["dataset_id"] == "ds-marriage-28"
    assert e_data["roc_auc"] >= 0.70
    assert e_data["permutation_p_value"] <= 0.05
    assert len(e_data["hypothesis_tests"]) == 1
