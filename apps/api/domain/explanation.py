"""
AstroOS — Explanation Domain Objects (Phase D)

Structured explanation of rule evaluation results, distinct from the raw
evaluation trace strings. Transforms RuleEngine output into human-readable,
condition-level explanations with derived-fact source attribution.

Pure Python dataclasses — no ORM/Pydantic dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ConditionExplanation:
    """Human-readable explanation of one condition evaluation."""

    condition_text: str
    satisfied: bool
    fact_key: str
    actual_value: Any
    expected_value: Any
    operator: str


@dataclass(frozen=True)
class Explanation:
    """Structured explanation of a rule result."""

    rule_id: str
    rule_name: str
    rule_category: str
    summary: str
    matched: bool
    conditions: tuple[ConditionExplanation, ...] = ()
    derived_facts: dict[str, Any] = field(default_factory=dict)
    derived_fact_sources: dict[str, str] = field(default_factory=dict)
    locked_facts: tuple[str, ...] = ()
    confidence: str = "medium"
    explanation_text: str = ""


@dataclass(frozen=True)
class FailureAnalysis:
    """Why a rule did NOT match, with corrective suggestions."""

    rule_id: str
    rule_name: str
    summary: str
    failed_conditions: tuple[ConditionExplanation, ...] = ()
    passed_conditions: tuple[ConditionExplanation, ...] = ()
    suggested_conditions: tuple[str, ...] = ()
