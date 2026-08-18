"""
Unit tests for Guru Research Engine.
Verifies boundary matching, ruler matching, comparison with classical dignity,
and custom rule registration.
"""

import pytest
from apps.api.services.guru_research_engine import GuruResearchEngine
from apps.api.domain.guru_rules import GuruZoneType, GuruZoneRule


def test_initial_partition_rules():
    engine = GuruResearchEngine()
    rules = engine.get_all_rules()
    
    assert "aries" in rules
    assert "cancer" in rules
    assert "virgo" in rules
    assert "libra" in rules
    assert "pisces" in rules
    
    # Aries should have 4 partitions
    assert len(rules["aries"]) == 4
    assert rules["aries"][0]["description"] == "0-10° Sun Exaltation Zone"
    assert rules["aries"][1]["description"] == "11-12° Mars Moolatrikona Zone"
    assert rules["aries"][2]["description"] == "13-20° Saturn Debilitation Zone"
    assert rules["aries"][3]["description"] == "21-30° Mars Own Sign Zone"


def test_aries_evaluations():
    engine = GuruResearchEngine()
    
    # Sun at 5° Aries (inside 0-10° Sun Exaltation Zone)
    eval_sun = engine.evaluate_planet("sun", "aries", 5.0)
    assert eval_sun.guru_zone_lord == "sun"
    assert eval_sun.guru_zone_type == GuruZoneType.EXALTATION
    assert eval_sun.is_ruler_match is True
    assert eval_sun.classical_dignity == "exalted"
    assert eval_sun.is_dignity_agreement is True
    
    # Mars at 11.5° Aries (inside 10-12° Mars Moolatrikona Zone)
    eval_mars = engine.evaluate_planet("mars", "aries", 11.5)
    assert eval_mars.guru_zone_lord == "mars"
    assert eval_mars.guru_zone_type == GuruZoneType.MOOLATRIKONA
    assert eval_mars.is_ruler_match is True
    assert eval_mars.classical_dignity == "moolatrikona"
    assert eval_mars.is_dignity_agreement is True

    # Saturn at 15° Aries (inside 12-20° Saturn Debilitation Zone)
    eval_sat = engine.evaluate_planet("saturn", "aries", 15.0)
    assert eval_sat.guru_zone_lord == "saturn"
    assert eval_sat.guru_zone_type == GuruZoneType.DEBILITATION
    assert eval_sat.is_ruler_match is True
    assert eval_sat.classical_dignity == "debilitated"
    assert eval_sat.is_dignity_agreement is True


def test_cancer_evaluations():
    engine = GuruResearchEngine()
    
    # Jupiter at 2° Cancer (0-5° Jupiter Exaltation Zone)
    eval_jup = engine.evaluate_planet("jupiter", "cancer", 2.0)
    assert eval_jup.guru_zone_lord == "jupiter"
    assert eval_jup.guru_zone_type == GuruZoneType.EXALTATION
    assert eval_jup.is_ruler_match is True

    # Mars at 10° Cancer (6-28° Mars Debilitation Zone)
    eval_mars = engine.evaluate_planet("mars", "cancer", 10.0)
    assert eval_mars.guru_zone_lord == "mars"
    assert eval_mars.guru_zone_type == GuruZoneType.DEBILITATION
    assert eval_mars.is_ruler_match is True


def test_chart_evaluation():
    engine = GuruResearchEngine()
    positions = [
        {"planet": "sun", "rashi": "aries", "degree_in_rashi": 5.0},
        {"planet": "moon", "rashi": "taurus", "degree_in_rashi": 2.0},
        {"planet": "mars", "rashi": "capricorn", "degree_in_rashi": 15.0},
        {"planet": "mercury", "rashi": "virgo", "degree_in_rashi": 10.0},
        {"planet": "jupiter", "rashi": "cancer", "degree_in_rashi": 3.0},
        {"planet": "venus", "rashi": "pisces", "degree_in_rashi": 20.0},
        {"planet": "saturn", "rashi": "libra", "degree_in_rashi": 15.0},
    ]
    
    report = engine.evaluate_chart(positions)
    assert len(report.evaluations) == 7
    assert report.agreements_count >= 5
    assert len(report.summary_insights) >= 5


def test_extensible_rule_registration():
    engine = GuruResearchEngine()
    
    # Register a new custom rule for Gemini
    custom_rule = GuruZoneRule(
        start_deg=0.0,
        end_deg=10.0,
        zone_type=GuruZoneType.SPECIAL,
        ruling_planet="mercury",
        description="0-10° Teacher Custom Intelligence Zone",
        strength_weight=9.5,
    )
    engine.register_zone_rule("gemini", custom_rule)
    
    eval_res = engine.evaluate_planet("mercury", "gemini", 5.0)
    assert eval_res.guru_zone_name == "0-10° Teacher Custom Intelligence Zone"
    assert eval_res.guru_zone_type == GuruZoneType.SPECIAL
