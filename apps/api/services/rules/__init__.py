"""
AstroOS — Rule Modules (Module 13)

Importing this package registers every rule module's RuleDefinitions
into the rule_registry. Phase 1: 20 rules across 4 categories
(dignity/house, yoga, strength, transit). Phase 2: +8 more — 4 new
"planetary state" rules using previously-unused retrograde/combust
facts, a new house_lord category (using a new house.N.lord_house
fact), 4 more yoga rules, and a new compound-rules category
demonstrating multi-condition AND semantics across fact categories.
28 rules total — still deliberately not attempting the full classical
rule catalog.
"""

from apps.api.services.rules import (  # noqa: F401
    compound_rules,
    dignity_rules,
    house_lord_rules,
    strength_rules,
    transit_rules,
    yoga_rules,
)
