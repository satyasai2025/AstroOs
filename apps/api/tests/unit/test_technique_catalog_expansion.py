"""
AstroOS — Technique Catalog Expansion Unit & Integration Tests

Proves that newly added techniques:
  - Ruchaka Yoga (Mars)
  - Bhadra Yoga (Mercury)
  - Hamsa Yoga (Jupiter)
  - Malavya Yoga (Venus)
  - Shasha Yoga (Saturn)
  - Parashari Marriage Timing
  - Classical Dhana Yoga (2nd/11th/9th)

execute correctly through the exact same unchanged TechniqueEngine and RuleEngine,
generating accurate triggers, evidence, and confidence.
"""

import importlib
import pytest
from apps.api.domain.facts import Fact
from apps.api.domain.technique import TriggerStatus
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.technique_engine import TechniqueEngine, to_prediction_evidence
from apps.api.services.technique_resolver import TechniqueResolver
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry


@pytest.fixture(autouse=True)
def isolated_registries():
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()

    import apps.api.services.techniques.panch_mahapurusha as _pm
    import apps.api.services.techniques.marriage_timing as _mt
    import apps.api.services.techniques.wealth_dhana as _wd
    import apps.api.services.techniques.gajakesari_yoga as _gj
    import apps.api.services.techniques.eye_health as _eye
    import apps.api.services.techniques.event_timing_migrated as _et

    importlib.reload(_pm)
    importlib.reload(_mt)
    importlib.reload(_wd)
    importlib.reload(_gj)
    importlib.reload(_eye)
    importlib.reload(_et)
    yield


def test_panch_mahapurusha_catalog_registration():
    """Verify all 5 Panch Mahapurusha Yogas are registered and discoverable by objective."""
    resolver = TechniqueResolver()
    mahapurushas = resolver.resolve_by_objective("panch_mahapurusha")
    tech_ids = {t.technique_id for t in mahapurushas}
    assert "ruchaka_yoga" in tech_ids
    assert "bhadra_yoga" in tech_ids
    assert "hamsa_yoga" in tech_ids
    assert "malavya_yoga" in tech_ids
    assert "shasha_yoga" in tech_ids


def test_ruchaka_yoga_execution_pass_and_fail():
    """Mars in House 1 exalted (Capricorn) forms Ruchaka Yoga."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("ruchaka_yoga")
    assert tech is not None

    # Pass: Mars in House 1, Exalted
    facts_pass = FactRegistry()
    facts_pass.add_fact(Fact("planet.mars.house", 1, "test"))
    facts_pass.add_fact(Fact("planet.mars.exalted", True, "test"))
    facts_pass.add_fact(Fact("planet.mars.own_sign", False, "test"))
    facts_pass.add_fact(Fact("planet.mars.combust", False, "test"))

    res_pass = TechniqueEngine().execute(tech, facts_pass)
    assert res_pass.confidence == 100
    assert len(res_pass.primary) == 1
    assert res_pass.primary[0].rule_id == "MAHA-RUCH-001"
    assert res_pass.primary[0].status == TriggerStatus.TRIGGERED

    # Fail: Mars in House 6 (Dusthana - not a Kendra)
    facts_fail = FactRegistry()
    facts_fail.add_fact(Fact("planet.mars.house", 6, "test"))
    facts_fail.add_fact(Fact("planet.mars.exalted", True, "test"))
    facts_fail.add_fact(Fact("planet.mars.own_sign", False, "test"))
    facts_fail.add_fact(Fact("planet.mars.combust", False, "test"))

    res_fail = TechniqueEngine().execute(tech, facts_fail)
    assert len(res_fail.primary) == 0
    pred_fail = to_prediction_evidence(tech, res_fail)
    assert pred_fail.is_matched is False


def test_malavya_yoga_execution():
    """Venus in House 7 in own sign (Taurus/Libra) forms Malavya Yoga."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("malavya_yoga")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.venus.house", 7, "test"))
    facts.add_fact(Fact("planet.venus.exalted", False, "test"))
    facts.add_fact(Fact("planet.venus.own_sign", True, "test"))
    facts.add_fact(Fact("planet.venus.combust", False, "test"))

    res = TechniqueEngine().execute(tech, facts)
    assert res.confidence == 100
    assert res.primary[0].rule_id == "MAHA-MAL-001"
    assert res.primary[0].status == TriggerStatus.TRIGGERED

    pred = to_prediction_evidence(tech, res)
    assert pred.is_matched is True


def test_marriage_timing_execution():
    """Venus in House 4 with Venus Mahadasha and Jupiter in House 7 triggers Marriage Timing."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("marriage_timing")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("dasha.current_mahadasha", "venus", "test"))
    facts.add_fact(Fact("dasha.antardasha_lord", "mercury", "test"))
    facts.add_fact(Fact("planet.venus.house", 4, "test"))
    facts.add_fact(Fact("planet.jupiter.house", 7, "test"))

    res = TechniqueEngine().execute(tech, facts)
    assert res.confidence == 100
    assert len(res.primary) == 2
    assert any(t.rule_id == "MARR-VIM-001" for t in res.primary)
    assert any(t.rule_id == "MARR-7TH-001" for t in res.primary)
    assert any(t.rule_id == "MARR-JUP-001" for t in res.supporting)


def test_dhana_yoga_wealth_execution():
    """2nd lord in 11th house and 9th lord in 1st house triggers Dhana Yoga."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("dhana_yoga")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("house.2.lord_house", 11, "test"))
    facts.add_fact(Fact("house.11.lord_house", 5, "test"))
    facts.add_fact(Fact("house.1.lord_house", 1, "test"))
    facts.add_fact(Fact("house.9.lord_house", 1, "test"))
    facts.add_fact(Fact("house.5.lord_house", 5, "test"))

    res = TechniqueEngine().execute(tech, facts)
    assert res.confidence == 100
    assert len(res.primary) == 1
    assert res.primary[0].rule_id == "DHAN-2-11-001"
    assert len(res.supporting) >= 1
    assert any(t.rule_id == "DHAN-9TH-001" for t in res.supporting)
    assert res.supporting[0].rule_id == "DHAN-9TH-001"