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


RULE_ALIASES: dict[str, str] = {
    # GAJA / Gajakesari
    "gaja_001": "gaja_kesari_yoga",
    "gaja-001": "gaja_kesari_yoga",
    "gajakesari": "gaja_kesari_yoga",
    "gajakesari_yoga": "gaja_kesari_yoga",

    # DHANA / Lakshmi
    "dhana_001": "lakshmi_yoga",
    "dhana-001": "lakshmi_yoga",
    "dhana_yoga": "lakshmi_yoga",
    "lakshmi_yoga": "lakshmi_yoga",

    # RAJA / Dharma-Karmadhipati
    "raja_001": "dharma_karmadhipati_yoga",
    "raja-001": "dharma_karmadhipati_yoga",
    "raja_yoga": "dharma_karmadhipati_yoga",
    "dharma_karmadhipati_yoga": "dharma_karmadhipati_yoga",
    "kendra_trikona_raja_yoga": "dharma_karmadhipati_yoga",

    # BUDHA / Budhaditya
    "budha_001": "budhaditya_yoga",
    "budha-001": "budhaditya_yoga",
    "budhaditya_yoga": "budhaditya_yoga",
    "bhadra_yoga": "budhaditya_yoga",

    # Panch Mahapurusha & other classical yogas
    "ruchaka": "ruchaka_yoga",
    "ruchaka_yoga": "ruchaka_yoga",
    "hamsa": "hamsa_yoga",
    "hamsa_yoga": "hamsa_yoga",
    "sasa": "sasa_yoga",
    "sasa_yoga": "sasa_yoga",
    "malavya": "malavya_yoga",
    "malavya_yoga": "malavya_yoga",
    "neecha_bhanga": "neecha_bhanga_raja_yoga",
    "neecha_bhanga_raja_yoga": "neecha_bhanga_raja_yoga",

    # Health / Transits
    "eye_001": "netra_dosha_rule",
    "eye-001": "netra_dosha_rule",
    "netra_dosha": "netra_dosha_rule",
    "netra_dosha_rule": "netra_dosha_rule",

    "trn_sj_001": "saturn_jupiter_double_transit",
    "trn-sj-001": "saturn_jupiter_double_transit",
    "saturn_jupiter_double_transit": "saturn_jupiter_double_transit",
}

RULE_TARGET_MAP: dict[str, str] = {
    "gaja_kesari_yoga": "RULE-YOGA-003",
    "lakshmi_yoga": "RULE-YOGA-008",
    "dharma_karmadhipati_yoga": "RULE-YOGA-004",
    "budhaditya_yoga": "RULE-YOGA-007",
    "ruchaka_yoga": "RULE-YOGA-001",
    "hamsa_yoga": "RULE-YOGA-002",
    "sasa_yoga": "RULE-YOGA-005",
    "malavya_yoga": "RULE-YOGA-006",
    "neecha_bhanga_raja_yoga": "RULE-YOGA-009",
    "netra_dosha_rule": "RULE-HOUSE-002",
    "saturn_jupiter_double_transit": "RULE-TRANSIT-001",
}


def normalize_rule_id(rule_id: str) -> str:
    """
    Case-insensitive string normalizer for rule IDs.
    Transforms rule_id to lower case with hyphens replaced by underscores and whitespace trimmed,
    then resolves standard aliases.
    """
    if not rule_id:
        return ""
    normalized = rule_id.lower().replace("-", "_").strip()
    return RULE_ALIASES.get(normalized, normalized)


def all_rules() -> list[RuleDefinition]:
    """All registered rules, in registration order."""
    from apps.api.services import rules as _rules  # noqa: F401
    return _registry.all()


def get_rule(rule_id: str) -> RuleDefinition | None:
    """Look up a registered rule by its rule_id, normalized name, or alias; returns None if unknown."""
    if not rule_id:
        return None

    from apps.api.services import rules as _rules  # noqa: F401

    # 1. Direct exact lookup
    rule = _registry.get(rule_id)
    if rule is not None:
        return rule

    # 2. Normalized alias lookup
    norm = rule_id.lower().replace("-", "_").strip()
    alias_target = RULE_ALIASES.get(norm, norm)

    if alias_target in RULE_TARGET_MAP:
        mapped_id = RULE_TARGET_MAP[alias_target]
        rule = _registry.get(mapped_id)
        if rule is not None:
            return rule

    rule = _registry.get(alias_target)
    if rule is not None:
        return rule

    # 3. Case-insensitive search across registered rules (by rule_id or rule_name)
    for r in _registry.all():
        r_norm_id = r.rule_id.lower().replace("-", "_").strip()
        if r_norm_id in (norm, alias_target):
            return r
        r_norm_name = r.rule_name.lower().replace("-", "_").replace(" ", "_").strip()
        if r_norm_name in (norm, alias_target) or alias_target in r_norm_name:
            return r

    return None


def registry_hash() -> str:
    """
    SHA-256 hash of all registered rules, used for experiment reproducibility.
    Serializes (rule_id, rule_version) tuples in sorted order.
    """
    return _registry.hash()


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _registry.clear()
