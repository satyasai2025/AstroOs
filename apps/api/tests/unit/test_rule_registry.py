"""
AstroOS — Rule Registry Unit Tests (Module 13)
"""

import pytest

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
import apps.api.services.rule_registry as rule_registry_module
from apps.api.services.rule_registry import all_rules, clear_registry, get_rule, register_rule


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    # rule_registry_module now stores entries in a shared Registry helper
    # (services/_registry.py) rather than a bare module-level dict; swap out
    # its internal storage the same way the old `_REGISTRY` dict was swapped.
    monkeypatch.setattr(rule_registry_module._registry, "_items", {})
    yield


def _rule(rule_id="R-1"):
    return RuleDefinition(
        rule_id=rule_id, rule_version="1.0", rule_name="Test",
        source_text="test", priority=1, category="test",
        conditions=(Condition("x", "==", 1),), conclusion=Conclusion(),
        explanation="test", tags=(),
    )


def test_register_and_get_rule():
    register_rule(_rule("R-1"))
    assert get_rule("R-1").rule_id == "R-1"


def test_get_rule_missing_returns_none():
    assert get_rule("NONEXISTENT") is None


def test_duplicate_rule_id_rejected():
    register_rule(_rule("R-1"))
    with pytest.raises(ValueError):
        register_rule(_rule("R-1"))


def test_all_rules_returns_every_registered_rule():
    register_rule(_rule("R-1"))
    register_rule(_rule("R-2"))
    assert {r.rule_id for r in all_rules()} == {"R-1", "R-2"}


def test_clear_registry_empties_it():
    register_rule(_rule("R-1"))
    clear_registry()
    assert all_rules() == []
