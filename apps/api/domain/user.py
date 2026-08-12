"""
AstroOS — User Aggregate Root (Domain Layer)

Pure Python dataclass. No ORM, no HTTP, no framework dependency.
This is the canonical representation of a User in the domain.
All business invariants live here.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass(frozen=True)
class UserId:
    """Typed value object for User identity. Prevents primitive obsession."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class User:
    """
    User aggregate root.

    Business rules enforced here:
    - Email must be lowercase and stripped.
    - A suspended user cannot generate tokens.
    - Role elevation requires explicit intent (no default admin).
    """

    id: UserId
    email: str
    display_name: str
    hashed_password: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        self.email = self.email.lower().strip()
        if not self.email:
            raise ValueError("User email must not be empty.")
        if not self.display_name.strip():
            raise ValueError("User display_name must not be empty.")

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and self.deleted_at is None

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def assert_can_authenticate(self) -> None:
        """Raise if this user is not allowed to receive auth tokens."""
        if not self.is_active:
            raise PermissionError(
                f"User {self.email} cannot authenticate: status={self.status.value}"
            )

    def record_login(self, now: datetime) -> "User":
        """Return a new User with updated last_login_at (domain event side-effect)."""
        self.last_login_at = now
        return self
