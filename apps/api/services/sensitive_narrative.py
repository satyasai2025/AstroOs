"""
AstroOS — Narrative rendering for sensitive windows

Turns a :class:`~apps.api.services.sensitive_timeline_service.SensitiveWindow`
into the sentences a native actually reads. Three voices, chosen by the
window's own policy rather than by a caller flag:

* **Retrodictive** (past) — "the indicators converge on this stretch, in
  these life areas". If the native disclosed an event that lines up, it
  is named; if not, they are invited to confirm or correct rather than
  handed a guess.
* **Advisory** (present) — a window being lived through, so conduct
  advice is meaningful.
* **Prospective** (future) — an alert: the period, the life areas, the
  lead time, and explicitly no event.

Alongside the prose, every narrative carries ``categories`` — the
sourced Sangya x Graha event categories behind the window, worded
classically for a retrodiction and guardedly for a forecast. That is the
answer to "kya event": a category ("sudden conflict and financial loss
bearing on capital and reserves"), never a prediction.

Every string produced here is scanned against the window's policy before
being returned, the same way ``sbc_ai_analyzer`` does. The templates are
authored to comply, so a redaction means a template regression and is
reported on the result rather than silently applied.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from apps.api.services.sensitive_timeline_service import SensitiveWindow
from packages.shared.disclosed_events import LifeDomain
from packages.shared.sensitive_convergence import ConvergenceGrade, Polarity
from packages.shared.temporal_stance import TemporalDirection, Voice, redact, scan_text

logger = logging.getLogger(__name__)

#: Plain-language names for the life domains. The domain *is* the claim in
#: every voice, so these are the most specific words any narrative uses.
DOMAIN_LABELS: dict[LifeDomain, str] = {
    LifeDomain.HEALTH: "physical health and vitality",
    LifeDomain.MENTAL_WELLBEING: "mental peace and clarity",
    LifeDomain.FAMILY: "family matters",
    LifeDomain.RELATIONSHIP: "close relationships",
    LifeDomain.CAREER: "work and professional standing",
    LifeDomain.FINANCE: "finances",
    LifeDomain.EDUCATION: "study and learning",
    LifeDomain.RELOCATION: "home, travel and relocation",
    LifeDomain.LEGAL: "legal and official matters",
    LifeDomain.SPIRITUAL: "inner and spiritual life",
    LifeDomain.OTHER: "general circumstances",
}

_GRADE_PHRASES: dict[ConvergenceGrade, str] = {
    ConvergenceGrade.STRONG: "several independent techniques agree strongly",
    ConvergenceGrade.CONVERGING: "more than one independent technique agrees",
    ConvergenceGrade.SINGLE: "one technique flags this, with nothing corroborating it",
    ConvergenceGrade.NONE: "nothing flags this",
}

#: Attached to every call, in every direction. The tradition flags a period;
#: it does not guarantee an outcome, and the difference is the whole claim.
_QUALIFIER = (
    "This is what the classical indicators say about the period, not a statement "
    "about what did or will happen."
)


@dataclass
class WindowNarrative:
    headline: str
    body: str
    #: The sourced event categories behind this window, worded for its
    #: direction — classical for past/disclosed, guarded for a forecast.
    #: This is the "kya event" layer; it is a category, never a prediction.
    categories: list[str] = field(default_factory=list)
    qualifier: str = _QUALIFIER
    invitation: str = ""
    #: Non-empty only if a template regressed into prohibited vocabulary.
    redactions: list[str] = field(default_factory=list)

    @property
    def paragraphs(self) -> list[str]:
        return [p for p in (self.body, self.qualifier, self.invitation) if p]


def render_window(window: SensitiveWindow, now_utc: datetime) -> WindowNarrative:
    """Render ``window`` in the voice its policy requires."""
    voice = window.policy.voice
    if voice is Voice.RETRODICTIVE:
        narrative = _render_past(window)
    elif voice is Voice.PROSPECTIVE:
        narrative = _render_future(window, now_utc)
    else:
        narrative = _render_present(window)

    return _enforce(narrative, window)


def _render_past(window: SensitiveWindow) -> WindowNarrative:
    period = _period(window)
    areas = _areas(window)
    confirmations = [m for m in window.event_matches if m.is_confirmation]

    if confirmations and window.policy.may_name_specific_event:
        event = confirmations[0].event
        named = event.description or f"the {DOMAIN_LABELS[event.domain]} event you described"
        return WindowNarrative(
            headline=f"{period} — matches something you told me about",
            categories=_categories(window),
            body=(
                f"Across {period}, {_GRADE_PHRASES[window.grade]}, pointing at {areas}. "
                f"That is the same area and the same stretch as {named}. The classical "
                f"reading and your own account line up here."
            ),
        )

    return WindowNarrative(
        headline=f"{period} — a stretch the indicators single out",
        categories=_categories(window),
        body=(
            f"Across {period}, {_GRADE_PHRASES[window.grade]}, pointing at {areas}. "
            f"The tradition treats that kind of agreement as marking a genuinely "
            f"demanding period. What form it took, if any, the technique does not "
            f"specify and this reading does not guess."
        ),
        invitation=(
            "If something significant did happen for you around then, telling me lets me "
            "calibrate the rest of the reading against it. If nothing did, that is just as "
            "useful — it tells us this technique reads your chart less well than it appears to."
        ),
    )


def _render_present(window: SensitiveWindow) -> WindowNarrative:
    return WindowNarrative(
        headline=f"{_period(window)} — running now",
        categories=_categories(window),
        body=(
            f"You are in this window at the moment: {_GRADE_PHRASES[window.grade]}, "
            f"pointing at {_areas(window)}. The practical reading is to give those areas "
            f"more margin than usual — slower decisions, more rest, fewer commitments made "
            f"in a hurry — rather than to expect anything in particular."
        ),
    )


def _render_future(window: SensitiveWindow, now_utc: datetime) -> WindowNarrative:
    lead = window.lead_time_days(now_utc)
    lead_phrase = (
        f"about {int(lead / 30)} months out" if lead >= 60
        else f"about {int(lead)} days out"
    )
    return WindowNarrative(
        headline=f"{_period(window)} — worth marking ahead ({lead_phrase})",
        categories=_categories(window),
        body=(
            f"Looking forward, {_GRADE_PHRASES[window.grade]} across {_period(window)}, "
            f"pointing at {_areas(window)}. Treat it as a period to plan around — avoid "
            f"stacking irreversible decisions into it where you have the choice — not as a "
            f"forecast of any particular event. The tradition marks the window; it does not "
            f"say what fills it."
        ),
    )


def _categories(window: SensitiveWindow) -> list[str]:
    """Sourced event categories behind this window, worded for its direction.

    Each is a Sangya x Graha pair: the Sangya says which part of life is
    touched, the graha in what manner. Deduplicated and capped, because a
    long window can accumulate a dozen near-identical pairs and a reader
    needs the shape, not the census.
    """
    direction = window.policy.direction
    seen: list[str] = []
    for indicator in window.indicators:
        signature = indicator.signature
        if signature is None:
            continue
        text = signature.describe(direction)
        if text not in seen:
            seen.append(text)
    return seen[:5]


def _period(window: SensitiveWindow) -> str:
    start = window.start_utc.strftime("%b %Y")
    end = window.end_utc.strftime("%b %Y")
    return start if start == end else f"{start} – {end}"


def _areas(window: SensitiveWindow) -> str:
    # Prefer domains more than one technique agreed on; fall back to the
    # wider union, and say so plainly when nothing narrowed down at all.
    domains = window.domains or window.domains_all
    labels = sorted(DOMAIN_LABELS[d] for d in domains)
    if not labels:
        return "no single life area in particular"
    if len(labels) == 1:
        return labels[0]
    return ", ".join(labels[:-1]) + f" and {labels[-1]}"


def _enforce(narrative: WindowNarrative, window: SensitiveWindow) -> WindowNarrative:
    """Scan the rendered text against the window's policy; redact on regression."""
    policy = window.policy
    redactions: list[str] = []

    for name in ("headline", "body", "invitation"):
        text = getattr(narrative, name)
        violations = scan_text(text, policy, field_name=name)
        if violations:
            redactions.extend(f"{v.field_name}: {v.term}" for v in violations)
            setattr(narrative, name, redact(text, policy))

    # Categories carry the classical wording, so they are the most likely
    # place for a policy lapse to show up.
    for i, text in enumerate(narrative.categories):
        violations = scan_text(text, policy, field_name=f"categories[{i}]")
        if violations:
            redactions.extend(f"{v.field_name}: {v.term}" for v in violations)
            narrative.categories[i] = redact(text, policy)

    if redactions:
        logger.warning(
            "Sensitive narrative template violated its %s policy and was redacted: %s",
            policy.direction.value,
            ", ".join(redactions),
        )
    narrative.redactions = redactions
    return narrative
