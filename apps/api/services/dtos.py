"""
AstroOS — Service-Layer Data Transfer Objects

Plain Python dataclasses that cross the service boundary.
No Pydantic, no SQLAlchemy, no FastAPI here.
Routers convert these to HTTP response schemas; services never touch schemas.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class AuthTokensDTO:
    """Token pair returned after successful auth."""

    access_token: str
    refresh_token: str
    expires_in: int  # seconds


@dataclass(frozen=True)
class UserDTO:
    """Read-only projection of a User for API responses."""

    id: UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: datetime
    last_login_at: Optional[datetime]
    timezone: str


@dataclass(frozen=True)
class AuthResultDTO:
    """Returned from register/login operations."""

    user: UserDTO
    tokens: AuthTokensDTO
