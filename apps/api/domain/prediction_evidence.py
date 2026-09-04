"""
AstroOS — Prediction Evidence Domain Models

A generic, technique-agnostic "why did this fire" evidence framework —
not Jaimini-specific, deliberately kept out of domain/jaimini.py so any
future rule-evaluating engine (Jaimini yogas, Parashari yogas, dasha-
triggered predictions, ...) can return results in this shape rather than
each inventing its own ad hoc evidence structure.

Mirrors the intent of domain/yoga.py's YogaDefinition/YogaResult split
(a static rule definition vs. its per-chart evaluated result) but
generalizes the result: every field YogaResult has informally via
strings/tuples (satisfied, missing, trace) is here made explicit and
structured (PredictionReason per condition, PredictionConfidence as its
own object rather than a bare int) specifically because a rule engine
consuming these must produce a real citation and a real confidence
breakdown for every match, not just a boolean.

Pure Python dataclasses — no ORM/Pydantic dependency, matching the
convention in domain/yoga.py, domain/jaimini.py.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionReason:
    """One atomic piece of supporting (or refuting) evidence for a rule."""

    description: str  # human-readable, e.g. "Atmakaraka (sun) occupies a Kendra from Arudha Lagna"
    matched_objects: tuple[str, ...]  # e.g. ("sun", "AL") — the concrete entities involved
    is_satisfied: bool  # True if this specific condition held for this chart


@dataclass(frozen=True)
class PredictionConfidence:
    """
    A 0-100 confidence score with a transparent breakdown, never a bare
    number — every score must be reconstructible from satisfied_conditions
    / total_conditions, not asserted independently of the evidence.
    """

    score: int  # 0-100
    satisfied_conditions: int
    total_conditions: int
    basis: str  # short note on how the score was derived

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError(f"score must be 0-100, got {self.score}")
        if self.satisfied_conditions > self.total_conditions:
            raise ValueError(
                f"satisfied_conditions ({self.satisfied_conditions}) cannot exceed "
                f"total_conditions ({self.total_conditions})"
            )


@dataclass(frozen=True)
class PredictionRule:
    """
    Static, registered-once definition of one prediction rule. Mirrors
    YogaDefinition's shape (stable id + explicit source citation +
    versioning) deliberately — a prediction with no sutra_reference is
    not a classical rule, it's an opinion, and this framework has no
    field to smuggle one in as if it were the former.
    """

    rule_id: str  # e.g. "JAIMINI-KARAKAMSA-001" — stable, never reused/renumbered once assigned
    name: str
    sutra_reference: str  # e.g. "Jaimini Upadesa Sutra 1.15" — the actual citation, not a paraphrase
    rule_version: str
    requires: tuple[str, ...]  # which engines/data this rule needs (documentation, not enforced here)


@dataclass(frozen=True)
class PredictionEvidence:
    """The full evaluated result of one PredictionRule against one chart."""

    rule: PredictionRule
    is_matched: bool
    triggering_conditions: tuple[str, ...]  # names of the conditions that were checked
    reasons: tuple[PredictionReason, ...]  # the atomic evidence list backing is_matched
    confidence: PredictionConfidence
    explanation: str  # plain-language summary, generated from `reasons` — never free-floating prose

    def __post_init__(self) -> None:
        if len(self.reasons) != self.confidence.total_conditions:
            raise ValueError(
                f"reasons has {len(self.reasons)} entries but confidence.total_conditions "
                f"is {self.confidence.total_conditions} — every checked condition must have "
                f"a corresponding PredictionReason."
            )
