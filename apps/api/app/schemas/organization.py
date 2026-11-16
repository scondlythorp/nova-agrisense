from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MembershipStatus, OrganizationRole, OrganizationType


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    organization_type: OrganizationType
    description: str | None = Field(default=None, max_length=2000)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    region: str = Field(min_length=2, max_length=100)
    district: str | None = Field(default=None, max_length=100)


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    region: str | None = Field(default=None, min_length=2, max_length=100)
    district: str | None = Field(default=None, max_length=100)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    organization_type: OrganizationType
    description: str | None
    contact_email: str | None
    contact_phone: str | None
    region: str
    district: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OrganizationWithRoleResponse(OrganizationResponse):
    membership_role: OrganizationRole
    membership_status: MembershipStatus
    permissions: list[str]


class OrganizationMemberAddRequest(BaseModel):
    email: EmailStr
    role: OrganizationRole
    status: MembershipStatus = MembershipStatus.INVITED


class OrganizationMemberUpdateRoleRequest(BaseModel):
    role: OrganizationRole


class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: OrganizationRole
    status: MembershipStatus
    joined_at: datetime | None
    created_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID | None
    actor_user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    request_id: str | None
    timestamp: datetime
    metadata_json: dict[str, Any]
