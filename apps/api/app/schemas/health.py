from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
    timestamp_utc: datetime


class DatabaseReadiness(BaseModel):
    configured: bool
    reachable: bool
    postgis_enabled: bool | None
    detail: str


class ReadinessChecks(BaseModel):
    database: DatabaseReadiness


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: ReadinessChecks
    timestamp_utc: datetime


class PhaseStatusItem(BaseModel):
    id: str
    name: str
    status: Literal["completed", "in_progress", "planned"]


class PlatformMetaResponse(BaseModel):
    platform: str
    api_version: str
    initial_geography: str
    supported_regions: list[str]
    roles: list[str]
    phases: list[PhaseStatusItem]
