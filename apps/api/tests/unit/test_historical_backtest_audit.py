"""
AstroOS — Historical Backtest & Accuracy Audit Unit Tests
=========================================================

Canonical Reference: docs/JHA_PREDICTION_FRAMEWORK.md (Step 10)
Tests:
1. Multi-Varga Explorer Service (D9, D10, D7, D4, D3, D12, D30).
2. Karakamsha & 7-Chara Karaka Synthesis Engine (Strictly 7 Karakas).
3. Historical Benchmark Empirical Backtest (Narendra Modi 2014/2019, Indira Gandhi 1984, Amitabh Bachchan 1982).
4. Accuracy & False-Positive Rate Assertions.
"""

import pytest
from datetime import date, datetime, timezone

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.phalita_core.divisional_explorer_service import DivisionalExplorerService
from apps.api.services.phalita_core.karakamsha_synthesis_engine import KarakamshaSynthesisEngine
from apps.api.services.phalita_core.historical_backtest_harness import HistoricalBacktestHarness


@pytest.fixture
def ephem_wrapper():
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


def test_divisional_explorer_service(ephem_wrapper):
    """Verify DivisionalExplorerService computes all fields for D9 and D10."""
    service = DivisionalExplorerService(ephem_wrapper)
    dt = datetime(1985, 5, 15, 14, 30, 0, tzinfo=timezone.utc)

    for varga in (9, 10, 7, 4):
        res = service.explore_varga(
            birth_datetime=dt,
            latitude=28.6139,
            longitude=77.2090,
            varga_number=varga,
            target_date=date(2026, 3, 15),
        )
        assert res.varga_number == varga
        assert res.varga_code == f"D{varga}"
        assert len(res.planets) >= 7
        assert res.active_divisional_dasha.mahadasha_lord is not None
        assert res.dual_dasha_comparison.siddhantic_verdict is not None
        assert res.vimshopaka_weight > 0.0


def test_karakamsha_7_chara_karakas(ephem_wrapper):
    """Verify strictly 7 Chara Karakas, AK extraction, and Karakamsha Lagna."""
    # Synthetic longitudes where Sun has highest degree (28.5°) and Saturn lowest (2.1°)
    planet_longitudes = {
        "sun": 28.5,       # 28.5° Aries -> AK
        "moon": 55.2,      # 25.2° Taurus -> AmK
        "mars": 81.0,      # 21.0° Gemini -> BK
        "mercury": 108.4,  # 18.4° Cancer -> MK
        "jupiter": 134.1,  # 14.1° Leo -> PK
        "venus": 160.3,    # 10.3° Virgo -> GK
        "saturn": 182.1,   # 2.1° Libra -> DK
    }
    lagna_lon = 15.0

    res = KarakamshaSynthesisEngine.compute_synthesis(
        d1_planet_longitudes=planet_longitudes,
        d1_lagna_lon=lagna_lon,
    )

    assert res.atmakaraka_planet == "Sun"
    assert len(res.chara_karakas) == 7

    roles = [k.karaka_role for k in res.chara_karakas]
    assert roles == ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]
    assert res.chara_karakas[0].planet == "Sun"
    assert res.chara_karakas[-1].planet == "Saturn"
    assert res.karakamsha_rashi is not None


def test_historical_benchmark_backtest_audit(ephem_wrapper):
    """Run full benchmark audit and verify accuracy >= 80% and false-positive <= 20%."""
    harness = HistoricalBacktestHarness(ephem_wrapper)
    summary = harness.run_benchmark_audit()

    assert summary.total_cases >= 4
    assert summary.passed_cases >= 4
    assert summary.accuracy_percentage >= 80.0
    assert summary.false_positive_rate <= 20.0

    for r in summary.detailed_results:
        assert r.passed, f"Benchmark {r.case_id} ({r.native_name}) failed: computed={r.computed_score}, prob={r.is_probable}"
