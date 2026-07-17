"""
AstroOS — Rule Engine (Module 13)

Evaluates registered rules against a FactRegistry. This is the ONE
piece of the pipeline with a hard constraint worth restating exactly as
specified: it NEVER calls an astrology calculation engine, NEVER
touches a D1Chart or any other engine-internal object, and NEVER
duplicates Yoga/Shadbala/Ashtakavarga/Transit/Graha/House/Aspect logic.
It reads Facts, evaluates Conditions against them with one generic
comparison mechanism, and returns RuleResults. That is the entire
surface area.
"""

from __future__ import annotations

import operator
import time

from apps.api.domain.rules import Condition, RuleDefinition, RuleResult
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.rule_registry import all_rules, get_rule

# Importing this triggers every rule module's register_rule() calls.
from apps.api.services import rules as _rules  # noqa: F401

_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}


def _evaluate_condition(condition: Condition, facts: FactRegistry) -> tuple[bool, str]:
    """
    Returns (satisfied, trace_line). The ONE generic comparison
    mechanism every rule's every condition goes through — no per-rule
    code, ever.
    """
    fact = facts.get_fact(condition.fact_key)
    label = condition.description or condition.fact_key

    if fact is None:
        return False, f"✗ {label}: fact '{condition.fact_key}' not found"

    if condition.operator not in _OPERATORS:
        return False, f"✗ {label}: unknown operator {condition.operator!r}"

    op_fn = _OPERATORS[condition.operator]
    try:
        satisfied = op_fn(fact.value, condition.expected_value)
    except TypeError:
        return False, (
            f"✗ {label}: cannot compare {fact.value!r} {condition.operator} "
            f"{condition.expected_value!r} (incompatible types)"
        )

    symbol = "✓" if satisfied else "✗"
    return satisfied, f"{symbol} {label}: {condition.fact_key} ({fact.value!r}) {condition.operator} {condition.expected_value!r}"


class RuleEngine:
    """
    Stateless — takes a FactRegistry per call, never holds chart or
    engine state itself.
    """

    def evaluate(self, rule_id: str, facts: FactRegistry) -> RuleResult:
        rule = get_rule(rule_id)
        if rule is None:
            raise ValueError(f"No rule registered with id {rule_id!r}")
        return self._evaluate_rule(rule, facts)

    def evaluate_all(self, facts: FactRegistry) -> list[RuleResult]:
        return [self._evaluate_rule(rule, facts) for rule in all_rules()]

    def _evaluate_rule(self, rule: RuleDefinition, facts: FactRegistry) -> RuleResult:
        start = time.perf_counter()

        trace: list[str] = [f"Evaluating rule {rule.rule_id} ({rule.rule_name})"]
        matched_conditions: list[str] = []
        failed_conditions: list[str] = []

        for condition in rule.conditions:
            satisfied, trace_line = _evaluate_condition(condition, facts)
            trace.append(trace_line)
            label = condition.description or condition.fact_key
            if satisfied:
                matched_conditions.append(label)
            else:
                failed_conditions.append(label)

        matched = len(failed_conditions) == 0 and len(rule.conditions) > 0

        derived_facts: dict = {}
        if matched:
            derived_facts = dict(rule.conclusion.derived_facts)
            trace.append(f"Derived Fact(s): {derived_facts}")
        else:
            trace.append("Rule did not match — no facts derived")

        execution_time = time.perf_counter() - start

        return RuleResult(
            rule_id=rule.rule_id,
            matched=matched,
            matched_conditions=tuple(matched_conditions),
            failed_conditions=tuple(failed_conditions),
            derived_facts=derived_facts,
            explanation=rule.explanation if matched else "",
            evaluation_trace=tuple(trace),
            execution_time=execution_time,
        )
