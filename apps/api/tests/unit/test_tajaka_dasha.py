"""
AstroOS - Unit Tests for Tajaka Annual Dasha Systems (Mudda & Patyayini Dasha)
Source: Tajika Neelakanthi, PyJHora, B.V. Raman's Varshaphal
"""

import pytest

from apps.api.services.tajaka_dasha_engine import TajakaDashaEngine


class _FakePlanet:
    def __init__(self, planet, sidereal_longitude, rashi_degree=10.0):
        self.planet = planet
        self.sidereal_longitude = sidereal_longitude
        self.rashi_degree = rashi_degree


class _FakeAscendant:
    def __init__(self, rashi_degree=15.0):
        self.rashi_degree = rashi_degree


class _FakeChart:
    def __init__(self, moon_long):
        self.planet_positions = [
            _FakePlanet("sun", 10.0, 10.0),
            _FakePlanet("moon", moon_long, moon_long % 30.0),
            _FakePlanet("mars", 100.0, 10.0),
            _FakePlanet("mercury", 40.0, 10.0),
            _FakePlanet("jupiter", 260.0, 20.0),
            _FakePlanet("venus", 190.0, 10.0),
            _FakePlanet("saturn", 280.0, 10.0),
        ]
        self.ascendant = _FakeAscendant(15.0)


def test_mudda_dasha_total_duration_matches_solar_year():
    """Total duration of all Mudda dasha periods must equal 365.2425 days."""
    chart = _FakeChart(moon_long=10.0)  # Ashwini (Ketu lord)
    solar_jd = 2460000.5
    periods = TajakaDashaEngine.calculate_mudda_dasha(chart, solar_jd, 365.2425)

    assert len(periods) > 0
    total_days = sum(p.duration_days for p in periods)
    assert total_days == pytest.approx(365.2425, abs=0.01)

    # First dasha is Ketu (Ashwini nakshatra)
    assert periods[0].planet == "ketu"


def test_mudda_dasha_antardashas():
    """Each Mudda dasha period has 9 sub-periods summing to its duration."""
    chart = _FakeChart(moon_long=10.0)
    solar_jd = 2460000.5
    periods = TajakaDashaEngine.calculate_mudda_dasha(chart, solar_jd, 365.2425)

    first_period = periods[0]
    assert len(first_period.antardashas) == 9
    sub_total = sum(sub.duration_days for sub in first_period.antardashas)
    assert sub_total == pytest.approx(first_period.duration_days, abs=0.01)


def test_patyayini_dasha_ordering_and_duration():
    """Patyayini dasha partitions the year based on ascending Krishnamsha degrees."""
    chart = _FakeChart(moon_long=25.0)
    solar_jd = 2460000.5
    periods = TajakaDashaEngine.calculate_patyayini_dasha(chart, solar_jd, 365.2425)

    assert len(periods) > 0
    total_days = sum(p.duration_days for p in periods)
    assert total_days == pytest.approx(365.2425, abs=0.1)

    # Verify ascending krishnamsha order
    for i in range(len(periods) - 1):
        assert periods[i].krishnamsha_deg <= periods[i + 1].krishnamsha_deg
