"""
AstroOS — RTCollab API Schemas (Phase IV, ADR-RTC-001)

Pydantic request/response models for session advertisement and discovery.
"""

from __future__ import annotations

import uuid
from typing import List

from pydantic import BaseModel, Field


class AdvertiseSessionRequest(BaseModel):
    """Request payload to start advertising a collaboration session on the LAN."""
    host_name: str = Field(min_length=1, max_length=100)
    port: int = Field(gt=0, le=65535)


class AdvertiseSessionResponse(BaseModel):
    session_id: str
    host_name: str
    port: int


class DiscoveredSessionResponse(BaseModel):
    session_id: str
    host_name: str
    address: str
    port: int


class DiscoveredSessionListResponse(BaseModel):
    sessions: List[DiscoveredSessionResponse]
