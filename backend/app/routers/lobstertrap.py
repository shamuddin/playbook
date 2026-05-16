"""Lobster Trap DPI integration router."""

from fastapi import APIRouter, Depends, Query, status
from fastapi.exceptions import HTTPException

from app.core.config import get_settings
from app.core.security import get_current_user
from app.schemas import StandardResponse
from app.services.lobstertrap_integration import (
    get_lobstertrap_status,
    get_recent_logs,
    run_lobstertrap_test,
)

router = APIRouter(prefix="/integrations/lobstertrap", tags=["lobstertrap"])
settings = get_settings()


@router.get("/status", response_model=StandardResponse)
async def lobstertrap_status(
    _=Depends(get_current_user),
) -> StandardResponse:
    """Return whether Lobster Trap is running, its PID, port, and loaded policy."""
    status_info = get_lobstertrap_status()
    return StandardResponse(
        data=status_info,
        message="Lobster Trap status retrieved",
    )


@router.post("/test", response_model=StandardResponse)
async def lobstertrap_test(
    _=Depends(get_current_user),
) -> StandardResponse:
    """Run `./lobstertrap test` and return the test results."""
    result = await run_lobstertrap_test()
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.get("error", "Test command failed"),
        )
    return StandardResponse(
        data=result,
        message="Lobster Trap policy test completed",
    )


@router.get("/logs", response_model=StandardResponse)
async def lobstertrap_logs(
    limit: int = Query(50, ge=1, le=500),
    _=Depends(get_current_user),
) -> StandardResponse:
    """Return recent audit log entries from the Lobster Trap proxy."""
    entries = await get_recent_logs(limit=limit)
    return StandardResponse(
        data={"entries": entries, "total": len(entries)},
        message=f"Retrieved {len(entries)} Lobster Trap audit entries",
    )
