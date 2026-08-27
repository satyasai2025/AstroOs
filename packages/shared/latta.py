"""
AstroOS — Latta Dosha (लत्ता, "the kick")

A planet standing in one nakshatra is held to strike — *kick* — a
second nakshatra a fixed number of stars away. When the struck star is
the native's Janma Nakshatra (or the star of a muhurta being selected),
that star is under Latta Dosha for as long as the planet stays put.
Unlike SBC Vedha, which needs a direction and a path, Latta is a single
fixed offset per planet, which makes it cheap to compute and easy to
converge with the machinery already in this package.

**Sourcing tier — read this before trusting output.** Two distinct
bodies of material sit behind this technique, and they are *not* at the
same confidence level in this repo:

1. **The per-planet offset table below** (Sun 12 forward, Mars 3
   forward, Jupiter 6 forward, Saturn 8 forward, Moon 22 forward;
   Mercury 7 backward, Venus 5 backward, Rahu 9 backward). These are
   widely and consistently attested across the classical Muhurta
   literature, Phaladeepika Ch. XXVI among them. **They have not been
   verified line-by-line against a specific edition inside this
   repository** — ``knowledge/sources/texts/phaladeepika.yaml`` carries
   the source's metadata but not its verse text. This is therefore the
   same honesty tier the Ashtakavarga bindu tables sit at:
   standard-table-based, not independently verified here. Every rule
   carries that status on its own record (:attr:`LattaRule.verification`)
   rather than in a comment, so callers can surface it.

2. **The seven named star-combinations** — Vidyunmukha, Shula,
   Sannipata, Ulka, Kampa, Vajra, Nirghata — which the same chapter
   reckons from the transiting Sun. Their offsets are **not
   reconstructed here and are deliberately left empty**
   (:data:`NAMED_COMBINATIONS`). Inventing a plausible-looking table
   would be indistinguishable from a sourced one after the fact, which
   is the failure mode this project's sourcing discipline exists to
   prevent. See :data:`NAMED_COMBINATIONS_STATUS`.

**Output discipline.** The classical predictive text for Latta is blunt
and event-specific in a way this codebase never reproduces. This module
therefore emits a *life domain* per hit and nothing narrower; the
mapping from a struck star to what may actually be said about it is
:mod:`packages.shared.temporal_stance`'s job, and
``latta_engine.LattaEngine`` wires the two together. Nothing in this
module produces prose.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Optional

from packages.shared.disclosed_events import LifeDomain
from packages.shared.enums import Nakshatra

_STANDARD_27: list[str] = [n.value for n in Nakshatra]


class LattaDirection(str, Enum):
    """Which way the kick is counted from the planet's own star."""

    #: Counted in the direction of the zodiac. Traditionally read as the
    #: harsher of the two, the planet striking what lies ahead of it.
    FORWARD = "forward"
    #: Counted against the zodiac.
    BACKWARD = "backward"


class VerificationStatus(str, Enum):
    """How well-grounded a given rule is *in this repository*."""

    #: Cross-checked against primary text held in this repo.
    VERIFIED = "verified"
    #: Standard across the classical literature; no primary text here to check against.
    STANDARD_UNVERIFIED = "standard_unverified"
    #: Known to exist, offsets not reconstructed. Never computed.
    NEEDS_SOURCE = "needs_source"


@dataclass(frozen=True)
class LattaRule:
    """One planet's fixed kick."""

    planet: str
    #: Stars from the planet's own nakshatra, counted inclusively — an
    #: offset of 12 means the planet's own star is 1 and the struck star is 12.
    offset: int
    direction: LattaDirection
    #: Life areas the tradition associates with this planet's Latta. Kept at
    #: domain granularity on purpose; see the module docstring.
    domains: frozenset[LifeDomain]
    #: Malefic Latta is read as materially heavier than benefic Latta.
    is_malefic: bool
    verification: VerificationStatus = VerificationStatus.STANDARD_UNVERIFIED

    def __post_init__(self) -> None:
        if self.offset < 1:
            raise ValueError("Latta offset is an inclusive count and must be >= 1")


LATTA_RULES: dict[str, LattaRule] = {
    "sun": LattaRule(
        planet="sun",
        offset=12,
        direction=LattaDirection.FORWARD,
        domains=frozenset({LifeDomain.HEALTH, LifeDomain.CAREER}),
        is_malefic=True,
    ),
    "moon": LattaRule(
        planet="moon",
        offset=22,
        direction=LattaDirection.FORWARD,
        domains=frozenset({LifeDomain.MENTAL_WELLBEING, LifeDomain.FAMILY}),
        is_malefic=False,
    ),
    "mars": LattaRule(
        planet="mars",
        offset=3,
        direction=LattaDirection.FORWARD,
        domains=frozenset({LifeDomain.HEALTH, LifeDomain.RELATIONSHIP}),
        is_malefic=True,
    ),
    "mercury": LattaRule(
        planet="mercury",
        offset=7,
        direction=LattaDirection.BACKWARD,
        domains=frozenset({LifeDomain.CAREER, LifeDomain.EDUCATION}),
        is_malefic=False,
    ),
    "jupiter": LattaRule(
        planet="jupiter",
        offset=6,
        direction=LattaDirection.FORWARD,
        domains=frozenset({LifeDomain.FINANCE, LifeDomain.SPIRITUAL}),
        is_malefic=False,
    ),
    "venus": LattaRule(
        planet="venus",
        offset=5,
        direction=LattaDirection.BACKWARD,
        domains=frozenset({LifeDomain.RELATIONSHIP, LifeDomain.FINANCE}),
        is_malefic=False,
    ),
    "saturn": LattaRule(
        planet="saturn",
        offset=8,
        direction=LattaDirection.FORWARD,
        domains=frozenset({LifeDomain.HEALTH, LifeDomain.CAREER, LifeDomain.FINANCE}),
        is_malefic=True,
    ),
    "rahu": LattaRule(
        planet="rahu",
        offset=9,
        direction=LattaDirection.BACKWARD,
        domains=frozenset({LifeDomain.MENTAL_WELLBEING, LifeDomain.OTHER}),
        is_malefic=True,
    ),
    # Ketu carries no Latta in the standard list. Its absence is the
    # sourced position, not an omission waiting to be filled in.
}


#: Latta reckoned from the transiting Sun, named in the same chapter.
#: Intentionally empty — see the module docstring.
NAMED_COMBINATIONS: dict[str, int] = {}

NAMED_COMBINATIONS_STATUS = {
    "status": VerificationStatus.NEEDS_SOURCE,
    "names": (
        "vidyunmukha",
        "shula",
        "sannipata",
        "ulka",
        "kampa",
        "vajra",
        "nirghata",
    ),
    "blocked_on": (
        "Phaladeepika Ch. XXVI slokas 42-47 verse text. The repo holds the source's "
        "metadata (knowledge/sources/texts/phaladeepika.yaml) but not its verses, so the "
        "offset each name corresponds to cannot be reconstructed without inventing it."
    ),
    "note": (
        "The classical predictive wording attached to these names is blunt and "
        "event-specific. When the offsets are sourced, the output must still route "
        "through the temporal-stance policy like every other sensitive-timing call."
    ),
}


@dataclass(frozen=True)
class LattaHit:
    """A planet's kick landing on a star the caller cares about."""

    planet: str
    #: The star the planet is standing in.
    from_nakshatra: str
    #: The star being struck.
    struck_nakshatra: str
    offset: int
    direction: LattaDirection
    is_malefic: bool
    domains: frozenset[LifeDomain]
    verification: VerificationStatus

    @property
    def is_severe(self) -> bool:
        """Malefic planet kicking forward — the heavier reading of the two axes."""
        return self.is_malefic and self.direction is LattaDirection.FORWARD


def latta_target(planet: str, from_nakshatra: str) -> str:
    """The nakshatra struck by ``planet`` while it stands in ``from_nakshatra``.

    Offsets count inclusively in the Vedic manner: the planet's own star is 1,
    so the Sun's 12th-star Latta lands eleven positions further along.
    """
    rule = LATTA_RULES.get(planet.strip().lower())
    if rule is None:
        raise KeyError(f"No Latta rule for planet {planet!r}")

    try:
        index = _STANDARD_27.index(from_nakshatra.strip().lower())
    except ValueError as exc:
        raise ValueError(f"Unknown 27-system nakshatra token {from_nakshatra!r}") from exc

    step = rule.offset - 1
    if rule.direction is LattaDirection.BACKWARD:
        step = -step
    return _STANDARD_27[(index + step) % 27]


def check_latta(
    target_nakshatra: str,
    transit_nakshatras: Mapping[str, str],
) -> list[LattaHit]:
    """Every planet whose Latta currently lands on ``target_nakshatra``.

    ``transit_nakshatras`` maps planet token -> the 27-system nakshatra it is
    transiting. Planets with no Latta rule (Ketu) are skipped rather than
    treated as an error, since a caller passing a full graha set is normal.
    Hits are returned severe-first.
    """
    target = target_nakshatra.strip().lower()
    if target not in _STANDARD_27:
        raise ValueError(f"Unknown 27-system nakshatra token {target_nakshatra!r}")

    hits: list[LattaHit] = []
    for planet, nakshatra in transit_nakshatras.items():
        rule = LATTA_RULES.get(planet.strip().lower())
        if rule is None:
            continue
        struck = latta_target(rule.planet, nakshatra)
        if struck != target:
            continue
        hits.append(
            LattaHit(
                planet=rule.planet,
                from_nakshatra=nakshatra.strip().lower(),
                struck_nakshatra=struck,
                offset=rule.offset,
                direction=rule.direction,
                is_malefic=rule.is_malefic,
                domains=rule.domains,
                verification=rule.verification,
            )
        )

    hits.sort(key=lambda h: (h.is_severe, h.is_malefic), reverse=True)
    return hits


def afflicted_domains(hits: Iterable[LattaHit]) -> frozenset[LifeDomain]:
    """Union of the life domains struck across a set of hits."""
    domains: set[LifeDomain] = set()
    for hit in hits:
        domains |= hit.domains
    return frozenset(domains)
