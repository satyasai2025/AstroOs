"""
AstroOS — ReportEngine Unit Tests (Module 20, Phase 1)
"""

import uuid
from datetime import date

import pytest

from apps.api.domain.ephemeris import DignityType, SiderealPosition
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.statistics import AggregateReport, DatasetMetadata, Distribution
from apps.api.domain.timeline import Timeline, TimelineEntry, TimelineSummary
from apps.api.domain.report import ReportContent
from apps.api.services.report_engine import ReportEngine
from apps.api.domain.research import AstrologicalSnapshot
from apps.api.domain.verification import (
    Alignment,
    VerificationFindings,
    VerificationPair,
    VerificationStrength,
)
from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord


def _make_planet(planet: str, house: int, rashi: str = "aries") -> SiderealPosition:
    return SiderealPosition(
        planet=planet, sidereal_longitude=float(house * 30), rashi=rashi,
        rashi_degree=10.0, house_number=house, nakshatra="pushya", pada=2,
        is_retrograde=False, is_combust=False, combustion_orb=None,
        dignity=DignityType.FRIENDLY,
    )


def _make_chart(planets: list | None = None) -> D1Chart:
    planets = planets or [
        _make_planet("sun", 1, "aries"),
        _make_planet("moon", 2, "taurus"),
        _make_planet("jupiter", 5, "cancer"),
    ]
    from apps.api.domain.ephemeris import Ascendant, HouseCusp
    asc = Ascendant(
        longitude=10.0, sidereal_longitude=10.0, rashi="aries",
        rashi_degree=10.0, nakshatra="ashwini", pada=1,
    )
    houses = [
        HouseCusp(house_number=n, longitude=float(n * 30), sidereal_longitude=float(n * 30), rashi="")
        for n in range(1, 13)
    ]
    return D1Chart(
        ephemeris=None, ascendant=asc, houses=houses, planets=planets,
        aspects=[], planet_strengths=[], panchanga=None,
        ayanamsa_system="lahiri", house_system="W",
    )


def _make_timeline() -> Timeline:
    cid = uuid.uuid4()
    event = EventRecord(id=uuid.uuid4(), chart_id=cid, event_date=date(2005, 1, 1), title="E", category="career")
    context = EventAstrologicalContext(event_id=event.id, chart_id=cid, active_dashas={}, transits=(), natal_snapshot=None)
    analysis = EventAnalysis(event=event, context=context)
    entry = TimelineEntry(event_id=event.id, event_date=date(2005, 1, 1), title="E", category="career",
                          is_verified=True, sort_key="2005-01-01", analysis=analysis)
    return Timeline(
        chart_id=cid, entries=(entry,),
        summary=TimelineSummary(total_events=1, date_range=(date(2005,1,1), date(2005,1,1)),
                               events_per_category={"career": 1}, events_per_dasha_system={},
                               verified_count=1, unverified_count=0),
        dasha_breakdown={}, clusters=(),
    )


def _make_verification() -> VerificationFindings:
    pair = VerificationPair(
        rule_id="R1", rule_name="R1", rule_category="g", rule_matched=True,
        event_id=uuid.uuid4(), event_date=date(2005,1,1), event_title="E",
        event_description=None, event_category="career", event_is_verified=True,
        derived_facts={}, inferred_domains=("career",),
        alignment=Alignment.CONFIRMED, strength=VerificationStrength.HIGH,
        explanation="",
    )
    return VerificationFindings(
        chart_id=uuid.uuid4(), period_covered=(date(2005,1,1), date(2005,1,1)),
        total_events=1, total_rules_evaluated=1, total_pairs=1,
        rule_summaries=(), verification_pairs=(pair,),
    )


class TestBuildChartReport:
    def test_minimal_report(self):
        chart = _make_chart()
        report = ReportEngine.build_chart_report(chart, title="Test")
        assert report.title == "Test"
        assert report.metadata.report_type == "chart"
        assert len(report.sections) >= 1

    def test_sections_include_chart_summary(self):
        chart = _make_chart()
        report = ReportEngine.build_chart_report(chart)
        types = [s.section_type for s in report.sections]
        assert "chart_summary" in types
        assert "planets" in types

    def test_timeline_section_included_when_provided(self):
        chart = _make_chart()
        tl = _make_timeline()
        report = ReportEngine.build_chart_report(chart, timeline=tl)
        types = [s.section_type for s in report.sections]
        assert "timeline_summary" in types

    def test_verification_section_included_when_provided(self):
        chart = _make_chart()
        vf = _make_verification()
        report = ReportEngine.build_chart_report(chart, verification=vf)
        types = [s.section_type for s in report.sections]
        assert "verification_summary" in types

    def test_generated_by_in_metadata(self):
        chart = _make_chart()
        report = ReportEngine.build_chart_report(chart, generated_by="test-user")
        assert report.metadata.generated_by == "test-user"

    def report_content_is_not_raw_dict(self):
        chart = _make_chart()
        report = ReportEngine.build_chart_report(chart)
        for s in report.sections:
            assert isinstance(s.content, ReportContent)


class TestBuildResearchReport:
    def test_minimal_report(self):
        pid = uuid.uuid4()
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=pid, chart_id=uuid.uuid4(),
            label="test", captured_at=None, chart_ref=_make_chart(),
        )
        report = ReportEngine.build_research_report(pid, (snap,), title="Research")
        assert report.title == "Research"
        assert report.metadata.report_type == "research"
        assert report.snapshot_count == 1

    def test_snapshot_overview_section(self):
        pid = uuid.uuid4()
        snap = AstrologicalSnapshot(
            id=uuid.uuid4(), project_id=pid, chart_id=uuid.uuid4(),
            label="S1", captured_at=None, chart_ref=_make_chart(),
        )
        report = ReportEngine.build_research_report(pid, (snap,))
        types = [s.section_type for s in report.sections]
        assert "snapshot_overview" in types


class TestBuildComparisonReport:
    def test_raises_on_single_chart(self):
        chart = _make_chart()
        with pytest.raises(ValueError, match="At least 2 charts"):
            ReportEngine.build_comparison_report((chart,), ("Only",))

    def test_raises_on_label_mismatch(self):
        chart = _make_chart()
        with pytest.raises(ValueError, match="must match labels"):
            ReportEngine.build_comparison_report((chart,), ("A", "B"))

    def test_planet_sections_present(self):
        c1 = _make_chart()
        c2 = _make_chart(planets=[
            _make_planet("sun", 7, "libra"),
            _make_planet("moon", 1, "aries"),
        ])
        report = ReportEngine.build_comparison_report((c1, c2), ("Chart A", "Chart B"))
        types = [s.section_type for s in report.sections]
        assert "planet_comparison" in types
        assert report.chart_labels == ("Chart A", "Chart B")
