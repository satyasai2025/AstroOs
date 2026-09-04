"""
AstroOS — HypothesisGenerator Unit Tests (Phase E)
"""

from __future__ import annotations

import pytest

from apps.api.domain.ai_phase_e import GeneratedHypothesis, HypothesisTemplate
from apps.api.domain.ephemeris import Ascendant, DignityType, HouseCusp, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.yoga import YogaResult
from apps.api.services.hypothesis_generator import HypothesisGenerator
from apps.api.services.knowledge_graph_engine import KnowledgeGraphEngine
from apps.api.services.ontology_registry import build_default_ontology


def _make_chart(exalted_planets: list[str] | None = None,
                debilitated_planets: list[str] | None = None) -> D1Chart:
    exalted = set(exalted_planets or [])
    debilitated = set(debilitated_planets or [])
    planets = [
        SiderealPosition(planet="sun", sidereal_longitude=10.0, rashi="aries",
            rashi_degree=10.0, house_number=1, nakshatra="ashwini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.EXALTED if "sun" in exalted else DignityType.OWN),
        SiderealPosition(planet="moon", sidereal_longitude=40.0, rashi="taurus",
            rashi_degree=10.0, house_number=2, nakshatra="rohini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="mars", sidereal_longitude=100.0, rashi="cancer",
            rashi_degree=10.0, house_number=5, nakshatra="pushya", pada=2,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.EXALTED if "mars" in exalted else DignityType.MOOLATRIKONA),
        SiderealPosition(planet="jupiter", sidereal_longitude=200.0, rashi="libra",
            rashi_degree=15.0, house_number=7, nakshatra="swati", pada=3,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="venus", sidereal_longitude=300.0, rashi="capricorn",
            rashi_degree=5.0, house_number=10, nakshatra="uttara ashadha", pada=4,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.DEBILITATED if "venus" in debilitated else DignityType.OWN),
        SiderealPosition(planet="saturn", sidereal_longitude=350.0, rashi="pisces",
            rashi_degree=20.0, house_number=12, nakshatra="revati", pada=3,
            is_retrograde=True, is_combust=False, combustion_orb=None,
            dignity=DignityType.DEBILITATED if "saturn" in debilitated else DignityType.FRIENDLY),
    ]
    asc = Ascendant(longitude=10.0, sidereal_longitude=10.0, rashi="aries",
                    rashi_degree=10.0, nakshatra="ashwini", pada=1)
    houses = [HouseCusp(house_number=n, longitude=float(n * 30),
                        sidereal_longitude=float(n * 30), rashi="")
              for n in range(1, 13)]
    return D1Chart(ephemeris=None, ascendant=asc, houses=houses, planets=planets,
                   aspects=[], planet_strengths=[], panchanga=None,
                   ayanamsa_system="lahiri", house_system="W")


def _default_kg() -> KnowledgeGraphEngine:
    return KnowledgeGraphEngine(build_default_ontology())


class TestHypothesisGenerator:
    def test_get_templates(self):
        templates = HypothesisGenerator.get_templates()
        assert len(templates) == 8
        assert all(isinstance(t, HypothesisTemplate) for t in templates)
        assert all(t.hypothesis_id.startswith("HYP-") for t in templates)

    def test_get_template_known(self):
        ht = HypothesisGenerator.get_template("HYP-001")
        assert ht is not None
        assert ht.title == "Exaltation Strength Correlation"

    def test_get_template_unknown(self):
        ht = HypothesisGenerator.get_template("HYP-999")
        assert ht is None

    def test_generate_for_chart_with_exalted_planets(self):
        chart = _make_chart(exalted_planets=["sun", "mars"])
        yogas = [YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                            source_text="BPHS", rule_version="1.0", is_present=True,
                            strength="full")]
        hypotheses = HypothesisGenerator.generate_for_chart(chart, yogas=yogas)
        assert len(hypotheses) > 0
        ids = {h.hypothesis_id for h in hypotheses}
        assert "HYP-001" in ids  # Exaltation Strength Correlation

    def test_generate_for_chart_with_debilitated_planets(self):
        chart = _make_chart(debilitated_planets=["venus", "saturn"])
        yogas = []
        hypotheses = HypothesisGenerator.generate_for_chart(chart, yogas=yogas)
        ids = {h.hypothesis_id for h in hypotheses}
        assert "HYP-008" in ids  # Debilitation Compensation

    def test_generate_with_domain_filter(self):
        chart = _make_chart(exalted_planets=["sun"])
        hypotheses = HypothesisGenerator.generate_for_chart(
            chart, domain_filter="dignity", max_hypotheses=10,
        )
        assert all(h.domain == "dignity" for h in hypotheses)

    def test_generate_respects_max_hypotheses(self):
        chart = _make_chart(exalted_planets=["sun", "mars"],
                            debilitated_planets=["venus", "saturn"])
        hypotheses = HypothesisGenerator.generate_for_chart(chart, max_hypotheses=3)
        assert len(hypotheses) <= 3

    def test_all_hypotheses_have_required_fields(self):
        chart = _make_chart(exalted_planets=["sun", "mars"],
                            debilitated_planets=["venus", "saturn"])
        yogas = [YogaResult(yoga_id="BPHS-RJ-001", name="Raja Yoga", category="raja",
                            source_text="BPHS", rule_version="1.0", is_present=True,
                            strength="partial")]
        hypotheses = HypothesisGenerator.generate_for_chart(chart, yogas=yogas, max_hypotheses=10)
        for h in hypotheses:
            assert isinstance(h, GeneratedHypothesis)
            assert h.hypothesis_id
            assert h.title
            assert h.description
            assert h.domain
            assert h.testable_prediction
            assert len(h.supporting_evidence) > 0
            assert 1 <= h.priority <= 10


class TestHypothesisDomain:
    def test_template_defaults(self):
        t = HypothesisTemplate(
            hypothesis_id="HYP-999",
            title="Test",
            description="A test template",
            domain="test",
            conditions=("cond1",),
            expected_outcome="Outcome",
            test_method="TestMethod",
        )
        assert t.priority == 5
        assert t.classical_references == ()

    def test_generated_confidence_default(self):
        h = GeneratedHypothesis(
            hypothesis_id="HYP-001", title="T", description="D", domain="test",
            supporting_evidence=("ev1",), contradicting_evidence=(),
            testable_prediction="P", suggested_dataset="GC-MASTER", priority=5,
        )
        assert h.confidence == "medium"

    def test_generated_graph_grounded_default(self):
        """graph_grounded defaults to False."""
        h = GeneratedHypothesis(
            hypothesis_id="HYP-001", title="T", description="D", domain="test",
            supporting_evidence=("ev1",), contradicting_evidence=(),
            testable_prediction="P", suggested_dataset="GC-MASTER", priority=5,
        )
        assert h.graph_grounded is False

    def test_generated_graph_grounded_custom(self):
        """graph_grounded can be set to True."""
        h = GeneratedHypothesis(
            hypothesis_id="HYP-001", title="T", description="D", domain="test",
            supporting_evidence=("ev1",), contradicting_evidence=(),
            testable_prediction="P", suggested_dataset="GC-MASTER", priority=5,
            graph_grounded=True,
        )
        assert h.graph_grounded is True


class TestHypothesisGeneratorWithKG:
    """Tests for KG-aware hypothesis generation."""

    def test_kg_adds_evidence_for_exalted(self):
        """KG evidence is appended for exalted planets."""
        chart = _make_chart(exalted_planets=["sun", "mars"])
        kg = _default_kg()
        hypotheses = HypothesisGenerator.generate_for_chart(
            chart, yogas=[], knowledge_graph=kg,
        )
        hyp_001 = next((h for h in hypotheses if h.hypothesis_id == "HYP-001"), None)
        assert hyp_001 is not None
        assert hyp_001.graph_grounded is True
        # Check that at least one KG evidence string was added.
        kg_evidence = [e for e in hyp_001.supporting_evidence if e.startswith("KG:")]
        assert len(kg_evidence) > 0

    def test_kg_adds_evidence_for_debilitated(self):
        """KG evidence is appended for debilitated planets."""
        chart = _make_chart(debilitated_planets=["venus", "saturn"])
        kg = _default_kg()
        hypotheses = HypothesisGenerator.generate_for_chart(
            chart, yogas=[], knowledge_graph=kg,
        )
        hyp_008 = next((h for h in hypotheses if h.hypothesis_id == "HYP-008"), None)
        assert hyp_008 is not None
        assert hyp_008.graph_grounded is True
        kg_evidence = [e for e in hyp_008.supporting_evidence if e.startswith("KG:")]
        assert len(kg_evidence) > 0

    def test_kg_does_not_break_without_kg(self):
        """generate_for_chart works when no KG is provided."""
        chart = _make_chart(exalted_planets=["sun"])
        hypotheses = HypothesisGenerator.generate_for_chart(chart, yogas=[])
        assert len(hypotheses) > 0
        for h in hypotheses:
            assert hasattr(h, "graph_grounded")

    def test_kg_adds_house_data_for_ashtakavarga(self):
        """KG adds dusthana house data for HYP-004."""
        chart = _make_chart()
        kg = _default_kg()
        hypotheses = HypothesisGenerator.generate_for_chart(
            chart, yogas=[], domain_filter="ashtakavarga", knowledge_graph=kg,
        )
        hyp_004 = next((h for h in hypotheses if h.hypothesis_id == "HYP-004"), None)
        assert hyp_004 is not None
        assert hyp_004.graph_grounded is True
        dusthana_evidence = [e for e in hyp_004.supporting_evidence if "dusthana" in e.lower()]
        assert len(dusthana_evidence) > 0