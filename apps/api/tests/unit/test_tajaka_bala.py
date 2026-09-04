"""
AstroOS - Unit Tests for Panchavargiya Bala (5-Fold Tajika Strength)
Source: Tajika Neelakanthi
"""

import pytest

from apps.api.services.tajaka_bala_engine import TajakaBalaEngine
from apps.api.services.tajaka_constants import (
    DEEP_DEBILITATION,
    DEEP_EXALTATION,
    HADDA_TABLE,
)


def test_hadda_table_completeness():
    """All 12 signs must have 5 hadda divisions summing to 30 degrees."""
    for sign_idx in range(12):
        assert sign_idx in HADDA_TABLE
        divisions = HADDA_TABLE[sign_idx]
        assert len(divisions) == 5
        assert divisions[-1][0] == 30.0
        # strictly increasing
        for i in range(len(divisions) - 1):
            assert divisions[i][0] < divisions[i + 1][0]


def test_hadda_lord_resolution():
    """Mesha 0-6 is Jupiter, 6-12 is Venus, 12-20 is Mercury, 20-25 is Mars, 25-30 is Saturn."""
    assert TajakaBalaEngine.get_hadda_lord(0, 3.0) == "jupiter"
    assert TajakaBalaEngine.get_hadda_lord(0, 8.0) == "venus"
    assert TajakaBalaEngine.get_hadda_lord(0, 15.0) == "mercury"
    assert TajakaBalaEngine.get_hadda_lord(0, 22.0) == "mars"
    assert TajakaBalaEngine.get_hadda_lord(0, 28.0) == "saturn"


def test_drekkana_lord_resolution():
    """Aries: 0-10 is Mars, 10-20 is Sun (Leo/5th), 20-30 is Jupiter (Sag/9th)."""
    assert TajakaBalaEngine.get_drekkana_lord(0, 5.0) == "mars"
    assert TajakaBalaEngine.get_drekkana_lord(0, 15.0) == "sun"
    assert TajakaBalaEngine.get_drekkana_lord(0, 25.0) == "jupiter"


def test_navamsha_lord_resolution():
    """Aries (Fire): Pada 0 is Aries (Mars), Pada 1 is Taurus (Venus), Pada 2 is Gemini (Mercury)."""
    assert TajakaBalaEngine.get_navamsha_lord(0, 1.0) == "mars"
    assert TajakaBalaEngine.get_navamsha_lord(0, 4.0) == "venus"
    assert TajakaBalaEngine.get_navamsha_lord(0, 7.0) == "mercury"


def test_uchcha_bala_at_deep_exaltation_and_debilitation():
    """Sun at Aries 10° gets full 20 pts Uchcha Bala; at Libra 10° gets 0 pts."""
    sun_uchcha = TajakaBalaEngine.calculate_planet_bala("sun", 10.0, "aries", 10.0)
    assert sun_uchcha.uchcha_bala == pytest.approx(20.0, abs=1e-4)

    sun_neecha = TajakaBalaEngine.calculate_planet_bala("sun", 190.0, "libra", 10.0)
    assert sun_neecha.uchcha_bala == pytest.approx(0.0, abs=1e-4)


def test_kshetra_bala_scoring():
    """Sun in Leo (own sign) gets 30 pts; in Aries (friendly) gets 22.5 pts."""
    sun_own = TajakaBalaEngine.calculate_planet_bala("sun", 130.0, "leo", 10.0)
    assert sun_own.kshetra_bala == 30.0

    sun_friend = TajakaBalaEngine.calculate_planet_bala("sun", 10.0, "aries", 10.0)
    assert sun_friend.kshetra_bala == 22.5


def test_panchavargiya_bala_total_and_visheshika_scale():
    """Total score is sum of 5 balas, Visheshika Bala is total / 4.0 (0-20 scale)."""
    bala = TajakaBalaEngine.calculate_planet_bala("jupiter", 95.0, "cancer", 5.0)
    expected_total = bala.kshetra_bala + bala.uchcha_bala + bala.hadda_bala + bala.drekkana_bala + bala.navamsha_bala
    assert bala.total_score == pytest.approx(expected_total, abs=1e-4)
    assert bala.visheshika_bala == pytest.approx(expected_total / 4.0, abs=1e-4)
    assert 0.0 <= bala.visheshika_bala <= 20.0
    assert bala.strength_category in ("POORNA", "MADHYA", "ALPA", "HEENA")
