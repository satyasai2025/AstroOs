"""
AstroOS — Unit Tests for Sarvatobhadra Chakra (SBC) Engine
"""

import pytest
from apps.api.services.sarvatobhadra_chakra import (
    ABHIJIT_START_DEG,
    ABHIJIT_END_DEG,
    ABHIJIT_SPAN_DEG,
    SBC_28_NAKSHATRAS,
    longitude_to_28_nakshatra,
    get_sensitive_nakshatras_28,
    compute_vedha_from_square,
    SarvatobhadraChakraEngine,
)


def test_sbc_28_nakshatras_and_abhijit_span():
    """
    Verify Abhijit intercalation:
    - Exactly 28 Nakshatras.
    - Abhijit starts at 276°40' (276.6667°) and ends at 280°53'20" (280.8889°).
    - Abhijit span is 4°13'20" (4.2222° = 253.333 arcmin).
    - Total circle equals 360.0°.
    """
    assert len(SBC_28_NAKSHATRAS) == 28

    abhijit_entry = SBC_28_NAKSHATRAS[21]  # 22nd nakshatra (0-indexed 21)
    assert abhijit_entry[0] == 22
    assert abhijit_entry[1] == "Abhijit"
    assert abhijit_entry[2] == pytest.approx(ABHIJIT_START_DEG, abs=1e-5)
    assert abhijit_entry[3] == pytest.approx(ABHIJIT_END_DEG, abs=1e-5)

    span = abhijit_entry[3] - abhijit_entry[2]
    assert span == pytest.approx(ABHIJIT_SPAN_DEG, abs=1e-5)

    # Check total circle sum
    total_span = sum(entry[3] - entry[2] for entry in SBC_28_NAKSHATRAS)
    assert total_span == pytest.approx(360.0, abs=1e-5)


def test_longitude_mapping_to_abhijit():
    """Verify mapping of longitudes around Abhijit boundary."""
    # 270.0° -> Uttara Ashadha (21)
    u_ashadha = longitude_to_28_nakshatra(270.0)
    assert u_ashadha[0] == 21
    assert u_ashadha[1] == "Uttara Ashadha"

    # 278.0° -> Abhijit (22)
    abhijit = longitude_to_28_nakshatra(278.0)
    assert abhijit[0] == 22
    assert abhijit[1] == "Abhijit"

    # 285.0° -> Shravana (23)
    shravana = longitude_to_28_nakshatra(285.0)
    assert shravana[0] == 23
    assert shravana[1] == "Shravana"


def test_sbc_sensitive_natal_points():
    """
    Verify classical SBC sensitive points from Janma:
    Karma = 10th, Sanghatika = 16th, Samudayika = 18th, Adhana = 19th, Vainashika = 23rd.
    """
    pts_ashwini = get_sensitive_nakshatras_28(1)
    assert pts_ashwini["janma"] == 1
    assert pts_ashwini["karma"] == 10       # 1 + 9
    assert pts_ashwini["sanghatika"] == 16  # 1 + 15
    assert pts_ashwini["samudayika"] == 18  # 1 + 17
    assert pts_ashwini["adhana"] == 19      # 1 + 18
    assert pts_ashwini["vainashika"] == 23  # 1 + 22


def test_sbc_4_fold_vedha_rays():
    """Verify 4-fold Vedha calculation from a border square."""
    # Square (0, 4) = Ardra (Top border)
    # Agra (Direct opposite) -> must hit bottom border at (8, 4) = Purva Ashadha
    aspects = compute_vedha_from_square(0, 4)
    assert "agra" in aspects
    assert aspects["agra"] == (8, 4)
    assert "dakshina" in aspects
    assert "vama" in aspects


def test_sbc_transit_evaluation():
    """
    Verify transit evaluation:
    When natal Moon is at 0° (Ashwini), and transit Saturn is at 180° (opposite border),
    verify Vedha hits are detected.
    """
    engine = SarvatobhadraChakraEngine()
    natal_moon = 5.0  # Ashwini (1)

    transits = {
        "saturn": 180.0,   # Chitra (14)
        "jupiter": 85.0,   # Punarvasu (7)
    }

    res = engine.evaluate_transit_vedha(
        natal_moon_longitude=natal_moon,
        transit_graha_longitudes=transits,
    )

    assert res["natal_janma_nakshatra"]["name"] == "Ashwini"
    assert res["total_vedha_hits"] > 0
    assert "transit_positions" in res
    assert "saturn" in res["transit_positions"]
    assert "jupiter" in res["transit_positions"]