from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MembershipStatus, OrganizationRole, OrganizationType, PlatformRole


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=150)
    phone_number: str | None = Field(default=None, max_length=32)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class MembershipSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str
    organization_slug: str
    organization_type: OrganizationType
    role: OrganizationRole
    status: MembershipStatus
    permissions: list[str]
    joined_at: datetime | None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone_number: str | None
    is_active: bool
    is_verified: bool
    platform_role: PlatformRole | None
    last_login_at: datetime | None
    created_at: datetime
    memberships: list[MembershipSummary] = Field(default_factory=list)


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    csrf_token: str | None = None
    user: UserProfileResponse


class LogoutResponse(BaseModel):
    revoked: bool
    message: str
