from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NovaAppError
from app.database.session import set_rls_context
from app.models.audit_log import AuditLog
from app.models.enums import MembershipStatus, OrganizationRole, PlatformRole
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import (
    OrganizationCreateRequest,
    OrganizationMemberAddRequest,
    OrganizationMemberResponse,
    OrganizationMemberUpdateRoleRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
    OrganizationWithRoleResponse,
)
from app.security.rbac import get_permissions_for_role
from app.services.audit_service import record_audit_event
from app.services.auth_service import normalize_email


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or f"org-{uuid.uuid4().hex[:8]}"


def create_organization(
    db: Session,
    creator: User,
    payload: OrganizationCreateRequest,
    *,
    request_id: str | None = None,
) -> OrganizationWithRoleResponse:
    desired_slug = (payload.slug or _slugify(payload.name)).strip().lower()
    existing_slug = db.execute(
        select(Organization).where(Organization.slug == desired_slug)
    ).scalar_one_or_none()
    if existing_slug is not None:
        raise NovaAppError(
            code="organization_slug_conflict",
            message="An organization with this slug already exists.",
            status_code=409,
        )

    now = datetime.now(timezone.utc)
    org = Organization(
        name=payload.name.strip(),
        slug=desired_slug,
        organization_type=payload.organization_type,
        description=payload.description.strip() if payload.description else None,
        contact_email=normalize_email(payload.contact_email) if payload.contact_email else None,
        contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
        region=payload.region.strip(),
        district=payload.district.strip() if payload.district else None,
        is_active=True,
    )
    db.add(org)
    db.flush()

    # Bind transaction-local RLS context so the creator's initial admin membership insert passes RLS.
    set_rls_context(
        db,
        user_id=creator.id,
        organization_id=org.id,
        is_platform_admin=(creator.platform_role == PlatformRole.PLATFORM_ADMIN),
    )

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=creator.id,
        role=OrganizationRole.ORGANIZATION_ADMIN,
        status=MembershipStatus.ACTIVE,
        invited_by_user_id=creator.id,
        joined_at=now,
    )
    db.add(membership)

    record_audit_event(
        db,
        action="organization.created",
        resource_type="organization",
        resource_id=str(org.id),
        organization_id=org.id,
        actor_user_id=creator.id,
        request_id=request_id,
        metadata={"slug": org.slug, "region": org.region},
    )
    db.flush()
    db.commit()

    return OrganizationWithRoleResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        organization_type=org.organization_type,
        description=org.description,
        contact_email=org.contact_email,
        contact_phone=org.contact_phone,
        region=org.region,
        district=org.district,
        is_active=org.is_active,
        created_at=org.created_at,
        updated_at=org.updated_at,
        membership_role=membership.role,
        membership_status=membership.status,
        permissions=sorted(p.value for p in get_permissions_for_role(membership.role)),
    )


def list_user_organizations(
    db: Session, user: User
) -> list[OrganizationWithRoleResponse]:
    set_rls_context(
        db,
        user_id=user.id,
        organization_id=None,
        is_platform_admin=(user.platform_role == PlatformRole.PLATFORM_ADMIN),
    )
    rows = db.execute(
        select(Organization, OrganizationMembership)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status.in_(
                [MembershipStatus.ACTIVE, MembershipStatus.INVITED]
            ),
            Organization.is_active.is_(True),
        )
        .order_by(Organization.name.asc())
    ).all()

    return [
        OrganizationWithRoleResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            organization_type=org.organization_type,
            description=org.description,
            contact_email=org.contact_email,
            contact_phone=org.contact_phone,
            region=org.region,
            district=org.district,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at,
            membership_role=membership.role,
            membership_status=membership.status,
            permissions=sorted(p.value for p in get_permissions_for_role(membership.role)),
        )
        for org, membership in rows
    ]


def update_organization(
    db: Session,
    *,
    organization: Organization,
    actor: User,
    payload: OrganizationUpdateRequest,
    request_id: str | None = None,
) -> OrganizationResponse:
    if payload.name is not None:
        organization.name = payload.name.strip()
    if payload.description is not None:
        organization.description = payload.description.strip() or None
    if payload.contact_email is not None:
        organization.contact_email = normalize_email(payload.contact_email)
    if payload.contact_phone is not None:
        organization.contact_phone = payload.contact_phone.strip() or None
    if payload.region is not None:
        organization.region = payload.region.strip()
    if payload.district is not None:
        organization.district = payload.district.strip() or None

    record_audit_event(
        db,
        action="organization.updated",
        resource_type="organization",
        resource_id=str(organization.id),
        organization_id=organization.id,
        actor_user_id=actor.id,
        request_id=request_id,
    )
    db.flush()
    db.commit()
    return OrganizationResponse.model_validate(organization)


def list_organization_members(
    db: Session, organization_id: uuid.UUID
) -> list[OrganizationMemberResponse]:
    rows = db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(OrganizationMembership.organization_id == organization_id)
        .order_by(User.full_name.asc())
    ).all()

    return [
        OrganizationMemberResponse(
            id=membership.id,
            organization_id=membership.organization_id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role,
            status=membership.status,
            joined_at=membership.joined_at,
            created_at=membership.created_at,
        )
        for membership, user in rows
    ]


def add_organization_member(
    db: Session,
    *,
    organization_id: uuid.UUID,
    actor: User,
    payload: OrganizationMemberAddRequest,
    request_id: str | None = None,
) -> OrganizationMemberResponse:
    if payload.status in {MembershipStatus.SUSPENDED, MembershipStatus.DEACTIVATED}:
        raise NovaAppError(
            code="invalid_initial_membership_status",
            message="New memberships must be created with status 'active' or 'invited'.",
            status_code=422,
        )

    normalized_email = normalize_email(payload.email)
    target_user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()
    if target_user is None:
        raise NovaAppError(
            code="user_not_found",
            message=(
                "No registered user exists for this email. Email delivery is not configured; "
                "the user must register an account before being assigned to an organization."
            ),
            status_code=404,
        )

    if not target_user.is_active:
        raise NovaAppError(
            code="target_user_inactive",
            message="Cannot add an inactive user account to an organization.",
            status_code=400,
        )

    existing = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == target_user.id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.status in {MembershipStatus.ACTIVE, MembershipStatus.INVITED}:
            raise NovaAppError(
                code="membership_already_exists",
                message="User already has a membership or pending invitation in this organization.",
                status_code=409,
            )
        # Re-activate a previously deactivated membership safely.
        existing.role = payload.role
        existing.status = payload.status
        existing.invited_by_user_id = actor.id
        if payload.status == MembershipStatus.ACTIVE:
            if existing.joined_at is None:
                existing.joined_at = datetime.now(timezone.utc)
        else:
            existing.joined_at = None
        membership = existing
    else:
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=target_user.id,
            role=payload.role,
            status=payload.status,
            invited_by_user_id=actor.id,
            joined_at=(
                datetime.now(timezone.utc)
                if payload.status == MembershipStatus.ACTIVE
                else None
            ),
        )
        db.add(membership)
        db.flush()

    record_audit_event(
        db,
        action="membership.added",
        resource_type="organization_membership",
        resource_id=str(membership.id),
        organization_id=organization_id,
        actor_user_id=actor.id,
        request_id=request_id,
        metadata={"target_user_id": str(target_user.id), "role": payload.role.value},
    )
    db.flush()
    db.commit()

    return OrganizationMemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        created_at=membership.created_at,
    )


def accept_organization_invitation(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user: User,
    request_id: str | None = None,
) -> OrganizationMemberResponse:
    organization = db.execute(
        select(Organization).where(Organization.id == organization_id)
    ).scalar_one_or_none()
    if organization is None or not organization.is_active:
        raise NovaAppError(
            code="organization_not_found",
            message="Organization not found or inactive.",
            status_code=404,
        )

    set_rls_context(
        db,
        user_id=user.id,
        organization_id=organization_id,
        is_platform_admin=(user.platform_role == PlatformRole.PLATFORM_ADMIN),
    )
    membership = db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user.id,
        )
    ).scalar_one_or_none()
    if membership is None or membership.status != MembershipStatus.INVITED:
        raise NovaAppError(
            code="invitation_not_found",
            message="No pending invitation found for this organization.",
            status_code=404,
        )

    membership.status = MembershipStatus.ACTIVE
    membership.joined_at = datetime.now(timezone.utc)

    record_audit_event(
        db,
        action="membership.invitation_accepted",
        resource_type="organization_membership",
        resource_id=str(membership.id),
        organization_id=organization_id,
        actor_user_id=user.id,
        request_id=request_id,
    )
    db.flush()
    db.commit()

    return OrganizationMemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        created_at=membership.created_at,
    )


def _count_active_admins(db: Session, organization_id: uuid.UUID) -> int:
    count = db.execute(
        select(func.count(OrganizationMembership.id)).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.role == OrganizationRole.ORGANIZATION_ADMIN,
            OrganizationMembership.status == MembershipStatus.ACTIVE,
        )
    ).scalar_one()
    return int(count)


def update_member_role(
    db: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    actor: User,
    payload: OrganizationMemberUpdateRoleRequest,
    request_id: str | None = None,
) -> OrganizationMemberResponse:
    row = db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(
            OrganizationMembership.id == membership_id,
            OrganizationMembership.organization_id == organization_id,
        )
    ).first()
    if row is None:
        raise NovaAppError(
            code="membership_not_found",
            message="Organization membership not found.",
            status_code=404,
        )
    membership, target_user = row

    if (
        membership.role == OrganizationRole.ORGANIZATION_ADMIN
        and membership.status == MembershipStatus.ACTIVE
        and payload.role != OrganizationRole.ORGANIZATION_ADMIN
        and _count_active_admins(db, organization_id) <= 1
    ):
        raise NovaAppError(
            code="last_admin_protected",
            message="Cannot demote the last active organization administrator.",
            status_code=409,
        )

    previous_role = membership.role
    membership.role = payload.role

    record_audit_event(
        db,
        action="membership.role_updated",
        resource_type="organization_membership",
        resource_id=str(membership.id),
        organization_id=organization_id,
        actor_user_id=actor.id,
        request_id=request_id,
        metadata={"previous_role": previous_role.value, "new_role": payload.role.value},
    )
    db.flush()
    db.commit()

    return OrganizationMemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        created_at=membership.created_at,
    )


def deactivate_member(
    db: Session,
    *,
    organization_id: uuid.UUID,
    membership_id: uuid.UUID,
    actor: User,
    request_id: str | None = None,
) -> OrganizationMemberResponse:
    row = db.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(
            OrganizationMembership.id == membership_id,
            OrganizationMembership.organization_id == organization_id,
        )
    ).first()
    if row is None:
        raise NovaAppError(
            code="membership_not_found",
            message="Organization membership not found.",
            status_code=404,
        )
    membership, target_user = row

    if (
        membership.role == OrganizationRole.ORGANIZATION_ADMIN
        and membership.status == MembershipStatus.ACTIVE
        and _count_active_admins(db, organization_id) <= 1
    ):
        raise NovaAppError(
            code="last_admin_protected",
            message="Cannot deactivate the last active organization administrator.",
            status_code=409,
        )

    membership.status = MembershipStatus.DEACTIVATED

    record_audit_event(
        db,
        action="membership.deactivated",
        resource_type="organization_membership",
        resource_id=str(membership.id),
        organization_id=organization_id,
        actor_user_id=actor.id,
        request_id=request_id,
        metadata={"target_user_id": str(target_user.id)},
    )
    db.flush()
    db.commit()

    return OrganizationMemberResponse(
        id=membership.id,
        organization_id=membership.organization_id,
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        status=membership.status,
        joined_at=membership.joined_at,
        created_at=membership.created_at,
    )


def list_organization_audit_logs(
    db: Session, *, organization_id: uuid.UUID, limit: int = 50
) -> list[AuditLog]:
    return list(
        db.execute(
            select(AuditLog)
            .where(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
