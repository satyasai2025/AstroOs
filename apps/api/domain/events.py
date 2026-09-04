"""
AstroOS — Event Domain Objects (Module 14, Phase 1)

Four objects, one clear responsibility each — per the Module 14 Design
Audit (approved, including the two post-approval refinements: the
`NatalSnapshot` grouping object and `EventAnalysis.analysis_version`):

  - NatalSnapshot: the reusable, once-per-chart bundle of natal Yoga,
    Shadbala, and Ashtakavarga results plus the D1 chart itself. Date-
    invariant — the same instance is shared across every EventRecord
    belonging to one chart, never recomputed per event.
  - EventRecord: one recorded life event, mirroring the `events` table
    (migration 0002) exactly.
  - EventAstrologicalContext: the assembled, per-event snapshot — active
    Dasha periods and Transit positions AS OF the event's date, plus a
    reference to the chart's NatalSnapshot (not a copy of its fields).
  - EventAnalysis: EventRecord + EventAstrologicalContext + (optionally)
    RuleEngine results, consumed as-is and never re-derived here, plus
    the standardized `event.*` Facts this module generates for
    downstream consumers.

Pure Python dataclasses — no ORM/Pydantic dependency, matching the
convention in every other domain module in this codebase
(domain/dasha.py, domain/transit.py, domain/yoga.py, etc.).

Nothing in this module performs an astrology calculation. Every
Dasha/Transit/Yoga/Shadbala/Ashtakavarga value here is produced
elsewhere (DashaEngine, TransitEngine, YogaEngine, ShadbalaEngine,
AshtakavargaEngine) and reused as-is.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from apps.api.domain.ashtakavarga import BhinnashtakavargaResult, SarvashtakavargaResult
from apps.api.domain.dasha import DashaPeriod
from apps.api.domain.facts import Fact
from apps.api.domain.horoscope import D1Chart
from apps.api.domain.rules import RuleResult
from apps.api.domain.shadbala import BalaComponentResult
from apps.api.domain.transit import TransitPlanetResult
from apps.api.domain.yoga import YogaResult


@dataclass(frozen=True)
class NatalSnapshot:
    """
    Everything about a person's astrological makeup that does NOT change
    with any individual event's date, grouped into one reusable object.

    Built once per chart by whatever calls EventEngine (a future router,
    a batch job, etc.) — EventEngine itself never constructs one, only
    consumes it. Passing the SAME NatalSnapshot instance to every
    EventRecord belonging to one chart is what actually prevents
    Yoga/Shadbala/Ashtakavarga from being silently recomputed per event;
    see the Module 14 Design Audit §3.1 for the rationale.

    `shadbala_components` is a merged dict of whatever
    ShadbalaEngine.compute_*_components() methods the caller ran for
    this chart (e.g. Phase 1 + Phase 2 + Sthana Bala) — component_id ->
    per-planet results, same shape ShadbalaEngine's own methods return.
    Which subset is present depends entirely on how that ShadbalaEngine
    instance was wired; NatalSnapshot makes no assumption about
    completeness, same "explicit gap, not silent" discipline as
    ShadbalaEngine.not_yet_implemented_components() itself.
    """

    chart_id: uuid.UUID
    chart: D1Chart
    yogas: tuple[YogaResult, ...]
    shadbala_components: dict[str, list[BalaComponentResult]]
    bhinnashtakavarga: tuple[BhinnashtakavargaResult, ...]
    sarvashtakavarga: SarvashtakavargaResult
    snapshot_version: str = "1.0"


def _capitalize_title(title: str) -> str:
    """Capitalize each word in a title/name string."""
    return " ".join(word.capitalize() for word in title.strip().split())


@dataclass(frozen=True)
class EventRecord:
    """
    One recorded life event. Mirrors the `events` table (migration
    0002) column-for-column — no invented fields, no renaming.
    `category` is a free string, informally cross-referenced against
    Module 12's 7 Ontology `Event` categories (marriage, career,
    education, health, progeny, wealth, longevity) for consistency,
    but not FK-enforced, matching that ontology's own "starting
    vocabulary, not exhaustive" stance.
    """

    id: uuid.UUID
    chart_id: uuid.UUID
    event_date: date
    title: str
    user_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_verified: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _capitalize_title(self.title))


@dataclass(frozen=True)
class EventAstrologicalContext:
    """
    The assembled, as-of-`event_date` (Dasha/Transit) plus as-of-birth
    (Yoga/Shadbala/Ashtakavarga, via NatalSnapshot) context for one
    event. Every field is a direct reuse of an existing result type or
    NatalSnapshot itself — no new result shapes duplicating engine
    output.
    """

    event_id: uuid.UUID
    chart_id: uuid.UUID
    active_dashas: dict[str, tuple[DashaPeriod, ...]]
    transits: tuple[TransitPlanetResult, ...]
    natal_snapshot: NatalSnapshot
    context_version: str = "1.0"


@dataclass(frozen=True)
class EventAnalysis:
    """
    Top-level object: EventRecord + EventAstrologicalContext + (if
    available) RuleEngine results, consumed as-is, + standardized
    `event.*` Facts for downstream modules (Research/Statistics/
    Knowledge/AI — none built yet).

    `rule_results` is None (not an empty tuple) when no RuleEngine was
    supplied for this analysis, so a caller can distinguish "no rules
    matched" from "rules weren't run."

    No score, no ranking, no causal language anywhere in this object —
    it states what was active; it asserts nothing about likelihood or
    causation. Same descriptive-not-predictive discipline already
    enforced for Arishta Yoga results (Module 8 Phase 2).

    `analysis_version` (added on refinement) identifies which version
    of EventEngine.analyze()'s own assembly logic produced this
    EventAnalysis — independent of context_version (versions only the
    context-assembly step) and independent of any individual rule's own
    rule_version. Same auditability convention as rule_version
    (Module 8/13) and component_id's rule_version (Module 9).
    """

    event: EventRecord
    context: EventAstrologicalContext
    event_facts: tuple[Fact, ...] = field(default_factory=tuple)
    rule_results: Optional[tuple[RuleResult, ...]] = None
    analysis_version: str = "1.0"