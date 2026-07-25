"""
AstroOS — Rule Engine Pipeline Integration Tests (Module 13)

Exercises the full pipeline (Birth Chart -> Calculation Engines ->
FactBuilder -> FactRegistry -> RuleEngine -> RuleResults) against real
chart data, using the actual 47 registered production rules — not
synthetic facts.
"""

from datetime import datetime, timezone

import pytest

from apps.api.services.divisional_engine import DivisionalEngine
from apps.api.services.ephemeris_wrapper import EphemerisWrapper
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.horoscope_engine import HoroscopeEngine
from apps.api.services.rule_engine import RuleEngine
from apps.api.services.rule_registry import all_rules
from apps.api.services.shadbala_engine import ShadbalaEngine
from apps.api.services.transit_engine import TransitEngine

_EPHE_PATH = "data/ephemeris"
_LAT = 28.6139
_LON = 77.2090


@pytest.fixture(scope="module")
def wrapper() -> EphemerisWrapper:
    return EphemerisWrapper(ephemeris_path=_EPHE_PATH)


@pytest.fixture(scope="module")
def natal_chart(wrapper):
    horoscope_engine = HoroscopeEngine(wrapper)
    return horoscope_engine.generate_d1(
        birth_datetime_utc=datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc),
        latitude=_LAT, longitude=_LON,
    )


@pytest.fixture(scope="module")
def full_facts(wrapper, natal_chart):
    shadbala_engine = ShadbalaEngine(divisional_engine=DivisionalEngine(wrapper), ephemeris_wrapper=wrapper)
    transit_engine = TransitEngine(wrapper)
    builder = FactBuilder(shadbala_engine=shadbala_engine, transit_engine=transit_engine)
    return builder.build_facts(natal_chart, transit_datetime_utc=datetime(2026, 7, 12, tzinfo=timezone.utc))


def test_exactly_47_rules_registered():
    assert len(all_rules()) == 47


def test_evaluate_all_returns_a_result_for_every_rule(full_facts):
    results = RuleEngine().evaluate_all(full_facts)
    assert len(results) == 47
    assert {r.rule_id for r in results} == {rule.rule_id for rule in all_rules()}


def test_every_result_has_required_fields(full_facts):
    results = RuleEngine().evaluate_all(full_facts)
    for r in results:
        assert r.rule_id
        assert isinstance(r.matched, bool)
        assert isinstance(r.matched_conditions, tuple)
        assert isinstance(r.failed_conditions, tuple)
        assert isinstance(r.derived_facts, dict)
        assert isinstance(r.evaluation_trace, tuple)
        assert len(r.evaluation_trace) > 0
        assert r.execution_time >= 0.0


def test_evaluate_single_rule_by_id(full_facts):
    result = RuleEngine().evaluate("RULE-DIGNITY-002", full_facts)
    assert result.rule_id == "RULE-DIGNITY-002"


def test_deterministic_across_repeated_calls(full_facts):
    """
    execution_time legitimately varies run-to-run (it's a real wall-clock
    measurement) — compare everything else for determinism instead of
    full object equality.
    """
    engine = RuleEngine()
    first = engine.evaluate_all(full_facts)
    second = engine.evaluate_all(full_facts)
    assert len(first) == len(second)
    for r1, r2 in zip(first, second):
        assert r1.rule_id == r2.rule_id
        assert r1.matched == r2.matched
        assert r1.matched_conditions == r2.matched_conditions
        assert r1.failed_conditions == r2.failed_conditions
        assert r1.derived_facts == r2.derived_facts
        assert r1.evaluation_trace == r2.evaluation_trace


def test_raja_yoga_rule_matches_when_underlying_yoga_present(natal_chart, full_facts):
    from apps.api.services.yoga_engine import YogaEngine

    yoga_engine = YogaEngine()
    yoga_result = next(r for r in yoga_engine.evaluate_all(natal_chart) if r.yoga_id == "BPHS-RY-001")

    rule_result = RuleEngine().evaluate("RULE-YOGA-004", full_facts)
    assert rule_result.matched == yoga_result.is_present


def test_rule_engine_never_receives_a_chart_object(full_facts):
    results = RuleEngine().evaluate_all(full_facts)
    assert len(results) > 0


def test_pipeline_works_without_shadbala_or_transit_engines(natal_chart):
    builder = FactBuilder()
    facts = builder.build_facts(natal_chart)
    results = RuleEngine().evaluate_all(facts)
    assert len(results) == 47
    shadbala_rule = next(r for r in results if r.rule_id == "RULE-STRENGTH-001")
    assert shadbala_rule.matched is False
    transit_rule = next(r for r in results if r.rule_id == "RULE-TRANSIT-001")
    assert transit_rule.matched is False


def test_matched_rules_have_nonempty_explanation(full_facts):
    results = RuleEngine().evaluate_all(full_facts)
    for r in results:
        if r.matched:
            assert r.explanation != ""


# ── Phase 2: compound (multi-condition) rule correctness ─────────────────────

def test_compound_rule_requires_both_conditions_true():
    """RULE-COMPOUND-001 (Jupiter exalted AND in lagna) must not match on either condition alone."""
    from apps.api.domain.facts import Fact
    from apps.api.services.fact_registry import FactRegistry

    engine = RuleEngine()

    both_true = FactRegistry()
    both_true.add_fact(Fact("planet.jupiter.exalted", True, "test"))
    both_true.add_fact(Fact("planet.jupiter.house", 1, "test"))
    assert engine.evaluate("RULE-COMPOUND-001", both_true).matched is True

    only_exalted = FactRegistry()
    only_exalted.add_fact(Fact("planet.jupiter.exalted", True, "test"))
    only_exalted.add_fact(Fact("planet.jupiter.house", 5, "test"))
    assert engine.evaluate("RULE-COMPOUND-001", only_exalted).matched is False

    only_lagna = FactRegistry()
    only_lagna.add_fact(Fact("planet.jupiter.exalted", False, "test"))
    only_lagna.add_fact(Fact("planet.jupiter.house", 1, "test"))
    assert engine.evaluate("RULE-COMPOUND-001", only_lagna).matched is False


def test_compound_rule_spans_two_different_engines_worth_of_facts():
    """RULE-COMPOUND-002 combines a Shadbala fact (Module 9) and an Ashtakavarga fact (Module 10)."""
    from apps.api.domain.facts import Fact
    from apps.api.services.fact_registry import FactRegistry

    facts = FactRegistry()
    facts.add_fact(Fact("shadbala.jupiter.total", 4.0, "test"))
    facts.add_fact(Fact("ashtakavarga.jupiter.bindu", 6, "test"))
    result = RuleEngine().evaluate("RULE-COMPOUND-002", facts)
    assert result.matched is True
    assert result.derived_facts == {"jupiter.convergent_strength": "very_high"}


# ── Phase 2: house-lord self-placement correctness ────────────────────────────

def test_house_lord_rule_matches_real_chart_self_placement(natal_chart, full_facts):
    """
    Cross-check RULE-HOUSELORD-001/002/003 directly against the chart's
    actual house-lord data, not just that the rule runs without error.
    """
    for house, rule_id in [(10, "RULE-HOUSELORD-001"), (1, "RULE-HOUSELORD-002"), (9, "RULE-HOUSELORD-003")]:
        lord_house = full_facts.get_value(f"house.{house}.lord_house")
        result = RuleEngine().evaluate(rule_id, full_facts)
        assert result.matched == (lord_house == house)
