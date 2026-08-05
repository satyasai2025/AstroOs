"""Add password_reset_tokens table

Revision ID: 0017
Revises: 0016
Create Date: 2026-08-05 00:00:00.000000

Mirrors user_sessions' single-use-token shape: a row is minted on
POST /auth/forgot-password and atomically consumed (used_at set) on
POST /auth/reset-password, the same replay-guard pattern used for
refresh-token rotation. Only a SHA-256 hash of the token is stored —
unlike refresh_token_jti (safe to store raw because it's a JWT id, not
a bearer secret), the raw reset token itself is the bearer secret, so
the row must not reveal it if the table is ever read.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
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
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"]
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_password_reset_tokens_updated_at
        BEFORE UPDATE ON password_reset_tokens
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_password_reset_tokens_updated_at "
        "ON password_reset_tokens"
    ))
    op.drop_table("password_reset_tokens")
