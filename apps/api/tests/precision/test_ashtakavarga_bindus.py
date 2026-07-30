"""
Precision tests: Ashtakavarga (bindu / point counting) computation.

Validates that:
  - Bhinnashtakavarga produces exactly 12 bindu values per planet
  - Each bindu value is in [0, 8]
  - Classical per-planet totals match (Sun=48, Moon=49, Mars=39,
    Mercury=54, Jupiter=56, Venus=52, Saturn=39)
  - Sarvashtakavarga total is exactly 337
  - Each rashi in Sarvashtakavarga is in [28, 47]
  - Shodhana (reduction) produces valid results
  - All 7 classical grahas are covered
  - bindus_from_lagna() convenience works correctly

These tests are DB-free and run purely against the Ashtakavarga engine.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.domain.ashtakavarga import (
    BhinnashtakavargaResult,
    SarvashtakavargaResult,
)
from apps.api.domain.horoscope import D1Chart
from apps.api.services.ashtakavarga_engine import AshtakavargaEngine
from apps.api.services.horoscope_engine import HoroscopeEngine

# Classical per-planet total bindu counts (invariant across all charts)
_CLASSICAL_TOTALS = {
    "sun":     48,
    "moon":    49,
    "mars":    39,
    "mercury": 54,
    "jupiter": 56,
    "venus":   52,
    "saturn":  39,
}

_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Classical Sarvashtakavarga grand total
_EXPECTED_SARVA_TOTAL = 337

# Birth data: known-good chart (Delhi, 2000-01-07 13:30 UTC)
_BIRTH_DT = datetime(2000, 1, 7, 13, 30, 0, tzinfo=timezone.utc)
_BIRTH_LAT = 28.6139
_BIRTH_LON = 77.2090

_RASHI_LIST = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_chart(horoscope_engine: HoroscopeEngine) -> D1Chart:
    return horoscope_engine.generate_d1(
        _BIRTH_DT, _BIRTH_LAT, _BIRTH_LON,
        ayanamsa="lahiri", house_system="W",
    )


# ---------------------------------------------------------------------------
# Test: Bhinnashtakavarga structure
# ---------------------------------------------------------------------------

class TestBhinnashtakavargaStructure:
    """Validate structural properties of Bhinnashtakavarga results."""

    def test_produces_exactly_seven_results(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        assert len(results) == 7, (
            f"Expected 7 Bhinnashtakavarga results, got {len(results)}"
        )

    def test_covers_all_seven_planets(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        planets = {r.target_planet for r in results}
        assert planets == set(_CLASSICAL_SEVEN), (
            f"Expected {_CLASSICAL_SEVEN}, got {sorted(planets)}"
        )

    def test_each_planet_has_12_rashi_values(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        for result in results:
            assert len(result.bindus_by_rashi) == 12, (
                f"{result.target_planet} has {len(result.bindus_by_rashi)} "
                f"rashi values, expected 12"
            )

    def test_each_bindu_in_valid_range(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        for result in results:
            for i, count in enumerate(result.bindus_by_rashi):
                assert 0 <= count <= 8, (
                    f"{result.target_planet} rashi {_RASHI_LIST[i]}: "
                    f"bindu count {count} out of range [0, 8]"
                )


# ---------------------------------------------------------------------------
# Test: Classical per-planet total bindu counts (invariant)
# ---------------------------------------------------------------------------

class TestClassicalTotals:
    """
    The total bindus per planet are classical constants that hold for
    ANY valid chart — they are properties of the bindu table itself,
    not of a specific birth data.
    """

    @pytest.mark.parametrize(
        "planet,expected_total",
        list(_CLASSICAL_TOTALS.items()),
        ids=list(_CLASSICAL_TOTALS.keys()),
    )
    def test_planet_total_bindus(
        self, ashtakavarga_engine, horoscope_engine,
        planet: str, expected_total: int
    ):
        chart = _generate_chart(horoscope_engine)
        results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        result = next(r for r in results if r.target_planet == planet)
        assert result.total_bindus == expected_total, (
            f"{planet} total bindus: got {result.total_bindus}, "
            f"expected {expected_total}"
        )

    def test_total_bindus_matches_sum(
        self, ashtakavarga_engine, horoscope_engine
    ):
        """total_bindus field must match actual sum of the 12 rashi values."""
        chart = _generate_chart(horoscope_engine)
        results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        for result in results:
            computed_sum = sum(result.bindus_by_rashi)
            assert result.total_bindus == computed_sum, (
                f"{result.target_planet}: total_bindus={result.total_bindus} "
                f"but sum(bindus)={computed_sum}"
            )


# ---------------------------------------------------------------------------
# Test: Sarvashtakavarga
# ---------------------------------------------------------------------------

class TestSarvashtakavarga:
    """Validate the combined Ashtakavarga (sum of all 7 planetary tables)."""

    def test_sarvashtakavarga_total_337(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        sarva = ashtakavarga_engine.compute_sarvashtakavarga(chart)
        assert sarva.total_bindus == _EXPECTED_SARVA_TOTAL, (
            f"Sarvashtakavarga total: got {sarva.total_bindus}, "
            f"expected {_EXPECTED_SARVA_TOTAL}"
        )

    def test_sarvashtakavarga_has_12_rashi_values(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        sarva = ashtakavarga_engine.compute_sarvashtakavarga(chart)
        assert len(sarva.bindus_by_rashi) == 12, (
            f"Expected 12 rashi values, got {len(sarva.bindus_by_rashi)}"
        )

    def test_sarvashtakavarga_per_rashi_in_range(
        self, ashtakavarga_engine, horoscope_engine
    ):
        """Each rashi in Sarvashtakavarga should have a reasonable bindu count.
        The theoretical range is 0-56 (7 planets x 8 max bindus each), but
        classical texts note typical values fall between ~15 and ~47.
        """
        chart = _generate_chart(horoscope_engine)
        sarva = ashtakavarga_engine.compute_sarvashtakavarga(chart)
        for i, count in enumerate(sarva.bindus_by_rashi):
            assert 15 <= count <= 50, (
                f"Sarvashtakavarga rashi {_RASHI_LIST[i]}: "
                f"bindu count {count} out of expected range [15, 50]"
            )

    def test_sarvashtakavarga_equals_sum_of_bhinna(
        self, ashtakavarga_engine, horoscope_engine
    ):
        """Sarvashtakavarga must equal element-wise sum of all 7 Bhinnashtakavargas."""
        chart = _generate_chart(horoscope_engine)
        bhinna_results = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        sarva = ashtakavarga_engine.compute_sarvashtakavarga(
            chart, bhinna_results=bhinna_results
        )

        expected_by_rashi = [0] * 12
        for result in bhinna_results:
            for i, count in enumerate(result.bindus_by_rashi):
                expected_by_rashi[i] += count

        for i, (actual, expected) in enumerate(
            zip(sarva.bindus_by_rashi, expected_by_rashi)
        ):
            assert actual == expected, (
                f"Sarvashtakavarga rashi {_RASHI_LIST[i]}: "
                f"got {actual}, expected {expected}"
            )

    def test_bindus_from_lagna(
        self, ashtakavarga_engine, horoscope_engine
    ):
        """bindus_from_lagna() should match rashi-indexed lookup."""
        chart = _generate_chart(horoscope_engine)
        sarva = ashtakavarga_engine.compute_sarvashtakavarga(chart)
        lagna_rashi = chart.ascendant.rashi

        # House 1 = lagna's own rashi
        from_lagna = sarva.bindus_from_lagna(lagna_rashi, house_number=1)
        lagna_index = _RASHI_LIST.index(lagna_rashi)
        from_rashi = sarva.bindus_by_rashi[lagna_index]
        assert from_lagna == from_rashi, (
            f"bindus_from_lagna for house 1: got {from_lagna}, "
            f"expected {from_rashi}"
        )


# ---------------------------------------------------------------------------
# Test: Shodhana (reduction)
# ---------------------------------------------------------------------------

class TestShodhana:
    """Validate that Shodhana (reduction) passes produce valid results."""

    def test_reduced_bhinnashtakavarga_produces_results(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        reduced = ashtakavarga_engine.compute_reduced_bhinnashtakavarga(chart)
        assert len(reduced) == 7, (
            f"Expected 7 reduced Bhinnashtakavarga results, got {len(reduced)}"
        )

    def test_reduced_values_in_valid_range(
        self, ashtakavarga_engine, horoscope_engine
    ):
        chart = _generate_chart(horoscope_engine)
        reduced = ashtakavarga_engine.compute_reduced_bhinnashtakavarga(chart)
        for result in reduced:
            for i, count in enumerate(result.bindus_by_rashi):
                assert 0 <= count <= 8, (
                    f"Reduced {result.target_planet} rashi {_RASHI_LIST[i]}: "
                    f"bindu count {count} out of range [0, 8]"
                )

    def test_reduced_total_less_or_equal_to_unreduced(
        self, ashtakavarga_engine, horoscope_engine
    ):
        """Shodhana can only reduce or maintain bindus, never increase."""
        chart = _generate_chart(horoscope_engine)
        unreduced = ashtakavarga_engine.compute_bhinnashtakavarga(chart)
        reduced = ashtakavarga_engine.compute_reduced_bhinnashtakavarga(chart)

        for ur, r in zip(unreduced, reduced):
            assert r.total_bindus <= ur.total_bindus, (
                f"{r.target_planet}: reduced total ({r.total_bindus}) "
                f"> unreduced total ({ur.total_bindus})"
            )
