"""
AstroOS — Jaimini Internal Consistency Validation Unit Tests
"""

import dataclasses
from datetime import date

import pytest

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.services.arudha_engine import ArudhaEngine
from apps.api.services.jaimini_engine import CharaKarakaEngine
from apps.api.services.jaimini_validation import (
    ArudhaValidationError,
    CharaKarakaValidationError,
    DashaValidationError,
    validate_arudha_result,
    validate_chara_karaka_result,
    validate_dasha_tree,
    validate_sign_indexing,
)
from apps.api.tests.unit.jaimini_fixtures import make_d1_chart, make_planet

_ALL_PLANETS = [
    make_planet(p, "aries", d)
    for p, d in [
        ("sun", 25.0), ("moon", 10.0), ("mars", 5.0), ("mercury", 20.0),
        ("jupiter", 15.0), ("venus", 8.0), ("saturn", 3.0), ("rahu", 12.0), ("ketu", 12.0),
    ]
]


def test_validate_sign_indexing_passes():
    validate_sign_indexing()  # no exception = pass


def test_validate_chara_karaka_result_passes_on_real_output():
    chart = make_d1_chart("aries", _ALL_PLANETS)
    result = CharaKarakaEngine().compute(chart, scheme="ashta_karaka")
    validate_chara_karaka_result(result)  # no exception = pass


def test_validate_chara_karaka_result_catches_wrong_count():
    chart = make_d1_chart("aries", _ALL_PLANETS)
    result = CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
    corrupted = dataclasses.replace(result, karakas=result.karakas[:-1])
    with pytest.raises(CharaKarakaValidationError) as exc_info:
        validate_chara_karaka_result(corrupted)
    assert exc_info.value.rule == "chara_karaka.count"


def test_validate_chara_karaka_result_catches_duplicate_planet():
    chart = make_d1_chart("aries", _ALL_PLANETS)
    result = CharaKarakaEngine().compute(chart, scheme="sapta_karaka")
    karakas = list(result.karakas)
    karakas[1] = dataclasses.replace(karakas[1], planet=karakas[0].planet)
    corrupted = dataclasses.replace(result, karakas=tuple(karakas))
    with pytest.raises(CharaKarakaValidationError) as exc_info:
        validate_chara_karaka_result(corrupted)
    assert exc_info.value.rule == "chara_karaka.duplicate_planet"


def test_validate_arudha_result_passes_on_real_output():
    chart = make_d1_chart("aries", _ALL_PLANETS)
    result = ArudhaEngine().compute(chart)
    validate_arudha_result(result)  # no exception = pass


def test_validate_arudha_result_catches_broken_exception_invariant():
    chart = make_d1_chart("aries", _ALL_PLANETS)
    result = ArudhaEngine().compute(chart)
    padas = list(result.padas)
    # Force an inconsistency: mark exception_applied True without shifting rashi.
    padas[0] = dataclasses.replace(padas[0], exception_applied=True, rashi=padas[0].raw_rashi)
    corrupted = dataclasses.replace(result, padas=tuple(padas))
    with pytest.raises(ArudhaValidationError) as exc_info:
        validate_arudha_result(corrupted)
    assert exc_info.value.rule == "arudha.exception_shift"


def test_validate_arudha_result_catches_missing_house():
    chart = make_d1_chart("aries", _ALL_PLANETS)
    result = ArudhaEngine().compute(chart)
    corrupted = dataclasses.replace(result, padas=result.padas[:-1])
    with pytest.raises(ArudhaValidationError) as exc_info:
        validate_arudha_result(corrupted)
    assert exc_info.value.rule == "arudha.house_coverage"


def _make_tree(periods):
    return DashaTree(
        system="chara", birth_date=date(2000, 1, 1), trigger_planet="aries",
        trigger_nakshatra="", trigger_nakshatra_number=0,
        mahadashas=tuple(periods), max_depth=1, total_cycle_years=sum(p.duration_days for p in periods) // 365,
    )


def test_validate_dasha_tree_passes_on_continuous_periods():
    periods = [
        DashaPeriod(lord="aries", start_date=date(2000, 1, 1), end_date=date(2001, 1, 1), duration_days=366, level=1),
        DashaPeriod(lord="taurus", start_date=date(2001, 1, 1), end_date=date(2002, 1, 1), duration_days=365, level=1),
    ]
    validate_dasha_tree(_make_tree(periods))  # no exception = pass


def test_validate_dasha_tree_catches_gap():
    periods = [
        DashaPeriod(lord="aries", start_date=date(2000, 1, 1), end_date=date(2001, 1, 1), duration_days=366, level=1),
        DashaPeriod(lord="taurus", start_date=date(2001, 2, 1), end_date=date(2002, 1, 1), duration_days=334, level=1),
    ]
    with pytest.raises(DashaValidationError) as exc_info:
        validate_dasha_tree(_make_tree(periods))
    assert exc_info.value.rule == "dasha.sequence_continuity"


def test_validate_dasha_tree_catches_duration_mismatch():
    periods = [
        DashaPeriod(lord="aries", start_date=date(2000, 1, 1), end_date=date(2001, 1, 1), duration_days=999, level=1),
    ]
    with pytest.raises(DashaValidationError) as exc_info:
        validate_dasha_tree(_make_tree(periods))
    assert exc_info.value.rule == "dasha.duration_mismatch"


def test_validate_dasha_tree_catches_empty():
    with pytest.raises(DashaValidationError) as exc_info:
        validate_dasha_tree(_make_tree([]))
    assert exc_info.value.rule == "dasha.empty"
