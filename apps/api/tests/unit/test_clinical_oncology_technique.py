"""
Unit tests for Clinical Oncology, Genetic Mutations & Surgical Resilience Technique
"""

from __future__ import annotations

import pytest
from apps.api.domain.facts import Fact
from apps.api.domain.technique import TriggerStatus
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.technique_engine import TechniqueEngine
from apps.api.services.technique_resolver import TechniqueResolver
import apps.api.services.rule_registry as rule_registry
import apps.api.services.techniques.clinical_oncology_genetics  # noqa: F401


def test_technique_registered():
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("clinical_oncology_genetics")
    assert tech is not None
    assert tech.technique_id == "clinical_oncology_genetics"
    assert len(tech.rule_refs) == 9


def test_all_medical_rules_discoverable():
    rule_ids = [
        "MED-ONCO-001",
        "MED-GEN-002",
        "MED-SURG-003",
        "MED-HOUSE-004",
        "MED-YOGA-005",
        "MED-DREK-006",
        "MED-D30-007",
        "MED-SAHAM-008",
        "MED-DASHA-009",
    ]
    for rid in rule_ids:
        rule = rule_registry.get_rule(rid)
        assert rule is not None, f"Rule {rid} not found in rule_registry"
        assert rule.category.startswith("medical_")


def test_med_onco_001_execution():
    """Verify Rahu-Jupiter axis triggers oncology malignancy rule."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("clinical_oncology_genetics")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("aspect.rahu_jupiter_axis", True, "test"))
    facts.add_fact(Fact("planet.rahu.house", 12, "test"))
    facts.add_fact(Fact("planet.jupiter.house", 8, "test"))

    res = TechniqueEngine().execute(tech, facts)
    triggered_rids = {t.rule_id for t in res.primary if t.status == TriggerStatus.TRIGGERED}
    assert "MED-ONCO-001" in triggered_rids


def test_med_gen_002_execution():
    """Verify Debilitated Mercury + Ketu in 6th triggers genetic nerve mutation."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("clinical_oncology_genetics")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.mercury.debilitated", True, "test"))
    facts.add_fact(Fact("planet.ketu.house", 6, "test"))
    facts.add_fact(Fact("planet.mercury.rashi", "pisces", "test"))
    facts.add_fact(Fact("planet.mercury.house", 3, "test"))

    res = TechniqueEngine().execute(tech, facts)
    triggered_rids = {t.rule_id for t in res.primary if t.status == TriggerStatus.TRIGGERED}
    assert "MED-GEN-002" in triggered_rids


def test_med_surg_003_execution():
    """Verify Exalted Mars in Lagna triggers surgical resilience & pain tolerance."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("clinical_oncology_genetics")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.mars.exalted", True, "test"))
    facts.add_fact(Fact("planet.mars.house", 1, "test"))

    res = TechniqueEngine().execute(tech, facts)
    triggered_rids = {t.rule_id for t in res.primary if t.status == TriggerStatus.TRIGGERED}
    assert "MED-SURG-003" in triggered_rids


def test_med_dasha_009_execution():
    """Verify Rahu-Jupiter & Rahu-Saturn dasha triggers clinical timing trajectory."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("clinical_oncology_genetics")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("dasha.active_mahadasha_lord", "Rahu", "test"))
    facts.add_fact(Fact("dasha.active_antardasha_lord", "Jupiter", "test"))

    res = TechniqueEngine().execute(tech, facts)
    triggered_rids = {t.rule_id for t in res.primary if t.status == TriggerStatus.TRIGGERED}
    assert "MED-DASHA-009" in triggered_rids
