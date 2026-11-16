from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.models.enums import OrganizationType

if TYPE_CHECKING:
    from app.models.membership import OrganizationMembership


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_region_active", "region", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(120),
        unique=True,
        index=True,
        nullable=False,
    )
    organization_type: Mapped[OrganizationType] = mapped_column(
        SAEnum(OrganizationType, name="organization_type_enum", native_enum=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    contact_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )
    region: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    memberships: Mapped[list[OrganizationMembership]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
    )
