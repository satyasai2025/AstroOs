"""
Unit tests for LagnaScanEngine.

Reference chart: 30-Jun-1971 04:57:40 IST, Vadodara (22N18, 73E12), Lahiri.
Chosen deliberately — its lagna sits at 29.81° Taurus, i.e. 49 seconds from
the Gemini boundary, which is what makes it a good rectification case and
also what exposed the original ET/UT bug.

Most assertions are structural (boundaries partition the division, the
timeline is contiguous) rather than hardcoded longitudes, so they stay valid
if the ayanamsa default ever changes.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.lagna_scan_engine import LagnaScanEngine

_BIRTH = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)  # 04:57:40 IST
_LAT, _LON = 22.3, 73.2

_SPANS = {"rashi": 30.0, "nakshatra": 360.0 / 27.0, "pada": 360.0 / 108.0}


@pytest.fixture(scope="module")
def engine():
    return LagnaScanEngine(EphemerisWrapper("data/ephemeris"))


@pytest.fixture(scope="module")
def result(engine):
    return engine.scan(_BIRTH, _LAT, _LON, "lahiri", window_hours=2.0)


class TestBirthPosition:
    def test_lagna_is_late_taurus(self, result):
        assert result.rashi == "taurus"
        assert result.rashi_degree == pytest.approx(29.806, abs=0.01)

    def test_nakshatra_matches_jhora(self, result):
        """Classical Vedic reports Mrigashira pada 2 for this lagna."""
        assert result.nakshatra == "mrigashira"
        assert result.pada == 2

    def test_sensitivity_is_plausible(self, result):
        """The ascendant averages 15'/min (360° per sidereal day) but varies
        with latitude and rising sign, so just bound it loosely."""
        assert 5.0 < result.arcmin_per_minute < 40.0


class TestBoundaries:
    @pytest.mark.parametrize("label", sorted(_SPANS))
    def test_degrees_partition_the_division(self, result, label):
        """since + until must reconstruct the division width exactly — this
        is what caught a bisection window longer than one revolution, which
        had returned the previous revolution's boundary."""
        b = next(x for x in result.boundaries if x.label == label)
        total = b.degrees_since_previous + b.degrees_until_next
        assert total == pytest.approx(_SPANS[label], abs=1e-6)

    @pytest.mark.parametrize("label", sorted(_SPANS))
    def test_times_are_positive_and_bounded(self, result, label):
        b = next(x for x in result.boundaries if x.label == label)
        assert b.minutes_since_previous > 0
        assert b.minutes_until_next > 0
        # No division of the zodiac takes over a day to rise at this latitude.
        assert b.minutes_since_previous + b.minutes_until_next < 24 * 60

    def test_rashi_change_is_imminent(self, result):
        """The whole point of this chart: under a minute to the sign change."""
        b = next(x for x in result.boundaries if x.label == "rashi")
        assert b.minutes_until_next < 1.0

    def test_finer_divisions_are_nearer(self, result):
        """A pada boundary can never be further off than its nakshatra's."""
        by = {b.label: b for b in result.boundaries}
        assert by["pada"].minutes_until_next <= by["nakshatra"].minutes_until_next + 1e-6


class TestTimeline:
    def test_exactly_one_interval_holds_the_birth(self, result):
        assert sum(1 for i in result.intervals if i.contains_birth) == 1

    def test_birth_interval_is_taurus(self, result):
        birth_iv = next(i for i in result.intervals if i.contains_birth)
        assert birth_iv.rashi == "taurus"

    def test_intervals_are_contiguous(self, result):
        for a, b in zip(result.intervals, result.intervals[1:]):
            assert a.end_utc == b.end_utc or a.end_utc == b.start_utc

    def test_intervals_are_in_zodiacal_order(self, result):
        order = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
                 "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
        idx = [order.index(i.rashi) for i in result.intervals]
        for a, b in zip(idx, idx[1:]):
            assert b == (a + 1) % 12

    def test_window_covers_the_birth(self, result):
        assert result.window_start_utc < _BIRTH < result.window_end_utc


class TestBirthtimeShift:
    def test_next_lands_at_start_of_gemini(self, engine):
        t = engine.birthtime_for_adjacent_sign(_BIRTH, _LAT, _LON, "next")
        assert t > _BIRTH
        r = engine.scan(t, _LAT, _LON, "lahiri", 0.1)
        assert r.rashi == "gemini"
        assert r.rashi_degree < 0.5   # just inside, not deep into the sign

    def test_previous_lands_at_end_of_aries(self, engine):
        t = engine.birthtime_for_adjacent_sign(_BIRTH, _LAT, _LON, "previous")
        assert t < _BIRTH
        r = engine.scan(t, _LAT, _LON, "lahiri", 0.1)
        assert r.rashi == "aries"
        assert r.rashi_degree > 29.5

    def test_rejects_bad_direction(self, engine):
        with pytest.raises(ValueError):
            engine.birthtime_for_adjacent_sign(_BIRTH, _LAT, _LON, "sideways")


class TestAyanamsaIsApplied:
    def test_different_ayanamsa_shifts_the_lagna(self, engine):
        """pyswisseph's sidereal mode is process-global; the engine must set
        it rather than inherit whatever was left over. True Pushya is ~1.14°
        from Lahiri, which is enough to flip this boundary chart's sign."""
        lahiri = engine.scan(_BIRTH, _LAT, _LON, "lahiri", 0.1)
        pushya = engine.scan(_BIRTH, _LAT, _LON, "true_pushya", 0.1)
        assert lahiri.rashi == "taurus"
        assert pushya.rashi == "gemini"
