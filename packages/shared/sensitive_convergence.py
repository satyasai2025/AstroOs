"""
AstroOS — Convergence grading for sensitive-timing techniques

The single most important rule in this whole area, stated repeatedly in
the source material: **a sensitive-timing call gets its weight from
several independent techniques agreeing, not from one technique firing
many times.** Four SBC Vedha hits in one week are still one technique's
opinion. One SBC hit plus an unfavourable Tara year plus a malefic
Latta is three.

This module encodes that distinction so it cannot be lost downstream:
:func:`grade_convergence` counts *distinct techniques*, never raw
indicator count. Everything here is pure — the ephemeris work lives in
``apps/api/services/sensitive_timeline_service.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional

from packages.shared.disclosed_events import LifeDomain
from packages.shared.latta import VerificationStatus


class Technique(str, Enum):
    """Independent sensitive-timing techniques that can converge."""

    SBC_VEDHA = "sbc_vedha"
    LATTA = "latta"
    YEARLY_TARA = "yearly_tara"
    TRANSIT_TARA = "transit_tara"
    #: Declared but not yet implemented — see NOT_YET_IMPLEMENTED below. Listed
    #: here so that "which techniques were checked" can be reported honestly
    #: rather than a partial check reading as a complete one.
    PROGRESSED_SATURN = "progressed_saturn"


#: Techniques named in the source material that this codebase does not yet
#: compute. A timeline reports these as *unchecked* rather than omitting them,
#: because "two of two techniques agree" and "two of three agree, one not run"
#: are different claims.
NOT_YET_IMPLEMENTED: frozenset[Technique] = frozenset({Technique.PROGRESSED_SATURN})

IMPLEMENTED_TECHNIQUES: tuple[Technique, ...] = tuple(
    t for t in Technique if t not in NOT_YET_IMPLEMENTED
)


class ConvergenceGrade(str, Enum):
    """How many independent techniques agree at a moment."""

    NONE = "none"
    SINGLE = "single"
    CONVERGING = "converging"
    STRONG = "strong"

    @property
    def rank(self) -> int:
        return _GRADE_RANK[self]


_GRADE_RANK = {
    ConvergenceGrade.NONE: 0,
    ConvergenceGrade.SINGLE: 1,
    ConvergenceGrade.CONVERGING: 2,
    ConvergenceGrade.STRONG: 3,
}


class Polarity(str, Enum):
    """Whether indicators point at difficulty or support.

    Kept separate from severity: a strongly supportive window and a
    strongly adverse one can both be "severe", and scoring a triumph
    against an affliction window is a category error rather than a miss.
    """

    ADVERSE = "adverse"
    SUPPORTIVE = "supportive"
    MIXED = "mixed"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Indicator:
    """One technique's finding at one moment."""

    technique: Technique
    #: Short machine-readable summary, e.g. "saturn:janma" or "tara:vipat".
    detail: str
    domains: frozenset[LifeDomain]
    #: The technique's own "this is the heavier reading" flag, where it has one.
    is_severe: bool = False
    verification: VerificationStatus = VerificationStatus.STANDARD_UNVERIFIED
    polarity: Polarity = Polarity.ADVERSE
    #: The sourced event category behind this indicator, where one exists.
    #: Typed loosely to keep this module free of a service-layer import;
    #: it holds an ``event_signature.EventSignature``.
    signature: Optional[object] = None


def count_techniques(indicators: Iterable[Indicator]) -> int:
    """How many *distinct* techniques fired."""
    return len({i.technique for i in indicators})


def meets_threshold(indicators: Iterable[Indicator], min_techniques: int) -> bool:
    """Whether enough independent techniques agree to answer YES.

    Deliberately separate from :func:`grade_convergence`: "three techniques
    agree" and "grade STRONG" are different predicates, since STRONG is
    reachable by two techniques plus a severity promotion. A binary verdict
    shown to a person must key off the count the user asked for, not off a
    grade that happens to correlate with it.
    """
    if min_techniques < 1:
        raise ValueError("min_techniques must be >= 1")
    return count_techniques(indicators) >= min_techniques


def polarity_of(indicators: Iterable[Indicator]) -> Polarity:
    """Overall polarity across a set of indicators."""
    found = {i.polarity for i in indicators if i.polarity is not Polarity.NEUTRAL}
    if not found:
        return Polarity.NEUTRAL
    if found == {Polarity.ADVERSE}:
        return Polarity.ADVERSE
    if found == {Polarity.SUPPORTIVE}:
        return Polarity.SUPPORTIVE
    return Polarity.MIXED


def grade_convergence(indicators: Iterable[Indicator]) -> ConvergenceGrade:
    """Grade by count of *distinct techniques*, promoted once for severity.

    A severe indicator (malefic Latta kicking forward, an afflicted Janma
    Sangya) promotes the grade one step, so a single severe technique reads
    as ``SINGLE`` rather than being dismissed, while three agreeing
    techniques reach ``STRONG`` whether or not any is individually severe.
    """
    found = list(indicators)
    techniques = {i.technique for i in found}
    if not techniques:
        return ConvergenceGrade.NONE

    score = len(techniques) + (1 if any(i.is_severe for i in found) else 0)
    if score >= 4:
        return ConvergenceGrade.STRONG
    if score >= 3:
        return ConvergenceGrade.CONVERGING
    return ConvergenceGrade.SINGLE


def converging_domains(indicators: Iterable[Indicator]) -> frozenset[LifeDomain]:
    """Life domains flagged by **more than one** technique.

    This is deliberately stricter than the union: a domain two techniques
    independently point at is the one worth naming, and reporting the union
    instead would let a single technique's broad domain list dominate.
    """
    counts: dict[LifeDomain, set[Technique]] = {}
    for indicator in indicators:
        for domain in indicator.domains:
            counts.setdefault(domain, set()).add(indicator.technique)
    return frozenset(d for d, techniques in counts.items() if len(techniques) > 1)


def all_domains(indicators: Iterable[Indicator]) -> frozenset[LifeDomain]:
    """Union of every domain touched, converging or not."""
    domains: set[LifeDomain] = set()
    for indicator in indicators:
        domains |= indicator.domains
    return frozenset(domains)


def techniques_checked(indicators: Iterable[Indicator]) -> dict[str, list[str]]:
    """Report which techniques fired, which were silent, and which never ran.

    Returned as plain strings so it can go straight into an API payload. The
    ``not_implemented`` bucket is the honest part: it stops a two-technique
    agreement from being presented as if every technique had been consulted.
    """
    fired = {i.technique for i in indicators}
    return {
        "fired": sorted(t.value for t in fired),
        "silent": sorted(t.value for t in IMPLEMENTED_TECHNIQUES if t not in fired),
        "not_implemented": sorted(t.value for t in NOT_YET_IMPLEMENTED),
    }


def weakest_verification(indicators: Iterable[Indicator]) -> VerificationStatus:
    """The lowest sourcing tier among the indicators backing a call.

    A convergence is only as well-sourced as its weakest contributor, so this
    is what a reading should state rather than the best tier present.
    """
    order = [
        VerificationStatus.NEEDS_SOURCE,
        VerificationStatus.STANDARD_UNVERIFIED,
        VerificationStatus.VERIFIED,
    ]
    found = [i.verification for i in indicators]
    if not found:
        return VerificationStatus.VERIFIED
    return min(found, key=order.index)
