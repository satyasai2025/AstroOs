"""
AstroOS — Rule Registry (Module 13 Phase B)

Rules register themselves as pure data (RuleDefinition instances), not
wrapped evaluator functions — RuleEngine evaluates every rule with the
same generic condition-comparison mechanism, so this registry never
needs an if/elif chain and neither does anything that uses it.

Phase B: added registry_hash() for experiment reproducibility tracking.
"""

from __future__ import annotations

import hashlib

from apps.api.domain.rules import RuleDefinition

_REGISTRY: dict[str, RuleDefinition] = {}


def register_rule(rule: RuleDefinition) -> None:
    """Register a rule definition; raises ValueError on duplicate rule_id."""
    if rule.rule_id in _REGISTRY:
        raise ValueError(f"Duplicate rule_id registered: {rule.rule_id!r}")
    _REGISTRY[rule.rule_id] = rule


def all_rules() -> list[RuleDefinition]:
    """All registered rules, in registration order."""
    return list(_REGISTRY.values())


def get_rule(rule_id: str) -> RuleDefinition | None:
    """Look up a registered rule by its rule_id, or None if unknown."""
    return _REGISTRY.get(rule_id)


def registry_hash() -> str:
    """
    SHA-256 hash of all registered rules, used for experiment reproducibility.
    Serializes (rule_id, rule_version) tuples in sorted order.
    """
    hasher = hashlib.sha256()
    for rid in sorted(_REGISTRY):
        rule = _REGISTRY[rid]
        hasher.update(f"{rid}:{rule.rule_version}\n".encode())
    return hasher.hexdigest()


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _REGISTRY.clear()
