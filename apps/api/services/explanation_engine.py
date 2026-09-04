"""
AstroOS — Explanation Engine (Phase D, Module 13 Extension)

Transforms raw RuleEngine evaluation traces into structured, human-readable
explanations. Parses trace lines to extract fact values, detects derived-fact
locking from priority conflicts, and generates failure analysis with
suggestions.

All methods are static — no state.
"""

from __future__ import annotations

import re
from typing import Any

from apps.api.domain.explanation import (
    ConditionExplanation,
    Explanation,
    FailureAnalysis,
)
from apps.api.domain.rules import RuleDefinition, RuleResult
from apps.api.domain.verification import VerificationPair
from apps.api.services.fact_registry import FactRegistry

# Regex for parsing evaluation trace lines.
# Format: "✓|✗ {label}: {fact_key} ({value!r}) {operator} {expected_value!r}"
_TRACE_LINE_RE = re.compile(
    r"^[✓✗]\s+(.+?):\s+(\S+)\s+\((.+?)\)\s+(\S+)\s+(.+)$"
)


def _parse_trace_line(line: str) -> dict[str, Any] | None:
    """Parse a single evaluation trace line into structured data."""
    m = _TRACE_LINE_RE.match(line)
    if not m:
        return None
    return {
        "label": m.group(1),
        "fact_key": m.group(2),
        "actual_value": m.group(3),
        "operator": m.group(4),
        "expected_value": m.group(5),
    }


def _build_confidence(derived_facts: dict, locked_count: int) -> str:
    """Derive confidence from fact completeness."""
    if not derived_facts:
        return "low"
    if locked_count > 0:
        return "medium"
    return "high"


class ExplanationEngine:
    """Transforms RuleEngine output into structured explanations."""

    @staticmethod
    def explain_rule_result(
        rule_result: RuleResult,
        facts_registry: FactRegistry | None = None,
        rule_definition: RuleDefinition | None = None,
    ) -> Explanation:
        """
        Converts a RuleResult's evaluation_trace lines into structured
        ConditionExplanation objects. Detects locked facts from priority
        conflicts by comparing derived_facts against the rule's conclusion.
        """
        conditions: list[ConditionExplanation] = []
        fact_sources: dict[str, str] = {}

        for line in rule_result.evaluation_trace:
            parsed = _parse_trace_line(line)
            if parsed is None:
                continue
            satisfied = line.startswith("✓")
            conditions.append(ConditionExplanation(
                condition_text=parsed["label"],
                satisfied=satisfied,
                fact_key=parsed["fact_key"],
                actual_value=parsed["actual_value"],
                expected_value=parsed["expected_value"],
                operator=parsed["operator"],
            ))

            # Look up fact source from registry if available.
            if facts_registry is not None:
                fact = facts_registry.get_fact(parsed["fact_key"])
                if fact is not None:
                    fact_sources[parsed["fact_key"]] = fact.source

        # Detect locked facts.
        locked: list[str] = []
        if rule_definition is not None:
            for key in rule_definition.conclusion.derived_facts:
                if key not in rule_result.derived_facts:
                    locked.append(key)

        # Build summary text.
        matched_count = sum(1 for c in conditions if c.satisfied)
        total_count = len(conditions)
        rule_name = getattr(rule_result, "rule_name", rule_result.rule_id)
        if rule_result.matched:
            summary = (
                f"Rule {rule_result.rule_id} ({rule_name}) matched: "
                f"{matched_count}/{total_count} conditions satisfied."
            )
        else:
            summary = (
                f"Rule {rule_result.rule_id} ({rule_name}) did not match: "
                f"only {matched_count}/{total_count} conditions satisfied."
            )

        confidence = _build_confidence(rule_result.derived_facts, len(locked))

        return Explanation(
            rule_id=rule_result.rule_id,
            rule_name=rule_result.rule_name,
            rule_category=getattr(rule_result, "rule_category", ""),
            summary=summary,
            matched=rule_result.matched,
            conditions=tuple(conditions),
            derived_facts=dict(rule_result.derived_facts),
            derived_fact_sources=fact_sources,
            locked_facts=tuple(locked),
            confidence=confidence,
            explanation_text=rule_result.explanation,
        )

    @staticmethod
    def explain_rule_failure(
        rule_result: RuleResult,
        facts_registry: FactRegistry | None = None,
        rule_definition: RuleDefinition | None = None,
    ) -> FailureAnalysis:
        """
        For unmatched rules, returns which conditions failed and what values
        would have been needed. Separates passed vs failed conditions.
        """
        failed: list[ConditionExplanation] = []
        passed: list[ConditionExplanation] = []
        suggestions: list[str] = []

        for line in rule_result.evaluation_trace:
            parsed = _parse_trace_line(line)
            if parsed is None:
                continue
            satisfied = line.startswith("✓")
            ce = ConditionExplanation(
                condition_text=parsed["label"],
                satisfied=satisfied,
                fact_key=parsed["fact_key"],
                actual_value=parsed["actual_value"],
                expected_value=parsed["expected_value"],
                operator=parsed["operator"],
            )
            if satisfied:
                passed.append(ce)
            else:
                failed.append(ce)
                # Generate suggestion for failed condition.
                if facts_registry is not None:
                    fact = facts_registry.get_fact(parsed["fact_key"])
                    if fact is None:
                        suggestions.append(
                            f"The fact '{parsed['fact_key']}' was not found. "
                            f"Check if the prerequisite engine data is available."
                        )
                    else:
                        suggestions.append(
                            f"Condition '{parsed['label']}' expects "
                            f"{parsed['expected_value']} but got "
                            f"{parsed['actual_value']}."
                        )
                else:
                    suggestions.append(
                        f"Condition '{parsed['label']}' requires "
                        f"{parsed['fact_key']} {parsed['operator']} "
                        f"{parsed['expected_value']} (got {parsed['actual_value']})."
                    )

        if rule_result.matched:
            summary = f"Rule {rule_result.rule_id} matched — no failure to analyze."
        else:
            summary = (
                f"Rule {rule_result.rule_id} failed: {len(failed)} condition(s) "
                f"not satisfied."
            )

        return FailureAnalysis(
            rule_id=rule_result.rule_id,
            rule_name=rule_result.rule_name,
            summary=summary,
            failed_conditions=tuple(failed),
            passed_conditions=tuple(passed),
            suggested_conditions=tuple(suggestions),
        )

    @staticmethod
    def explain_verification_pair(
        pair: VerificationPair,
        rule_result: RuleResult | None = None,
    ) -> Explanation:
        """
        Richer explanation for event-rule alignment. Extends base explanation
        with event context and alignment classification.
        """
        base_explanation = pair.explanation

        conditions = ()
        if rule_result is not None:
            conditions = ExplanationEngine.explain_rule_result(
                rule_result
            ).conditions

        summary = (
            f"Rule {pair.rule_id} vs event '{pair.event_title}' "
            f"({pair.event_date}): alignment={pair.alignment.value}, "
            f"strength={pair.strength.value}."
        )

        return Explanation(
            rule_id=pair.rule_id,
            rule_name=pair.rule_name,
            rule_category=pair.rule_category,
            summary=summary,
            matched=pair.rule_matched,
            conditions=conditions,
            derived_facts=dict(pair.derived_facts),
            explanation_text=base_explanation,
        )
