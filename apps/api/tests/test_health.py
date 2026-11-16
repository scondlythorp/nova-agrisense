from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok_and_security_headers(unit_client: TestClient) -> None:
    response = unit_client.get("/api/v1/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Nova AgriSense API"
    assert body["environment"] == "test"

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "x-request-id" in response.headers


def test_readiness_endpoint_reports_503_when_database_unconfigured(
    unit_client: TestClient, monkeypatch
) -> None:
    monkeypatch.delenv("NOVA_DATABASE_URL", raising=False)
    from app.config.settings import get_settings

    get_settings.cache_clear()
    response = unit_client.get("/api/v1/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["database"]["configured"] is False


def test_meta_endpoint_exposes_gambia_regions_and_roles(unit_client: TestClient) -> None:
    response = unit_client.get("/api/v1/meta")
    assert response.status_code == 200
    body = response.json()
    assert "Lower River Region" in body["supported_regions"]
    assert "organization_admin" in body["roles"]
    assert body["phases"][0]["id"] == "phase-0"
    assert body["phases"][1]["status"] == "completed"
