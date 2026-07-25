"""
AstroOS — HouseEngine Unit Tests (Module 6.5 — Foundation Completion)
"""

import pytest

from apps.api.domain.ephemeris import DignityType, HouseCusp, SiderealPosition
from apps.api.services.house_engine import HouseEngine


@pytest.fixture
def engine() -> HouseEngine:
    return HouseEngine()


def _make_house(house_number: int, rashi: str) -> HouseCusp:
    return HouseCusp(
        house_number=house_number,
        longitude=float((house_number - 1) * 30),
        sidereal_longitude=float((house_number - 1) * 30),
        rashi=rashi,
    )


def _make_planet(planet: str, house_number: int) -> SiderealPosition:
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=house_number, nakshatra="ashwini", pada=1,
        is_retrograde=False, is_combust=False, combustion_orb=None,
        dignity=DignityType.NEUTRAL,
    )


# ── Classification ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("house_number", [1, 4, 7, 10])
def test_classify_kendra_houses(engine, house_number):
    c = engine.classify(house_number)
    assert c.quadrant == "kendra"


@pytest.mark.parametrize("house_number", [2, 5, 8, 11])
def test_classify_panapara_houses(engine, house_number):
    c = engine.classify(house_number)
    assert c.quadrant == "panapara"


@pytest.mark.parametrize("house_number", [3, 6, 9, 12])
def test_classify_apoklima_houses(engine, house_number):
    c = engine.classify(house_number)
    assert c.quadrant == "apoklima"


def test_every_house_has_exactly_one_quadrant(engine):
    """Quadrant classification must partition all 12 houses with no overlap."""
    quadrants = [engine.classify(h).quadrant for h in range(1, 13)]
    assert set(quadrants) == {"kendra", "panapara", "apoklima"}
    kendra_count = quadrants.count("kendra")
    panapara_count = quadrants.count("panapara")
    apoklima_count = quadrants.count("apoklima")
    assert kendra_count == panapara_count == apoklima_count == 4


@pytest.mark.parametrize("house_number,expected", [
    (1, True), (5, True), (9, True), (2, False), (6, False),
])
def test_classify_trikona_flag(engine, house_number, expected):
    assert engine.classify(house_number).is_trikona is expected


@pytest.mark.parametrize("house_number,expected", [
    (6, True), (8, True), (12, True), (1, False), (7, False),
])
def test_classify_dusthana_flag(engine, house_number, expected):
    assert engine.classify(house_number).is_dusthana is expected


@pytest.mark.parametrize("house_number,expected", [
    (3, True), (6, True), (10, True), (11, True), (1, False), (7, False),
])
def test_classify_upachaya_flag(engine, house_number, expected):
    assert engine.classify(house_number).is_upachaya is expected


def test_house_5_is_both_trikona_and_panapara(engine):
    """Non-exclusive flags can overlap with quadrant — house 5 is a real example."""
    c = engine.classify(5)
    assert c.quadrant == "panapara"
    assert c.is_trikona is True


# ── House lordship ────────────────────────────────────────────────────────────

def test_get_house_lord(engine):
    assert engine.get_house_lord("aries") == "mars"
    assert engine.get_house_lord("cancer") == "moon"
    assert engine.get_house_lord("libra") == "venus"


def test_get_house_lord_all_12_signs_resolve(engine):
    rashis = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
    ]
    for rashi in rashis:
        lord = engine.get_house_lord(rashi)
        assert isinstance(lord, str) and lord


# ── Full house summary ────────────────────────────────────────────────────────

def test_build_house_summary_returns_12_houses(engine):
    houses = [_make_house(i, "aries") for i in range(1, 13)]
    summary = engine.build_house_summary(houses, planets=[])
    assert len(summary) == 12
    assert {h.house_number for h in summary} == set(range(1, 13))


def test_build_house_summary_assigns_occupants(engine):
    houses = [_make_house(i, "aries") for i in range(1, 13)]
    planets = [_make_planet("sun", house_number=1), _make_planet("moon", house_number=1),
               _make_planet("mars", house_number=5)]
    summary = engine.build_house_summary(houses, planets)

    house_1 = next(h for h in summary if h.house_number == 1)
    house_5 = next(h for h in summary if h.house_number == 5)
    house_2 = next(h for h in summary if h.house_number == 2)

    assert set(house_1.occupants) == {"sun", "moon"}
    assert house_5.occupants == ["mars"]
    assert house_2.occupants == []


def test_build_house_summary_includes_lord_and_classification(engine):
    houses = [_make_house(1, "aries")]
    summary = engine.build_house_summary(houses, planets=[])
    assert summary[0].lord == "mars"
    assert summary[0].classification.quadrant == "kendra"
    assert summary[0].rashi == "aries"
