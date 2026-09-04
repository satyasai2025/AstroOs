"""Add timezone column to users

Revision ID: 0020
Revises: 0019
Create Date: 2026-08-12 00:00:00.000000

Settings > Profile has had a Timezone dropdown that never actually did
anything — it was a local useState never loaded from or saved to the
account. This adds the column it should have been wired to, so the
value is real and can be threaded into date/time displays (starting
with Transit Analysis's "Jump to Date & Time" picker).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "timezone",
            sa.String(64),
            nullable=False,
            server_default="UTC",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
