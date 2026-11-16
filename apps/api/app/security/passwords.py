from __future__ import annotations

import re
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.exceptions import NovaAppError

_ARGON2_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

_WEAK_PASSWORDS = {
    "password1234",
    "password12345",
    "qwerty123456",
    "letmein12345",
    "admin1234567",
    "agrisense123",
    "novaagrisense",
}


def validate_password_policy(password: str, email: str | None = None) -> None:
    """Enforce baseline password strength without exposing sensitive details."""
    if len(password) < 12:
        raise NovaAppError(
            code="weak_password",
            message="Password must be at least 12 characters long.",
            status_code=422,
        )
    if len(password) > 128:
        raise NovaAppError(
            code="weak_password",
            message="Password must not exceed 128 characters.",
            status_code=422,
        )
    if not re.search(r"[a-z]", password):
        raise NovaAppError(
            code="weak_password",
            message="Password must include at least one lowercase letter.",
            status_code=422,
        )
    if not re.search(r"[A-Z]", password):
        raise NovaAppError(
            code="weak_password",
            message="Password must include at least one uppercase letter.",
            status_code=422,
        )
    if not re.search(r"\d", password):
        raise NovaAppError(
            code="weak_password",
            message="Password must include at least one digit.",
            status_code=422,
        )
    lowered = password.lower()
    if lowered in _WEAK_PASSWORDS:
        raise NovaAppError(
            code="weak_password",
            message="Password is too common. Choose a stronger passphrase.",
            status_code=422,
        )
    if email:
        local_part = email.split("@", 1)[0].strip().lower()
        if len(local_part) >= 4 and local_part in lowered:
            raise NovaAppError(
                code="weak_password",
                message="Password must not contain your email address.",
                status_code=422,
            )


def hash_password(password: str) -> str:
    return _ARGON2_HASHER.hash(password)


def verify_password(password_hash: str, plain_password: str) -> bool:
    try:
        return _ARGON2_HASHER.verify(password_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _ARGON2_HASHER.check_needs_rehash(password_hash)
