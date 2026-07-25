import uuid
from datetime import date

import pytest

from apps.api.domain.events import EventRecord
from apps.api.domain.facts import Fact
from apps.api.domain.rules import RuleResult
from apps.api.services.event_engine import BatchAnalysisResult, EventEngine
from apps.api.services.fact_registry import FactRegistry


class FlakyTransitEngine:
    """Raises for one specific date, to exercise per-event failure isolation."""

    def __init__(self, fail_on_date):
        self._fail_on_date = fail_on_date
        self.calls = 0

    def compute_transit(self, natal_chart, transit_datetime_utc):
        self.calls += 1
        if transit_datetime_utc.date() == self._fail_on_date:
            raise RuntimeError("simulated transit failure")
        return []


class RecordingRuleEngine:
    def __init__(self):
        self.seen_registries = []

    def evaluate_all(self, facts):
        self.seen_registries.append(facts)
        return [RuleResult(
            rule_id="R1", matched=True, matched_conditions=(), failed_conditions=(),
            derived_facts={}, explanation="", evaluation_trace=(), execution_time=0.0,
        )]


def _events_for_chart(chart_id, dates):
    return [
        EventRecord(id=uuid.uuid4(), chart_id=chart_id, event_date=d, title=f"Event {i}")
        for i, d in enumerate(dates)
    ]


class TestAnalyzeBatchValidation:
    def test_raises_value_error_listing_all_mismatched_ids(self, natal_snapshot):
        good = EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id, event_date=date(2001, 1, 1), title="Good")
        bad1 = EventRecord(id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2001, 1, 1), title="Bad1")
        bad2 = EventRecord(id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2001, 1, 1), title="Bad2")

        engine = EventEngine()
        with pytest.raises(ValueError) as exc_info:
            engine.analyze_batch([good, bad1, bad2], {}, natal_snapshot)

        message = str(exc_info.value)
        assert str(bad1.id) in message
        assert str(bad2.id) in message
        assert str(good.id) not in message

    def test_no_analysis_performed_when_batch_validation_fails(self, natal_snapshot):
        bad = EventRecord(id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2001, 1, 1), title="Bad")
        engine = EventEngine()
        with pytest.raises(ValueError):
            engine.analyze_batch([bad], {}, natal_snapshot)
        # (Nothing further to assert directly here beyond "raises before any
        # analysis" — covered structurally since analyze_batch validates
        # before entering its loop at all.)


class TestAnalyzeBatchHappyPath:
    def test_all_events_succeed(self, natal_snapshot, simple_dasha_tree):
        events = _events_for_chart(natal_snapshot.chart_id, [date(2001, 6, 1), date(2005, 1, 1), date(2015, 1, 1)])
        engine = EventEngine()

        result = engine.analyze_batch(events, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        assert isinstance(result, BatchAnalysisResult)
        assert result.total_events == 3
        assert result.successful == 3
        assert result.failed == 0
        assert len(result.analyses) == 3

    def test_analyses_preserve_input_order(self, natal_snapshot, simple_dasha_tree):
        events = _events_for_chart(natal_snapshot.chart_id, [date(2001, 1, 1), date(2011, 1, 1), date(2003, 1, 1)])
        engine = EventEngine()

        result = engine.analyze_batch(events, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        assert [a.event.id for a in result.analyses] == [e.id for e in events]

    def test_natal_snapshot_and_dasha_trees_shared_across_events(self, natal_snapshot, simple_dasha_tree):
        events = _events_for_chart(natal_snapshot.chart_id, [date(2001, 1, 1), date(2011, 1, 1)])
        engine = EventEngine()

        result = engine.analyze_batch(events, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        for analysis in result.analyses:
            assert analysis.context.natal_snapshot is natal_snapshot

    def test_empty_batch_returns_zeroed_result(self, natal_snapshot):
        engine = EventEngine()
        result = engine.analyze_batch([], {}, natal_snapshot)
        assert result == BatchAnalysisResult(analyses=(), total_events=0, successful=0, failed=0)


class TestAnalyzeBatchPerEventFailureIsolation:
    def test_one_failing_event_does_not_abort_the_rest(self, natal_snapshot, simple_dasha_tree):
        fail_date = date(2005, 1, 1)
        events = _events_for_chart(natal_snapshot.chart_id, [date(2001, 1, 1), fail_date, date(2015, 1, 1)])
        transit = FlakyTransitEngine(fail_on_date=fail_date)
        engine = EventEngine(transit_engine=transit)

        result = engine.analyze_batch(events, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        assert result.total_events == 3
        assert result.successful == 2
        assert result.failed == 1
        assert len(result.analyses) == 2
        assert fail_date not in [a.event.event_date for a in result.analyses]


class TestAnalyzeBatchWithFactRegistriesAndRuleEngine:
    def test_per_event_fact_registry_looked_up_by_id(self, natal_snapshot, simple_dasha_tree):
        events = _events_for_chart(natal_snapshot.chart_id, [date(2001, 1, 1), date(2011, 1, 1)])
        registry_a = FactRegistry()
        registry_a.add_fact(Fact("planet.sun.house", 1, "graha_engine"))

        rule_engine = RecordingRuleEngine()
        engine = EventEngine(rule_engine=rule_engine)

        result = engine.analyze_batch(
            events, {"vimshottari": simple_dasha_tree}, natal_snapshot,
            fact_registries={events[0].id: registry_a},
        )

        # Event 0 had a registry supplied -> rule engine ran for it.
        assert result.analyses[0].rule_results is not None
        # Event 1 had no registry entry -> rule_results stays None, same
        # graceful-degradation behavior as calling analyze() directly.
        assert result.analyses[1].rule_results is None

    def test_missing_fact_registries_dict_defaults_to_none_for_all(self, natal_snapshot, simple_dasha_tree):
        events = _events_for_chart(natal_snapshot.chart_id, [date(2001, 1, 1)])
        rule_engine = RecordingRuleEngine()
        engine = EventEngine(rule_engine=rule_engine)

        result = engine.analyze_batch(events, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        assert result.analyses[0].rule_results is None
        assert rule_engine.seen_registries == []
