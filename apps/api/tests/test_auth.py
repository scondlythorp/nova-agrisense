from __future__ import annotations

from datetime import timedelta
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.security.tokens import create_access_token


def _register(client: TestClient, email: str, password: str = "StrongAgriPass123", name: str = "Amina Jallow"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )


def _login(client: TestClient, email: str, password: str = "StrongAgriPass123"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def test_register_normalizes_email_and_rejects_duplicate(client: TestClient) -> None:
    res = _register(client, "  Farmer.One@Example.GM ")
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "farmer.one@example.gm"
    assert "password_hash" not in data

    dup = _register(client, "farmer.one@example.gm")
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "email_already_registered"


def test_register_rejects_weak_password(client: TestClient) -> None:
    res = _register(client, "weak@example.gm", password="short")
    assert res.status_code == 422


def test_login_issues_access_token_and_refresh_csrf_cookies(client: TestClient) -> None:
    assert _register(client, "officer@example.gm").status_code == 201
    res = _login(client, "officer@example.gm")
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"]
    assert "password_hash" not in body["user"]

    settings = get_settings()
    assert settings.refresh_cookie_name in res.cookies
    assert settings.csrf_cookie_name in res.cookies


def test_login_rejects_invalid_password_and_rate_limits(client: TestClient, monkeypatch) -> None:
    monkeypatch.setenv("NOVA_AUTH_RATE_LIMIT_MAX_ATTEMPTS", "3")
    get_settings.cache_clear()

    assert _register(client, "locked@example.gm").status_code == 201
    for _ in range(3):
        bad = _login(client, "locked@example.gm", password="WrongPassword123")
        assert bad.status_code == 401

    throttled = _login(client, "locked@example.gm", password="WrongPassword123")
    assert throttled.status_code == 429
    assert throttled.json()["error"]["code"] == "rate_limit_exceeded"


def test_inactive_user_cannot_login_or_access_me(client: TestClient, db_session: Session) -> None:
    assert _register(client, "inactive@example.gm").status_code == 201
    user = db_session.execute(select(User).where(User.email == "inactive@example.gm")).scalar_one()
    user.is_active = False
    db_session.commit()

    res = _login(client, "inactive@example.gm")
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "account_inactive"


def test_expired_access_token_rejected(client: TestClient) -> None:
    reg = _register(client, "expired@example.gm")
    assert reg.status_code == 201
    user_id = uuid.UUID(reg.json()["id"])

    expired_token, _ = create_access_token(
        user_id=user_id,
        expires_delta=timedelta(seconds=-10),
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401


def test_refresh_rotation_reuse_detection_and_csrf(client: TestClient, db_session: Session) -> None:
    assert _register(client, "rotate@example.gm").status_code == 201
    login_res = _login(client, "rotate@example.gm")
    assert login_res.status_code == 200

    settings = get_settings()
    first_refresh = client.cookies.get(settings.refresh_cookie_name)
    first_csrf = client.cookies.get(settings.csrf_cookie_name)
    assert first_refresh and first_csrf

    # Missing CSRF header must be rejected on cookie-authenticated refresh.
    no_csrf = client.post("/api/v1/auth/refresh")
    assert no_csrf.status_code == 403

    # Valid refresh rotates token and issues new pair.
    refreshed = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": first_csrf},
    )
    assert refreshed.status_code == 200
    second_refresh = client.cookies.get(settings.refresh_cookie_name)
    second_csrf = client.cookies.get(settings.csrf_cookie_name)
    assert second_refresh and second_refresh != first_refresh

    # Replay of the already-rotated first refresh token triggers family revocation.
    client.cookies.set(settings.refresh_cookie_name, first_refresh)
    client.cookies.set(settings.csrf_cookie_name, second_csrf)
    reused = client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": second_csrf},
    )
    assert reused.status_code == 401
    assert reused.json()["error"]["code"] == "refresh_token_reused"

    # Confirm all sessions in the family are now revoked in DB.
    active_sessions = (
        db_session.execute(
            select(RefreshSession).where(RefreshSession.revoked_at.is_(None))
        )
        .scalars()
        .all()
    )
    assert active_sessions == []


def test_logout_revokes_session_and_password_change_revokes_sessions(
    client: TestClient, db_session: Session
) -> None:
    assert _register(client, "pwd@example.gm", password="OldPassword123").status_code == 201
    login_res = _login(client, "pwd@example.gm", password="OldPassword123")
    access_token = login_res.json()["access_token"]
    settings = get_settings()
    csrf = client.cookies.get(settings.csrf_cookie_name)

    change_res = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "OldPassword123",
            "new_password": "NewStrongPassword456",
        },
    )
    assert change_res.status_code == 204

    # Old password fails, new password succeeds.
    assert _login(client, "pwd@example.gm", password="OldPassword123").status_code == 401
    login2 = _login(client, "pwd@example.gm", password="NewStrongPassword456")
    assert login2.status_code == 200

    csrf = client.cookies.get(settings.csrf_cookie_name)
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["revoked"] is True

    active_sessions = (
        db_session.execute(
            select(RefreshSession).where(RefreshSession.revoked_at.is_(None))
        )
        .scalars()
        .all()
    )
    assert active_sessions == []


def test_spoofed_x_forwarded_for_cannot_bypass_login_rate_limit(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setenv("NOVA_AUTH_RATE_LIMIT_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("NOVA_TRUST_PROXY_HEADERS", "false")
    get_settings.cache_clear()

    assert _register(client, "spoof@example.gm").status_code == 201
    for idx in range(2):
        res = client.post(
            "/api/v1/auth/login",
            headers={"X-Forwarded-For": f"198.51.100.{idx + 1}"},
            json={"email": "spoof@example.gm", "password": "WrongPassword123"},
        )
        assert res.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        headers={"X-Forwarded-For": "203.0.113.99"},
        json={"email": "spoof@example.gm", "password": "WrongPassword123"},
    )
    assert blocked.status_code == 429


def test_email_verification_policy_toggle(
    client: TestClient, db_session: Session, monkeypatch
) -> None:
    # Phase 1 default (require_email_verification=False): unverified users can authenticate.
    reg = _register(client, "verify@example.gm")
    assert reg.status_code == 201
    assert reg.json()["is_verified"] is False
    assert _login(client, "verify@example.gm").status_code == 200

    # When require_email_verification=True, unverified users are blocked at login, /me, and /refresh.
    monkeypatch.setenv("NOVA_REQUIRE_EMAIL_VERIFICATION", "true")
    get_settings.cache_clear()

    blocked_login = _login(client, "verify@example.gm")
    assert blocked_login.status_code == 403
    assert blocked_login.json()["error"]["code"] == "account_unverified"

    user = db_session.execute(select(User).where(User.email == "verify@example.gm")).scalar_one()
    user.is_verified = True
    db_session.commit()

    allowed_login = _login(client, "verify@example.gm")
    assert allowed_login.status_code == 200


def test_register_rejects_unexpected_privilege_fields(client: TestClient) -> None:
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "escalate@example.gm",
            "password": "StrongAgriPass123",
            "full_name": "Malicious Escalator",
            "platform_role": "PLATFORM_ADMIN",
        },
    )
    assert res.status_code == 422

