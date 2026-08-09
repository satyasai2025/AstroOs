"""Add ai_settings table

Revision ID: 0018
Revises: 0017
Create Date: 2026-08-07 00:00:00.000000

One row per user, letting each researcher point AI-backed features
(pattern explanations, the Ask tab, AI search) at their own provider and
API key instead of the server-wide OPENAI_* config. api_key_encrypted
stores a Fernet token (apps.api.security.encryption), never plaintext —
api_key_last4 duplicates just the last 4 characters so the UI can render
"sk-...ab12" without decrypting.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
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
        sa.Column(
            "provider",
            sa.String(20),
            nullable=False,
            server_default="astroos_ai",
        ),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("api_key_last4", sa.String(8), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="1000"),
    )
    op.create_index(
        "ix_ai_settings_user_id", "ai_settings", ["user_id"], unique=True
    )
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        CREATE TRIGGER trg_ai_settings_updated_at
        BEFORE UPDATE ON ai_settings
        FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """
    ))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_ai_settings_updated_at ON ai_settings"
    ))
    op.drop_table("ai_settings")
