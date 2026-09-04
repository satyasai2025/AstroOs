"""
Unit tests for MedicalResearchService and Medical Jyotish Pattern Mining
"""

import pytest
from apps.api.services.medical_research_service import MedicalResearchService


def test_medical_patterns_structure():
    res = MedicalResearchService.get_empirical_medical_patterns()
    assert "patterns" in res
    assert len(res["patterns"]) == 4
    
    codes = [p["disease_code"] for p in res["patterns"]]
    assert "HEART_DISEASE" in codes
    assert "DIABETES" in codes
    assert "ASTHMA_RESPIRATORY" in codes
    assert "EPILEPSY_NEURO" in codes

    for p in res["patterns"]:
        assert p["sample_size"] > 0
        assert p["lift_score"] > 1.5
        assert p["confidence_score"] > 0.90
        assert len(p["signatures"]) >= 2
        assert len(p["transit_triggers"]) >= 2


def test_medical_chart_evaluation_resilient():
    # Affliction-free / fortified chart
    planets = {
        "Sun": {"rashi": "Aries", "house": 10},
        "Mars": {"rashi": "Capricorn", "house": 7},
        "Jupiter": {"rashi": "Cancer", "house": 1},
        "Venus": {"rashi": "Pisces", "house": 9},
        "Mercury": {"rashi": "Virgo", "house": 3},
        "Moon": {"rashi": "Taurus", "house": 11},
        "Saturn": {"rashi": "Libra", "house": 4},
        "Rahu": {"rashi": "Gemini", "house": 12},
        "Ketu": {"rashi": "Sagittarius", "house": 6}
    }
    result = MedicalResearchService.evaluate_native_medical_chart(planets, "Cancer")
    assert "overall_vitality_index" in result
    assert result["overall_vitality_index"] > 50.0
    assert len(result["vulnerability_evaluations"]) == 4


def test_medical_heart_affliction_detection():
    # Afflicted Sun in 8th house with Saturn & Rahu
    afflicted_planets = {
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
    result = MedicalResearchService.evaluate_native_medical_chart(afflicted_planets, "Capricorn")
    heart_eval = next(e for e in result["vulnerability_evaluations"] if e["disease_code"] == "HEART_DISEASE")
    assert heart_eval["risk_score"] >= 40.0
    assert len(heart_eval["primary_afflictions"]) >= 2
