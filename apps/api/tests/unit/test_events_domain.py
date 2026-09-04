import dataclasses
import uuid
from datetime import date

import pytest

from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord, NatalSnapshot


class TestEventRecord:
    def test_mirrors_events_table_columns(self):
        record = EventRecord(
            id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2010, 5, 1),
            title="Career change", description="Started new role", category="career",
            is_verified=True,
        )
        assert record.title == "Career Change"
        assert record.category == "career"
        assert record.is_verified is True

    def test_optional_fields_default_sensibly(self):
        record = EventRecord(id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2010, 5, 1), title="X")
        assert record.user_id is None
        assert record.description is None
        assert record.category is None
        assert record.is_verified is False

    def test_is_frozen(self):
        record = EventRecord(id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2010, 5, 1), title="X")
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.title = "Y"


class TestNatalSnapshot:
    def test_is_frozen(self, natal_snapshot):
        with pytest.raises(dataclasses.FrozenInstanceError):
            natal_snapshot.chart_id = uuid.uuid4()

    def test_holds_chart_and_natal_results_together(self, natal_snapshot, minimal_chart):
        assert natal_snapshot.chart is minimal_chart
        assert len(natal_snapshot.yogas) == 1
        assert "naisargika_bala" in natal_snapshot.shadbala_components
        assert natal_snapshot.sarvashtakavarga.total_bindus == 337


class TestEventAstrologicalContext:
    def test_default_context_version(self, event_record, natal_snapshot):
        context = EventAstrologicalContext(
            event_id=event_record.id, chart_id=event_record.chart_id,
            active_dashas={}, transits=(), natal_snapshot=natal_snapshot,
        )
        assert context.context_version == "1.0"


class TestEventAnalysis:
    def test_rule_results_defaults_to_none(self, event_record, natal_snapshot):
        context = EventAstrologicalContext(
            event_id=event_record.id, chart_id=event_record.chart_id,
            active_dashas={}, transits=(), natal_snapshot=natal_snapshot,
        )
        analysis = EventAnalysis(event=event_record, context=context)
        assert analysis.rule_results is None
        assert analysis.event_facts == ()

    def test_analysis_version_field_present_and_defaulted(self, event_record, natal_snapshot):
        context = EventAstrologicalContext(
            event_id=event_record.id, chart_id=event_record.chart_id,
            active_dashas={}, transits=(), natal_snapshot=natal_snapshot,
        )
        analysis = EventAnalysis(event=event_record, context=context)
        assert analysis.analysis_version == "1.0"

    def test_analysis_version_independent_of_context_version(self, event_record, natal_snapshot):
        context = EventAstrologicalContext(
            event_id=event_record.id, chart_id=event_record.chart_id,
            active_dashas={}, transits=(), natal_snapshot=natal_snapshot,
            context_version="1.1",
        )
        analysis = EventAnalysis(event=event_record, context=context, analysis_version="2.0")
        assert analysis.context.context_version == "1.1"
        assert analysis.analysis_version == "2.0"
