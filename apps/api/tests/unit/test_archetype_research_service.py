"""
Unit tests for ArchetypeResearchService and Professional Archetype Discovery
"""

import pytest
from apps.api.services.archetype_research_service import ArchetypeResearchService


def test_archetype_patterns_structure():
    res = ArchetypeResearchService.get_empirical_archetype_patterns()
    assert "archetypes" in res
    assert len(res["archetypes"]) == 5

    keys = [a["archetype_key"] for a in res["archetypes"]]
    assert "POLITICIAN_LEADER" in keys
    assert "ACTOR_CINEMA" in keys
    assert "SPORTS_ATHLETICS" in keys
    assert "BUSINESS_WEALTH" in keys
    assert "SPIRITUAL_SAINT" in keys

    for a in res["archetypes"]:
        assert a["sample_size"] > 0
        assert a["lift_score"] > 2.0
        assert a["confidence_score"] > 0.95
        assert len(a["signatures"]) >= 3


def test_native_archetype_leader_evaluation():
    leader_planets = {
        "Sun": {"rashi": "Leo", "house": 10},
        "Mars": {"rashi": "Aries", "house": 6},
        "Jupiter": {"rashi": "Sagittarius", "house": 2},
        "Saturn": {"rashi": "Aquarius", "house": 4},
        "Venus": {"rashi": "Libra", "house": 12},
        "Mercury": {"rashi": "Virgo", "house": 11},
        "Moon": {"rashi": "Cancer", "house": 9},
        "Rahu": {"rashi": "Gemini", "house": 8},
        "Ketu": {"rashi": "Sagittarius", "house": 2}
    }
    eval_res = ArchetypeResearchService.evaluate_native_archetype(leader_planets, "Scorpio")
    assert "dominant_archetype" in eval_res
    assert eval_res["dominant_archetype"]["archetype_key"] in ["POLITICIAN_LEADER", "SPORTS_ATHLETICS"]
    assert eval_res["dominant_archetype"]["resonance_score"] >= 60.0


def test_native_archetype_spiritual_evaluation():
    saint_planets = {
        "Jupiter": {"rashi": "Pisces", "house": 9},
        "Ketu": {"rashi": "Taurus", "house": 12},
        "Sun": {"rashi": "Aries", "house": 10},
        "Moon": {"rashi": "Cancer", "house": 1},
        "Mars": {"rashi": "Capricorn", "house": 7},
        "Mercury": {"rashi": "Gemini", "house": 12},
        "Venus": {"rashi": "Taurus", "house": 11},
        "Saturn": {"rashi": "Aquarius", "house": 8},
        "Rahu": {"rashi": "Scorpio", "house": 6}
    }
    eval_res = ArchetypeResearchService.evaluate_native_archetype(saint_planets, "Cancer")
    assert "dominant_archetype" in eval_res
    saint_eval = next(a for a in eval_res["archetype_evaluations"] if a["archetype_key"] == "SPIRITUAL_SAINT")
    assert saint_eval["resonance_score"] >= 60.0
