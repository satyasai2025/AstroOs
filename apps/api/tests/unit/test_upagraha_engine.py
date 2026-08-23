"""
Unit tests for UpagrahaEngine (Gulika/Maandi + Bhava/Hora/Ghati lagnas).

The reference chart is the one used throughout this repo's accuracy work:
30-Jun-1971 04:57:40 IST, Vadodara (22N18, 73E12), Lahiri. Expected values
come from Classical Vedic System's own output for that chart.

Tolerance is 2 arc-minutes rather than arc-seconds on purpose: Classical Vedic's
Lahiri variant differs from Swiss Ephemeris SIDM_LAHIRI by ~55", which
shows up on every derived point (and on every planet). Tightening below
that would be testing the ayanamsa variant, not the upagraha maths — with
Classical Vedic's own ayanamsa substituted, these same formulas land within ~20".
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.upagraha_engine import UpagrahaEngine

_BIRTH = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)  # 04:57:40 IST 30-Jun
_LAT, _LON = 22.3, 73.2
_TOL_ARCMIN = 2.0


def _dms(d: int, m: int, s: float) -> float:
    return d + m / 60 + s / 3600


# Classical Vedic reference longitudes (sidereal, Lahiri)
_JHORA = {
    "gulika":      240 + _dms(13, 44, 7.34),
    "maandi":      240 + _dms(23, 23, 28.23),
    "bhava_lagna":  30 + _dms(27, 40, 56.13),
    "hora_lagna":   30 + _dms(12, 9, 37.05),
    "ghati_lagna": 330 + _dms(25, 35, 39.83),
}

_JHORA_RASHI = {
    "gulika": "sagittarius",
    "maandi": "sagittarius",
    "bhava_lagna": "taurus",
    "hora_lagna": "taurus",
    "ghati_lagna": "pisces",
}


@pytest.fixture(scope="module")
def result():
    wrapper = EphemerisWrapper("data/ephemeris")
    return UpagrahaEngine(wrapper).compute(_BIRTH, _LAT, _LON, "lahiri")


@pytest.fixture(scope="module")
def by_name(result):
    return {p.name: p for p in list(result.upagrahas) + list(result.special_lagnas)}


class TestDayNightFrame:
    def test_pre_dawn_birth_is_night(self, result):
        """04:57 IST is before sunrise (~05:59), so this is a night birth."""
        assert result.is_daytime_birth is False

    def test_vedic_weekday_is_previous_day(self, result):
        """Vedic days run sunrise-to-sunrise: a pre-dawn Wednesday birth
        still belongs to Tuesday. Classical Vedic likewise reports Tuesday."""
        assert result.weekday == "tuesday"

    def test_night_starts_from_fifth_weekday_lord(self, result):
        """Night parts start from the 5th weekday onward — Tuesday + 4 =
        Saturday, so Saturn rules the first part."""
        assert result.starting_lord == "saturn"

    def test_eight_parts_span_the_period(self, result):
        span_hours = (result.period_end_jd - result.period_start_jd) * 24.0
        assert result.part_duration_hours == pytest.approx(span_hours / 8.0, abs=1e-9)


class TestAgainstJHora:
    @pytest.mark.parametrize("name", sorted(_JHORA))
    def test_longitude_matches(self, by_name, name):
        got = by_name[name].sidereal_longitude
        diff_arcmin = abs(got - _JHORA[name]) * 60
        assert diff_arcmin < _TOL_ARCMIN, (
            f"{name}: got {got:.4f}, Classical Vedic {_JHORA[name]:.4f} "
            f"({diff_arcmin:.2f} arc-min apart)"
        )

    @pytest.mark.parametrize("name", sorted(_JHORA_RASHI))
    def test_rashi_matches(self, by_name, name):
        assert by_name[name].rashi == _JHORA_RASHI[name]


class TestStructure:
    def test_maandi_is_half_a_part_after_gulika(self, result, by_name):
        """Gulika sits at the start of Saturn's part, Maandi at its midpoint,
        so they are half a part apart in time — a little over 9 deg here."""
        gap = by_name["maandi"].sidereal_longitude - by_name["gulika"].sidereal_longitude
        assert 8.0 < gap < 11.0

    def test_every_point_has_a_house(self, by_name):
        for p in by_name.values():
            assert 1 <= p.house_number <= 12

    def test_special_lagna_rates_are_ordered(self, by_name):
        """Ghati advances fastest, Bhava slowest — so from the same sunrise
        origin they must not all coincide."""
        lons = {n: by_name[n].sidereal_longitude
                for n in ("bhava_lagna", "hora_lagna", "ghati_lagna")}
        assert len(set(round(v, 3) for v in lons.values())) == 3

    def test_all_longitudes_normalised(self, by_name):
        for p in by_name.values():
            assert 0.0 <= p.sidereal_longitude < 360.0
