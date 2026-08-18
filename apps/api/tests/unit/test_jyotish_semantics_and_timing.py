"""
AstroOS — Rigorous Jyotish Semantics & Timing Intelligence Audit Test Suite

Tests specifically proving all 6 required architectural & sastric corrections:
  1. Ashtama Shani: Evaluates 8th strictly from natal Moon; 8th from Lagna does NOT trigger it.
  2. Career Timing: 3-tier hierarchy (Natal Promise -> Dasha Activation -> Gochara Trigger).
     Missing natal promise fails career prediction even with active Dasha and transit.
  3. Double Transit: Evaluated as K.N. Rao empirical heuristic with Dasha requirement.
  4. Sade Sati Mitigation: Core cycle detected; sign dignity is a separate supporting modifier.
  5. Decoupled Yoga Existence vs Strength:
     - Gajakesari: Kendra from Moon = PRESENT; dignity & combustion modulate strength separately.
     - Panch Mahapurusha: Kendra + Dignity sign = PRESENT; combustion is an affliction modifier.
  6. Granular Dhana Yoga: 2nd->11th, 11th->2nd, 9th->fortune, 5th->merit individually traced.
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

    import apps.api.services.techniques.timing_events as _te
    import apps.api.services.techniques.panch_mahapurusha as _pm
    import apps.api.services.techniques.marriage_timing as _mt
    import apps.api.services.techniques.wealth_dhana as _wd
    import apps.api.services.techniques.gajakesari_yoga as _gj
    import apps.api.services.techniques.eye_health as _eye
    import apps.api.services.techniques.event_timing_migrated as _et

    importlib.reload(_te)
    importlib.reload(_pm)
    importlib.reload(_mt)
    importlib.reload(_wd)
    importlib.reload(_gj)
    importlib.reload(_eye)
    importlib.reload(_et)
    yield


# ── 1. Ashtama Shani: 8th from Moon vs 8th from Lagna ─────────────────────────


def test_ashtama_shani_strictly_from_moon_negative_when_8th_from_lagna():
    """
    Negative Test: Saturn is in the 8th house from Lagna (in natal chart),
    but in transit Saturn is in house 4 from natal Moon (ashtama_shani == False).
    Ashtama Shani technique MUST NOT trigger.
    """
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("ashtama_shani_transit")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.saturn.house", 8, "test"))             # 8th from Lagna in natal D1
    facts.add_fact(Fact("transit.saturn.house", 4, "test"))            # 4th from Moon in transit
    facts.add_fact(Fact("transit.saturn.ashtama_shani", False, "test"))  # NOT 8th from Moon

    result = TechniqueEngine().execute(tech, facts)
    assert len(result.primary) == 0
    assert result.confidence == 0
    pred = to_prediction_evidence(tech, result)
    assert pred.is_matched is False


def test_ashtama_shani_triggers_when_8th_from_moon():
    """Positive Test: Saturn in transit is in the 8th house strictly from natal Moon."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("ashtama_shani_transit")

    facts = FactRegistry()
    facts.add_fact(Fact("transit.saturn.house", 8, "test"))             # 8th from Moon
    facts.add_fact(Fact("transit.saturn.ashtama_shani", True, "test"))   # Ashtama Shani active

    result = TechniqueEngine().execute(tech, facts)
    assert len(result.primary) == 1
    assert result.primary[0].rule_id == "TRN-ASHT-001"
    assert result.confidence == 100
    pred = to_prediction_evidence(tech, result)
    assert pred.is_matched is True


# ── 2. Career Timing: 3-Tier Hierarchy & Natal Promise Prerequisite ───────────


def test_career_timing_fails_without_natal_promise():
    """
    Negative Test: Favorable Jupiter transit + active Sun Dasha,
    BUT natal 10th lord is in 8th house (Dusthana - No strong natal career promise).
    Must NOT produce a full career prediction.
    """
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("career_elevation_timing")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("house.10.lord_house", 8, "test"))             # 10th lord in 8th (No natal promise)
    facts.add_fact(Fact("dasha.current_mahadasha", "sun", "test"))     # Dasha active
    facts.add_fact(Fact("transit.jupiter.house", 10, "test"))          # Jupiter in 10th from Moon

    result = TechniqueEngine().execute(tech, facts)
    # Natal promise rule failed -> only 1 of 2 primary rules triggered
    assert not any(t.rule_id == "TIM-CAR-PROMISE-001" and t.status == TriggerStatus.TRIGGERED for t in result.triggers)
    assert result.confidence < 100
    assert "Candidate timing window only" in tech.description


def test_career_timing_succeeds_with_full_hierarchy():
    """Positive Test: Natal Promise (10th lord in 10th) + Dasha (Sun) + Gochara (Jupiter in 10th)."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("career_elevation_timing")

    facts = FactRegistry()
    facts.add_fact(Fact("house.10.lord_house", 10, "test"))            # 10th lord in 10th (Kendra)
    facts.add_fact(Fact("dasha.current_mahadasha", "sun", "test"))
    facts.add_fact(Fact("transit.jupiter.house", 10, "test"))

    result = TechniqueEngine().execute(tech, facts)
    assert result.confidence == 100
    assert len(result.primary) == 2
    assert any(t.rule_id == "TIM-CAR-PROMISE-001" for t in result.primary)
    assert any(t.rule_id == "TIM-CAR-DASH-001" for t in result.primary)
    assert any(t.rule_id == "TIM-CAR-GOCHARA-001" for t in result.supporting)


# ── 3. Double Transit: Methodology-Specific Heuristic ─────────────────────────


def test_double_transit_classified_as_heuristic_and_requires_dasha():
    """Double transit is scoped as K.N. Rao modern empirical research methodology."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("double_transit_marriage")
    assert tech is not None
    assert "K.N. Rao" in tech.tradition

    # Transit present without Dasha -> primary rule not fulfilled
    facts = FactRegistry()
    facts.add_fact(Fact("dasha.current_mahadasha", "saturn", "test"))
    facts.add_fact(Fact("dasha.antardasha_lord", "mercury", "test"))
    facts.add_fact(Fact("transit.jupiter.house_from_venus", 7, "test"))
    facts.add_fact(Fact("transit.saturn.house_from_venus", 7, "test"))

    result = TechniqueEngine().execute(tech, facts)
    assert result.confidence == 50  # Dasha primary rule failed


# ── 4. Sade Sati: Existence vs Optional Mitigation ────────────────────────────


def test_sade_sati_with_mitigating_dignity():
    """
    Sade Sati remains PRESENT when Saturn is in 12/1/2 from Moon,
    and sign dignity in Libra/Capricorn/Aquarius is reported as a separate supporting modifier.
    """
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("sade_sati_cycle")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("transit.saturn.sade_sati", True, "test"))
    facts.add_fact(Fact("transit.saturn.house", 1, "test"))
    facts.add_fact(Fact("transit.saturn.rashi", "libra", "test"))

    result = TechniqueEngine().execute(tech, facts)
    assert len(result.primary) == 1
    assert result.primary[0].rule_id == "TRN-SADE-001"
    assert result.primary[0].status == TriggerStatus.TRIGGERED
    assert len(result.supporting) == 1
    assert result.supporting[0].rule_id == "TRN-SADE-MIT-001"
    assert result.confidence == 100


# ── 5. Yoga Existence vs Strength vs Affliction Modifiers ─────────────────────


def test_gajakesari_weak_dignity_remains_present_with_lower_strength():
    """
    Gajakesari Kendra condition present with non-dignified Jupiter (e.g. neutral sign):
    Yoga remains PRESENT (existence rule triggered), but dignity modifier rule does not fire.
    """
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("gajakesari_yoga")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.moon.house", 1, "test"))
    facts.add_fact(Fact("planet.jupiter.house", 4, "test"))
    facts.add_fact(Fact("planet.jupiter.exalted", False, "test"))
    facts.add_fact(Fact("planet.jupiter.own_sign", False, "test"))
    facts.add_fact(Fact("planet.jupiter.combust", False, "test"))

    result = TechniqueEngine().execute(tech, facts)
    # Existence is verified
    assert len(result.primary) == 1
    assert result.primary[0].rule_id == "GAJA-001"
    assert result.primary[0].status == TriggerStatus.TRIGGERED
    # Dignity modifier is not triggered
    assert len(result.supporting) == 0
    pred = to_prediction_evidence(tech, result)
    assert pred.is_matched is True


def test_panch_mahapurusha_with_combustion_retains_core_configuration():
    """
    Ruchaka Yoga: Mars in Kendra in Aries (Own sign), but combust by the Sun.
    Core existence rule is TRIGGERED, but combustion affliction rule is also triggered (penalizing output).
    """
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("ruchaka_yoga")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.mars.house", 1, "test"))
    facts.add_fact(Fact("planet.mars.exalted", False, "test"))
    facts.add_fact(Fact("planet.mars.own_sign", True, "test"))
    facts.add_fact(Fact("planet.mars.combust", True, "test"))

    result = TechniqueEngine().execute(tech, facts)
    # Core formation / existence is triggered
    assert len(result.primary) == 1
    assert result.primary[0].rule_id == "MAHA-RUCH-001"
    assert result.primary[0].status == TriggerStatus.TRIGGERED
    # Combustion affliction is triggered
    assert len(result.contradicting) == 1
    assert result.contradicting[0].rule_id == "MAHA-RUCH-COMBUST"
    assert result.contradicting[0].status == TriggerStatus.TRIGGERED
    # Confidence is penalized by combustion
    assert result.confidence < 100


# ── 6. Granular Dhana Yoga Lord Relationships (BPHS Ch. 41) ───────────────────


def test_dhana_yoga_granular_combinations_individually_traced():
    """
    Each tested lord relationship is individually traced and verified:
    - 2nd lord in 11th (DHAN-2TO11-001)
    - 9th lord in 5th (DHAN-9TH-001)
    - 5th lord in 9th (DHAN-5TH-001)
    """
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("dhana_yoga")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("house.2.lord_house", 11, "test"))  # 2nd in 11th
    facts.add_fact(Fact("house.11.lord_house", 4, "test"))  # 11th in 4th (not 2nd)
    facts.add_fact(Fact("house.9.lord_house", 5, "test"))   # 9th in 5th (fortune in trine)
    facts.add_fact(Fact("house.5.lord_house", 9, "test"))   # 5th in 9th (merit in fortune)

    result = TechniqueEngine().execute(tech, facts)
    # Primary Dhana-Labha rule is triggered
    assert any(t.rule_id == "DHAN-2-11-001" and t.status == TriggerStatus.TRIGGERED for t in result.primary)
    # 9th and 5th lords are triggered
    assert any(t.rule_id == "DHAN-9TH-001" and t.status == TriggerStatus.TRIGGERED for t in result.supporting)
    assert any(t.rule_id == "DHAN-5TH-001" and t.status == TriggerStatus.TRIGGERED for t in result.supporting)
    assert result.confidence == 100