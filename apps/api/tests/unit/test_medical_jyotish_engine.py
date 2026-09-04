"""
Unit tests for MedicalJyotishEngine and Clinical Vulnerability Timing
"""

import pytest
from apps.api.services.medical_jyotish_engine import MedicalJyotishEngine


def test_medical_jyotish_engine_patterns():
    res = MedicalJyotishEngine.get_empirical_medical_patterns()
    assert "patterns" in res
    assert len(res["patterns"]) == 4

    disease_codes = [p["disease_code"] for p in res["patterns"]]
    assert "HEART_DISEASE" in disease_codes
    assert "DIABETES" in disease_codes
    assert "ASTHMA_RESPIRATORY" in disease_codes
    assert "EPILEPSY_NEURO" in disease_codes

    for pat in res["patterns"]:
        assert pat["sample_size"] > 0
        assert pat["lift_score"] >= 2.0
        assert pat["confidence_score"] >= 0.95
        assert len(pat["signatures"]) >= 3
        assert len(pat["transit_triggers"]) >= 3


def test_medical_jyotish_engine_vulnerability_scoring():
    planets = {
        "Sun": {"rashi": "Leo", "house": 8},
        "Saturn": {"rashi": "Leo", "house": 8},
        "Rahu": {"rashi": "Leo", "house": 8},
        "Mars": {"rashi": "Taurus", "house": 5},
        "Jupiter": {"rashi": "Capricorn", "house": 1},
        "Venus": {"rashi": "Virgo", "house": 9},
        "Mercury": {"rashi": "Cancer", "house": 7},
        "Moon": {"rashi": "Scorpio", "house": 11},
        "Ketu": {"rashi": "Aquarius", "house": 2}
    }
    result = MedicalJyotishEngine.evaluate_native_medical_chart(planets, "Capricorn")
    assert "overall_vitality_index" in result
    assert result["overall_vitality_index"] < 90.0

    evals = result["vulnerability_evaluations"]
    assert len(evals) == 4
    heart_eval = next(e for e in evals if e["disease_code"] == "HEART_DISEASE")
    assert heart_eval["risk_score"] >= 40.0
    assert len(heart_eval["shastric_remedies"]) >= 2
