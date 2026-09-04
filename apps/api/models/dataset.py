"""
AstroOS — Dataset ORM Model

Represents an imported dataset record in the platform. Created as a
post-import step by DatasetService.record_import() after the file-based
import pipeline completes successfully.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.models.base import AstroBase


class DatasetModel(AstroBase):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="External dataset identifier (e.g. ASTRO-RS-COHORT-v2.0.0)",
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_file: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    field_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    quality_tier: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    lifecycle_stage: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Draft",
        comment="Draft | Candidacy | Stable | Deprecated | Archived",
    )
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="Relative path to the exported data file",
    )
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
