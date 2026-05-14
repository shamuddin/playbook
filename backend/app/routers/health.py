from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HealthCheck, StandardResponse

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    """Health check endpoint. Public — no auth required."""
    components = {
        "database": "healthy",
        "api": "healthy",
    }
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        components=components,
    )


@router.get("/settings/public", response_model=StandardResponse)
async def public_settings() -> StandardResponse:
    """Return non-sensitive system configuration for the frontend Settings page.

    Public — no auth required so the Settings page can display system info
    before the user authenticates.
    """
    from app.core.config import get_settings

    settings = get_settings()
    return StandardResponse(
        data={
            "environment": settings.environment,
            "demo_mode": settings.demo_mode,
            "version": "0.1.0",
            "notifications": {
                "slack": bool(settings.slack_webhook_url),
                "email": bool(settings.smtp_host and settings.smtp_from),
                "pagerduty": bool(settings.pagerduty_routing_key),
            },
        }
    )
