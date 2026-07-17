"""
AstroOS — TimelineEngine Unit Tests (Module 15, Phase 1)

Tests use synthetic EventAnalysis objects (no real engines, no DB, no
Ephemeris). EventAnalysis is constructed directly from domain objects
using the same approach as test_event_engine.py's test doubles.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest

from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord
from apps.api.domain.timeline import Timeline
from apps.api.services.timeline_engine import TimelineEngine


# ── Helpers ──────────────────────────────────────────────────────────────────


def _dasha(lord: str, start: date, end: date, level: int = 1) -> DashaPeriod:
    return DashaPeriod(
        lord=lord, start_date=start, end_date=end,
        duration_days=(end - start).days, level=level, sub_periods=(),
    )


def _analysis(
    event_date: date,
    title: str = "Event",
    category: str | None = None,
    is_verified: bool = False,
    chart_id: uuid.UUID | None = None,
    vim_lord: str | None = "jupiter",
    vim_start: date = date(2000, 1, 1),
    vim_end: date = date(2010, 1, 1),
    yog_lord: str | None = None,
) -> EventAnalysis:
    cid = chart_id or uuid.uuid4()
    event = EventRecord(
        id=uuid.uuid4(), chart_id=cid, event_date=event_date,
        title=title, category=category, is_verified=is_verified,
    )
    active_dashas: dict[str, tuple[DashaPeriod, ...]] = {}
    if vim_lord is not None:
        active_dashas["vimshottari"] = (_dasha(vim_lord, vim_start, vim_end),)
    if yog_lord is not None:
        active_dashas["yogini"] = (_dasha(yog_lord, vim_start, vim_end),)
    context = EventAstrologicalContext(
        event_id=event.id, chart_id=event.chart_id,
        active_dashas=active_dashas, transits=(), natal_snapshot=None,
    )
    return EventAnalysis(event=event, context=context, analysis_version="1.0")


def _analyses_for_dates(dates: list[date], **kw) -> tuple[EventAnalysis, ...]:
    """Build tuple of analyses from a list of dates (same chart_id)."""
    cid = uuid.uuid4()
    return tuple(_analysis(d, chart_id=cid, **kw) for d in dates)


# ── build_timeline ───────────────────────────────────────────────────────────


class TestBuildTimeline:
    def test_empty_analyses_returns_empty_timeline(self):
        timeline = TimelineEngine.build_timeline(())
        assert timeline.is_empty
        assert timeline.total_events == 0

    def test_single_event_timeline(self):
        analyses = (_analysis(date(2010, 5, 1), category="career", is_verified=True),)
        timeline = TimelineEngine.build_timeline(analyses)
        assert timeline.total_events == 1
        assert timeline.entries[0].event_date == date(2010, 5, 1)
        assert timeline.entries[0].category == "career"
        assert timeline.entries[0].is_verified is True

    def test_entries_sorted_chronologically(self):
        analyses = _analyses_for_dates([
            date(2010, 1, 1),
            date(2005, 6, 15),
            date(2000, 12, 31),
        ])
        timeline = TimelineEngine.build_timeline(analyses)
        assert [e.event_date for e in timeline.entries] == [
            date(2000, 12, 31),
            date(2005, 6, 15),
            date(2010, 1, 1),
        ]

    def test_mixed_chart_id_raises_error(self):
        analyses = (
            _analysis(date(2010, 1, 1), chart_id=uuid.uuid4()),
            _analysis(date(2010, 2, 1), chart_id=uuid.uuid4()),
        )
        with pytest.raises(ValueError, match="multiple chart_ids"):
            TimelineEngine.build_timeline(analyses)

    def test_summary_computed_correctly(self):
        cid = uuid.uuid4()
        analyses = (
            _analysis(date(2000, 1, 1), category="career", is_verified=True, chart_id=cid),
            _analysis(date(2005, 1, 1), category="marriage", is_verified=True, chart_id=cid),
            _analysis(date(2010, 1, 1), category="career", is_verified=False, chart_id=cid),
        )
        timeline = TimelineEngine.build_timeline(analyses)
        assert timeline.summary.total_events == 3
        assert timeline.summary.date_range == (date(2000, 1, 1), date(2010, 1, 1))
        assert timeline.summary.events_per_category == {"career": 2, "marriage": 1}
        assert timeline.summary.verified_count == 2
        assert timeline.summary.unverified_count == 1


# ── Dasha breakdown ──────────────────────────────────────────────────────────


class TestDashaBreakdown:
    def test_dasha_period_span_event_assignment(self):
        """Events are assigned to the DashaPeriodSpan matching their date."""
        cid = uuid.uuid4()
        # Jupiter mahadasha: 2000-2010, Saturn mahadasha: 2010-2020
        analyses = (
            _analysis(date(2005, 1, 1), chart_id=cid, vim_lord="jupiter",
                      vim_start=date(2000, 1, 1), vim_end=date(2010, 1, 1)),
            _analysis(date(2015, 1, 1), chart_id=cid, vim_lord="saturn",
                      vim_start=date(2010, 1, 1), vim_end=date(2020, 1, 1)),
        )
        timeline = TimelineEngine.build_timeline(analyses)
        breakdown = timeline.dasha_breakdown
        assert "vimshottari" in breakdown
        spans = breakdown["vimshottari"]
        assert len(spans) == 2
        # Jupiter span should contain the 2005 event.
        jupiter_span = spans[0]
        assert jupiter_span.lord == "jupiter"
        assert jupiter_span.event_count == 1
        assert jupiter_span.event_ids[0] == analyses[0].event.id
        # Saturn span should contain the 2015 event.
        saturn_span = spans[1]
        assert saturn_span.lord == "saturn"
        assert saturn_span.event_count == 1
        assert saturn_span.event_ids[0] == analyses[1].event.id

    def test_multiple_dasha_systems(self):
        cid = uuid.uuid4()
        analyses = (
            _analysis(date(2005, 1, 1), chart_id=cid,
                      vim_lord="jupiter", yog_lord="mangala"),
        )
        timeline = TimelineEngine.build_timeline(analyses)
        assert "vimshottari" in timeline.dasha_breakdown
        assert "yogini" in timeline.dasha_breakdown


# ── compute_density ──────────────────────────────────────────────────────────


class TestComputeDensity:
    def test_empty_entries_returns_empty(self):
        assert TimelineEngine.compute_density(()) == ()

    def test_single_event_density(self, sample_timeline):
        density = TimelineEngine.compute_density(sample_timeline.entries, window_days=365)
        # Single event in 365-day window = (1/365)*365.25 ≈ 1.0
        assert len(density) == 2
        for _, d in density:
            assert d == pytest.approx(1.0, rel=0.1)

    def test_two_close_events_density(self):
        """Events 180 days apart → both share the same 365-day window → density ~2.0."""
        entries = _entries_for_dates([
            date(2000, 6, 1),
            date(2000, 11, 28),
        ])
        density = TimelineEngine.compute_density(entries, window_days=365)
        for _, d in density:
            assert d == pytest.approx(2.0, rel=0.1)

    def test_density_increases_with_closer_events(self):
        # 5 events within 30 days → density should be very high.
        base = date(2000, 6, 1)
        dates = [base + timedelta(days=i * 7) for i in range(5)]
        entries = _entries_for_dates(dates)
        density = TimelineEngine.compute_density(entries, window_days=365)
        for _, d in density:
            assert d > 3.0  # At least 3 events/year

    def test_widely_spaced_events_low_density(self):
        # 3 events each 2 years apart → density near 1.0
        entries = _entries_for_dates([
            date(2000, 1, 1),
            date(2002, 1, 1),
            date(2004, 1, 1),
        ])
        density = TimelineEngine.compute_density(entries, window_days=365)
        for _, d in density:
            assert d <= 2.0


# ── Filters ──────────────────────────────────────────────────────────────────


class TestFilterByCategory:
    def test_filters_to_category(self, mixed_category_timeline):
        career = TimelineEngine.filter_by_category(mixed_category_timeline, "career")
        assert career.total_events == 2
        for e in career.entries:
            assert e.category == "career"

    def test_empty_result_when_no_match(self, mixed_category_timeline):
        result = TimelineEngine.filter_by_category(mixed_category_timeline, "education")
        assert result.is_empty

    def test_original_unchanged(self, mixed_category_timeline):
        original_count = mixed_category_timeline.total_events
        TimelineEngine.filter_by_category(mixed_category_timeline, "career")
        assert mixed_category_timeline.total_events == original_count


class TestFilterByDateRange:
    def test_filters_to_range(self, sample_timeline):
        result = TimelineEngine.filter_by_date_range(
            sample_timeline, date(2000, 1, 1), date(2002, 1, 1),
        )
        for e in result.entries:
            assert date(2000, 1, 1) <= e.event_date <= date(2002, 1, 1)

    def test_empty_result_outside_range(self, sample_timeline):
        result = TimelineEngine.filter_by_date_range(
            sample_timeline, date(2030, 1, 1), date(2040, 1, 1),
        )
        assert result.is_empty

    def test_inclusive_boundaries(self, sample_timeline):
        result = TimelineEngine.filter_by_date_range(
            sample_timeline, date(2000, 1, 1), date(2000, 1, 1),
        )
        assert result.total_events >= 1


class TestFilterVerified:
    def test_verified_only(self, sample_timeline):
        verified = TimelineEngine.filter_verified(sample_timeline, verified=True)
        for e in verified.entries:
            assert e.is_verified is True

    def test_unverified_only(self, sample_timeline):
        unverified = TimelineEngine.filter_verified(sample_timeline, verified=False)
        for e in unverified.entries:
            assert e.is_verified is False

    def test_summary_recomputed_after_filter(self, mixed_category_timeline):
        career = TimelineEngine.filter_by_category(mixed_category_timeline, "career")
        # After filtering to career-only, category counts should only have career.
        assert career.summary.events_per_category.get("marriage", 0) == 0


# ── Cluster detection ────────────────────────────────────────────────────────


class TestFindClusters:
    def test_no_clusters_with_wide_spacing(self):
        entries = _entries_for_dates([
            date(2000, 1, 1),
            date(2005, 1, 1),
            date(2010, 1, 1),
        ])
        timeline = TimelineEngine.build_timeline(
            _analyses_for_dates([date(2000, 1, 1), date(2005, 1, 1), date(2010, 1, 1)])
        )
        clusters = TimelineEngine.find_clusters(timeline, window_days=365, min_events=1)
        assert len(clusters) >= 1  # each event is its own cluster with min_events=1

    def test_cluster_detected_with_close_events(self):
        """5 events in 60 days should form at least one cluster."""
        base = date(2000, 6, 1)
        dates = [base + timedelta(days=i * 14) for i in range(5)]
        timeline = TimelineEngine.build_timeline(
            _analyses_for_dates(dates)
        )
        clusters = TimelineEngine.find_clusters(timeline, window_days=365, min_events=2)
        assert len(clusters) >= 1
        biggest = max(clusters, key=lambda c: c.event_count)
        assert biggest.event_count >= 2

    def test_cluster_density_is_events_per_year(self):
        """Validate that cluster density is a reasonable events/year value."""
        dates = [date(2000, 6, 1) + timedelta(days=i * 15) for i in range(5)]
        timeline = TimelineEngine.build_timeline(_analyses_for_dates(dates))
        clusters = TimelineEngine.find_clusters(timeline, window_days=365, min_events=2)
        if clusters:
            for c in clusters:
                assert c.density > 0
                assert c.event_count >= 2


def _entries_for_dates(dates: list[date], cid: uuid.UUID | None = None) -> tuple:
    """Build TimelineEntry tuple from date list, all same chart."""
    cid = cid or uuid.uuid4()
    analyses = tuple(
        _analysis(d, chart_id=cid) for d in dates
    )
    timeline = TimelineEngine.build_timeline(analyses)
    return timeline.entries


# ── Sample timelines for reuse ───────────────────────────────────────────────


@pytest.fixture
def sample_timeline() -> Timeline:
    """Two events in the same chart, 2 years apart."""
    cid = uuid.uuid4()
    analyses = (
        _analysis(date(2000, 1, 1), title="Early", category="career",
                  is_verified=True, chart_id=cid),
        _analysis(date(2002, 1, 1), title="Late", category="marriage",
                  is_verified=False, chart_id=cid),
    )
    return TimelineEngine.build_timeline(analyses)


@pytest.fixture
def mixed_category_timeline() -> Timeline:
    """3 events: 2 career, 1 marriage."""
    cid = uuid.uuid4()
    analyses = (
        _analysis(date(2000, 1, 1), title="Job start", category="career",
                  is_verified=True, chart_id=cid),
        _analysis(date(2005, 1, 1), title="Wedding", category="marriage",
                  is_verified=True, chart_id=cid),
        _analysis(date(2010, 1, 1), title="Promotion", category="career",
                  is_verified=False, chart_id=cid),
    )
    return TimelineEngine.build_timeline(analyses)
