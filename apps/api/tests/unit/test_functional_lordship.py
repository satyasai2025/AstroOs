"""
AstroOS — Unit tests for Functional Lordship and Yogakaraka Engine
"""

import pytest

from apps.api.services.functional_lordship_engine import FunctionalLordshipEngine


def test_functional_lordship_all_yogakarakas():
    engine = FunctionalLordshipEngine()

    # Taurus Lagna: Saturn is Yogakaraka (9L + 10L)
    taurus = engine.compute_by_lagna("taurus")
    assert taurus.planets["saturn"].is_yogakaraka is True
    assert taurus.planets["saturn"].lordship == "benefic"
    assert taurus.planets["jupiter"].lordship == "malefic"

    # Cancer Lagna: Mars is Yogakaraka (5L + 10L)
    cancer = engine.compute_by_lagna("cancer")
    assert cancer.planets["mars"].is_yogakaraka is True
    assert cancer.planets["mars"].lordship == "benefic"
    assert cancer.planets["moon"].lordship == "benefic"

    # Leo Lagna: Mars is Yogakaraka (4L + 9L)
    leo = engine.compute_by_lagna("leo")
    assert leo.planets["mars"].is_yogakaraka is True
    assert leo.planets["mars"].lordship == "benefic"

    # Libra Lagna: Saturn is Yogakaraka (4L + 5L)
    libra = engine.compute_by_lagna("libra")
    assert libra.planets["saturn"].is_yogakaraka is True
    assert libra.planets["saturn"].lordship == "benefic"

    # Capricorn Lagna: Venus is Yogakaraka (5L + 10L)
    capricorn = engine.compute_by_lagna("capricorn")
    assert capricorn.planets["venus"].is_yogakaraka is True
    assert capricorn.planets["venus"].lordship == "benefic"

    # Aquarius Lagna: Venus is Yogakaraka (4L + 9L)
    aquarius = engine.compute_by_lagna("aquarius")
    assert aquarius.planets["venus"].is_yogakaraka is True
    assert aquarius.planets["venus"].lordship == "benefic"


def test_functional_lordship_non_yogakaraka_lagnas():
    engine = FunctionalLordshipEngine()

    # Aries Lagna: Sun (5L) benefic, Mars (1L) benefic, Mercury (3L, 6L) malefic
    aries = engine.compute_by_lagna("aries")
    assert all(not p.is_yogakaraka for p in aries.planets.values())
    assert aries.planets["sun"].lordship == "benefic"
    assert aries.planets["mars"].lordship == "benefic"
    assert aries.planets["mercury"].lordship == "malefic"
    assert aries.planets["venus"].lordship == "malefic"


def test_functional_lordship_all_12_lagnas():
    engine = FunctionalLordshipEngine()
    lagnas = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    for lagna in lagnas:
        res = engine.compute_by_lagna(lagna)
        assert len(res.planets) == 7
        for planet, p_res in res.planets.items():
            assert p_res.lordship in ("benefic", "malefic", "neutral")
            assert isinstance(p_res.is_yogakaraka, bool)
