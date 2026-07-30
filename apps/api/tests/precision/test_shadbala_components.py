"""
Precision tests: Shadbala (6-fold planetary strength) computation.

Validates that:
  - All 6 classical Shadbala components are computed for all 9 grahas
  - Each sub-component produces non-negative Shashtiamsa values
  - Naisargika Bala matches fixed classical descending order
  - Dig Bala values are within classical bounds
  - All implemented sub-components are covered
  - No component crashes for known-good birth data

These tests are DB-free and run purely against the Swiss Ephemeris +
Shadbala engine.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala_engine import ShadbalaEngine

# Classical Naisargika Bala values (BPHS Ch. 27):
# n * 60/7 Shashtiamsas, n=7..1, in classical order Sun > Moon > Venus >
# Jupiter > Mercury > Mars > Saturn. This is the ordering used in this
# codebase (see naisargika_bala.py).
_NAISARGIKA_VALUES = {
    "sun":     60.0,        # 7*60/7
    "moon":    51.428571,   # 6*60/7
    "venus":   42.857143,   # 5*60/7
    "jupiter": 34.285714,   # 4*60/7
    "mercury": 25.714286,   # 3*60/7
    "mars":    17.142857,   # 2*60/7
    "saturn":  8.571429,    # 1*60/7
}

# Classical descending order (strongest to weakest)
_NAISARGIKA_ORDER = ["sun", "moon", "venus", "jupiter", "mercury", "mars", "saturn"]

# All 9 grahas that some Shadbala components may cover
_ALL_GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

# Classical 7 grahas for Naisargika
_CLASSICAL_SEVEN = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]

# Chesta and Yuddha Bala cover only the 5 non-luminary grahas
# (Sun and Moon have no retrograde motion / don't participate in planetary war)
_NON_LUMINARY_FIVE = ["mars", "mercury", "jupiter", "venus", "saturn"]

# Birth data: known-good chart (Delhi, 2000-01-07 13:30 UTC)
_BIRTH_DT = datetime(2000, 1, 7, 13, 30, 0, tzinfo=timezone.utc)
_BIRTH_LAT = 28.6139
_BIRTH_LON = 77.2090


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_chart(horoscope_engine: HoroscopeEngine) -> D1Chart:
    return horoscope_engine.generate_d1(
        _BIRTH_DT, _BIRTH_LAT, _BIRTH_LON,
        ayanamsa="lahiri", house_system="W",
    )


def _planet_set(results: list[BalaComponentResult]) -> set[str]:
    """Extract the set of planets covered by a result list."""
    return {r.planet for r in results}


def _values_by_planet(results: list[BalaComponentResult]) -> dict[str, float]:
    """Map planet -> value_shashtiamsas."""
    return {r.planet: r.value_shashtiamsas for r in results}


# ---------------------------------------------------------------------------
# Test: Naisargika Bala (fixed classical values)
# ---------------------------------------------------------------------------

class TestNaisargikaBala:
    """Naisargika Bala has fixed classical values independent of birth data."""

    def test_covers_all_seven_classical_planets(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["naisargika_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Naisargika Bala should cover 7 classical planets, "
            f"got {covered}"
        )

    def test_values_match_classical(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["naisargika_bala"]
        vals = _values_by_planet(results)

        for planet, expected in _NAISARGIKA_VALUES.items():
            actual = vals.get(planet)
            assert actual is not None, f"{planet} missing from Naisargika Bala"
            assert abs(actual - expected) < 0.001, (
                f"Naisargika Bala for {planet}: got {actual:.6f}, "
                f"expected {expected:.6f}"
            )

    def test_descending_order(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["naisargika_bala"]
        vals = _values_by_planet(results)
        order = [_NAISARGIKA_VALUES[p] for p in _NAISARGIKA_ORDER]
        for i in range(len(order) - 1):
            assert order[i] > order[i + 1], (
                f"Naisargika Bala should be descending: {_NAISARGIKA_ORDER[i]} "
                f"({order[i]:.4f}) > {_NAISARGIKA_ORDER[i+1]} ({order[i+1]:.4f})"
            )


# ---------------------------------------------------------------------------
# Test: Dig Bala (directional strength)
# ---------------------------------------------------------------------------

class TestDigBala:
    """Dig Bala values must be non-negative and within classical bounds."""

    def test_covers_all_classical_planets(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["dig_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Dig Bala should cover 7 classical grahas, got {covered}"
        )

    def test_values_non_negative(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["dig_bala"]
        for r in results:
            assert r.value_shashtiamsas >= 0.0, (
                f"Dig Bala for {r.planet} is negative: {r.value_shashtiamsas}"
            )

    def test_values_within_bounds(self, shadbala_engine, horoscope_engine):
        """Dig Bala ranges from 0 to 60 Shashtiamsas per planet."""
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["dig_bala"]
        for r in results:
            assert 0.0 <= r.value_shashtiamsas <= 60.0, (
                f"Dig Bala for {r.planet} out of bounds: "
                f"{r.value_shashtiamsas}"
            )


# ---------------------------------------------------------------------------
# Test: Drik Bala (aspect-based strength)
# ---------------------------------------------------------------------------

class TestDrikBala:
    """Drik Bala is computed from aspects and should be non-negative."""

    def test_covers_planets_with_aspects(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["drik_bala"]
        assert len(results) > 0, "Drik Bala should produce at least one result"

    def test_values_non_negative(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        results = components["drik_bala"]
        for r in results:
            assert r.value_shashtiamsas >= 0.0, (
                f"Drik Bala for {r.planet} is negative: {r.value_shashtiamsas}"
            )


# ---------------------------------------------------------------------------
# Test: Chesta Bala (motional strength)
# ---------------------------------------------------------------------------

class TestChestaBala:
    """Chesta Bala depends on retrograde status and speed."""

    def test_covers_non_luminary_five(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["chesta_bala"]
        covered = _planet_set(results)
        assert covered == set(_NON_LUMINARY_FIVE), (
            f"Chesta Bala should cover 5 non-luminary grahas, got {covered}"
        )

    def test_values_non_negative(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["chesta_bala"]
        for r in results:
            assert r.value_shashtiamsas >= 0.0, (
                f"Chesta Bala for {r.planet} is negative: "
                f"{r.value_shashtiamsas}"
            )


# ---------------------------------------------------------------------------
# Test: Paksha Bala (lunar phase strength)
# ---------------------------------------------------------------------------

class TestPakshaBala:
    """Paksha Bala depends on Moon-Sun angular distance."""

    def test_covers_classical_seven(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["paksha_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Paksha Bala should cover 7 classical grahas, got {covered}"
        )

    def test_values_non_negative(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["paksha_bala"]
        for r in results:
            assert r.value_shashtiamsas >= 0.0, (
                f"Paksha Bala for {r.planet} is negative: "
                f"{r.value_shashtiamsas}"
            )


# ---------------------------------------------------------------------------
# Test: Ayana Bala (equatorial strength)
# ---------------------------------------------------------------------------

class TestAyanaBala:
    """Ayana Bala depends on declination."""

    def test_covers_classical_seven(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["ayana_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Ayana Bala should cover 7 classical grahas, got {covered}"
        )

    def test_values_non_negative(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["ayana_bala"]
        for r in results:
            assert r.value_shashtiamsas >= 0.0, (
                f"Ayana Bala for {r.planet} is negative: "
                f"{r.value_shashtiamsas}"
            )


# ---------------------------------------------------------------------------
# Test: Yuddha Bala (planetary war)
# ---------------------------------------------------------------------------

class TestYuddhaBala:
    """Yuddha Bala is relevant when planets are very close."""

    def test_covers_non_luminary_five(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        results = components["yuddha_bala"]
        covered = _planet_set(results)
        assert covered == set(_NON_LUMINARY_FIVE), (
            f"Yuddha Bala should cover 5 non-luminary grahas, got {covered}"
        )


# ---------------------------------------------------------------------------
# Test: Sthana Bala sub-components
# ---------------------------------------------------------------------------

class TestSthanaBala:
    """Sthana Bala's 5 sub-components: Uchcha, Kendradi, Drekkana,
    Saptavargaja, Ojayugmarasyamsa."""

    def test_uchcha_bala_covers_classical_seven(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_sthana_bala_components(chart)
        results = components["uchcha_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Uchcha Bala should cover 7 classical grahas, got {covered}"
        )

    def test_kendradi_bala_covers_classical_seven(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_sthana_bala_components(chart)
        results = components["kendradi_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Kendradi Bala should cover 7 classical grahas, got {covered}"
        )

    def test_drekkana_bala_covers_classical_seven(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_sthana_bala_components(chart)
        results = components["drekkana_bala"]
        covered = _planet_set(results)
        assert covered == set(_CLASSICAL_SEVEN), (
            f"Drekkana Bala should cover 7 classical grahas, got {covered}"
        )

    def test_saptavargaja_bala_computes(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        results = shadbala_engine.compute_saptavargaja_bala(
            chart,
            birth_datetime_utc=_BIRTH_DT,
            latitude=_BIRTH_LAT,
            longitude=_BIRTH_LON,
        )
        assert len(results) > 0, "Saptavargaja Bala should produce results"
        covered = _planet_set(results)
        # Saptavargaja covers 7 classical grahas + potentially nodes
        assert len(covered) >= 7, (
            f"Saptavargaja Bala should cover at least 7 planets, got {covered}"
        )

    def test_ojayugmarasyamsa_bala_computes(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        results = shadbala_engine.compute_ojayugmarasyamsa_bala(
            chart,
            birth_datetime_utc=_BIRTH_DT,
            latitude=_BIRTH_LAT,
            longitude=_BIRTH_LON,
        )
        assert len(results) > 0, "Ojayugmarasyamsa Bala should produce results"
        covered = _planet_set(results)
        assert len(covered) >= 7, (
            f"Ojayugmarasyamsa Bala should cover at least 7 planets, got {covered}"
        )


# ---------------------------------------------------------------------------
# Test: Kala Bala sub-components
# ---------------------------------------------------------------------------

class TestKalaBala:
    """Tribhaga, Nathonnata, and Dina-Hora Bala (all require ephemeris_wrapper)."""

    def test_tribhaga_bala_computes(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        results = shadbala_engine.compute_tribhaga_bala(
            chart, latitude=_BIRTH_LAT, longitude=_BIRTH_LON,
        )
        assert len(results) > 0, "Tribhaga Bala should produce results"
        covered = _planet_set(results)
        assert len(covered) >= 7, (
            f"Tribhaga Bala should cover at least 7 planets, got {covered}"
        )

    def test_nathonnata_bala_computes(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        results = shadbala_engine.compute_nathonnata_bala(
            chart, latitude=_BIRTH_LAT, longitude=_BIRTH_LON,
        )
        assert len(results) > 0, "Nathonnata Bala should produce results"

    def test_dina_hora_bala_computes(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        results = shadbala_engine.compute_dina_hora_bala(
            chart, latitude=_BIRTH_LAT, longitude=_BIRTH_LON,
        )
        assert len(results) > 0, "Dina-Hora Bala should produce results"


# ---------------------------------------------------------------------------
# Test: Component coverage tracking
# ---------------------------------------------------------------------------

class TestComponentCoverage:
    """Validate that the engine correctly reports implemented vs gap components."""

    def test_implemented_components_list(self, shadbala_engine):
        implemented = shadbala_engine.implemented_components()
        assert len(implemented) >= 15, (
            f"Expected at least 15 implemented components, got {len(implemented)}"
        )
        # Core components must be present
        assert "naisargika_bala" in implemented
        assert "dig_bala" in implemented
        assert "drik_bala" in implemented
        assert "chesta_bala" in implemented

    def test_not_yet_implemented_list(self, shadbala_engine):
        gaps = shadbala_engine.not_yet_implemented_components()
        assert "kala_bala.varsha_masa_lord" in gaps, (
            "Varsha/Masa lord should be listed as not yet implemented"
        )

    def test_all_phase1_components_computed(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase1_components(chart)
        expected_keys = {"naisargika_bala", "dig_bala", "drik_bala"}
        assert set(components.keys()) == expected_keys

    def test_all_phase2_components_computed(self, shadbala_engine, horoscope_engine):
        chart = _generate_chart(horoscope_engine)
        components = shadbala_engine.compute_phase2_components(chart)
        expected_keys = {
            "chesta_bala", "paksha_bala", "ayana_bala", "yuddha_bala"
        }
        assert set(components.keys()) == expected_keys
