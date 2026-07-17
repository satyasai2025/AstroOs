"""
AstroOS — Verification Domain Objects (Module 16, Phase 1)

Maps rule evaluations (RuleEngine results) to recorded life events,
classifying each pair by alignment and strength of supporting evidence.

Pure Python dataclasses + enums — no ORM/Pydantic dependency, matching
every other domain module in this codebase.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Optional


class Alignment(str, Enum):
    """
    Classification of how a rule result relates to an event's category.

    CONFIRMED:  rule matched AND event category aligns with an inferred domain.
    UNTESTED:   rule matched BUT event has no category — cannot compare.
    CATEGORY_MISMATCH: rule matched BUT event category differs from every
                inferred domain. Not a contradiction — the rule may still be
                valid; this specific event simply does not test it.
    NOT_APPLICABLE: rule did NOT match — no interpretation was made.
    """

    CONFIRMED = "confirmed"
    UNTESTED = "untested"
    CATEGORY_MISMATCH = "category_mismatch"
    NOT_APPLICABLE = "not_applicable"


class VerificationStrength(str, Enum):
    """
    Amount of supporting evidence for a VerificationPair.

    HIGH:    CONFIRMED alignment + event is_verified=True.
    MEDIUM:  CONFIRMED alignment + event is_verified=False.
    LOW:     CATEGORY_MISMATCH (rule fired but event doesn't test it).
    UNKNOWN: UNTESTED or NOT_APPLICABLE — no conclusion possible.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class VerificationPair:
    """
    One rule result paired with one event, classified by alignment and
    evidence strength. Carries the full EventRecord context (title,
    description, category, is_verified) so callers have everything
    they need without traversing back to the original EventAnalysis.
    """

    rule_id: str
    rule_name: str
    rule_category: str
    rule_matched: bool

    event_id: uuid.UUID
    event_date: date
    event_title: str
    event_description: Optional[str]
    event_category: Optional[str]
    event_is_verified: bool

    derived_facts: dict[str, Any]
    inferred_domains: tuple[str, ...]
    alignment: Alignment
    strength: VerificationStrength
    explanation: str


@dataclass(frozen=True)
class RuleVerificationSummary:
    """
    Aggregated verification results for one rule across the full timeline.
    strengths counts each VerificationStrength tier for quick scanning.
    """

    rule_id: str
    rule_name: str
    rule_category: str
    total_evaluations: int
    times_matched: int
    times_confirmed: int
    times_untested: int
    times_mismatched: int
    strengths: dict[str, int]  # "HIGH" -> N, "MEDIUM" -> N, "LOW" -> N, "UNKNOWN" -> N
    event_ids_confirmed: tuple[uuid.UUID, ...]
    event_ids_untested: tuple[uuid.UUID, ...]
    event_ids_mismatched: tuple[uuid.UUID, ...]


@dataclass(frozen=True)
class VerificationFindings:
    """
    Top-level container for one chart's complete verification results.

    verification_pairs is the full detail — one entry per (event, rule)
    combination. rule_summaries aggregates per rule. Both cover the same
    data at different granularities.
    """

    chart_id: uuid.UUID
    period_covered: tuple[date, date]
    total_events: int
    total_rules_evaluated: int
    total_pairs: int
    rule_summaries: tuple[RuleVerificationSummary, ...]
    verification_pairs: tuple[VerificationPair, ...]
    engine_version: str = "1.0"
