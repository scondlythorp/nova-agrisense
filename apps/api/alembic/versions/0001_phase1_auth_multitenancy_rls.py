"""Phase 1: Users, Organizations, Memberships, Refresh Sessions, Audit Logs, and RLS.

Revision ID: 0001_phase1_auth_rls
Revises:
Create Date: 2026-11-14 00:00:00+00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_phase1_auth_rls"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("platform_role", sa.String(length=32), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"], unique=False)

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("organization_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.String(length=320), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("slug", name=op.f("uq_organizations_slug")),
    )
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"], unique=True)
    op.create_index(
        "ix_organizations_region_active",
        "organizations",
        ["region", "is_active"],
        unique=False,
    )

    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_user_id"],
            ["users.id"],
            name=op.f("fk_organization_memberships_invited_by_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_organization_memberships_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_organization_memberships_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organization_memberships")),
        sa.UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_organization_memberships_org_user",
        ),
    )
    op.create_index(
        op.f("ix_organization_memberships_organization_id"),
        "organization_memberships",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_organization_memberships_user_id"),
        "organization_memberships",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_org_memberships_user_status",
        "organization_memberships",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_org_memberships_org_role",
        "organization_memberships",
        ["organization_id", "role"],
        unique=False,
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("replaced_by_session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=256), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["replaced_by_session_id"],
            ["refresh_sessions.id"],
            name=op.f("fk_refresh_sessions_replaced_by_session_id_refresh_sessions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_sessions_token_hash")),
    )
    op.create_index(
        op.f("ix_refresh_sessions_token_hash"),
        "refresh_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_sessions_user_id"),
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_sessions_user_active",
        "refresh_sessions",
        ["user_id", "revoked_at"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_sessions_family_id",
        "refresh_sessions",
        ["token_family_id"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name=op.f("fk_audit_logs_actor_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_audit_logs_organization_id_organizations"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(
        op.f("ix_audit_logs_actor_user_id"),
        "audit_logs",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_organization_id"),
        "audit_logs",
        ["organization_id"],
        unique=False,
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index(
        "ix_audit_logs_org_timestamp",
        "audit_logs",
        ["organization_id", "timestamp"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_actor_timestamp",
        "audit_logs",
        ["actor_user_id", "timestamp"],
        unique=False,
    )

    # PostgreSQL Row-Level Security (RLS) for tenant-scoped tables.
    # Policies rely strictly on transaction-local settings (`set_config(..., true)`).
    # Unset context evaluates to NULL and denies all tenant access.
    op.execute("ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organization_memberships FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY org_memberships_tenant_select
        ON organization_memberships
        FOR SELECT
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        );
        """
    )
    op.execute(
        """
        CREATE POLICY org_memberships_tenant_insert
        ON organization_memberships
        FOR INSERT
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        );
        """
    )
    op.execute(
        """
        CREATE POLICY org_memberships_tenant_update
        ON organization_memberships
        FOR UPDATE
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        )
        WITH CHECK (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        );
        """
    )
    op.execute(
        """
        CREATE POLICY org_memberships_tenant_delete
        ON organization_memberships
        FOR DELETE
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        );
        """
    )

    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY audit_logs_tenant_read
        ON audit_logs
        FOR SELECT
        USING (
            organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        );
        """
    )
    op.execute(
        """
        CREATE POLICY audit_logs_append_only_insert
        ON audit_logs
        FOR INSERT
        WITH CHECK (
            current_setting('app.audit_write_allowed', true) = 'true'
            OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            OR current_setting('app.is_platform_admin', true) = 'true'
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS audit_logs_append_only_insert ON audit_logs;")
    op.execute("DROP POLICY IF EXISTS audit_logs_tenant_read ON audit_logs;")
    op.execute("ALTER TABLE audit_logs NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY;")

    op.execute("DROP POLICY IF EXISTS org_memberships_tenant_delete ON organization_memberships;")
    op.execute("DROP POLICY IF EXISTS org_memberships_tenant_update ON organization_memberships;")
    op.execute("DROP POLICY IF EXISTS org_memberships_tenant_insert ON organization_memberships;")
    op.execute("DROP POLICY IF EXISTS org_memberships_tenant_select ON organization_memberships;")
    op.execute("ALTER TABLE organization_memberships NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE organization_memberships DISABLE ROW LEVEL SECURITY;")

    op.drop_index("ix_audit_logs_actor_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_org_timestamp", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_organization_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_refresh_sessions_family_id", table_name="refresh_sessions")
    op.drop_index("ix_refresh_sessions_user_active", table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_user_id"), table_name="refresh_sessions")
    op.drop_index(op.f("ix_refresh_sessions_token_hash"), table_name="refresh_sessions")
    op.drop_table("refresh_sessions")

    op.drop_index("ix_org_memberships_org_role", table_name="organization_memberships")
    op.drop_index("ix_org_memberships_user_status", table_name="organization_memberships")
    op.drop_index(
        op.f("ix_organization_memberships_user_id"),
        table_name="organization_memberships",
    )
    op.drop_index(
        op.f("ix_organization_memberships_organization_id"),
        table_name="organization_memberships",
    )
    op.drop_table("organization_memberships")

    op.drop_index("ix_organizations_region_active", table_name="organizations")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_table("organizations")

    op.drop_index("ix_users_email_active", table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
