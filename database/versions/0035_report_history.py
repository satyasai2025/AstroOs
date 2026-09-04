"""Report history and downloads table (Phase 10)

Revision ID: 0035
Revises: 0034
Create Date: 2026-08-27 00:00:00.000000

Adds the Phase 10 report_history table:
  - report_history : log of generated tiered PDF/HTML reports
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0035"
down_revision: Union[str, None] = "0034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_history",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chart_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "subject_name", sa.String(100), nullable=False,
            server_default=sa.text("'Subject'"),
        ),
        sa.Column(
            "report_tier", sa.String(32), nullable=False,
            server_default=sa.text("'free_2page'"),
        ),
        sa.Column(
            "export_format", sa.String(10), nullable=False,
            server_default=sa.text("'pdf'"),
        ),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("document_content", sa.Text(), nullable=True),
        sa.Column("download_url", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_report_history_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chart_id"], ["birth_charts.id"], name="fk_report_history_chart_id_birth_charts",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_report_history_user_id", "report_history", ["user_id"])
    op.create_index("ix_report_history_chart_id", "report_history", ["chart_id"])
    op.create_index("ix_report_history_tier", "report_history", ["report_tier"])
    op.create_index(
        "ix_report_history_user_tier", "report_history", ["user_id", "report_tier"]
    )


def downgrade() -> None:
    op.drop_index("ix_report_history_user_tier", table_name="report_history")
    op.drop_index("ix_report_history_tier", table_name="report_history")
    op.drop_index("ix_report_history_chart_id", table_name="report_history")
    op.drop_index("ix_report_history_user_id", table_name="report_history")
    op.drop_table("report_history")
