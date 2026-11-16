from __future__ import annotations

import uuid
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine | None:
    """Create a lazy SQLAlchemy engine if NOVA_DATABASE_URL is configured."""
    settings = get_settings()
    if not settings.database_url:
        return None
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        echo=settings.db_echo,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session] | None:
    engine = get_engine()
    if engine is None:
        return None
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency providing a scoped SQLAlchemy session.

    Any uncommitted transaction state or transaction-local PostgreSQL RLS GUCs
    (`set_config(..., true)`) are cleared on rollback/close so pooled connections
    never retain tenant context across requests.
    """
    factory = get_session_factory()
    if factory is None:
        raise RuntimeError("Database is not configured. Set NOVA_DATABASE_URL.")
    session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        if session.in_transaction():
            session.rollback()
        session.close()


def set_rls_context(
    session: Session,
    *,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    is_platform_admin: bool = False,
) -> None:
    """Bind transaction-local PostgreSQL RLS settings via set_config(..., true).

    The third argument `true` scopes settings strictly to the current transaction.
    Non-PostgreSQL dialects (such as unit-test SQLite if ever used for non-RLS
    helpers) skip PostgreSQL `set_config` gracefully.
    """
    bind = session.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return

    session.execute(
        text(
            "SELECT "
            "set_config('app.current_user_id', :uid, true), "
            "set_config('app.current_organization_id', :oid, true), "
            "set_config('app.is_platform_admin', :is_admin, true)"
        ),
        {
            "uid": str(user_id) if user_id else "",
            "oid": str(organization_id) if organization_id else "",
            "is_admin": "true" if is_platform_admin else "false",
        },
    )


def check_database_readiness() -> tuple[bool, bool, bool | None, str]:
    """Check whether the database is configured, reachable, and has PostGIS enabled."""
    settings = get_settings()
    if not settings.database_url:
        return False, False, None, "NOVA_DATABASE_URL is not configured."

    engine = get_engine()
    if engine is None:
        return False, False, None, "Database engine unavailable."

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            postgis_row = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')")
            ).scalar()
        return True, True, bool(postgis_row), "PostgreSQL connection healthy."
    except Exception:
        return True, False, None, "PostgreSQL connection failed."
