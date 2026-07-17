"""
AstroOS — Shadbala Engine Integration Tests (Module 9 Phase 1)

Exercises ShadbalaEngine against real chart data computed by
EphemerisWrapper (Moshier fallback, same pattern as
test_aspect_engine_integration.py and test_yoga_engine_integration.py —
no live .se1 files required).
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.shadbala_engine import ShadbalaEngine

_EPHE_PATH = "data/ephemeris"
_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
_LAT = 28.6139
_LON = 77.2090

_CLASSICAL_SEVEN = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def real_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )


def test_all_three_phase1_components_computed(real_chart):
    engine = ShadbalaEngine()
    components = engine.compute_phase1_components(real_chart)
    assert set(components.keys()) == {"naisargika_bala", "dig_bala", "drik_bala"}


def test_every_component_covers_all_7_classical_grahas(real_chart):
    engine = ShadbalaEngine()
    components = engine.compute_phase1_components(real_chart)
    for name, results in components.items():
        planets = {r.planet for r in results}
        assert planets == _CLASSICAL_SEVEN, f"{name} missing planets: {_CLASSICAL_SEVEN - planets}"


def test_naisargika_bala_identical_across_different_charts():
    """Naisargika Bala is chart-independent — must be identical regardless of birth data."""
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    engine = ShadbalaEngine()

    chart_a = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    chart_b = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        latitude=40.7128, longitude=-74.0060,
    )

    naisargika_a = {r.planet: r.value_shashtiamsas for r in engine.compute_phase1_components(chart_a)["naisargika_bala"]}
    naisargika_b = {r.planet: r.value_shashtiamsas for r in engine.compute_phase1_components(chart_b)["naisargika_bala"]}
    assert naisargika_a == naisargika_b


def test_dig_bala_varies_across_different_charts():
    """Unlike Naisargika, Dig Bala IS chart-dependent — different charts should generally differ."""
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    engine = ShadbalaEngine()

    chart_a = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    chart_b = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        latitude=40.7128, longitude=-74.0060,
    )

    dig_a = {r.planet: r.value_shashtiamsas for r in engine.compute_phase1_components(chart_a)["dig_bala"]}
    dig_b = {r.planet: r.value_shashtiamsas for r in engine.compute_phase1_components(chart_b)["dig_bala"]}
    assert dig_a != dig_b


def test_deterministic_across_repeated_calls(real_chart):
    engine = ShadbalaEngine()
    first = engine.compute_phase1_components(real_chart)
    second = engine.compute_phase1_components(real_chart)
    assert first == second


def test_all_dig_bala_values_within_valid_range(real_chart):
    engine = ShadbalaEngine()
    components = engine.compute_phase1_components(real_chart)
    for r in components["dig_bala"]:
        assert 0.0 <= r.value_shashtiamsas <= 60.0


def test_engine_reports_incomplete_status_honestly(real_chart):
    """The engine must never silently imply completeness it doesn't have."""
    engine = ShadbalaEngine()
    assert len(engine.implemented_components()) == 15
    assert len(engine.not_yet_implemented_components()) == 1
    assert "sthana_bala.saptavargaja_bala" in engine.implemented_components()
    assert "kala_bala.tribhaga_bala" in engine.implemented_components()
    assert "kala_bala.ayana_bala" in engine.implemented_components()
    assert "sthana_bala.ojayugmarasyamsa_bala" in engine.implemented_components()
    assert "kala_bala.nathonnata_bala" in engine.implemented_components()
    assert "kala_bala.dina_hora_bala" in engine.implemented_components()
    assert "kala_bala.yuddha_bala" in engine.implemented_components()
    assert "kala_bala.varsha_masa_lord" in engine.not_yet_implemented_components()


def test_compute_ojayugmarasyamsa_bala_requires_divisional_engine(real_chart):
    """Without a divisional_engine at construction, this must fail loudly, not silently."""
    engine = ShadbalaEngine()  # no divisional_engine wired
    with pytest.raises(RuntimeError):
        engine.compute_ojayugmarasyamsa_bala(
            real_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
        )


def test_compute_ojayugmarasyamsa_bala_works_when_wired(wrapper, real_chart):
    from apps.api.services.divisional_engine import DivisionalEngine

    engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper))
    results = engine.compute_ojayugmarasyamsa_bala(
        real_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    assert len(results) == 7
    assert "sthana_bala.ojayugmarasyamsa_bala" in engine.implemented_components()


def test_phase2_components_computed(real_chart):
    engine = ShadbalaEngine()
    components = engine.compute_phase2_components(real_chart)
    assert set(components.keys()) == {"chesta_bala", "paksha_bala", "ayana_bala", "yuddha_bala"}
    # Chesta Bala applies to 5 planets (not Sun/Moon)
    assert len(components["chesta_bala"]) == 5
    # Paksha Bala and Ayana Bala apply to all 7 classical grahas
    assert len(components["paksha_bala"]) == 7
    assert len(components["ayana_bala"]) == 7
    # Yuddha Bala applies to the 5 non-luminary grahas
    assert len(components["yuddha_bala"]) == 5


def test_sthana_bala_components_computed(real_chart):
    engine = ShadbalaEngine()
    components = engine.compute_sthana_bala_components(real_chart)
    assert set(components.keys()) == {"uchcha_bala", "kendradi_bala", "drekkana_bala"}
    assert len(components["uchcha_bala"]) == 7
    assert len(components["kendradi_bala"]) == 7
    assert len(components["drekkana_bala"]) == 7


def test_compute_saptavargaja_bala_requires_divisional_engine(real_chart):
    """Without a divisional_engine at construction, this must fail loudly, not silently."""
    engine = ShadbalaEngine()  # no divisional_engine wired
    with pytest.raises(RuntimeError):
        engine.compute_saptavargaja_bala(
            real_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
        )


def test_compute_saptavargaja_bala_works_when_wired(wrapper, real_chart):
    from apps.api.services.divisional_engine import DivisionalEngine

    engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper))
    results = engine.compute_saptavargaja_bala(
        real_chart, birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )
    assert len(results) == 7
    assert "sthana_bala.saptavargaja_bala" in engine.implemented_components()


def test_compute_tribhaga_bala_requires_ephemeris_wrapper(real_chart):
    """Without an ephemeris_wrapper at construction, this must fail loudly, not silently."""
    engine = ShadbalaEngine()  # no ephemeris_wrapper wired
    with pytest.raises(RuntimeError):
        engine.compute_tribhaga_bala(real_chart, latitude=_LAT, longitude=_LON)


def test_compute_tribhaga_bala_works_when_wired(wrapper, real_chart):
    engine = ShadbalaEngine(ephemeris_wrapper=wrapper)
    results = engine.compute_tribhaga_bala(real_chart, latitude=_LAT, longitude=_LON)
    assert len(results) == 7
    assert "kala_bala.tribhaga_bala" in engine.implemented_components()


def test_compute_nathonnata_bala_requires_ephemeris_wrapper(real_chart):
    """Without an ephemeris_wrapper at construction, this must fail loudly, not silently."""
    engine = ShadbalaEngine()  # no ephemeris_wrapper wired
    with pytest.raises(RuntimeError):
        engine.compute_nathonnata_bala(real_chart, latitude=_LAT, longitude=_LON)


def test_compute_nathonnata_bala_works_when_wired(wrapper, real_chart):
    engine = ShadbalaEngine(ephemeris_wrapper=wrapper)
    results = engine.compute_nathonnata_bala(real_chart, latitude=_LAT, longitude=_LON)
    assert len(results) == 7
    assert "kala_bala.nathonnata_bala" in engine.implemented_components()


def test_compute_dina_hora_bala_requires_ephemeris_wrapper(real_chart):
    """Without an ephemeris_wrapper at construction, this must fail loudly, not silently."""
    engine = ShadbalaEngine()
    with pytest.raises(RuntimeError):
        engine.compute_dina_hora_bala(real_chart, latitude=_LAT, longitude=_LON)


def test_compute_dina_hora_bala_works_when_wired(wrapper, real_chart):
    engine = ShadbalaEngine(ephemeris_wrapper=wrapper)
    results = engine.compute_dina_hora_bala(real_chart, latitude=_LAT, longitude=_LON)
    assert len(results) == 7
    assert "kala_bala.dina_hora_bala" in engine.implemented_components()
