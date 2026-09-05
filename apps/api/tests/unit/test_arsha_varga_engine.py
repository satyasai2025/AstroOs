"""
Unit tests for Arsha Parashari vs Popular Varga Calculation Modes.

Tests Vinay Jha's Kundalee software switch @10944:
- POPULAR: Modern standard (JHora default, forward progression in even signs).
- ARSHA_PARASHARI: Original Sanskrit BPHS (reverse progression in even signs for D2, D7, D9, D10, D16, D20, D24, D27, D30, D60).
"""

import pytest
from packages.shared.enums import VargaMethod
from apps.api.services.divisional_engine import compute_varga_sign


def test_odd_sign_invariance():
    """Odd signs (e.g. Aries, Gemini, Leo) must yield IDENTICAL results in both modes."""
    # Planet at Aries 10° (Odd sign)
    lon_aries = 10.0
    for varga in ["D2", "D3", "D7", "D9", "D10", "D16", "D20", "D24", "D27", "D30", "D60"]:
        r_pop, d_pop = compute_varga_sign(varga, lon_aries, varga_method=VargaMethod.POPULAR)
        r_arsha, d_arsha = compute_varga_sign(varga, lon_aries, varga_method=VargaMethod.ARSHA_PARASHARI)
        assert r_pop == r_arsha, f"{varga} mismatch on odd sign: {r_pop} vs {r_arsha}"
        assert abs(d_pop - d_arsha) < 1e-4


def test_even_sign_d7_saptamsha():
    """D7 on even sign (e.g. Taurus = index 1)."""
    # Taurus 2nd part (part index 1, ~6° in Taurus -> lon = 36.0)
    lon = 36.0
    # Popular: start from 7th (Scorpio=7), forward -> 7 + 1 = Sagittarius (8)
    r_pop, _ = compute_varga_sign("D7", lon, varga_method=VargaMethod.POPULAR)
    assert r_pop == "sagittarius"
    
    # Arsha: start from 7th (Scorpio=7), backward -> 7 - 1 = Libra (6)
    r_arsha, _ = compute_varga_sign("D7", lon, varga_method=VargaMethod.ARSHA_PARASHARI)
    assert r_arsha == "libra"


def test_even_sign_d10_dashamsha():
    """D10 on even sign (e.g. Taurus = index 1)."""
    # Taurus 2nd part (part index 1, 4.5° in Taurus -> lon = 34.5)
    lon = 34.5
    # Popular: start from 9th (Capricorn=9), forward -> 9 + 1 = Aquarius (10)
    r_pop, _ = compute_varga_sign("D10", lon, varga_method=VargaMethod.POPULAR)
    assert r_pop == "aquarius"
    
    # Arsha: start from 9th (Capricorn=9), backward -> 9 - 1 = Sagittarius (8)
    r_arsha, _ = compute_varga_sign("D10", lon, varga_method=VargaMethod.ARSHA_PARASHARI)
    assert r_arsha == "sagittarius"


def test_even_sign_d24_chaturvimshamsha():
    """D24 on even sign (e.g. Taurus = index 1)."""
    # Taurus 2nd part (part index 1, 2° in Taurus -> lon = 32.0)
    lon = 32.0
    # Popular: start from Cancer (3), forward -> 3 + 1 = Leo (4)
    r_pop, _ = compute_varga_sign("D24", lon, varga_method=VargaMethod.POPULAR)
    assert r_pop == "leo"
    
    # Arsha: start from Cancer (3), backward -> 3 - 1 = Gemini (2)
    r_arsha, _ = compute_varga_sign("D24", lon, varga_method=VargaMethod.ARSHA_PARASHARI)
    assert r_arsha == "gemini"


def test_d30_trimshamsha_both_modes():
    """D30 has reverse order in even signs in BOTH popular and Arsha modes."""
    # Taurus 2° (0-5° in even sign -> Venus -> Taurus)
    lon_tau_2 = 32.0
    r_pop, _ = compute_varga_sign("D30", lon_tau_2, varga_method=VargaMethod.POPULAR)
    r_arsha, _ = compute_varga_sign("D30", lon_tau_2, varga_method=VargaMethod.ARSHA_PARASHARI)
    assert r_pop == "taurus"
    assert r_arsha == "taurus"
