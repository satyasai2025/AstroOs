"""
AstroOS — Jaimini Rashi Aspect Engine Unit Tests
"""

from apps.api.services.rashi_aspect_engine import RashiAspectEngine
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet


def test_chara_sign_aspects_3_of_4_sthira_signs_excluding_adjacent():
    matrix = RashiAspectEngine().compute_matrix()
    assert set(matrix["aries"]) == {"leo", "scorpio", "aquarius"}  # not taurus (adjacent)


def test_sthira_sign_aspects_3_of_4_chara_signs_excluding_adjacent():
    matrix = RashiAspectEngine().compute_matrix()
    assert set(matrix["taurus"]) == {"cancer", "libra", "capricorn"}  # not aries (adjacent)


def test_dvisvabhava_signs_aspect_each_other_with_no_exception():
    matrix = RashiAspectEngine().compute_matrix()
    assert set(matrix["gemini"]) == {"virgo", "sagittarius", "pisces"}


def test_aspect_relation_is_symmetric_for_chara_sthira_pairs():
    matrix = RashiAspectEngine().compute_matrix()
    for chara in ("aries", "cancer", "libra", "capricorn"):
        for sthira in matrix[chara]:
            assert chara in matrix[sthira], f"{chara} aspects {sthira} but not vice versa"


def test_every_sign_has_exactly_3_aspect_targets():
    matrix = RashiAspectEngine().compute_matrix()
    assert len(matrix) == 12
    for rashi, targets in matrix.items():
        assert len(targets) == 3, f"{rashi} has {len(targets)} targets, expected 3"


def test_compute_only_returns_aspects_from_occupied_signs():
    chart = make_d1_chart("aries", [make_planet("mars", "aries", 10.0)])
    result = RashiAspectEngine().compute(chart)
    # Aries is occupied (mars) -> 3 real aspects cast from it.
    assert len(result.aspects) == 3
    assert all(a.from_rashi == "aries" for a in result.aspects)
    assert all(a.aspecting_planets == ("mars",) for a in result.aspects)


def test_aspected_planets_reflects_real_occupancy():
    chart = make_d1_chart(
        "aries", [make_planet("mars", "aries", 10.0), make_planet("sun", "leo", 5.0)]
    )
    result = RashiAspectEngine().compute(chart)
    leo_aspect = next(a for a in result.aspects if a.to_rashi == "leo")
    assert leo_aspect.aspected_planets == ("sun",)
    scorpio_aspect = next(a for a in result.aspects if a.to_rashi == "scorpio")
    assert scorpio_aspect.aspected_planets == ()  # unoccupied


def test_does_aspect_and_aspects_on_helpers():
    chart = make_d1_chart("aries", [make_planet("mars", "aries", 10.0)])
    result = RashiAspectEngine().compute(chart)
    assert result.does_aspect("aries", "leo") is True
    assert result.does_aspect("aries", "taurus") is False
    assert len(result.aspects_on("leo")) == 1
