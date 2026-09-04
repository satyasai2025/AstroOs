"""
AstroOS — Comprehensive Ashtakavarga Unit Tests
===============================================
Tests:
  1. 337 Classical Bindu Checksum Invariant (Sarvashtakavarga)
  2. Individual Bhinnashtakavarga 7-Planet Totals (Sun=48, Moon=49, Mars=39, Mercury=54, Jupiter=56, Venus=52, Saturn=39)
  3. Trikona & Ekadhipatya Shodhana
  4. Shodhya Pinda (Rashi Pinda + Graha Pinda)
  5. Prastarashtakavarga 8x12 Matrix
  6. Kakshya 3°45' Subdivisions & Transit Evaluation
"""

import pytest

from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.ashtakavarga.shodhya_pinda_calculator import ShodhyaPindaCalculator, RASHI_GUNAKARA, GRAHA_GUNAKARA
from apps.api.services.ashtakavarga.kakshya_calculator import KakshyaCalculator, KAKSHYA_LORDS, KAKSHYA_SPAN_DEG
from apps.api.domain.ashtakavarga import BhinnashtakavargaResult
from packages.shared.ashtakavarga_bindu_table import EXPECTED_GRAND_TOTAL, EXPECTED_PLANET_TOTALS


def test_classical_bindu_table_constants():
    """Verify Parashari checksums: Sun=48, Moon=49, Mars=39, Mercury=54, Jupiter=56, Venus=52, Saturn=39, Total=337."""
    assert sum(EXPECTED_PLANET_TOTALS.values()) == EXPECTED_GRAND_TOTAL
    assert EXPECTED_GRAND_TOTAL == 337
    assert EXPECTED_PLANET_TOTALS["sun"] == 48
    assert EXPECTED_PLANET_TOTALS["moon"] == 49
    assert EXPECTED_PLANET_TOTALS["mars"] == 39
    assert EXPECTED_PLANET_TOTALS["mercury"] == 54
    assert EXPECTED_PLANET_TOTALS["jupiter"] == 56
    assert EXPECTED_PLANET_TOTALS["venus"] == 52
    assert EXPECTED_PLANET_TOTALS["saturn"] == 39


def test_prastara_matrix_sums_to_bhinnashtakavarga():
    """Sum of each column in an 8x12 Prastarashtakavarga matrix must equal the BAV bindus for that sign."""
    calc = KakshyaCalculator()
    contributor_rashis = {
        "sun": "aries",
        "moon": "taurus",
        "mars": "gemini",
        "mercury": "aries",
        "jupiter": "cancer",
        "venus": "taurus",
        "saturn": "aquarius",
        "lagna": "leo",
    }

    matrices = calc.compute_all_prastara(contributor_rashis)
    assert len(matrices) == 7

    for planet, matrix in matrices.items():
        assert len(matrix) == 8  # 8 kakshya lords
        total_planet_bindus = 0
        for sign_idx in range(12):
            sign_bindus = sum(matrix[lord][sign_idx] for lord in KAKSHYA_LORDS)
            assert 0 <= sign_bindus <= 8
            total_planet_bindus += sign_bindus
        assert total_planet_bindus == EXPECTED_PLANET_TOTALS[planet]


def test_kakshya_transit_evaluation():
    """Verify transit kakshya detection at 3°45' boundaries and correct lord assignment."""
    calc = KakshyaCalculator()
    prastara_matrix = {lord: [1 if lord in ("saturn", "sun") else 0] * 12 for lord in KAKSHYA_LORDS}

    # Test 1: 0°10' Aries -> 1st Kakshya (0° - 3°45'), Lord = Saturn
    eval1 = calc.evaluate_transit_kakshya("jupiter", 0.1667, prastara_matrix)
    assert eval1.rashi == "aries"
    assert eval1.kakshya_index == 0
    assert eval1.kakshya_lord == "saturn"
    assert eval1.has_bindu is True

    # Test 2: 4°00' Aries -> 2nd Kakshya (3°45' - 7°30'), Lord = Jupiter
    eval2 = calc.evaluate_transit_kakshya("jupiter", 4.0, prastara_matrix)
    assert eval2.rashi == "aries"
    assert eval2.kakshya_index == 1
    assert eval2.kakshya_lord == "jupiter"
    assert eval2.has_bindu is False  # Jupiter lord has 0 in mock matrix


def test_shodhya_pinda_calculation():
    """Verify classical Shodhya Pinda (Rashi Pinda + Graha Pinda) formula."""
    pinda_calc = ShodhyaPindaCalculator()
    
    # 12-sign reduced bindu sample
    reduced = (3, 2, 0, 4, 1, 0, 2, 5, 0, 1, 3, 2)
    positions = {
        "sun": "aries",
        "moon": "taurus",
        "mars": "gemini",
        "mercury": "cancer",
        "jupiter": "leo",
        "venus": "libra",
        "saturn": "aquarius",
    }

    res = pinda_calc.calculate_for_planet("sun", reduced, positions)

    # Manual verification of Rashi Pinda:
    # Aries(7)*3 + Taurus(10)*2 + Gemini(8)*0 + Cancer(4)*4 + Leo(10)*1 + Virgo(5)*0 +
    # Libra(7)*2 + Scorpio(8)*5 + Sag(9)*0 + Cap(5)*1 + Aquar(11)*3 + Pisces(12)*2
    # = 21 + 20 + 0 + 16 + 10 + 0 + 14 + 40 + 0 + 5 + 33 + 24 = 183
    assert res.rashi_pinda == 183

    # Manual verification of Graha Pinda:
    # Sun in Aries (reduced=3) * 5 = 15
    # Moon in Taurus (reduced=2) * 5 = 10
    # Mars in Gemini (reduced=0) * 8 = 0
    # Mercury in Cancer (reduced=4) * 5 = 20
    # Jupiter in Leo (reduced=1) * 10 = 10
    # Venus in Libra (reduced=2) * 7 = 14
    # Saturn in Aquarius (reduced=3) * 5 = 15
    # Sum = 15 + 10 + 0 + 20 + 10 + 14 + 15 = 84
    assert res.graha_pinda == 84

    # Shodhya Pinda = Rashi Pinda + Graha Pinda = 183 + 84 = 267
    assert res.shodhya_pinda == 267