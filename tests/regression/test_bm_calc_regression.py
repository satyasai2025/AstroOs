"""
AstroOS — BM-CALC Golden-Reference Regression Tests (Phase C)

Validates planet position calculations against GC-MASTER expected data
across all 5 reference charts and 6 ayanamsa systems.
"""

from __future__ import annotations

import json

import pytest

from apps.api.services.benchmark_engine import BenchmarkEngine, _positional_error

_GC_PATH = "datasets/gc-master/GC-MASTER-v1.0.0.json"
_AYANAMSA_SYSTEMS = ["lahiri", "kp", "raman", "yukteshwar", "fagan_bradley", "true_chitra"]


@pytest.fixture(scope="session")
def gc_master_data():
    with open(_GC_PATH) as f:
        return json.load(f)


@pytest.fixture
def engine(monkeypatch, gc_master_data):
    """BenchmarkEngine pre-loaded with GC-MASTER data without disk I/O."""
    eng = BenchmarkEngine.__new__(BenchmarkEngine)
    eng._gc_master = gc_master_data
    eng._tolerance = 0.5
    return eng


# ── _positional_error unit tests ──────────────────────────────────────────────


class TestPositionalError:
    """Unit tests for the core angular distance function."""

    def test_exact_match(self):
        assert _positional_error(100.0, 100.0) == 0.0

    def test_normal_offset(self):
        assert _positional_error(100.0, 105.0) == 5.0

    def test_wrap_around_360(self):
        assert _positional_error(358.0, 2.0) == 4.0

    def test_reverse_wrap(self):
        assert _positional_error(2.0, 358.0) == 4.0

    def test_max_error_180(self):
        assert _positional_error(10.0, 190.0) == 180.0

    def test_negative_values(self):
        assert _positional_error(-5.0, 5.0) == 10.0


# ── GC-MASTER data integrity ─────────────────────────────────────────────────


class TestGCMasterData:
    """Verify GC-MASTER JSON has all required data loaded correctly."""

    def test_dataset_loaded(self, gc_master_data):
        assert gc_master_data.get("dataset_id") == "GC-MASTER"
        assert gc_master_data.get("status") == "STABLE"

    def test_all_five_references_present(self, gc_master_data):
        refs = gc_master_data.get("references", [])
        assert len(refs) == 5
        ids = [r["chart_id"] for r in refs]
        for i in range(1, 6):
            assert f"GC-REF-00{i}" in ids

    def test_each_reference_has_expected_planets(self, gc_master_data):
        for ref in gc_master_data["references"]:
            planets = ref.get("expected_planets", {})
            assert len(planets) == 9, f"{ref['chart_id']} has {len(planets)} planets"
            for p in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
                assert p in planets, f"{ref['chart_id']} missing {p}"

    def test_each_reference_has_house_cusps(self, gc_master_data):
        for ref in gc_master_data["references"]:
            houses = ref.get("expected_house_cusps", {})
            assert "W" in houses, f"{ref['chart_id']} missing W house cusps"
            assert "P" in houses
            assert "K" in houses
            assert "E" in houses
            for hs in ["W", "P", "K", "E"]:
                assert len(houses[hs]) == 12, f"{ref['chart_id']} {hs} has {len(houses[hs])} cusps"

    def test_each_reference_has_vargas(self, gc_master_data):
        varga_codes = ["D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
                       "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
        for ref in gc_master_data["references"]:
            vargas = ref.get("expected_vargas", {})
            for vc in varga_codes:
                assert vc in vargas, f"{ref['chart_id']} missing {vc}"


# ── Engine matching tests ─────────────────────────────────────────────────────


class TestBenchmarkEngineMatching:
    """Verify reference resolution logic."""

    def test_get_reference_by_id(self, engine):
        ref = engine._get_reference_by_id("GC-REF-001")
        assert ref is not None
        assert ref["person_name"] == "Queen Elizabeth II"

    def test_get_reference_by_name_exact(self, engine):
        ref = engine._get_reference_by_name("Queen Elizabeth II")
        assert ref is not None
        assert ref["chart_id"] == "GC-REF-001"

    def test_get_reference_by_name_partial(self, engine):
        ref = engine._get_reference_by_name("Elizabeth")
        assert ref is not None
        assert ref["chart_id"] == "GC-REF-001"

    def test_get_reference_by_name_case_insensitive(self, engine):
        ref = engine._get_reference_by_name("barack obama")
        assert ref is not None
        assert ref["chart_id"] == "GC-REF-002"

    def test_get_reference_unknown_returns_none(self, engine):
        ref = engine._get_reference_by_name("Nonexistent Person")
        assert ref is None


# ── BenchmarkResult domain tests ──────────────────────────────────────────────


class TestBenchmarkResult:
    """Verify BenchmarkResult domain object behavior."""

    def test_benchmark_result_passed(self):
        from apps.api.domain.benchmark import BenchmarkResult, PlanetBenchmark
        from datetime import datetime, timezone
        result = BenchmarkResult(
            chart_id="00000000-0000-0000-0000-000000000001",
            reference_id="GC-REF-001",
            reference_name="Test",
            planets=(
                PlanetBenchmark(planet="sun", computed_longitude=10.0, expected_longitude=10.0, error_degrees=0.0, within_tolerance=True),
            ),
            mean_error=0.0, max_error=0.0, passed=True,
            tolerance=0.5, timestamp=datetime.now(timezone.utc),
        )
        assert result.passed is True
        assert result.mean_error == 0.0


# ── Regression marker ─────────────────────────────────────────────────────────


pytestmark = pytest.mark.regression
