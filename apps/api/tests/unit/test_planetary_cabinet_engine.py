"""
AstroOS — Unit Tests for Planetary Cabinet Engine (Nava Nayakas)
"""

import pytest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.mundane_ingress_engine import MundaneIngressEngine
from apps.api.services.planetary_cabinet_engine import PlanetaryCabinetEngine


@pytest.fixture
def cabinet_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    ingress_engine = MundaneIngressEngine(wrapper)
    return PlanetaryCabinetEngine(ingress_engine)


def test_planetary_cabinet_nava_nayakas_calculation(cabinet_engine):
    """Calculates all 9 cosmic ministers for 2026."""
    cabinet = cabinet_engine.calculate_cabinet(2026, "lahiri")

    assert cabinet.year == 2026
    assert len(cabinet.ministers) == 9
    portfolios = [m.portfolio for m in cabinet.ministers]
    assert any("Raja" in p for p in portfolios)
    assert any("Mantri" in p for p in portfolios)
    assert any("Senadhipati" in p for p in portfolios)
    assert any("Meghadhipati" in p for p in portfolios)

    assert cabinet.overall_balance_score >= 0.0
    assert len(cabinet.governance_climate) > 0
    assert "Brihat Samhita" in cabinet.classical_summary
