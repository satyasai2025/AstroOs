import uuid
from datetime import date, datetime

import pytest

from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord
from apps.api.domain.facts import Fact
from apps.api.domain.rules import Condition, Conclusion, RuleDefinition, RuleResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.event_engine import EventEngine
from apps.api.services.fact_registry import FactRegistry


class StubTransitEngine:
    """Test double matching TransitEngine's public compute_transit() shape."""

    def __init__(self):
        self.calls: list[tuple] = []

    def compute_transit(self, natal_chart, transit_datetime_utc):
        self.calls.append((natal_chart, transit_datetime_utc))
        return [
            TransitPlanetResult(
                planet="jupiter", transit_rashi="cancer", house_from_natal_moon=3,
                ashtakavarga_bindus=4,
            ),
        ]


class StubRuleEngine:
    """Test double matching RuleEngine's public evaluate_all() shape."""

    def __init__(self, results=None):
        self._results = results or []
        self.received_registry: FactRegistry | None = None

    def evaluate_all(self, facts):
        self.received_registry = facts
        return self._results


def _make_rule_result(rule_id="RULE-1", matched=True):
    return RuleResult(
        rule_id=rule_id, matched=matched, matched_conditions=(), failed_conditions=(),
        derived_facts={}, explanation="", evaluation_trace=(), execution_time=0.0,
    )


class TestBuildContext:
    def test_chart_id_mismatch_raises(self, event_record, natal_snapshot, simple_dasha_tree):
        mismatched_event = EventRecord(
            id=uuid.uuid4(), chart_id=uuid.uuid4(), event_date=date(2005, 6, 15), title="X",
        )
        engine = EventEngine()
        with pytest.raises(ValueError):
            engine.build_context(mismatched_event, {"vimshottari": simple_dasha_tree}, natal_snapshot)

    def test_active_dashas_looked_up_per_system(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        assert [p.lord for p in context.active_dashas["vimshottari"]] == ["jupiter", "venus"]

    def test_no_transit_engine_gives_empty_transits(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine(transit_engine=None)
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        assert context.transits == ()

    def test_transit_engine_called_with_midnight_utc_on_event_date(
        self, event_record, natal_snapshot, simple_dasha_tree
    ):
        stub = StubTransitEngine()
        engine = EventEngine(transit_engine=stub)
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        assert len(stub.calls) == 1
        called_chart, called_datetime = stub.calls[0]
        assert called_chart is natal_snapshot.chart
        assert called_datetime == datetime(2005, 6, 15, 0, 0, tzinfo=called_datetime.tzinfo)
        assert context.transits[0].planet == "jupiter"

    def test_natal_snapshot_is_referenced_not_copied(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        assert context.natal_snapshot is natal_snapshot

    def test_context_version_stamped(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        assert context.context_version == "1.0"

    def test_multiple_dasha_systems_all_looked_up(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        trees = {"vimshottari": simple_dasha_tree, "yogini": simple_dasha_tree}
        context = engine.build_context(event_record, trees, natal_snapshot)
        assert set(context.active_dashas.keys()) == {"vimshottari", "yogini"}


class TestBuildEventFacts:
    def test_category_and_verified_facts_present(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        facts = engine.build_event_facts(event_record, context)

        keys = {f.key: f.value for f in facts}
        assert keys[f"event.{event_record.id}.category"] == "marriage"
        assert keys[f"event.{event_record.id}.is_verified"] is True

    def test_dasha_facts_generated_per_active_period(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        facts = engine.build_event_facts(event_record, context)

        keys = {f.key: f.value for f in facts}
        assert keys[f"event.{event_record.id}.dasha.vimshottari.level1.lord"] == "jupiter"
        assert keys[f"event.{event_record.id}.dasha.vimshottari.level2.lord"] == "venus"

    def test_no_rule_facts_when_rule_results_absent(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        facts = engine.build_event_facts(event_record, context, rule_results=None)
        assert not any(".rule." in f.key for f in facts)

    def test_rule_facts_generated_when_rule_results_present(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        rule_results = (_make_rule_result("RULE-1", matched=True),)
        facts = engine.build_event_facts(event_record, context, rule_results=rule_results)

        keys = {f.key: f.value for f in facts}
        assert keys[f"event.{event_record.id}.rule.RULE-1.matched"] is True

    def test_all_facts_use_existing_fact_dataclass(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        context = engine.build_context(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        facts = engine.build_event_facts(event_record, context)
        assert all(isinstance(f, Fact) for f in facts)
        assert all(f.source == "event_engine" for f in facts)


class TestAnalyze:
    def test_rule_results_none_when_no_rule_engine(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        analysis = engine.analyze(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        assert analysis.rule_results is None

    def test_rule_results_none_when_no_fact_registry_supplied(self, event_record, natal_snapshot, simple_dasha_tree):
        stub_rules = StubRuleEngine(results=[_make_rule_result()])
        engine = EventEngine(rule_engine=stub_rules)
        analysis = engine.analyze(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)
        assert analysis.rule_results is None

    def test_rule_engine_consumed_not_reimplemented(self, event_record, natal_snapshot, simple_dasha_tree):
        expected_result = _make_rule_result("RULE-42", matched=True)
        stub_rules = StubRuleEngine(results=[expected_result])
        engine = EventEngine(rule_engine=stub_rules)

        registry = FactRegistry()
        registry.add_fact(Fact("planet.jupiter.house", 10, "graha_engine"))

        analysis = engine.analyze(
            event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot, fact_registry=registry
        )

        # Exactly the stub's own result object, unmodified — never re-derived.
        assert analysis.rule_results == (expected_result,)

    def test_original_fact_registry_not_mutated(self, event_record, natal_snapshot, simple_dasha_tree):
        stub_rules = StubRuleEngine(results=[])
        engine = EventEngine(rule_engine=stub_rules)

        registry = FactRegistry()
        registry.add_fact(Fact("planet.jupiter.house", 10, "graha_engine"))
        original_count = registry.fact_count()

        engine.analyze(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot, fact_registry=registry)

        assert registry.fact_count() == original_count
        assert not registry.has_fact("dasha.vimshottari.level1.lord")

    def test_dasha_facts_merged_into_registry_passed_to_rule_engine(
        self, event_record, natal_snapshot, simple_dasha_tree
    ):
        stub_rules = StubRuleEngine(results=[])
        engine = EventEngine(rule_engine=stub_rules)

        registry = FactRegistry()
        registry.add_fact(Fact("planet.jupiter.house", 10, "graha_engine"))

        engine.analyze(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot, fact_registry=registry)

        merged = stub_rules.received_registry
        assert merged is not registry  # a new registry, not the caller's own
        assert merged.get_value("planet.jupiter.house") == 10
        assert merged.get_value("dasha.vimshottari.level1.lord") == "jupiter"
        assert merged.get_value("dasha.vimshottari.level2.lord") == "venus"

    def test_event_facts_include_rule_results_when_present(self, event_record, natal_snapshot, simple_dasha_tree):
        stub_rules = StubRuleEngine(results=[_make_rule_result("RULE-7", matched=False)])
        engine = EventEngine(rule_engine=stub_rules)
        registry = FactRegistry()

        analysis = engine.analyze(
            event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot, fact_registry=registry
        )

        keys = {f.key: f.value for f in analysis.event_facts}
        assert keys[f"event.{event_record.id}.rule.RULE-7.matched"] is False

    def test_returns_event_analysis_with_expected_composition(self, event_record, natal_snapshot, simple_dasha_tree):
        engine = EventEngine()
        analysis = engine.analyze(event_record, {"vimshottari": simple_dasha_tree}, natal_snapshot)

        assert isinstance(analysis, EventAnalysis)
        assert analysis.event is event_record
        assert isinstance(analysis.context, EventAstrologicalContext)
        assert analysis.analysis_version == "1.0"

    def test_no_predictive_or_causal_language_in_analysis_object_fields(
        self, event_record, natal_snapshot, simple_dasha_tree
    ):
        # Structural guard, mirroring test_arishta_results_do_not_contain_predictive_language
        # (Module 8): EventAnalysis carries no free-text interpretation field at all to
        # check — the object itself has no score/explanation/prediction field.
        analysis_fields = EventAnalysis.__dataclass_fields__.keys()
        assert "score" not in analysis_fields
        assert "prediction" not in analysis_fields
        assert "explanation" not in analysis_fields
