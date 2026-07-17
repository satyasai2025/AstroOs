"""
AstroOS — Verification Engine Integration Tests (Module 16, Phase 1)

Full pipeline: EventEngine.analyze() → TimelineEngine.build_timeline()
→ VerificationEngine.verify_timeline(). Uses stubs for TransitEngine
and RuleEngine, same pattern as every prior module's integration suite.
"""

import uuid
from datetime import date

from apps.api.domain.dasha import DashaPeriod, DashaTree
from apps.api.domain.events import EventRecord
from apps.api.domain.facts import Fact
from apps.api.domain.rules import RuleResult
from apps.api.services.event_engine import EventEngine
from apps.api.services.fact_registry import FactRegistry
from apps.api.services.timeline_engine import TimelineEngine
from apps.api.services.verification_engine import VerificationEngine
from apps.api.domain.verification import Alignment, VerificationStrength


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
            _period("venus", date(1990, 1, 1), date(2010, 1, 1), level=1),
            _period("sun", date(2010, 1, 1), date(2016, 1, 1), level=1),
        ),
        max_depth=1, total_cycle_years=120,
    )


class StubTransitEngine:
    def compute_transit(self, natal_chart, transit_datetime_utc):
        from apps.api.domain.transit import TransitPlanetResult
        return [
            TransitPlanetResult(
                planet="jupiter", transit_rashi="libra", house_from_natal_moon=6,
                ashtakavarga_bindus=3,
            ),
        ]


class FixedRuleEngine:
    """Returns fixed RuleResults matching the event's category context."""

    def __init__(self):
        self.last_facts = None

    def evaluate_all(self, facts):
        self.last_facts = facts
        # Return one career rule and one general rule.
        return [
            RuleResult(
                rule_id="RULE-CAREER-001", matched=True,
                matched_conditions=("career condition",),
                failed_conditions=(), derived_facts={"career.leadership": "high"},
                explanation="Career rule matched",
                evaluation_trace=(), execution_time=0.001,
            ),
            RuleResult(
                rule_id="RULE-GENERAL-001", matched=True,
                matched_conditions=("general condition",),
                failed_conditions=(), derived_facts={"wisdom.growth": True},
                explanation="General rule matched",
                evaluation_trace=(), execution_time=0.001,
            ),
        ]


class TestVerificationIntegration:
    """End-to-end: EventEngine → TimelineEngine → VerificationEngine."""

    def test_full_pipeline_confirmed_career_event(self, natal_snapshot):
        """A verified career event with a career-rule → HIGH strength."""
        engine = EventEngine(
            transit_engine=StubTransitEngine(),
            rule_engine=FixedRuleEngine(),
        )
        tree = _vimshottari_tree()

        event = EventRecord(
            id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
            event_date=date(2005, 6, 1), title="Promotion", category="career",
            is_verified=True,
        )

        facts = FactRegistry()
        facts.add_fact(Fact("planet.sun.house", 10, "graha_engine"))
        analysis = engine.analyze(event, {"vimshottari": tree}, natal_snapshot, fact_registry=facts)
        timeline = TimelineEngine.build_timeline((analysis,))
        findings = VerificationEngine.verify_timeline(timeline)

        assert findings.total_events == 1
        assert findings.total_pairs == 2  # 2 rules returned

        # Career rule should be CONFIRMED + HIGH.
        career_pairs = [p for p in findings.verification_pairs if "CAREER" in p.rule_id]
        assert len(career_pairs) == 1
        assert career_pairs[0].alignment == Alignment.CONFIRMED
        assert career_pairs[0].strength == VerificationStrength.HIGH
        assert "career" in career_pairs[0].inferred_domains

    def test_full_pipeline_category_mismatch(self, natal_snapshot):
        """A marriage event with career-rule → MISMATCH + LOW."""
        engine = EventEngine(
            transit_engine=StubTransitEngine(),
            rule_engine=FixedRuleEngine(),
        )
        tree = _vimshottari_tree()

        event = EventRecord(
            id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
            event_date=date(2005, 6, 1), title="Wedding", category="marriage",
            is_verified=True,
        )

        facts = FactRegistry()
        facts.add_fact(Fact("planet.sun.house", 10, "graha_engine"))
        analysis = engine.analyze(event, {"vimshottari": tree}, natal_snapshot, fact_registry=facts)
        timeline = TimelineEngine.build_timeline((analysis,))
        findings = VerificationEngine.verify_timeline(timeline)

        career_pairs = [p for p in findings.verification_pairs if "CAREER" in p.rule_id]
        assert career_pairs[0].alignment == Alignment.CATEGORY_MISMATCH
        assert career_pairs[0].strength == VerificationStrength.LOW

    def test_full_pipeline_event_coverage(self, natal_snapshot):
        """Two events: one confirmed, one mismatch — verify coverage counts."""
        engine = EventEngine(
            transit_engine=StubTransitEngine(),
            rule_engine=FixedRuleEngine(),
        )
        tree = _vimshottari_tree()

        events = [
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(2005, 1, 1), title="Promotion",
                        category="career", is_verified=True),
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(2007, 1, 1), title="Wedding",
                        category="marriage", is_verified=True),
        ]

        facts = FactRegistry()
        facts.add_fact(Fact("planet.sun.house", 10, "graha_engine"))
        analyses = [engine.analyze(e, {"vimshottari": tree}, natal_snapshot, fact_registry=facts) for e in events]
        timeline = TimelineEngine.build_timeline(tuple(analyses))
        findings = VerificationEngine.verify_timeline(timeline)
        coverage = VerificationEngine.event_coverage(findings)

        # Event 1 has at least one CONFIRMED career rule → covered.
        # Event 2 has no CONFIRMED rules for career → uncovered
        #   (marriage doesn't match any career-related domain).
        assert coverage["covered"] == 1
        assert coverage["uncovered"] >= 1

    def test_rule_summary_aggregation(self, natal_snapshot):
        """Two events with same rule → summary counts both."""
        engine = EventEngine(
            transit_engine=StubTransitEngine(),
            rule_engine=FixedRuleEngine(),
        )
        tree = _vimshottari_tree()

        events = [
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(2000, 1, 1), title="First",
                        category="career", is_verified=True),
            EventRecord(id=uuid.uuid4(), chart_id=natal_snapshot.chart_id,
                        event_date=date(2005, 1, 1), title="Second",
                        category="career", is_verified=False),
        ]

        facts = FactRegistry()
        facts.add_fact(Fact("planet.sun.house", 10, "graha_engine"))
        analyses = [engine.analyze(e, {"vimshottari": tree}, natal_snapshot, fact_registry=facts) for e in events]
        timeline = TimelineEngine.build_timeline(tuple(analyses))
        findings = VerificationEngine.verify_timeline(timeline)

        career_summary = [s for s in findings.rule_summaries if "CAREER" in s.rule_id]
        assert len(career_summary) == 1
        assert career_summary[0].times_matched == 2
        assert career_summary[0].times_confirmed == 2
        assert career_summary[0].strengths.get("high", 0) == 1
        assert career_summary[0].strengths.get("medium", 0) == 1
