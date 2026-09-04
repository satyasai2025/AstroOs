"""
AstroOS — Unit Tests for Kundalee 144 Bhaava-Phala Engine
"""

import pytest
from apps.api.services.canonical_bhava_phala import KundaleeBhavaPhalaEngine


@pytest.fixture
def bhava_phala_engine():
    return KundaleeBhavaPhalaEngine()


def test_load_all_144_rules(bhava_phala_engine):
    """Verify that all 144 Bhaava-Phala rules from Kundalee binary (Phalit.kkk) are loaded."""
    assert bhava_phala_engine.total_rules == 144


def test_lookup_specific_rules(bhava_phala_engine):
    """Verify specific classical Parashari rules from Kundalee dataset."""
    # 1L in 1H -> KU0001
    r1_1 = bhava_phala_engine.get_rule(1, 1)
    assert r1_1 is not None
    assert r1_1["knowledge_id"] == "KU0001"
    assert "physical happiness and prowess" in r1_1["statement"]

    # 10L in 10H -> KU0118
    r10_10 = bhava_phala_engine.get_rule(10, 10)
    assert r10_10 is not None
    assert "10L in 10H" in r10_10["statement"]
    assert "skilful in all jobs, be valorous, truthful" in r10_10["result"]

    # 12L in 12H -> KU0144
    r12_12 = bhava_phala_engine.get_rule(12, 12)
    assert r12_12 is not None
    assert r12_12["knowledge_id"] == "KU0144"
    assert "heavy expenditure" in r12_12["statement"]


def test_chart_evaluation(bhava_phala_engine):
    """Verify evaluation of a complete chart's 12 house lords."""
    sample_chart = {
        1: 1,   # 1L in 1H
        2: 11,  # 2L in 11H
        3: 3,   # 3L in 3H
        4: 10,  # 4L in 10H
        5: 5,   # 5L in 5H
        6: 6,   # 6L in 6H
        7: 1,   # 7L in 1H
        8: 8,   # 8L in 8H
        9: 9,   # 9L in 9H
        10: 10, # 10L in 10H
        11: 2,  # 11L in 2H
        12: 12, # 12L in 12H
    }
    results = bhava_phala_engine.evaluate_chart_placements(sample_chart)
    assert len(results) == 12
    assert results[0]["knowledge_id"] == "KU0001"
    assert results[9]["occupied_house"] == 10


def test_dual_lordship_synthesis_mars_aries_lagna(bhava_phala_engine):
    """
    In Aries Lagna (1):
    Mars owns Aries (1H - Moolatrikona) and Scorpio (8H - Secondary).
    If Mars is in 1H:
    - Primary is 1L in 1H (physical happiness, prowess).
    - Secondary is 8L in 1H (sickly, hard-hearted, etc.).
    Jha's synthesis rule: Contrary results exist -> VARIED_AND_MODIFIED with 1H dominating.
    """
    synth = bhava_phala_engine.synthesize_planet_lordships(
        planet="mars",
        lagna_sign=1,  # Aries
        occupied_house=1,  # in 1H
    )
    assert synth.planet == "mars"
    assert synth.occupied_house == 1
    assert synth.primary_house == 1
    assert synth.secondary_house == 8
    assert synth.verdict == "VARIED_AND_MODIFIED"
    assert "Moolatrikona" in synth.synthesis_text
    assert synth.primary_phala["knowledge_id"] == "KU0001"
    assert synth.secondary_phala["knowledge_id"] == "KU0085"  # 8L in 1H


def test_dual_lordship_single_lord_sun(bhava_phala_engine):
    """Sun owns only Leo (5H for Aries Lagna). Verdict must be SINGLE_LORDSHIP."""
    synth = bhava_phala_engine.synthesize_planet_lordships(
        planet="sun",
        lagna_sign=1,
        occupied_house=10,
    )
    assert synth.planet == "sun"
    assert synth.primary_house == 5
    assert synth.secondary_house is None
    assert synth.verdict == "SINGLE_LORDSHIP"
    assert synth.primary_phala["knowledge_id"] == "KU0058"  # 5L in 10H


def test_synthesize_chart_all_7_planets(bhava_phala_engine):
    """Verify complete chart synthesis across all 7 classical planets."""
    placements = {
        "sun": 10,
        "moon": 4,
        "mars": 1,
        "mercury": 2,
        "jupiter": 9,
        "venus": 7,
        "saturn": 11,
    }
    chart_synths = bhava_phala_engine.synthesize_chart_dual_lordships(
        lagna_sign=1,
        planet_placements=placements,
    )
    assert len(chart_synths) == 7
    assert set(chart_synths.keys()) == {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
    assert chart_synths["jupiter"].primary_house == 9  # Sagittarius MT
    assert chart_synths["jupiter"].secondary_house == 12  # Pisces
    assert chart_synths["saturn"].primary_house == 11  # Aquarius MT
    assert chart_synths["saturn"].secondary_house == 10  # Capricorn


def test_modulate_phala_by_strength_full_half_quarter():
    """
    Verify Jha's Shastric rule from Phalit.kkk:
    'The Grah will yield full, half, or a quarter of the effects according to its
     strength being full, medium and negligible, respectively.'
    """
    from apps.api.services.canonical_bhava_phala import modulate_phala_by_strength

    raw = "the native will be endowed with royal honour and great wealth."

    # Full strength (Tier 9: Exalted) -> factor 1.0 (100%)
    m_full = modulate_phala_by_strength(raw, dignity_tier=9)
    assert m_full["strength_tier"] == "FULL"
    assert m_full["modulation_factor"] == 1.0
    assert "Full effects (100% manifestation)" in m_full["modulated_statement"]

    # Medium strength (Tier 5: Neutral / Mitra) -> factor 0.5 (50%)
    m_med = modulate_phala_by_strength(raw, dignity_tier=5)
    assert m_med["strength_tier"] == "MEDIUM"
    assert m_med["modulation_factor"] == 0.5
    assert "Medium/Half effects (50% manifestation" in m_med["modulated_statement"]

    # Negligible strength (Tier 1: Debilitated) -> factor 0.25 (25%)
    m_neg = modulate_phala_by_strength(raw, dignity_tier=1)
    assert m_neg["strength_tier"] == "NEGLIGIBLE"
    assert m_neg["modulation_factor"] == 0.25
    assert "Quarter/Negligible effects (25% manifestation" in m_neg["modulated_statement"]


def test_chart_synthesis_with_dignity_tiers(bhava_phala_engine):
    """Verify that passing dignity tiers into chart synthesis sets modulation factors accurately."""
    placements = {"sun": 10, "mars": 1}
    dignities = {"sun": 9, "mars": 1}  # Sun exalted (Tier 9), Mars debilitated (Tier 1)

    synths = bhava_phala_engine.synthesize_chart_dual_lordships(
        lagna_sign=1,
        planet_placements=placements,
        planet_dignity_tiers=dignities,
    )
    assert synths["sun"].strength_tier == "FULL"
    assert synths["sun"].modulation_factor == 1.0

    assert synths["mars"].strength_tier == "NEGLIGIBLE"
    assert synths["mars"].modulation_factor == 0.25
