"""
AstroOS — User ORM Model

Maps the `users` and `user_sessions` tables to Python objects.
The ORM model is an infrastructure concern; the domain.User is the authoritative representation.
Repositories convert between the two.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase
from apps.api.domain.user import UserRole, UserStatus


class UserModel(AstroBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(320),  # RFC 5321 max
        unique=True,
        index=True,
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        # values_callable ensures SQLAlchemy stores enum.value ("researcher")
        # not enum.name ("RESEARCHER") — must match PostgreSQL enum literals.
        SAEnum(
            UserRole,
            name="user_role",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=UserRole.RESEARCHER,
        server_default=UserRole.RESEARCHER.value,
    )

    status: Mapped[UserStatus] = mapped_column(
        SAEnum(
            UserStatus,
            name="user_status",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
        server_default="UTC",
        doc="IANA timezone name (e.g. 'Asia/Kolkata') used to interpret "
        "date/time inputs the user enters without an explicit offset.",
    )

    sessions: Mapped[List["UserSessionModel"]] = relationship(
        "UserSessionModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    user_plan: Mapped[Optional["UserPlanModel"]] = relationship(
        "UserPlanModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserSessionModel(AstroBase):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    refresh_token_jti: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="JWT ID of the refresh token — uniquely identifies this session.",
    )

    device_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="sessions")

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


class PasswordResetTokenModel(AstroBase):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 hex digest of the reset token — never the raw token.",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_used(self) -> bool:
        return self.used_at is not None


class AuditLogModel(AstroBase):
    __tablename__ = "audit_log"

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        doc="User who performed the action, NULL for system actions.",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    resource_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON blob with additional event context. Not indexed.",
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
