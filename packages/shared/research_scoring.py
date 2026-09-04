"""
AstroOS — Research Scoring: Coverage-Adjusted Lift

Workstream 5 scoring metric.

The core insight from the source plan is that raw recall is misleading
when a technique only runs over part of the available time window.
A technique that scans 10% of time and hits 10% of events has the same
lift as one that scans 100% of time and hits 100% of events — but they
are not equally informative.

    lift = recall / coverage

where:
    recall   = hits / total_events          (fraction of events correctly flagged)
    coverage = windows_scanned / total_time  (fraction of timeline examined)

A lift > 1.0 means the technique finds events at above-random rate.
A lift = 1.0 is chance. A lift < 1.0 is worse than random.

Binary YES/NO Verdict
---------------------
Per the plan: a window gets a YES verdict if and only if >= 3 *distinct*
techniques agree (see :mod:`packages.shared.sensitive_convergence` for the
convergence logic). This module wraps the verdict in a typed dataclass.

Pure module — no ephemeris, no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class TechniqueScore:
    """Coverage-adjusted lift for one sensitive-timing technique.

    Args:
        technique:      Short identifier (e.g. ``"sbc_vedha"``).
        hits:           Number of disclosed events correctly flagged by this
                        technique.
        total_events:   Total disclosed events in the evaluation corpus.
        windows_scanned: Number of time windows this technique actually
                        examined (e.g. number of calendar weeks scanned).
        total_windows:  Total time windows in the evaluation period.

    The distinction between *windows_scanned* and *total_windows* captures
    partial-coverage runs: a technique that only operates over a subset of
    the natal chart's dasha periods will have coverage < 1.0.
    """

    technique: str
    hits: int
    total_events: int
    windows_scanned: int
    total_windows: int

    def __post_init__(self) -> None:
        if self.hits < 0:
            raise ValueError("hits must be >= 0")
        if self.total_events < 0:
            raise ValueError("total_events must be >= 0")
        if self.windows_scanned < 0:
            raise ValueError("windows_scanned must be >= 0")
        if self.total_windows <= 0:
            raise ValueError("total_windows must be > 0")
        if self.hits > self.total_events:
            raise ValueError("hits cannot exceed total_events")
        if self.windows_scanned > self.total_windows:
            raise ValueError("windows_scanned cannot exceed total_windows")

    @property
    def recall(self) -> float:
        """Fraction of disclosed events correctly flagged. 0.0 if no events."""
        if self.total_events == 0:
            return 0.0
        return self.hits / self.total_events

    @property
    def coverage(self) -> float:
        """Fraction of time windows the technique examined. Always > 0."""
        return self.windows_scanned / self.total_windows

    @property
    def lift(self) -> float:
        """Coverage-adjusted lift: recall / coverage.

        Interpretation:
        - lift > 1.0: technique finds events at above-random rate.
        - lift = 1.0: technique performs at random baseline.
        - lift < 1.0: technique performs below random.
        - lift = 0.0: no hits at all.

        Returns 0.0 when coverage is 0 (no windows scanned).
        """
        if self.coverage == 0.0:
            return 0.0
        return self.recall / self.coverage

    @property
    def precision(self) -> float:
        """Hits / windows_scanned — how often a flagged window contains an event.

        Returns 0.0 when no windows were scanned.
        """
        if self.windows_scanned == 0:
            return 0.0
        return self.hits / self.windows_scanned


@dataclass(frozen=True)
class EnsembleVerdict:
    """YES/NO binary verdict for a time window based on technique agreement.

    Per the plan: YES iff >= min_techniques distinct techniques agree.
    The canonical threshold is 3 (SBC Vedha + Latta + Tara must all fire).
    """

    window_id: str
    techniques_fired: tuple[str, ...]
    min_techniques: int = 3
    notes: str = ""

    @property
    def verdict(self) -> str:
        """``'YES'`` if >= min_techniques *distinct* techniques agree, else ``'NO'``."""
        return "YES" if self.technique_count >= self.min_techniques else "NO"

    @property
    def is_yes(self) -> bool:
        """True when the verdict is YES."""
        return self.verdict == "YES"

    @property
    def technique_count(self) -> int:
        """Number of distinct techniques that fired."""
        return len(set(self.techniques_fired))


def rank_techniques(scores: Sequence[TechniqueScore]) -> list[TechniqueScore]:
    """Return techniques ordered by lift descending (highest lift first).

    Ties are broken by recall descending, then by technique name ascending.
    """
    return sorted(
        scores,
        key=lambda s: (-s.lift, -s.recall, s.technique),
    )


def corpus_summary(scores: Sequence[TechniqueScore]) -> dict[str, float]:
    """Aggregate lift statistics across the whole technique ensemble.

    Returns:
        dict with keys: mean_lift, max_lift, min_lift, mean_recall, mean_coverage.
    """
    if not scores:
        return {
            "mean_lift": 0.0,
            "max_lift": 0.0,
            "min_lift": 0.0,
            "mean_recall": 0.0,
            "mean_coverage": 0.0,
        }
    lifts = [s.lift for s in scores]
    recalls = [s.recall for s in scores]
    coverages = [s.coverage for s in scores]
    n = len(scores)
    return {
        "mean_lift": sum(lifts) / n,
        "max_lift": max(lifts),
        "min_lift": min(lifts),
        "mean_recall": sum(recalls) / n,
        "mean_coverage": sum(coverages) / n,
    }
