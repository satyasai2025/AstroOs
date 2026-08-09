"""
AstroOS — Arudha Pada Engine Unit Tests
"""

import pytest

from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet

# Everyone at a fixed degree, only signs vary between tests — degree math
# already covered by test_jaimini_engine.py, these tests are about sign
# arithmetic (lord placement -> raw Arudha -> exception shift).
_ALL_PLANETS_IN_ARIES = [
    make_planet(p, "aries", 10.0)
    for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")
]


def test_arudha_lagna_matches_worked_textbook_example():
    """
    Lagna Aries; Mars (lord of Aries) placed in Gemini.
    Count Aries->Gemini inclusive = 3. Count 3 more from Gemini
    (inclusive) = Gemini(1), Cancer(2), Leo(3) -> raw AL = Leo.
    Leo is neither Aries itself nor its 7th (Libra) -> no exception.
    """
    planets = [p for p in _ALL_PLANETS_IN_ARIES if p.planet != "mars"]
    planets.append(make_planet("mars", "gemini", 10.0))
    chart = make_d1_chart("aries", planets)
    result = ArudhaEngine().compute(chart)
    assert result.arudha_lagna.rashi == "leo"
    assert result.arudha_lagna.exception_applied is False


def test_all_12_houses_present_in_order():
    chart = make_d1_chart("aries", _ALL_PLANETS_IN_ARIES)
    result = ArudhaEngine().compute(chart)
    assert [p.house_number for p in result.padas] == list(range(1, 13))
    assert [p.pada_name for p in result.padas] == [f"A{n}" for n in range(1, 13)]


def test_upapada_lagna_is_arudha_of_12th_house():
    chart = make_d1_chart("aries", _ALL_PLANETS_IN_ARIES)
    result = ArudhaEngine().compute(chart)
    assert result.upapada_lagna is result.by_house(12)


def test_exception_fires_when_raw_lands_on_house_itself():
    """
    Lagna Aries (house 1 = Aries); Mars (lord of Aries) placed in Aries
    itself -> distance 1 -> raw AL = Aries (same as house 1's own sign)
    -> exception must shift +9 signs to Capricorn.
    """
    planets = [p for p in _ALL_PLANETS_IN_ARIES if p.planet != "mars"]
    planets.append(make_planet("mars", "aries", 10.0))
    chart = make_d1_chart("aries", planets)
    result = ArudhaEngine().compute(chart)
    al = result.arudha_lagna
    assert al.raw_rashi == "aries"
    assert al.exception_applied is True
    assert al.rashi == "capricorn"  # aries + 9 signs


def test_exception_fires_when_raw_lands_on_7th_from_house():
    """
    Lagna Aries; Mars placed in Libra (the 7th sign, distance 7) ->
    counting 7 more from Libra (inclusive) lands back on Aries... use a
    placement that produces exactly the 7th-from-house case: distance 4
    from Aries to Cancer, then 4 more from Cancer lands on Libra (7th
    from Aries) -> exception must fire.
    """
    planets = [p for p in _ALL_PLANETS_IN_ARIES if p.planet != "mars"]
    planets.append(make_planet("mars", "cancer", 10.0))
    chart = make_d1_chart("aries", planets)
    result = ArudhaEngine().compute(chart)
    al = result.arudha_lagna
    assert al.raw_rashi == "libra"  # 7th from Aries
    assert al.exception_applied is True
    assert al.rashi == "cancer"  # libra + 9 signs


def test_missing_lord_position_raises():
    # Lagna Taurus (house 1 = Taurus, lord Venus) but no Venus in chart.
    planets = [p for p in _ALL_PLANETS_IN_ARIES if p.planet != "venus"]
    chart = make_d1_chart("taurus", planets)
    with pytest.raises(ValueError):
        ArudhaEngine().compute(chart)
