"""
AstroOS — Unit Tests for Mundane Ingress Engine
"""

import pytest
from apps.api.domain.mundane import IngressType
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.mundane_ingress_engine import MundaneIngressEngine


@pytest.fixture
def ingress_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return MundaneIngressEngine(wrapper)


def test_chaitra_shukla_pratipada_calculation(ingress_engine):
    """Calculates exact Chaitra Shukla Pratipada New Moon ingress for 2026."""
    moment = ingress_engine.find_chaitra_shukla_pratipada(2026, "lahiri")

    assert moment.ingress_type == IngressType.CHAITRA_SHUKLA_PRATIPADA
    assert moment.timestamp_utc.year == 2026
    assert moment.timestamp_utc.month in (3, 4)
    # Sun and Moon separation should be within sub-arcsecond precision (< 0.005°)
    diff = abs(moment.moon_longitude - moment.sun_longitude) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    assert diff < 0.01
    assert len(moment.weekday) > 0
    assert len(moment.weekday_lord) > 0


def test_cardinal_solar_ingress_mesha(ingress_engine):
    """Calculates Mesha Sankranti (0° Aries Ingress) for 2026."""
    moment = ingress_engine.find_solar_ingress(2026, 0.0, IngressType.MESHA_SANKRANTI, 4, 14, "lahiri")

    assert moment.ingress_type == IngressType.MESHA_SANKRANTI
    assert moment.timestamp_utc.month == 4
    diff_0 = min(moment.sun_longitude, abs(moment.sun_longitude - 360.0))
    assert diff_0 < 0.05


def test_national_ingress_chart_generation(ingress_engine):
    """Casts Chaitra Pratipada national horoscope for New Delhi, India."""
    moment = ingress_engine.find_chaitra_shukla_pratipada(2026, "lahiri")
    chart_res = ingress_engine.generate_ingress_chart(
        moment=moment,
        country_name="India",
        capital_city="New Delhi",
        latitude=28.6139,
        longitude=77.2090,
        ayanamsa="lahiri",
    )

    assert chart_res.country_name == "India"
    assert chart_res.capital_city == "New Delhi"
    assert len(chart_res.ascendant_rashi) > 0
    assert len(chart_res.tenth_house_rashi) > 0
    assert chart_res.chart is not None
