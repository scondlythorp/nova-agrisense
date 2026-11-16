from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.database.session import check_database_readiness
from app.schemas.health import (
    DatabaseReadiness,
    HealthResponse,
    PhaseStatusItem,
    PlatformMetaResponse,
    ReadinessChecks,
    ReadinessResponse,
)

router = APIRouter(tags=["Platform & Health"])

GAMBIA_ADMIN_REGIONS = [
    "Banjul",
    "Kanifing",
    "West Coast Region",
    "Lower River Region",
    "North Bank Region",
    "Central River Region",
    "Upper River Region",
]

PLATFORM_ROLES = [
    "platform_admin",
    "organization_admin",
    "agricultural_officer",
    "data_manager",
    "researcher",
    "cooperative_manager",
    "farmer",
    "read_only_analyst",
]


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.env,
        timestamp_utc=datetime.now(timezone.utc),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe (PostgreSQL & PostGIS)",
)
def readiness_check() -> JSONResponse:
    configured, reachable, postgis_enabled, detail = check_database_readiness()
    is_ready = configured and reachable
    payload = ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        checks=ReadinessChecks(
            database=DatabaseReadiness(
                configured=configured,
                reachable=reachable,
                postgis_enabled=postgis_enabled,
                detail=detail,
            )
        ),
        timestamp_utc=datetime.now(timezone.utc),
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload.model_dump(mode="json"),
    )


@router.get("/meta", response_model=PlatformMetaResponse, summary="Platform architecture metadata")
def platform_meta() -> PlatformMetaResponse:
    settings = get_settings()
    return PlatformMetaResponse(
        platform="Nova AgriSense",
        api_version=settings.app_version,
        initial_geography="The Gambia (West Africa Expansion Ready)",
        supported_regions=GAMBIA_ADMIN_REGIONS,
        roles=PLATFORM_ROLES,
        phases=[
            PhaseStatusItem(
                id="phase-0",
                name="Architecture and Repository Foundation",
                status="completed",
            ),
            PhaseStatusItem(
                id="phase-1",
                name="Database, Multi-Tenancy, Auth & RBAC",
                status="completed",
            ),
            PhaseStatusItem(
                id="phase-2",
                name="Core Agricultural Management",
                status="planned",
            ),
            PhaseStatusItem(
                id="phase-3",
                name="Agricultural Data Imports & Staging",
                status="planned",
            ),
            PhaseStatusItem(
                id="phase-4",
                name="Dashboard & Agricultural Analytics",
                status="planned",
            ),
            PhaseStatusItem(
                id="phase-5",
                name="Reporting & External Integrations",
                status="planned",
            ),
            PhaseStatusItem(
                id="phase-6",
                name="Explainable Agricultural Intelligence",
                status="planned",
            ),
            PhaseStatusItem(
                id="phase-7",
                name="Production Readiness & Security Audit",
                status="planned",
            ),
        ],
    )
