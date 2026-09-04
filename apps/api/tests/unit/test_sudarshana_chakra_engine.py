"""
Unit tests for Sudarshana Chakra (SC) Engine implementing Vinay Jha's exact rules.
"""

import pytest
from apps.api.services.sudarshana_chakra_engine import SudarshanaChakraEngine


def test_sudarshana_chakra_tri_lagna_active():
    engine = SudarshanaChakraEngine()
    # Lagna = Taurus (35°), Sun = Gemini (75°), Moon = Virgo (165°)
    # Sun and Moon are in H2 and H5 (not in Lagna) -> Tri-Lagna should be ACTIVE
    rep = engine.analyze(
        lagna_deg=35.0,
        sun_deg=75.0,
        moon_deg=165.0,
    )

    assert rep.is_tri_lagna_active is True
    assert rep.lagna_rashi.lower() == "taurus"
    assert rep.sun_rashi.lower() == "gemini"
    assert rep.moon_rashi.lower() == "virgo"

    # Saturn in Taurus Lagna rules H9 (Capricorn) & H10 (Aquarius) -> Trikona lord in LK (+1)
    sat_prof = rep.profiles["Saturn"]
    assert 9 in sat_prof.lk_houses_owned or 10 in sat_prof.lk_houses_owned
    assert sat_prof.lk_functional_score >= 1  # Benefic in LK


def test_sudarshana_chakra_sun_in_lagna_branch():
    engine = SudarshanaChakraEngine()
    # Sun in Lagna: Lagna = Leo (130°), Sun = Leo (135°), Moon = Libra (190°)
    rep = engine.analyze(
        lagna_deg=130.0,
        sun_deg=135.0,
        moon_deg=190.0,
    )

    # Jha Rule: If Sun is in Lagna, ONLY Lagna Chakra (LK) is used (SK and CK are NOT added)
    assert rep.sun_in_lagna is True
    assert rep.is_tri_lagna_active is False

    # For all planets, net_score must equal lk_score exactly, with SK and CK scores as 0
    for prof in rep.profiles.values():
        assert prof.sk_functional_score == 0
        assert prof.ck_functional_score == 0
        assert prof.net_functional_score == prof.lk_functional_score
