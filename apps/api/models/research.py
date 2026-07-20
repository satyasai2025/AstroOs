"""
AstroOS — Research Models

New models for Phase I.4 Research Tools:
- ResearchModeSettingModel: per-user research mode toggle
- ResearchQueryLogModel: query/action log for reproducibility
- HypothesisValidationModel: hypothesis flagging/confirmation workflow

These are separate from the main astrology models for modularity.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.models.base import AstroBase


class ResearchModeSettingModel(AstroBase):
    """
    Per-user research mode toggle.

    When enabled, all research queries/analyses are logged for
    reproducibility. Persists across sessions.
    """

    __tablename__ = "research_mode_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<ResearchModeSetting user={self.user_id} enabled={self.enabled}>"


class ResearchQueryLogModel(AstroBase):
    """
    Log entry for a research query or action when research mode is enabled.

    Captures the full request parameters, response summary, and duration
    to enable full reproducibility of research analyses.
    """

    __tablename__ = "research_query_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        doc="Action type: workflow_analyze, research_query, export, "
            "hypothesis_generate, snapshot_capture, snapshot_compare, hypothesis_validate",
    )
    request_payload: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}",
        doc="JSON-serialised request parameters.",
    )
    response_summary: Mapped[str] = mapped_column(
        String(500), nullable=False, default="",
        doc="Brief summary of the response for searchability.",
    )
    duration_ms: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        doc="Execution duration in milliseconds.",
    )

    def __repr__(self) -> str:
        return (
            f"<ResearchQueryLog {self.action} "
            f"user={self.user_id} at {self.created_at}>"
        )


class HypothesisValidationModel(AstroBase):
    """
    A hypothesis flagged for human review/confirmation.

    When the AI generates a hypothesis, a researcher can flag it for
    human confirmation. A human reviewer then confirms or rejects it,
    recording notes for the research record.
    """

    __tablename__ = "hypothesis_validations"

    hypothesis_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        doc="The HypothesisTemplate ID (e.g. 'HYP-001').",
    )
    chart_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("birth_charts.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    domain: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    hypothesis_data: Mapped[str] = mapped_column(
        Text, nullable=False, default="{}",
        doc="JSON-serialised full hypothesis object.",
    )
    ai_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        doc="True if AI-generated, False if manually created.",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        doc="pending | confirmed | rejected | needs_revision",
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<HypothesisValidation {self.hypothesis_id} "
            f"status={self.status} project={self.project_id}>"
        )
