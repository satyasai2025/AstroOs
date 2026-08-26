"""
AstroOS - Unit Tests for Dasa Kuta (10 Poruthams) Engine
"""

import pytest

from apps.api.services.dasa_kuta_engine import DasaKutaEngine


def test_dasa_kuta_all_10_poruthams_evaluated():
    """Verifies all 10 Poruthams are evaluated with scores and classical sources."""
    # Ashwini (Girl) vs Rohini (Boy)
    # Girl: Ashwini (Pada Rajju)
    # Boy: Rohini (Kanta Rajju) -> Different Rajjus -> Rajju Compatible!
    res = DasaKutaEngine.evaluate(
        girl_rashi="aries",
        girl_nakshatra="ashwini",
        boy_rashi="taurus",
        boy_nakshatra="rohini",
    )

    assert len(res.items) == 10
    names = [it.name for it in res.items]
    assert "Dina" in names
    assert "Gana" in names
    assert "Mahendra" in names
    assert "Stree Deergha" in names
    assert "Yoni" in names
    assert "Rashi" in names
    assert "Rashi Adhipati" in names
    assert "Vashya" in names
    assert "Rajju" in names
    assert "Vedha" in names

    assert res.is_rajju_compatible is True
    assert res.total_score > 0.0


def test_rajju_dosha_detection_same_rajju():
    """Same Rajju zone (e.g. Rohini & Ardra both in Kanta Rajju) triggers Rajju affliction."""
    res = DasaKutaEngine.evaluate(
        girl_rashi="taurus",
        girl_nakshatra="rohini",
        boy_rashi="gemini",
        boy_nakshatra="ardra",
    )
    assert res.is_rajju_compatible is False
    assert "Rajju Dosha present" in res.verdict


def test_vedha_dosha_detection_repellent_pair():
    """Ashwini and Jyeshtha are classical Vedha repellent pair."""
    res = DasaKutaEngine.evaluate(
        girl_rashi="aries",
        girl_nakshatra="ashwini",
        boy_rashi="scorpio",
        boy_nakshatra="jyeshtha",
    )
    assert res.is_vedha_compatible is False
    vedha_item = next(it for it in res.items if it.name == "Vedha")
    assert vedha_item.is_compatible is False
