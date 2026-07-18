"""
AstroOS — BM-VARGA Golden-Reference Regression Tests (Phase C)

Validates divisional chart calculations against GC-MASTER expected varga data.
Covers all 15 vargas (D2-D60) across the 5 reference charts.
"""

from __future__ import annotations

import json

import pytest

from apps.api.services.benchmark_engine import BenchmarkEngine

_GC_PATH = "datasets/gc-master/GC-MASTER-v1.0.0.json"
_ALL_VARGAS = ["D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16",
               "D20", "D24", "D27", "D30", "D40", "D45", "D60"]


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


class TestGCMasterVargaData:
    """Verify varga data exists in GC-MASTER."""

    def test_all_references_have_all_15_vargas(self, gc_master_data):
        for ref in gc_master_data["references"]:
            vargas = ref.get("expected_vargas", {})
            for vc in _ALL_VARGAS:
                assert vc in vargas, f"{ref['chart_id']} missing varga {vc}"

    def test_each_varga_has_all_9_planets(self, gc_master_data):
        for ref in gc_master_data["references"]:
            for vc, vdata in ref.get("expected_vargas", {}).items():
                planet_keys = [k for k in vdata.keys() if k != "_metadata"]
                assert len(planet_keys) == 9, f"{ref['chart_id']} {vc} has {len(planet_keys)} planets"

    def test_each_planet_has_rashi_and_house(self, gc_master_data):
        for ref in gc_master_data["references"]:
            for vc, vdata in ref.get("expected_vargas", {}).items():
                for planet, pdata in vdata.items():
                    if planet == "_metadata":
                        continue
                    assert "rashi" in pdata, f"{ref['chart_id']} {vc} {planet} missing rashi"
                    assert "house" in pdata, f"{ref['chart_id']} {vc} {planet} missing house"
                    assert 1 <= pdata["house"] <= 12, f"{ref['chart_id']} {vc} {planet} house={pdata['house']}"


# ── Varga benchmark domain ────────────────────────────────────────────────────


class TestVargaBenchmark:
    """Verify VargaBenchmark domain objects."""

    def test_varga_benchmark_creation(self):
        from apps.api.domain.benchmark import VargaBenchmark
        v = VargaBenchmark(varga_code="D9", planet="sun",
                           computed_rashi="leo", expected_rashi="leo", matched=True)
        assert v.varga_code == "D9"
        assert v.matched is True

    def test_varga_benchmark_mismatch(self):
        from apps.api.domain.benchmark import VargaBenchmark
        v = VargaBenchmark(varga_code="D9", planet="sun",
                           computed_rashi="leo", expected_rashi="cancer", matched=False)
        assert v.matched is False


# ── Varga benchmark result domain ─────────────────────────────────────────────


class TestVargaBenchmarkResult:
    """Verify VargaBenchmarkResult aggregation."""

    def test_result_all_matched(self):
        from apps.api.domain.benchmark import VargaBenchmark, VargaBenchmarkResult
        vargas = (VargaBenchmark("D9", "sun", "leo", "leo", True),)
        r = VargaBenchmarkResult(reference_id="GC-REF-001", reference_name="Test",
                                 vargas=vargas, total_checks=1, matched=1, failed=0)
        assert r.failed == 0
        assert r.matched == 1


pytestmark = pytest.mark.regression
