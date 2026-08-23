"""
AstroOS — Dina-Hora Bala Unit Tests (Module 9)

Uses real EphemerisWrapper output (not a synthetic stub) because the
Hora-lord formula itself (see dina_hora_bala.py) needs a real calendar
date/civil-weekday, not just relative JD offsets — a from-scratch
"24 planetary hours" method used here previously didn't; it's been
replaced with PyJHora's verified formula, which does.

Every expected value below was independently cross-checked against
PyJHora's jhora.horoscope.chart.strength._hora_bala() /
_vaaradhipathi() for New Delhi (28.6139N, 77.2090E, IST) on 1995-01-01
at each listed birth time — see tests/integration/
test_dina_hora_bala_integration.py for further chart-level coverage.
"""

from datetime import datetime, timezone

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala.dina_hora_bala import DinaHoraBalaCalculator

_LAT, _LON = 28.6139, 77.2090


def _make_planet(planet):
    return SiderealPosition(
        planet=planet, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        house_number=1, nakshatra="ashwini", pada=1, is_retrograde=False,
        is_combust=False, combustion_orb=None, dignity=DignityType.NEUTRAL,
    )


def _ephemeris_result(hour, minute=0):
    """Real EphemerisResult for 1995-01-01, IST time (hour:minute), New Delhi."""
    from datetime import timedelta
    wrapper = EphemerisWrapper("data/ephemeris")
    local_dt = datetime(1995, 1, 1, hour, minute, 0, tzinfo=timezone.utc)
    birth_dt_utc = local_dt - timedelta(hours=5, minutes=30)
    return wrapper.calculate(dt=birth_dt_utc, latitude=_LAT, longitude=_LON, ayanamsa="lahiri")


@pytest.mark.parametrize("hour,minute,expected_dina,expected_hora", [
    (17, 30, "sun", "mercury"),     # verified: 17:30 IST -> Sunday, dina=Sun, hora=Mercury
    (23, 0, "sun", "sun"),          # verified: 23:00 IST -> still Sunday's Vedic day, hora=Sun
    (6, 0, "saturn", "jupiter"),    # verified: 06:00 IST, before ~07:13 sunrise -> previous
                                     # (Saturday) Vedic day. Fixed in ephemeris_wrapper.py's
                                     # calculate(): Vara is now derived from the sunrise JD
                                     # bracketing the birth moment, not the birth moment's own
                                     # civil-midnight-based JD.
])
def test_dina_and_hora_lord_match_verified_reference(hour, minute, expected_dina, expected_hora):
    result = _ephemeris_result(hour, minute)
    calc = DinaHoraBalaCalculator(EphemerisWrapper("data/ephemeris"))

    dina_r = calc.calculate(_make_planet(expected_dina), result, latitude=_LAT, longitude=_LON)
    assert dina_r.value_shashtiamsas >= 45.0, f"{expected_dina} should score at least Dina's 45 points"

    hora_r = calc.calculate(_make_planet(expected_hora), result, latitude=_LAT, longitude=_LON)
    assert hora_r.value_shashtiamsas >= 60.0, f"{expected_hora} should score at least Hora's 60 points"


def test_dina_lord_no_match_scores_0_for_dina_component():
    result = _ephemeris_result(17, 30)
    calc = DinaHoraBalaCalculator(EphemerisWrapper("data/ephemeris"))
    r = calc.calculate(_make_planet("venus"), result, latitude=_LAT, longitude=_LON)
    assert any("Dina" in t and "no match" in t for t in r.trace)


def test_sun_dina_lord_scores_exactly_45_when_not_also_hora_lord():
    """17:30 IST: Sun is Dina lord (45) but Mercury is Hora lord, so Sun scores exactly 45, not 105."""
    result = _ephemeris_result(17, 30)
    calc = DinaHoraBalaCalculator(EphemerisWrapper("data/ephemeris"))
    r = calc.calculate(_make_planet("sun"), result, latitude=_LAT, longitude=_LON)
    assert r.value_shashtiamsas == pytest.approx(45.0)


def test_missing_sunrise_skips_hora_but_keeps_dina():
    result = _ephemeris_result(17, 30)
    result = result.__class__(**{**result.__dict__, "sunrise_jd": None, "sunset_jd": None})
    calc = DinaHoraBalaCalculator(EphemerisWrapper("data/ephemeris"))
    r = calc.calculate(_make_planet("sun"), result, latitude=_LAT, longitude=_LON)
    assert r.value_shashtiamsas == pytest.approx(45.0)
    assert any("hora lord skipped" in t for t in r.trace)


def test_rejects_rahu_ketu():
    result = _ephemeris_result(17, 30)
    calc = DinaHoraBalaCalculator(EphemerisWrapper("data/ephemeris"))
    with pytest.raises(ValueError):
        calc.calculate(_make_planet("rahu"), result, latitude=_LAT, longitude=_LON)


def test_calculate_all_returns_7_classical_grahas():
    result = _ephemeris_result(17, 30)
    planets = [_make_planet(p) for p in
               ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]]
    calc = DinaHoraBalaCalculator(EphemerisWrapper("data/ephemeris"))
    results = calc.calculate_all(planets, result, latitude=_LAT, longitude=_LON)
    assert len(results) == 7
    assert "rahu" not in {r.planet for r in results}
