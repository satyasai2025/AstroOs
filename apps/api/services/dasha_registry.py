"""
AstroOS — Dasha Engine Registry

Central catalog of every registered Dasha engine. Mirrors the structure of
jaimini_yoga_registry.py: engines register their metadata here instead of
the router/orchestrator containing a hardcoded per-system list. Adding a
future engine (Shoola, Lagna Kala, KP Vimshottari, ...) is a matter of
adding one register_dasha_engine(...) call — no router changes needed.

This registry does NOT perform any calculation itself; compute_method
names a method on DashaEngine (apps/api/services/dasha_engine.py), which
remains the single source of truth for dasha math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DashaCategory = Literal["nakshatra", "sign"]


@dataclass(frozen=True)
class DashaEngineDescriptor:
    """Metadata for one registered dasha system."""

    system: str
    label: str
    category: DashaCategory
    compute_method: str
    summary: str
    description: str


_REGISTRY: dict[str, DashaEngineDescriptor] = {}


def register_dasha_engine(descriptor: DashaEngineDescriptor) -> None:
    if descriptor.system in _REGISTRY:
        raise ValueError(f"Duplicate dasha system registered: {descriptor.system!r}")
    _REGISTRY[descriptor.system] = descriptor


def all_dasha_engines() -> list[DashaEngineDescriptor]:
    """All registered descriptors, in registration order."""
    return list(_REGISTRY.values())


def get_dasha_engine(system: str) -> DashaEngineDescriptor:
    """Look up a registered descriptor by system id. Raises KeyError if unknown."""
    return _REGISTRY[system]


def clear_registry() -> None:
    """Test-only: clear all registrations. Not used by production code paths."""
    _REGISTRY.clear()


# ── Built-in registrations ──────────────────────────────────────────────────
# These six systems are already implemented by DashaEngine.compute_*. Shoola,
# Lagna Kala, and KP Vimshottari are deferred — see AstroOS Dasha Module Spec.

register_dasha_engine(
    DashaEngineDescriptor(
        system="vimshottari",
        label="Vimshottari Dasha",
        category="nakshatra",
        compute_method="compute_vimshottari",
        summary="Vimshottari Dasha",
        description="120-year Parashara cycle based on Moon's nakshatra. Returns Mahadasha through Prana.",
    )
)
register_dasha_engine(
    DashaEngineDescriptor(
        system="yogini",
        label="Yogini Dasha",
        category="nakshatra",
        compute_method="compute_yogini",
        summary="Yogini Dasha",
        description="36-year cycle. Eight Yogini lords cycle through Moon's nakshatra sequence.",
    )
)
register_dasha_engine(
    DashaEngineDescriptor(
        system="ashtottari",
        label="Ashtottari Dasha",
        category="nakshatra",
        compute_method="compute_ashtottari",
        summary="Ashtottari Dasha",
        description="108-year cycle. Applied when Rahu occupies a Kendra or Trikona from Lagna.",
    )
)
register_dasha_engine(
    DashaEngineDescriptor(
        system="kalachakra",
        label="Kalachakra Dasha",
        category="sign",
        compute_method="compute_kalachakra",
        summary="Kalachakra Dasha",
        description="100-year sign-based cycle derived from Moon's Navamsha (D9) position.",
    )
)
register_dasha_engine(
    DashaEngineDescriptor(
        system="chara",
        label="Chara Dasha (Jaimini)",
        category="sign",
        compute_method="compute_chara",
        summary="Chara Dasha",
        description="Sign-based Jaimini dasha. Duration computed from D1 sign-lord placements.",
    )
)
register_dasha_engine(
    DashaEngineDescriptor(
        system="narayana",
        label="Narayana Dasha (Jaimini)",
        category="sign",
        compute_method="compute_narayana",
        summary="Narayana Dasha",
        description="Sign-based Jaimini dasha using Navamsha (D9) sign-lord placements.",
    )
)
