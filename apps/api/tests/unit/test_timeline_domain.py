"""
AstroOS — Timeline Domain Model Unit Tests (Module 15, Phase 1)
"""

import dataclasses
import uuid
from datetime import date

import pytest

from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord
from apps.api.domain.timeline import (
    TemporalCluster,
    Timeline,
    TimelineDashaPeriodSpan,
    TimelineEntry,
    TimelineSummary,
)


def _minimal_analysis(event_date=date(2010, 5, 1), title="X", category="career",
                       is_verified=False) -> EventAnalysis:
    event = EventRecord(
        id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=event_date,
        title=title, category=category, is_verified=is_verified,
    )
    context = EventAstrologicalContext(
        event_id=event.id, chart_id=event.chart_id,
        active_dashas={}, transits=(), natal_snapshot=None,
    )
    return EventAnalysis(event=event, context=context)


class TestTimelineEntry:
    def test_is_frozen(self):
        entry = TimelineEntry(
            event_id=uuid.uuid4(), event_date=date(2010, 1, 1), title="A",
            category="career", is_verified=True, sort_key="2010-01-01",
            analysis=_minimal_analysis(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            entry.title = "Changed"

    def test_lt_compares_by_date_then_title(self):
        early = TimelineEntry(
            event_id=uuid.uuid4(), event_date=date(2000, 1, 1), title="A",
            category=None, is_verified=False, sort_key="2000-01-01",
            analysis=_minimal_analysis(),
        )
        late = TimelineEntry(
            event_id=uuid.uuid4(), event_date=date(2010, 1, 1), title="A",
            category=None, is_verified=False, sort_key="2010-01-01",
            analysis=_minimal_analysis(),
        )
        same_date_a = TimelineEntry(
            event_id=uuid.uuid4(), event_date=date(2005, 1, 1), title="A",
            category=None, is_verified=False, sort_key="2005-01-01",
            analysis=_minimal_analysis(),
        )
        same_date_b = TimelineEntry(
            event_id=uuid.uuid4(), event_date=date(2005, 1, 1), title="B",
            category=None, is_verified=False, sort_key="2005-01-01",
            analysis=_minimal_analysis(),
        )
        assert early < late
        assert not (late < early)
        assert same_date_a < same_date_b


class TestTimelineDashaPeriodSpan:
    def test_is_frozen(self):
        span = TimelineDashaPeriodSpan(
            system="vimshottari", lord="jupiter", level=1,
            start_date=date(2000, 1, 1), end_date=date(2010, 1, 1),
            event_ids=(), event_count=0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            span.event_count = 5

    def test_stores_event_ids_and_count(self):
        eid = uuid.uuid4()
        span = TimelineDashaPeriodSpan(
            system="vimshottari", lord="venus", level=2,
            start_date=date(2003, 1, 1), end_date=date(2006, 1, 1),
            event_ids=(eid,), event_count=1,
        )
        assert span.event_ids == (eid,)
        assert span.event_count == 1


class TestTemporalCluster:
    def test_is_frozen(self):
        cluster = TemporalCluster(
            start_date=date(2005, 1, 1), end_date=date(2006, 1, 1),
            center_date=date(2005, 6, 1),
            events=(), event_count=0, density=2.5,
            active_dashas={},
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            cluster.density = 3.0

    def test_density_field(self):
        cluster = TemporalCluster(
            start_date=date(2005, 1, 1), end_date=date(2006, 1, 1),
            center_date=date(2005, 6, 1), events=(), event_count=3,
            density=3.0, active_dashas={},
        )
        assert cluster.density == 3.0
        assert cluster.event_count == 3

    def test_empty_events_allowed(self):
        cluster = TemporalCluster(
            start_date=date(2005, 1, 1), end_date=date(2005, 6, 1),
            center_date=date(2005, 3, 1), events=(), event_count=0,
            density=0.0, active_dashas={},
        )
        assert cluster.event_count == 0


class TestTimelineSummary:
    def test_single_event_summary(self):
        summary = TimelineSummary(
            total_events=1,
            date_range=(date(2010, 5, 1), date(2010, 5, 1)),
            events_per_category={"career": 1},
            events_per_dasha_system={"vimshottari": 1},
            verified_count=1,
            unverified_count=0,
        )
        assert summary.total_events == 1
        assert summary.date_range == (date(2010, 5, 1), date(2010, 5, 1))
        assert summary.verified_count == 1
        assert summary.unverified_count == 0

    def test_multiple_categories_summary(self):
        summary = TimelineSummary(
            total_events=3,
            date_range=(date(2000, 1, 1), date(2010, 1, 1)),
            events_per_category={"career": 2, "marriage": 1},
            events_per_dasha_system={"vimshottari": 3, "yogini": 1},
            verified_count=1,
            unverified_count=2,
        )
        assert summary.events_per_category["career"] == 2
        assert summary.events_per_category["marriage"] == 1
        assert summary.verified_count == 1
        assert summary.unverified_count == 2

    def test_is_frozen(self):
        summary = TimelineSummary(
            total_events=0,
            date_range=(date(1, 1, 1), date(1, 1, 1)),
            events_per_category={}, events_per_dasha_system={},
            verified_count=0, unverified_count=0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            summary.total_events = 5


class TestTimeline:
    def test_is_frozen(self):
        empty = uuid.UUID(int=0)
        timeline = Timeline(
            chart_id=empty, entries=(),
            summary=TimelineSummary(
                total_events=0, date_range=(date(1, 1, 1), date(1, 1, 1)),
                events_per_category={}, events_per_dasha_system={},
                verified_count=0, unverified_count=0,
            ),
            dasha_breakdown={}, clusters=(),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            timeline.entries = ("x",)  # type: ignore

    def test_total_events_property(self):
        timeline = Timeline(
            chart_id=uuid.uuid4(), entries=(),
            summary=TimelineSummary(
                total_events=3, date_range=(date(2000, 1, 1), date(2010, 1, 1)),
                events_per_category={"a": 3}, events_per_dasha_system={"v": 3},
                verified_count=1, unverified_count=2,
            ),
            dasha_breakdown={}, clusters=(),
        )
        assert timeline.total_events == 3

    def test_date_range_property(self):
        dr = (date(2000, 1, 1), date(2010, 1, 1))
        timeline = Timeline(
            chart_id=uuid.uuid4(), entries=(),
            summary=TimelineSummary(
                total_events=2, date_range=dr,
                events_per_category={"a": 2}, events_per_dasha_system={"v": 2},
                verified_count=0, unverified_count=2,
            ),
            dasha_breakdown={}, clusters=(),
        )
        assert timeline.date_range == dr

    def test_is_empty_true_when_no_entries(self):
        empty = uuid.UUID(int=0)
        timeline = Timeline(
            chart_id=empty, entries=(),
            summary=TimelineSummary(
                total_events=0, date_range=(date(1, 1, 1), date(1, 1, 1)),
                events_per_category={}, events_per_dasha_system={},
                verified_count=0, unverified_count=0,
            ),
            dasha_breakdown={}, clusters=(),
        )
        assert timeline.is_empty is True

    def test_is_empty_false_when_entries_present(self):
        timeline = Timeline(
            chart_id=uuid.uuid4(), entries=(_minimal_entry(),),
            summary=TimelineSummary(
                total_events=1, date_range=(date(2010, 1, 1), date(2010, 1, 1)),
                events_per_category={"x": 1}, events_per_dasha_system={},
                verified_count=0, unverified_count=1,
            ),
            dasha_breakdown={}, clusters=(),
        )
        assert timeline.is_empty is False

    def test_timeline_version_default(self):
        timeline = Timeline(
            chart_id=uuid.uuid4(), entries=(),
            summary=TimelineSummary(
                total_events=0, date_range=(date(1, 1, 1), date(1, 1, 1)),
                events_per_category={}, events_per_dasha_system={},
                verified_count=0, unverified_count=0,
            ),
            dasha_breakdown={}, clusters=(),
        )
        assert timeline.timeline_version == "1.0"


def _minimal_entry(event_date=date(2010, 1, 1)) -> TimelineEntry:
    return TimelineEntry(
        event_id=uuid.uuid4(), event_date=event_date, title="Test",
        category=None, is_verified=False, sort_key=event_date.isoformat(),
        analysis=_minimal_analysis(event_date),
    )
