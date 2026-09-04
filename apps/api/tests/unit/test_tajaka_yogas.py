"""
AstroOS - Unit Tests for 16 Classical Tajika Yogas (Shodasha Tajika Yogas)
Source: Tajika Neelakanthi
"""

import pytest

from apps.api.domain.varshaphal import TajikaAspect
from apps.api.services.tajaka_yoga_engine import TajakaYogaEngine


class _FakePlanet:
    def __init__(self, planet, sidereal_longitude, rashi, rashi_degree, house_number, speed_deg_per_day=1.0, is_retrograde=False, is_combust=False):
        self.planet = planet
        self.sidereal_longitude = sidereal_longitude
        self.rashi = rashi
        self.rashi_degree = rashi_degree
        self.house_number = house_number
        self.speed_deg_per_day = speed_deg_per_day
        self.is_retrograde = is_retrograde
        self.is_combust = is_combust


class _FakeAscendant:
    def __init__(self, rashi="aries"):
        self.rashi = rashi


class _FakeChart:
    def __init__(self, positions, asc_rashi="aries"):
        self.planet_positions = positions
        self.ascendant = _FakeAscendant(asc_rashi)


def test_ikabala_yoga_formation():
    """All planets in Kendra (1,4,7,10) or Panapara (2,5,8,11) forms Ikabala Yoga."""
    planets = [
        _FakePlanet("sun", 10.0, "aries", 10.0, 1),
        _FakePlanet("moon", 40.0, "taurus", 10.0, 2),
        _FakePlanet("mars", 100.0, "cancer", 10.0, 4),
        _FakePlanet("mercury", 130.0, "leo", 10.0, 5),
        _FakePlanet("jupiter", 190.0, "libra", 10.0, 7),
        _FakePlanet("venus", 220.0, "scorpio", 10.0, 8),
        _FakePlanet("saturn", 280.0, "capricorn", 10.0, 10),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, ())
    assert any(y.yoga_name == "Ikabala" and y.is_formed for y in yogas)


def test_induvara_yoga_formation():
    """All planets in Apoklima (3,6,9,12) forms Induvara Yoga."""
    planets = [
        _FakePlanet("sun", 70.0, "gemini", 10.0, 3),
        _FakePlanet("moon", 160.0, "virgo", 10.0, 6),
        _FakePlanet("mars", 250.0, "sagittarius", 10.0, 9),
        _FakePlanet("mercury", 340.0, "pisces", 10.0, 12),
        _FakePlanet("jupiter", 75.0, "gemini", 15.0, 3),
        _FakePlanet("venus", 165.0, "virgo", 15.0, 6),
        _FakePlanet("saturn", 255.0, "sagittarius", 15.0, 9),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, ())
    assert any(y.yoga_name == "Induvara" and y.is_formed for y in yogas)


def test_ithasala_and_isharpha_yogas():
    """Ithasala (applying within orb) and Isharpha (separating) are recognized as Tajika Yogas."""
    aspect_ithasala = TajikaAspect(
        planet_a="moon",
        planet_b="sun",
        aspect_angle=0,
        current_orb_deg=2.0,
        is_applying=True,
        is_ithasala=True,
        is_isharpha=False,
        days_to_exact=0.16,
        deeptamsha_orb_limit=13.5,
        within_deeptamsha=True,
    )
    aspect_isharpha = TajikaAspect(
        planet_a="venus",
        planet_b="mars",
        aspect_angle=60,
        current_orb_deg=1.5,
        is_applying=False,
        is_ithasala=False,
        is_isharpha=True,
        days_to_exact=None,
        deeptamsha_orb_limit=7.5,
        within_deeptamsha=True,
    )
    planets = [
        _FakePlanet("sun", 10.0, "aries", 10.0, 1),
        _FakePlanet("moon", 8.0, "aries", 8.0, 1),
        _FakePlanet("mars", 70.0, "gemini", 10.0, 3),
        _FakePlanet("venus", 11.5, "aries", 11.5, 1),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, (aspect_ithasala, aspect_isharpha))

    assert any(y.yoga_name == "Ithasala" and y.is_formed for y in yogas)
    assert any(y.yoga_name == "Isharpha" and y.is_formed for y in yogas)


def test_nakta_yoga_transfer_of_light():
    """Moon transfers light between Sun and Jupiter when they have no direct Ithasala."""
    aspect_ca = TajikaAspect(
        planet_a="moon", planet_b="sun", aspect_angle=60, current_orb_deg=1.0,
        is_applying=True, is_ithasala=True, is_isharpha=False, days_to_exact=0.1, within_deeptamsha=True,
    )
    aspect_cb = TajikaAspect(
        planet_a="moon", planet_b="jupiter", aspect_angle=120, current_orb_deg=1.5,
        is_applying=True, is_ithasala=True, is_isharpha=False, days_to_exact=0.2, within_deeptamsha=True,
    )
    planets = [
        _FakePlanet("sun", 10.0, "aries", 10.0, 1, speed_deg_per_day=1.0),
        _FakePlanet("moon", 70.0, "gemini", 10.0, 3, speed_deg_per_day=13.0),  # faster than both
        _FakePlanet("jupiter", 250.0, "sagittarius", 10.0, 9, speed_deg_per_day=0.1),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, (aspect_ca, aspect_cb))
    assert any(y.yoga_name == "Nakta" and y.is_formed for y in yogas)


def test_manahoo_yoga_interruption():
    """Mars interrupts an Ithasala between Moon and Jupiter."""
    ithasala_main = TajikaAspect(
        planet_a="moon", planet_b="jupiter", aspect_angle=120, current_orb_deg=3.0,
        is_applying=True, is_ithasala=True, is_isharpha=False, days_to_exact=2.0, within_deeptamsha=True,
    )
    interfering = TajikaAspect(
        planet_a="mars", planet_b="moon", aspect_angle=90, current_orb_deg=0.5,
        is_applying=True, is_ithasala=True, is_isharpha=False, days_to_exact=0.5, within_deeptamsha=True,
    )
    planets = [
        _FakePlanet("moon", 70.0, "gemini", 10.0, 3),
        _FakePlanet("jupiter", 250.0, "sagittarius", 10.0, 9),
        _FakePlanet("mars", 160.0, "virgo", 10.0, 6),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, (ithasala_main, interfering))
    assert any(y.yoga_name == "Manahoo" and y.is_formed for y in yogas)


def test_radda_yoga_cancellation_by_retrograde():
    """Ithasala spoiled by retrograde planet forms Radda Yoga."""
    ithasala = TajikaAspect(
        planet_a="moon", planet_b="jupiter", aspect_angle=120, current_orb_deg=1.0,
        is_applying=True, is_ithasala=True, is_isharpha=False, days_to_exact=0.1, within_deeptamsha=True,
    )
    planets = [
        _FakePlanet("moon", 70.0, "gemini", 10.0, 3),
        _FakePlanet("jupiter", 250.0, "sagittarius", 10.0, 9, is_retrograde=True),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, (ithasala,))
    assert any(y.yoga_name == "Radda" and y.is_formed for y in yogas)


def test_thambira_yoga_sandhi():
    """Planet at 29.5° of a sign forms Thambira Yoga."""
    planets = [
        _FakePlanet("sun", 29.5, "aries", 29.5, 1),
    ]
    chart = _FakeChart(planets)
    yogas = TajakaYogaEngine.evaluate_all_yogas(chart, ())
    assert any(y.yoga_name == "Thambira" and y.is_formed for y in yogas)
