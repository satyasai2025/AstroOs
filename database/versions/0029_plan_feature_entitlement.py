"""Plan / Feature / Entitlement schema (Phase 2)

Revision ID: 0029
Revises: 0028
Create Date: 2026-08-26 00:00:00.000000

Adds the five Phase 2 tables:
  - plans           : tier catalog (FREE, PRO, RESEARCH, CUSTOM)
  - features        : feature catalog (chart_calc, dasha, ai_analysis, ...)
  - plan_features   : entitlement mapping (which plan can do what on a feature)
  - plan_limits     : numeric limits per plan (saved_horoscopes, research_projects_monthly)
  - user_plans      : per-user current plan assignment (null = default Free)

AstroBase audit columns (id/created_at/updated_at/deleted_at) are inherited.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0029"
down_revision: Union[str, None] = "0028"
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
    # ── plans ────────────────────────────────────────────────────────────────
    op.create_table(
        "plans",
        *_audit_columns(),
        sa.Column("plan_code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_plans_plan_code", "plans", ["plan_code"], unique=True)

    # ── features ────────────────────────────────────────────────────────────
    op.create_table(
        "features",
        *_audit_columns(),
        sa.Column("feature_key", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("category", sa.String(50), nullable=False, server_default="core"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_features_feature_key", "features", ["feature_key"], unique=True)
    op.create_index("ix_features_category", "features", ["category"])

    # ── plan_features ───────────────────────────────────────────────────────
    op.create_table(
        "plan_features",
        *_audit_columns(),
        sa.Column(
            "plan_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "feature_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("features.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("can_view", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_create", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_edit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("can_export", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("view_limit", sa.Integer(), nullable=True),
        sa.Column("create_limit", sa.Integer(), nullable=True),
        sa.Column("edit_limit", sa.Integer(), nullable=True),
        sa.Column("run_limit", sa.Integer(), nullable=True),
        sa.UniqueConstraint("plan_id", "feature_id", name="uc_plan_feature"),
    )
    op.create_index("ix_plan_features_plan_id", "plan_features", ["plan_id"])
    op.create_index("ix_plan_features_feature_id", "plan_features", ["feature_id"])

    # ── plan_limits ─────────────────────────────────────────────────────────
    op.create_table(
        "plan_limits",
        *_audit_columns(),
        sa.Column(
            "plan_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column("saved_horoscopes", sa.Integer(), nullable=True),
        sa.Column("research_projects_monthly", sa.Integer(), nullable=True),
        sa.Column("extra_limits_json", sa.Text(), nullable=True),
    )

    # ── user_plans ──────────────────────────────────────────────────────────
    op.create_table(
        "user_plans",
        *_audit_columns(),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True,
        ),
        sa.Column(
            "plan_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_user_plans_user_id", "user_plans", ["user_id"], unique=True)
    op.create_index("ix_user_plans_plan_id", "user_plans", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_user_plans_plan_id", table_name="user_plans")
    op.drop_index("ix_user_plans_user_id", table_name="user_plans")
    op.drop_table("user_plans")
    op.drop_table("plan_limits")
    op.drop_index("ix_plan_features_feature_id", table_name="plan_features")
    op.drop_index("ix_plan_features_plan_id", table_name="plan_features")
    op.drop_table("plan_features")
    op.drop_index("ix_features_category", table_name="features")
    op.drop_index("ix_features_feature_key", table_name="features")
    op.drop_table("features")
    op.drop_index("ix_plans_plan_code", table_name="plans")
    op.drop_table("plans")