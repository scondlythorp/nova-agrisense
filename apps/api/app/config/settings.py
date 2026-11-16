from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Production deployments fail fast when mandatory security or database settings
    are missing or left at unsafe placeholder values.
    """

    model_config = SettingsConfigDict(
        env_prefix="NOVA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    env: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "Nova AgriSense API"
    app_version: str = "0.2.0"
    api_v1_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Database (PostgreSQL / Cloud SQL via psycopg3)
    database_url: str | None = None
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=50)
    db_echo: bool = False

    # Security & JWT
    secret_key: str = "dev-only-insecure-key-replace-in-production"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "nova-agrisense-api"
    jwt_audience: str = "nova-agrisense-clients"
    access_token_expire_minutes: int = Field(default=15, ge=5, le=120)
    refresh_token_expire_days: int = Field(default=14, ge=1, le=60)
    allow_self_registration: bool = True
    require_email_verification: bool = False

    # Refresh & CSRF Cookies
    refresh_cookie_name: str = "nova_refresh_token"
    csrf_cookie_name: str = "nova_csrf_token"
    cookie_domain: str | None = None
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_secure: bool | None = None

    # Rate Limiting & Proxy Trust
    trust_proxy_headers: bool = False
    auth_rate_limit_max_attempts: int = Field(default=10, ge=1, le=200)
    auth_rate_limit_window_seconds: int = Field(default=60, ge=10, le=3600)

    # Strict CORS Origins
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"]
    )

    # Integrations (Cloud Storage, External Weather/Remote Sensing)
    gcs_bucket_name: str | None = None
    weather_provider: str = "unconfigured"
    weather_api_key: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):
                import json

                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_safety(self) -> Settings:
        if self.env in {"staging", "production"}:
            if not self.database_url:
                raise ValueError(
                    "NOVA_DATABASE_URL must be configured in staging and production environments."
                )
            if (
                not self.secret_key
                or len(self.secret_key) < 32
                or "dev-only" in self.secret_key
                or "CHANGE_ME" in self.secret_key
            ):
                raise ValueError(
                    "NOVA_SECRET_KEY must be a strong secret (>= 32 chars) in staging/production."
                )
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS origins are forbidden in staging/production.")
            if self.cookie_samesite == "none" and not self.effective_cookie_secure:
                raise ValueError("SameSite=None cookies require secure=True in staging/production.")
        return self

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def effective_cookie_secure(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.env in {"staging", "production"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
