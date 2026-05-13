from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import EvidencePackageResponse, StandardResponse

router = APIRouter(prefix="/forensics", tags=["forensics"])


@router.get("/{incident_id}")
async def get_forensics(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get forensics package for an incident."""
    # TODO(hackathon): Implement query
    return StandardResponse(data={})


@router.get("/{incident_id}/export")
async def export_forensics(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Export forensics package as ZIP."""
    # TODO(hackathon): Implement export
    return StandardResponse(message="Export queued")
