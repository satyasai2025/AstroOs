"""
AstroOS — Knowledge API Schemas (Module 19, Phase B — Versioned)

Pydantic request/response models for the Knowledge Engine's books,
verses, rules, karakatvas, and search endpoints. Thin DTO layer over
apps/api/domain/knowledge.py — same convention as schemas/events.py.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

# ── Shared ────────────────────────────────────────────────────────────────────


class KnowledgeReferenceResponse(BaseModel):
    """Response payload describing knowledge reference data."""
    book_id: uuid.UUID
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    edition: Optional[str] = None
    translator: Optional[str] = None


# ── Books ─────────────────────────────────────────────────────────────────────


class BookCreateRequest(BaseModel):
    """Request payload for book create operations."""
    title: str = Field(min_length=1, max_length=300)
    author: Optional[str] = None
    language: Optional[str] = None
    period_ce: Optional[str] = None
    tradition: Optional[str] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class BookUpdateRequest(BaseModel):
    """Request payload for book update operations."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    author: Optional[str] = None
    language: Optional[str] = None
    period_ce: Optional[str] = None
    tradition: Optional[str] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class BookResponse(BaseModel):
    """Response payload describing book data."""
    id: uuid.UUID
    title: str
    author: Optional[str]
    language: Optional[str]
    period_ce: Optional[str]
    tradition: Optional[str]
    description: Optional[str]
    version: int = 1
    version_comment: Optional[str] = None
    superseded_by: Optional[uuid.UUID] = None


class BookListResponse(BaseModel):
    """Response payload describing book list data."""
    books: list[BookResponse]
    total: int


# ── Verses ────────────────────────────────────────────────────────────────────


class VerseCreateRequest(BaseModel):
    """Request payload for verse create operations."""
    book_id: uuid.UUID
    original_text: str = Field(min_length=1)
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    commentary: Optional[str] = None
    version_comment: Optional[str] = None


class VerseUpdateRequest(BaseModel):
    """Request payload for verse update operations."""
    original_text: Optional[str] = Field(default=None, min_length=1)
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    commentary: Optional[str] = None
    version_comment: Optional[str] = None


class VerseResponse(BaseModel):
    """Response payload describing verse data."""
    id: uuid.UUID
    book_id: uuid.UUID
    original_text: str
    chapter: Optional[int]
    verse_number: Optional[int]
    transliteration: Optional[str]
    translation: Optional[str]
    commentary: Optional[str]
    version: int = 1
    version_comment: Optional[str] = None
    superseded_by: Optional[uuid.UUID] = None


class VerseListResponse(BaseModel):
    """Response payload describing verse list data."""
    verses: list[VerseResponse]
    total: int


# ── Rules ─────────────────────────────────────────────────────────────────────


class RuleCreateRequest(BaseModel):
    """Request payload for rule create operations."""
    title: str = Field(min_length=1, max_length=300)
    interpretation: str = Field(min_length=1)
    verse_id: Optional[uuid.UUID] = None
    tradition: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    version_comment: Optional[str] = None


class RuleUpdateRequest(BaseModel):
    """Request payload for rule update operations."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    interpretation: Optional[str] = Field(default=None, min_length=1)
    tradition: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    version_comment: Optional[str] = None


class RuleResponse(BaseModel):
    """Response payload describing rule data."""
    id: uuid.UUID
    title: str
    interpretation: str
    source: Optional[KnowledgeReferenceResponse]
    tradition: Optional[str]
    confidence: Optional[float]
    version: int = 1
    version_comment: Optional[str] = None
    superseded_by: Optional[uuid.UUID] = None


class RuleListResponse(BaseModel):
    """Response payload describing rule list data."""
    rules: list[RuleResponse]
    total: int


# ── Karakatvas ────────────────────────────────────────────────────────────────


class KarakatvaCreateRequest(BaseModel):
    """Request payload for karakatva create operations."""
    subject: str = Field(min_length=1, max_length=300)
    graha: Optional[str] = None
    sign_id: Optional[int] = None
    house_number: Optional[int] = None
    tradition: Optional[str] = None
    source_verse_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class KarakatvaUpdateRequest(BaseModel):
    """Request payload for karakatva update operations."""
    subject: Optional[str] = Field(default=None, min_length=1, max_length=300)
    graha: Optional[str] = None
    sign_id: Optional[int] = None
    house_number: Optional[int] = None
    tradition: Optional[str] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class KarakatvaResponse(BaseModel):
    """Response payload describing karakatva data."""
    id: uuid.UUID
    subject: str
    graha: Optional[str]
    sign_id: Optional[int]
    house_number: Optional[int]
    tradition: Optional[str]
    source: Optional[KnowledgeReferenceResponse]
    description: Optional[str]
    version: int = 1
    version_comment: Optional[str] = None
    superseded_by: Optional[uuid.UUID] = None


class KarakatvaListResponse(BaseModel):
    """Response payload describing karakatva list data."""
    karakatvas: list[KarakatvaResponse]
    total: int


# ── Search ────────────────────────────────────────────────────────────────────


class KnowledgeSearchRequest(BaseModel):
    """Request payload for knowledge search operations."""
    text: str = Field(min_length=1)
    entity_type: Optional[str] = Field(
        default=None, description="Restrict to one of: book, verse."
    )
    book_id: Optional[uuid.UUID] = None
    tradition: Optional[str] = None
    graha: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class KnowledgeSearchResultResponse(BaseModel):
    """Response payload describing knowledge search result data."""
    entity_type: str
    entity_id: uuid.UUID
    title: str
    snippet: str
    relevance: float
    book_title: Optional[str] = None
    tradition: Optional[str] = None


class KnowledgeSearchResponse(BaseModel):
    """Response payload describing knowledge search data."""
    results: list[KnowledgeSearchResultResponse]
    total: int
