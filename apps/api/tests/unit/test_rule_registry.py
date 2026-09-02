"""
AstroOS — Rule Registry Unit Tests (Module 13) & Governance CI Validation
"""

from pathlib import Path
import pytest
import yaml

from apps.api.domain.rules import Condition, Conclusion, RuleDefinition
import apps.api.services.rule_registry as rule_registry_module
from apps.api.services.rule_registry import all_rules, clear_registry, get_rule, register_rule

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_YAML_PATH = REPO_ROOT / "apps" / "api" / "services" / "rules_registry.yaml"
WIKIDOT_DOCS_DIR = REPO_ROOT / "docs" / "wikidot_canonical_knowledge" / "01_astronomical_foundations"
DOCS_DIR = REPO_ROOT / "docs"


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


# ── GOVERNANCE CI TESTS: RULES_REGISTRY.YAML ───────────────────────────────

def test_rules_registry_yaml_file_existence_ci():
    """
    CI File-Existence Test: Every source_ref.doc cited in rules_registry.yaml
    MUST physically exist on disk in the repository.
    Path existence is CI-verified; quotetext fidelity is scholar-audited.
    """
    assert REGISTRY_YAML_PATH.exists(), f"Missing rules_registry.yaml at {REGISTRY_YAML_PATH}"
    data = yaml.safe_load(REGISTRY_YAML_PATH.read_text(encoding="utf-8"))

    rules = data.get("rules", [])
    assert len(rules) > 0, "rules_registry.yaml contains no rules"

    for r in rules:
        sref = r.get("source_ref")
        if isinstance(sref, dict) and "doc" in sref:
            doc_name = sref["doc"]
            # Check in canonical wikidot directory or general docs directory
            candidate_1 = WIKIDOT_DOCS_DIR / doc_name
            candidate_2 = DOCS_DIR / doc_name
            assert (
                candidate_1.exists() or candidate_2.exists()
            ), f"Rule '{r.get('rule_id')}' references missing doc: {doc_name}"


def test_rules_registry_yaml_status_and_gating_vocab():
    """Validates that status_vocab and gating_states are well-formed and valid."""
    data = yaml.safe_load(REGISTRY_YAML_PATH.read_text(encoding="utf-8"))

    status_vocab = data.get("status_vocab", {})
    assert "VERIFIED_SOURCE" in status_vocab
    assert "DOCTRINE_DECISION" in status_vocab
    assert "UNVERIFIED_PENDING_CITATION_AUDIT" in status_vocab
    assert "UNVERIFIED" in status_vocab

    gating_states = data.get("gating_states", {})
    assert "PROMISE_ABSENT" in gating_states
    assert "DEFER_PROMISE_NOT_CLEAR" in gating_states
    assert "REASONABLE" in gating_states
    assert "HIGH" in gating_states

    # Verify all rules use only valid statuses
    for r in data.get("rules", []):
        st = r.get("status")
        assert st in status_vocab, f"Rule '{r.get('rule_id')}' has invalid status '{st}'"


def test_rules_registry_applies_at_stages():
    """Validates applies_at stage annotations for staging discipline."""
    data = yaml.safe_load(REGISTRY_YAML_PATH.read_text(encoding="utf-8"))
    valid_stages = {"COHORT_ELIGIBILITY", "SCORING", "SYNTHESIS", "RECTIFICATION"}

    for r in data.get("rules", []):
        applies_at = r.get("applies_at")
        if applies_at:
            assert applies_at in valid_stages, f"Rule '{r.get('rule_id')}' has unknown stage '{applies_at}'"
