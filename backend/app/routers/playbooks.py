from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import PlaybookResponse, StandardResponse

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("", response_model=StandardResponse)
async def list_playbooks(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List available playbooks."""
    # TODO(hackathon): Implement query
    return StandardResponse(data=[])


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: str,
    db: AsyncSession = Depends(get_db),
) -> PlaybookResponse:
    """Get a single playbook definition."""
    # TODO(hackathon): Implement query
    raise NotImplementedError()
