import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Make sure backend/ is on the path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Base  # noqa: E402 — import after sys.path fix

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Configure logging from the .ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """
    Return a synchronous database URL for Alembic migrations.
    Alembic runs migrations synchronously (psycopg2), while the app
    uses asyncpg at runtime — both point to the same database.
    """
    raw = os.environ.get("DATABASE_URL", "postgresql://stash:stash@db:5432/stash")
    # Strip asyncpg driver prefix if present; ensure plain postgresql://
    url = (
        raw
        .replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgres://", "postgresql://")
    )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection required)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to the DB)."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
