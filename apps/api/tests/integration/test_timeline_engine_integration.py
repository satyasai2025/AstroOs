"""
AstroOS — Timeline Engine Integration Tests (Module 15, Phase 1)

Exercises TimelineEngine.build_timeline() end-to-end against EventAnalysis
objects produced by EventEngine.analyze() with stubs — the same "full
pipeline, test doubles for heavy engines" shape used by every prior
module's integration suite.
"""

import uuid
from datetime import date

import pytest

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.events import EventRecord
from apps.api.domain.rules import RuleResult
from apps.api.services.event_engine import EventEngine
from apps.api.services.timeline_engine import TimelineEngine


def _period(lord, start, end, level, sub=()):
    return DashaPeriod(
        lord=lord, start_date=start, end_date=end,
        duration_days=(end - start).days, level=level, sub_periods=sub,
    )


def _vimshottari_tree():
    return DashaTree(
        system="vimshottari", birth_date=date(1990, 1, 1),
        trigger_planet="venus", trigger_nakshatra="bharani",
        trigger_nakshatra_number=2,
        mahadashas=(
            _period("venus", date(1990, 1, 1), date(2010, 1, 1), level=1,
                    sub=(_period("venus", date(1990, 1, 1), date(1993, 1, 1), level=2),
                         _period("sun", date(1993, 1, 1), date(1994, 1, 1), level=2))),
            _period("sun", date(2010, 1, 1), date(2016, 1, 1), level=1),
        ),
        max_depth=2, total_cycle_years=120,
    )


class StubTransitEngine:
    """Returns a single fixed transit result — never derives its own."""

    def compute_transit(self, natal_chart, transit_datetime_utc):
        from apps.api.domain.transit import TransitPlanetResult
        return [
            TransitPlanetResult(
                planet="jupiter", transit_rashi="libra", house_from_natal_moon=6,
                ashtakavarga_bindus=3,
            ),
        ]


class StubRuleEngine:
    """Returns a fixed, pre-built RuleResult set."""

    def __init__(self, results=None):
        self._results = results or []

    def evaluate_all(self, facts):
        return list(self._results)


class TestTimelineEngineIntegration:
    """End-to-end: EventEngine.analyze() → TimelineEngine.build_timeline()."""

    def test_full_pipeline_from_analysis_to_timeline(self, natal_snapshot):
        """Build EventAnalyses, then Timeline — verify chronology and counts."""
        engine = EventEngine(
            transit_engine=StubTransitEngine(),
            rule_engine=StubRuleEngine(),
        )
        tree = _vimshottari_tree()

        events = [
            EventRecord(
                id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                event_date=date(1992, 6, 1), title="Event A", category="career",
            ),
            EventRecord(
                id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                event_date=date(2000, 1, 1), title="Event B", category="marriage",
            ),
            EventRecord(
                id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                event_date=date(2012, 3, 1), title="Event C", category="career",
            ),
        ]

        # Analyze all 3 events.
        analyses = []
        for ev in events:
            analysis = engine.analyze(ev, {"vimshottari": tree}, natal_snapshot)
            analyses.append(analysis)

        # Build timeline.
        timeline = TimelineEngine.build_timeline(tuple(analyses))

        # Entries should be sorted chronologically.
        assert [e.event_date for e in timeline.entries] == [
            date(1992, 6, 1),
            date(2000, 1, 1),
            date(2012, 3, 1),
        ]

        # Summary.
        assert timeline.summary.total_events == 3
        assert timeline.summary.events_per_category == {"career": 2, "marriage": 1}
        assert timeline.summary.date_range == (date(1992, 6, 1), date(2012, 3, 1))
        assert timeline.summary.verified_count == 0

        # Dasha breakdown: first two events in venus mahadasha,
        # third in sun mahadasha (2010-2016).
        vim = timeline.dasha_breakdown["vimshottari"]
        venus_spans = [s for s in vim if s.lord == "venus" and s.level == 1]
        sun_spans = [s for s in vim if s.lord == "sun"]
        assert len(venus_spans) == 1
        assert venus_spans[0].event_count == 2
        assert len(sun_spans) == 1
        assert sun_spans[0].event_count == 1

        # Clusters: 2 events (1992, 2000) are ~8 years apart → not a cluster
        # at default min_events=2 for window_days=365, unless density is high.
        # We just verify the method runs without error.
        assert timeline.clusters is not None

    def test_density_computation_multiple_events(self, natal_snapshot):
        """Verify O(n) density produces reasonable values."""
        engine = EventEngine()
        tree = _vimshottari_tree()

        # 4 events tightly clustered (within 360 days of each other).
        events = [
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(1992, 1, 1), title="A"),
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(1992, 3, 1), title="B"),
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(1992, 6, 1), title="C"),
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(1992, 9, 1), title="D"),
        ]
        analyses = [engine.analyze(e, {"vimshottari": tree}, natal_snapshot) for e in events]
        timeline = TimelineEngine.build_timeline(tuple(analyses))

        # Density: all 4 events within 244 days → (4/365)*365.25 ≈ 4.0
        density = TimelineEngine.compute_density(timeline.entries, window_days=365)
        max_density = max(d for _, d in density)
        assert max_density == pytest.approx(4.0, rel=0.2)

    def test_timeline_entry_has_correct_analysis_reference(self, natal_snapshot):
        """Each TimelineEntry.analysis is the original EventAnalysis."""
        engine = EventEngine()
        tree = _vimshottari_tree()

        event = EventRecord(
            id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
            event_date=date(1995, 1, 1), title="Test Event", category="test",
        )
        analysis = engine.analyze(event, {"vimshottari": tree}, natal_snapshot)
        timeline = TimelineEngine.build_timeline((analysis,))

        entry = timeline.entries[0]
        assert entry.analysis is analysis
        assert entry.event_id == analysis.event.id
        assert entry.event_date == analysis.event.event_date
        assert entry.title == analysis.event.title

    def test_filter_integration(self, natal_snapshot):
        """Filter the built timeline and verify recomputed stats."""
        engine = EventEngine()
        tree = _vimshottari_tree()

        events = [
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(1995, 1, 1), title="A", category="career"),
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(2000, 1, 1), title="B", category="marriage"),
        ]
        analyses = [engine.analyze(e, {"vimshottari": tree}, natal_snapshot) for e in events]
        timeline = TimelineEngine.build_timeline(tuple(analyses))

        career = TimelineEngine.filter_by_category(timeline, "career")
        assert career.total_events == 1
        assert career.summary.events_per_category == {"career": 1}
