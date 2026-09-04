"""
AstroOS — Admin Domain Objects (Module 23, Phase 1)

System health, user summaries, and module registry for the admin portal.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class ModuleHealth:
    """Status of one module."""

    module_name: str
    status: str  # "ok" | "warning" | "error"
    version: str
    message: str = ""


@dataclass(frozen=True)
class SystemStatus:
    """Aggregated health of the system."""

    status: str  # "healthy" | "degraded" | "unavailable"
    modules: dict[str, ModuleHealth] = field(default_factory=dict)
    ephemeris_mode: str = ""
    uptime_seconds: float = 0.0
    version: str = "1.0.0"


@dataclass(frozen=True)
class AdminUserSummary:
    """Lightweight user representation for admin listing."""

    id: uuid.UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
