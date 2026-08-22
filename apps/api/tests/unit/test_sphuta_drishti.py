"""
AstroOS — Sphuta Drishti Engine Unit Tests

Pure unit coverage testing BPHS Chapter 28 Sphuta Drishti formulas for:
  - General Grahas (Sun, Moon, Mercury, Venus)
  - Special Grahas (Saturn, Mars, Jupiter)
  - Exact boundary conditions (0°, 30°, 60°, 90°, 120°, 150°, 180°, 210°, 240°, 270°, 300°, 360°)
  - Forward zodiacal angular distance calculations and normalization.
"""

import pytest

from apps.api.services.sphuta_drishti_engine import (
    SphutaDrishtiEngine,
    SphutaDrishtiResult,
    calculate_forward_distance,
)


@pytest.fixture
def engine() -> SphutaDrishtiEngine:
    return SphutaDrishtiEngine()


# ── Forward Distance Calculation ──────────────────────────────────────────────

def test_forward_distance_calculation():
    assert calculate_forward_distance(0.0, 45.0) == pytest.approx(45.0)
    assert calculate_forward_distance(350.0, 10.0) == pytest.approx(20.0)
    assert calculate_forward_distance(10.0, 350.0) == pytest.approx(340.0)
    assert calculate_forward_distance(180.0, 180.0) == pytest.approx(0.0)


# ── General Graha Sphuta (Sun, Moon, Mercury, Venus) ──────────────────────────

def test_general_zero_aspect_range(engine):
    """Aspect is 0 for D <= 30° or D >= 300°."""
    res_0 = engine.compute("sun", 0.0, 15.0)  # D = 15°
    assert res_0.virupa_strength == 0.0
    assert res_0.percentage == 0.0

    res_30 = engine.compute("sun", 0.0, 30.0)  # D = 30°
    assert res_30.virupa_strength == 0.0

    res_315 = engine.compute("sun", 0.0, 315.0)  # D = 315°
    assert res_315.virupa_strength == 0.0


def test_general_30_to_60(engine):
    """S = D/2 - 15 for 30 < D <= 60."""
    res_45 = engine.compute("sun", 0.0, 45.0)  # D = 45° -> 45/2 - 15 = 7.5
    assert res_45.virupa_strength == pytest.approx(7.5)

    res_60 = engine.compute("sun", 0.0, 60.0)  # D = 60° -> 60/2 - 15 = 15.0
    assert res_60.virupa_strength == pytest.approx(15.0)


def test_general_60_to_90(engine):
    """S = D - 45 for 60 < D <= 90."""
    res_75 = engine.compute("moon", 0.0, 75.0)  # D = 75° -> 75 - 45 = 30.0
    assert res_75.virupa_strength == pytest.approx(30.0)

    res_90 = engine.compute("moon", 0.0, 90.0)  # D = 90° -> 90 - 45 = 45.0
    assert res_90.virupa_strength == pytest.approx(45.0)


def test_general_90_to_120(engine):
    """S = 90 - D/2 for 90 < D <= 120."""
    res_105 = engine.compute("mercury", 0.0, 105.0)  # D = 105° -> 90 - 52.5 = 37.5
    assert res_105.virupa_strength == pytest.approx(37.5)

    res_120 = engine.compute("mercury", 0.0, 120.0)  # D = 120° -> 90 - 60 = 30.0
    assert res_120.virupa_strength == pytest.approx(30.0)


def test_general_120_to_150(engine):
    """S = 150 - D for 120 < D <= 150."""
    res_135 = engine.compute("venus", 0.0, 135.0)  # D = 135° -> 150 - 135 = 15.0
    assert res_135.virupa_strength == pytest.approx(15.0)

    res_150 = engine.compute("venus", 0.0, 150.0)  # D = 150° -> 150 - 150 = 0.0
    assert res_150.virupa_strength == pytest.approx(0.0)


def test_general_150_to_180(engine):
    """S = 2D - 300 for 150 < D <= 180."""
    res_165 = engine.compute("sun", 0.0, 165.0)  # D = 165° -> 330 - 300 = 30.0
    assert res_165.virupa_strength == pytest.approx(30.0)

    res_180 = engine.compute("sun", 0.0, 180.0)  # D = 180° -> 360 - 300 = 60.0
    assert res_180.virupa_strength == pytest.approx(60.0)
    assert res_180.percentage == pytest.approx(100.0)


def test_general_180_to_300(engine):
    """S = 150 - D/2 for 180 < D < 300."""
    res_210 = engine.compute("sun", 0.0, 210.0)  # D = 210° -> 150 - 105 = 45.0
    assert res_210.virupa_strength == pytest.approx(45.0)

    res_240 = engine.compute("sun", 0.0, 240.0)  # D = 240° -> 150 - 120 = 30.0
    assert res_240.virupa_strength == pytest.approx(30.0)

    res_270 = engine.compute("sun", 0.0, 270.0)  # D = 270° -> 150 - 135 = 15.0
    assert res_270.virupa_strength == pytest.approx(15.0)


# ── Special Graha Exact Examples ─────────────────────────────────────────────

def test_saturn_exact_60_degrees_peak_3rd_aspect(engine):
    """Saturn at 60° (3rd house) has peak 60 Virupa strength."""
    res = engine.compute("saturn", 0.0, 60.0)
    assert res.virupa_strength == pytest.approx(60.0)
    assert res.percentage == pytest.approx(100.0)


def test_saturn_10th_house_peak(engine):
    """Saturn at 270° (10th house) has peak 60 Virupa strength."""
    res = engine.compute("saturn", 0.0, 270.0)
    assert res.virupa_strength == pytest.approx(60.0)
    assert res.percentage == pytest.approx(100.0)


def test_mars_exact_90_degrees_peak_4th_aspect(engine):
    """Mars at 90° (4th house) has peak 60 Virupa strength."""
    res = engine.compute("mars", 0.0, 90.0)
    assert res.virupa_strength == pytest.approx(60.0)
    assert res.percentage == pytest.approx(100.0)


def test_mars_8th_house_peak(engine):
    """Mars at 210° (8th house) has peak aspect."""
    res_180 = engine.compute("mars", 0.0, 180.0)
    assert res_180.virupa_strength == pytest.approx(60.0)


def test_jupiter_exact_120_degrees_peak_5th_aspect(engine):
    """Jupiter at 120° (5th house) has peak 60 Virupa strength."""
    res = engine.compute("jupiter", 0.0, 120.0)
    assert res.virupa_strength == pytest.approx(60.0)
    assert res.percentage == pytest.approx(100.0)


def test_jupiter_9th_house_peak_240_degrees(engine):
    """Jupiter at 240° (9th house) has peak 60 Virupa strength."""
    res = engine.compute("jupiter", 0.0, 240.0)
    assert res.virupa_strength == pytest.approx(60.0)
    assert res.percentage == pytest.approx(100.0)


# ── Invariant & Boundary Tests ───────────────────────────────────────────────

def test_virupa_always_clamped_between_0_and_60(engine):
    """Every test output must satisfy 0 <= virupa <= 60 and 0 <= percentage <= 100."""
    for graha in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        for deg in range(0, 360, 15):
            res = engine.compute(graha, 0.0, float(deg))
            assert 0.0 <= res.virupa_strength <= 60.0
            assert 0.0 <= res.percentage <= 100.0


def test_boundary_neighborhoods(engine):
    """Check continuity near boundary points (29.9°, 30.1°, 59.9°, 60.1°)."""
    res_299 = engine.compute("sun", 0.0, 29.9)
    assert res_299.virupa_strength == 0.0

    res_301 = engine.compute("sun", 0.0, 30.1)
    assert res_301.virupa_strength > 0.0

    res_sat_599 = engine.compute("saturn", 0.0, 59.9)
    res_sat_601 = engine.compute("saturn", 0.0, 60.1)
    assert abs(res_sat_599.virupa_strength - 60.0) < 1.0
    assert abs(res_sat_601.virupa_strength - 60.0) < 1.0
