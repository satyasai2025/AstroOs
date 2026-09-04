"""
AstroOS — Technique Framework End-to-End Test Suite

Verifies the complete pipeline:
  Active Chart
      ↓
  Canonical Chart Facts (FactBuilder)
      ↓
  Technique Resolver (TechniqueResolver)
      ↓
  TechniqueEngine
      ↓
  Rules & Rule Evaluation (RuleEngine)
      ↓
  Evidence & Analysis (TechniqueExecutionResult)
      ↓
  Prediction Result (PredictionEvidence)
      ↓
  AI Explanation (AIEngine / TechniqueExplainer)

Covers all required acceptance points:
  A. Technique registration
  B. Technique lookup/resolution
  C. Rule execution
  D. Rule pass/fail behaviour
  E. Evidence generation
  F. Full technique execution against a real/test chart
  G. Structured result returned by API / Execution mapping
  H. Invalid technique handling (missing facts -> INSUFFICIENT_DATA)
  I. Version and source metadata preservation
"""

import uuid
from datetime import datetime, timezone
import pytest

from apps.api.domain.ai import AIResponse, Citation
from apps.api.domain.ephemeris import Ascendant, HouseCusp, SiderealPosition
from apps.api.domain.facts import Fact
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.rules import Condition, ConditionGroup, Conclusion, RuleDefinition
from apps.api.domain.technique import (
    DataAvailability,
    ProvenanceStatus,
    RuleRole,
    TechniqueDefinition,
    TechniqueRuleRef,
    TriggerStatus,
)
from apps.api.domain.technique_import import SourceType, TechniqueSource
from apps.api.services.ai_engine import AIEngine
from apps.api.services.fact_builder import FactBuilder
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.rule_engine import RuleEngine
import apps.api.services.rule_registry as rule_registry
import apps.api.services.technique_registry as technique_registry
from apps.api.services.technique_engine import TechniqueEngine, to_prediction_evidence
from apps.api.services.technique_import_pipeline import TechniqueImportPipeline
from apps.api.services.technique_resolver import TechniqueResolver


@pytest.fixture(autouse=True)
def isolated_registries(monkeypatch):
    """Ensure clean isolated registries for every test while retaining loaded fixtures."""
    rule_registry._registry._items.clear()
    technique_registry._registry._items.clear()

    # Re-import fixtures
    import apps.api.services.techniques.eye_health as _eye
    import apps.api.services.techniques.event_timing_migrated as _et
    import apps.api.services.techniques.gajakesari_yoga as _gj
    import importlib
    importlib.reload(_eye)
    importlib.reload(_et)
    importlib.reload(_gj)
    yield


def _build_full_chart(moon_house=1, jupiter_house=4):
    """Helper to build a complete 9-planet D1Chart suitable for all engine calculations."""
    asc = Ascendant(
        longitude=10.0, sidereal_longitude=10.0, rashi="aries", rashi_degree=10.0,
        nakshatra="ashwini", pada=1,
    )
    # 12 rashis in order
    rashis = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    moon_rashi = rashis[(moon_house - 1) % 12]
    jup_rashi = rashis[(jupiter_house - 1) % 12]

    planets = [
        SiderealPosition(
            planet="sun", sidereal_longitude=30.0, rashi="taurus", rashi_degree=0.0,
            house_number=2, nakshatra="krittika", pada=2, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="moon", sidereal_longitude=float((moon_house - 1) * 30 + 15), rashi=moon_rashi, rashi_degree=15.0,
            house_number=moon_house, nakshatra="bharani", pada=1, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="mars", sidereal_longitude=60.0, rashi="gemini", rashi_degree=0.0,
            house_number=3, nakshatra="mrigashira", pada=3, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="mercury", sidereal_longitude=90.0, rashi="cancer", rashi_degree=0.0,
            house_number=4, nakshatra="punarvasu", pada=4, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="jupiter", sidereal_longitude=float((jupiter_house - 1) * 30 + 15), rashi=jup_rashi, rashi_degree=15.0,
            house_number=jupiter_house, nakshatra="pushya", pada=2, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="venus", sidereal_longitude=120.0, rashi="leo", rashi_degree=0.0,
            house_number=5, nakshatra="magha", pada=1, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="saturn", sidereal_longitude=150.0, rashi="virgo", rashi_degree=0.0,
            house_number=6, nakshatra="uttara_phalguni", pada=2, is_retrograde=False, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="rahu", sidereal_longitude=180.0, rashi="libra", rashi_degree=0.0,
            house_number=7, nakshatra="chitra", pada=3, is_retrograde=True, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
        SiderealPosition(
            planet="ketu", sidereal_longitude=0.0, rashi="aries", rashi_degree=0.0,
            house_number=1, nakshatra="ashwini", pada=1, is_retrograde=True, is_combust=False,
            combustion_orb=None, dignity=None,
        ),
    ]
    houses = [
        HouseCusp(house_number=n, longitude=float((n - 1) * 30), sidereal_longitude=float((n - 1) * 30), rashi=rashis[n - 1])
        for n in range(1, 13)
    ]
    return D1Chart(
        ephemeris=None,
        ascendant=asc,
        houses=houses,
        planets=planets,
        aspects=[],
        planet_strengths=[],
        panchanga=None,
        ayanamsa_system="lahiri",
        house_system="W",
    )


# ── A. Technique Registration ───────────────────────────────────────────────────


def test_technique_registration_and_catalog():
    """Verify built-in techniques are registered in the technique registry with proper metadata."""
    tech = technique_registry.get_technique("gajakesari_yoga")
    assert tech is not None
    assert tech.technique_id == "gajakesari_yoga"
    assert tech.version == 1
    assert tech.objective == "raja_yoga"
    assert tech.tradition == "Parashari"
    assert len(tech.rule_refs) >= 1

    eye = technique_registry.get_technique("eye_health")
    assert eye is not None
    assert eye.technique_id == "eye_health"


# ── B. Technique Lookup & Resolution ───────────────────────────────────────────


def test_technique_resolver_lookup():
    """Verify TechniqueResolver resolves techniques by ID, objective, and fact applicability."""
    resolver = TechniqueResolver()

    # 1. Resolve by ID
    tech = resolver.resolve_by_id("gajakesari_yoga")
    assert tech is not None
    assert tech.name == "Gajakesari Yoga"

    # 2. Resolve by objective
    yoga_techs = resolver.resolve_by_objective("raja_yoga")
    assert any(t.technique_id == "gajakesari_yoga" for t in yoga_techs)

    # 3. Resolve applicable against FactRegistry
    facts = FactRegistry()
    facts.add_fact(Fact("planet.moon.house", 1, "test"))
    facts.add_fact(Fact("planet.jupiter.house", 4, "test"))

    applicable = resolver.resolve_applicable(facts, objective="raja_yoga")
    assert any(t.technique_id == "gajakesari_yoga" for t in applicable)


# ── C. Rule Execution & D. Pass/Fail Behaviour ──────────────────────────────────


def test_rule_execution_and_pass_fail():
    """Verify RuleEngine independently evaluates conditions and records matched/failed condition details."""
    engine = RuleEngine()

    facts_pass = FactRegistry()
    facts_pass.add_fact(Fact("planet.moon.house", 1, "test"))
    facts_pass.add_fact(Fact("planet.jupiter.house", 4, "test"))

    result_pass = engine.evaluate("GAJA-001", facts_pass)
    assert result_pass.matched is True
    assert len(result_pass.matched_conditions) > 0
    assert len(result_pass.failed_conditions) == 0

    facts_fail = FactRegistry()
    facts_fail.add_fact(Fact("planet.moon.house", 1, "test"))
    facts_fail.add_fact(Fact("planet.jupiter.house", 6, "test"))

    result_fail = engine.evaluate("GAJA-001", facts_fail)
    assert result_fail.matched is False
    assert len(result_fail.failed_conditions) > 0


# ── E. Evidence Generation ─────────────────────────────────────────────────────


def test_evidence_generation_and_confidence_basis():
    """Verify TechniqueEngine produces structured triggers, input availability, and traceable confidence basis."""
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("gajakesari_yoga")
    assert tech is not None

    facts = FactRegistry()
    facts.add_fact(Fact("planet.moon.house", 1, "test"))
    facts.add_fact(Fact("planet.jupiter.house", 4, "test"))
    facts.add_fact(Fact("planet.jupiter.exalted", True, "test"))
    facts.add_fact(Fact("planet.jupiter.own_sign", False, "test"))
    facts.add_fact(Fact("planet.jupiter.combust", False, "test"))

    result = TechniqueEngine().execute(tech, facts)

    assert result.confidence == 100
    assert "primary rules triggered" in result.confidence_basis
    assert len(result.primary) == 1
    trigger = result.primary[0]
    assert trigger.rule_id == "GAJA-001"
    assert trigger.status == TriggerStatus.TRIGGERED
    assert len(trigger.matched_conditions) > 0
    assert len(result.evidence) > 0


# ── F. Full End-to-End Pipeline Against Chart ──────────────────────────────────


def test_full_pipeline_active_chart_to_ai_explanation():
    """
    Test the complete 8-stage pipeline:
      Active Chart -> FactBuilder -> TechniqueResolver -> TechniqueEngine ->
      Rules/Evaluation -> Evidence/Analysis -> Prediction -> AI Explanation
    """
    chart_pos = _build_full_chart(moon_house=1, jupiter_house=4)
    chart_neg = _build_full_chart(moon_house=1, jupiter_house=6)

    # 1. FactBuilder extracts canonical facts from D1Chart
    fact_builder = FactBuilder()
    facts_positive = fact_builder.build_facts(chart_pos)

    assert facts_positive.has_fact("planet.moon.house")
    assert facts_positive.get_fact("planet.moon.house").value == 1
    assert facts_positive.has_fact("planet.jupiter.house")
    assert facts_positive.get_fact("planet.jupiter.house").value == 4

    # 2. TechniqueResolver resolves candidate technique
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("gajakesari_yoga")
    assert tech is not None

    # 3. TechniqueEngine evaluates against facts
    exec_result_positive = TechniqueEngine().execute(tech, facts_positive)
    assert exec_result_positive.confidence == 100
    assert len(exec_result_positive.primary) == 1
    assert exec_result_positive.primary[0].status == TriggerStatus.TRIGGERED

    # 4. Prediction evidence adapter
    prediction_positive = to_prediction_evidence(tech, exec_result_positive)
    assert prediction_positive.is_matched is True
    assert prediction_positive.confidence.score == 100
    assert "GAJA-001" in prediction_positive.triggering_conditions

    # 5. AI Explanation generation
    ai_resp_positive = AIEngine.explain_technique(tech, exec_result_positive)
    assert isinstance(ai_resp_positive, AIResponse)
    assert ai_resp_positive.response_type == "technique_explanation"
    assert "Gajakesari Yoga" in ai_resp_positive.title
    assert "100%" in ai_resp_positive.title
    assert "Triggered Primary Indications:" in ai_resp_positive.body
    assert "GAJA-001" in ai_resp_positive.body

    # ── Negative case (Moon in 1, Jupiter in 6) ─────────────────────────────────
    facts_negative = fact_builder.build_facts(chart_neg)
    exec_result_negative = TechniqueEngine().execute(tech, facts_negative)
    assert exec_result_negative.confidence == 0
    assert len(exec_result_negative.primary) == 0

    prediction_negative = to_prediction_evidence(tech, exec_result_negative)
    assert prediction_negative.is_matched is False
    assert prediction_negative.confidence.score == 0

    ai_resp_negative = AIEngine.explain_technique(tech, exec_result_negative)
    assert "No primary indications were triggered" in ai_resp_negative.body


# ── G. Structured Result & H. Invalid Technique Handling ────────────────────────


def test_invalid_technique_missing_facts_and_unregistered_rule():
    """Verify missing facts report INSUFFICIENT_DATA honestly rather than fabricating a result."""
    # 1. Technique with missing facts
    resolver = TechniqueResolver()
    tech = resolver.resolve_by_id("gajakesari_yoga")
    empty_facts = FactRegistry()

    result = TechniqueEngine().execute(tech, empty_facts)
    assert result.confidence == 0
    assert len(result.triggers) == len(tech.rule_refs)
    assert all(t.status == TriggerStatus.INSUFFICIENT_DATA for t in result.triggers)
    assert any("planet.moon.house" in t.missing_facts for t in result.triggers)

    # 2. Technique with an unregistered rule
    invalid_tech = TechniqueDefinition(
        technique_id="invalid_tech",
        name="Invalid Technique",
        version=1,
        rule_refs=(TechniqueRuleRef(rule_id="NON_EXISTENT_RULE", rule_version="1.0", role=RuleRole.PRIMARY),),
    )
    result_invalid = TechniqueEngine().execute(invalid_tech, empty_facts)
    assert result_invalid.confidence == 0
    assert result_invalid.triggers[0].status == TriggerStatus.INSUFFICIENT_DATA
    assert "not registered" in result_invalid.triggers[0].explanation


# ── I. Version and Source Metadata Preservation ─────────────────────────────────


def test_version_and_source_metadata_preservation():
    """Verify technique versioning, citations, and unresolved inconsistencies are preserved throughout."""
    eye = technique_registry.get_technique("eye_health")
    assert eye is not None
    assert eye.version == 1
    assert eye.provenance == ProvenanceStatus.UNTESTED
    assert len(eye.source_references) > 0
    assert len(eye.unresolved_inconsistencies) > 0

    facts = FactRegistry()
    result = TechniqueEngine().execute(eye, facts)
    assert result.technique_id == eye.technique_id
    assert result.technique_version == eye.version
    assert result.unresolved_inconsistencies == eye.unresolved_inconsistencies

    ai_resp = AIEngine.explain_technique(eye, result)
    assert "Preserved Source Inconsistencies:" in ai_resp.body
    assert len(ai_resp.citations) > 0