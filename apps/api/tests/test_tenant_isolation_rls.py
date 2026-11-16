from __future__ import annotations

import os
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session, sessionmaker


def _register_and_login(client: TestClient, email: str, name: str) -> str:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongAgriPass123", "full_name": name},
    )
    assert reg.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongAgriPass123"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_org(client: TestClient, token: str, name: str, region: str) -> str:
    res = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": name,
            "organization_type": "cooperative",
            "region": region,
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


def test_api_cross_tenant_isolation(client: TestClient) -> None:
    token_a = _register_and_login(client, "lead.a@northbank.gm", "Modou Njie")
    token_b = _register_and_login(client, "lead.b@upperriver.gm", "Mariama Bah")
    token_outsider = _register_and_login(client, "outsider@gambia.gm", "Ebrima Sanyang")

    org_a = _create_org(client, token_a, "North Bank Rice Cooperative", "North Bank Region")
    org_b = _create_org(client, token_b, "Upper River Groundnut Union", "Upper River Region")

    # Missing tenant header is rejected.
    missing_ctx = client.get(
        f"/api/v1/organizations/{org_a}/members",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert missing_ctx.status_code == 400
    assert missing_ctx.json()["error"]["code"] == "organization_context_required"

    # Org A admin cannot access Org B using Org B's header or Org A's header.
    assert (
        client.get(
            f"/api/v1/organizations/{org_b}/members",
            headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_b},
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/organizations/{org_b}/audit-logs",
            headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a},
        ).status_code
        == 403
    )

    # User without any membership cannot access either organization.
    assert (
        client.get(
            f"/api/v1/organizations/{org_a}",
            headers={"Authorization": f"Bearer {token_outsider}", "X-Organization-ID": org_a},
        ).status_code
        == 403
    )


def test_postgresql_rls_enforces_strict_tenant_isolation(
    client: TestClient, db_session: Session
) -> None:
    """Verify PostgreSQL RLS directly under a non-superuser role (`NOBYPASSRLS`)."""
    token_a = _register_and_login(client, "rls.a@coop.gm", "RLS User A")
    token_b = _register_and_login(client, "rls.b@coop.gm", "RLS User B")

    org_a = _create_org(client, token_a, "RLS Coop A", "West Coast Region")
    org_b = _create_org(client, token_b, "RLS Coop B", "Central River Region")

    user_a_id = str(
        db_session.execute(
            text("SELECT id FROM users WHERE email = 'rls.a@coop.gm'")
        ).scalar_one()
    )

    # Verify RLS is both ENABLED and FORCED in PostgreSQL catalog.
    rls_flags = db_session.execute(
        text(
            "SELECT relname, relrowsecurity, relforcerowsecurity "
            "FROM pg_class WHERE relname IN ('organization_memberships', 'audit_logs') "
            "ORDER BY relname"
        )
    ).all()
    assert rls_flags == [
        ("audit_logs", True, True),
        ("organization_memberships", True, True),
    ]

    # Ensure we test against an unprivileged role so superuser BYPASSRLS cannot mask defects.
    current_user_is_super = db_session.execute(
        text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")
    ).scalar_one()

    if current_user_is_super:
        db_session.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nova_rls_verifier') THEN
                        CREATE ROLE nova_rls_verifier NOLOGIN NOBYPASSRLS;
                    END IF;
                END
                $$;
                """
            )
        )
        db_session.execute(text("GRANT USAGE ON SCHEMA public TO nova_rls_verifier"))
        db_session.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON organization_memberships, audit_logs "
                "TO nova_rls_verifier"
            )
        )
        db_session.commit()
        db_session.execute(text("SET LOCAL ROLE nova_rls_verifier"))

    # 1. With no tenant or user context set, PostgreSQL RLS must return 0 rows.
    db_session.execute(
        text(
            "SELECT set_config('app.current_organization_id', '', true), "
            "set_config('app.current_user_id', '', true), "
            "set_config('app.is_platform_admin', 'false', true)"
        )
    )
    assert db_session.execute(text("SELECT count(*) FROM organization_memberships")).scalar_one() == 0
    assert db_session.execute(text("SELECT count(*) FROM audit_logs")).scalar_one() == 0

    # 2. With Org A context set, only Org A rows are visible; Org B rows remain hidden.
    db_session.execute(
        text("SELECT set_config('app.current_organization_id', :oid, true)"),
        {"oid": org_a},
    )
    visible_org_ids = {
        str(row[0])
        for row in db_session.execute(
            text("SELECT DISTINCT organization_id FROM organization_memberships")
        ).all()
    }
    assert visible_org_ids == {org_a}
    assert org_b not in visible_org_ids

    audit_org_ids = {
        str(row[0])
        for row in db_session.execute(
            text("SELECT DISTINCT organization_id FROM audit_logs")
        ).all()
    }
    assert audit_org_ids == {org_a}
    assert org_b not in audit_org_ids

    # 3. With only current_user_id set (no org context), user CANNOT insert a membership into Org B.
    db_session.execute(
        text(
            "SELECT set_config('app.current_organization_id', '', true), "
            "set_config('app.current_user_id', :uid, true)"
        ),
        {"uid": user_a_id},
    )
    savepoint = db_session.begin_nested()
    try:
        try:
            db_session.execute(
                text(
                    "INSERT INTO organization_memberships "
                    "(id, organization_id, user_id, role, status) "
                    "VALUES (:id, :oid, :uid, 'ORGANIZATION_ADMIN', 'active')"
                ),
                {"id": str(uuid.uuid4()), "oid": org_b, "uid": user_a_id},
            )
            raise AssertionError("Expected PostgreSQL RLS to block cross-org membership insert")
        except ProgrammingError:
            savepoint.rollback()
    finally:
        if savepoint.is_active:
            savepoint.rollback()

    # 3b. With Org A context set, cross-tenant INSERT, UPDATE, and DELETE on Org B are denied.
    db_session.execute(
        text(
            "SELECT set_config('app.current_organization_id', :oid, true), "
            "set_config('app.current_user_id', :uid, true)"
        ),
        {"oid": org_a, "uid": user_a_id},
    )
    savepoint = db_session.begin_nested()
    try:
        try:
            db_session.execute(
                text(
                    "INSERT INTO organization_memberships "
                    "(id, organization_id, user_id, role, status) "
                    "VALUES (:id, :oid, :uid, 'ORGANIZATION_ADMIN', 'active')"
                ),
                {"id": str(uuid.uuid4()), "oid": org_b, "uid": user_a_id},
            )
            raise AssertionError("Expected PostgreSQL RLS to block Org A context inserting into Org B")
        except ProgrammingError:
            savepoint.rollback()
    finally:
        if savepoint.is_active:
            savepoint.rollback()

    updated_memberships = db_session.execute(
        text("UPDATE organization_memberships SET role = 'FARMER' WHERE organization_id = :oid"),
        {"oid": org_b},
    )
    assert updated_memberships.rowcount == 0
    deleted_memberships = db_session.execute(
        text("DELETE FROM organization_memberships WHERE organization_id = :oid"),
        {"oid": org_b},
    )
    assert deleted_memberships.rowcount == 0

    # 3c. Cross-tenant INSERT into audit_logs for Org B (or unflagged NULL org) is denied under Org A context.
    for target_org in (org_b, None):
        savepoint = db_session.begin_nested()
        try:
            try:
                db_session.execute(
                    text(
                        "INSERT INTO audit_logs "
                        "(id, organization_id, actor_user_id, action, resource_type, metadata_json) "
                        "VALUES (:id, :oid, :uid, 'cross.tenant.forge', 'organization', '{}'::jsonb)"
                    ),
                    {"id": str(uuid.uuid4()), "oid": target_org, "uid": user_a_id},
                )
                raise AssertionError(
                    f"Expected PostgreSQL RLS to block audit_logs insert for org={target_org}"
                )
            except ProgrammingError:
                savepoint.rollback()
        finally:
            if savepoint.is_active:
                savepoint.rollback()

    # 3d. record_audit_event allows system/auth audit writes without leaking app.audit_write_allowed
    # or exposing organization_id IS NULL rows to tenant SELECT queries.
    from app.services.audit_service import record_audit_event

    record_audit_event(
        db_session,
        action="auth.system_check",
        resource_type="user",
        resource_id=user_a_id,
        organization_id=None,
        actor_user_id=uuid.UUID(user_a_id),
    )
    assert (
        db_session.execute(
            text("SELECT current_setting('app.audit_write_allowed', true)")
        ).scalar_one()
        == "false"
    )
    assert (
        db_session.execute(
            text("SELECT count(*) FROM audit_logs WHERE organization_id IS NULL")
        ).scalar_one()
        == 0
    )

    # 4. audit_logs are append-only: UPDATE/DELETE affect 0 rows under RLS.
    updated = db_session.execute(text("UPDATE audit_logs SET action = 'tampered'"))
    assert updated.rowcount == 0
    deleted = db_session.execute(text("DELETE FROM audit_logs"))
    assert deleted.rowcount == 0


def test_pooled_connection_does_not_leak_tenant_context(client: TestClient) -> None:
    """Verify pool_size=1 connections never retain transaction-local RLS GUCs across requests."""
    token_a = _register_and_login(client, "pool.a@coop.gm", "Pool User A")
    org_a = _create_org(client, token_a, "Pool Coop A", "North Bank Region")

    db_url = os.environ.get("NOVA_TEST_DATABASE_URL") or os.environ.get("NOVA_DATABASE_URL")
    assert db_url
    pooled_engine = create_engine(db_url, pool_size=1, max_overflow=0, pool_pre_ping=True)
    PoolSession = sessionmaker(bind=pooled_engine, autoflush=False, autocommit=False)
    try:
        s1 = PoolSession()
        try:
            s1.execute(
                text("SELECT set_config('app.current_organization_id', :oid, true)"),
                {"oid": org_a},
            )
            assert (
                s1.execute(
                    text("SELECT current_setting('app.current_organization_id', true)")
                ).scalar_one()
                == org_a
            )
            s1.rollback()
        finally:
            s1.close()

        # Re-borrow the exact same pooled physical connection in a second session.
        s2 = PoolSession()
        try:
            leaked = s2.execute(
                text("SELECT NULLIF(current_setting('app.current_organization_id', true), '')")
            ).scalar_one()
            assert leaked is None
        finally:
            s2.rollback()
            s2.close()
    finally:
        pooled_engine.dispose()

