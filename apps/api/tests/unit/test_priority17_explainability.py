"""
Unit & Integration Tests for Priority 17 — Research & Prediction Explainability Engine
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from apps.api.domain.explainability import FactorLayer
from apps.api.main import app
from apps.api.services.explainability_engine import PredictionExplainabilityEngine


def test_prediction_explainability_engine_computations():
    """Verify PredictionExplainabilityEngine decomposes predictions, computes exact contribution %, and runs counterfactuals."""
    engine = PredictionExplainabilityEngine()

    # 1. Explain Marriage Prediction
    exp_marriage = engine.explain_prediction(
        target_objective="marriage",
        event_window_start=date(2026, 4, 1),
        event_window_end=date(2026, 9, 30),
    )

    assert exp_marriage.target_objective == "marriage"
    assert len(exp_marriage.atomic_factors) >= 4
    # Verify exact percentage attribution sums to 100% (+/- 0.5% due to rounding)
    total_pct = sum(f.contribution_percent for f in exp_marriage.atomic_factors)
    assert 99.0 <= total_pct <= 101.0
    assert exp_marriage.composite_confidence_score > 0.70
    assert len(exp_marriage.counterfactuals) >= 3
    assert exp_marriage.counterfactuals[0].simulated_score < exp_marriage.counterfactuals[0].baseline_score

    # 2. Interactive Counterfactual Simulation
    custom_cf = engine.evaluate_counterfactual(
        base_explanation=exp_marriage,
        perturbation_parameter="birth_time_shift_minutes",
        perturbation_value="-3 min",
    )
    assert custom_cf.perturbed_parameter == "birth_time_shift_minutes"
    assert custom_cf.score_delta_percent < 0.0

    # 3. Explain Career Prediction
    exp_career = engine.explain_prediction(target_objective="career")
    assert exp_career.target_objective == "career"
    assert len(exp_career.atomic_factors) >= 3


def test_prediction_explainability_fastapi_endpoints():
    """Verify FastAPI router endpoints for prediction explainability and counterfactual simulation."""
    client = TestClient(app)

    # 1. Test POST /api/v1/research/explain/prediction
    res_pred = client.post(
        "/api/v1/research/explain/prediction",
        json={"target_objective": "marriage", "event_window_start": "2026-04-01", "event_window_end": "2026-09-30"},
    )
    assert res_pred.status_code == 200
    data_pred = res_pred.json()
    assert data_pred["target_objective"] == "marriage"
    assert len(data_pred["atomic_factors"]) >= 4
    assert len(data_pred["counterfactuals"]) >= 3
    assert "plain_summary" in data_pred
    assert "classical_justification" in data_pred

    # 2. Test POST /api/v1/research/explain/counterfactual
    res_cf = client.post(
        "/api/v1/research/explain/counterfactual",
        json={
            "target_objective": "marriage",
            "perturbed_parameter": "dasha_lord_combustion",
            "parameter_value": "TRUE",
        },
    )
    assert res_cf.status_code == 200
    data_cf = res_cf.json()
    assert data_cf["perturbed_parameter"] == "dasha_lord_combustion"
    assert data_cf["simulated_score"] < data_cf["baseline_score"]
