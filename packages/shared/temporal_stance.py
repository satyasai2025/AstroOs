"""
AstroOS — Temporal Stance Policy for sensitive-timing output

Sensitive-timing techniques (Sarvatobhadra Chakra Vedha, the Tara
cycle, Progressed Saturn) can legitimately flag a period as
classically high-risk. What varies — and what this module makes
explicit — is *how much may be said about it*, which depends on three
independent axes rather than one blanket rule:

1. ``TemporalDirection`` — is the flagged window in the past, running
   now, or still ahead? A retrodiction about a past window is
   falsifiable: the native already knows what happened, so naming a
   specific window carries none of the fear-inducing weight a forecast
   does. A forecast does.
2. ``EventSource`` — did the native disclose the event themselves, or
   did the engine infer a window with nothing to anchor it to?
   Repeating back what someone told you is not a prediction. Guessing
   at what befell them is.
3. ``SubjectStatus`` — a living person versus a historical, already
   deceased public figure being used for backtesting. The longevity /
   Arishta family of formulas is research-only and never runs for the
   living, in either temporal direction.

The resulting :class:`StancePolicy` is a data object, not prose: engines
attach it to their output and presentation layers read it. A vocabulary
scanner (:func:`scan_text`) then acts as a regression guard so that a
future template edit cannot quietly reintroduce disease/mortality
language into a channel where the policy forbids it.

This module is pure — no ephemeris, no I/O — so it can be imported by
domain code, services and tests alike.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Iterable, Optional

# ── Axes ──────────────────────────────────────────────────────────────────────


class TemporalDirection(str, Enum):
    """Where a flagged window sits relative to the moment of reading."""

    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"


class EventSource(str, Enum):
    """Whether a concrete event behind a window is known or merely inferred."""

    USER_DISCLOSED = "user_disclosed"
    SYSTEM_INFERRED = "system_inferred"


class SubjectStatus(str, Enum):
    """Who the reading is about."""

    LIVING = "living"
    DECEASED_HISTORICAL = "deceased_historical"


class Voice(str, Enum):
    """The grammatical stance an output for this policy must take."""

    RETRODICTIVE = "retrodictive"  # "the indicators converged in that window"
    ADVISORY = "advisory"  # "right now, avoid ..."
    PROSPECTIVE = "prospective"  # "this window is traditionally read as ..."


class LanguageCategory(str, Enum):
    """Vocabulary families the scanner recognises."""

    MORTALITY = "mortality"
    DISEASE = "disease"
    CATASTROPHE = "catastrophe"


#: A window within this many days of "now" reads as currently running rather
#: than past or future. Daily SBC sampling has roughly this much slack anyway
#: (see ``sbc_scan_engine`` for its granularity caveat).
DEFAULT_PRESENT_WINDOW_DAYS = 7


# ── Prohibited vocabulary ─────────────────────────────────────────────────────
#
# Deliberately narrow. The point is to block *naming the form the risk takes*
# — a specific disease, a cause of death, a named catastrophe — not to strip
# every serious word. Domain-level language ("health", "family matters",
# "financial pressure") is what the policy wants these channels to use
# instead, and none of it is listed here.

_VOCABULARY: dict[LanguageCategory, tuple[str, ...]] = {
    LanguageCategory.MORTALITY: (
        "death",
        "deaths",
        "die",
        "dies",
        "died",
        "dying",
        "fatal",
        "fatality",
        "fatalities",
        "demise",
        "perish",
        "perishes",
        "perished",
        "widow",
        "widowed",
        "widower",
        "bereavement",
        "funeral",
        "terminal illness",
        "life expectancy",
        "longevity span",
        "end of life",
    ),
    LanguageCategory.DISEASE: (
        "cancer",
        "tumour",
        "tumor",
        "stroke",
        "heart attack",
        "cardiac arrest",
        "diabetes",
        "paralysis",
        "tuberculosis",
        "kidney failure",
        "liver failure",
        "organ failure",
        "diagnosis",
        "diagnosed",
        "incurable",
    ),
    LanguageCategory.CATASTROPHE: (
        "accident",
        "accidents",
        "murder",
        "murdered",
        "suicide",
        "miscarriage",
        "bankruptcy",
        "imprisonment",
        "jailed",
        "divorce",
        "divorced",
    ),
}

_PATTERNS: dict[LanguageCategory, re.Pattern[str]] = {
    category: re.compile(
        r"\b(" + "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )
    for category, terms in _VOCABULARY.items()
}


# ── Policy ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class StancePolicy:
    """What an output about a given window is and is not allowed to do."""

    direction: TemporalDirection
    event_source: EventSource
    subject_status: SubjectStatus

    voice: Voice
    #: May the output name a concrete event (rather than only its life domain)?
    may_name_specific_event: bool
    #: Must the output invite the native to confirm or correct the reading?
    requires_invitation_to_confirm: bool
    #: May the Ayurdaya / Arishta "critical nakshatra" family of formulas run at all?
    longevity_formula_allowed: bool
    #: Vocabulary families that must not appear in generated text.
    prohibited_categories: frozenset[LanguageCategory]
    rationale: str

    #: Every sensitive-timing call, in every direction, states what the
    #: tradition claims rather than what will happen. This never varies, so
    #: it is a constant field rather than a computed one.
    requires_confidence_qualifier: bool = True

    def permits(self, category: LanguageCategory) -> bool:
        return category not in self.prohibited_categories


def classify_direction(
    moment_utc: datetime,
    now_utc: Optional[datetime] = None,
    present_window_days: int = DEFAULT_PRESENT_WINDOW_DAYS,
) -> TemporalDirection:
    """Classify a flagged moment as past, currently running, or future.

    ``present_window_days`` on either side of ``now_utc`` counts as present;
    a window that close is being lived through, so advisory voice fits it
    better than either retrodiction or forecast.
    """
    if present_window_days < 0:
        raise ValueError("present_window_days must be >= 0")

    reference = now_utc or datetime.now(timezone.utc)
    if moment_utc.tzinfo is None:
        moment_utc = moment_utc.replace(tzinfo=timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)

    slack = timedelta(days=present_window_days)
    if moment_utc < reference - slack:
        return TemporalDirection.PAST
    if moment_utc > reference + slack:
        return TemporalDirection.FUTURE
    return TemporalDirection.PRESENT


def resolve_policy(
    direction: TemporalDirection,
    event_source: EventSource = EventSource.SYSTEM_INFERRED,
    subject_status: SubjectStatus = SubjectStatus.LIVING,
) -> StancePolicy:
    """Resolve the three axes into a single policy object."""

    if subject_status is SubjectStatus.DECEASED_HISTORICAL:
        # Backtesting against a documented historical outcome. The whole
        # point is to compare the computed window against the recorded
        # event, so nothing is gained by euphemism — and no living person
        # is on the receiving end of it.
        return StancePolicy(
            direction=direction,
            event_source=event_source,
            subject_status=subject_status,
            voice=Voice.RETRODICTIVE,
            may_name_specific_event=True,
            requires_invitation_to_confirm=False,
            longevity_formula_allowed=True,
            prohibited_categories=frozenset(),
            rationale=(
                "Research/backtesting mode against a documented historical subject: "
                "hypothesis-testing against a known outcome, not a reading given to anyone."
            ),
        )

    if direction is TemporalDirection.PAST:
        if event_source is EventSource.USER_DISCLOSED:
            return StancePolicy(
                direction=direction,
                event_source=event_source,
                subject_status=subject_status,
                voice=Voice.RETRODICTIVE,
                may_name_specific_event=True,
                requires_invitation_to_confirm=False,
                longevity_formula_allowed=False,
                prohibited_categories=frozenset(),
                rationale=(
                    "The native disclosed this event themselves; reflecting it back while "
                    "explaining the classical convergence withholds nothing they do not already know."
                ),
            )
        return StancePolicy(
            direction=direction,
            event_source=event_source,
            subject_status=subject_status,
            voice=Voice.RETRODICTIVE,
            may_name_specific_event=False,
            requires_invitation_to_confirm=True,
            longevity_formula_allowed=False,
            prohibited_categories=frozenset(
                {LanguageCategory.MORTALITY, LanguageCategory.DISEASE, LanguageCategory.CATASTROPHE}
            ),
            rationale=(
                "A window was inferred with nothing to anchor it to. Naming the period and its "
                "life domain informs the native that something was detected; guessing the event "
                "itself would be a fabrication if wrong. Invite confirmation instead."
            ),
        )

    if direction is TemporalDirection.PRESENT:
        return StancePolicy(
            direction=direction,
            event_source=event_source,
            subject_status=subject_status,
            voice=Voice.ADVISORY,
            may_name_specific_event=event_source is EventSource.USER_DISCLOSED,
            requires_invitation_to_confirm=False,
            longevity_formula_allowed=False,
            prohibited_categories=frozenset({LanguageCategory.MORTALITY, LanguageCategory.DISEASE}),
            rationale=(
                "A currently-running window supports practical advice about conduct, "
                "but naming a disease or mortality outcome is a claim the technique cannot make."
            ),
        )

    return StancePolicy(
        direction=direction,
        event_source=event_source,
        subject_status=subject_status,
        voice=Voice.PROSPECTIVE,
        may_name_specific_event=False,
        requires_invitation_to_confirm=False,
        longevity_formula_allowed=False,
        prohibited_categories=frozenset(
            {LanguageCategory.MORTALITY, LanguageCategory.DISEASE, LanguageCategory.CATASTROPHE}
        ),
        rationale=(
            "Forecast. The tradition flags a period as heightened-risk; it does not specify "
            "the form the risk takes, so the period and its life domain are the whole claim."
        ),
    )


def policy_for_moment(
    moment_utc: datetime,
    now_utc: Optional[datetime] = None,
    event_source: EventSource = EventSource.SYSTEM_INFERRED,
    subject_status: SubjectStatus = SubjectStatus.LIVING,
    present_window_days: int = DEFAULT_PRESENT_WINDOW_DAYS,
) -> StancePolicy:
    """Convenience wrapper: classify ``moment_utc`` then resolve its policy."""
    return resolve_policy(
        classify_direction(moment_utc, now_utc, present_window_days),
        event_source=event_source,
        subject_status=subject_status,
    )


# ── Output validation ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LanguageViolation:
    """A prohibited term found in generated text."""

    category: LanguageCategory
    term: str
    field_name: str
    excerpt: str

    def __str__(self) -> str:  # pragma: no cover - diagnostic only
        return f"{self.field_name}: '{self.term}' ({self.category.value}) in …{self.excerpt}…"


class StancePolicyViolation(RuntimeError):
    """Raised by :func:`assert_compliant` when generated text breaks its policy."""

    def __init__(self, violations: list[LanguageViolation]) -> None:
        self.violations = violations
        super().__init__(
            "Generated text violates its temporal stance policy: "
            + "; ".join(str(v) for v in violations)
        )


def scan_text(
    text: str,
    policy: StancePolicy,
    field_name: str = "text",
    excerpt_radius: int = 40,
) -> list[LanguageViolation]:
    """Return every prohibited-vocabulary hit in ``text`` under ``policy``."""
    if not text:
        return []

    violations: list[LanguageViolation] = []
    for category in policy.prohibited_categories:
        for match in _PATTERNS[category].finditer(text):
            start = max(0, match.start() - excerpt_radius)
            end = min(len(text), match.end() + excerpt_radius)
            violations.append(
                LanguageViolation(
                    category=category,
                    term=match.group(0),
                    field_name=field_name,
                    excerpt=text[start:end].strip(),
                )
            )
    return violations


def scan_fields(
    fields: dict[str, str],
    policy: StancePolicy,
) -> list[LanguageViolation]:
    """Scan a mapping of ``field name -> text`` in one pass."""
    violations: list[LanguageViolation] = []
    for name, text in fields.items():
        violations.extend(scan_text(text, policy, field_name=name))
    return violations


def assert_compliant(fields: dict[str, str], policy: StancePolicy) -> None:
    """Raise :class:`StancePolicyViolation` if any field breaks ``policy``.

    Intended for tests and for CI over the response templates, where a
    violation means a template regression rather than a runtime condition.
    """
    violations = scan_fields(fields, policy)
    if violations:
        raise StancePolicyViolation(violations)


#: Neutral stand-ins used when redacting rather than raising.
_REDACTION: dict[LanguageCategory, str] = {
    LanguageCategory.MORTALITY: "a significant life event",
    LanguageCategory.DISEASE: "a health matter",
    LanguageCategory.CATASTROPHE: "a serious disruption",
}


def redact(text: str, policy: StancePolicy) -> str:
    """Replace prohibited terms with neutral domain-level stand-ins.

    The templates in this codebase are authored to be compliant, so this is
    a last-resort net for runtime paths that must not fail hard. Prefer
    :func:`assert_compliant` in tests, where failing loudly is the point.
    """
    if not text:
        return text
    for category in policy.prohibited_categories:
        text = _PATTERNS[category].sub(_REDACTION[category], text)
    return text
