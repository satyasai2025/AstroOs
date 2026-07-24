"""Performance indexes migration - Phase M3"""

from alembic import op

# Revision identifiers
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    """Create performance indexes for chart computation queries.

    This migration originally referenced tables/columns that don't exist
    (house_positions, dasha_periods, divisional_charts.parent_chart_id)
    and re-created several indexes that migration 0002 (astrology_schema)
    already creates inline when it first builds those tables. Both classes
    of bug broke every fresh `alembic upgrade head` run. Verified against
    0002's actual table/column/index definitions -- only genuinely new,
    non-duplicate indexes remain below:

    Removed (each already exists from 0002, under the same or a different
    name, on the same column):
      - ix_birth_charts_user_id       (birth_charts.user_id)
      - ix_planet_positions_chart_id  (planet_positions.chart_id)
      - ix_events_chart_id            (events.chart_id)
      - ix_events_event_date          (events.event_date -> 0002's ix_events_date)
      - "house_positions" -> real table is "houses", already has
        ix_houses_chart_id from 0002
      - "dasha_periods" -> real table is "dashas", already has
        ix_dashas_chart_id from 0002
      - divisional_charts."parent_chart_id" does not exist; the real FK
        column is birth_chart_id, already indexed as
        ix_divisional_charts_birth_chart_id from 0002
    """
    # Birth charts: created_at has no existing index.
    op.create_index(
        "ix_birth_charts_created_at",
        "birth_charts",
        ["created_at"],
        postgresql_using="btree",
    )

    # Planet positions: column is "graha" (enum), not "planet_name" -- there
    # is no planet_name column on this table. A composite unique index on
    # (chart_id, graha) already exists from migration 0002
    # (ix_planet_positions_chart_graha); this one is for queries filtering
    # by planet alone, across charts.
    op.create_index(
        "ix_planet_positions_graha",
        "planet_positions",
        ["graha"],
        postgresql_using="btree",
    )

    # Events: category has no existing index.
    op.create_index(
        "ix_events_category",
        "events",
        ["category"],
        postgresql_using="btree",
    )


def downgrade():
    """Remove performance indexes added by this migration's upgrade()."""
    op.drop_index("ix_birth_charts_created_at")
    op.drop_index("ix_planet_positions_graha")
    op.drop_index("ix_events_category")
