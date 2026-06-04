from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from ..core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
    }


@router.get("/api/v1/")
async def api_root() -> dict:
    return {
        "message": "HelixOps API v1",
        "version": settings.APP_VERSION,
        "routes": [
            "/api/v1/auth",
            "/api/v1/clinics",
            "/api/v1/patients",
            "/api/v1/appointments",
            "/api/v1/documents",
            "/api/v1/notifications",
            "/api/v1/analytics",
        ],
    }
