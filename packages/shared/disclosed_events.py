"""
AstroOS — Disclosed life events

A ``DisclosedEvent`` is something the native told us happened, with a
date or date range attached. It is deliberately the *only* kind of
concrete event this codebase treats as known: everything else a
sensitive-timing engine produces is an inferred window, and the
distinction is what :mod:`packages.shared.temporal_stance` keys its
output policy on.

Two things follow from having these as structured data rather than
free text:

1. **Retrodiction calibration.** When an SBC/Tara scan flags a past
   window that overlaps a disclosed event in a matching life domain,
   the reading may name the event directly instead of hedging around
   it — the native is not being told anything they did not supply.
2. **Ground truth for validation.** Disclosed events give the
   benchmark and cohort-validation machinery real outcomes to score
   technique hit-rates against, rather than only measuring whether the
   computation matches another piece of software.

Pure module: no ephemeris, no persistence. Storage is the caller's
concern; :class:`DisclosedEvent` is what gets stored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable, Optional


class LifeDomain(str, Enum):
    """Coarse life areas — the granularity at which inferred windows may speak.

    Values added in the Workstream-4 pass (2026-08-27):
    - POWER: Political power, governance events (elections, inaugurations, etc.)
    - TRANSFORMATION: Major life upheavals, crises, sudden reversals of fortune.
    - ACHIEVEMENT: Accomplishments, recognitions, completions.

    These extend the original 11 values to cover the Wikidot case-study corpus
    disclosed event taxonomy without remapping existing data.
    """

    HEALTH = "health"
    MENTAL_WELLBEING = "mental_wellbeing"
    FAMILY = "family"
    RELATIONSHIP = "relationship"
    CAREER = "career"
    FINANCE = "finance"
    EDUCATION = "education"
    RELOCATION = "relocation"
    LEGAL = "legal"
    SPIRITUAL = "spiritual"
    POWER = "power"
    TRANSFORMATION = "transformation"
    ACHIEVEMENT = "achievement"
    OTHER = "other"


#: Which life domains each of the 10 classical Sangyas speaks to. Derived from
#: the domain strings in ``sbc_vedha_engine.SANGYA_LIFE_AREAS``; kept here as an
#: explicit mapping so that domain-matching does not depend on parsing prose.
#:
#: Extensions (2026-08-27):
#: - "karma" now includes EDUCATION (study/knowledge acquisition is karma-linked
#:   in the BPHS scheme; the 5th and 9th houses are Karma/Dharma houses).
#: - "adhana" now includes LEGAL (6th-house litigation/conflict domain maps to
#:   adhana Sangya's adversarial quality per SBC tradition).
#: - "abhisheka" now includes POWER (consecration/coronation Sangya directly
#:   speaks to authority and political power events).
#: - "karma" now includes ACHIEVEMENT (career accomplishment is karma-domain).
#: - "sanghatika" now includes TRANSFORMATION (collective upheavals, crises).
SANGYA_DOMAINS: dict[str, frozenset[LifeDomain]] = {
    "janma": frozenset({LifeDomain.HEALTH, LifeDomain.MENTAL_WELLBEING}),
    "karma": frozenset({LifeDomain.CAREER, LifeDomain.EDUCATION, LifeDomain.ACHIEVEMENT}),
    "sanghatika": frozenset({
        LifeDomain.FINANCE, LifeDomain.RELATIONSHIP,
        LifeDomain.MENTAL_WELLBEING, LifeDomain.TRANSFORMATION,
    }),
    "samudayika": frozenset({LifeDomain.FINANCE}),
    "adhana": frozenset({
        LifeDomain.CAREER, LifeDomain.RELOCATION,
        LifeDomain.FAMILY, LifeDomain.LEGAL,
    }),
    "vainashika": frozenset({LifeDomain.FINANCE}),
    "manasa": frozenset({LifeDomain.MENTAL_WELLBEING}),
    "jati": frozenset({LifeDomain.FAMILY, LifeDomain.HEALTH}),
    "desha": frozenset({LifeDomain.RELOCATION, LifeDomain.OTHER}),
    "abhisheka": frozenset({LifeDomain.CAREER, LifeDomain.SPIRITUAL, LifeDomain.POWER}),
}


class EventValence(str, Enum):
    """Whether the native experienced the event as difficult or supportive."""

    DIFFICULT = "difficult"
    SUPPORTIVE = "supportive"
    MIXED = "mixed"


@dataclass(frozen=True)
class DisclosedEvent:
    """A life event the native reported, with the precision they reported it at.

    ``occurred_end_utc`` is optional: a native who says "sometime in 2003"
    supplies a year-long range, one who names a date supplies a point. Both
    are usable; conflating them would overstate how tightly a technique
    matched, so the range is preserved as given.
    """

    event_id: str
    domain: LifeDomain
    occurred_start_utc: datetime
    description: str = ""
    occurred_end_utc: Optional[datetime] = None
    valence: EventValence = EventValence.DIFFICULT
    #: Native's own sense of magnitude, 1 (minor) to 5 (life-altering).
    significance: int = 3
    #: Free-form provenance, e.g. "intake form", "chat 2026-08-27".
    recorded_via: str = "user"

    def __post_init__(self) -> None:
        if not 1 <= self.significance <= 5:
            raise ValueError("significance must be between 1 and 5")
        if self.occurred_end_utc is not None and self.occurred_end_utc < self.occurred_start_utc:
            raise ValueError("occurred_end_utc must not precede occurred_start_utc")

    @property
    def start_utc(self) -> datetime:
        return _as_utc(self.occurred_start_utc)

    @property
    def end_utc(self) -> datetime:
        return _as_utc(self.occurred_end_utc or self.occurred_start_utc)

    @property
    def span_days(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds() / 86400.0

    @property
    def is_point_in_time(self) -> bool:
        return self.occurred_end_utc is None or self.span_days < 1.0

    def covers(self, moment_utc: datetime, tolerance_days: float = 0.0) -> bool:
        slack = timedelta(days=tolerance_days)
        return self.start_utc - slack <= _as_utc(moment_utc) <= self.end_utc + slack


@dataclass(frozen=True)
class EventMatch:
    """A disclosed event that lines up with a flagged window."""

    event: DisclosedEvent
    #: Days of overlap between the event's span and the flagged window.
    overlap_days: float
    #: True when the flagged Sangyas speak to the event's own life domain.
    domain_matches: bool
    matched_sangyas: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_confirmation(self) -> bool:
        """A match strong enough to let a reading name the event directly."""
        return self.overlap_days > 0 and self.domain_matches


def domains_for_sangyas(sangya_keys: Iterable[str]) -> frozenset[LifeDomain]:
    """Union of the life domains the given Sangyas speak to."""
    domains: set[LifeDomain] = set()
    for key in sangya_keys:
        domains |= SANGYA_DOMAINS.get(key.strip().lower(), frozenset())
    return frozenset(domains)


def match_events(
    events: Iterable[DisclosedEvent],
    window_start_utc: datetime,
    window_end_utc: datetime,
    sangya_keys: Iterable[str] = (),
    tolerance_days: float = 0.0,
) -> list[EventMatch]:
    """Find disclosed events overlapping a flagged window.

    ``sangya_keys`` are the afflicted/activated Sangyas that produced the
    window; supplying them lets the match distinguish "this window overlaps
    an event" from the much stronger "this window overlaps an event *in the
    life domain the window actually points at*". Matches are returned
    strongest-first so a caller taking only the top one gets the best.
    """
    window_start = _as_utc(window_start_utc) - timedelta(days=tolerance_days)
    window_end = _as_utc(window_end_utc) + timedelta(days=tolerance_days)
    if window_end < window_start:
        raise ValueError("window_end_utc must not precede window_start_utc")

    keys = tuple(k.strip().lower() for k in sangya_keys)
    matches: list[EventMatch] = []

    for event in events:
        overlap_start = max(event.start_utc, window_start)
        overlap_end = min(event.end_utc, window_end)
        if overlap_end < overlap_start:
            continue

        # A point-in-time event inside the window has zero span but is a real
        # hit; report it as a full day rather than as no overlap at all.
        overlap_days = (overlap_end - overlap_start).total_seconds() / 86400.0
        if overlap_days == 0.0:
            overlap_days = 1.0

        matched = tuple(k for k in keys if event.domain in SANGYA_DOMAINS.get(k, frozenset()))
        matches.append(
            EventMatch(
                event=event,
                overlap_days=overlap_days,
                domain_matches=bool(matched) if keys else False,
                matched_sangyas=matched,
            )
        )

    matches.sort(key=lambda m: (m.domain_matches, m.event.significance, m.overlap_days), reverse=True)
    return matches


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
