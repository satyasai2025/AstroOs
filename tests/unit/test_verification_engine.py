"""
AstroOS — VerificationEngine Unit Tests (Module 16, Phase 1)

Tests use synthetic Timeline + EventAnalysis objects with hand-crafted
RuleResults. No real engines, no DB, no Ephemeris.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.events import EventAnalysis, EventAstrologicalContext, EventRecord
from apps.api.domain.facts import Fact
from apps.api.domain.rules import RuleResult
from apps.api.domain.timeline import Timeline, TimelineEntry, TimelineSummary
from apps.api.domain.verification import Alignment, VerificationStrength
from apps.api.services.verification_engine import (
    VerificationEngine,
    infer_rule_domains,
)


# ── infer_rule_domains ───────────────────────────────────────────────────────


class TestInferRuleDomains:
    def test_extracts_prefix_from_known_category(self):
        domains = infer_rule_domains({"career.leadership": "high"}, "general")
        assert domains == ("career",)

    def test_collects_all_matching_prefixes(self):
        domains = infer_rule_domains(
            {"career.leadership": "high", "wealth.potential": 0.8, "health.vitality": 70},
            "general",
        )
        assert set(domains) == {"career", "health", "wealth"}

    def test_skips_unknown_prefix(self):
        domains = infer_rule_domains({"wisdom.growth": True}, "general")
        assert domains == ("general",)  # fallback

    def test_empty_derived_facts_falls_back_to_rule_category(self):
        domains = infer_rule_domains({}, "dignity")
        assert domains == ("dignity",)

    def test_mixed_known_and_unknown_prefixes(self):
        domains = infer_rule_domains(
            {"career.advancement": True, "some.custom.key": 42},
            "general",
        )
        assert domains == ("career",)  # only known prefixes included

    def test_returns_sorted_tuple(self):
        domains = infer_rule_domains(
            {"wealth.gain": 1, "career.promotion": 1, "education.degree": 1},
            "general",
        )
        assert domains == ("career", "education", "wealth")


# ── VerificationEngine ───────────────────────────────────────────────────────


class TestVerifyTimeline:
    def test_empty_timeline(self):
        timeline = _empty_timeline()
        findings = VerificationEngine.verify_timeline(timeline)
        assert findings.total_events == 0
        assert findings.total_pairs == 0
        assert findings.rule_summaries == ()

    def test_single_event_single_rule_confirmed(self):
        timeline = _make_timeline([
            _make_entry(
                date(2005, 1, 1), "Promotion", "career", is_verified=True,
                rules=[_make_rule("RULE-HOUSE-001", matched=True,
                                  derived_facts={"career.leadership": "high"})],
            ),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        assert findings.total_pairs == 1
        pair = findings.verification_pairs[0]
        assert pair.alignment == Alignment.CONFIRMED
        assert pair.strength == VerificationStrength.HIGH
        assert pair.event_title == "Promotion"

    def test_single_event_single_rule_unverified_medium(self):
        """CONFIRMED but unverified event → MEDIUM strength."""
        timeline = _make_timeline([
            _make_entry(
                date(2005, 1, 1), "Promotion", "career", is_verified=False,
                rules=[_make_rule("RULE-HOUSE-001", matched=True,
                                  derived_facts={"career.leadership": "high"})],
            ),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        pair = findings.verification_pairs[0]
        assert pair.alignment == Alignment.CONFIRMED
        assert pair.strength == VerificationStrength.MEDIUM

    def test_rule_not_matched_not_applicable(self):
        timeline = _make_timeline([
            _make_entry(
                date(2005, 1, 1), "Test", "career",
                rules=[_make_rule("RULE-001", matched=False)],
            ),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        pair = findings.verification_pairs[0]
        assert pair.alignment == Alignment.NOT_APPLICABLE
        assert pair.strength == VerificationStrength.UNKNOWN
        assert pair.rule_matched is False

    def test_no_event_category_untested(self):
        timeline = _make_timeline([
            _make_entry(
                date(2005, 1, 1), "Something", category=None,
                rules=[_make_rule("RULE-001", matched=True,
                                  derived_facts={"career.leadership": "high"})],
            ),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        pair = findings.verification_pairs[0]
        assert pair.alignment == Alignment.UNTESTED
        assert pair.strength == VerificationStrength.UNKNOWN

    def test_category_mismatch_low(self):
        timeline = _make_timeline([
            _make_entry(
                date(2005, 1, 1), "Wedding", "marriage",
                rules=[_make_rule("RULE-001", matched=True,
                                  derived_facts={"career.leadership": "high"})],
            ),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        pair = findings.verification_pairs[0]
        assert pair.alignment == Alignment.CATEGORY_MISMATCH
        assert pair.strength == VerificationStrength.LOW

    def test_rule_results_none_raises(self):
        entry = _make_entry(date(2005, 1, 1), "X", "career", rules=None)
        timeline = _make_timeline([entry])
        with pytest.raises(ValueError, match="rule_results=None"):
            VerificationEngine.verify_timeline(timeline)

    def test_multiple_rules_per_event(self):
        timeline = _make_timeline([
            _make_entry(
                date(2005, 1, 1), "Promotion", "career", is_verified=True,
                rules=[
                    _make_rule("RULE-HOUSE-001", matched=True,
                               derived_facts={"career.leadership": "high"}),
                    _make_rule("RULE-DIG-002", matched=True,
                               derived_facts={"career.authority": True}),
                ],
            ),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        assert findings.total_pairs == 2
        assert all(p.alignment == Alignment.CONFIRMED for p in findings.verification_pairs)
        assert findings.total_rules_evaluated == 2

    def test_multiple_events_same_rule_summary(self):
        timeline = _make_timeline([
            _make_entry(date(2000, 1, 1), "Job A", "career", is_verified=True,
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
            _make_entry(date(2005, 1, 1), "Job B", "career", is_verified=False,
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        assert findings.total_pairs == 2
        assert len(findings.rule_summaries) == 1
        summary = findings.rule_summaries[0]
        assert summary.times_matched == 2
        assert summary.times_confirmed == 2
        assert summary.strengths.get("high", 0) == 1
        assert summary.strengths.get("medium", 0) == 1

    def test_empty_rule_results_skipped(self):
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "A", "career", rules=[]),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        assert findings.total_pairs == 0


class TestVerifyRule:
    def test_returns_summary_for_known_rule(self):
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "A", "career",
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
        ])
        summary = VerificationEngine.verify_rule(timeline, "RULE-001")
        assert summary is not None
        assert summary.rule_id == "RULE-001"
        assert summary.times_matched == 1

    def test_returns_none_for_unknown_rule(self):
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "A", "career",
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
        ])
        summary = VerificationEngine.verify_rule(timeline, "RULE-UNKNOWN")
        assert summary is None


class TestEventCoverage:
    def test_all_events_covered(self):
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "A", "career",
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
            _make_entry(date(2006, 1, 1), "B", "career",
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        coverage = VerificationEngine.event_coverage(findings)
        assert coverage["covered"] == 2
        assert coverage["uncovered"] == 0

    def test_no_covered_events(self):
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "A", "marriage",
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        coverage = VerificationEngine.event_coverage(findings)
        assert coverage["covered"] == 0
        assert coverage["uncovered"] == 1

    def test_inferred_domains_collect_all(self):
        """Multiple derived_fact prefixes are all collected."""
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "Event", "career", is_verified=True,
                        rules=[_make_rule("RULE-001", matched=True, derived_facts={
                            "career.advancement": True,
                            "wealth.gain": 0.5,
                        })]),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        pair = findings.verification_pairs[0]
        assert "career" in pair.inferred_domains
        assert "wealth" in pair.inferred_domains
        # Event category is "career" which matches one of the domains.
        assert pair.alignment == Alignment.CONFIRMED
        assert pair.strength == VerificationStrength.HIGH

    def test_explanation_includes_all_domains(self):
        timeline = _make_timeline([
            _make_entry(date(2005, 1, 1), "Test", "career",
                        rules=[_make_rule("RULE-001", matched=True,
                                          derived_facts={"career.x": True})]),
        ])
        findings = VerificationEngine.verify_timeline(timeline)
        explanation = findings.verification_pairs[0].explanation
        assert "Inferred domain(s)" in explanation
        assert "career" in explanation


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_rule(
    rule_id: str = "RULE-001",
    matched: bool = True,
    derived_facts: dict | None = None,
) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        matched=matched,
        matched_conditions=("cond1",) if matched else (),
        failed_conditions=() if matched else ("cond1",),
        derived_facts=derived_facts or {},
        explanation="Test rule explanation" if matched else "",
        evaluation_trace=("trace",),
        execution_time=0.001,
    )


def _make_entry(
    event_date: date,
    title: str,
    category: str | None,
    is_verified: bool = False,
    rules: list[RuleResult] | None = None,
) -> TimelineEntry:
    cid = uuid.uuid4()
    eid = uuid.uuid4()

    event = EventRecord(
        id=eid, chart_id=cid, event_date=event_date,
        title=title, category=category, is_verified=is_verified,
        description=f"Description of {title}",
    )
    context = EventAstrologicalContext(
        event_id=eid, chart_id=cid,
        active_dashas={}, transits=(), natal_snapshot=None,
    )
    rule_tuple = tuple(rules) if rules is not None else None
    analysis = EventAnalysis(
        event=event, context=context,
        rule_results=rule_tuple,
        event_facts=(
            Fact(f"event.{eid}.category", category, "event_engine"),
            Fact(f"event.{eid}.is_verified", is_verified, "event_engine"),
        ) if category else (),
    )

    return TimelineEntry(
        event_id=eid, event_date=event_date, title=title,
        category=category, is_verified=is_verified,
        sort_key=event_date.isoformat(),
        analysis=analysis,
    )


def _make_timeline(entries: list[TimelineEntry]) -> Timeline:
    if not entries:
        return _empty_timeline()
    cid = entries[0].analysis.event.chart_id
    entries_tuple = tuple(entries)
    earliest = min(e.event_date for e in entries)
    latest = max(e.event_date for e in entries)

    categories: dict[str, int] = {}
    for e in entries:
        if e.category:
            categories[e.category] = categories.get(e.category, 0) + 1

    return Timeline(
        chart_id=cid,
        entries=entries_tuple,
        summary=TimelineSummary(
            total_events=len(entries),
            date_range=(earliest, latest),
            events_per_category=categories,
            events_per_dasha_system={},
            verified_count=sum(1 for e in entries if e.is_verified),
            unverified_count=sum(1 for e in entries if not e.is_verified),
        ),
        dasha_breakdown={},
        clusters=(),
    )


def _empty_timeline() -> Timeline:
    empty = uuid.UUID(int=0)
    return Timeline(
        chart_id=empty,
        entries=(),
        summary=TimelineSummary(
            total_events=0, date_range=(date(1, 1, 1), date(1, 1, 1)),
            events_per_category={}, events_per_dasha_system={},
            verified_count=0, unverified_count=0,
        ),
        dasha_breakdown={},
        clusters=(),
    )
