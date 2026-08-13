"""
AstroOS — Technique Import: Domain Objects

The intermediate representation that flows through the generic import pipeline:

    Source -> Extraction -> Normalization -> Rule creation -> Provenance
           -> Validation -> Technique Repository

These are deliberately SEPARATE from the runtime domain (domain/technique.py,
domain/rules.py): a `RawTechnique` is what an extractor proposes from a source,
BEFORE it becomes an evaluable TechniqueDefinition + registered RuleDefinitions.
Keeping them apart is what lets extraction distinguish "what the source states"
(`origin="explicit"`) from "what the extractor derived" (`origin="derived"`)
without that distinction leaking into — or being lost by — the runtime model.

Pure dataclasses; no ORM/Pydantic, matching domain/technique.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceType(str, Enum):
    PDF = "pdf"
    YOUTUBE = "youtube"
    BOOK = "book"
    CLASSICAL_TEXT = "classical_text"
    RESEARCH_PAPER = "research_paper"
    NOTES = "notes"
    USER = "user"
    RESEARCH = "research"
    STRUCTURED = "structured"  # already-structured JSON payload (no extraction needed)


class RuleOrigin(str, Enum):
    """Whether the source explicitly states a rule, or the extractor derived it.

    This maps 1:1 onto ProvenanceStatus at the Provenance stage
    (EXPLICIT -> SOURCE_DERIVED, DERIVED -> DERIVED) and MUST be preserved: a
    derived rule is never presented as a source fact.
    """

    EXPLICIT = "explicit"
    DERIVED = "derived"


@dataclass(frozen=True)
class TechniqueSource:
    """One raw input to the pipeline."""

    source_type: SourceType
    reference: str                    # citation / URL / filename
    content: str = ""                 # raw text (transcript, extracted PDF text, ...)
    excerpt: str | None = None        # the specific relevant excerpt, if known
    notes: str | None = None
    # For SourceType.STRUCTURED, a ready-made RawTechnique payload as a dict.
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class RawRule:
    """A rule as proposed by an extractor, before normalization/registration.

    `conditions` is a list of the serialized condition dicts understood by
    services/rule_serialization.py (condition/group trees). Normalization
    rewrites fact_keys/operators inside these dicts; rule creation deserializes
    them into domain/rules.py objects. No evaluation logic lives here.
    """

    rule_id: str
    name: str
    conditions: tuple[dict[str, Any], ...]
    origin: RuleOrigin = RuleOrigin.EXPLICIT
    role: str = "primary"             # RuleRole value
    priority: int = 1
    category: str = "imported"
    source_text: str = ""
    explanation: str = ""
    derived_facts: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    source_reference: str = ""


@dataclass(frozen=True)
class RawTechnique:
    """A technique as proposed by an extractor, before it is built + persisted."""

    technique_id: str
    name: str
    version: int = 1
    description: str = ""
    tradition: str = ""
    objective: str = ""
    source_references: tuple[str, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    rules: tuple[RawRule, ...] = field(default_factory=tuple)
    unresolved_inconsistencies: tuple[str, ...] = field(default_factory=tuple)
    # Optional pre-computed required inputs; normalization fills this if empty.
    required_inputs: tuple[str, ...] = field(default_factory=tuple)
