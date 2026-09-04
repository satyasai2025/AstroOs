"""
AstroOS — Event API Schemas (Module 14, Phase 3)

Pydantic request/response models. Converts to/from the domain
EventRecord in the router layer — schemas never leak into
EventRepository or EventEngine, same DTO-boundary discipline as
apps/api/schemas/auth.py.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _capitalize_title(title: str) -> str:
    """Capitalize each word in a title string."""
    return " ".join(word.capitalize() for word in title.strip().split())


class EventCreateRequest(BaseModel):
    """Request payload for event create operations."""
    chart_id: uuid.UUID
    event_date: date
    title: str = Field(min_length=1, max_length=300)
    user_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_verified: bool = False

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str) -> str:
        # Capitalize each word in title (event name)
        return _capitalize_title(v)


class EventUpdateRequest(BaseModel):
    """
    All fields optional — a PATCH. The router distinguishes "field
    omitted" from "field explicitly set to null" via
    `model_dump(exclude_unset=True)`, so only fields actually present
    in the request body are forwarded to EventRepository.update()
    (which itself distinguishes the same thing via its `_UNSET`
    sentinel). This lets a caller explicitly clear `description` or
    `category` (nullable fields) with `"description": null` while
    leaving every other field untouched.
    """

    title: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    category: Optional[str] = None
    is_verified: Optional[bool] = None
    event_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Capitalize each word in title (event name)
        return _capitalize_title(v)


class EventResponse(BaseModel):
    """Response payload describing event data."""
    id: uuid.UUID
    chart_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    event_date: date
    title: str
    description: Optional[str]
    category: Optional[str]
    is_verified: bool


class EventListResponse(BaseModel):
    """Response payload describing event list data."""
    events: list[EventResponse]
    total: int