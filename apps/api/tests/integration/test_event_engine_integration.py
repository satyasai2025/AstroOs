"""
Integration-style tests for Module 14 (Event Engine) — exercises
EventEngine.analyze() end-to-end across multiple Dasha systems, a
Transit stub, and a Rule Engine stub together, the same "full pipeline,
still with test doubles for the heavy ephemeris-backed engines" shape
used by every prior module's own integration suite (e.g. Shadbala's
stub DivisionalEngine, Tribhaga's stub EphemerisWrapper).
"""

import uuid
from datetime import date

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.events import EventRecord
from apps.api.domain.facts import Fact
from apps.api.domain.rules import RuleResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.services.event_engine import EventEngine
from apps.api.services.fact_registry import FactRegistry


def _period(lord, start, end, level, sub=()):
    return DashaPeriod(
        lord=lord, start_date=start, end_date=end,
        duration_days=(end - start).days, level=level, sub_periods=sub,
    )


def _vimshottari_tree():
    return DashaTree(
        system="vimshottari", birth_date=date(1990, 1, 1),
        trigger_planet="venus", trigger_nakshatra="bharani", trigger_nakshatra_number=2,
        mahadashas=(
            _period("venus", date(1990, 1, 1), date(2010, 1, 1), level=1,
                    sub=(_period("venus", date(1990, 1, 1), date(1993, 1, 1), level=2),
                         _period("sun", date(1993, 1, 1), date(1994, 1, 1), level=2))),
            _period("sun", date(2010, 1, 1), date(2016, 1, 1), level=1),
        ),
        max_depth=2, total_cycle_years=120,
    )


def _yogini_tree():
    return DashaTree(
        system="yogini", birth_date=date(1990, 1, 1),
        trigger_planet="siddha", trigger_nakshatra="bharani", trigger_nakshatra_number=2,
        mahadashas=(
            _period("mangala", date(1990, 1, 1), date(2000, 1, 1), level=1),
            _period("pingala", date(2000, 1, 1), date(2005, 1, 1), level=1),
        ),
        max_depth=1, total_cycle_years=36,
    )


class MultiPlanetTransitEngine:
    def compute_transit(self, natal_chart, transit_datetime_utc):
        return [
            TransitPlanetResult(planet="jupiter", transit_rashi="libra", house_from_natal_moon=6, ashtakavarga_bindus=3),
            TransitPlanetResult(planet="saturn", transit_rashi="aquarius", house_from_natal_moon=10, ashtakavarga_bindus=2),
        ]


class EchoRuleEngine:
    """Returns a fixed, pre-built RuleResult set — never derives its own logic."""

    def __init__(self, results):
        self._results = results
        self.last_facts = None

    def evaluate_all(self, facts):
        self.last_facts = facts
        return list(self._results)


class TestFullPipeline:
    def test_multi_system_multi_engine_analysis(self, natal_snapshot):
        event = EventRecord(
            id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
            event_date=date(1993, 6, 1), title="Career change", category="career",
            is_verified=True,
        )

        precomputed_result = RuleResult(
            rule_id="RULE-CAREER-001", matched=True, matched_conditions=("x",),
            failed_conditions=(), derived_facts={"career.leadership": "high"},
            explanation="Sun antardasha active", evaluation_trace=(), execution_time=0.001,
        )
        rule_engine = EchoRuleEngine(results=[precomputed_result])
        transit_engine = MultiPlanetTransitEngine()

        engine = EventEngine(transit_engine=transit_engine, rule_engine=rule_engine)

        base_registry = FactRegistry()
        base_registry.add_fact(Fact("planet.sun.house", 10, "graha_engine"))
        base_registry.add_fact(Fact("yoga.BPHS-PM-001.present", True, "yoga_engine"))

        dasha_trees = {"vimshottari": _vimshottari_tree(), "yogini": _yogini_tree()}

        analysis = engine.analyze(event, dasha_trees, natal_snapshot, fact_registry=base_registry)

        # Dasha: 1993-06-01 falls in venus mahadasha / sun antardasha (vimshottari),
        # and mangala mahadasha (yogini, no sub-periods).
        assert [p.lord for p in analysis.context.active_dashas["vimshottari"]] == ["venus", "sun"]
        assert [p.lord for p in analysis.context.active_dashas["yogini"]] == ["mangala"]

        # Transit: passed through from the stub engine unmodified.
        assert {t.planet for t in analysis.context.transits} == {"jupiter", "saturn"}

        # Rule Engine: exactly the pre-built result, never re-derived.
        assert analysis.rule_results == (precomputed_result,)

        # The merged registry handed to RuleEngine contains the caller's own
        # facts AND both systems' dasha facts, but the caller's original
        # registry was left untouched.
        assert rule_engine.last_facts.get_value("planet.sun.house") == 10
        assert rule_engine.last_facts.get_value("dasha.vimshottari.level1.lord") == "venus"
        assert rule_engine.last_facts.get_value("dasha.vimshottari.level2.lord") == "sun"
        assert rule_engine.last_facts.get_value("dasha.yogini.level1.lord") == "mangala"
        assert base_registry.fact_count() == 2

        # Standardized event.* facts include category, verified, dasha (both
        # systems), and the rule match — all under one namespace.
        fact_keys = {f.key: f.value for f in analysis.event_facts}
        assert fact_keys[f"event.{event.id}.category"] == "career"
        assert fact_keys[f"event.{event.id}.dasha.vimshottari.level1.lord"] == "venus"
        assert fact_keys[f"event.{event.id}.dasha.yogini.level1.lord"] == "mangala"
        assert fact_keys[f"event.{event.id}.rule.RULE-CAREER-001.matched"] is True

    def test_natal_snapshot_shared_across_two_events_same_chart(self, natal_snapshot):
        """
        The core non-duplication guarantee: two different EventRecords for
        the SAME chart reuse the identical NatalSnapshot instance — Yoga/
        Shadbala/Ashtakavarga are never recomputed per event.
        """
        engine = EventEngine()
        tree = _vimshottari_tree()

        event_a = EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                               event_date=date(1991, 1, 1), title="Event A")
        event_b = EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                               event_date=date(2011, 1, 1), title="Event B")

        analysis_a = engine.analyze(event_a, {"vimshottari": tree}, natal_snapshot)
        analysis_b = engine.analyze(event_b, {"vimshottari": tree}, natal_snapshot)

        assert analysis_a.context.natal_snapshot is natal_snapshot
        assert analysis_b.context.natal_snapshot is natal_snapshot
        assert analysis_a.context.natal_snapshot is analysis_b.context.natal_snapshot
        # But the per-event, date-dependent parts genuinely differ.
        assert analysis_a.context.active_dashas["vimshottari"][0].lord == "venus"
        assert analysis_b.context.active_dashas["vimshottari"][0].lord == "sun"
