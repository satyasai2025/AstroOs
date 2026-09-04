"""
AstroOS — Rule Engine (Module 13, Phase B — Enhanced)

Evaluates registered rules against a FactRegistry. This is the ONE
piece of the pipeline with a hard constraint worth restating exactly as
specified: it NEVER calls an astrology calculation engine, NEVER
touches a D1Chart or any other engine-internal object, and NEVER
duplicates Yoga/Shadbala/Ashtakavarga/Transit/Graha/House/Aspect logic.
It reads Facts, evaluates Conditions against them with one generic
comparison mechanism, and returns RuleResults. That is the entire
surface area.

Phase B additions:
  - Priority sorting: evaluate_all sorts rules by priority descending.
    Derived-fact locking: when multiple rules write the same derived_fact
    key, the highest-priority rule's value wins.
  - IN / NOT IN operators for list membership tests.
  - ConditionGroup for AND/OR nesting across conditions.
"""

from __future__ import annotations

import operator
import time

from apps.api.domain.rules import Condition, ConditionGroup, Conclusion, RuleDefinition, RuleResult
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.rule_registry import all_rules, get_rule

# Importing this triggers every rule module's register_rule() calls.
from apps.api.services import rules as _rules  # noqa: F401


def _in(a: object, b: object) -> bool:
    """Check if a is a member of collection b."""
    try:
        return a in b  # type: ignore[operator]
    except TypeError:
        return False


def _not_in(a: object, b: object) -> bool:
    """Check if a is NOT a member of collection b."""
    try:
        return a not in b  # type: ignore[operator]
    except TypeError:
        return False


_OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
    "in": _in,
    "not_in": _not_in,
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
    return satisfied, (
        f"{symbol} {label}: {condition.fact_key} ({fact.value!r}) "
        f"{condition.operator} {condition.expected_value!r}"
    )


def _evaluate_condition_group(
    group: ConditionGroup,
    facts: FactRegistry,
    depth: int = 0,
) -> tuple[bool, list[str]]:
    """
    Recursively evaluate a ConditionGroup (AND/OR) and return
    (satisfied, trace_lines). Nested groups are evaluated depth-first.
    """
    indent = "  " * depth
    traces: list[str] = []

    results: list[bool] = []
    for item in group.conditions:
        if isinstance(item, ConditionGroup):
            satisfied, child_traces = _evaluate_condition_group(item, facts, depth + 1)
            results.append(satisfied)
            traces.extend(child_traces)
        else:
            satisfied, trace_line = _evaluate_condition(item, facts)
            results.append(satisfied)
            traces.append(trace_line)

    if not results:
        return True, traces  # empty group vacuously true

    if group.operator == "AND":
        satisfied = all(results)
    else:  # OR
        satisfied = any(results)

    label = f"ConditionGroup({group.operator})"
    symbol = "✓" if satisfied else "✗"
    traces.append(f"{indent}{symbol} {label} → {'all matched' if satisfied else 'not all matched'}")
    return satisfied, traces


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
        """
        Evaluate every registered rule, sorted by priority descending.
        Derived-fact locking: when multiple rules write the same
        derived_fact key, the highest-priority rule's value wins and
        lower-priority rules cannot overwrite it.
        """
        sorted_rules = sorted(all_rules(), key=lambda r: r.priority, reverse=True)
        results: list[RuleResult] = []
        locked_facts: dict[str, object] = {}

        for rule in sorted_rules:
            result = self._evaluate_rule(rule, facts)

            # Apply derived-fact locking: keep facts already set by
            # higher-priority rules.
            if result.matched and result.derived_facts:
                filtered = {}
                for key, value in result.derived_facts.items():
                    if key not in locked_facts:
                        filtered[key] = value
                        locked_facts[key] = value
                result = RuleResult(
                    rule_id=result.rule_id,
                    matched=result.matched,
                    matched_conditions=result.matched_conditions,
                    failed_conditions=result.failed_conditions,
                    derived_facts=filtered,
                    explanation=result.explanation,
                    evaluation_trace=result.evaluation_trace,
                    execution_time=result.execution_time,
                    priority=result.priority,
                    rule_name=result.rule_name,
                    rule_category=result.rule_category,
                )

            results.append(result)

        return results

    def _evaluate_rule(self, rule: RuleDefinition, facts: FactRegistry) -> RuleResult:
        start = time.perf_counter()

        trace: list[str] = [
            f"Evaluating rule {rule.rule_id} ({rule.rule_name}) "
            f"[priority={rule.priority}]"
        ]
        matched_conditions: list[str] = []
        failed_conditions: list[str] = []

        for item in rule.conditions:
            if isinstance(item, ConditionGroup):
                satisfied, child_traces = _evaluate_condition_group(item, facts)
                trace.extend(child_traces)
                label = f"ConditionGroup({item.operator})"
                if satisfied:
                    matched_conditions.append(label)
                else:
                    failed_conditions.append(label)
            else:
                satisfied, trace_line = _evaluate_condition(item, facts)
                trace.append(trace_line)
                label = item.description or item.fact_key
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
            priority=rule.priority,
            rule_name=rule.rule_name,
            rule_category=rule.category,
        )
