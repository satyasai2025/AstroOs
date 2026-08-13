"""
AstroOS — Technique Engine Unit Tests

Two layers:
  1. Framework genericity/determinism with synthetic rules in an isolated
     registry — proves the engine has NO domain assumptions and delegates all
     evaluation to the existing RuleEngine.
  2. The Eye Health fixture (first imported technique) executes end-to-end,
     preserves its DERIVED provenance and unresolved source inconsistencies,
     and reports INSUFFICIENT_DATA rather than fabricating missing facts.
"""

from __future__ import annotations

import pytest

from apps.api.domain.facts import Fact
from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
from apps.api.domain.technique import (
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
    TriggerStatus,
)
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.technique_engine import TechniqueEngine
import apps.api.services.rule_registry as rule_registry_module
import apps.api.services.technique_registry as technique_registry_module


@pytest.fixture(autouse=True)
def isolated_registries(monkeypatch):
    # Both registries now store entries in a shared Registry helper
    # (services/_registry.py) rather than a bare module-level dict; swap out
    # each one's internal storage the same way the old `_REGISTRY` dicts
    # were swapped.
    monkeypatch.setattr(rule_registry_module._registry, "_items", {})
    monkeypatch.setattr(technique_registry_module._registry, "_items", {})
    yield


def _facts(**kwargs) -> FactRegistry:
    reg = FactRegistry()
    for key, value in kwargs.items():
        reg.add_fact(Fact(key.replace("__", "."), value, "test"))
    return reg


def _rule(rule_id, fact_key, expected, derived=None):
    return RuleDefinition(
        rule_id=rule_id, rule_version="1.0", rule_name=rule_id,
        source_text="test", priority=1, category="test",
        conditions=(Condition(fact_key, "==", expected, fact_key),),
        conclusion=Conclusion(derived_facts=derived or {}),
        explanation=f"{rule_id} fired", tags=(),
    )


# ── 1. framework genericity / determinism ─────────────────────────────────────


def test_engine_triggers_and_buckets_by_role():
    rule_registry_module.register_rule(_rule("GEN-001", "x.a", 1))
    rule_registry_module.register_rule(_rule("GEN-002", "x.b", 1))
    tech = TechniqueDefinition(
        technique_id="generic", name="Generic", version=1,
        required_inputs=("x.a", "x.b"),
        rule_refs=(
            TechniqueRuleRef("GEN-001", "1.0", RuleRole.PRIMARY, ProvenanceStatus.SOURCE_DERIVED),
            TechniqueRuleRef("GEN-002", "1.0", RuleRole.CONTRADICTING, ProvenanceStatus.SOURCE_DERIVED),
        ),
    )
    result = TechniqueEngine().execute(tech, _facts(x__a=1, x__b=1))

    assert len(result.primary) == 1
    assert len(result.contradicting) == 1
    # contradiction pulls a fully-triggered primary below 100
    assert result.confidence < 100
    # deterministic: same inputs → same score
    again = TechniqueEngine().execute(tech, _facts(x__a=1, x__b=1))
    assert again.confidence == result.confidence


def test_missing_fact_is_insufficient_data_not_false():
    rule_registry_module.register_rule(_rule("GEN-001", "x.a", 1))
    tech = TechniqueDefinition(
        technique_id="generic", name="Generic", version=1,
        required_inputs=("x.a",),
        rule_refs=(TechniqueRuleRef("GEN-001", "1.0", RuleRole.PRIMARY,
                                    ProvenanceStatus.SOURCE_DERIVED),),
    )
    result = TechniqueEngine().execute(tech, _facts())  # x.a absent
    trigger = result.triggers[0]
    assert trigger.status is TriggerStatus.INSUFFICIENT_DATA
    assert "x.a" in trigger.missing_facts
    assert result.confidence == 0  # no evaluable primary → 0, never guessed


def test_confidence_basis_is_reconstructible():
    rule_registry_module.register_rule(_rule("GEN-001", "x.a", 1))
    tech = TechniqueDefinition(
        technique_id="generic", name="Generic", version=1,
        required_inputs=("x.a",),
        rule_refs=(TechniqueRuleRef("GEN-001", "1.0", RuleRole.PRIMARY,
                                    ProvenanceStatus.SOURCE_DERIVED),),
    )
    result = TechniqueEngine().execute(tech, _facts(x__a=1))
    assert result.confidence == 100
    assert "1/1 primary rules triggered" in result.confidence_basis


# ── 2. Eye Health fixture ─────────────────────────────────────────────────────


def test_eye_fixture_executes_and_preserves_provenance(monkeypatch):
    # Re-import the fixture into the isolated registries.
    import importlib
    import apps.api.services.techniques.eye_health as eye
    importlib.reload(eye)

    from apps.api.services.technique_registry import get_technique
    tech = get_technique("eye_health")
    assert tech is not None

    # EYE-008 must remain DERIVED (never presented as source fact).
    eye008 = next(r for r in tech.rule_refs if r.rule_id == "EYE-008")
    assert eye008.provenance is ProvenanceStatus.DERIVED

    # The Section A/B numbering conflict is preserved, not resolved.
    assert any("Section A" in n for n in tech.unresolved_inconsistencies)

    # Execute: Sun in 8th → EYE-001 primary triggers.
    facts = _facts(
        planet__sun__house=8,
        planet__moon__house=3,
        planet__sun__debilitated=False,
        planet__moon__debilitated=False,
        planet__jupiter__house=5,
    )
    result = TechniqueEngine().execute(tech, facts)
    assert any(t.rule_id == "EYE-001" and t.status is TriggerStatus.TRIGGERED
               for t in result.triggers)
    # Neutral output: unresolved inconsistencies carried through untouched.
    assert result.unresolved_inconsistencies == tech.unresolved_inconsistencies
