"""
Unit tests for BhavachalitaEngine and BHAVA-SANDHI-RULES-v0.1
"""

import pytest
from apps.api.services.bhavachalita_engine import BhavachalitaEngine


def test_bhava_sandhi_frozen_rules():
    # Ascendant at 29.79° (Sandhi high)
    report_high = BhavachalitaEngine.analyze_chart(
        ascendant_lon=59.79,  # 29.79° Taurus
        planet_longitudes={"saturn": 37.86},  # 7.86° Taurus
    )
    assert report_high.is_bhava_sandhi is True
    assert report_high.placements["saturn"].whole_sign_house == 1
    # 7.86° Taurus is more than 15° behind 29.79° Taurus -> falls into 12th house Bhava Madhya!
    assert report_high.placements["saturn"].bhavachalita_house == 12
    assert report_high.placements["saturn"].is_displaced is True

    # Ascendant at 1.50° (Sandhi low)
    report_low = BhavachalitaEngine.analyze_chart(
        ascendant_lon=1.50,  # 1.50° Aries
        planet_longitudes={"sun": 25.0},  # 25.0° Aries
    )
    assert report_low.is_bhava_sandhi is True
    assert report_low.placements["sun"].whole_sign_house == 1
    # 25.0° Aries is more than 15° ahead of 1.50° Aries -> falls into 2nd house Bhava Madhya!
    assert report_low.placements["sun"].bhavachalita_house == 2
    assert report_low.placements["sun"].is_displaced is True

    # Ascendant at 15.0° (Mid-rashi, non-sandhi)
    report_mid = BhavachalitaEngine.analyze_chart(
        ascendant_lon=15.0,  # 15.0° Aries
        planet_longitudes={"sun": 16.0},  # 16.0° Aries
    )
    assert report_mid.is_bhava_sandhi is False
    assert report_mid.placements["sun"].whole_sign_house == 1
    assert report_mid.placements["sun"].bhavachalita_house == 1
    assert report_mid.placements["sun"].is_displaced is False


def test_d10_dignity_calculation():
    # Sun in Gemini 14.10° (Lon = 74.10°) -> D10 index = (2 + 4 + 4) % 12 = 6 (Libra) -> DEBILITATED
    d10_sun_idx = BhavachalitaEngine.compute_d10_rashi_index(74.10)
    assert d10_sun_idx == 6  # Libra
    assert BhavachalitaEngine.evaluate_d10_dignity("sun", d10_sun_idx) == "DEBILITATED"

    # Saturn in Libra (Lon = 190.0°) -> D10 idx for Libra 10.0°: sign 6 (even) -> 6 + 8 + 3 = 17 % 12 = 5 (Virgo)
    assert BhavachalitaEngine.evaluate_d10_dignity("saturn", 6) == "EXALTED"
    assert BhavachalitaEngine.evaluate_d10_dignity("saturn", 0) == "DEBILITATED"
    assert BhavachalitaEngine.evaluate_d10_dignity("saturn", 9) == "OWN"
