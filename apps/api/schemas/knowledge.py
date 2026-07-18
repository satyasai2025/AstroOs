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
    book_id: uuid.UUID
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    edition: Optional[str] = None
    translator: Optional[str] = None


# ── Books ─────────────────────────────────────────────────────────────────────


class BookCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author: Optional[str] = None
    language: Optional[str] = None
    period_ce: Optional[str] = None
    tradition: Optional[str] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class BookUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    author: Optional[str] = None
    language: Optional[str] = None
    period_ce: Optional[str] = None
    tradition: Optional[str] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class BookResponse(BaseModel):
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
    books: list[BookResponse]
    total: int


# ── Verses ────────────────────────────────────────────────────────────────────


class VerseCreateRequest(BaseModel):
    book_id: uuid.UUID
    original_text: str = Field(min_length=1)
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    commentary: Optional[str] = None
    version_comment: Optional[str] = None


class VerseUpdateRequest(BaseModel):
    original_text: Optional[str] = Field(default=None, min_length=1)
    chapter: Optional[int] = None
    verse_number: Optional[int] = None
    transliteration: Optional[str] = None
    translation: Optional[str] = None
    commentary: Optional[str] = None
    version_comment: Optional[str] = None


class VerseResponse(BaseModel):
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
    verses: list[VerseResponse]
    total: int


# ── Rules ─────────────────────────────────────────────────────────────────────


class RuleCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    interpretation: str = Field(min_length=1)
    verse_id: Optional[uuid.UUID] = None
    tradition: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    version_comment: Optional[str] = None


class RuleUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    interpretation: Optional[str] = Field(default=None, min_length=1)
    tradition: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    version_comment: Optional[str] = None


class RuleResponse(BaseModel):
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
    rules: list[RuleResponse]
    total: int


# ── Karakatvas ────────────────────────────────────────────────────────────────


class KarakatvaCreateRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    graha: Optional[str] = None
    sign_id: Optional[int] = None
    house_number: Optional[int] = None
    tradition: Optional[str] = None
    source_verse_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class KarakatvaUpdateRequest(BaseModel):
    subject: Optional[str] = Field(default=None, min_length=1, max_length=300)
    graha: Optional[str] = None
    sign_id: Optional[int] = None
    house_number: Optional[int] = None
    tradition: Optional[str] = None
    description: Optional[str] = None
    version_comment: Optional[str] = None


class KarakatvaResponse(BaseModel):
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
    karakatvas: list[KarakatvaResponse]
    total: int


# ── Search ────────────────────────────────────────────────────────────────────


class KnowledgeSearchRequest(BaseModel):
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
    entity_type: str
    entity_id: uuid.UUID
    title: str
    snippet: str
    relevance: float
    book_title: Optional[str] = None
    tradition: Optional[str] = None


class KnowledgeSearchResponse(BaseModel):
    results: list[KnowledgeSearchResultResponse]
    total: int
