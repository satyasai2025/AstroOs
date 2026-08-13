"""
AstroOS — Rule (de)serialization

The bridge that lets a *persisted, structured* rule definition become an
evaluable rule for the EXISTING deterministic RuleEngine — with NO new engine
and NO per-technique Python file.

RuleEngine.evaluate(rule_id, facts) resolves rules through
rule_registry.get_rule(), and RuleEngine._evaluate_rule works on any
RuleDefinition object. So an imported technique's rules only need to be:
  1. reconstructed from JSON into domain/rules.py objects (this module), then
  2. registered into the existing rule_registry (rule_registry.ensure_rule).
After that the untouched RuleEngine evaluates them exactly like the hand-coded
rules in services/rules/. This module is the serialization boundary only; it
contains no evaluation logic.

JSON shapes
-----------
condition : {"type": "condition", "fact_key", "operator", "value", "description"}
group     : {"type": "group", "operator": "AND"|"OR", "conditions": [ ... ]}
rule      : {"rule_id", "rule_version", "rule_name", "source_text", "priority",
             "category", "conditions": [ ... ], "conclusion": {"derived_facts",
             "description"}, "explanation", "tags": [ ... ]}
"""

from __future__ import annotations

from typing import Any

from apps.api.domain.rules import (
    Condition,
    Conclusion,
    ConditionGroup,
    RuleDefinition,
)

# The ONLY operators the RuleEngine understands. Serialization refuses anything
# else rather than silently emitting a rule that can never match — normalization
# (technique_import_pipeline) is responsible for mapping synonyms to these.
_VALID_OPERATORS = frozenset({"==", "!=", ">", "<", ">=", "<=", "in", "not_in"})


class RuleSerializationError(ValueError):
    """Raised on a malformed rule/condition payload."""


# ── serialize (RuleDefinition -> JSON-able dict) ──────────────────────────────


def _condition_to_dict(item: Condition | ConditionGroup) -> dict[str, Any]:
    if isinstance(item, ConditionGroup):
        return {
            "type": "group",
            "operator": item.operator,
            "conditions": [_condition_to_dict(c) for c in item.conditions],
        }
    return {
        "type": "condition",
        "fact_key": item.fact_key,
        "operator": item.operator,
        "value": item.expected_value,
        "description": item.description,
    }


def rule_to_dict(rule: RuleDefinition) -> dict[str, Any]:
    return {
        "rule_id": rule.rule_id,
        "rule_version": rule.rule_version,
        "rule_name": rule.rule_name,
        "source_text": rule.source_text,
        "priority": rule.priority,
        "category": rule.category,
        "conditions": [_condition_to_dict(c) for c in rule.conditions],
        "conclusion": {
            "derived_facts": dict(rule.conclusion.derived_facts),
            "description": rule.conclusion.description,
        },
        "explanation": rule.explanation,
        "tags": list(rule.tags),
    }


# ── deserialize (dict -> RuleDefinition) ──────────────────────────────────────


def _coerce_value(operator: str, value: Any) -> Any:
    # Membership operators need a container; JSON arrays arrive as lists, which
    # `x in [...]` handles fine, but tuples match the hand-coded rule style.
    if operator in ("in", "not_in") and isinstance(value, list):
        return tuple(value)
    return value


def _dict_to_condition(d: dict[str, Any]) -> Condition | ConditionGroup:
    kind = d.get("type", "condition")
    if kind == "group":
        op = d.get("operator")
        if op not in ("AND", "OR"):
            raise RuleSerializationError(f"group operator must be AND/OR, got {op!r}")
        return ConditionGroup(
            operator=op,
            conditions=tuple(_dict_to_condition(c) for c in d.get("conditions", ())),
        )
    op = d.get("operator")
    if op not in _VALID_OPERATORS:
        raise RuleSerializationError(
            f"unknown operator {op!r}; valid: {sorted(_VALID_OPERATORS)}"
        )
    if "fact_key" not in d:
        raise RuleSerializationError("condition missing 'fact_key'")
    return Condition(
        fact_key=d["fact_key"],
        operator=op,
        expected_value=_coerce_value(op, d.get("value")),
        description=d.get("description", ""),
    )


def rule_from_dict(d: dict[str, Any]) -> RuleDefinition:
    for required in ("rule_id", "rule_name"):
        if not d.get(required):
            raise RuleSerializationError(f"rule missing required field {required!r}")
    conclusion_data = d.get("conclusion") or {}
    return RuleDefinition(
        rule_id=d["rule_id"],
        rule_version=str(d.get("rule_version", "1.0")),
        rule_name=d["rule_name"],
        source_text=d.get("source_text", ""),
        priority=int(d.get("priority", 1)),
        category=d.get("category", "imported"),
        conditions=tuple(_dict_to_condition(c) for c in d.get("conditions", ())),
        conclusion=Conclusion(
            derived_facts=dict(conclusion_data.get("derived_facts", {})),
            description=conclusion_data.get("description", ""),
        ),
        explanation=d.get("explanation", ""),
        tags=tuple(d.get("tags", ())),
    )
