"""
AstroOS — Sensitive timeline

Builds the two things an individual chart reading needs from the
sensitive-timing techniques at once:

* **Past windows** — periods the classical indicators converge on,
  which the native can check against their own life. A retrodiction is
  falsifiable; this is the half of the reading that can actually be
  wrong in a way anyone would notice.
* **Future alerts** — periods still ahead, reported as a heightened-risk
  *window* and a life *domain*, never as an event. Same computation,
  different voice, enforced by the policy attached to each window rather
  than by whoever writes the presentation layer.

Convergence across SBC Vedha, Latta and the yearly Tara cycle is graded
by :mod:`packages.shared.sensitive_convergence`, which counts distinct
techniques rather than raw hits. Progressed Saturn is named in the
source material but not implemented; every timeline reports it as
unchecked rather than quietly leaving it out.

**Cost and granularity.** A whole-life scan at daily resolution is
thousands of ephemeris rounds. ``step_days`` defaults to weekly, which
is appropriate for locating a *period* but will miss a hit that opens
and clears inside one step — the same class of caveat
``sbc_scan_engine`` already documents, and the reason
:attr:`SensitiveTimeline.step_days` is reported back to the caller
rather than hidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from apps.api.services.latta_engine import LATTA_PLANETS, LattaEngine
from apps.api.services.sbc_report_service import SBCReportService
from packages.shared.disclosed_events import (
    DisclosedEvent,
    EventMatch,
    LifeDomain,
    SANGYA_DOMAINS,
    match_events,
)
from packages.shared.event_signature import EventSignature, build_signature
from packages.shared.latta import VerificationStatus, check_latta
from packages.shared.sensitive_convergence import (
    ConvergenceGrade,
    Indicator,
    Polarity,
    Technique,
    all_domains,
    converging_domains,
    count_techniques,
    grade_convergence,
    meets_threshold,
    polarity_of,
    techniques_checked,
    weakest_verification,
)
from packages.shared.tarabala import (
    TARA_NAMES_9,
    UNFAVORABLE_TARA_9,
    extended_27_name,
    yearly_tara,
)
from packages.shared.temporal_stance import (
    DEFAULT_PRESENT_WINDOW_DAYS,
    EventSource,
    StancePolicy,
    SubjectStatus,
    TemporalDirection,
    classify_direction,
    resolve_policy,
)

#: Weekly. Fine enough to locate a period, coarse enough to scan a lifetime.
DEFAULT_STEP_DAYS = 7

#: Windows graded below this are not reported. A single technique firing once
#: is noise at lifetime scale — reporting it would bury the convergences.
DEFAULT_MIN_GRADE = ConvergenceGrade.CONVERGING

#: Independent techniques that must agree before a window answers YES.
#:
#: Only three techniques are implemented (SBC Vedha, Latta, yearly Tara), so
#: this is currently a strict 3-of-3. That is deliberate and was the chosen
#: threshold; implementing Progressed Saturn turns it into 3-of-4 and makes it
#: less brittle. Callers that need the looser research view should read
#: ``grade`` rather than lowering this.
DEFAULT_MIN_TECHNIQUES = 3


def yearly_tara_is_unfavorable(position_1_indexed: int) -> bool:
    """Whether a yearly Tara position is classically unfavourable.

    Favourability is read off the **base 9-cycle position**, which is sourced
    (``tarabala.UNFAVORABLE_TARA_9``), not off the extended 27-name — the
    extended table renames eight positions but the source material never
    states a separate favourability list for them. Inheriting from the base
    position is an inference, and a deliberately conservative one: it avoids
    inventing a second table. Stated here rather than buried so it can be
    corrected if a source turns up.
    """
    base_name = TARA_NAMES_9[(position_1_indexed - 1) % 9]
    return base_name in UNFAVORABLE_TARA_9


@dataclass
class SensitiveWindow:
    """A contiguous period several techniques agree on."""

    start_utc: datetime
    end_utc: datetime
    temporal_direction: TemporalDirection
    grade: ConvergenceGrade
    policy: StancePolicy
    #: Binary answer to "kuch hoga ya nahi" — enough independent techniques agree.
    verdict: str  # "yes" | "no"
    techniques_agreeing: int
    #: Whether the window reads as difficulty, support, or both at once.
    polarity: Polarity
    indicators: list[Indicator]
    #: Domains flagged by more than one technique — the ones worth naming.
    domains: frozenset[LifeDomain]
    #: Every domain touched, including single-technique ones.
    domains_all: frozenset[LifeDomain]
    techniques: dict[str, list[str]]
    verification: VerificationStatus
    event_matches: list[EventMatch] = field(default_factory=list)

    @property
    def duration_days(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds() / 86400.0

    @property
    def is_confirmed_by_disclosure(self) -> bool:
        return any(m.is_confirmation for m in self.event_matches)

    def lead_time_days(self, now_utc: datetime) -> float:
        """Days until this window opens. Negative once it has begun."""
        return (self.start_utc - now_utc).total_seconds() / 86400.0


@dataclass
class SensitiveTimeline:
    janma_nakshatra: str
    start_utc: datetime
    end_utc: datetime
    step_days: int
    now_utc: datetime
    past_windows: list[SensitiveWindow]
    present_windows: list[SensitiveWindow]
    future_alerts: list[SensitiveWindow]
    #: Techniques named in the source material but not computed anywhere here.
    unchecked_techniques: list[str]
    #: Disclosed events that fell in no reported window — the misses, kept
    #: visible so the reading cannot look better than it is.
    unexplained_events: list[DisclosedEvent] = field(default_factory=list)

    @property
    def all_windows(self) -> list[SensitiveWindow]:
        return self.past_windows + self.present_windows + self.future_alerts

    def scanned_span_days(self) -> float:
        return (self.end_utc - self.start_utc).total_seconds() / 86400.0

    def elapsed_span_days(self) -> float:
        """Scanned span up to now — the part that could have produced an outcome."""
        end = min(self.end_utc, self.now_utc)
        return max(0.0, (end - self.start_utc).total_seconds() / 86400.0)


class SensitiveTimelineService:
    def __init__(
        self,
        sbc_report_service: SBCReportService,
        latta_engine: LattaEngine,
    ) -> None:
        self._sbc = sbc_report_service
        self._latta = latta_engine

    def build_timeline(
        self,
        janma_nakshatra: str,
        birth_datetime_utc: datetime,
        start_utc: datetime,
        end_utc: datetime,
        sbc_janma_nakshatra: Optional[str] = None,
        step_days: int = DEFAULT_STEP_DAYS,
        now_utc: Optional[datetime] = None,
        disclosed_events: Optional[Iterable[DisclosedEvent]] = None,
        subject_status: SubjectStatus = SubjectStatus.LIVING,
        min_grade: ConvergenceGrade = DEFAULT_MIN_GRADE,
        min_techniques: int = DEFAULT_MIN_TECHNIQUES,
        present_window_days: int = DEFAULT_PRESENT_WINDOW_DAYS,
    ) -> SensitiveTimeline:
        if step_days < 1:
            raise ValueError("step_days must be >= 1")
        if end_utc <= start_utc:
            raise ValueError("end_utc must be after start_utc")

        reference = now_utc or datetime.now(timezone.utc)
        events = list(disclosed_events or ())
        janma = janma_nakshatra.strip().lower()

        samples: list[tuple[datetime, list[Indicator]]] = []
        cursor = start_utc
        step = timedelta(days=step_days)
        while cursor <= end_utc:
            samples.append((cursor, self._indicators_at(cursor, janma, sbc_janma_nakshatra, birth_datetime_utc)))
            cursor += step

        windows = self._to_windows(
            samples,
            step_days=step_days,
            reference=reference,
            events=events,
            subject_status=subject_status,
            min_grade=min_grade,
            min_techniques=min_techniques,
            present_window_days=present_window_days,
        )

        explained = {
            m.event.event_id
            for w in windows
            for m in w.event_matches
            if m.is_confirmation
        }

        return SensitiveTimeline(
            janma_nakshatra=janma,
            start_utc=start_utc,
            end_utc=end_utc,
            step_days=step_days,
            now_utc=reference,
            past_windows=[w for w in windows if w.temporal_direction is TemporalDirection.PAST],
            present_windows=[w for w in windows if w.temporal_direction is TemporalDirection.PRESENT],
            future_alerts=[w for w in windows if w.temporal_direction is TemporalDirection.FUTURE],
            unchecked_techniques=techniques_checked([])["not_implemented"],
            unexplained_events=[e for e in events if e.event_id not in explained],
        )

    # ── Per-sample indicator collection ───────────────────────────────────

    def _indicators_at(
        self,
        moment_utc: datetime,
        janma_27: str,
        sbc_janma: Optional[str],
        birth_datetime_utc: datetime,
    ) -> list[Indicator]:
        indicators: list[Indicator] = []
        indicators.extend(self._sbc_indicators(moment_utc, sbc_janma or janma_27))
        indicators.extend(self._latta_indicators(moment_utc, janma_27))
        indicators.extend(self._yearly_tara_indicators(moment_utc, janma_27, birth_datetime_utc))
        return indicators

    def _sbc_indicators(self, moment_utc: datetime, janma: str) -> list[Indicator]:
        """Adverse *and* supportive Sangya hits, each carrying its event signature.

        Both polarities are collected. Reporting only afflictions would make
        every supportive event in a native's life score as a miss, which is
        exactly the flaw the first backtest had.
        """
        report = self._sbc.build_report(moment_utc, janma_nakshatra=janma)
        indicators: list[Indicator] = []

        for point in report.sensitive_points:
            if point.status == "afflicted":
                pairs = [(g, Polarity.ADVERSE) for g in point.malefic_hits]
            elif point.status == "activated":
                pairs = [(g, Polarity.SUPPORTIVE) for g in point.benefic_hits]
            elif point.status == "mixed":
                pairs = [(g, Polarity.ADVERSE) for g in point.malefic_hits]
                pairs += [(g, Polarity.SUPPORTIVE) for g in point.benefic_hits]
            else:
                continue

            domains = SANGYA_DOMAINS.get(point.key, frozenset({LifeDomain.OTHER}))
            # A summary can name the point without naming a graha; keep the
            # hit rather than dropping it, just without a signature.
            if not pairs:
                indicators.append(
                    Indicator(
                        technique=Technique.SBC_VEDHA,
                        detail=f"sangya:{point.key}",
                        domains=domains,
                        is_severe=point.key == "janma",
                        polarity=Polarity.ADVERSE if point.status == "afflicted" else Polarity.SUPPORTIVE,
                    )
                )
                continue

            for graha, polarity in pairs:
                signature = _signature_or_none(point.key, graha)
                indicators.append(
                    Indicator(
                        technique=Technique.SBC_VEDHA,
                        detail=signature.label if signature else f"sangya:{point.key}",
                        domains=domains,
                        # Affliction of Janma itself is the heavier reading.
                        is_severe=polarity is Polarity.ADVERSE and point.key == "janma",
                        polarity=polarity,
                        signature=signature,
                    )
                )
        return indicators

    def _latta_indicators(self, moment_utc: datetime, janma_27: str) -> list[Indicator]:
        report = self._latta.build_report(janma_27, moment_utc, now_utc=moment_utc)
        return [
            Indicator(
                technique=Technique.LATTA,
                detail=f"latta:{hit.planet}",
                domains=hit.domains,
                is_severe=hit.is_severe,
                verification=hit.verification,
                # Benefic Latta is a milder reading, not an adverse one.
                polarity=Polarity.ADVERSE if hit.is_malefic else Polarity.SUPPORTIVE,
            )
            for hit in report.hits
        ]

    def _yearly_tara_indicators(
        self,
        moment_utc: datetime,
        janma_27: str,
        birth_datetime_utc: datetime,
    ) -> list[Indicator]:
        try:
            _, position, _ = yearly_tara(janma_27, birth_datetime_utc, moment_utc)
        except ValueError:
            return []  # moment precedes birth
        if not yearly_tara_is_unfavorable(position):
            return []
        return [
            Indicator(
                technique=Technique.YEARLY_TARA,
                detail=f"tara:{extended_27_name(position)}",
                # The Tara year speaks to the whole life, not one area; it
                # contributes convergence weight without narrowing the domain.
                domains=frozenset(),
            )
        ]

    # ── Grouping ──────────────────────────────────────────────────────────

    def _to_windows(
        self,
        samples: list[tuple[datetime, list[Indicator]]],
        step_days: int,
        reference: datetime,
        events: list[DisclosedEvent],
        subject_status: SubjectStatus,
        min_grade: ConvergenceGrade,
        min_techniques: int,
        present_window_days: int,
    ) -> list[SensitiveWindow]:
        windows: list[SensitiveWindow] = []
        bucket: list[tuple[datetime, list[Indicator]]] = []

        def flush() -> None:
            # A stretch running from the past through to the future is cut at
            # each direction boundary rather than flattened to one label: a
            # window that began in childhood and is still open must still
            # report its past portion as a retrodiction, and collapsing the
            # whole thing to "present" would lose exactly the half the native
            # can check.
            for direction, run in _split_by_direction(bucket, reference, present_window_days):
                windows.append(
                    self._build_window(
                        run, direction, step_days, events, subject_status, min_techniques
                    )
                )

        for moment, indicators in samples:
            if grade_convergence(indicators).rank >= min_grade.rank:
                bucket.append((moment, indicators))
                continue
            if bucket:
                flush()
                bucket = []

        if bucket:
            flush()
        return windows

    def _build_window(
        self,
        bucket: list[tuple[datetime, list[Indicator]]],
        direction: TemporalDirection,
        step_days: int,
        events: list[DisclosedEvent],
        subject_status: SubjectStatus,
        min_techniques: int,
    ) -> SensitiveWindow:
        start = bucket[0][0]
        # The last sample stands in for the whole step it represents.
        end = bucket[-1][0] + timedelta(days=step_days)

        merged: list[Indicator] = []
        seen: set[tuple[Technique, str]] = set()
        for _, indicators in bucket:
            for indicator in indicators:
                key = (indicator.technique, indicator.detail)
                if key not in seen:
                    seen.add(key)
                    merged.append(indicator)

        domains = converging_domains(merged)
        union = all_domains(merged)

        matches = (
            match_events_by_domains(events, start, end, union)
            if events and union
            else []
        )
        source = (
            EventSource.USER_DISCLOSED
            if any(m.is_confirmation for m in matches)
            else EventSource.SYSTEM_INFERRED
        )

        return SensitiveWindow(
            start_utc=start,
            end_utc=end,
            temporal_direction=direction,
            grade=grade_convergence(merged),
            policy=resolve_policy(direction, source, subject_status),
            verdict="yes" if meets_threshold(merged, min_techniques) else "no",
            techniques_agreeing=count_techniques(merged),
            polarity=polarity_of(merged),
            indicators=merged,
            domains=domains,
            domains_all=union,
            techniques=techniques_checked(merged),
            verification=weakest_verification(merged),
            event_matches=matches,
        )


def _signature_or_none(sangya_key: str, hit: str) -> Optional[EventSignature]:
    """Build an event signature from an SBC hit string.

    ``SBCPointVedhaSummary.benefic_hits`` / ``malefic_hits`` carry display
    strings like ``"Saturn (Right)"`` — the graha plus the ray direction —
    so the planet name has to be taken off the front. An unrecognised
    string yields ``None`` rather than raising: losing one signature is
    better than losing the whole window over a formatting change.
    """
    graha = hit.split("(")[0].strip()
    if not graha:
        return None
    try:
        return build_signature(sangya_key, graha)
    except KeyError:
        return None


def _split_by_direction(
    bucket: list[tuple[datetime, list[Indicator]]],
    reference: datetime,
    present_window_days: int,
) -> list[tuple[TemporalDirection, list[tuple[datetime, list[Indicator]]]]]:
    """Cut a run of consecutive hits into homogeneous past/present/future runs."""
    runs: list[tuple[TemporalDirection, list[tuple[datetime, list[Indicator]]]]] = []
    current: list[tuple[datetime, list[Indicator]]] = []
    current_direction: Optional[TemporalDirection] = None

    for moment, indicators in bucket:
        direction = classify_direction(moment, reference, present_window_days)
        if current_direction is None or direction is current_direction:
            current.append((moment, indicators))
            current_direction = direction
            continue
        runs.append((current_direction, current))
        current = [(moment, indicators)]
        current_direction = direction

    if current and current_direction is not None:
        runs.append((current_direction, current))
    return runs


def match_events_by_domains(
    events: list[DisclosedEvent],
    window_start_utc: datetime,
    window_end_utc: datetime,
    domains: frozenset[LifeDomain],
) -> list[EventMatch]:
    """Match disclosed events to a window by life domain rather than Sangya key.

    ``disclosed_events.match_events`` keys alignment off Sangya keys; a
    convergence window has already reduced several techniques to a domain set,
    so this rescoring keeps the same overlap arithmetic while asking the
    question the window can actually answer.
    """
    raw = match_events(events, window_start_utc, window_end_utc)
    rescored = [
        EventMatch(
            event=m.event,
            overlap_days=m.overlap_days,
            domain_matches=m.event.domain in domains,
            matched_sangyas=(),
        )
        for m in raw
    ]
    rescored.sort(key=lambda m: (m.domain_matches, m.event.significance, m.overlap_days), reverse=True)
    return rescored
