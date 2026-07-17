"""
AstroOS — Bhinnashtakavarga Calculator Unit Tests (Module 10)
"""

import pytest

from apps.api.services.ashtakavarga.bhinnashtakavarga_calculator import BhinnashtakavargaCalculator

_CONTRIBUTORS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "lagna"]


def _all_in(rashi: str) -> dict[str, str]:
    return {c: rashi for c in _CONTRIBUTORS}


@pytest.mark.parametrize("planet,expected_total", [
    ("sun", 48), ("moon", 49), ("mars", 39), ("mercury", 54),
    ("jupiter", 56), ("venus", 52), ("saturn", 39),
])
def test_total_bindus_invariant_regardless_of_rashi_positions(planet, expected_total):
    calc = BhinnashtakavargaCalculator()
    result_a = calc.calculate(planet, _all_in("aries"))
    result_b = calc.calculate(planet, _all_in("scorpio"))
    assert result_a.total_bindus == expected_total
    assert result_b.total_bindus == expected_total


def test_distribution_differs_when_rashi_positions_differ():
    calc = BhinnashtakavargaCalculator()
    result_a = calc.calculate("sun", _all_in("aries"))
    result_b = calc.calculate("sun", _all_in("scorpio"))
    assert result_a.bindus_by_rashi != result_b.bindus_by_rashi


def test_bindus_by_rashi_sums_to_total():
    calc = BhinnashtakavargaCalculator()
    contributors = {
        "sun": "aries", "moon": "taurus", "mars": "gemini", "mercury": "cancer",
        "jupiter": "leo", "venus": "virgo", "saturn": "libra", "lagna": "scorpio",
    }
    result = calc.calculate("jupiter", contributors)
    assert sum(result.bindus_by_rashi) == result.total_bindus


def test_bindus_in_rashi_matches_tuple_index():
    calc = BhinnashtakavargaCalculator()
    result = calc.calculate("sun", _all_in("aries"))
    assert result.bindus_in_rashi("aries") == result.bindus_by_rashi[0]
    assert result.bindus_in_rashi("pisces") == result.bindus_by_rashi[11]


def test_bindus_from_lagna_house_1_equals_lagna_rashi():
    calc = BhinnashtakavargaCalculator()
    contributors = _all_in("aries")
    contributors["lagna"] = "cancer"
    result = calc.calculate("sun", contributors)
    assert result.bindus_from_lagna("cancer", 1) == result.bindus_in_rashi("cancer")


def test_bindus_from_lagna_wraps_cyclically():
    calc = BhinnashtakavargaCalculator()
    result = calc.calculate("sun", _all_in("aries"))
    assert result.bindus_from_lagna("taurus", 10) == result.bindus_in_rashi("aquarius")


def test_rejects_rahu_ketu_as_target():
    calc = BhinnashtakavargaCalculator()
    with pytest.raises(ValueError):
        calc.calculate("rahu", _all_in("aries"))


def test_rejects_missing_contributor():
    calc = BhinnashtakavargaCalculator()
    incomplete = _all_in("aries")
    del incomplete["saturn"]
    with pytest.raises(ValueError):
        calc.calculate("sun", incomplete)


def test_calculate_all_returns_7_planets_with_correct_totals():
    calc = BhinnashtakavargaCalculator()
    results = calc.calculate_all(_all_in("leo"))
    assert len(results) == 7
    totals = {r.target_planet: r.total_bindus for r in results}
    assert totals == {
        "sun": 48, "moon": 49, "mars": 39, "mercury": 54,
        "jupiter": 56, "venus": 52, "saturn": 39,
    }


def test_values_always_between_0_and_8_per_rashi():
    calc = BhinnashtakavargaCalculator()
    contributors = {
        "sun": "aries", "moon": "taurus", "mars": "gemini", "mercury": "cancer",
        "jupiter": "leo", "venus": "virgo", "saturn": "libra", "lagna": "scorpio",
    }
    for result in calc.calculate_all(contributors):
        for count in result.bindus_by_rashi:
            assert 0 <= count <= 8
