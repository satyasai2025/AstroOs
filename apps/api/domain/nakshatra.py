"""
AstroOS — Nakshatra Knowledge Domain Objects

Represents the classical reference catalogue for the 27 nakshatras (lunar
mansions), loaded from the YAML files in knowledge/catalogues/nakshatras/.

This is reference data, not chart-specific — one object per nakshatra,
shared across every chart. It's the "Level 2 — Integrated Knowledge Base"
building block: Deity, Shakti, Nature (guna/gana/yoni/nadi), per-pada
Navamsha-sign mapping, karakatvas, and cited sources, all as actually
catalogued today. Several fields sketched in early vision docs (Varna,
Symbol, Animal, Tree, Motivation, Purushartha, Element, Direction, Gender)
are NOT in the current catalogue and are deliberately omitted here rather
than invented — they're a real gap to fill in a future catalogue revision,
not something this loader should fabricate.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NakshatraDeity:
    name: str
    description: str = ""
    attributes: tuple[str, ...] = ()


@dataclass(frozen=True)
class NakshatraShakti:
    name: str
    meaning: str = ""
    power: str = ""


@dataclass(frozen=True)
class NakshatraPada:
    """One of the 4 padas (quarters) of a nakshatra — each pada is
    classically tied to a specific Navamsha (D9) sign, in fixed rotation."""
    pada: int
    degrees: str
    rashi: str
    navamsha_rashi: str


@dataclass(frozen=True)
class NakshatraNature:
    temperament: str = ""
    guna: str = ""
    gana: str = ""
    yoni: str = ""
    nadi: str = ""


@dataclass(frozen=True)
class NakshatraSourceCitation:
    ref: str
    claim: str = ""
    confidence: str = "high"


@dataclass(frozen=True)
class NakshatraKnowledge:
    """Full classical reference entry for one nakshatra."""
    id: str
    name: str
    sequential: int = 0
    aliases: tuple[str, ...] = ()
    classical_name: str = ""
    devanagari: str = ""
    meaning: str = ""
    ruler: str = ""  # Vimshottari dasha lord, e.g. "ketu"
    starting_degree: float = 0.0
    ending_degree: float = 0.0
    rashi_span: tuple[str, ...] = ()
    padas: tuple[NakshatraPada, ...] = ()
    deity: NakshatraDeity | None = None
    shakti: NakshatraShakti | None = None
    nature: NakshatraNature | None = None
    karakatvas: tuple[str, ...] = ()
    compatible_nakshatras: tuple[str, ...] = ()
    incompatible_nakshatras: tuple[str, ...] = ()
    sources: tuple[NakshatraSourceCitation, ...] = ()
    notes: str = ""
