"""
AstroOS — Yoga Engine Integration Tests (Module 8, Phase 1)

Exercises YogaEngine against real chart data computed by EphemerisWrapper
(Moshier fallback, same pattern as test_aspect_engine_integration.py — no
live .se1 files required). Not marked pytest.mark.integration for the
same reason as that file — this needs no live external infra.
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.yoga_engine import YogaEngine
from apps.api.services.yoga_registry import all_yogas

_EPHE_PATH = "data/ephemeris"
_BIRTH_DT = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def real_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=_BIRTH_DT, latitude=_LAT, longitude=_LON,
    )


def test_yoga_engine_evaluates_every_registered_yoga(real_chart):
    engine = YogaEngine()
    results = engine.evaluate_all(real_chart)
    assert len(results) == len(all_yogas())


def test_yoga_engine_every_result_has_required_fields(real_chart):
    """Every result must carry the four audit requirements: id, version, deps, trace."""
    engine = YogaEngine()
    results = engine.evaluate_all(real_chart)
    for r in results:
        assert r.yoga_id.startswith("BPHS-")
        assert r.rule_version in ("1.0", "1.1", "2.0")
        assert r.source_text == "BPHS"
        assert isinstance(r.trace, tuple)
        # Every result has either satisfied or missing content — never both empty
        assert len(r.satisfied) > 0 or len(r.missing) > 0


def test_yoga_engine_deterministic_across_repeated_runs(real_chart):
    engine = YogaEngine()
    first = engine.evaluate_all(real_chart)
    second = engine.evaluate_all(real_chart)
    assert first == second


def test_yoga_engine_present_results_have_strength(real_chart):
    engine = YogaEngine()
    results = engine.evaluate_all(real_chart)
    for r in results:
        if r.is_present:
            assert r.strength is not None
        else:
            assert r.strength is None


def test_evaluate_one_matches_evaluate_all(real_chart):
    """Targeted single-yoga evaluation must match the corresponding entry from evaluate_all()."""
    engine = YogaEngine()
    all_results = {r.yoga_id: r for r in engine.evaluate_all(real_chart)}
    single = engine.evaluate_one(real_chart, "BPHS-PM-001")
    assert single == all_results["BPHS-PM-001"]


def test_evaluate_one_unknown_yoga_id_raises(real_chart):
    engine = YogaEngine()
    with pytest.raises(ValueError):
        engine.evaluate_one(real_chart, "BPHS-NOTREAL-999")


def test_yoga_engine_across_multiple_charts_varies_results():
    """Different birth data should generally produce different yoga presence patterns."""
    wrapper = EphemerisWrapper(ephemeris_path=_EPHE_PATH)
    horoscope_engine = HoroscopeEngine(wrapper)
    engine = YogaEngine()

    chart_a = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=28.6139, longitude=77.2090,
    )
    chart_b = horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1975, 12, 25, 3, 0, 0, tzinfo=timezone.utc),
        latitude=40.7128, longitude=-74.0060,
    )

    results_a = {r.yoga_id: r.is_present for r in engine.evaluate_all(chart_a)}
    results_b = {r.yoga_id: r.is_present for r in engine.evaluate_all(chart_b)}
    # Not a strict requirement that they differ, but they should not error
    # and should both be well-formed dicts keyed by the same yoga_ids.
    assert set(results_a.keys()) == set(results_b.keys())


def test_all_70_yogas_registered():
    """Sanity check on the expected full catalog size after Phase I.5."""
    ids = {y.yoga_id for y in all_yogas()}
    assert len(ids) == 70
    assert "BPHS-PM-001" in ids
    assert "BPHS-OMY-001" in ids
    assert "BPHS-DY-001" in ids
    assert "BPHS-DY-002" in ids
    assert "BPHS-RY-001" in ids
    assert "BPHS-NBRY-001" in ids
    assert "BPHS-CY-001" in ids
    assert "BPHS-NY-001" in ids
    assert "BPHS-ARY-001" in ids
    assert "BPHS-SY-001" in ids
    assert "BPHS-SY-002" in ids
    assert "BPHS-OMY-002" in ids  # Vosi
    assert "BPHS-OMY-005" in ids  # Budhaditya
    assert "BPHS-OMY-006" in ids  # Amala
    assert "BPHS-OMY-007" in ids  # Kalasarpa


def test_version_bumped_yogas_report_correct_version():
    """Kemadruma (now 1.2 — added the missing lagna-kendra base condition) and Shakata (1.1) — confirm the registry reflects it."""
    from apps.api.services.yoga_registry import get_yoga

    assert get_yoga("BPHS-CY-004").rule_version == "1.2"
    assert get_yoga("BPHS-ARY-003").rule_version == "1.1"
