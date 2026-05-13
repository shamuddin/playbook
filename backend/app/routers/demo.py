from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import get_db
from app.schemas import DemoSeedRequest, DemoSeedResponse, StandardResponse

router = APIRouter(prefix="/demo", tags=["demo"])
settings = get_settings()


def require_demo_mode():
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo endpoints are only available in DEMO_MODE",
        )


@router.post("/seed", response_model=DemoSeedResponse)
async def seed_demo_data(
    request: DemoSeedRequest = DemoSeedRequest(),
    db: AsyncSession = Depends(get_db),
) -> DemoSeedResponse:
    """Seed demo scenarios. Only available in DEMO_MODE."""
    require_demo_mode()
    # TODO(hackathon): Implement demo seeding
    return DemoSeedResponse(scenarios_seeded=6, incidents_created=20)


@router.post("/reset")
async def reset_demo_data(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Reset all demo data. Only available in DEMO_MODE."""
    require_demo_mode()
    # TODO(hackathon): Implement demo reset
    return StandardResponse(message="Demo data reset")


@router.post("/trigger")
async def trigger_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Trigger a specific demo scenario. Only available in DEMO_MODE."""
    require_demo_mode()
    # TODO(hackathon): Implement scenario trigger
    return StandardResponse(message=f"Scenario {scenario_id} triggered")
