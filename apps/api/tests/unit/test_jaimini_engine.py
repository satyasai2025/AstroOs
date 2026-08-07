"""
AstroOS — Chara Karaka Engine Unit Tests
"""

import pytest

from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet

_SAPTA_PLANETS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")


def _distinct_degree_chart():
    """No two planets share a karaka_degree — the plain-ranking case."""
    degrees = {
        "sun": 25.0, "moon": 10.0, "mars": 5.0, "mercury": 20.0,
        "jupiter": 15.0, "venus": 8.0, "saturn": 3.0,
    }
    planets = [make_planet(p, "aries", d) for p, d in degrees.items()]
    planets.append(make_planet("rahu", "aries", 12.0))
    planets.append(make_planet("ketu", "aries", 12.0))
    return make_d1_chart("aries", planets)


def test_sapta_karaka_scheme_has_7_karakas_no_nodes():
    chart = _distinct_degree_chart()
    result = CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
    assert len(result.karakas) == 7
    assert {k.planet for k in result.karakas} == set(_SAPTA_PLANETS)
    assert "rahu" not in {k.planet for k in result.karakas}
    assert "ketu" not in {k.planet for k in result.karakas}


def test_ashta_karaka_scheme_has_8_karakas_includes_rahu_not_ketu():
    chart = _distinct_degree_chart()
    result = CharaKarakaEngine().compute(chart, scheme="ashta_karaka")
    assert len(result.karakas) == 8
    planets = {k.planet for k in result.karakas}
    assert planets == set(_SAPTA_PLANETS) | {"rahu"}
    assert "ketu" not in planets


def test_ranking_is_descending_by_karaka_degree():
    chart = _distinct_degree_chart()
    result = CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
    degrees = [k.karaka_degree for k in result.karakas]
    assert degrees == sorted(degrees, reverse=True)
    assert result.atmakaraka.planet == "sun"  # highest degree (25.0)
    assert result.darakaraka.planet == "saturn"  # lowest degree (3.0)


def test_rahu_karaka_degree_is_reversed():
    """Rahu at 12.0 rashi_degree -> karaka_degree must be 30 - 12 = 18.0."""
    chart = _distinct_degree_chart()
    result = CharaKarakaEngine().compute(chart, scheme="ashta_karaka")
    rahu = next(k for k in result.karakas if k.planet == "rahu")
    assert rahu.rashi_degree == 12.0
    assert rahu.karaka_degree == 18.0


def test_tie_broken_by_speed():
    """Sun and Mars tied at exactly 15.0 degrees; Sun faster -> Sun ranks higher."""
    planets = [
        make_planet("sun", "aries", 15.0, speed_deg_per_day=1.0),
        make_planet("mars", "aries", 15.0, speed_deg_per_day=0.5),
        make_planet("moon", "cancer", 10.0, speed_deg_per_day=13.0),
        make_planet("mercury", "gemini", 20.0, speed_deg_per_day=1.2),
        make_planet("jupiter", "leo", 5.0, speed_deg_per_day=0.2),
        make_planet("venus", "libra", 8.0, speed_deg_per_day=1.1),
        make_planet("saturn", "capricorn", 2.0, speed_deg_per_day=0.05),
    ]
    chart = make_d1_chart("aries", planets)
    result = CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
    sun_rank = next(k.rank for k in result.karakas if k.planet == "sun")
    mars_rank = next(k.rank for k in result.karakas if k.planet == "mars")
    assert sun_rank < mars_rank
    sun_karaka = next(k for k in result.karakas if k.planet == "sun")
    assert sun_karaka.tiebreak_rule == "speed"


def test_tie_broken_by_natural_benefic_when_speed_also_ties():
    """Venus and Mercury tied at exactly 20.0 degrees AND identical speed;
    Jupiter > Venus > Mercury hierarchy -> Venus ranks higher."""
    planets = [
        make_planet("mercury", "gemini", 20.0, speed_deg_per_day=1.2),
        make_planet("venus", "gemini", 20.0, speed_deg_per_day=1.2),
        make_planet("sun", "aries", 15.0, speed_deg_per_day=1.0),
        make_planet("moon", "cancer", 10.0, speed_deg_per_day=13.0),
        make_planet("jupiter", "leo", 5.0, speed_deg_per_day=0.2),
        make_planet("mars", "scorpio", 8.0, speed_deg_per_day=0.7),
        make_planet("saturn", "capricorn", 2.0, speed_deg_per_day=0.05),
    ]
    chart = make_d1_chart("aries", planets)
    result = CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
    venus_rank = next(k.rank for k in result.karakas if k.planet == "venus")
    mercury_rank = next(k.rank for k in result.karakas if k.planet == "mercury")
    assert venus_rank < mercury_rank
    venus_karaka = next(k for k in result.karakas if k.planet == "venus")
    assert venus_karaka.tiebreak_rule == "natural_benefic"


def test_missing_required_planet_raises():
    chart = make_d1_chart("aries", [make_planet("sun", "aries", 10.0)])  # only 1 of 7 required
    with pytest.raises(ValueError):
        CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
