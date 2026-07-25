"""
AstroOS — ExplanationEngine Unit Tests (Phase D, Module 13 Extension)
"""

import uuid
from datetime import date

import pytest

from apps.api.domain.explanation import (
    ConditionExplanation,
    Explanation,
    FailureAnalysis,
)
from apps.api.domain.facts import Fact
from apps.api.domain.rules import Conclusion, Condition, RuleDefinition, RuleResult
from apps.api.domain.verification import (
    Alignment,
    VerificationPair,
    VerificationStrength,
)
from apps.api.services.explanation_engine import ExplanationEngine, _parse_trace_line
from apps.api.services.fact_registry import FactRegistry


def _matched_rule_result() -> RuleResult:
    return RuleResult(
        rule_id="RULE-001",
        matched=True,
        matched_conditions=("planet in kendra",),
        failed_conditions=(),
        derived_facts={"dignity.mars": "exalted"},
        explanation="Mars is exalted in a kendra.",
        evaluation_trace=(
            "Evaluating rule RULE-001 (Mars Kendra) [priority=10]",
            "✓ planet in kendra: planet.mars.house (1) == 1",
            "✓ dignity check: planet.mars.dignity ('exalted') == 'exalted'",
        ),
        execution_time=0.001,
        priority=10,
        rule_name="Mars Kendra",
        rule_category="dignity",
    )


def _failed_rule_result() -> RuleResult:
    return RuleResult(
        rule_id="RULE-002",
        matched=False,
        matched_conditions=("planet in kendra",),
        failed_conditions=("dignity check",),
        derived_facts={},
        explanation="",
        evaluation_trace=(
            "Evaluating rule RULE-002 (Moon Strength) [priority=5]",
            "✓ planet in kendra: planet.moon.house (4) == 4",
            "✗ dignity check: planet.moon.dignity ('neutral') == 'exalted'",
        ),
        execution_time=0.002,
        priority=5,
        rule_name="Moon Strength",
        rule_category="strength",
    )


def _rule_definition_with_extra_fact() -> RuleDefinition:
    return RuleDefinition(
        rule_id="RULE-001",
        rule_version="1.0",
        rule_name="Mars Kendra",
        source_text="BPHS",
        priority=10,
        category="dignity",
        conditions=(
            Condition(fact_key="planet.mars.house", operator="==", expected_value=1),
        ),
        conclusion=Conclusion(
            derived_facts={"dignity.mars": "exalted", "yoga.ruchaka": True},
        ),
        explanation="Mars is exalted in a kendra.",
    )


def _facts_registry() -> FactRegistry:
    reg = FactRegistry()
    reg.add_fact(Fact(key="planet.mars.house", value=1, source="graha_engine"))
    reg.add_fact(Fact(key="planet.mars.dignity", value="exalted", source="graha_engine"))
    reg.add_fact(Fact(key="planet.moon.house", value=4, source="graha_engine"))
    reg.add_fact(Fact(key="planet.moon.dignity", value="neutral", source="graha_engine"))
    return reg


class TestParseTraceLine:
    def test_parses_satisfied_line(self):
        line = "✓ planet in kendra: planet.mars.house (1) == 1"
        parsed = _parse_trace_line(line)
        assert parsed is not None
        assert parsed["label"] == "planet in kendra"
        assert parsed["fact_key"] == "planet.mars.house"
        assert parsed["actual_value"] == "1"
        assert parsed["operator"] == "=="
        assert parsed["expected_value"] == "1"

    def test_parses_failed_line(self):
        line = "✗ dignity check: planet.moon.dignity ('neutral') == 'exalted'"
        parsed = _parse_trace_line(line)
        assert parsed is not None
        assert parsed["label"] == "dignity check"
        assert parsed["fact_key"] == "planet.moon.dignity"
        assert parsed["actual_value"] == "'neutral'"
        assert parsed["operator"] == "=="
        assert parsed["expected_value"] == "'exalted'"

    def test_returns_none_for_header_line(self):
        line = "Evaluating rule RULE-001 (Mars Kendra) [priority=10]"
        assert _parse_trace_line(line) is None

    def test_returns_none_for_empty_string(self):
        assert _parse_trace_line("") is None

    def test_returns_none_for_derived_fact_line(self):
        line = "Derived Fact(s): {'dignity.mars': 'exalted'}"
        assert _parse_trace_line(line) is None


class TestExplainRuleResult:
    def test_matched_rule_basic(self):
        result = _matched_rule_result()
        explanation = ExplanationEngine.explain_rule_result(result)

        assert isinstance(explanation, Explanation)
        assert explanation.rule_id == "RULE-001"
        assert explanation.rule_name == "Mars Kendra"
        assert explanation.matched is True
        assert "matched" in explanation.summary
        assert "2/2" in explanation.summary
        assert len(explanation.conditions) == 2
        assert all(c.satisfied for c in explanation.conditions)
        assert explanation.derived_facts == {"dignity.mars": "exalted"}
        assert explanation.explanation_text == "Mars is exalted in a kendra."

    def test_unmatched_rule(self):
        result = _failed_rule_result()
        explanation = ExplanationEngine.explain_rule_result(result)

        assert explanation.matched is False
        assert "did not match" in explanation.summary
        assert "1/2" in explanation.summary
        passed = [c for c in explanation.conditions if c.satisfied]
        failed = [c for c in explanation.conditions if not c.satisfied]
        assert len(passed) == 1
        assert len(failed) == 1

    def test_with_facts_registry_populates_sources(self):
        result = _matched_rule_result()
        registry = _facts_registry()
        explanation = ExplanationEngine.explain_rule_result(result, facts_registry=registry)

        assert "planet.mars.house" in explanation.derived_fact_sources
        assert explanation.derived_fact_sources["planet.mars.house"] == "graha_engine"

    def test_confidence_high_when_matched_no_locked(self):
        result = _matched_rule_result()
        explanation = ExplanationEngine.explain_rule_result(result)
        assert explanation.confidence == "high"

    def test_confidence_low_when_no_derived_facts(self):
        result = _failed_rule_result()
        explanation = ExplanationEngine.explain_rule_result(result)
        assert explanation.confidence == "low"

    def test_empty_trace_produces_empty_conditions(self):
        result = RuleResult(
            rule_id="RULE-003",
            matched=False,
            matched_conditions=(),
            failed_conditions=(),
            derived_facts={},
            explanation="",
            evaluation_trace=(),
            execution_time=0.0,
            rule_name="Empty Rule",
        )
        explanation = ExplanationEngine.explain_rule_result(result)
        assert len(explanation.conditions) == 0
        assert "0/0" in explanation.summary


class TestLockedFactDetection:
    def test_detects_locked_facts(self):
        result = _matched_rule_result()
        rule_def = _rule_definition_with_extra_fact()
        explanation = ExplanationEngine.explain_rule_result(
            result, rule_definition=rule_def,
        )
        assert "yoga.ruchaka" in explanation.locked_facts
        assert "dignity.mars" not in explanation.locked_facts

    def test_confidence_medium_with_locked_facts(self):
        result = _matched_rule_result()
        rule_def = _rule_definition_with_extra_fact()
        explanation = ExplanationEngine.explain_rule_result(
            result, rule_definition=rule_def,
        )
        assert explanation.confidence == "medium"

    def test_no_locked_facts_without_definition(self):
        result = _matched_rule_result()
        explanation = ExplanationEngine.explain_rule_result(result)
        assert len(explanation.locked_facts) == 0


class TestExplainRuleFailure:
    def test_failed_rule_separates_conditions(self):
        result = _failed_rule_result()
        analysis = ExplanationEngine.explain_rule_failure(result)

        assert isinstance(analysis, FailureAnalysis)
        assert analysis.rule_id == "RULE-002"
        assert analysis.rule_name == "Moon Strength"
        assert len(analysis.failed_conditions) == 1
        assert len(analysis.passed_conditions) == 1
        assert "1 condition(s)" in analysis.summary

    def test_failed_rule_generates_suggestions_without_registry(self):
        result = _failed_rule_result()
        analysis = ExplanationEngine.explain_rule_failure(result)

        assert len(analysis.suggested_conditions) == 1
        assert "dignity check" in analysis.suggested_conditions[0]
        assert "planet.moon.dignity" in analysis.suggested_conditions[0]

    def test_failed_rule_with_registry_found_fact(self):
        result = _failed_rule_result()
        registry = _facts_registry()
        analysis = ExplanationEngine.explain_rule_failure(result, facts_registry=registry)

        assert len(analysis.suggested_conditions) == 1
        assert "expects" in analysis.suggested_conditions[0]

    def test_failed_rule_with_registry_missing_fact(self):
        result = RuleResult(
            rule_id="RULE-X",
            matched=False,
            matched_conditions=(),
            failed_conditions=("missing check",),
            derived_facts={},
            explanation="",
            evaluation_trace=(
                "✗ missing check: nonexistent.fact ('None') == 'expected'",
            ),
            execution_time=0.0,
            rule_name="Missing Fact Rule",
        )
        registry = FactRegistry()
        analysis = ExplanationEngine.explain_rule_failure(result, facts_registry=registry)

        assert len(analysis.suggested_conditions) == 1
        assert "was not found" in analysis.suggested_conditions[0]

    def test_matched_rule_failure_analysis(self):
        result = _matched_rule_result()
        analysis = ExplanationEngine.explain_rule_failure(result)
        assert "matched" in analysis.summary
        assert "no failure" in analysis.summary
        assert len(analysis.failed_conditions) == 0


class TestExplainVerificationPair:
    def test_basic_pair_explanation(self):
        pair = VerificationPair(
            rule_id="RULE-001",
            rule_name="Mars Kendra",
            rule_category="dignity",
            rule_matched=True,
            event_id=uuid.uuid4(),
            event_date=date(2020, 6, 15),
            event_title="Promotion",
            event_description="Got promoted at work",
            event_category="career",
            event_is_verified=True,
            derived_facts={"dignity.mars": "exalted"},
            inferred_domains=("career",),
            alignment=Alignment.CONFIRMED,
            strength=VerificationStrength.HIGH,
            explanation="Rule aligns with career event.",
        )
        explanation = ExplanationEngine.explain_verification_pair(pair)

        assert isinstance(explanation, Explanation)
        assert explanation.rule_id == "RULE-001"
        assert explanation.rule_name == "Mars Kendra"
        assert "Promotion" in explanation.summary
        assert "confirmed" in explanation.summary
        assert "high" in explanation.summary
        assert explanation.matched is True
        assert explanation.derived_facts == {"dignity.mars": "exalted"}

    def test_pair_with_rule_result_includes_conditions(self):
        pair = VerificationPair(
            rule_id="RULE-001",
            rule_name="Mars Kendra",
            rule_category="dignity",
            rule_matched=True,
            event_id=uuid.uuid4(),
            event_date=date(2020, 6, 15),
            event_title="Promotion",
            event_description=None,
            event_category="career",
            event_is_verified=True,
            derived_facts={"dignity.mars": "exalted"},
            inferred_domains=("career",),
            alignment=Alignment.CONFIRMED,
            strength=VerificationStrength.HIGH,
            explanation="Rule aligns with career event.",
        )
        rule_result = _matched_rule_result()
        explanation = ExplanationEngine.explain_verification_pair(pair, rule_result)

        assert len(explanation.conditions) == 2
        assert all(c.satisfied for c in explanation.conditions)

    def test_pair_without_rule_result_has_empty_conditions(self):
        pair = VerificationPair(
            rule_id="RULE-001",
            rule_name="Mars Kendra",
            rule_category="dignity",
            rule_matched=True,
            event_id=uuid.uuid4(),
            event_date=date(2020, 6, 15),
            event_title="Promotion",
            event_description=None,
            event_category="career",
            event_is_verified=True,
            derived_facts={},
            inferred_domains=(),
            alignment=Alignment.UNTESTED,
            strength=VerificationStrength.UNKNOWN,
            explanation="",
        )
        explanation = ExplanationEngine.explain_verification_pair(pair)
        assert len(explanation.conditions) == 0
