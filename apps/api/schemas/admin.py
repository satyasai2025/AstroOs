"""
AstroOS — Admin API Schemas (Module 23 — HTTP surface)

Pydantic request/response models for the Admin Portal — system health,
module registry, and user management. Thin DTO layer over
apps/api/domain/admin.py, same convention as schemas/events.py.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# ── System status ─────────────────────────────────────────────────────────────


class ModuleHealthResponse(BaseModel):
    module_name: str
    status: str
    version: str
    message: str = ""


class SystemStatusResponse(BaseModel):
    status: str
    modules: dict[str, ModuleHealthResponse]
    ephemeris_mode: str
    version: str


class ModuleRegistryResponse(BaseModel):
    modules: dict[str, str]


# ── Users ─────────────────────────────────────────────────────────────────────


class AdminUserSummaryResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: Optional[datetime]
    last_login_at: Optional[datetime]


class AdminUserListResponse(BaseModel):
    users: list[AdminUserSummaryResponse]
    total: int


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(description="One of the UserRole enum values, e.g. 'admin', 'user'.")
