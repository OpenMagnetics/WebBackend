import os
import pathlib
import sys

from alembic import context
from sqlalchemy import create_engine, text

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.backend.accounts.models import Base  # noqa: E402

target_metadata = Base.metadata


def _database_url():
    missing = [v for v in ("OM_DB_ADDRESS", "OM_DB_PORT", "OM_DB_NAME", "OM_DB_USER", "OM_DB_PASSWORD")
               if os.getenv(v) is None]
    if missing:
        raise RuntimeError(f"Cannot run migrations: missing environment variables {missing}")
    return (f"postgresql+psycopg2://{os.getenv('OM_DB_USER')}:{os.getenv('OM_DB_PASSWORD')}"
            f"@{os.getenv('OM_DB_ADDRESS')}:{os.getenv('OM_DB_PORT')}/{os.getenv('OM_DB_NAME')}")


def _include_object(object, name, type_, reflected, compare_to):
    """Only manage objects in the accounts schema — the database also holds
    legacy public tables, telemetry and umami, which alembic must never touch."""
    if type_ == "table":
        return object.schema == "accounts"
    return True


def _include_name(name, type_, parent_names):
    """Restrict reflection to the accounts schema; the db user cannot even read
    some of the other schemas (heaviside_telemetry)."""
    if type_ == "schema":
        return name == "accounts"
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=_include_object,
        include_name=_include_name,
        version_table_schema="accounts",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_database_url())
    with engine.connect() as connection:
        # The alembic version table lives in the accounts schema — make sure it
        # exists before alembic looks for it.
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS accounts"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=_include_object,
            include_name=_include_name,
            version_table_schema="accounts",
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
