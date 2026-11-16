from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault("NOVA_ENV", "test")
os.environ.setdefault(
    "NOVA_SECRET_KEY",
    "test-secret-key-with-at-least-thirty-two-bytes-0001",
)

from app.config.settings import get_settings
from app.database.session import get_db, get_engine, get_session_factory
from app.main import create_app
from app.security.rate_limit import auth_rate_limiter


def _resolve_test_database_url() -> str | None:
    return os.environ.get("NOVA_TEST_DATABASE_URL") or os.environ.get("NOVA_DATABASE_URL")


@pytest.fixture(scope="session")
def pg_engine():
    db_url = _resolve_test_database_url()
    if not db_url:
        pytest.fail(
            "PostgreSQL is required for Phase 1 integration & RLS tests. "
            "Set NOVA_TEST_DATABASE_URL or NOVA_DATABASE_URL."
        )
    if not db_url.startswith("postgresql"):
        pytest.fail("Phase 1 integration and RLS tests must run against PostgreSQL, not SQLite.")

    engine = create_engine(db_url, pool_pre_ping=True)

    # Verify schema is migrated before executing integration tests.
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'users'"
                ")"
            )
        ).scalar()
        if not exists:
            pytest.fail(
                "Database schema is not migrated. Run `alembic upgrade head` before pytest."
            )
    return engine


@pytest.fixture(autouse=True)
def reset_state(request):
    auth_rate_limiter.reset()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    if "pg_engine" in request.fixturenames or "db_session" in request.fixturenames or "client" in request.fixturenames:
        engine = request.getfixturevalue("pg_engine")
        with engine.begin() as conn:
            conn.execute(
                text(
                    "TRUNCATE TABLE audit_logs, refresh_sessions, "
                    "organization_memberships, organizations, users RESTART IDENTITY CASCADE"
                )
            )
    yield


@pytest.fixture()
def db_session(pg_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        bind=pg_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        if session.in_transaction():
            session.rollback()
        session.close()


@pytest.fixture()
def client(pg_engine) -> Generator[TestClient, None, None]:
    TestingSessionLocal = sessionmaker(
        bind=pg_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    def _override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            if session.in_transaction():
                session.rollback()
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def unit_client() -> Generator[TestClient, None, None]:
    """Client without DB connection for non-DB endpoints like /health and /meta."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
