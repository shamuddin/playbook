from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    IncidentCreate,
    IncidentFilter,
    IncidentListResponse,
    IncidentResponse,
    StandardResponse,
    TimelineEventResponse,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> IncidentListResponse:
    """List incidents with filtering and pagination."""
    # TODO(hackathon): Implement query
    return IncidentListResponse(data=[], total=0, page=page, page_size=page_size)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Get a single incident by ID."""
    # TODO(hackathon): Implement query
    raise NotImplementedError()


@router.post("/{incident_id}/classify", response_model=StandardResponse)
async def classify_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Classify an incident."""
    # TODO(hackathon): Implement classification
    return StandardResponse(message="Classification queued")


@router.post("/{incident_id}/respond", response_model=StandardResponse)
async def respond_to_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Trigger playbook response for an incident."""
    # TODO(hackathon): Implement response
    return StandardResponse(message="Response queued")


@router.get("/{incident_id}/timeline", response_model=list[TimelineEventResponse])
async def get_timeline(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TimelineEventResponse]:
    """Get incident timeline."""
    # TODO(hackathon): Implement query
    return []
