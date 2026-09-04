"""Email and notification tables (Phase 7)

Revision ID: 0033
Revises: 0032
Create Date: 2026-08-27 00:00:00.000000

Adds the Phase 7 tables:
  - email_logs               : audit log & idempotency tracking for outbound emails
  - notification_preferences : user notification channel & opt-in/opt-out settings
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0033"
down_revision: Union[str, None] = "0032"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    # ── email_logs ──────────────────────────────────────────────────────────
    op.create_table(
        "email_logs",
        *_audit_columns(),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=True,
        ),
        sa.Column("recipient_email", sa.String(320), nullable=False),
        sa.Column("template_name", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column(
            "provider", sa.String(32), nullable=False,
            server_default=sa.text("'mock'"),
        ),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column(
            "status", sa.String(32), nullable=False,
            server_default=sa.text("'queued'"),
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_email_logs_user_id_users",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_email_logs_user_id", "email_logs", ["user_id"])
    op.create_index("ix_email_logs_recipient_email", "email_logs", ["recipient_email"])
    op.create_index("ix_email_logs_template_name", "email_logs", ["template_name"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])
    op.create_index(
        "ux_email_logs_idempotency_key", "email_logs", ["idempotency_key"], unique=True
    )
    op.create_index(
        "ix_email_logs_status_created", "email_logs", ["status", "created_at"]
    )

    # ── notification_preferences ────────────────────────────────────────────
    op.create_table(
        "notification_preferences",
        *_audit_columns(),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column(
            "billing_notifications", sa.Boolean(), nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "security_alerts", sa.Boolean(), nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "quota_warnings", sa.Boolean(), nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "product_updates", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_notification_preferences_user_id_users",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ux_notification_preferences_user_id",
        "notification_preferences", ["user_id"], unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_notification_preferences_user_id",
        table_name="notification_preferences",
    )
    op.drop_table("notification_preferences")

    op.drop_index("ix_email_logs_status_created", table_name="email_logs")
    op.drop_index("ux_email_logs_idempotency_key", table_name="email_logs")
    op.drop_index("ix_email_logs_status", table_name="email_logs")
    op.drop_index("ix_email_logs_template_name", table_name="email_logs")
    op.drop_index("ix_email_logs_recipient_email", table_name="email_logs")
    op.drop_index("ix_email_logs_user_id", table_name="email_logs")
    op.drop_table("email_logs")
