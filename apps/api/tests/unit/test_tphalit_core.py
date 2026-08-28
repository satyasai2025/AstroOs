"""
Unit tests for TPhalitCore deterministic feature extraction.
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.services.phalita_core.tphalit_core import (
    TPhalitCore,
    TPhalitFeatureVector,
)


@pytest.fixture
def sample_rajayoga_chart():
    """Chart with exalted Sun in Aries (1st house), exalted Moon in Taurus, and Gaja Kesari Yoga."""
    rashis = ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
              "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    asc = Ascendant(0.0, 0.0, "aries", 0.0, "ashwini", 1)
    planets = [
        SiderealPosition("sun", 10.0, "aries", 10.0, 1, "ashwini", 3, False, False, None, "exalted"),
        SiderealPosition("moon", 33.0, "taurus", 3.0, 2, "krittika", 2, False, False, None, "exalted"),
        SiderealPosition("mars", 298.0, "capricorn", 28.0, 10, "dhanishta", 2, False, False, None, "exalted"),
        SiderealPosition("mercury", 20.0, "aries", 20.0, 1, "bharani", 3, False, False, None, None),
        SiderealPosition("jupiter", 95.0, "cancer", 5.0, 4, "pushya", 1, False, False, None, "exalted"),
        SiderealPosition("venus", 357.0, "pisces", 27.0, 12, "revati", 4, False, False, None, "exalted"),
        SiderealPosition("saturn", 200.0, "libra", 20.0, 7, "vishakha", 1, False, False, None, "exalted"),
        SiderealPosition("rahu", 50.0, "taurus", 20.0, 2, "rohini", 4, True, False, None, None),
        SiderealPosition("ketu", 230.0, "scorpio", 20.0, 8, "jyeshtha", 2, True, False, None, None),
    ]
    houses = [HouseCusp(n, float((n - 1) * 30), float((n - 1) * 30), rashis[n - 1]) for n in range(1, 13)]
    return D1Chart(None, asc, houses, planets, [], [], None, "lahiri", "W")


@pytest.fixture
def sample_dasha_tree():
    sun_ad1 = DashaPeriod("sun", date(2020, 1, 1), date(2020, 4, 19), 108, 2, [])
    sun_ad2 = DashaPeriod("moon", date(2020, 4, 19), date(2020, 10, 19), 183, 2, [])
    sun_ad3 = DashaPeriod("mars", date(2020, 10, 19), date(2021, 2, 25), 129, 2, [])

    sun_md = DashaPeriod("sun", date(2020, 1, 1), date(2026, 1, 1), 2191, 1, [sun_ad1, sun_ad2, sun_ad3])
    return DashaTree("vimshottari", date(1990, 1, 1), "sun", "krittika", 3, [sun_md], 2, 120)


def test_tphalit_core_planet_dignity(sample_rajayoga_chart):
    core = TPhalitCore()
    sun_pos = next(p for p in sample_rajayoga_chart.planets if p.planet == "sun")
    score, rank, has_nb, _ = core.compute_planet_strength("sun", sun_pos, sample_rajayoga_chart)

    assert rank == 9
    assert score >= 0.8
    assert not has_nb


def test_tphalit_core_yogas_detection(sample_rajayoga_chart):
    core = TPhalitCore()
    yogas = core.compute_active_yogas(sample_rajayoga_chart)
    yoga_names = [y.yoga_name for y in yogas]

    assert "Ruchaka Yoga" in yoga_names
    assert "Hamsa Yoga" in yoga_names
    assert "Sasa Yoga" in yoga_names
    assert "Budhaditya Yoga" in yoga_names


def test_tphalit_core_full_feature_vector(sample_rajayoga_chart, sample_dasha_tree):
    core = TPhalitCore()
    vec = core.extract_full_vector(
        chart=sample_rajayoga_chart,
        dasha_tree=sample_dasha_tree,
        target_date=date(2020, 6, 1),
    )

    assert isinstance(vec, TPhalitFeatureVector)
    assert len(vec.raw_vector) == 128
    assert all(not (x != x) for x in vec.raw_vector)  # No NaNs
    assert "career" in vec.domain_scores
    assert "marriage" in vec.domain_scores
    assert vec.domain_scores["career"] > 0.0  # Auspicious Sun-Moon dasha with exalted planets
