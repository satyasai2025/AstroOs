"""
AstroOS — Yoga Domain Objects (Module 8)

Two related but distinct objects:
  - YogaDefinition: the static, registered-once description of a yoga rule
    (its stable ID, source text, version, declared dependencies, and the
    evaluator function that checks a chart against it).
  - YogaResult: the per-chart output of running one YogaDefinition's
    evaluator against one YogaContext.

Pure Python dataclasses — no ORM/Pydantic dependency, matching the
convention in domain/horoscope.py, domain/ephemeris.py, domain/house.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Optional

YogaStrength = Literal["full", "partial", "cancelled"]


@dataclass(frozen=True)
class YogaDefinition:
    """
    Static, registered-once definition of one yoga rule.

    yoga_id format: {SOURCE}-{CATEGORY_CODE}-{NNN}, e.g. "BPHS-PM-001".
    Category codes: PM=Panch Mahapurusha, RY=Raja Yoga, DY=Dhana Yoga,
    NBRY=Neecha Bhanga Raja Yoga, CY=Chandra Yoga, NY=Nabhasa Yoga,
    ARY=Arishta Yoga, SY=Sanyasa Yoga, OMY=Other Major Yoga.
    Once assigned, a yoga_id is never reused or renumbered, even if the
    yoga is later deprecated — see the Yoga Engine Design Audit, §4.
    """
    yoga_id: str
    name: str
    category: str
    source_text: str
    rule_version: str
    requires: tuple[str, ...]
    evaluator: Callable[["YogaContext"], Optional["YogaResult"]]


@dataclass(frozen=True)
class YogaResult:
    """
    Result of evaluating one YogaDefinition against one chart.

    Returned for every registered yoga on every evaluated chart —
    including yogas that did NOT fire (is_present=False) — so a research
    query can ask "how close did this chart come" and not just "did it
    fire." See the Yoga Engine Design Audit, §4, for the rationale.
    """
    yoga_id: str
    name: str
    category: str
    source_text: str
    rule_version: str
    is_present: bool
    strength: Optional[YogaStrength]
    involved_planets: tuple[str, ...] = field(default_factory=tuple)
    involved_houses: tuple[int, ...] = field(default_factory=tuple)
    satisfied: tuple[str, ...] = field(default_factory=tuple)
    missing: tuple[str, ...] = field(default_factory=tuple)
    trace: tuple[str, ...] = field(default_factory=tuple)
