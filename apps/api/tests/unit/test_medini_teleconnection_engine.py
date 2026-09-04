"""
AstroOS — Unit Tests for Medini Teleconnection Engine (Vinay Jha 61-Year Waveform)
"""

import pytest
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.medini_teleconnection_engine import MediniTeleconnectionEngine


@pytest.fixture
def teleconnection_engine():
    wrapper = EphemerisWrapper(ephemeris_path="data/ephemeris")
    return MediniTeleconnectionEngine(wrapper)


def test_61_year_waveform_teleconnection_calculation(teleconnection_engine):
    """Calculates 61-year climatic waveform and Sapta-Nadi monsoon forecast for 2026."""
    res = teleconnection_engine.compute_teleconnection_forecast(2026, "lahiri")

    assert res.target_year == 2026
    assert res.analogue_year_61 == 1965
    assert res.analogue_year_122 == 1904

    # 2026 Aridra Pravesha weekday is Monday -> Meghadhipati is Moon
    assert res.meghadhipati == "Moon"
    assert res.sasyeshadhipati == "Jupiter"

    # Sapta-Nadi checks
    assert len(res.active_nadis) == 7
    nadi_names = [n.nadi for n in res.active_nadis]
    assert "AMRITA" in nadi_names
    assert "JALA" in nadi_names
    assert "DAHANA" in nadi_names
    assert "VAYU" in nadi_names

    # Monsoon forecast assertions
    assert res.predicted_rainfall_pct_lpa > 100.0
    assert "NORMAL" in res.predicted_monsoon_category or "EXCESS" in res.predicted_monsoon_category
    assert "Vinay Jha" in res.research_citation
    assert "61-Year Waveform" in res.sst_teleconnection_coupling
