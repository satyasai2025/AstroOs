"""
AstroOS — Desha-Kaala-Paatra (JHA-DKP-1) & Multiplicative Gating (JHA-GATE-1) Unit Tests
========================================================================================

Validates:
1. Dynamic registry-to-behavior linkage for Desha-Kaala-Paatra age eligibility bounds.
2. PROMISE_ABSENT (determinate zero: seed absent) vs DEFER_PROMISE_NOT_CLEAR (indeterminate).
3. Eligibility exclusion prior to scoring vs scoring-level gating.
"""

from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_YAML_PATH = REPO_ROOT / "apps" / "api" / "services" / "rules_registry.yaml"


@pytest.fixture(scope="module")
def registry_data():
    """Loads raw rules_registry.yaml."""
    assert REGISTRY_YAML_PATH.exists()
    return yaml.safe_load(REGISTRY_YAML_PATH.read_text(encoding="utf-8"))


def test_jha_dkp_1_registry_linkage(registry_data):
    """Asserts that JHA-DKP-1 parameters are dynamically pullable from registry."""
    rules = {r["rule_id"]: r for r in registry_data.get("rules", [])}
    assert "JHA-DKP-1" in rules, "Missing JHA-DKP-1 in rules_registry.yaml"

    dkp = rules["JHA-DKP-1"]
    assert dkp.get("applies_at") == "COHORT_ELIGIBILITY"
    assert dkp.get("status") == "UNVERIFIED_PENDING_CITATION_AUDIT"

    logic = dkp.get("logic", {})
    assert "marriage_age_range" in logic
    assert "career_elevation_age_range" in logic
    assert "childbirth_age_range" in logic
    assert logic.get("parameters_status") == "DOCTRINE_DECISION"

    m_range = logic["marriage_age_range"]
    assert len(m_range) == 2
    assert m_range[0] == 18
    assert m_range[1] == 55


def test_jha_gate_1_vocabulary_and_states(registry_data):
    """Asserts that JHA-GATE-1 contains the 4-tier gating states and relation."""
    rules = {r["rule_id"]: r for r in registry_data.get("rules", [])}
    assert "JHA-GATE-1" in rules, "Missing JHA-GATE-1 in rules_registry.yaml"

    gate = rules["JHA-GATE-1"]
    assert gate.get("applies_at") == "SCORING"
    assert gate.get("status") == "UNVERIFIED_PENDING_CITATION_AUDIT"

    formula = gate.get("formula", {})
    assert formula.get("type") == "gating_relation"
    states = formula.get("states", [])

    assert "PROMISE_ABSENT" in states
    assert "DEFER_PROMISE_NOT_CLEAR" in states
    assert "REASONABLE" in states
    assert "HIGH" in states


def test_cohort_eligibility_filter_simulation(registry_data):
    """Simulates slice filtering using registry-pulled bounds without magic numbers."""
    rules = {r["rule_id"]: r for r in registry_data.get("rules", [])}
    m_min, m_max = rules["JHA-DKP-1"]["logic"]["marriage_age_range"]

    def is_marriage_eligible(age_years: float) -> bool:
        return m_min <= age_years <= m_max

    # Age 6 (Child) -> Ineligible
    assert not is_marriage_eligible(6.0)
    # Age 17.5 (Minor) -> Ineligible
    assert not is_marriage_eligible(17.5)
    # Age 25 (Adult) -> Eligible
    assert is_marriage_eligible(25.0)
    # Age 40 (Adult) -> Eligible
    assert is_marriage_eligible(40.0)
    # Age 75 (Elder) -> Ineligible
    assert not is_marriage_eligible(75.0)


def test_promise_absent_vs_defer_gating_logic():
    """
    Asserts distinct semantics:
    - PROMISE_ABSENT: determinate zero (seed absent) -> slice excluded from scoring.
    - DEFER_PROMISE_NOT_CLEAR: indeterminate -> retained as deferral.
    """
    def evaluate_slice_gating(natal_promise_score: float, layer_agreement_count: int) -> str:
        if natal_promise_score == 0.0:
            return "PROMISE_ABSENT"
        elif layer_agreement_count < 3:
            return "DEFER_PROMISE_NOT_CLEAR"
        elif layer_agreement_count >= 5:
            return "HIGH"
        else:
            return "REASONABLE"

    # Case 1: Seed is absent -> PROMISE_ABSENT (cannot evaluate dasha/gochara)
    assert evaluate_slice_gating(natal_promise_score=0.0, layer_agreement_count=5) == "PROMISE_ABSENT"

    # Case 2: Seed is present but mixed/few layers agree -> DEFER_PROMISE_NOT_CLEAR
    assert evaluate_slice_gating(natal_promise_score=1.0, layer_agreement_count=2) == "DEFER_PROMISE_NOT_CLEAR"

    # Case 3: 3 layers agree -> REASONABLE
    assert evaluate_slice_gating(natal_promise_score=1.0, layer_agreement_count=3) == "REASONABLE"

    # Case 4: 5 layers agree -> HIGH
    assert evaluate_slice_gating(natal_promise_score=1.0, layer_agreement_count=5) == "HIGH"
