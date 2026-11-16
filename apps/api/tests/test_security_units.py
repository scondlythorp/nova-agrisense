from __future__ import annotations

from datetime import timedelta
import uuid

import pytest

from app.core.exceptions import NovaAppError
from app.models.enums import OrganizationRole, PlatformRole
from app.security.passwords import hash_password, validate_password_policy, verify_password
from app.security.rbac import Permission, has_permission
from app.security.tokens import (
    create_access_token,
    decode_access_token,
    generate_opaque_refresh_token,
    hash_refresh_token,
)


def test_argon2id_hash_and_verify() -> None:
    hashed = hash_password("StrongGambiaFarm2026")
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, "StrongGambiaFarm2026") is True
    assert verify_password(hashed, "WrongPassword2026") is False


def test_password_policy_rejects_email_substring() -> None:
    with pytest.raises(NovaAppError, match="email"):
        validate_password_policy("AminaJallow2026!", email="aminajallow@coop.gm")


def test_access_token_roundtrip_and_expiry() -> None:
    uid = uuid.uuid4()
    token, expires_in = create_access_token(
        user_id=uid,
        platform_role=PlatformRole.PLATFORM_ADMIN,
        expires_delta=timedelta(minutes=5),
    )
    assert expires_in == 300
    claims = decode_access_token(token)
    assert claims.user_id == uid
    assert claims.platform_role == PlatformRole.PLATFORM_ADMIN

    expired, _ = create_access_token(
        user_id=uid,
        expires_delta=timedelta(seconds=-5),
    )
    with pytest.raises(NovaAppError):
        decode_access_token(expired)

    import jwt
    from app.config.settings import get_settings

    settings = get_settings()
    wrong_iss = jwt.encode(
        {
            "sub": str(uid),
            "type": "access",
            "iss": "evil-issuer",
            "aud": settings.jwt_audience,
            "iat": 1700000000,
            "exp": 9999999999,
            "jti": "jti-1",
        },
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(NovaAppError):
        decode_access_token(wrong_iss)


def test_refresh_token_hashing_is_deterministic_and_opaque() -> None:
    raw = generate_opaque_refresh_token()
    assert len(raw) >= 48
    h1 = hash_refresh_token(raw)
    h2 = hash_refresh_token(raw)
    assert h1 == h2
    assert h1 != raw


def test_rbac_permission_matrix_covers_all_seven_roles() -> None:
    assert len(OrganizationRole) == 7
    assert has_permission(OrganizationRole.ORGANIZATION_ADMIN, Permission.MEMBERSHIP_MANAGE)
    assert has_permission(OrganizationRole.ORGANIZATION_ADMIN, Permission.AUDIT_READ)
    assert has_permission(OrganizationRole.AGRICULTURAL_OFFICER, Permission.FARMER_WRITE)
    assert not has_permission(OrganizationRole.AGRICULTURAL_OFFICER, Permission.ORG_UPDATE)
    assert has_permission(OrganizationRole.DATA_MANAGER, Permission.IMPORT_MANAGE)
    assert not has_permission(OrganizationRole.DATA_MANAGER, Permission.AUDIT_READ)
    assert has_permission(OrganizationRole.RESEARCHER, Permission.ANALYTICS_READ)
    assert not has_permission(OrganizationRole.RESEARCHER, Permission.FARMER_WRITE)
    assert has_permission(OrganizationRole.COOPERATIVE_MANAGER, Permission.FARM_WRITE)
    assert not has_permission(OrganizationRole.COOPERATIVE_MANAGER, Permission.MEMBERSHIP_MANAGE)
    assert has_permission(OrganizationRole.FARMER, Permission.PRODUCTION_WRITE)
    assert not has_permission(OrganizationRole.FARMER, Permission.MEMBERSHIP_READ)
    assert has_permission(OrganizationRole.READ_ONLY_ANALYST, Permission.ANALYTICS_READ)
    assert not has_permission(OrganizationRole.READ_ONLY_ANALYST, Permission.PRODUCTION_WRITE)

