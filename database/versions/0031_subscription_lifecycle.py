"""Subscription lifecycle tables (Phase 5)

Revision ID: 0031
Revises: 0030
Create Date: 2026-08-27 00:00:00.000000

Adds the two Phase 5 tables:

  - subscriptions       : one row per user — lifecycle state machine
                          (status ∈ trialing|active|past_due_cancelled|expired),
                          period/trial timestamps, cancel bookkeeping, and an
                          event_version counter bumped on every transition.
  - subscription_events : append-only history log (created/trial_started/
                          activated/past_due_marked/cancelled/expired/renewed/
                          period_extended).

``user_plans`` (0029) remains the assignment table EntitlementService reads;
``subscriptions`` adds the lifecycle dimension without touching frozen models.

Downgrade intentionally destructive (drop tables); no data migration needed —
the tables are created empty.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0031"
down_revision: Union[str, None] = "0030"
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
    # ── subscriptions ────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        *_audit_columns(),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column(
            "plan_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column(
            "status", sa.String(32), nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "event_version", sa.Integer(), nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "current_period_start", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end", sa.Boolean(), nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_subscriptions_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"], name="fk_subscriptions_plan_id_plans",
        ),
    )
    op.create_index(
        "ux_subscriptions_user_id", "subscriptions", ["user_id"], unique=True
    )
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # ── subscription_events ─────────────────────────────────────────────────
    op.create_table(
        "subscription_events",
        *_audit_columns(),
        sa.Column(
            "subscription_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["subscriptions.id"],
            name="fk_subscription_events_subscription_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_subscription_events_subscription_id",
        "subscription_events", ["subscription_id"],
    )
    op.create_index(
        "ix_subscription_events_sub_created",
        "subscription_events", ["subscription_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_subscription_events_sub_created", table_name="subscription_events"
    )
    op.drop_index(
        "ix_subscription_events_subscription_id", table_name="subscription_events"
    )
    op.drop_table("subscription_events")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ux_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
