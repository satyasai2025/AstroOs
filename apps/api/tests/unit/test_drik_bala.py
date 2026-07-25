"""
AstroOS — Drik Bala Unit Tests (Module 9 Phase 1)
"""

import pytest

from apps.api.domain.horoscope import AspectInfo
from apps.api.services.shadbala.drik_bala import DrikBalaCalculator


def _make_aspect(from_planet, to_planet, orb_degrees, aspect_type="conjunction"):
    return AspectInfo(
        from_planet=from_planet, to_planet=to_planet, aspect_type=aspect_type,
        orb_degrees=orb_degrees, is_applying=False,
    )


def test_benefic_aspect_adds_positive_contribution():
    calc = DrikBalaCalculator()
    aspects = [_make_aspect("jupiter", "sun", orb_degrees=0.0)]
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas > 0


def test_malefic_aspect_subtracts():
    calc = DrikBalaCalculator()
    aspects = [_make_aspect("saturn", "sun", orb_degrees=0.0)]
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas < 0


def test_exact_orb_gives_maximum_strength():
    calc = DrikBalaCalculator()
    aspects = [_make_aspect("jupiter", "sun", orb_degrees=0.0)]
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas == pytest.approx(15.0, abs=1e-4)


def test_orb_at_limit_gives_zero_strength():
    from apps.api.services.aspect_engine import ASPECT_ORB
    calc = DrikBalaCalculator()
    aspects = [_make_aspect("jupiter", "sun", orb_degrees=ASPECT_ORB)]
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-4)


def test_no_aspects_received_gives_zero():
    calc = DrikBalaCalculator()
    result = calc.calculate("sun", aspects=[])
    assert result.value_shashtiamsas == 0.0


def test_ignores_aspects_where_planet_is_the_source_not_target():
    """Only aspects RECEIVED (to_planet) count, not aspects this planet casts."""
    calc = DrikBalaCalculator()
    aspects = [_make_aspect("sun", "moon", orb_degrees=0.0)]  # sun is the source here
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas == 0.0


def test_multiple_aspects_sum():
    calc = DrikBalaCalculator()
    aspects = [
        _make_aspect("jupiter", "sun", orb_degrees=0.0),
        _make_aspect("venus", "sun", orb_degrees=0.0),
    ]
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas == pytest.approx(30.0, abs=1e-3)


def test_mixed_benefic_and_malefic_aspects_net_out():
    calc = DrikBalaCalculator()
    aspects = [
        _make_aspect("jupiter", "sun", orb_degrees=0.0),   # +15
        _make_aspect("saturn", "sun", orb_degrees=0.0),    # -15
    ]
    result = calc.calculate("sun", aspects)
    assert result.value_shashtiamsas == pytest.approx(0.0, abs=1e-3)


def test_rejects_rahu_ketu_as_target():
    calc = DrikBalaCalculator()
    with pytest.raises(ValueError):
        calc.calculate("rahu", aspects=[])


def test_calculate_all_returns_7_classical_grahas():
    calc = DrikBalaCalculator()
    results = calc.calculate_all(aspects=[])
    assert len(results) == 7
    assert {r.planet for r in results} == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"
    }


def test_trace_documents_each_aspect():
    calc = DrikBalaCalculator()
    aspects = [_make_aspect("jupiter", "sun", orb_degrees=2.0)]
    result = calc.calculate("sun", aspects)
    assert any("jupiter" in t for t in result.trace)
