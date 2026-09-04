"""
AstroOS — Rule Modules (Module 13 Phase B)

Importing this package registers every rule module's RuleDefinitions
into the rule_registry. Phase 1: 28 rules across 6 categories.
Phase B: +11 more across 3 new categories (dasha, temporal, varga),
using the new IN/NOT_IN operators and ConditionGroup OR support.
39 rules total across 9 categories.
"""

from apps.api.services.rules import (  # noqa: F401
    compound_rules,
    dasha_rules,
    dignity_rules,
    house_lord_rules,
    strength_rules,
    temporal_rules,
    transit_rules,
    varga_rules,
    yoga_rules,
)
