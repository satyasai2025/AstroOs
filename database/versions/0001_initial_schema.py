"""Initial schema: users, user_sessions, audit_log

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── Enable pgcrypto for gen_random_uuid() ────────────────────────────────
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    # ── Enums — explicit SQL so we control IF NOT EXISTS ─────────────────────
    conn.execute(sa.text(
        "CREATE TYPE user_role AS ENUM ('guest', 'researcher', 'admin')"
        " -- skip if exists"
        if False else
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN "
        "    CREATE TYPE user_role AS ENUM ('guest', 'researcher', 'admin'); "
        "  END IF; "
        "END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status') THEN "
        "    CREATE TYPE user_status AS ENUM ('active', 'suspended', 'pending_verification'); "
        "  END IF; "
        "END $$"
    ))

    # ── updated_at trigger function ───────────────────────────────────────────
    conn.execute(sa.text(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$
        """
    ))

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column(
            "role",
            # postgresql.ENUM with create_type=False prevents double-creation
            postgresql.ENUM(
                "guest", "researcher", "admin",
                name="user_role",
                create_type=False,
            ),
            nullable=False,
            server_default="researcher",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "active", "suspended", "pending_verification",
                name="user_status",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))

    # ── user_sessions ─────────────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("refresh_token_jti", sa.String(64), nullable=False),
        sa.Column("device_name", sa.String(200), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "ix_user_sessions_refresh_token_jti",
        "user_sessions",
        ["refresh_token_jti"],
        unique=True,
    )
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_user_sessions_updated_at
        BEFORE UPDATE ON user_sessions
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))

    # ── audit_log ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
    )
    op.create_index("ix_audit_log_actor_id", "audit_log", ["actor_id"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_audit_log_updated_at
        BEFORE UPDATE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_audit_log_updated_at ON audit_log"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_user_sessions_updated_at ON user_sessions"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS trg_users_updated_at ON users"))
    op.drop_table("audit_log")
    op.drop_table("user_sessions")
    op.drop_table("users")
    conn.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at()"))
    conn.execute(sa.text("DROP TYPE IF EXISTS user_status"))
    conn.execute(sa.text("DROP TYPE IF EXISTS user_role"))
