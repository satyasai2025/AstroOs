"""
AstroOS — Generated Report History ORM Model (Phase 10)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class ReportTierType(str, Enum):
    FREE_2PAGE = "free_2page"
    PRO_5PAGE = "pro_5page"
    RESEARCH_DOSSIER = "research_dossier"


class ReportHistoryModel(AstroBase):
    """
    Log of generated and downloadable PDF/HTML narrative reports.
    """

    __tablename__ = "report_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chart_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("birth_charts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        server_default=text("'Subject'"),
    )
    report_tier: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=ReportTierType.FREE_2PAGE.value,
        index=True,
    )
    export_format: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default=text("'pdf'"),
    )
    page_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    document_content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    download_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index("ix_report_history_user_tier", "user_id", "report_tier"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReportHistoryModel id={self.id} user_id={self.user_id} "
            f"tier={self.report_tier} format={self.export_format}>"
        )
