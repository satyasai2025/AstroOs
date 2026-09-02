"""
Unit tests for Noise Diagnostic Engine implementing Section 18.
"""

import pytest
from apps.api.services.ml.noise_diagnostic_engine import (
    NoiseDiagnosticEngine,
    NoiseDiagnosticReport,
)


def test_noise_diagnostic_clean_case():
    rep = NoiseDiagnosticEngine.diagnose(
        latitude=28.6139,
        longitude=77.2090,
        deterministic_score=3.5,
        planet_block_total=2.1,
        residual_error=0.2,
        varga_opposition_index=0.1,
    )
    assert isinstance(rep, NoiseDiagnosticReport)
    assert rep.data_noise_score == 0.0
    assert rep.rules_noise_score == 0.0
    assert rep.model_noise_score == 0.0
    assert rep.dominant_noise_category == "CLEAN"
    assert rep.is_prediction_trustworthy is True


def test_noise_diagnostic_data_noise_triggered():
    rep = NoiseDiagnosticEngine.diagnose(
        latitude=0.0,
        longitude=0.0,
        deterministic_score=1.0,
        planet_block_total=1.0,
        residual_error=0.1,
    )
    assert rep.data_noise_score == 1.0
    assert rep.dominant_noise_category == "DATA"
    assert rep.is_prediction_trustworthy is False


def test_noise_diagnostic_rules_noise_weak_field():
    rep = NoiseDiagnosticEngine.diagnose(
        latitude=28.6139,
        longitude=77.2090,
        deterministic_score=0.05,
        planet_block_total=0.08,  # Weak-field zone
        residual_error=0.1,
    )
    assert rep.rules_noise_score >= 0.8
    assert rep.dominant_noise_category == "RULES"
