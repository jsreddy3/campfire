from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.database import Base  # uses the Base we already defined

config = context.config
fileConfig(config.config_file_name)

# Inject DB URL (sync driver!)
# Replace the asyncpg driver with psycopg2 for Alembic migrations
db_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/postgres")
if "+asyncpg" in db_url:
    db_url = db_url.replace("+asyncpg", "+psycopg2")

# Use the environment variable (with driver replaced) for migrations
config.set_main_option(
    "sqlalchemy.url",
    db_url
)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
