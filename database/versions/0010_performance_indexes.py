"""Performance indexes migration - Phase M3"""

from alembic import op

# Revision identifiers
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    """Create performance indexes for chart computation queries."""
    # Birth charts indexes
    op.create_index(
        "ix_birth_charts_user_id",
        "birth_charts",
        ["user_id"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_birth_charts_created_at",
        "birth_charts",
        ["created_at"],
        postgresql_using="btree",
    )

    # Planet positions indexes
    op.create_index(
        "ix_planet_positions_chart_id",
        "planet_positions",
        ["chart_id"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_planet_positions_planet_name",
        "planet_positions",
        ["planet_name"],
        postgresql_using="btree",
    )

    # House positions indexes
    op.create_index(
        "ix_house_positions_chart_id",
        "house_positions",
        ["chart_id"],
        postgresql_using="btree",
    )

    # Events indexes
    op.create_index(
        "ix_events_chart_id",
        "events",
        ["chart_id"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_events_event_date",
        "events",
        ["event_date"],
        postgresql_using="btree",
    )
    op.create_index(
        "ix_events_category",
        "events",
        ["category"],
        postgresql_using="btree",
    )

    # Divisional charts indexes
    op.create_index(
        "ix_divisional_charts_parent_chart_id",
        "divisional_charts",
        ["parent_chart_id"],
        postgresql_using="btree",
    )

    # Dasha indexes
    op.create_index(
        "ix_dasha_periods_chart_id",
        "dasha_periods",
        ["chart_id"],
        postgresql_using="btree",
    )


def downgrade():
    """Remove performance indexes."""
    op.drop_index("ix_birth_charts_user_id")
    op.drop_index("ix_birth_charts_created_at")
    op.drop_index("ix_planet_positions_chart_id")
    op.drop_index("ix_planet_positions_planet_name")
    op.drop_index("ix_house_positions_chart_id")
    op.drop_index("ix_events_chart_id")
    op.drop_index("ix_events_event_date")
    op.drop_index("ix_events_category")
    op.drop_index("ix_divisional_charts_parent_chart_id")
    op.drop_index("ix_dasha_periods_chart_id")