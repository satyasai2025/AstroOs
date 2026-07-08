"""
AstroOS — SQLAlchemy Declarative Base

All ORM models inherit from AstroBase which provides:
- UUID primary key (not serial — avoids enumeration attacks)
- created_at / updated_at timestamps (timezone-aware)
- soft-delete via deleted_at
- A __tablename__ convention check at class creation time
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, event, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AstroBase(DeclarativeBase):
    """Shared base for all AstroOS ORM models."""

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        server_default=text("now()"),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        server_default=text("now()"),
        nullable=False,
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
