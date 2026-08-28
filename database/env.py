"""
AstroOS — Alembic Environment

Reads DATABASE_URL from the environment (never from alembic.ini).
Supports both sync (for migration runs) and async (optional) SQLAlchemy.
All ORM models must be imported here so Alembic's autogenerate can
detect schema changes.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make workspace root importable ───────────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Import all models so Alembic sees them ───────────────────────────────────
from apps.api.models.base import AstroBase  # noqa: E402
from apps.api.models.user import (  # noqa: E402
    AuditLogModel,
    PasswordResetTokenModel,
    UserModel,
    UserSessionModel,
)
from apps.api.models.dataset import DatasetModel  # noqa: E402
from apps.api.models.digital_twin import DigitalTwinModel, TwinModificationModel  # noqa: E402
from apps.api.models.research_case import (  # noqa: E402
    AttachmentModel,
    EventSnapshotModel,
    LifeEventModel,
    ResearchCaseModel,
)
from apps.api.models.pattern import (  # noqa: E402
    DiscoveredPatternModel,
    PatternDiscoveryRunModel,
)
from apps.api.models.ai_settings import AISettingsModel  # noqa: E402
from apps.api.models.technique import (  # noqa: E402
    TechniqueModel,
    TechniqueSourceModel,
    TechniqueValidationCaseModel,
)
from apps.api.models.plan import (  # noqa: E402
    PlanModel,
    FeatureModel,
    PlanFeatureModel,
    PlanLimitModel,
    UserPlanModel,
)

# ── Alembic Config ────────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = AstroBase.metadata

# ── Database URL from environment (required) ──────────────────────────────────
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    try:
        from apps.api.config import get_settings
        DATABASE_URL = get_settings().DATABASE_URL
    except Exception:
        pass

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Migrations require a live PostgreSQL connection."
    )

# asyncpg URLs must be converted back to psycopg2 for Alembic's sync engine
if "asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Emit SQL without a live connection (useful for review)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()