"""
AstroOS — AIEngine Unit Tests (Module 24, Phase 1)
"""

import uuid
from datetime import date

import pytest

from apps.api.domain.ai import AIResponse, Citation, ExplanationRequest
from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.statistics import AggregateReport, DatasetMetadata, Distribution
from apps.api.domain.timeline import Timeline, TimelineEntry, TimelineSummary
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.yoga import YogaResult
from apps.api.domain.verification import (
    Alignment,
    VerificationFindings,
    VerificationPair,
    VerificationStrength,
)
from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord
from apps.api.services.ai_engine import (
    AIEngine,
    ChartSummarizer,
    DashaIinterpreter,
    QAResponder,
    RecommendationEngine,
    ResearchInsightGenerator,
    TransitReader,
    VerificationReporter,
    YogaExplainer,
)


def _make_chart() -> D1Chart:
    from apps.api.domain.ephemeris import Ascendant, HouseCusp
    planets = [
        SiderealPosition(planet="sun", sidereal_longitude=10.0, rashi="aries",
            rashi_degree=10.0, house_number=1, nakshatra="ashwini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.OWN),
        SiderealPosition(planet="moon", sidereal_longitude=40.0, rashi="taurus",
            rashi_degree=10.0, house_number=2, nakshatra="rohini", pada=1,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.FRIENDLY),
        SiderealPosition(planet="jupiter", sidereal_longitude=130.0, rashi="cancer",
            rashi_degree=10.0, house_number=5, nakshatra="pushya", pada=2,
            is_retrograde=False, is_combust=False, combustion_orb=None,
            dignity=DignityType.EXALTED),
    ]
    asc = Ascendant(longitude=10.0, sidereal_longitude=10.0, rashi="aries",
                    rashi_degree=10.0, nakshatra="ashwini", pada=1)
    houses = [HouseCusp(house_number=n, longitude=float(n*30), sidereal_longitude=float(n*30), rashi="")
              for n in range(1, 13)]
    return D1Chart(ephemeris=None, ascendant=asc, houses=houses, planets=planets,
                   aspects=[], planet_strengths=[], panchanga=None,
                   ayanamsa_system="lahiri", house_system="W")


class TestChartSummarizer:
    def test_generates_summary(self):
        chart = _make_chart()
        result = ChartSummarizer.generate(chart)
        assert result.response_type == "chart_summary"
        assert "Aries" in result.title
        assert "Ascendant" in result.title
        assert "chart_engine" in result.sources
        assert len(result.body) > 0

    def test_confidence_from_verification(self):
        chart = _make_chart()
        vf = _make_verification(confirmed=True)
        result = ChartSummarizer.generate(chart, verification=vf)
        assert result.confidence == "high"

    def test_confidence_low_with_no_verification(self):
        chart = _make_chart()
        vf = _make_verification(confirmed=False)
        result = ChartSummarizer.generate(chart, verification=vf)
        assert result.confidence == "low"


class TestYogaExplainer:
    def test_present_yoga(self):
        yoga = YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                          source_text="BPHS", rule_version="1.0", is_present=True,
                          strength="full", involved_planets=("mars",), involved_houses=(1,))
        result = YogaExplainer.generate(yoga)
        assert result.response_type == "yoga_explanation"
        assert "Ruchaka" in result.title
        assert "Full" in result.title

    def test_not_present_yoga(self):
        yoga = YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                          source_text="BPHS", rule_version="1.0", is_present=False,
                          strength=None)
        result = YogaExplainer.generate(yoga)
        assert "Not Present" in result.title

    def test_with_citations(self):
        yoga = YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                          source_text="BPHS", rule_version="1.0", is_present=True,
                          strength="full", involved_planets=("mars",), involved_houses=(1,))
        cit = Citation(source="BPHS", reference="46.12", text="Ruchaka yoga description")
        result = YogaExplainer.generate(yoga, citations=(cit,))
        assert len(result.citations) == 1


class TestDashaIinterpreter:
    def test_generates_interpretation(self):
        period = DashaPeriod(lord="jupiter", start_date=date(2000,1,1), end_date=date(2010,1,1),
                             duration_days=3653, level=1, sub_periods=())
        chart = _make_chart()
        result = DashaIinterpreter.generate(period, chart)
        assert result.response_type == "dasha_interpretation"
        assert "Jupiter" in result.title
        assert "house 5" in result.body  # jupiter is in house 5

    def test_without_chart(self):
        period = DashaPeriod(lord="venus", start_date=date(2000,1,1), end_date=date(2010,1,1),
                             duration_days=3653, level=2, sub_periods=())
        result = DashaIinterpreter.generate(period)
        assert result.response_type == "dasha_interpretation"
        assert "Venus" in result.title


class TestTransitReader:
    def test_generates_reading(self):
        transits = (
            TransitPlanetResult(planet="saturn", transit_rashi="aquarius", house_from_natal_moon=8,
                                ashtakavarga_bindus=3, is_sade_sati=False, is_ashtama_shani=True),
        )
        result = TransitReader.generate(transits)
        assert result.response_type == "transit_reading"
        assert "Saturn" in result.body
        assert "Ashtama Shani" in result.body

    def test_empty_transits(self):
        result = TransitReader.generate(())
        assert "No transit data" in result.summary


class TestVerificationReporter:
    def test_generates_report(self):
        vf = _make_verification(confirmed=True)
        result = VerificationReporter.generate(vf)
        assert result.response_type == "verification_report"
        assert "Verification" in result.title


class TestResearchInsightGenerator:
    def test_generates_insight(self):
        dist = Distribution(label="Planet House", variable="x",
                            bins=("1","2","3"), counts=(10,20,30), total=60)
        meta = DatasetMetadata(sample_size=3, snapshot_count=3)
        stats = AggregateReport(title="Stats", metadata=meta, distributions=(dist,))
        result = ResearchInsightGenerator.generate(stats)
        assert result.response_type == "research_insight"
        assert "3 snapshots" in result.summary


class TestRecommendationEngine:
    def test_sade_sati_recommendation(self):
        transits = (
            TransitPlanetResult(planet="saturn", transit_rashi="capricorn", house_from_natal_moon=12,
                                ashtakavarga_bindus=2, is_sade_sati=True),
        )
        result = RecommendationEngine.generate(transits=transits)
        assert len(result.recommendations) >= 1
        assert "Sade Sati" in result.recommendations[0]

    def test_default_recommendation(self):
        result = RecommendationEngine.generate()
        assert len(result.recommendations) >= 1


class TestQAResponder:
    def test_ascendant_question(self):
        chart = _make_chart()
        result = QAResponder.generate("What is the ascendant?", chart)
        assert "aries" in result.body.lower()

    def test_sun_question(self):
        chart = _make_chart()
        result = QAResponder.generate("Where is the Sun?", chart)
        assert "sun" in result.body.lower()

    def test_moon_question(self):
        chart = _make_chart()
        result = QAResponder.generate("Tell me about the Moon", chart)
        assert "moon" in result.body.lower()

    def test_retrograde_question(self):
        chart = _make_chart()
        result = QAResponder.generate("Which planets are retrograde?", chart)
        assert "direct (forward)" in result.body or "No planets" in result.body or "Retrograde" in result.body

    def test_no_chart(self):
        result = QAResponder.generate("Where is the Sun?")
        assert "Chart data is required" in result.body

    def test_unknown_question(self):
        chart = _make_chart()
        result = QAResponder.generate("What about Pluto?", chart)
        assert "executive summary" in result.body.lower() or "astrological analysis" in result.body.lower()


class TestAIEngine:
    def test_explain_chart_summary(self):
        chart = _make_chart()
        req = ExplanationRequest(topic="chart_summary", source_data={"chart": chart})
        result = AIEngine.explain(req)
        assert result.response_type == "chart_summary"

    def test_explain_yoga(self):
        yoga = YogaResult(yoga_id="BPHS-PM-001", name="Ruchaka", category="PM",
                          source_text="BPHS", rule_version="1.0", is_present=True,
                          strength="full", involved_planets=("mars",), involved_houses=(1,))
        req = ExplanationRequest(topic="yoga_explanation", source_data={"yoga": yoga})
        result = AIEngine.explain(req)
        assert result.response_type == "yoga_explanation"

    def test_explain_dasha(self):
        period = DashaPeriod(lord="jupiter", start_date=date(2000,1,1), end_date=date(2010,1,1),
                             duration_days=3653, level=1, sub_periods=())
        req = ExplanationRequest(topic="dasha_interpretation", source_data={"period": period})
        result = AIEngine.explain(req)
        assert result.response_type == "dasha_interpretation"

    def test_explain_transit(self):
        req = ExplanationRequest(topic="transit_reading", source_data={"transits": []})
        result = AIEngine.explain(req)
        assert result.response_type == "transit_reading"

    def test_explain_verification(self):
        vf = _make_verification(confirmed=True)
        req = ExplanationRequest(topic="verification_report", source_data={"findings": vf})
        result = AIEngine.explain(req)
        assert result.response_type == "verification_report"

    def test_explain_qa(self):
        req = ExplanationRequest(topic="qa", source_data={"question": "Where is the Sun?"})
        result = AIEngine.explain(req)
        assert result.response_type == "qa_answer"

    def test_unknown_topic(self):
        req = ExplanationRequest(topic="nonexistent")
        result = AIEngine.explain(req)
        assert result.response_type == "error"

    def test_missing_data(self):
        req = ExplanationRequest(topic="chart_summary", source_data={})
        result = AIEngine.explain(req)
        assert result.response_type == "error"

    def test_convenience_methods(self):
        chart = _make_chart()
        r = AIEngine.chart_summary(chart)
        assert r.response_type == "chart_summary"

        yoga = YogaResult(yoga_id="BPHS-PM-001", name="R", category="PM",
                          source_text="", rule_version="1.0", is_present=True,
                          strength="full")
        r = AIEngine.explain_yoga(yoga)
        assert r.response_type == "yoga_explanation"

        r = AIEngine.read_transit(())
        assert r.response_type == "transit_reading"


def _make_verification(confirmed: bool = True) -> VerificationFindings:
    pair = VerificationPair(
        rule_id="R1", rule_name="R1", rule_category="g", rule_matched=True,
        event_id=uuid.uuid4(), event_date=date(2005,1,1), event_title="E",
        event_description=None, event_category="career", event_is_verified=confirmed,
        derived_facts={}, inferred_domains=("career",),
        alignment=Alignment.CONFIRMED if confirmed else Alignment.CATEGORY_MISMATCH,
        strength=VerificationStrength.HIGH if confirmed else VerificationStrength.LOW,
        explanation="",
    )
    return VerificationFindings(
        chart_id=uuid.uuid4(), period_covered=(date(2005,1,1), date(2005,1,1)),
        total_events=1, total_rules_evaluated=1, total_pairs=1,
        rule_summaries=(), verification_pairs=(pair,),
    )
