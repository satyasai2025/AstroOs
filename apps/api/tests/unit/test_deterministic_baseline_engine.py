"""
Unit tests for Deterministic Baseline Engine implementing all 8 Section 11 metrics.
"""

import pytest
from apps.api.services.deterministic_baseline_engine import (
    DeterministicBaselineEngine,
    DeterministicBaselineReport,
)


def test_deterministic_baseline_metrics_perfect_fit():
    preds = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    acts = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

    rep = DeterministicBaselineEngine.evaluate(preds, acts)
    assert rep.sample_count == 10
    assert rep.standard_deviation_error == 0.0
    assert rep.mean_error == 0.0
    
    # Check all 8 secondary metrics
    assert rep.correlation == 1.0
    assert rep.direction_accuracy_pct == 100.0
    assert rep.volatility_fit == 1.0
    assert rep.drawdown_error == 0.0
    assert rep.walk_forward_stability == 0.0
    assert rep.probability_calibration < 0.1
    assert rep.residual_autocorrelation == 0.0


def test_deterministic_baseline_metrics_realistic_error():
    preds = [2.0, -1.5, 3.0, -2.0, 4.5, -3.0, 2.5, -1.0, 3.5, -2.5]
    acts = [1.8, -1.2, 2.5, -1.8, 4.0, -2.8, 2.2, -0.8, 3.0, -2.0]

    rep = DeterministicBaselineEngine.evaluate(preds, acts)
    assert rep.sample_count == 10
    assert rep.standard_deviation_error > 0.0
    assert rep.direction_accuracy_pct == 100.0
    assert rep.correlation > 0.95
    assert rep.volatility_fit > 0.0
    assert rep.drawdown_error >= 0.0
    assert rep.probability_calibration >= 0.0
