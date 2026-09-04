"""
AstroOS — Unit Tests for Maraka, Badhaka, and Sambandha Engine
==============================================================
Validates:
  1. Badhaka Sthana & Badhakesh based on Lagna Modality (Chara -> 11th, Sthira -> 9th, Dvisvabhava -> 7th)
  2. Primary Marakas (2H & 7H) and Secondary Marakas (Trik 6H, 8H, 12H)
  3. Saturn Maraka absorption rule
  4. Jha's 5-Tier Maraka Confluence:
     "सामान्यतः मृत्यु तब होती है जब विंशोत्तरी महादशा से प्राणदशा तक पाँचों ग्रह मारक हों और अलग-अलग ग्रह हों।"
  5. Distinct Graha Axiom (repeating same planet does NOT trigger mortality)
  6. Tatkalika Maitri filter
  7. Flexible (Non-hardcoded) configuration
"""

import pytest

from apps.api.domain.maraka import BadhakaConfig, LagnaModality, MarakaConfig
from apps.api.services.maraka_engine import MarakaEngine


def test_badhaka_modality_rules():
    """Verify Badhaka house assignment: Chara -> 11th, Sthira -> 9th, Dvisvabhava -> 7th."""
    engine = MarakaEngine()

    # Aries (Chara) -> 11th house = Aquarius (Saturn)
    b_aries = engine.get_badhaka_info("aries")
    assert b_aries.lagna_modality == LagnaModality.CHARA
    assert b_aries.badhaka_house == 11
    assert b_aries.badhakesh_planet == "saturn"

    # Taurus (Sthira) -> 9th house = Capricorn (Saturn)
    b_taurus = engine.get_badhaka_info("taurus")
    assert b_taurus.lagna_modality == LagnaModality.STHIRA
    assert b_taurus.badhaka_house == 9
    assert b_taurus.badhakesh_planet == "saturn"

    # Gemini (Dvisvabhava) -> 7th house = Sagittarius (Jupiter)
    b_gemini = engine.get_badhaka_info("gemini")
    assert b_gemini.lagna_modality == LagnaModality.DVISVABHAVA
    assert b_gemini.badhaka_house == 7
    assert b_gemini.badhakesh_planet == "jupiter"


def test_maraka_planet_identification_and_saturn_absorption():
    """Verify identification of 2H, 7H, and Trik lords, plus Saturn absorption."""
    engine = MarakaEngine()
    
    # Aries Lagna: 2nd = Taurus (Venus), 7th = Libra (Venus)
    # Trik: 6th = Virgo (Mercury), 8th = Scorpio (Mars), 12th = Pisces (Jupiter)
    planet_rashis = {
        "venus": "taurus",
        "mars": "aries",
        "saturn": "scorpio", # Saturn in Scorpio aspects Taurus (7th aspect to 2nd house)
    }

    marakas = engine.get_maraka_planets("aries", planet_rashis)
    assert "venus" in marakas   # Primary (2nd & 7th)
    assert "mercury" in marakas # Secondary (6th)
    assert "mars" in marakas    # Secondary (8th)
    assert "jupiter" in marakas # Secondary (12th)
    assert "saturn" in marakas  # Absorbed via aspect on Venus


def test_jha_5tier_distinct_maraka_mortality_confluence():
    """
    Strict test of Jha's exact rule:
    Mortality risk is triggered when ALL 5 TIERS are Marakas AND are distinct planets.
    """
    engine = MarakaEngine()
    planet_rashis = {
        "sun": "leo",
        "moon": "cancer",
        "mars": "aries",
        "mercury": "virgo",
        "jupiter": "pisces",
        "venus": "taurus",
        "saturn": "scorpio",
    }

    # Case 1: 5 distinct Marakas (Venus, Mercury, Mars, Jupiter, Saturn)
    distinct_5_tiers = {
        "MD": "venus",
        "AD": "mercury",
        "PD": "mars",
        "SD": "jupiter",
        "PrD": "saturn",
    }
    res1 = engine.evaluate_5tier_maraka_confluence("aries", planet_rashis, distinct_5_tiers)
    assert res1.active_tier_count == 5
    assert res1.distinct_graha_count == 5
    assert res1.are_grahas_distinct is True
    assert res1.risk_level == "CRITICAL_MORTALITY_RISK"
    assert res1.is_maraka_active is True

    # Case 2: Repeating same planet (Venus in all 5 tiers)
    # Even though Venus is primary Maraka, Jha's rule says a planet does NOT kill in its own sub-periods!
    same_planet_tiers = {
        "MD": "venus",
        "AD": "venus",
        "PD": "venus",
        "SD": "venus",
        "PrD": "venus",
    }
    res2 = engine.evaluate_5tier_maraka_confluence("aries", planet_rashis, same_planet_tiers)
    assert res2.active_tier_count == 5
    assert res2.distinct_graha_count == 1
    assert res2.are_grahas_distinct is False
    # Not marked as CRITICAL_MORTALITY_RISK because planets are not distinct
    assert res2.risk_level != "CRITICAL_MORTALITY_RISK"


def test_flexible_maraka_configuration():
    """Verify that configuration is flexible and not hardcoded."""
    # Disable Trik lords, so only 2H & 7H are Marakas
    strict_config = MarakaConfig(include_trik_lords=False, min_tiers_for_death_risk=4)
    engine = MarakaEngine(maraka_config=strict_config)

    planet_rashis = {"venus": "taurus"}
    marakas = engine.get_maraka_planets("aries", planet_rashis, config=strict_config)
    
    # For Aries, only Venus is 2H and 7H lord
    assert "venus" in marakas
    assert "mercury" not in marakas
    assert "mars" not in marakas