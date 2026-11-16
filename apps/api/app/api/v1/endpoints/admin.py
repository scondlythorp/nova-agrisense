from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import AuditLogResponse, OrganizationResponse
from app.security.dependencies import require_platform_admin

router = APIRouter(prefix="/admin", tags=["Platform Administration"])


@router.get(
    "/organizations",
    response_model=list[OrganizationResponse],
    summary="List all platform organizations (Platform Admin only)",
)
def list_all_organizations(
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[OrganizationResponse]:
    orgs = db.execute(select(Organization).order_by(Organization.created_at.desc())).scalars().all()
    return [OrganizationResponse.model_validate(org) for org in orgs]


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
    summary="List platform-wide audit events (Platform Admin only)",
)
def list_platform_audit_logs(
    limit: int = Query(default=100, ge=1, le=250),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> list[AuditLogResponse]:
    logs = (
        db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit))
        .scalars()
        .all()
    )
    return [AuditLogResponse.model_validate(row) for row in logs]
