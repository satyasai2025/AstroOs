"""
AstroOS — Shadbala Domain Objects (Module 9)

Unlike Yoga Engine's YogaResult (boolean presence + satisfied/missing),
every Shadbala component is a continuous numeric contribution in
Shashtiamsas (60ths of a Rupa). BalaComponentResult adapts the same
auditability spirit — stable id, rule_version, and a trace — to numeric
data: value instead of is_present, trace instead of satisfied/missing
(there's nothing to "not satisfy" about a graded number).

Pure Python dataclasses — no ORM/Pydantic dependency, matching every
other domain module in this codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BalaComponentResult:
    """
    One Shadbala component's contribution for one planet.

    component_id is stable and shared across all planets a given
    calculator scores (e.g. "SHADBALA-NAISARGIKA" applies to all 7
    classical grahas) — unlike Yoga Engine's per-yoga-variant ids, a bala
    component is one rule applied uniformly, not a family of named
    variants, so one id per component is the natural granularity here.
    """
    component_id: str
    component_name: str
    rule_version: str
    planet: str
    value_shashtiamsas: float
    trace: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ShadbalaTotal:
    """Sum of all computed components for one planet, once the full engine (Phase 4) exists."""
    planet: str
    total_shashtiamsas: float
    components: tuple[BalaComponentResult, ...] = field(default_factory=tuple)
