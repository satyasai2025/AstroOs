"""
AstroOS — Event signatures (Sangya × Graha)

The answer to "kya hoga" that the computation can actually support.

A Vedha hit is not a bare life-domain. It is a specific *graha* striking
a specific *Sangya*, and the tradition attaches meaning to both halves:
the Sangya says which part of life is touched (Vainashika = ruin and
loss of capital), the graha says in what manner (Mars = sudden conflict
and financial loss). Together they give an event *category* — "sudden
conflict and financial loss bearing on capital and reserves" — which is
far more specific than the eleven-value ``LifeDomain`` enum this
codebase was previously flattening it into, and unlike that enum it is
sourced rather than invented.

What it still is not, and must not be presented as, is a specific
predicted event. "Sudden conflict affecting capital" is a category; "your
business will fail in March" is a claim the computation cannot make.

**Two-tier wording.** Each graha carries two parallel phrasings:

* ``classical_keywords`` — the tradition's own words, taken verbatim
  from ``GRAHA_VEDHA_RULES``. Used for past and disclosed windows, where
  the native already knows what happened and euphemism buys nothing.
* ``guarded_keywords`` — the same category, authored to be safe for a
  forecast. Mars keeps "sudden conflict" and "financial pressure" but
  does not say "accidents"; Ketu keeps "sudden disruption" but does not
  say "ailments".

These are hand-authored pairs rather than a regex-softening of the
classical string, because automatic redaction turns a useful reading
into mush ("a serious disruption") while an authored pair stays specific
in both voices. :func:`verify_guarded_keywords` exists so tests can
prove the guarded side actually satisfies the forecast policy, rather
than relying on runtime redaction to catch a lapse.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from packages.shared.temporal_stance import (
    StancePolicy,
    TemporalDirection,
    resolve_policy,
    scan_text,
)

#: Forecast-safe restatements, one per graha, parallel to
#: ``GRAHA_VEDHA_RULES[graha]["keywords"]``. Same category, no named
#: catastrophe or named ailment — see the module docstring.
GUARDED_KEYWORDS: dict[str, str] = {
    "sun": "ego friction, pressure from authority, and low physical energy",
    "mars": "sudden conflict, financial pressure, and a period to be physically careful in",
    "saturn": "chronic delay, stagnation, and heavy responsibility",
    "rahu": "unsettled anxiety, risk of being misled, and instability at the base",
    "ketu": "abrupt change of direction, detachment, and unexpected setbacks",
    "jupiter": "growth, good counsel, and a protected stretch",
    "venus": "material comfort, financial gain, and ease in close relationships",
    "moon": "emotional steadiness, protection, and unexpected support",
    "mercury": "mental clarity, profitable dealing, and negotiations going smoothly",
}

#: Forecast-safe restatements of each Sangya's life area, parallel to
#: ``SANGYA_LIFE_AREAS[key]["domain"]``.
#:
#: Guarding the graha keywords alone would not keep the two-tier promise:
#: Vainashika's classical area is "Ruin, loss of capital, complete breakdown
#: and severe vulnerability", which is blunter in a forecast than any graha
#: phrasing it would be paired with. The area is softened for forecasts for
#: the same reason the keywords are, and left classical everywhere else.
GUARDED_SANGYA_AREAS: dict[str, str] = {
    "janma": "general well-being, physical energy and vitality",
    "karma": "work, standing and professional authority",
    "sanghatika": "money, partnerships and mental load",
    "samudayika": "overall financial and social stability",
    "adhana": "career foundation, home base and root stability",
    "vainashika": "capital, reserves and financial resilience",
    "manasa": "mental state, sleep and clarity of decision",
    "jati": "family, community standing and physical vitality",
    "desha": "travel, property and the wider environment",
    "abhisheka": "recognition, advancement and protection",
}


@dataclass(frozen=True)
class EventSignature:
    """One graha striking one Sangya — the event category of a single hit."""

    sangya_key: str
    sangya_name: str
    #: The Sangya's classical life-area, from ``SANGYA_LIFE_AREAS[key]["domain"]``.
    classical_area: str
    graha: str
    #: "benefic" | "malefic", from ``GRAHA_VEDHA_RULES``.
    nature: str
    classical_keywords: str
    guarded_keywords: str
    #: Forecast-safe restatement of ``classical_area``.
    guarded_area: str

    @property
    def is_adverse(self) -> bool:
        return self.nature == "malefic"

    def describe(self, direction: TemporalDirection) -> str:
        """The event category, worded for the given temporal direction."""
        if direction is TemporalDirection.FUTURE:
            return f"{self.guarded_keywords} — bearing on {self.guarded_area}"
        return f"{self.classical_keywords} — bearing on {self.classical_area.lower()}"

    @property
    def label(self) -> str:
        """Compact machine/UI label, e.g. 'vainashika:mars'."""
        return f"{self.sangya_key}:{self.graha}"


def build_signature(sangya_key: str, graha: str) -> EventSignature:
    """Assemble the signature for a (Sangya, graha) pair.

    Imported lazily from ``sbc_vedha_engine`` so this module stays free of
    a service-layer import at module load, which would make it unusable
    from other pure modules.
    """
    from apps.api.services.sbc_vedha_engine import GRAHA_VEDHA_RULES, SANGYA_LIFE_AREAS

    key = sangya_key.strip().lower()
    planet = graha.strip().lower()

    sangya = SANGYA_LIFE_AREAS.get(key)
    if sangya is None:
        raise KeyError(f"Unknown Sangya {sangya_key!r}")
    rule = GRAHA_VEDHA_RULES.get(planet)
    if rule is None:
        raise KeyError(f"Unknown graha {graha!r}")
    guarded = GUARDED_KEYWORDS.get(planet)
    if guarded is None:
        raise KeyError(f"No guarded restatement authored for graha {graha!r}")
    guarded_area = GUARDED_SANGYA_AREAS.get(key)
    if guarded_area is None:
        raise KeyError(f"No guarded restatement authored for Sangya {sangya_key!r}")

    return EventSignature(
        sangya_key=key,
        sangya_name=sangya["name"],
        classical_area=sangya["domain"],
        graha=planet,
        nature=rule["nature"],
        classical_keywords=rule["keywords"],
        guarded_keywords=guarded,
        guarded_area=guarded_area,
    )


def signatures_for_point(
    sangya_key: str,
    grahas: Iterable[str],
) -> list[EventSignature]:
    """Signatures for every graha that struck one Sangya.

    Unknown grahas are skipped rather than raising: a Vedha summary may
    carry a display name this table does not recognise, and losing one
    signature is better than losing the whole window.
    """
    found: list[EventSignature] = []
    for graha in grahas:
        try:
            found.append(build_signature(sangya_key, graha))
        except KeyError:
            continue
    return found


def verify_guarded_keywords(policy: Optional[StancePolicy] = None) -> dict[str, list[str]]:
    """Return any guarded phrasing that would still break a forecast policy.

    Empty result means the guarded table is genuinely forecast-safe. Tests
    assert on this directly so a lapse fails at build time rather than
    being papered over by runtime redaction.
    """
    effective = policy or resolve_policy(TemporalDirection.FUTURE)
    problems: dict[str, list[str]] = {}
    for source in (GUARDED_KEYWORDS, GUARDED_SANGYA_AREAS):
        for name, text in source.items():
            violations = scan_text(text, effective, field_name=name)
            if violations:
                problems.setdefault(name, []).extend(v.term for v in violations)
    return problems
