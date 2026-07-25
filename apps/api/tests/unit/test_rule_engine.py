"""
AstroOS — Rule Engine Unit Tests (Module 13)

Uses synthetic Facts (not real chart data) to test condition evaluation
precisely and deterministically. See
tests/integration/test_rule_engine_integration.py for coverage against
real chart data and the actual registered rules.
"""

import pytest

from apps.api.domain.facts import Fact
from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.rule_engine import RuleEngine
import apps.api.services.rule_registry as rule_registry_module


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    """Each test gets a fresh, empty rule registry — doesn't pollute the real 20 production rules."""
    fresh_registry: dict = {}
    monkeypatch.setattr(rule_registry_module, "_REGISTRY", fresh_registry)
    yield


def _make_facts(**kwargs) -> FactRegistry:
    registry = FactRegistry()
    for key, value in kwargs.items():
        registry.add_fact(Fact(key.replace("__", "."), value, "test"))
    return registry


def _simple_rule(rule_id="TEST-001", conditions=(), derived_facts=None):
    return RuleDefinition(
        rule_id=rule_id, rule_version="1.0", rule_name="Test Rule",
        source_text="test", priority=1, category="test",
        conditions=conditions,
        conclusion=Conclusion(derived_facts=derived_facts or {}),
        explanation="test explanation", tags=("test",),
    )


def test_equals_operator_true():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 1})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.matched is True


def test_equals_operator_false():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 5})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.matched is False


def test_not_equals_operator():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "!=", 1),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 5})
    assert RuleEngine().evaluate("TEST-001", facts).matched is True


def test_greater_than_operator():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("shadbala.jupiter.total", ">", 7),
    )))
    facts = _make_facts(**{"shadbala.jupiter.total": 8.32})
    assert RuleEngine().evaluate("TEST-001", facts).matched is True


def test_less_than_operator():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("ashtakavarga.saturn.bindu", "<", 3),
    )))
    facts = _make_facts(**{"ashtakavarga.saturn.bindu": 2})
    assert RuleEngine().evaluate("TEST-001", facts).matched is True


def test_greater_than_or_equal_operator():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("ashtakavarga.jupiter.bindu", ">=", 6),
    )))
    facts = _make_facts(**{"ashtakavarga.jupiter.bindu": 6})
    assert RuleEngine().evaluate("TEST-001", facts).matched is True


def test_less_than_or_equal_operator():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("ashtakavarga.saturn.bindu", "<=", 2),
    )))
    facts = _make_facts(**{"ashtakavarga.saturn.bindu": 2})
    assert RuleEngine().evaluate("TEST-001", facts).matched is True


def test_all_conditions_must_pass():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
        Condition("planet.jupiter.exalted", "==", True),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 1, "planet.jupiter.exalted": True})
    assert RuleEngine().evaluate("TEST-001", facts).matched is True


def test_one_failing_condition_fails_the_whole_rule():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
        Condition("planet.jupiter.exalted", "==", True),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 1, "planet.jupiter.exalted": False})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.matched is False
    assert len(result.matched_conditions) == 1
    assert len(result.failed_conditions) == 1


def test_rule_with_no_conditions_never_matches():
    rule_registry_module.register_rule(_simple_rule(conditions=()))
    facts = _make_facts()
    assert RuleEngine().evaluate("TEST-001", facts).matched is False


def test_missing_fact_fails_the_condition_not_crashes():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
    )))
    facts = _make_facts()
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.matched is False
    assert "not found" in result.evaluation_trace[1]


def test_derived_facts_populated_only_when_matched():
    rule_registry_module.register_rule(_simple_rule(
        conditions=(Condition("planet.jupiter.house", "==", 1),),
        derived_facts={"career.wisdom_capacity": "strong"},
    ))
    facts = _make_facts(**{"planet.jupiter.house": 1})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.derived_facts == {"career.wisdom_capacity": "strong"}


def test_derived_facts_empty_when_not_matched():
    rule_registry_module.register_rule(_simple_rule(
        conditions=(Condition("planet.jupiter.house", "==", 1),),
        derived_facts={"career.wisdom_capacity": "strong"},
    ))
    facts = _make_facts(**{"planet.jupiter.house": 5})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.derived_facts == {}


def test_evaluation_trace_is_nonempty():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 1})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert len(result.evaluation_trace) > 0


def test_explanation_empty_when_not_matched():
    rule = _simple_rule(conditions=(Condition("planet.jupiter.house", "==", 1),))
    object.__setattr__(rule, "explanation", "This should not appear")
    rule_registry_module.register_rule(rule)
    facts = _make_facts(**{"planet.jupiter.house": 5})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.explanation == ""


def test_execution_time_is_recorded():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "==", 1),
    )))
    facts = _make_facts(**{"planet.jupiter.house": 1})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.execution_time >= 0.0


def test_evaluate_unknown_rule_id_raises():
    facts = _make_facts()
    with pytest.raises(ValueError):
        RuleEngine().evaluate("NONEXISTENT-RULE", facts)


def test_evaluate_all_runs_every_registered_rule():
    rule_registry_module.register_rule(_simple_rule(rule_id="TEST-A", conditions=(
        Condition("x", "==", 1),
    )))
    rule_registry_module.register_rule(_simple_rule(rule_id="TEST-B", conditions=(
        Condition("y", "==", 2),
    )))
    facts = _make_facts(x=1, y=99)
    results = RuleEngine().evaluate_all(facts)
    assert len(results) == 2
    result_by_id = {r.rule_id: r for r in results}
    assert result_by_id["TEST-A"].matched is True
    assert result_by_id["TEST-B"].matched is False


def test_incompatible_type_comparison_fails_gracefully():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.rashi", ">", 5),
    )))
    facts = _make_facts(**{"planet.jupiter.rashi": "sagittarius"})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.matched is False


def test_unknown_operator_fails_gracefully_not_crashes():
    rule_registry_module.register_rule(_simple_rule(conditions=(
        Condition("planet.jupiter.house", "~=", 1),  # not a real operator
    )))
    facts = _make_facts(**{"planet.jupiter.house": 1})
    result = RuleEngine().evaluate("TEST-001", facts)
    assert result.matched is False
    assert "unknown operator" in result.evaluation_trace[1]
