"""
Canonical Unit Tests for Missing Chakra & Fusion Engines
=========================================================

Validates:
1. Sapta-Nadi Chakra (SNC) classification, cyclone signatures, and flood signatures.
2. Sudarshana Chakra Dasha (SCD) annual/monthly progressions across LK, SK, and CK.
3. Varga Fusion Engine: Signed combination across D1, D9, D10, D60, Bhāvottama detection, and Vargottama.
"""

from datetime import date, datetime, timezone
import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.sapta_nadi_chakra_engine import (
    SaptaNadiChakraEngine,
    SaptaNadiReport,
)
from apps.api.services.sudarshana_chakra_dasha_engine import (
    SudarshanaChakraDashaEngine,
    SudarshanaChakraDashaReport,
)
from apps.api.services.phalita_core.varga_fusion_engine import (
    VargaFusionEngine,
    VargaFusionReport,
)


@pytest.fixture
def horoscope_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return HoroscopeEngine(wrapper)


@pytest.fixture
def sample_d1_chart(horoscope_engine):
    """Generate D1 chart for Taurus Lagna test case (Vadodara coords)."""
    dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    return horoscope_engine.generate_d1(dt, 22.3072, 73.1812)


def test_sapta_nadi_chakra_evaluation(sample_d1_chart):
    """Verify Sapta-Nadi Chakra evaluation for all 7 planets."""
    snc_engine = SaptaNadiChakraEngine()
    report = snc_engine.evaluate_chart(sample_d1_chart)

    assert isinstance(report, SaptaNadiReport)
    assert report.dominant_nadi in ("chanda", "vata", "vahni", "soumya", "neera", "jala", "amrita")
    assert 0.0 <= report.cyclone_risk_score <= 1.0
    assert 0.0 <= report.flood_risk_score <= 1.0
    assert len(report.planet_nadis) >= 7


def test_sudarshana_chakra_dasha_annual_progression(sample_d1_chart):
    """Verify SCD progression: age 30 -> house 7."""
    scd_engine = SudarshanaChakraDashaEngine()
    birth_dt = datetime(1971, 6, 29, 23, 27, 40, tzinfo=timezone.utc)
    target_d = date(2002, 4, 15)  # Raj's marriage (Age ~30.8) -> 30 years elapsed -> Year 31 -> House 7

    report = scd_engine.compute_scd(sample_d1_chart, birth_dt, target_d)
    assert isinstance(report, SudarshanaChakraDashaReport)
    assert report.annual_house_offset == 7  # 7th House of Marriage active!
    assert report.scd_cycle_number == 3      # 3rd 12-year cycle
    assert report.lk_annual.active_house_num == 7
    assert -1.0 <= report.composite_scd_score <= 1.0


def test_varga_fusion_engine_computation(sample_d1_chart):
    """Verify signed varga fusion across D1, D9, D10, D60."""
    varga_engine = VargaFusionEngine()
    report = varga_engine.evaluate_vargas(sample_d1_chart)

    assert isinstance(report, VargaFusionReport)
    assert len(report.planet_statuses) >= 7
    assert "career" in report.fused_domain_scores
    assert "marriage" in report.fused_domain_scores
    assert "wealth" in report.fused_domain_scores
    assert -1.0 <= report.overall_varga_harmony <= 1.0
    for domain, score in report.fused_domain_scores.items():
        assert -1.0 <= score <= 1.0
