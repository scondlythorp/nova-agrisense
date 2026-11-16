from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.exceptions import NovaAppError
from app.database.session import get_db
from app.models.user import User
from app.schemas.organization import (
    AuditLogResponse,
    OrganizationCreateRequest,
    OrganizationMemberAddRequest,
    OrganizationMemberResponse,
    OrganizationMemberUpdateRoleRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
    OrganizationWithRoleResponse,
)
from app.security.dependencies import TenantContext, get_current_user, require_org_permission
from app.security.rbac import Permission
from app.services import organization_service

router = APIRouter(prefix="/organizations", tags=["Organizations & Memberships"])


def _assert_matching_org_path(organization_id: uuid.UUID, tenant: TenantContext) -> None:
    if organization_id != tenant.organization.id:
        raise NovaAppError(
            code="organization_context_mismatch",
            message="Path organization ID does not match X-Organization-ID context.",
            status_code=403,
        )


@router.post(
    "",
    response_model=OrganizationWithRoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization and assign creator as Organization Admin",
)
def create_organization(
    payload: OrganizationCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationWithRoleResponse:
    return organization_service.create_organization(
        db,
        current_user,
        payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "",
    response_model=list[OrganizationWithRoleResponse],
    summary="List organizations where the authenticated user holds a membership",
)
def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[OrganizationWithRoleResponse]:
    return organization_service.list_user_organizations(db, current_user)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization details (requires active membership and X-Organization-ID)",
)
def get_organization_detail(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(require_org_permission(Permission.ORG_READ)),
) -> OrganizationResponse:
    _assert_matching_org_path(organization_id, tenant)
    return OrganizationResponse.model_validate(tenant.organization)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization profile (Organization Admin only)",
)
def update_organization_detail(
    organization_id: uuid.UUID,
    payload: OrganizationUpdateRequest,
    request: Request,
    tenant: TenantContext = Depends(require_org_permission(Permission.ORG_UPDATE)),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    _assert_matching_org_path(organization_id, tenant)
    return organization_service.update_organization(
        db,
        organization=tenant.organization,
        actor=tenant.user,
        payload=payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
    summary="List organization members (tenant-isolated)",
)
def list_members(
    organization_id: uuid.UUID,
    tenant: TenantContext = Depends(require_org_permission(Permission.MEMBERSHIP_READ)),
    db: Session = Depends(get_db),
) -> list[OrganizationMemberResponse]:
    _assert_matching_org_path(organization_id, tenant)
    return organization_service.list_organization_members(db, tenant.organization.id)


@router.post(
    "/{organization_id}/members",
    response_model=OrganizationMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or invite a registered user to the organization (Organization Admin only)",
)
def add_member(
    organization_id: uuid.UUID,
    payload: OrganizationMemberAddRequest,
    request: Request,
    tenant: TenantContext = Depends(require_org_permission(Permission.MEMBERSHIP_MANAGE)),
    db: Session = Depends(get_db),
) -> OrganizationMemberResponse:
    _assert_matching_org_path(organization_id, tenant)
    return organization_service.add_organization_member(
        db,
        organization_id=tenant.organization.id,
        actor=tenant.user,
        payload=payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post(
    "/{organization_id}/invitations/accept",
    response_model=OrganizationMemberResponse,
    summary="Accept an administrator-issued pending invitation",
)
def accept_invitation(
    organization_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMemberResponse:
    return organization_service.accept_organization_invitation(
        db,
        organization_id=organization_id,
        user=current_user,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch(
    "/{organization_id}/members/{membership_id}",
    response_model=OrganizationMemberResponse,
    summary="Update member organization role (Organization Admin only)",
)
def update_member_role(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: OrganizationMemberUpdateRoleRequest,
    request: Request,
    tenant: TenantContext = Depends(require_org_permission(Permission.MEMBERSHIP_MANAGE)),
    db: Session = Depends(get_db),
) -> OrganizationMemberResponse:
    _assert_matching_org_path(organization_id, tenant)
    return organization_service.update_member_role(
        db,
        organization_id=tenant.organization.id,
        membership_id=membership_id,
        actor=tenant.user,
        payload=payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete(
    "/{organization_id}/members/{membership_id}",
    response_model=OrganizationMemberResponse,
    summary="Deactivate an organization membership (Organization Admin only)",
)
def deactivate_member(
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    request: Request,
    tenant: TenantContext = Depends(require_org_permission(Permission.MEMBERSHIP_MANAGE)),
    db: Session = Depends(get_db),
) -> OrganizationMemberResponse:
    _assert_matching_org_path(organization_id, tenant)
    return organization_service.deactivate_member(
        db,
        organization_id=tenant.organization.id,
        membership_id=membership_id,
        actor=tenant.user,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get(
    "/{organization_id}/audit-logs",
    response_model=list[AuditLogResponse],
    summary="List tenant-scoped audit logs (Organization Admin only)",
)
def list_audit_logs(
    organization_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    tenant: TenantContext = Depends(require_org_permission(Permission.AUDIT_READ)),
    db: Session = Depends(get_db),
) -> list[AuditLogResponse]:
    _assert_matching_org_path(organization_id, tenant)
    rows = organization_service.list_organization_audit_logs(
        db,
        organization_id=tenant.organization.id,
        limit=limit,
    )
    return [AuditLogResponse.model_validate(row) for row in rows]
