from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

from core.config import get_settings
from database import Base
import models  # noqa: F401  -- DO NOT REMOVE: registers User + Expense on Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- target_metadata -------------------------------------------------------- #
# `import models` above is load-bearing. Base.metadata is populated as a side
# effect of the model modules being imported. Without that import, autogenerate
# sees EMPTY metadata, concludes that `users` and `expenses` are no longer
# wanted, and writes a migration that DROPS BOTH TABLES.
target_metadata = Base.metadata

# --- database URL ----------------------------------------------------------- #
# Read from core.config (env var DATABASE_URL via .env), never from alembic.ini,
# which is committed to git. Handed straight to create_engine rather than through
# config.set_main_option(), because that path runs ConfigParser %-interpolation
# and would mangle any '%' in the password.
DATABASE_URL = get_settings().database_url


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of running it (alembic upgrade head --sql)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and run migrations against it."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

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
