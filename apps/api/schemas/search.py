"""
AstroOS — Unified Search Schemas

Defines request/response models for Phase 9 keyword search across charts,
knowledge base, and research projects.
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UnifiedSearchRequest(BaseModel):
    """Request payload for unified search across all domains."""
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=15, ge=1, le=50)


class SearchResultChart(BaseModel):
    """A birth chart search result."""
    type: str = "chart"
    id: UUID
    title: str  # subject_name
    subtitle: Optional[str] = None  # place_name
    snippet: str  # lagna_rashi + moon_nakshatra
    created_at: datetime
    href: str


class SearchResultKnowledge(BaseModel):
    """A knowledge base search result (book, verse, rule, karakatva)."""
    type: str
    id: UUID
    title: str
    snippet: str
    relevance: float
    book_title: Optional[str] = None
    tradition: Optional[str] = None
    href: str


class SearchResultProject(BaseModel):
    """A research project search result."""
    type: str = "project"
    id: UUID
    title: str
    snippet: str
    created_at: datetime
    href: str


# Union type for all possible results
SearchResult = SearchResultChart | SearchResultKnowledge | SearchResultProject


class UnifiedSearchResponse(BaseModel):
    """Response payload for unified search."""
    results: list[SearchResult]
    total: int
    query: str
    ai_enhanced: bool = False
    expanded_terms: list[str] = []
