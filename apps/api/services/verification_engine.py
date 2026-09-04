"""
AstroOS — Verification Engine (Module 16, Phase 1)

Maps rule evaluations (from RuleEngine) to recorded life events, producing
a structured classification of how well astrological interpretations align
with actual events.

Takes an already-built Timeline — never calls any astrology engine or
EventEngine/TimelineEngine itself. Same "compute once, reuse" discipline as
every engine in this stack.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any, Optional

from apps.api.domain.rules import RuleResult
from apps.api.domain.timeline import Timeline, TimelineEntry
from apps.api.domain.verification import (
    Alignment,
    RuleVerificationSummary,
    VerificationFindings,
    VerificationPair,
    VerificationStrength,
)

_KNOWN_EVENT_CATEGORIES = frozenset({
    "marriage",
    "career",
    "education",
    "health",
    "progeny",
    "wealth",
    "longevity",
})

_ENGINE_VERSION = "1.0"


def infer_rule_domains(
    derived_facts: dict[str, Any],
    rule_category: str,
) -> tuple[str, ...]:
    """
    Extract ALL domains from derived_fact key prefixes.

    For each key in derived_facts:
      prefix = key.split(".")[0]
      if prefix in _KNOWN_EVENT_CATEGORIES:
        add to result set

    If no prefix matches a known category:
      result = {rule_category}  (fallback)

    Returns sorted tuple (stable, deterministic).
    """
    domains: set[str] = set()
    for key in derived_facts:
        prefix = key.split(".", 1)[0]
        if prefix in _KNOWN_EVENT_CATEGORIES:
            domains.add(prefix)

    if not domains:
        domains.add(rule_category)

    return tuple(sorted(domains))


def _determine_alignment(
    inferred_domains: tuple[str, ...],
    event_category: Optional[str],
) -> Alignment:
    """Classify alignment between a rule's inferred domains and an event's category."""
    if event_category is None:
        return Alignment.UNTESTED
    if any(d == event_category for d in inferred_domains):
        return Alignment.CONFIRMED
    return Alignment.CATEGORY_MISMATCH


def _determine_strength(
    alignment: Alignment,
    event_is_verified: bool,
) -> VerificationStrength:
    """Determine evidence strength from alignment and event verification status."""
    if alignment == Alignment.CONFIRMED:
        return VerificationStrength.HIGH if event_is_verified else VerificationStrength.MEDIUM
    if alignment == Alignment.CATEGORY_MISMATCH:
        return VerificationStrength.LOW
    return VerificationStrength.UNKNOWN


def _build_explanation(
    rule: RuleResult,
    alignment: Alignment,
    strength: VerificationStrength,
    inferred_domains: tuple[str, ...],
    event_title: str,
    event_category: Optional[str],
) -> str:
    """Build a structured natural-language explanation for a VerificationPair."""
    base = (
        f"Rule {rule.rule_id} ({rule.explanation or 'no description'}) "
        f"{'matched' if rule.matched else 'did not match'} "
        f"→ derived facts: {dict(rule.derived_facts) if rule.matched else 'none'}."
    )

    if alignment == Alignment.NOT_APPLICABLE:
        return f"{base} Rule did not match — no interpretation was made. Strength: UNKNOWN."

    domains_str = str(list(inferred_domains))
    cat_str = f"'{event_title}' ({event_category or 'no category'})"

    if alignment == Alignment.UNTESTED:
        return (
            f"{base} Inferred domain(s): {domains_str}. "
            f"Event {cat_str} has no category. Cannot confirm or refute. "
            f"Strength: UNKNOWN."
        )

    if alignment == Alignment.CONFIRMED:
        verified_str = "Event is verified." if strength == VerificationStrength.HIGH else "Event is unverified."
        return (
            f"{base} Inferred domain(s): {domains_str}. "
            f"Event {cat_str} aligns. "
            f"{verified_str} Strength: {strength.value.upper()}."
        )

    # CATEGORY_MISMATCH
    return (
        f"{base} Inferred domain(s): {domains_str}. "
        f"Event {cat_str} does not align with any inferred domain {domains_str}. "
        f"Strength: LOW."
    )


class VerificationEngine:
    """
    Verifies astrological interpretations (RuleEngine results) against
    recorded life events by classifying each (rule, event) pair.

    Takes an already-built Timeline — never performs any astrology
    calculation or re-runs any engine.
    """

    _ENGINE_VERSION = _ENGINE_VERSION

    # ── Main entry point ─────────────────────────────────────────────────

    @staticmethod
    def verify_timeline(timeline: Timeline) -> VerificationFindings:
        """
        Run verification across all entries in a timeline.

        For each TimelineEntry with rule_results, examines every
        RuleResult and produces a VerificationPair. Aggregates per-rule
        summaries.

        Raises ValueError if any entry has rule_results=None (caller
        constructed EventEngine without a RuleEngine). Entries with
        empty rule_results are silently skipped.
        """
        for entry in timeline.entries:
            if entry.analysis.rule_results is None:
                raise ValueError(
                    f"Timeline entry {entry.event_id} has rule_results=None. "
                    "EventEngine must be constructed with a RuleEngine for verification."
                )

        pairs: list[VerificationPair] = []
        chart_id = timeline.chart_id
        earliest = timeline.date_range[0]
        latest = timeline.date_range[1]

        for entry in timeline.entries:
            rule_results = entry.analysis.rule_results or ()
            for rule_result in rule_results:
                pair = _build_pair(entry, rule_result)
                pairs.append(pair)

        summaries = _build_summaries(tuple(pairs))

        # Count unique rule_ids across all pairs.
        unique_rule_ids = len({p.rule_id for p in pairs})

        # Compute confidence score (0.0–1.0).
        total_pairs = len(pairs)
        confirmed = sum(1 for p in pairs if p.alignment == Alignment.CONFIRMED)
        matched = sum(1 for p in pairs if p.rule_matched)
        verified_events = sum(1 for p in pairs if p.event_is_verified)

        if total_pairs > 0 and unique_rule_ids > 0 and timeline.total_events > 0:
            confidence_score = (
                (confirmed / max(total_pairs, 1))
                * (matched / max(unique_rule_ids, 1))
                * (verified_events / max(timeline.total_events, 1))
            )
            confidence_score = round(min(confidence_score, 1.0), 4)
        else:
            confidence_score = 0.0

        return VerificationFindings(
            chart_id=chart_id,
            period_covered=(earliest, latest),
            total_events=timeline.total_events,
            total_rules_evaluated=unique_rule_ids,
            total_pairs=total_pairs,
            rule_summaries=summaries,
            verification_pairs=tuple(pairs),
            engine_version=_ENGINE_VERSION,
            confidence_score=confidence_score,
        )

    # ── Convenience methods ──────────────────────────────────────────────

    @staticmethod
    def verify_rule(
        timeline: Timeline,
        rule_id: str,
    ) -> RuleVerificationSummary | None:
        """
        Verify a single rule across all timeline entries.

        Returns the RuleVerificationSummary for *rule_id*, or None if
        no entry had a result for that rule.
        """
        findings = VerificationEngine.verify_timeline(timeline)
        for summary in findings.rule_summaries:
            if summary.rule_id == rule_id:
                return summary
        return None

    @staticmethod
    def event_coverage(findings: VerificationFindings) -> dict[str, int]:
        """
        Count events by coverage status.

        Returns {"covered": N, "uncovered": M} where "covered" means at
        least one rule matched with CONFIRMED alignment for that event.
        """
        covered: set[uuid.UUID] = set()
        uncovered: set[uuid.UUID] = set()

        for pair in findings.verification_pairs:
            if pair.alignment == Alignment.CONFIRMED:
                covered.add(pair.event_id)
            else:
                uncovered.add(pair.event_id)

        # An event in both covered and uncovered means it had at least
        # one CONFIRMED rule, so it's covered.
        truly_uncovered = uncovered - covered

        return {"covered": len(covered), "uncovered": len(truly_uncovered)}


# ── Private helpers ────────────────────────────────────────────────────────


def _build_pair(
    entry: TimelineEntry,
    rule_result: RuleResult,
) -> VerificationPair:
    """Build one VerificationPair from a TimelineEntry + RuleResult."""
    event = entry.analysis.event

    inferred_domains = infer_rule_domains(
        rule_result.derived_facts,
        rule_category="general",
    )

    if not rule_result.matched:
        alignment = Alignment.NOT_APPLICABLE
    else:
        alignment = _determine_alignment(inferred_domains, event.category)

    strength = _determine_strength(alignment, event.is_verified if rule_result.matched else False)
    explanation = _build_explanation(
        rule_result, alignment, strength, inferred_domains,
        event.title, event.category,
    )

    return VerificationPair(
        rule_id=rule_result.rule_id,
        rule_name=rule_result.rule_id,  # will be enriched from RuleDefinition if needed
        rule_category="general",
        rule_matched=rule_result.matched,
        event_id=event.id,
        event_date=event.event_date,
        event_title=event.title,
        event_description=event.description,
        event_category=event.category,
        event_is_verified=event.is_verified,
        derived_facts=dict(rule_result.derived_facts),
        inferred_domains=inferred_domains,
        alignment=alignment,
        strength=strength,
        explanation=explanation,
    )


def _build_summaries(
    pairs: tuple[VerificationPair, ...],
) -> tuple[RuleVerificationSummary, ...]:
    """Aggregate per-rule summaries from all verification pairs."""
    # Group pairs by rule_id.
    by_rule: dict[str, list[VerificationPair]] = defaultdict(list)
    for pair in pairs:
        by_rule[pair.rule_id].append(pair)

    summaries: list[RuleVerificationSummary] = []
    for rule_id, rule_pairs in sorted(by_rule.items()):
        total = len(rule_pairs)
        matched = sum(1 for p in rule_pairs if p.rule_matched)
        confirmed = sum(1 for p in rule_pairs if p.alignment == Alignment.CONFIRMED)
        untested = sum(1 for p in rule_pairs if p.alignment == Alignment.UNTESTED)
        mismatched = sum(1 for p in rule_pairs if p.alignment == Alignment.CATEGORY_MISMATCH)

        strengths: dict[str, int] = defaultdict(int)
        for p in rule_pairs:
            strengths[p.strength.value] += 1

        summaries.append(RuleVerificationSummary(
            rule_id=rule_id,
            rule_name=rule_id,
            rule_category="general",
            total_evaluations=total,
            times_matched=matched,
            times_confirmed=confirmed,
            times_untested=untested,
            times_mismatched=mismatched,
            strengths=dict(strengths),
            event_ids_confirmed=tuple(
                p.event_id for p in rule_pairs if p.alignment == Alignment.CONFIRMED
            ),
            event_ids_untested=tuple(
                p.event_id for p in rule_pairs if p.alignment == Alignment.UNTESTED
            ),
            event_ids_mismatched=tuple(
                p.event_id for p in rule_pairs if p.alignment == Alignment.CATEGORY_MISMATCH
            ),
        ))

    return tuple(summaries)
