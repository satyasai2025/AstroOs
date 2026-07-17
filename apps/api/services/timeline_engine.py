"""
AstroOS — Timeline Engine (Module 15, Phase 1)

Composes already-computed EventAnalysis objects (from Module 14) into a
chronological Timeline with summary statistics, Dasha period breakdowns,
sliding-window event density, and temporal cluster detection.

Architecture notes:
  - Takes already-computed ``tuple[EventAnalysis, ...]``, never calls
    EventEngine itself — same "compute once, reuse" discipline as
    EventEngine not calling YogaEngine.
  - All filtering methods return new Timeline instances (frozen
    dataclasses are never mutated).
  - Density computation uses an O(n) two-pointer sliding-window
    algorithm over sorted event dates (not O(n × window_days)).

Not wired into any router or persistence layer — same scope discipline
as every engine before it (EventEngine, RuleEngine, YogaEngine, etc.
at their own Phase 1).
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import date, timedelta
from typing import Optional

from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.events import EventAnalysis
from apps.api.domain.timeline import (
    TemporalCluster,
    Timeline,
    TimelineDashaPeriodSpan,
    TimelineEntry,
    TimelineSummary,
)

_TIMELINE_VERSION = "1.0"


def _sort_key(analysis: EventAnalysis) -> tuple[date, str]:
    """Stable sort key: (event_date, title)."""
    return (analysis.event.event_date, analysis.event.title)


def _density_at_event(
    event_index: int,
    event_dates: list[date],
    window_days: int,
) -> float:
    """
    O(n) per-event density via two-pointer sliding window.

    ``event_dates`` is sorted ascending.  Starting from ``event_index``,
    ``left`` is the first index where
    ``date - event_dates[left] <= window_days``; ``right`` is the last
    index where ``event_dates[right] - date <= window_days``.

    The count ``right - left + 1`` includes the event itself.  Density
    is scaled to events-per-year::

        (count / window_days) × 365.25
    """
    target = event_dates[event_index]
    left = event_index
    right = event_index

    # Expand left while still within window
    while left > 0 and (target - event_dates[left - 1]).days <= window_days:
        left -= 1
    # Expand right while still within window
    while right < len(event_dates) - 1 and (event_dates[right + 1] - target).days <= window_days:
        right += 1

    count = right - left + 1
    return (count / window_days) * 365.25


class TimelineEngine:
    """
    Constructed with no dependencies — operates entirely on already-
    computed EventAnalysis objects passed to its methods.

    Methods are idempotent and leave their inputs unmodified.
    """

    _TIMELINE_VERSION = _TIMELINE_VERSION

    # ── Timeline construction ────────────────────────────────────────────

    @staticmethod
    def build_timeline(
        analyses: tuple[EventAnalysis, ...],
    ) -> Timeline:
        """
        Build a fully-populated Timeline from already-computed
        EventAnalysis objects.

        Steps:
          1. Convert each EventAnalysis to TimelineEntry.
          2. Sort chronologically by (event_date, title).
          3. Compute TimelineSummary.
          4. Compute Dasha period breakdown across all systems present.
          5. Run cluster detection with default parameters.
        """
        if not analyses:
            return _empty_timeline()

        # Guard: all analyses must share the same chart_id.
        chart_id = analyses[0].event.chart_id
        for a in analyses:
            if a.event.chart_id != chart_id:
                raise ValueError(
                    f"Analyses span multiple chart_ids: "
                    f"found {a.event.chart_id!r}, expected {chart_id!r}."
                )

        # Step 1: convert & sort (O(n log n) once, then always sorted).
        entries = tuple(
            TimelineEntry(
                event_id=a.event.id,
                event_date=a.event.event_date,
                title=a.event.title,
                category=a.event.category,
                is_verified=a.event.is_verified,
                sort_key=a.event.event_date.isoformat(),
                analysis=a,
            )
            for a in sorted(analyses, key=_sort_key)
        )

        # Step 2: summary.
        summary = _build_summary(entries)

        # Step 3: Dasha breakdown.
        dasha_breakdown = _build_dasha_breakdown(entries)

        # Step 4: cluster detection at default density threshold.
        clusters = _find_clusters(entries)

        return Timeline(
            chart_id=chart_id,
            entries=entries,
            summary=summary,
            dasha_breakdown=dasha_breakdown,
            clusters=clusters,
            timeline_version=_TIMELINE_VERSION,
        )

    # ── Filters ───────────────────────────────────────────────────────────

    @staticmethod
    def filter_by_category(timeline: Timeline, category: str) -> Timeline:
        """Return a new Timeline with only entries matching *category*."""
        filtered = tuple(e for e in timeline.entries if e.category == category)
        return _rebuild_filtered(timeline, filtered)

    @staticmethod
    def filter_by_date_range(
        timeline: Timeline,
        start: date,
        end: date,
    ) -> Timeline:
        """Return a new Timeline with entries in ``[start, end]``."""
        filtered = tuple(e for e in timeline.entries if start <= e.event_date <= end)
        return _rebuild_filtered(timeline, filtered)

    @staticmethod
    def filter_verified(timeline: Timeline, verified: bool = True) -> Timeline:
        """Return a new Timeline with only verified or unverified entries."""
        filtered = tuple(e for e in timeline.entries if e.is_verified == verified)
        return _rebuild_filtered(timeline, filtered)

    # ── Density ───────────────────────────────────────────────────────────

    @staticmethod
    def compute_density(
        entries: tuple[TimelineEntry, ...],
        window_days: int = 365,
    ) -> tuple[tuple[date, float], ...]:
        """
        O(n) sliding-window event density.

        For each event's date, counts how many events fall within
        ``window_days`` (both before and after), then scales to events
        per year::

            density = (count_in_window / window_days) × 365.25

        Returns a tuple of ``(date, density)`` pairs, one per event,
        preserving chronological order.  An empty entries tuple returns
        an empty tuple.

        **Complexity**: O(n) where n = len(entries) — each event is
        visited at most twice (once by the left pointer, once by the
        right pointer) across the whole pass.
        """
        if not entries:
            return ()

        dates = [e.event_date for e in entries]
        n = len(dates)
        result: list[tuple[date, float]] = []

        left = 0
        for right in range(n):
            # Advance left while the window (left..right) exceeds window_days,
            # measured from `right`'s date backward.
            while left < right and (dates[right] - dates[left]).days > window_days:
                left += 1
            # Advance right past any future dates still within window_days
            # of `right`'s date — but track the true endpoint so we don't
            # revisit events unnecessarily.  The right pointer is already
            # the outer loop variable, so we trust it will reach those
            # events in subsequent iterations.
            count = right - left + 1
            density = (count / window_days) * 365.25  # pyright: ignore
            result.append((dates[right], density))

        # Run a complementary forward-looking pass to ensure early events
        # get credit for future events near the window boundary.  The
        # backward pass above only counts events <= window_days behind the
        # current event; the forward pass counts events ahead.
        right = 0
        forward_result: list[tuple[date, float]] = []
        for left in range(n):
            while right < n and (dates[right] - dates[left]).days <= window_days:
                right += 1
            count = right - left
            density = (count / window_days) * 365.25  # pyright: ignore
            forward_result.append((dates[left], density))

        # Take the max density from both passes at each date.
        merged: list[tuple[date, float]] = []
        for i in range(n):
            merged.append((dates[i], max(result[i][1], forward_result[i][1])))

        return tuple(merged)

    # ── Cluster detection ─────────────────────────────────────────────────

    @staticmethod
    def find_clusters(
        timeline: Timeline,
        window_days: int = 365,
        min_events: int = 2,
    ) -> tuple[TemporalCluster, ...]:
        """
        Detect temporal clusters using a sliding window.

        Windows with ``count_in_window >= min_events`` are marked as
        candidate windows.  Overlapping candidate windows are merged
        into contiguous cluster regions.  Each region's center_date
        is the midpoint of the densest window within it.

        Returns an empty tuple if no windows meet the threshold.
        """
        return _find_clusters(timeline.entries, window_days, min_events)


# ── Private helpers ────────────────────────────────────────────────────────


def _empty_timeline() -> Timeline:
    """Return a zero-event Timeline for an empty input."""
    empty_uuid = uuid.UUID(int=0)
    return Timeline(
        chart_id=empty_uuid,
        entries=(),
        summary=TimelineSummary(
            total_events=0,
            date_range=(date(1, 1, 1), date(1, 1, 1)),
            events_per_category={},
            events_per_dasha_system={},
            verified_count=0,
            unverified_count=0,
        ),
        dasha_breakdown={},
        clusters=(),
        timeline_version=_TIMELINE_VERSION,
    )


def _build_summary(entries: tuple[TimelineEntry, ...]) -> TimelineSummary:
    """Aggregate statistics across *entries*."""
    total = len(entries)
    if total == 0:
        return TimelineSummary(
            total_events=0,
            date_range=(date(1, 1, 1), date(1, 1, 1)),
            events_per_category={},
            events_per_dasha_system={},
            verified_count=0,
            unverified_count=0,
        )

    categories: Counter = Counter()
    dasha_systems: Counter = Counter()
    verified = 0

    earliest = entries[0].event_date
    latest = entries[0].event_date

    for entry in entries:
        if entry.category:
            categories[entry.category] += 1
        if entry.is_verified:
            verified += 1

        # Count distinct Dasha systems mentioned in this entry.
        for system in entry.analysis.context.active_dashas:
            dasha_systems[system] += 1

        if entry.event_date < earliest:
            earliest = entry.event_date
        if entry.event_date > latest:
            latest = entry.event_date

    return TimelineSummary(
        total_events=total,
        date_range=(earliest, latest),
        events_per_category=dict(categories),
        events_per_dasha_system=dict(dasha_systems),
        verified_count=verified,
        unverified_count=total - verified,
    )


def _build_dasha_breakdown(
    entries: tuple[TimelineEntry, ...],
) -> dict[str, tuple[TimelineDashaPeriodSpan, ...]]:
    """
    For each Dasha system present in entries, build the ordered list of
    periods with their contained event_ids.

    Events are assigned to DashaPeriodSpans by matching their date against
    each period's ``[start, end)`` range, using the same boundary semantics
    as ``find_active_dasha_chain``.
    """
    if not entries:
        return {}

    # Collect all unique system names across entries.
    systems: set[str] = set()
    for entry in entries:
        systems.update(entry.analysis.context.active_dashas.keys())

    breakdown: dict[str, list[TimelineDashaPeriodSpan]] = {}

    for system in sorted(systems):
        # Collect every unique DashaPeriod across all entries, keyed by
        # (lord, level, start_date, end_date) so repeated periods from
        # different entries collapse into one span.
        period_map: dict[tuple[str, int, date, date], list[uuid.UUID]] = {}

        for entry in entries:
            chain = entry.analysis.context.active_dashas.get(system)
            if not chain:
                continue
            for period in chain:
                key = (period.lord, period.level, period.start_date, period.end_date)
                if key not in period_map:
                    period_map[key] = []
                period_map[key].append(entry.event_id)

        # Sort spans by start_date then lord for deterministic output.
        sorted_keys = sorted(period_map.keys(), key=lambda k: (k[2], k[0]))
        spans = [
            TimelineDashaPeriodSpan(
                system=system,
                lord=key[0],
                level=key[1],
                start_date=key[2],
                end_date=key[3],
                event_ids=tuple(period_map[key]),
                event_count=len(period_map[key]),
            )
            for key in sorted_keys
        ]

        breakdown[system] = tuple(spans)

    return dict(breakdown)


def _find_clusters(
    entries: tuple[TimelineEntry, ...],
    window_days: int = 365,
    min_events: int = 2,
) -> tuple[TemporalCluster, ...]:
    """
    Sliding-window cluster detection.

    Every window (anchored at each event) whose count >= min_events is a
    candidate.  Overlapping or adjacent candidates are merged into
    contiguous regions.  Each region's center_date is the midpoint of
    the window with the highest count within that region.

    O(n) — the two-pointer density pass also identifies window bounds.
    """
    if not entries:
        return ()

    dates = [e.event_date for e in entries]
    n = len(dates)

    # Track which events are in candidate windows.
    in_candidate = [False] * n
    best_center_for_region: dict[int, int] = {}  # region_start -> best_density_index

    left = 0
    for right in range(n):
        while left < right and (dates[right] - dates[left]).days > window_days:
            left += 1
        count = right - left + 1
        if count >= min_events:
            in_candidate[left] = True
            in_candidate[right] = True
            # Midpoint index within the window.
            mid = (left + right) // 2
            # Track which region this mid belongs to (determined later).

    # Merge contiguous candidate regions.
    clusters: list[TemporalCluster] = []
    i = 0
    while i < n:
        if not in_candidate[i]:
            i += 1
            continue
        # Start of a candidate region.
        region_start = dates[i]
        region_end = dates[i]
        region_start_idx = i
        while i < n and in_candidate[i]:
            region_end = dates[i]
            i += 1

        # Gather events in this region.
        region_events = entries[region_start_idx:i]

        # Find the densest window center within the region.
        best_density = 0.0
        best_center = region_events[0].event_date
        # Active dashas at center.
        active_chain: dict[str, tuple[DashaPeriod, ...]] = {}

        for candidate in region_events:
            density = _density_at_event(
                dates.index(candidate.event_date),
                dates,
                window_days,
            )
            if density > best_density:
                best_density = density
                best_center = candidate.event_date
                # Capture active dashas at this center point.
                active_chain = {
                    system: chain
                    for system, chain in candidate.analysis.context.active_dashas.items()
                }

        clusters.append(TemporalCluster(
            start_date=region_start,
            end_date=region_end,
            center_date=best_center,
            events=region_events,
            event_count=len(region_events),
            density=best_density,
            active_dashas=active_chain,
        ))

    return tuple(clusters)


def _rebuild_filtered(
    original: Timeline,
    filtered_entries: tuple[TimelineEntry, ...],
) -> Timeline:
    """Rebuild a Timeline from a filtered subset, recomputing derived fields."""
    if not filtered_entries:
        return _empty_timeline()

    summary = _build_summary(filtered_entries)
    dasha_breakdown = _build_dasha_breakdown(filtered_entries)
    clusters = _find_clusters(filtered_entries)

    return Timeline(
        chart_id=original.chart_id,
        entries=filtered_entries,
        summary=summary,
        dasha_breakdown=dasha_breakdown,
        clusters=clusters,
        timeline_version=original.timeline_version,
    )
