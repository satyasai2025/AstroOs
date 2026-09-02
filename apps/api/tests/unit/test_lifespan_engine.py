import pytest
from datetime import datetime, timezone

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.lifespan_engine import LifespanEngine


@pytest.fixture
def ephem_wrapper():
    return EphemerisWrapper(ephemeris_path="data/ephemeris")


@pytest.fixture
def lifespan_engine(ephem_wrapper):
    return LifespanEngine(ephem_wrapper)


def test_lifespan_engine_computes_pindayu_amshayu_nisargayu(ephem_wrapper, lifespan_engine):
    birth_dt = datetime(1990, 5, 15, 10, 30, 0, tzinfo=timezone.utc)
    chart = ephem_wrapper.calculate(birth_dt, 28.6139, 77.2090, "lahiri", "W")

    # 1. Pindayu
    pindayu = lifespan_engine.calculate_pindayu(chart)
    assert pindayu.method_name == "Pindayu"
    assert len(pindayu.planetary_contributions) == 7
    assert pindayu.total_years > 10.0
    assert pindayu.category in ("ALPAYU", "MADHYAYU", "PURNAYU")

    # 2. Nisargayu
    nisargayu = lifespan_engine.calculate_nisargayu(chart)
    assert nisargayu.method_name == "Nisargayu"
    assert len(nisargayu.planetary_contributions) == 7
    assert nisargayu.total_years > 10.0
    assert nisargayu.category in ("ALPAYU", "MADHYAYU", "PURNAYU")

    # 3. Amshayu
    amshayu = lifespan_engine.calculate_amshayu(chart)
    assert amshayu.method_name == "Amshayu"
    assert len(amshayu.planetary_contributions) == 7
    assert amshayu.total_years > 10.0
    assert amshayu.category in ("ALPAYU", "MADHYAYU", "PURNAYU")

    # 4. Maraka & D30 Evaluation
    maraka_eval = lifespan_engine.evaluate_marakas_and_d30(chart)
    assert len(maraka_eval.primary_maraka_lords) >= 1
    assert maraka_eval.badhaka_house in (7, 9, 11)
    assert isinstance(maraka_eval.is_saturn_maraka_absorber, bool)
    assert len(maraka_eval.high_risk_dasha_lords) >= 1
    assert 0.0 <= maraka_eval.vulnerability_index <= 10.0

    # 5. Tri-Lifespan Synthesis
    synthesis = lifespan_engine.calculate_tri_lifespan_synthesis(chart)
    assert synthesis.mean_lifespan_years == round((pindayu.total_years + nisargayu.total_years + amshayu.total_years) / 3.0, 2)
    assert synthesis.consensus_category in ("ALPAYU", "MADHYAYU", "PURNAYU")
    assert len(synthesis.shastric_notes) >= 4
