"""Payment gateway tables (Phase 6)

Revision ID: 0032
Revises: 0031
Create Date: 2026-08-27 00:00:00.000000

Adds the Phase 6 payment gateway tables:
  - payments               : individual transaction / receipt records
  - payment_customers      : mapping of user_id to provider customer IDs
  - payment_webhook_events : append-only audit & deduplication log for webhooks
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0032"
down_revision: Union[str, None] = "0031"
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
    # ── payments ────────────────────────────────────────────────────────────
    op.create_table(
        "payments",
        *_audit_columns(),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column(
            "subscription_id", postgresql.UUID(as_uuid=True), nullable=True,
        ),
        sa.Column(
            "plan_id", postgresql.UUID(as_uuid=True), nullable=True,
        ),
        sa.Column(
            "provider", sa.String(32), nullable=False,
            server_default=sa.text("'mock'"),
        ),
        sa.Column("provider_payment_id", sa.String(255), nullable=True),
        sa.Column("provider_order_id", sa.String(255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "currency", sa.String(10), nullable=False,
            server_default=sa.text("'USD'"),
        ),
        sa.Column(
            "status", sa.String(32), nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("payment_method", sa.String(64), nullable=True),
        sa.Column("receipt_url", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_payments_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["subscriptions.id"],
            name="fk_payments_subscription_id_subscriptions",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"], ["plans.id"],
            name="fk_payments_plan_id_plans",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])
    op.create_index("ix_payments_plan_id", "payments", ["plan_id"])
    op.create_index("ix_payments_provider", "payments", ["provider"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_user_status", "payments", ["user_id", "status"])
    op.create_index(
        "ix_payments_provider_payment_id", "payments", ["provider", "provider_payment_id"]
    )
    op.create_index(
        "ix_payments_provider_order_id", "payments", ["provider_order_id"]
    )

    # ── payment_customers ───────────────────────────────────────────────────
    op.create_table(
        "payment_customers",
        *_audit_columns(),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_customer_id", sa.String(255), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_payment_customers_user_id_users",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_payment_customers_user_id", "payment_customers", ["user_id"])
    op.create_index(
        "ux_payment_customers_user_provider", "payment_customers", ["user_id", "provider"],
        unique=True,
    )
    op.create_index(
        "ix_payment_customers_provider_id", "payment_customers", ["provider", "provider_customer_id"]
    )

    # ── payment_webhook_events ──────────────────────────────────────────────
    op.create_table(
        "payment_webhook_events",
        *_audit_columns(),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "status", sa.String(32), nullable=False,
            server_default=sa.text("'processed'"),
        ),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
    )
    op.create_index(
        "ux_payment_webhooks_provider_event",
        "payment_webhook_events",
        ["provider", "provider_event_id"],
        unique=True,
    )
    op.create_index(
        "ix_payment_webhooks_status",
        "payment_webhook_events",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_payment_webhooks_status", table_name="payment_webhook_events")
    op.drop_index("ux_payment_webhooks_provider_event", table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")

    op.drop_index("ix_payment_customers_provider_id", table_name="payment_customers")
    op.drop_index("ux_payment_customers_user_provider", table_name="payment_customers")
    op.drop_index("ix_payment_customers_user_id", table_name="payment_customers")
    op.drop_table("payment_customers")

    op.drop_index("ix_payments_provider_order_id", table_name="payments")
    op.drop_index("ix_payments_provider_payment_id", table_name="payments")
    op.drop_index("ix_payments_user_status", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_provider", table_name="payments")
    op.drop_index("ix_payments_plan_id", table_name="payments")
    op.drop_index("ix_payments_subscription_id", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")
