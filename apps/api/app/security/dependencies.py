from __future__ import annotations

import hmac
import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.exceptions import NovaAppError
from app.database.session import get_db, set_rls_context
from app.models.enums import MembershipStatus, OrganizationRole, PlatformRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.security.rbac import Permission, has_permission
from app.security.tokens import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TenantContext:
    user: User
    organization: Organization
    membership: OrganizationMembership
    role: OrganizationRole


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise NovaAppError(
            code="authentication_required",
            message="Authentication credentials were not provided.",
            status_code=401,
        )

    claims = decode_access_token(credentials.credentials)

    user = db.execute(select(User).where(User.id == claims.user_id)).scalar_one_or_none()
    if user is None:
        raise NovaAppError(
            code="invalid_token",
            message="Authenticated user account does not exist.",
            status_code=401,
        )
    if not user.is_active:
        raise NovaAppError(
            code="account_inactive",
            message="User account is inactive.",
            status_code=403,
        )
    settings = get_settings()
    if settings.require_email_verification and not user.is_verified:
        raise NovaAppError(
            code="account_unverified",
            message="Account email verification is required.",
            status_code=403,
        )

    set_rls_context(
        db,
        user_id=user.id,
        organization_id=None,
        is_platform_admin=(user.platform_role == PlatformRole.PLATFORM_ADMIN),
    )
    return user


def require_platform_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.platform_role != PlatformRole.PLATFORM_ADMIN:
        raise NovaAppError(
            code="forbidden",
            message="Platform administrator privileges are required.",
            status_code=403,
        )
    return current_user


def resolve_tenant_context(
    x_organization_id: str | None = Header(default=None, alias="X-Organization-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TenantContext:
    """Resolve and verify active tenant membership from X-Organization-ID."""
    if not x_organization_id or not x_organization_id.strip():
        raise NovaAppError(
            code="organization_context_required",
            message="X-Organization-ID header is required for organization-scoped endpoints.",
            status_code=400,
        )

    try:
        org_id = uuid.UUID(x_organization_id.strip())
    except ValueError as exc:
        raise NovaAppError(
            code="invalid_organization_id",
            message="X-Organization-ID must be a valid UUID.",
            status_code=400,
        ) from exc

    organization = db.execute(
        select(Organization).where(Organization.id == org_id)
    ).scalar_one_or_none()
    if organization is None or not organization.is_active:
        raise NovaAppError(
            code="organization_not_found",
            message="Organization not found or inactive.",
            status_code=404,
        )

    # Bind transaction-local user + organization context before querying RLS-protected memberships.
    set_rls_context(
        db,
        user_id=current_user.id,
        organization_id=org_id,
        is_platform_admin=(current_user.platform_role == PlatformRole.PLATFORM_ADMIN),
    )

    membership = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == org_id,
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        )
    ).scalar_one_or_none()

    if membership is None:
        raise NovaAppError(
            code="membership_forbidden",
            message="You do not have an active membership in this organization.",
            status_code=403,
        )

    return TenantContext(
        user=current_user,
        organization=organization,
        membership=membership,
        role=membership.role,
    )


def require_org_permission(permission: Permission):
    def _dependency(tenant: TenantContext = Depends(resolve_tenant_context)) -> TenantContext:
        if not has_permission(tenant.role, permission):
            raise NovaAppError(
                code="permission_denied",
                message=f"Role '{tenant.role.value}' lacks permission '{permission.value}'.",
                status_code=403,
            )
        return tenant

    return _dependency


def verify_csrf_for_cookie_request(request: Request) -> None:
    """Verify double-submit CSRF cookie + X-CSRF-Token header on cookie-auth POST endpoints."""
    settings = get_settings()
    refresh_cookie = request.cookies.get(settings.refresh_cookie_name)
    if not refresh_cookie:
        return

    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")
    if not csrf_cookie or not csrf_header or not hmac.compare_digest(csrf_cookie, csrf_header):
        raise NovaAppError(
            code="csrf_validation_failed",
            message="CSRF token validation failed.",
            status_code=403,
        )
