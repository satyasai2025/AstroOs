"""
AstroOS — Retrodiction validation

Scores computed sensitive windows against life events a native actually
reported. This is the research half of the sensitive-timing work: the
reading surface tells someone what the indicators say, and this tells
*us* whether the indicators have been worth listening to.

Three methodological points are built into the output rather than left
to whoever reads it, because each one is a place this kind of analysis
usually goes wrong:

1. **Coverage is the denominator that matters.** If the windows cover
   half of a native's life, then "we caught 3 of their 4 events" is
   close to what tossing a coin would do. :attr:`ValidationMetrics.lift`
   divides recall by coverage; a lift near 1.0 means the technique is
   indistinguishable from marking dates at random, however good the raw
   recall looks. This is reported first-class, not as a footnote.
2. **Precision is usually not computable.** A window with no disclosed
   event in it is not a false positive — the native may simply not have
   mentioned anything. Precision is therefore only computed when the
   caller explicitly asserts the event list is exhaustive for the period
   scanned, and is ``None`` otherwise rather than being silently
   approximated.
3. **Misses are reported alongside hits.** :attr:`missed_events` is part
   of the result, so a summary cannot show only what worked.

Nothing here is a reading. It never runs for a live interpretation
path; it consumes windows that have already been computed and returns
numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from apps.api.services.sensitive_timeline_service import SensitiveTimeline, SensitiveWindow
from packages.shared.disclosed_events import DisclosedEvent, EventValence, LifeDomain
from packages.shared.sensitive_convergence import ConvergenceGrade, Polarity, Technique
from packages.shared.temporal_stance import SubjectStatus, TemporalDirection


@dataclass(frozen=True)
class EventOutcome:
    """How one disclosed event fared against the computed windows."""

    event: DisclosedEvent
    #: A window overlapped it *and* flagged its life domain.
    is_hit: bool
    #: A window overlapped it but flagged different domains — a partial result,
    #: kept distinct from a clean hit rather than rounded up to one.
    overlapped_wrong_domain: bool
    #: Right period and right life area, but the window read as difficulty
    #: while the event was supportive (or vice versa). Not a hit, not a miss.
    polarity_mismatch: bool = False
    matched_window_start: Optional[datetime] = None
    matched_grade: Optional[ConvergenceGrade] = None
    techniques_present: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TechniqueScore:
    """How often a technique was present when an event was correctly caught."""

    technique: str
    hits_contributed: int
    total_hits: int

    @property
    def share(self) -> Optional[float]:
        if self.total_hits == 0:
            return None
        return self.hits_contributed / self.total_hits


@dataclass(frozen=True)
class ValidationMetrics:
    """Scores for one native's timeline against their disclosed events."""

    total_events: int
    hits: int
    misses: int
    overlapped_wrong_domain: int
    polarity_mismatch: int

    #: Fraction of the scanned span covered by reported windows, 0-1.
    coverage: float
    #: hits / total_events. None when nothing was disclosed.
    recall: Optional[float]
    #: recall / coverage. 1.0 means no better than marking dates at random.
    lift: Optional[float]
    #: Only computable when the caller asserts the event list is exhaustive.
    precision: Optional[float]
    precision_note: str

    windows_examined: int
    windows_with_a_disclosed_event: int

    @property
    def is_better_than_chance(self) -> Optional[bool]:
        """Whether lift clears 1.0. None when there is nothing to judge on."""
        if self.lift is None:
            return None
        return self.lift > 1.0


@dataclass
class ValidationReport:
    janma_nakshatra: str
    scanned_start_utc: datetime
    scanned_end_utc: datetime
    metrics: ValidationMetrics
    outcomes: list[EventOutcome]
    technique_scores: list[TechniqueScore]
    unchecked_techniques: list[str]
    #: Events no window explained — surfaced, never dropped.
    missed_events: list[DisclosedEvent] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)


class RetrodictionValidationEngine:
    """Scores an already-computed timeline. Does no astrology of its own."""

    def validate(
        self,
        timeline: SensitiveTimeline,
        events: Optional[Iterable[DisclosedEvent]] = None,
        events_are_exhaustive: bool = False,
    ) -> ValidationReport:
        """Score ``timeline``'s past windows against ``events``.

        Only past and present windows are scored — a future alert has no
        outcome yet, and including it would inflate coverage while
        contributing no possible hit.
        """
        disclosed = list(events if events is not None else _events_from(timeline))
        windows = [
            w
            for w in timeline.all_windows
            if w.temporal_direction is not TemporalDirection.FUTURE
        ]

        outcomes = [self._score_event(event, windows) for event in disclosed]
        hits = [o for o in outcomes if o.is_hit]
        wrong_domain = [o for o in outcomes if o.overlapped_wrong_domain]
        wrong_polarity = [o for o in outcomes if o.polarity_mismatch]
        missed = [
            o.event
            for o in outcomes
            if not o.is_hit and not o.overlapped_wrong_domain and not o.polarity_mismatch
        ]

        # Denominator is the *elapsed* span, not the whole scanned range: only
        # past and present windows are being scored, so measuring them against
        # a range that runs into the future would understate coverage and
        # inflate lift in exactly the flattering direction.
        coverage = _coverage(windows, timeline.elapsed_span_days())
        recall = (len(hits) / len(disclosed)) if disclosed else None
        lift = (recall / coverage) if (recall is not None and coverage > 0) else None

        windows_with_event = sum(
            1 for w in windows if any(m.is_confirmation for m in w.event_matches)
        )
        precision: Optional[float] = None
        if events_are_exhaustive and windows:
            precision = windows_with_event / len(windows)
            precision_note = (
                "Computed: the caller asserted the disclosed-event list is exhaustive "
                "for the scanned period."
            )
        else:
            precision_note = (
                "Not computed. A window with no disclosed event in it is not a false "
                "positive — the native may simply not have mentioned anything. Pass "
                "events_are_exhaustive=True only if the event list genuinely covers the "
                "whole scanned period."
            )

        return ValidationReport(
            janma_nakshatra=timeline.janma_nakshatra,
            scanned_start_utc=timeline.start_utc,
            scanned_end_utc=timeline.end_utc,
            metrics=ValidationMetrics(
                total_events=len(disclosed),
                hits=len(hits),
                misses=len(missed),
                overlapped_wrong_domain=len(wrong_domain),
                polarity_mismatch=len(wrong_polarity),
                coverage=coverage,
                recall=recall,
                lift=lift,
                precision=precision,
                precision_note=precision_note,
                windows_examined=len(windows),
                windows_with_a_disclosed_event=windows_with_event,
            ),
            outcomes=outcomes,
            technique_scores=_technique_scores(hits),
            unchecked_techniques=list(timeline.unchecked_techniques),
            missed_events=missed,
            caveats=_caveats(timeline, disclosed, coverage),
        )

    def _score_event(
        self,
        event: DisclosedEvent,
        windows: list[SensitiveWindow],
    ) -> EventOutcome:
        """Score one event, requiring time, domain *and* polarity to agree.

        Polarity matters as much as the other two: scoring a coronation
        against a malefic-affliction window is a category error, not a miss,
        and treating it as a miss is what made the first backtest
        meaningless. A mismatch gets its own bucket so it can neither be
        counted as a success nor silently inflate the miss count.
        """
        overlapping = [
            w
            for w in windows
            if w.start_utc <= event.end_utc and event.start_utc <= w.end_utc
        ]
        if not overlapping:
            return EventOutcome(event=event, is_hit=False, overlapped_wrong_domain=False)

        domain_matched = [w for w in overlapping if event.domain in w.domains_all]
        if not domain_matched:
            return EventOutcome(event=event, is_hit=False, overlapped_wrong_domain=True)

        polarity_matched = [w for w in domain_matched if _polarity_agrees(event, w)]
        if not polarity_matched:
            return EventOutcome(
                event=event,
                is_hit=False,
                overlapped_wrong_domain=False,
                polarity_mismatch=True,
            )

        best = max(polarity_matched, key=lambda w: w.grade.rank)
        return EventOutcome(
            event=event,
            is_hit=True,
            overlapped_wrong_domain=False,
            matched_window_start=best.start_utc,
            matched_grade=best.grade,
            techniques_present=tuple(sorted({i.technique.value for i in best.indicators})),
        )


def _polarity_agrees(event: DisclosedEvent, window: SensitiveWindow) -> bool:
    """Whether a window's polarity can account for an event's valence.

    A MIXED window carries both an adverse and a supportive reading, so it
    can account for either; a MIXED event is likewise satisfied by either
    window. NEUTRAL windows account for nothing — they carry no reading.
    """
    if window.polarity is Polarity.NEUTRAL:
        return False
    if window.polarity is Polarity.MIXED or event.valence is EventValence.MIXED:
        return True
    if event.valence is EventValence.DIFFICULT:
        return window.polarity is Polarity.ADVERSE
    return window.polarity is Polarity.SUPPORTIVE


def _events_from(timeline: SensitiveTimeline) -> list[DisclosedEvent]:
    """Recover the events a timeline was built with, hits and misses alike."""
    seen: dict[str, DisclosedEvent] = {
        e.event_id: e for e in timeline.unexplained_events
    }
    for window in timeline.all_windows:
        for match in window.event_matches:
            seen.setdefault(match.event.event_id, match.event)
    return list(seen.values())


def _coverage(windows: list[SensitiveWindow], span_days: float) -> float:
    """Fraction of the scanned span sitting inside a reported window.

    Overlapping windows are merged before measuring, so a doubled-up period
    cannot push coverage above 1.0 and quietly deflate lift.
    """
    if span_days <= 0 or not windows:
        return 0.0

    intervals = sorted((w.start_utc, w.end_utc) for w in windows)
    merged: list[list[datetime]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    covered = sum((end - start).total_seconds() / 86400.0 for start, end in merged)
    return min(1.0, covered / span_days)


def _technique_scores(hits: list[EventOutcome]) -> list[TechniqueScore]:
    total = len(hits)
    counts: dict[str, int] = {t.value: 0 for t in Technique}
    for outcome in hits:
        for technique in outcome.techniques_present:
            counts[technique] = counts.get(technique, 0) + 1
    return sorted(
        (TechniqueScore(technique=name, hits_contributed=count, total_hits=total)
         for name, count in counts.items()),
        key=lambda s: s.hits_contributed,
        reverse=True,
    )


def _caveats(
    timeline: SensitiveTimeline,
    disclosed: list[DisclosedEvent],
    coverage: float,
) -> list[str]:
    """Conditions that make these numbers weaker than they look."""
    notes: list[str] = []

    if len(disclosed) < 5:
        notes.append(
            f"Only {len(disclosed)} disclosed event(s). Far too few to establish a "
            "hit-rate for any technique; treat this as a single case, not evidence."
        )
    if coverage > 0.5:
        notes.append(
            f"Windows cover {coverage:.0%} of the scanned period. At that density a "
            "high recall is close to what marking dates at random would produce — "
            "read the lift, not the recall."
        )
    if timeline.step_days > 1:
        notes.append(
            f"Sampled every {timeline.step_days} days, so a window that opened and "
            "closed inside one step was not seen at all."
        )
    if timeline.unchecked_techniques:
        notes.append(
            "Not every technique in the source material was computed: "
            f"{', '.join(timeline.unchecked_techniques)} was not run."
        )
    return notes
