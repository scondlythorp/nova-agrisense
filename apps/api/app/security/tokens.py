from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

from app.config.settings import get_settings
from app.core.exceptions import NovaAppError
from app.models.enums import PlatformRole


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: uuid.UUID
    jti: str
    platform_role: PlatformRole | None
    expires_at: datetime


def create_access_token(
    *,
    user_id: uuid.UUID,
    platform_role: PlatformRole | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    """Create a short-lived signed JWT access token and return (token, expires_in_seconds)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    exp = now + delta

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": str(uuid.uuid4()),
        "platform_role": platform_role.value if platform_role else None,
    }
    encoded = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded, max(1, int(delta.total_seconds()))


def decode_access_token(token: str) -> AccessTokenClaims:
    """Validate signature, expiration, issuer, audience, and token type."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require": ["sub", "exp", "iat", "iss", "aud", "type", "jti"],
            },
        )
    except InvalidTokenError as exc:
        raise NovaAppError(
            code="invalid_token",
            message="Authentication token is invalid or expired.",
            status_code=401,
        ) from exc

    if payload.get("type") != "access":
        raise NovaAppError(
            code="invalid_token_type",
            message="Invalid token type supplied.",
            status_code=401,
        )

    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except ValueError as exc:
        raise NovaAppError(
            code="invalid_token",
            message="Malformed token subject.",
            status_code=401,
        ) from exc

    raw_platform_role = payload.get("platform_role")
    platform_role: PlatformRole | None = None
    if raw_platform_role:
        try:
            platform_role = PlatformRole(str(raw_platform_role))
        except ValueError as exc:
            raise NovaAppError(
                code="invalid_token",
                message="Unrecognized platform role claim.",
                status_code=401,
            ) from exc

    exp_dt = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
    return AccessTokenClaims(
        user_id=user_id,
        jti=str(payload["jti"]),
        platform_role=platform_role,
        expires_at=exp_dt,
    )


def generate_opaque_refresh_token() -> str:
    """Generate a high-entropy CSPRNG opaque refresh token."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """Hash an opaque refresh token using HMAC-SHA256 keyed by the server secret."""
    settings = get_settings()
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        raw_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_csrf_token() -> str:
    """Generate a CSPRNG double-submit CSRF token."""
    return secrets.token_urlsafe(32)
