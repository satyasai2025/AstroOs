"""
AstroOS — Rule Domain Objects (Module 13)

Rules and their Conditions are pure declarative data, not custom
evaluator callables (unlike Yoga Engine's registry, Module 8). A
Condition is just (fact_key, operator, expected_value) — RuleEngine
contains ONE generic comparison mechanism that evaluates every rule's
conditions the same way, so adding a rule never means adding code,
avoiding the if/elif chain by construction rather than by discipline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Condition:
    """One comparison against a single Fact. fact_key must match a Fact.key exactly."""
    fact_key: str
    operator: str  # "==", "!=", ">", "<", ">=", "<="
    expected_value: Any
    description: str = ""  # human-readable, for trace/explanation output


@dataclass(frozen=True)
class Conclusion:
    """What a rule asserts when all of its conditions are satisfied."""
    derived_facts: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True)
class RuleDefinition:
    """
    A registered rule — pure data, no attached evaluator function. All
    fields the review specified, in the shape it specified.
    """
    rule_id: str
    rule_version: str
    rule_name: str
    source_text: str
    priority: int
    category: str
    conditions: tuple[Condition, ...]
    conclusion: Conclusion
    explanation: str
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RuleResult:
    """Result of evaluating one RuleDefinition against one FactRegistry."""
    rule_id: str
    matched: bool
    matched_conditions: tuple[str, ...]
    failed_conditions: tuple[str, ...]
    derived_facts: dict[str, Any]
    explanation: str
    evaluation_trace: tuple[str, ...]
    execution_time: float  # seconds
