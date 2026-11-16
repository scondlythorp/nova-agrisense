from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_production_fails_safely_without_database_url() -> None:
    with pytest.raises(ValidationError, match="NOVA_DATABASE_URL"):
        Settings(
            env="production",
            database_url=None,
            secret_key="a" * 40,
            cors_origins=["https://agrisense.example.com"],
        )


def test_production_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="Wildcard CORS"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://u:p@localhost:5432/nova",
            secret_key="a" * 40,
            cors_origins=["*"],
        )


def test_production_rejects_weak_secret_key() -> None:
    with pytest.raises(ValidationError, match="NOVA_SECRET_KEY"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://u:p@localhost:5432/nova",
            secret_key="dev-only-insecure-key-replace-in-production",
            cors_origins=["https://agrisense.example.com"],
        )


def test_production_defaults_secure_cookies_and_enforces_samesite_none() -> None:
    prod = Settings(
        env="production",
        database_url="postgresql+psycopg://u:p@localhost:5432/nova",
        secret_key="a" * 40,
        cors_origins=["https://agrisense.example.com"],
    )
    assert prod.effective_cookie_secure is True

    with pytest.raises(ValidationError, match="SameSite=None"):
        Settings(
            env="production",
            database_url="postgresql+psycopg://u:p@localhost:5432/nova",
            secret_key="a" * 40,
            cors_origins=["https://agrisense.example.com"],
            cookie_samesite="none",
            cookie_secure=False,
        )

