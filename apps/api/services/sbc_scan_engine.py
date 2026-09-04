"""
AstroOS — Sarvatobhadra Chakra (SBC) Date-Range Scanner

A single SBCReport is a snapshot at one instant — most instants show no
active Vedha, since a hit needs a specific benefic planet in a specific
nakshatra casting in a specific direction that happens to land on the
selected Janma element. Locating a "sensitive period" (per the
sensitive-timing skill's convergence framework) requires scanning
forward across a date range and reporting every day a hit actually
occurs, not just checking "right now" — that's what this module adds
on top of sbc_report_service.py.

**Granularity caveat.** Daily sampling (one check per day, noon UTC by
default) can miss a hit that both starts and clears within the same
day — the Moon alone can cross an entire nakshatra in under a day at
perigee. This is a real, stated limitation, not silently glossed over:
callers wanting exact entry/exit times need a finer step or a proper
forward/backward boundary search, neither of which this module does
yet (same class of limitation VedhaAnalysisPanel.tsx already documents
for Rashi Vedha).

**Temporal stance.** Every hit is annotated with whether it falls in
the past, present or future relative to the moment the scan runs, and
with the :class:`~packages.shared.temporal_stance.StancePolicy` that
follows. A past window is a retrodiction the native can check against
their own life; a future one is a forecast. Deciding that here — once,
against real dates — keeps presentation layers from re-deriving it and
getting it wrong. Passing ``disclosed_events`` additionally lets a past
window that overlaps a known event be reported in the native's own
terms rather than hedged to the life-domain level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable, Optional

from apps.api.services.sbc_report_service import SBCReport, SBCReportService
from packages.shared.disclosed_events import DisclosedEvent, EventMatch, match_events
from packages.shared.temporal_stance import (
    DEFAULT_PRESENT_WINDOW_DAYS,
    EventSource,
    StancePolicy,
    SubjectStatus,
    TemporalDirection,
    classify_direction,
    resolve_policy,
)


class SeverityTier(str, Enum):
    """How much converges at a sampled moment.

    Convergence — several independent indicators landing on the same
    point — is what gives a sensitive-timing call its weight; a single
    hit is not the same claim as four, and reporting both as "a hit"
    would round a thin case up to a strong one. This tier is a plain
    count-based label over the afflicted Sangyas, not a classical
    citation, so it carries the same caveat as any other convenience
    banding in this area.
    """

    NONE = "none"
    SINGLE = "single"
    CONVERGING = "converging"
    STRONG_CONVERGENCE = "strong_convergence"


#: Affliction of the Janma Sangya itself is read as more severe than
#: affliction of any other point (see the career workflow's note that damage
#: to Karma is *less* severe than damage to Janma), so its presence promotes
#: the tier by one step.
_JANMA_KEY = "janma"


def severity_tier(afflicted_keys: Iterable[str]) -> SeverityTier:
    """Grade a moment by how many Sangyas are simultaneously afflicted."""
    keys = {k.strip().lower() for k in afflicted_keys if k}
    if not keys:
        return SeverityTier.NONE

    score = len(keys) + (1 if _JANMA_KEY in keys else 0)
    if score >= 4:
        return SeverityTier.STRONG_CONVERGENCE
    if score >= 2:
        return SeverityTier.CONVERGING
    return SeverityTier.SINGLE


@dataclass
class SBCScanHit:
    moment_utc: datetime
    report: SBCReport
    #: Past / present / future relative to the moment the scan was run.
    temporal_direction: TemporalDirection = TemporalDirection.PRESENT
    #: What may be said about this hit, given its direction and subject.
    policy: Optional[StancePolicy] = None
    tier: SeverityTier = SeverityTier.NONE
    afflicted_sangyas: tuple[str, ...] = field(default_factory=tuple)
    activated_sangyas: tuple[str, ...] = field(default_factory=tuple)
    #: Disclosed events overlapping this moment, strongest match first.
    event_matches: list[EventMatch] = field(default_factory=list)

    @property
    def is_confirmed_by_disclosure(self) -> bool:
        """True when a disclosed event in a matching life domain overlaps this hit."""
        return any(m.is_confirmation for m in self.event_matches)


@dataclass
class SBCScanWindow:
    """Consecutive hits collapsed into one contiguous period.

    A scan over years produces hundreds of individual daily hits; a native
    asking about their life needs "this stretch of 1998–2000", not a list of
    dates. The window carries the strongest tier seen inside it, since that
    is what any summary of the period should be graded on.
    """

    start_utc: datetime
    end_utc: datetime
    hits: list[SBCScanHit]
    temporal_direction: TemporalDirection
    tier: SeverityTier
    policy: StancePolicy
    afflicted_sangyas: tuple[str, ...]
    event_matches: list[EventMatch] = field(default_factory=list)

    @property
    def duration_days(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds() / 86400.0

    @property
    def is_confirmed_by_disclosure(self) -> bool:
        return any(m.is_confirmation for m in self.event_matches)


_TIER_ORDER = {
    SeverityTier.NONE: 0,
    SeverityTier.SINGLE: 1,
    SeverityTier.CONVERGING: 2,
    SeverityTier.STRONG_CONVERGENCE: 3,
}


class SBCScanEngine:
    def __init__(self, report_service: SBCReportService) -> None:
        self._report_service = report_service

    def scan(
        self,
        janma_nakshatra: str,
        start_utc: datetime,
        end_utc: datetime,
        step_days: int = 1,
        sample_hour_utc: int = 12,
        now_utc: Optional[datetime] = None,
        disclosed_events: Optional[Iterable[DisclosedEvent]] = None,
        subject_status: SubjectStatus = SubjectStatus.LIVING,
        present_window_days: int = DEFAULT_PRESENT_WINDOW_DAYS,
    ) -> list[SBCScanHit]:
        """Sample the range and return every moment carrying a Vedha hit.

        Each hit is annotated with its temporal direction and the output
        policy that follows from it, so that downstream presentation never
        has to re-derive whether a window is a retrodiction or a forecast.
        Passing ``disclosed_events`` additionally lets a past window that
        overlaps a known event be reported in the native's own terms rather
        than hedged (see :mod:`packages.shared.temporal_stance`).
        """
        if step_days < 1:
            raise ValueError("step_days must be >= 1")
        if end_utc <= start_utc:
            raise ValueError("end_utc must be after start_utc")

        reference = now_utc or datetime.now(timezone.utc)
        events = list(disclosed_events or ())

        hits: list[SBCScanHit] = []
        cursor = start_utc.replace(hour=sample_hour_utc, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        step = timedelta(days=step_days)

        while cursor <= end_utc:
            report = self._report_service.build_report(cursor, janma_nakshatra=janma_nakshatra)
            if report.vedha_result is not None and report.vedha_result.hits:
                hits.append(
                    self._annotate(
                        cursor,
                        report,
                        reference=reference,
                        events=events,
                        subject_status=subject_status,
                        present_window_days=present_window_days,
                        step_days=step_days,
                    )
                )
            cursor += step

        return hits

    def _annotate(
        self,
        moment_utc: datetime,
        report: SBCReport,
        reference: datetime,
        events: list[DisclosedEvent],
        subject_status: SubjectStatus,
        present_window_days: int,
        step_days: int,
    ) -> SBCScanHit:
        afflicted = tuple(p.key for p in report.sensitive_points if p.status == "afflicted")
        activated = tuple(p.key for p in report.sensitive_points if p.status == "activated")

        direction = classify_direction(moment_utc, reference, present_window_days)
        matches = (
            match_events(
                events,
                moment_utc,
                moment_utc,
                sangya_keys=afflicted + activated,
                # A daily sample stands in for the whole step it represents.
                tolerance_days=step_days / 2.0,
            )
            if events
            else []
        )

        # A disclosed event only unlocks the plainer voice when it actually
        # lines up with what this window points at — an overlapping career
        # event does not license naming it while the window flags health.
        source = (
            EventSource.USER_DISCLOSED
            if any(m.is_confirmation for m in matches)
            else EventSource.SYSTEM_INFERRED
        )

        return SBCScanHit(
            moment_utc=moment_utc,
            report=report,
            temporal_direction=direction,
            policy=resolve_policy(direction, source, subject_status),
            tier=severity_tier(afflicted),
            afflicted_sangyas=afflicted,
            activated_sangyas=activated,
            event_matches=matches,
        )


def group_into_windows(
    hits: list[SBCScanHit],
    max_gap_days: float = 3.0,
) -> list[SBCScanWindow]:
    """Collapse hits separated by no more than ``max_gap_days`` into windows.

    Hits must be chronologically ordered, which is what :meth:`SBCScanEngine.scan`
    returns. A window's policy is the *most restrictive* of its members' — a
    stretch that runs from the past into the present is not licensed to speak
    in past-tense certainties about its still-running tail.
    """
    if not hits:
        return []
    if max_gap_days < 0:
        raise ValueError("max_gap_days must be >= 0")

    windows: list[SBCScanWindow] = []
    bucket: list[SBCScanHit] = [hits[0]]

    for previous, current in zip(hits, hits[1:]):
        gap = (current.moment_utc - previous.moment_utc).total_seconds() / 86400.0
        if gap > max_gap_days:
            windows.append(_build_window(bucket))
            bucket = []
        bucket.append(current)

    windows.append(_build_window(bucket))
    return windows


def _build_window(bucket: list[SBCScanHit]) -> SBCScanWindow:
    peak = max(bucket, key=lambda h: _TIER_ORDER[h.tier])
    afflicted: list[str] = []
    for hit in bucket:
        for key in hit.afflicted_sangyas:
            if key not in afflicted:
                afflicted.append(key)

    matches: list[EventMatch] = []
    seen_ids: set[str] = set()
    for hit in bucket:
        for match in hit.event_matches:
            if match.event.event_id not in seen_ids:
                seen_ids.add(match.event.event_id)
                matches.append(match)
    matches.sort(key=lambda m: (m.is_confirmation, m.event.significance), reverse=True)

    directions = {h.temporal_direction for h in bucket}
    # Most restrictive wins: a mixed window is treated as still running.
    if directions == {TemporalDirection.PAST}:
        direction = TemporalDirection.PAST
    elif directions == {TemporalDirection.FUTURE}:
        direction = TemporalDirection.FUTURE
    else:
        direction = TemporalDirection.PRESENT

    source = (
        EventSource.USER_DISCLOSED
        if any(m.is_confirmation for m in matches)
        else EventSource.SYSTEM_INFERRED
    )
    subject_status = (
        bucket[0].policy.subject_status if bucket[0].policy is not None else SubjectStatus.LIVING
    )

    return SBCScanWindow(
        start_utc=bucket[0].moment_utc,
        end_utc=bucket[-1].moment_utc,
        hits=bucket,
        temporal_direction=direction,
        tier=peak.tier,
        policy=resolve_policy(direction, source, subject_status),
        afflicted_sangyas=tuple(afflicted),
        event_matches=matches,
    )
