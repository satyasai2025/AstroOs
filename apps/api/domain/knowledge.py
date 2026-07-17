"""
AstroOS — Knowledge Domain Objects (Module 19, Phase 1)

Classical astrological knowledge base — books, verses, interpretation
rules, and significations (karakatvas).

Pure Python dataclasses — no ORM/Pydantic dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class KnowledgeReference:
    """
    Reusable citation object.

    Carried by KnowledgeRule and Karakatva to reference a source verse
    in the knowledge base without embedding raw citation fields.
    """

    book_id: uuid.UUID
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    edition: Optional[str] = None
    translator: Optional[str] = None


@dataclass(frozen=True)
class KnowledgeBook:
    """A classical astrology text."""

    id: uuid.UUID
    title: str
    author: Optional[str] = None
    language: Optional[str] = None
    period_ce: Optional[str] = None
    tradition: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class KnowledgeVerse:
    """One verse from a classical text, with translations."""

    id: uuid.UUID
    book_id: uuid.UUID
    original_text: str
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    commentary: Optional[str] = None


@dataclass(frozen=True)
class KnowledgeRule:
    """
    A classical interpretation rule.

    Distinct from Module 13's RuleDefinition — this is a knowledge-base
    entry, not an evaluable rule. May optionally reference its evaluable
    counterpart via rule_definition_id.
    """

    id: uuid.UUID
    title: str
    interpretation: str
    source: Optional[KnowledgeReference] = None
    rule_definition_id: Optional[str] = None
    tradition: Optional[str] = None
    confidence: Optional[float] = None


@dataclass(frozen=True)
class Karakatva:
    """
    A signification — e.g. "Sun signifies soul."

    Links a subject to a graha, sign, or house, optionally citing a
    source verse.
    """

    id: uuid.UUID
    subject: str
    graha: Optional[str] = None
    sign_id: Optional[int] = None
    house_number: Optional[int] = None
    tradition: Optional[str] = None
    source: Optional[KnowledgeReference] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class KnowledgeSearchQuery:
    """Structured search over the knowledge base."""

    text: str
    entity_type: Optional[str] = None  # "book" | "verse" | "rule" | "karakatva"
    book_id: Optional[uuid.UUID] = None
    tradition: Optional[str] = None
    graha: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class KnowledgeSearchResult:
    """Flat search result with match context."""

    entity_type: str
    entity_id: uuid.UUID
    title: str
    snippet: str
    relevance: float
    book_title: Optional[str] = None
    tradition: Optional[str] = None
