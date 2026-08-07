"""
AstroOS — Jaimini Shared Primitives Unit Tests
"""

import pytest

from apps.api.services.jaimini_shared import (
    RASHI_LIST,
    house_count,
    is_benefic,
    is_kendra,
    planets_in_rashi,
    rashi_at,
    rashi_index,
    sign_nature,
    signs_from,
    whole_sign_house_rashi,
)
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet


def test_rashi_list_is_zodiacal_order():
    assert RASHI_LIST[0] == "aries"
    assert RASHI_LIST[11] == "pisces"
    assert len(RASHI_LIST) == 12


def test_rashi_index_and_rashi_at_round_trip():
    for i, rashi in enumerate(RASHI_LIST):
        assert rashi_index(rashi) == i
        assert rashi_at(i) == rashi


def test_signs_from_wraps_forward_and_backward():
    assert signs_from("aries", 0) == "aries"
    assert signs_from("aries", 1) == "taurus"
    assert signs_from("aries", 12) == "aries"  # full revolution
    assert signs_from("aries", -1) == "pisces"  # backward wraps correctly
    assert signs_from("pisces", 1) == "aries"


def test_house_count_is_inclusive_1_to_12():
    assert house_count("aries", "aries") == 1
    assert house_count("aries", "taurus") == 2
    assert house_count("aries", "pisces") == 12
    assert house_count("taurus", "aries") == 12  # wraps backward through the whole zodiac


@pytest.mark.parametrize(
    "from_rashi,to_rashi,expected",
    [
        ("aries", "aries", True),  # 1st (conjunction) is always a Kendra
        ("aries", "cancer", True),  # 4th
        ("aries", "libra", True),  # 7th
        ("aries", "capricorn", True),  # 10th
        ("aries", "taurus", False),  # 2nd
        ("aries", "gemini", False),  # 3rd
    ],
)
def test_is_kendra(from_rashi, to_rashi, expected):
    assert is_kendra(from_rashi, to_rashi) is expected


@pytest.mark.parametrize(
    "rashi,expected",
    [
        ("aries", "chara"), ("cancer", "chara"), ("libra", "chara"), ("capricorn", "chara"),
        ("taurus", "sthira"), ("leo", "sthira"), ("scorpio", "sthira"), ("aquarius", "sthira"),
        ("gemini", "dvisvabhava"), ("virgo", "dvisvabhava"),
        ("sagittarius", "dvisvabhava"), ("pisces", "dvisvabhava"),
    ],
)
def test_sign_nature_classifies_all_12_signs(rashi, expected):
    assert sign_nature(rashi) == expected


def test_sign_nature_rejects_unknown_rashi():
    with pytest.raises(ValueError):
        sign_nature("not-a-sign")


def test_whole_sign_house_rashi_from_lagna():
    chart = make_d1_chart("leo", [make_planet("sun", "aries")])
    assert whole_sign_house_rashi(chart, 1) == "leo"
    assert whole_sign_house_rashi(chart, 2) == "virgo"
    assert whole_sign_house_rashi(chart, 12) == "cancer"


def test_whole_sign_house_rashi_rejects_out_of_range():
    chart = make_d1_chart("leo", [make_planet("sun", "aries")])
    with pytest.raises(ValueError):
        whole_sign_house_rashi(chart, 13)
    with pytest.raises(ValueError):
        whole_sign_house_rashi(chart, 0)


def test_planets_in_rashi_finds_all_occupants():
    chart = make_d1_chart(
        "leo", [make_planet("sun", "aries"), make_planet("mercury", "aries"), make_planet("moon", "cancer")]
    )
    assert set(planets_in_rashi(chart, "aries")) == {"sun", "mercury"}
    assert planets_in_rashi(chart, "cancer") == ["moon"]
    assert planets_in_rashi(chart, "pisces") == []


def test_is_benefic_natural_classification():
    chart = make_d1_chart("aries", [], paksha="shukla")
    assert is_benefic("jupiter", chart) is True
    assert is_benefic("venus", chart) is True
    assert is_benefic("mercury", chart) is True
    assert is_benefic("sun", chart) is False
    assert is_benefic("mars", chart) is False
    assert is_benefic("saturn", chart) is False
    assert is_benefic("rahu", chart) is False
    assert is_benefic("ketu", chart) is False


def test_is_benefic_moon_depends_on_paksha():
    waxing_chart = make_d1_chart("aries", [], paksha="shukla")
    waning_chart = make_d1_chart("aries", [], paksha="krishna")
    assert is_benefic("moon", waxing_chart) is True
    assert is_benefic("moon", waning_chart) is False
