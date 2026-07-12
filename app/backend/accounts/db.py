"""Shared pooled SQLAlchemy engine for the accounts feature.

Unlike the legacy tables (which open and dispose an engine per request), the
accounts feature uses one process-wide pooled engine. Credentials come from the
same OM_DB_* environment variables the rest of the backend uses. If they are
missing, the first use raises loudly — the accounts endpoints must never run
against a half-configured database.
"""
import os

import sqlalchemy
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None


def _database_url():
    missing = [v for v in ("OM_DB_ADDRESS", "OM_DB_PORT", "OM_DB_NAME", "OM_DB_USER", "OM_DB_PASSWORD")
               if os.getenv(v) is None]
    if missing:
        raise RuntimeError(f"Accounts database is not configured: missing environment variables {missing}")
    return (f"postgresql+psycopg2://{os.getenv('OM_DB_USER')}:{os.getenv('OM_DB_PASSWORD')}"
            f"@{os.getenv('OM_DB_ADDRESS')}:{os.getenv('OM_DB_PORT')}/{os.getenv('OM_DB_NAME')}")


def get_engine():
    global _engine
    if _engine is None:
        _engine = sqlalchemy.create_engine(
            _database_url(),
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_db():
    """FastAPI dependency: one ORM session per request."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
