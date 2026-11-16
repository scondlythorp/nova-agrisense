from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.exceptions import NovaAppError
from app.database.session import set_rls_context
from app.models.enums import MembershipStatus, PlatformRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    MembershipSummary,
    RegisterRequest,
    UserProfileResponse,
)
from app.security.passwords import (
    hash_password,
    password_needs_rehash,
    validate_password_policy,
    verify_password,
)
from app.security.rbac import get_permissions_for_role
from app.security.tokens import (
    create_access_token,
    generate_opaque_refresh_token,
    hash_refresh_token,
)
from app.services.audit_service import record_audit_event


def normalize_email(email: str) -> str:
    return email.strip().lower()


def build_user_profile(db: Session, user: User) -> UserProfileResponse:
    set_rls_context(
        db,
        user_id=user.id,
        organization_id=None,
        is_platform_admin=(user.platform_role == PlatformRole.PLATFORM_ADMIN),
    )
    rows = db.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status.in_(
                [MembershipStatus.ACTIVE, MembershipStatus.INVITED]
            ),
            Organization.is_active.is_(True),
        )
        .order_by(Organization.name.asc())
    ).all()

    memberships = [
        MembershipSummary(
            id=membership.id,
            organization_id=org.id,
            organization_name=org.name,
            organization_slug=org.slug,
            organization_type=org.organization_type,
            role=membership.role,
            status=membership.status,
            permissions=sorted(p.value for p in get_permissions_for_role(membership.role)),
            joined_at=membership.joined_at,
        )
        for membership, org in rows
    ]

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=user.is_active,
        is_verified=user.is_verified,
        platform_role=user.platform_role,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        memberships=memberships,
    )


def register_user(
    db: Session,
    payload: RegisterRequest,
    *,
    request_id: str | None = None,
) -> UserProfileResponse:
    settings = get_settings()
    if not settings.allow_self_registration:
        raise NovaAppError(
            code="registration_disabled",
            message="Self-registration is currently disabled. Contact an administrator.",
            status_code=403,
        )

    normalized = normalize_email(payload.email)
    validate_password_policy(payload.password, email=normalized)

    existing = db.execute(select(User).where(User.email == normalized)).scalar_one_or_none()
    if existing is not None:
        raise NovaAppError(
            code="email_already_registered",
            message="An account with this email address already exists.",
            status_code=409,
        )

    user = User(
        email=normalized,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        phone_number=payload.phone_number.strip() if payload.phone_number else None,
        is_active=True,
        is_verified=False,
        platform_role=None,
    )
    db.add(user)
    db.flush()

    record_audit_event(
        db,
        action="auth.register",
        resource_type="user",
        resource_id=str(user.id),
        actor_user_id=user.id,
        request_id=request_id,
        metadata={"self_registered": True},
    )
    db.flush()
    db.commit()
    return build_user_profile(db, user)


def login_user(
    db: Session,
    payload: LoginRequest,
    *,
    request_id: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[AuthTokenResponse, str]:
    settings = get_settings()
    normalized = normalize_email(payload.email)

    user = db.execute(select(User).where(User.email == normalized)).scalar_one_or_none()
    if user is None or not verify_password(user.password_hash, payload.password):
        record_audit_event(
            db,
            action="auth.login_failed",
            resource_type="user",
            resource_id=str(user.id) if user else None,
            actor_user_id=user.id if user else None,
            request_id=request_id,
            metadata={"reason": "invalid_credentials"},
        )
        db.commit()
        raise NovaAppError(
            code="invalid_credentials",
            message="Invalid email or password.",
            status_code=401,
        )

    if not user.is_active:
        record_audit_event(
            db,
            action="auth.login_blocked_inactive",
            resource_type="user",
            resource_id=str(user.id),
            actor_user_id=user.id,
            request_id=request_id,
        )
        db.commit()
        raise NovaAppError(
            code="account_inactive",
            message="User account is inactive.",
            status_code=403,
        )

    if settings.require_email_verification and not user.is_verified:
        record_audit_event(
            db,
            action="auth.login_blocked_unverified",
            resource_type="user",
            resource_id=str(user.id),
            actor_user_id=user.id,
            request_id=request_id,
        )
        db.commit()
        raise NovaAppError(
            code="account_unverified",
            message="Account email verification is required before signing in.",
            status_code=403,
        )

    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)

    now = datetime.now(timezone.utc)
    user.last_login_at = now

    raw_refresh = generate_opaque_refresh_token()
    session_record = RefreshSession(
        user_id=user.id,
        token_family_id=uuid.uuid4(),
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        last_used_at=now,
        user_agent=user_agent[:256] if user_agent else None,
        ip_address=ip_address[:64] if ip_address else None,
    )
    db.add(session_record)

    access_token, expires_in = create_access_token(
        user_id=user.id,
        platform_role=user.platform_role,
    )

    record_audit_event(
        db,
        action="auth.login_succeeded",
        resource_type="refresh_session",
        resource_id=str(session_record.id),
        actor_user_id=user.id,
        request_id=request_id,
    )
    db.flush()
    db.commit()

    profile = build_user_profile(db, user)
    return (
        AuthTokenResponse(
            access_token=access_token,
            expires_in=expires_in,
            user=profile,
        ),
        raw_refresh,
    )


def rotate_refresh_session(
    db: Session,
    raw_refresh_token: str | None,
    *,
    request_id: str | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[AuthTokenResponse, str]:
    if not raw_refresh_token:
        raise NovaAppError(
            code="refresh_token_missing",
            message="Refresh session cookie is missing.",
            status_code=401,
        )

    settings = get_settings()
    token_hash = hash_refresh_token(raw_refresh_token)
    existing = db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    ).scalar_one_or_none()

    if existing is None:
        raise NovaAppError(
            code="invalid_refresh_token",
            message="Refresh session is invalid.",
            status_code=401,
        )

    now = datetime.now(timezone.utc)

    # Reuse detection: if an already-revoked or already-rotated token is presented again,
    # revoke the entire token family immediately to contain credential theft.
    if existing.revoked_at is not None or existing.replaced_by_session_id is not None:
        db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.token_family_id == existing.token_family_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now, revocation_reason="refresh_token_reuse_detected")
        )
        record_audit_event(
            db,
            action="auth.refresh_reuse_detected",
            resource_type="refresh_session",
            resource_id=str(existing.id),
            actor_user_id=existing.user_id,
            request_id=request_id,
            metadata={"token_family_id": str(existing.token_family_id)},
        )
        db.commit()
        raise NovaAppError(
            code="refresh_token_reused",
            message="Refresh token reuse detected. All sessions in this family were revoked.",
            status_code=401,
        )

    expires_at = existing.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        existing.revoked_at = now
        existing.revocation_reason = "expired"
        db.commit()
        raise NovaAppError(
            code="refresh_token_expired",
            message="Refresh session has expired.",
            status_code=401,
        )

    user = db.execute(select(User).where(User.id == existing.user_id)).scalar_one_or_none()
    if user is None or not user.is_active:
        existing.revoked_at = now
        existing.revocation_reason = "user_inactive"
        db.commit()
        raise NovaAppError(
            code="account_inactive",
            message="User account is inactive.",
            status_code=403,
        )
    if settings.require_email_verification and not user.is_verified:
        existing.revoked_at = now
        existing.revocation_reason = "user_unverified"
        db.commit()
        raise NovaAppError(
            code="account_unverified",
            message="Account email verification is required.",
            status_code=403,
        )

    new_raw_refresh = generate_opaque_refresh_token()
    new_session = RefreshSession(
        user_id=user.id,
        token_family_id=existing.token_family_id,
        token_hash=hash_refresh_token(new_raw_refresh),
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
        last_used_at=now,
        user_agent=user_agent[:256] if user_agent else None,
        ip_address=ip_address[:64] if ip_address else None,
    )
    db.add(new_session)
    db.flush()

    existing.revoked_at = now
    existing.revocation_reason = "rotated"
    existing.replaced_by_session_id = new_session.id
    existing.last_used_at = now

    access_token, expires_in = create_access_token(
        user_id=user.id,
        platform_role=user.platform_role,
    )

    record_audit_event(
        db,
        action="auth.refresh_rotated",
        resource_type="refresh_session",
        resource_id=str(new_session.id),
        actor_user_id=user.id,
        request_id=request_id,
    )
    db.commit()

    profile = build_user_profile(db, user)
    return (
        AuthTokenResponse(
            access_token=access_token,
            expires_in=expires_in,
            user=profile,
        ),
        new_raw_refresh,
    )


def revoke_refresh_session(
    db: Session,
    raw_refresh_token: str | None,
    *,
    request_id: str | None = None,
) -> bool:
    if not raw_refresh_token:
        return False

    token_hash = hash_refresh_token(raw_refresh_token)
    existing = db.execute(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash)
    ).scalar_one_or_none()

    if existing is None:
        return False

    now = datetime.now(timezone.utc)
    if existing.revoked_at is None:
        existing.revoked_at = now
        existing.revocation_reason = "logout"

    record_audit_event(
        db,
        action="auth.logout",
        resource_type="refresh_session",
        resource_id=str(existing.id),
        actor_user_id=existing.user_id,
        request_id=request_id,
    )
    db.commit()
    return True


def change_user_password(
    db: Session,
    user: User,
    payload: ChangePasswordRequest,
    *,
    request_id: str | None = None,
) -> None:
    if not verify_password(user.password_hash, payload.current_password):
        raise NovaAppError(
            code="invalid_current_password",
            message="Current password is incorrect.",
            status_code=400,
        )

    validate_password_policy(payload.new_password, email=user.email)
    if verify_password(user.password_hash, payload.new_password):
        raise NovaAppError(
            code="password_reuse_forbidden",
            message="New password must be different from your current password.",
            status_code=422,
        )

    now = datetime.now(timezone.utc)
    user.password_hash = hash_password(payload.new_password)

    # Revoke all active refresh sessions upon password rotation.
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=now, revocation_reason="password_changed")
    )

    record_audit_event(
        db,
        action="auth.password_changed",
        resource_type="user",
        resource_id=str(user.id),
        actor_user_id=user.id,
        request_id=request_id,
    )
    db.commit()
