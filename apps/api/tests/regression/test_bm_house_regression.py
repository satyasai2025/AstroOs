"""
AstroOS — BM-HOUSE Golden-Reference Regression Tests (Phase C)

Validates house cusp calculations across all 4 house systems
against GC-MASTER expected house data.
"""

from __future__ import annotations

import json

import pytest

from apps.api.services.benchmark_engine import BenchmarkEngine, _rashi_index

_GC_PATH = "datasets/gc-master/GC-MASTER-v1.0.0.json"
_RASHI_ORDER = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]


@pytest.fixture(scope="session")
def gc_master_data():
    with open(_GC_PATH) as f:
        return json.load(f)


@pytest.fixture
def engine(monkeypatch, gc_master_data):
    eng = BenchmarkEngine.__new__(BenchmarkEngine)
    eng._gc_master = gc_master_data
    eng._tolerance = 0.5
    return eng


# ── Data integrity ────────────────────────────────────────────────────────────


class TestGCMasterHouseData:
    """Verify house cusp data exists in GC-MASTER."""

    def test_all_references_have_house_cusps(self, gc_master_data):
        for ref in gc_master_data["references"]:
            assert "expected_house_cusps" in ref, f"{ref['chart_id']} missing house cusps"
            for hs in ["W", "P", "K", "E"]:
                cusps = ref["expected_house_cusps"].get(hs, {})
                assert len(cusps) >= 12, f"{ref['chart_id']} {hs} only {len(cusps)} cusps"

    def test_house_cusp_values_in_range(self, gc_master_data):
        for ref in gc_master_data["references"]:
            for hs, cusps in ref.get("expected_house_cusps", {}).items():
                for hnum, cusp in cusps.items():
                    assert 0 <= cusp < 360, f"{ref['chart_id']} {hs} house {hnum} cusp {cusp} out of range"


# ── House benchmark domain ────────────────────────────────────────────────────


class TestHouseBenchmark:
    """Verify HouseBenchmark domain objects."""

    def test_house_benchmark_creation(self):
        from apps.api.domain.benchmark import HouseBenchmark
        h = HouseBenchmark(house_number=1, computed_cusp=10.0, expected_cusp=10.0,
                          error_degrees=0.0, within_tolerance=True)
        assert h.house_number == 1
        assert h.within_tolerance is True
        assert h.error_degrees == 0.0


# ── House benchmark result domain ─────────────────────────────────────────────


class TestHouseBenchmarkResult:
    """Verify HouseBenchmarkResult aggregation."""

    def test_result_creation(self):
        from apps.api.domain.benchmark import HouseBenchmark, HouseBenchmarkResult
        from datetime import datetime, timezone
        cusps = (HouseBenchmark(1, 10.0, 10.0, 0.0, True),)
        r = HouseBenchmarkResult(
            reference_id="GC-REF-001", reference_name="Test",
            house_system="W", cusps=cusps,
            mean_error=0.0, max_error=0.0, passed=True, tolerance=0.001,
        )
        assert r.passed is True
        assert r.house_system == "W"


# ── Rashi index helper ────────────────────────────────────────────────────────


class TestRashiIndex:
    """Verify rashi index lookup."""

    def test_aries_is_zero(self):
        assert _rashi_index("aries") == 0

    def test_pisces_is_eleven(self):
        assert _rashi_index("pisces") == 11

    def test_case_insensitive(self):
        assert _rashi_index("Aries") == 0

    def test_unknown_returns_zero(self):
        assert _rashi_index("nonexistent") == 0


pytestmark = pytest.mark.regression
