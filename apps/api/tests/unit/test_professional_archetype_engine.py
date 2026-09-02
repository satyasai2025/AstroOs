"""
AstroOS — Professional Archetype & Wealth/Authority Discovery Engine Unit Tests
==============================================================================
Tests shastric rules, Rajya Yoga & Dhana Yoga verification, and 0-100% affinity scores
across 5 core archetypes:
1. Statesman / Politician (10th House, Sun, Mars, Rajya Pada A10)
2. Creative / Cinema (Venus, Rahu, 3rd & 5th Houses)
3. Sports / Athletes (Mars, 3rd & 6th Houses, Bhuja Bala, Shatru Vijaya)
4. Business / Wealth (Mercury, 2nd, 7th & 11th Houses, Dhana Yoga Lift)
5. Spiritual / Saints (Jupiter, Ketu, 9th & 12th Houses, Moksha Trikona)
"""

import os
from datetime import datetime, timezone
import pytest

from apps.api.services.professional_archetype_engine import (
    ARCHETYPE_SPECS,
    ProfessionalArchetypeEngine,
    ProfessionalArchetypeEvaluation,
)
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine


def test_archetype_specs_integrity():
    """Verify all 5 professional archetypes are properly cataloged with statistical metrics."""
    assert len(ARCHETYPE_SPECS) == 5
    expected_keys = [
        "POLITICIAN_LEADER",
        "ACTOR_CINEMA",
        "SPORTS_ATHLETICS",
        "BUSINESS_WEALTH",
        "SPIRITUAL_SAINT"
    ]
    for k in expected_keys:
        assert k in ARCHETYPE_SPECS
        spec = ARCHETYPE_SPECS[k]
        assert "title" in spec
        assert "domain" in spec
        assert len(spec["primary_planets"]) >= 3
        assert len(spec["primary_houses"]) >= 3
        assert spec["sample_size"] > 0
        assert spec["lift_score"] >= 2.0
        assert spec["confidence_score"] >= 0.95
        assert len(spec["shastric_rationale"]) > 20


def test_leader_politician_evaluation():
    """Tests sovereign leader signature with 10th house Sun, Mars in 6th, A10 in 10th, and Raja Yoga."""
    leader_planets = {
        "Sun": {"rashi": "Leo", "house": 10},
        "Mars": {"rashi": "Aries", "house": 6},
        "Jupiter": {"rashi": "Cancer", "house": 9},
        "Saturn": {"rashi": "Libra", "house": 12},
        "Venus": {"rashi": "Virgo", "house": 11},
        "Mercury": {"rashi": "Virgo", "house": 11},
        "Moon": {"rashi": "Cancer", "house": 9},
        "Rahu": {"rashi": "Gemini", "house": 8},
        "Ketu": {"rashi": "Sagittarius", "house": 2}
    }
    arudha_padas = {
        "A10": {"house": 10, "rashi": "Leo"},
        "AL": {"house": 1, "rashi": "Scorpio"}
    }
    active_yogas = ["Kendra-Trikona Raja Yoga", "Simhasana Yoga"]

    eval_res: ProfessionalArchetypeEvaluation = ProfessionalArchetypeEngine.evaluate_chart(
        planet_positions=leader_planets,
        lagna_rashi="Scorpio",
        arudha_padas=arudha_padas,
        active_yogas=active_yogas,
        amatyakaraka="Sun"
    )

    assert eval_res.dominant_archetype_key == "POLITICIAN_LEADER"
    assert eval_res.dominant_score >= 75.0
    assert eval_res.rajya_yogas_count >= 1

    leader_eval = next(a for a in eval_res.archetype_affinities if a.archetype_key == "POLITICIAN_LEADER")
    assert leader_eval.affinity_score >= 75.0
    assert len(leader_eval.matched_signatures) >= 3
    assert any("Surya" in s["signature_name"] or "Sun" in s["signature_name"] for s in leader_eval.matched_signatures)
    assert any("A10" in s["signature_name"] for s in leader_eval.matched_signatures)


def test_creative_cinema_evaluation():
    """Tests creative / cinema signature with Venus in 5th, Rahu on Lagna, 3rd-5th axis."""
    actor_planets = {
        "Venus": {"rashi": "Pisces", "house": 5, "nakshatra": "Revati"},
        "Rahu": {"rashi": "Scorpio", "house": 1},
        "Moon": {"rashi": "Pisces", "house": 5},
        "Mercury": {"rashi": "Capricorn", "house": 3},
        "Sun": {"rashi": "Aquarius", "house": 4},
        "Mars": {"rashi": "Aries", "house": 6},
        "Jupiter": {"rashi": "Cancer", "house": 9},
        "Saturn": {"rashi": "Taurus", "house": 7},
        "Ketu": {"rashi": "Taurus", "house": 7}
    }

    eval_res = ProfessionalArchetypeEngine.evaluate_chart(
        planet_positions=actor_planets,
        lagna_rashi="Scorpio"
    )

    assert eval_res.dominant_archetype_key == "ACTOR_CINEMA"
    assert eval_res.dominant_score >= 70.0

    actor_eval = next(a for a in eval_res.archetype_affinities if a.archetype_key == "ACTOR_CINEMA")
    assert actor_eval.affinity_score >= 70.0
    assert any("Venus" in s["signature_name"] for s in actor_eval.matched_signatures)
    assert any("Rahu" in s["signature_name"] for s in actor_eval.matched_signatures)


def test_sports_athletics_evaluation():
    """Tests sports champion signature with Mars in 6th, Saturn in 3rd, strong Upachaya malefic fortification."""
    athlete_planets = {
        "Mars": {"rashi": "Capricorn", "house": 6},
        "Saturn": {"rashi": "Libra", "house": 3},
        "Sun": {"rashi": "Leo", "house": 1},
        "Moon": {"rashi": "Aries", "house": 9},
        "Jupiter": {"rashi": "Sagittarius", "house": 5},
        "Mercury": {"rashi": "Virgo", "house": 2},
        "Venus": {"rashi": "Cancer", "house": 12},
        "Rahu": {"rashi": "Gemini", "house": 11},
        "Ketu": {"rashi": "Sagittarius", "house": 5}
    }

    eval_res = ProfessionalArchetypeEngine.evaluate_chart(
        planet_positions=athlete_planets,
        lagna_rashi="Leo"
    )

    assert eval_res.dominant_archetype_key == "SPORTS_ATHLETICS"
    assert eval_res.dominant_score >= 75.0

    athlete_eval = next(a for a in eval_res.archetype_affinities if a.archetype_key == "SPORTS_ATHLETICS")
    assert athlete_eval.affinity_score >= 75.0
    assert any("Mars" in s["signature_name"] or "Mangala" in s["signature_name"] for s in athlete_eval.matched_signatures)
    assert any("6th House" in s["signature_name"] for s in athlete_eval.matched_signatures)


def test_business_wealth_evaluation():
    """Tests commercial wealth titan signature with Mercury in 11th, Jupiter in 2nd, Dhana Yoga active."""
    business_planets = {
        "Mercury": {"rashi": "Virgo", "house": 11},
        "Jupiter": {"rashi": "Sagittarius", "house": 2},
        "Venus": {"rashi": "Libra", "house": 12},
        "Sun": {"rashi": "Leo", "house": 10},
        "Mars": {"rashi": "Capricorn", "house": 3},
        "Saturn": {"rashi": "Aquarius", "house": 4},
        "Moon": {"rashi": "Taurus", "house": 7},
        "Rahu": {"rashi": "Gemini", "house": 8},
        "Ketu": {"rashi": "Sagittarius", "house": 2}
    }
    arudha_padas = {
        "AL": {"house": 1, "rashi": "Scorpio"}
    }
    active_yogas = ["Dhana Yoga (2nd-11th Lord Association)"]

    eval_res = ProfessionalArchetypeEngine.evaluate_chart(
        planet_positions=business_planets,
        lagna_rashi="Scorpio",
        arudha_padas=arudha_padas,
        active_yogas=active_yogas
    )

    assert eval_res.dominant_archetype_key in ["BUSINESS_WEALTH", "POLITICIAN_LEADER"]
    biz_eval = next(a for a in eval_res.archetype_affinities if a.archetype_key == "BUSINESS_WEALTH")
    assert biz_eval.affinity_score >= 70.0
    assert eval_res.dhana_yogas_count >= 1
    assert any("Mercury" in s["signature_name"] for s in biz_eval.matched_signatures)
    assert any("11th House" in s["signature_name"] for s in biz_eval.matched_signatures)


def test_spiritual_saint_evaluation():
    """Tests spiritual guru signature with Jupiter in 9th, Ketu in 12th, and Moksha Trikona."""
    saint_planets = {
        "Jupiter": {"rashi": "Pisces", "house": 9},
        "Ketu": {"rashi": "Gemini", "house": 12},
        "Saturn": {"rashi": "Aquarius", "house": 8},
        "Moon": {"rashi": "Scorpio", "house": 5},
        "Sun": {"rashi": "Aries", "house": 10},
        "Mars": {"rashi": "Capricorn", "house": 7},
        "Mercury": {"rashi": "Taurus", "house": 11},
        "Venus": {"rashi": "Pisces", "house": 9},
        "Rahu": {"rashi": "Sagittarius", "house": 6}
    }

    eval_res = ProfessionalArchetypeEngine.evaluate_chart(
        planet_positions=saint_planets,
        lagna_rashi="Cancer",
        atmakaraka="Jupiter"
    )

    assert eval_res.dominant_archetype_key == "SPIRITUAL_SAINT"
    assert eval_res.dominant_score >= 75.0

    saint_eval = next(a for a in eval_res.archetype_affinities if a.archetype_key == "SPIRITUAL_SAINT")
    assert saint_eval.affinity_score >= 75.0
    assert any("Jupiter" in s["signature_name"] for s in saint_eval.matched_signatures)
    assert any("Ketu" in s["signature_name"] for s in saint_eval.matched_signatures)


def test_d1chart_end_to_end_evaluation():
    """Tests full end-to-end evaluation using a live D1Chart object generated from EphemerisWrapper."""
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    horoscope = HoroscopeEngine(wrapper)
    chart = horoscope.generate_d1(
        birth_datetime_utc=datetime(1950, 9, 17, 5, 30, tzinfo=timezone.utc),
        latitude=23.7833,
        longitude=72.6333
    )

    eval_res = ProfessionalArchetypeEngine.evaluate_chart(chart=chart)
    assert isinstance(eval_res, ProfessionalArchetypeEvaluation)
    assert eval_res.dominant_score > 0.0
    assert len(eval_res.archetype_affinities) == 5
    for a in eval_res.archetype_affinities:
        assert 0.0 <= a.affinity_score <= 100.0
        assert a.empirical_lift >= 2.0
        assert len(a.key_planetary_drivers) >= 0


def test_kundalee_store_case_loading():
    """Tests parsing and loading of empirical records from KundaleeStore."""
    cases = ProfessionalArchetypeEngine.load_empirical_cases()
    assert isinstance(cases, list)
    if cases:
        sample = cases[0]
        assert "case_id" in sample
        assert "archetype_key" in sample
        assert "latitude" in sample
        assert "longitude" in sample
