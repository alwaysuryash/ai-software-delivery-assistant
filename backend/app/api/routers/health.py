"""Liveness / readiness endpoints (NFR-02, observability)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession
from app.api.schemas import HealthCheckResponse
from app.core.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/healthz", response_model=HealthCheckResponse)
async def liveness() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="ok", service=get_settings().otel_service_name, time=datetime.now(UTC)
    )


@router.get("/readyz", response_model=HealthCheckResponse)
async def readiness(session: DbSession) -> HealthCheckResponse:
    # Verify DB connectivity; failure surfaces (BRD: make every failure visible).
    await session.execute(text("SELECT 1"))
    return HealthCheckResponse(
        status="ready", service=get_settings().otel_service_name, time=datetime.now(UTC)
    )
