from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "current_password",
    "new_password",
    "token",
    "refresh_token",
    "access_token",
    "secret",
    "secret_key",
    "authorization",
}


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        if str(key).lower() in _SENSITIVE_KEYS:
            continue
        clean[str(key)] = value
    return clean


def record_audit_event(
    db: Session,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    organization_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Persist an append-only audit log entry without sensitive credentials."""
    entry = AuditLog(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        metadata_json=sanitize_metadata(metadata),
    )
    bind = db.get_bind()
    is_pg = bind is not None and bind.dialect.name == "postgresql"
    if is_pg:
        db.execute(text("SELECT set_config('app.audit_write_allowed', 'true', true)"))
    db.add(entry)
    db.flush([entry])
    if is_pg:
        db.execute(text("SELECT set_config('app.audit_write_allowed', 'false', true)"))
    return entry
