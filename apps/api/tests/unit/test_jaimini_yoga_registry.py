"""
AstroOS — Jaimini Yoga Registry Unit Tests
"""

import pytest

from apps.api.domain.prediction_evidence import PredictionEvidence, PredictionConfidence
import apps.api.services.jaimini_yoga_registry as jyr_module
from apps.api.services.jaimini_yoga_registry import (
    all_jaimini_yogas,
    clear_registry,
    get_jaimini_yoga,
    register_jaimini_yoga,
)


@pytest.fixture(autouse=True)
def isolated_registry(monkeypatch):
    # jaimini_yoga_registry stores entries in a shared Registry helper
    # (services/_registry.py) rather than a bare module-level dict; swap
    # out its internal storage per test, same pattern as
    # test_rule_registry.py / test_yoga_registry.py.
    monkeypatch.setattr(jyr_module._registry, "_items", {})
    yield


def _dummy_evaluator(ctx):
    return PredictionEvidence(
        rule=None,  # unused by these tests — real evaluators fill this in
        is_matched=False,
        triggering_conditions=(),
        reasons=(),
        confidence=PredictionConfidence(score=0, satisfied_conditions=0, total_conditions=0, basis="test"),
        explanation="test",
    )


def _register(rule_id="JAIMINI-TEST-001"):
    return register_jaimini_yoga(
        rule_id=rule_id, name="Test Yoga", sutra_reference="Test Sutra",
        rule_version="1.0", requires=("D1",),
    )(_dummy_evaluator)


def test_register_and_get():
    _register()
    entry = get_jaimini_yoga("JAIMINI-TEST-001")
    assert entry is not None
    rule, evaluator = entry
    assert rule.rule_id == "JAIMINI-TEST-001"
    assert rule.name == "Test Yoga"
    assert evaluator is _dummy_evaluator


def test_get_missing_returns_none():
    assert get_jaimini_yoga("NONEXISTENT") is None


def test_duplicate_rule_id_rejected():
    _register()
    with pytest.raises(ValueError):
        _register()


def test_all_jaimini_yogas_returns_every_registered_rule():
    _register("JAIMINI-TEST-001")
    _register("JAIMINI-TEST-002")
    ids = {rule.rule_id for rule, _ in all_jaimini_yogas()}
    assert ids == {"JAIMINI-TEST-001", "JAIMINI-TEST-002"}


def test_clear_registry_empties_it():
    _register()
    clear_registry()
    assert all_jaimini_yogas() == []


def test_decorator_returns_original_evaluator_unchanged():
    result = _register()
    assert result is _dummy_evaluator
