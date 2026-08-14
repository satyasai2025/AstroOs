"""
Unit tests for SignChangeEngine ("when will this planet change sign?").

Reference chart: 30-Jun-1971 04:57:40 IST, Vadodara, Lahiri.

The assertions that matter most are the retrograde ones. A naive
degrees-remaining ÷ speed estimate gets Jupiter and Saturn badly wrong here,
so those cases are pinned explicitly — they are exactly what a scan-based
implementation buys over arithmetic.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.sign_change_engine import SignChangeEngine

_BIRTH = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
_LAT, _LON = 22.3, 73.2

_ZODIAC = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
           "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]


@pytest.fixture(scope="module")
def engine():
    return SignChangeEngine(EphemerisWrapper("data/ephemeris"))


@pytest.fixture(scope="module")
def all_planets(engine):
    return {p.planet: p for p in engine.all_planets(_BIRTH, _LAT, _LON, "lahiri")}


class TestCoverage:
    def test_returns_all_nine_grahas(self, all_planets):
        assert set(all_planets) == {
            "sun", "moon", "mars", "mercury", "jupiter",
            "venus", "saturn", "rahu", "ketu",
        }

    def test_every_planet_resolves_both_boundaries(self, all_planets):
        """Search horizons must be wide enough for even Saturn."""
        for p in all_planets.values():
            assert p.entered_utc is not None, f"{p.planet} entry not found"
            assert p.exits_utc is not None, f"{p.planet} exit not found"

    def test_entry_precedes_birth_and_exit_follows(self, all_planets):
        for p in all_planets.values():
            assert p.entered_utc < _BIRTH < p.exits_utc
            assert p.days_since_entry > 0
            assert p.days_until_exit > 0


class TestDirectMotion:
    def test_moon_leaves_virgo_in_about_two_days(self, all_planets):
        moon = all_planets["moon"]
        assert moon.rashi == "virgo"
        assert moon.next_rashi == "libra"
        assert moon.days_until_exit == pytest.approx(2.05, abs=0.15)

    def test_direct_planets_move_to_the_next_sign(self, all_planets):
        for name in ("sun", "moon", "mercury", "venus", "mars", "saturn"):
            p = all_planets[name]
            if p.is_retrograde or p.exits_retrograde:
                continue
            expected = _ZODIAC[(_ZODIAC.index(p.rashi) + 1) % 12]
            assert p.next_rashi == expected, f"{name} exits to {p.next_rashi}"


class TestRetrogradeHandling:
    def test_jupiter_exits_forward_despite_being_retrograde(self, all_planets):
        """Jupiter is retrograde at 4.06 deg Scorpio. Extrapolating its
        current speed suggests Libra in ~56 days; in fact it stations direct
        first and reaches Sagittarius ~190 days later."""
        jup = all_planets["jupiter"]
        assert jup.is_retrograde is True
        assert jup.rashi == "scorpio"
        assert jup.next_rashi == "sagittarius"
        assert jup.days_until_exit == pytest.approx(190.1, abs=3.0)

    def test_saturn_exit_is_delayed_by_a_retrograde_loop(self, all_planets):
        """Naive estimate ~196 days; the real answer is ~712 because Saturn
        turns retrograde in between."""
        sat = all_planets["saturn"]
        assert sat.days_until_exit == pytest.approx(711.6, abs=10.0)
        assert sat.days_until_exit > 400

    def test_rahu_moves_backwards_through_the_zodiac(self, all_planets):
        rahu = all_planets["rahu"]
        assert rahu.is_retrograde is True
        expected = _ZODIAC[(_ZODIAC.index(rahu.rashi) - 1) % 12]
        assert rahu.next_rashi == expected


class TestKetuMirrorsRahu:
    def test_ketu_is_opposite_rahu(self, all_planets):
        rahu, ketu = all_planets["rahu"], all_planets["ketu"]
        gap = (ketu.sidereal_longitude - rahu.sidereal_longitude) % 360
        assert gap == pytest.approx(180.0, abs=1e-6)

    def test_ketu_changes_sign_at_the_same_moment_as_rahu(self, all_planets):
        rahu, ketu = all_planets["rahu"], all_planets["ketu"]
        assert ketu.days_until_exit == pytest.approx(rahu.days_until_exit, abs=1e-3)
        assert ketu.days_since_entry == pytest.approx(rahu.days_since_entry, abs=1e-3)

    def test_ketu_target_sign_is_opposite_rahus(self, all_planets):
        rahu, ketu = all_planets["rahu"], all_planets["ketu"]
        expected = _ZODIAC[(_ZODIAC.index(rahu.next_rashi) + 6) % 12]
        assert ketu.next_rashi == expected


class TestSingleQuery:
    def test_single_matches_batch(self, engine, all_planets):
        one = engine.sign_period("jupiter", _BIRTH, _LAT, _LON, "lahiri")
        assert one.rashi == all_planets["jupiter"].rashi
        assert one.days_until_exit == pytest.approx(
            all_planets["jupiter"].days_until_exit, abs=1e-6
        )

    def test_ayanamsa_is_applied(self, engine):
        """Sanity that the process-global sidereal mode is actually set."""
        lahiri = engine.sign_period("sun", _BIRTH, _LAT, _LON, "lahiri")
        pushya = engine.sign_period("sun", _BIRTH, _LAT, _LON, "true_pushya")
        assert lahiri.sidereal_longitude != pushya.sidereal_longitude
