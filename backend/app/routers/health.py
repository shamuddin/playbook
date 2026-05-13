from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import HealthCheck

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
