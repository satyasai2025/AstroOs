"""
AstroOS — Rule Registry (Module 13 Phase B)

Rules register themselves as pure data (RuleDefinition instances), not
wrapped evaluator functions — RuleEngine evaluates every rule with the
same generic condition-comparison mechanism, so this registry never
needs an if/elif chain and neither does anything that uses it.

Phase B: added registry_hash() for experiment reproducibility tracking.
"""

from __future__ import annotations

from apps.api.domain.rules import RuleDefinition
from apps.api.services._registry import Registry

_registry: Registry[str, RuleDefinition] = Registry(
    hash_line=lambda rule_id, rule: f"{rule_id}:{rule.rule_version}\n"
)


def register_rule(rule: RuleDefinition) -> None:
    """Register a rule definition; raises ValueError on duplicate rule_id."""
    _registry.register(
        rule.rule_id, rule,
        duplicate_message=f"Duplicate rule_id registered: {rule.rule_id!r}",
    )


def ensure_rule(rule: RuleDefinition) -> None:
    """Register a rule if absent; no-op if the same rule_id is already present.

    Idempotent counterpart to register_rule(), for rules reconstructed from
    persisted data (imported techniques): loading the same technique twice, or
    re-running the import pipeline, must not raise. Same-id rules are assumed
    identical by construction (a new rule VERSION uses a new rule_id per the
    immutable-versioning convention); this never overwrites an existing entry.
    """
    if not _registry.contains(rule.rule_id):
        _registry.set(rule.rule_id, rule)


def all_rules() -> list[RuleDefinition]:
    """All registered rules, in registration order."""
    return _registry.all()


def get_rule(rule_id: str) -> RuleDefinition | None:
    """Look up a registered rule by its rule_id, or None if unknown."""
    return _registry.get(rule_id)


def registry_hash() -> str:
    """
    SHA-256 hash of all registered rules, used for experiment reproducibility.
    Serializes (rule_id, rule_version) tuples in sorted order.
    """
    return _registry.hash()


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _registry.clear()
