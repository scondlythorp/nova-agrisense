from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import PlatformRole
from app.models.user import User


def _create_user_and_token(client: TestClient, email: str, name: str) -> tuple[str, str]:
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
    return reg.json()["id"], login.json()["access_token"]


def test_anonymous_access_rejected(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/organizations").status_code == 401
    assert client.get("/api/v1/admin/organizations").status_code == 401


def test_privilege_escalation_and_rbac_enforcement(
    client: TestClient, db_session: Session
) -> None:
    _, admin_token = _create_user_and_token(client, "admin1@coop.gm", "Lamin Touray")
    _, analyst_token = _create_user_and_token(client, "analyst@coop.gm", "Fatou Ceesay")

    # Ordinary user cannot access platform admin endpoints.
    assert (
        client.get(
            "/api/v1/admin/organizations",
            headers={"Authorization": f"Bearer {admin_token}"},
        ).status_code
        == 403
    )

    # Create organization (assigns creator as ORGANIZATION_ADMIN).
    org_res = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Lower River Growers Cooperative",
            "organization_type": "cooperative",
            "region": "Lower River Region",
            "district": "Jarra West",
        },
    )
    assert org_res.status_code == 201
    org_id = org_res.json()["id"]
    assert org_res.json()["membership_role"] == "ORGANIZATION_ADMIN"

    # Admin invites analyst as READ_ONLY_ANALYST; cannot assign PLATFORM_ADMIN.
    bad_role = client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": org_id,
        },
        json={"email": "analyst@coop.gm", "role": "PLATFORM_ADMIN", "status": "active"},
    )
    assert bad_role.status_code == 422

    add_res = client.post(
        f"/api/v1/organizations/{org_id}/members",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": org_id,
        },
        json={
            "email": "analyst@coop.gm",
            "role": "READ_ONLY_ANALYST",
            "status": "invited",
        },
    )
    assert add_res.status_code == 201
    membership_id = add_res.json()["id"]

    # Analyst cannot access org before accepting invitation.
    assert (
        client.get(
            f"/api/v1/organizations/{org_id}",
            headers={
                "Authorization": f"Bearer {analyst_token}",
                "X-Organization-ID": org_id,
            },
        ).status_code
        == 403
    )

    # Analyst accepts invitation.
    accept_res = client.post(
        f"/api/v1/organizations/{org_id}/invitations/accept",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "active"

    # Analyst can read org profile, but cannot update org, manage members, or read audit logs.
    assert (
        client.get(
            f"/api/v1/organizations/{org_id}",
            headers={
                "Authorization": f"Bearer {analyst_token}",
                "X-Organization-ID": org_id,
            },
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/organizations/{org_id}",
            headers={
                "Authorization": f"Bearer {analyst_token}",
                "X-Organization-ID": org_id,
            },
            json={"name": "Unauthorized Rename"},
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/api/v1/organizations/{org_id}/audit-logs",
            headers={
                "Authorization": f"Bearer {analyst_token}",
                "X-Organization-ID": org_id,
            },
        ).status_code
        == 403
    )

    # Admin cannot demote/deactivate last active admin, but can update & deactivate analyst.
    members = client.get(
        f"/api/v1/organizations/{org_id}/members",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert members.status_code == 200
    admin_membership_id = next(
        m["id"] for m in members.json() if m["email"] == "admin1@coop.gm"
    )
    assert (
        client.delete(
            f"/api/v1/organizations/{org_id}/members/{admin_membership_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "X-Organization-ID": org_id,
            },
        ).status_code
        == 409
    )

    deact = client.delete(
        f"/api/v1/organizations/{org_id}/members/{membership_id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Organization-ID": org_id,
        },
    )
    assert deact.status_code == 200
    assert deact.json()["status"] == "deactivated"

    # Revoked member loses access immediately.
    assert (
        client.get(
            f"/api/v1/organizations/{org_id}",
            headers={
                "Authorization": f"Bearer {analyst_token}",
                "X-Organization-ID": org_id,
            },
        ).status_code
        == 403
    )

    # Promote a platform admin via DB and verify /api/v1/admin/organizations access.
    user_obj = db_session.execute(
        select(User).where(User.email == "admin1@coop.gm")
    ).scalar_one()
    user_obj.platform_role = PlatformRole.PLATFORM_ADMIN
    db_session.commit()

    platform_orgs = client.get(
        "/api/v1/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert platform_orgs.status_code == 200
    assert len(platform_orgs.json()) == 1


def test_cross_organization_membership_manipulation_and_all_roles(client: TestClient) -> None:
    _, admin_a_token = _create_user_and_token(client, "admin.a@coop.gm", "Admin A")
    _, admin_b_token = _create_user_and_token(client, "admin.b@coop.gm", "Admin B")
    _, officer_token = _create_user_and_token(client, "officer.b@coop.gm", "Officer B")
    _, farmer_token = _create_user_and_token(client, "farmer.b@coop.gm", "Farmer B")

    org_a = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {admin_a_token}"},
        json={"name": "Org A Coop", "organization_type": "cooperative", "region": "Banjul"},
    ).json()["id"]

    org_b = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {admin_b_token}"},
        json={"name": "Org B Coop", "organization_type": "ngo", "region": "Kanifing"},
    ).json()["id"]

    # Add Officer and Farmer directly as active members in Org B.
    officer_m = client.post(
        f"/api/v1/organizations/{org_b}/members",
        headers={"Authorization": f"Bearer {admin_b_token}", "X-Organization-ID": org_b},
        json={
            "email": "officer.b@coop.gm",
            "role": "AGRICULTURAL_OFFICER",
            "status": "active",
        },
    )
    assert officer_m.status_code == 201
    officer_membership_id = officer_m.json()["id"]

    farmer_m = client.post(
        f"/api/v1/organizations/{org_b}/members",
        headers={"Authorization": f"Bearer {admin_b_token}", "X-Organization-ID": org_b},
        json={"email": "farmer.b@coop.gm", "role": "FARMER", "status": "active"},
    )
    assert farmer_m.status_code == 201

    # Admin A cannot modify Org B membership even if substituting UUIDs or headers.
    assert (
        client.patch(
            f"/api/v1/organizations/{org_a}/members/{officer_membership_id}",
            headers={"Authorization": f"Bearer {admin_a_token}", "X-Organization-ID": org_a},
            json={"role": "ORGANIZATION_ADMIN"},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/organizations/{org_b}/members/{officer_membership_id}",
            headers={"Authorization": f"Bearer {admin_a_token}", "X-Organization-ID": org_b},
            json={"role": "ORGANIZATION_ADMIN"},
        ).status_code
        == 403
    )

    # Officer can read members, cannot manage members or self-escalate.
    assert (
        client.get(
            f"/api/v1/organizations/{org_b}/members",
            headers={"Authorization": f"Bearer {officer_token}", "X-Organization-ID": org_b},
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/api/v1/organizations/{org_b}/members/{officer_membership_id}",
            headers={"Authorization": f"Bearer {officer_token}", "X-Organization-ID": org_b},
            json={"role": "ORGANIZATION_ADMIN"},
        ).status_code
        == 403
    )

    # Farmer cannot read members list or audit logs, only org summary.
    assert (
        client.get(
            f"/api/v1/organizations/{org_b}",
            headers={"Authorization": f"Bearer {farmer_token}", "X-Organization-ID": org_b},
        ).status_code
        == 200
    )
    assert (
        client.get(
            f"/api/v1/organizations/{org_b}/members",
            headers={"Authorization": f"Bearer {farmer_token}", "X-Organization-ID": org_b},
        ).status_code
        == 403
    )

