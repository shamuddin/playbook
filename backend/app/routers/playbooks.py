"""Playbook API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Playbook, PlaybookAction
from app.schemas import PlaybookActionSchema, PlaybookResponse, StandardResponse
from app.services.response_engine import ResponseEngine

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("", response_model=StandardResponse)
async def list_playbooks(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all available playbooks with action summaries."""
    result = await db.execute(
        select(Playbook).where(Playbook.is_active == True)
    )
    playbooks = result.scalars().all()

    data = []
    for pb in playbooks:
        # Count actions
        action_count_result = await db.execute(
            select(PlaybookAction).where(PlaybookAction.playbook_id == pb.id)
        )
        actions = action_count_result.scalars().all()

        data.append({
            "id": pb.id,
            "playbook_id": pb.playbook_id,
            "name": pb.name,
            "incident_type": pb.incident_type,
            "version": pb.version,
            "auto_execute": pb.auto_execute,
            "action_count": len(actions),
            "description": pb.description,
        })

    return StandardResponse(
        data=data,
        message=f"Found {len(data)} active playbooks",
    )


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: str,
    db: AsyncSession = Depends(get_db),
) -> PlaybookResponse:
    """Get a single playbook definition with all actions."""
    result = await db.execute(
        select(Playbook).where(
            Playbook.playbook_id == playbook_id,
            Playbook.is_active == True,
        )
    )
    playbook = result.scalar_one_or_none()

    if playbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found",
        )

    # Get actions
    actions_result = await db.execute(
        select(PlaybookAction)
        .where(PlaybookAction.playbook_id == playbook.id)
        .order_by(PlaybookAction.step_order)
    )
    actions = actions_result.scalars().all()

    return PlaybookResponse(
        id=playbook.id,
        playbook_id=playbook.playbook_id,
        name=playbook.name,
        version=playbook.version,
        incident_type=playbook.incident_type,
        description=playbook.description,
        auto_execute=playbook.auto_execute,
        is_active=playbook.is_active,
        actions=[
            PlaybookActionSchema(
                step_order=a.step_order,
                name=a.name,
                action_type=a.action_type,
                target=a.target,
                parameters=a.parameters or {},
                timeout_seconds=a.timeout_seconds,
            )
            for a in actions
        ],
    )


@router.post("/{playbook_id}/execute", response_model=StandardResponse)
async def execute_playbook(
    playbook_id: str,
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Trigger playbook execution for an incident.

    The playbook is resolved by incident_type, not by playbook_id parameter.
    The playbook_id parameter is validated for existence.
    """
    # Validate playbook exists
    result = await db.execute(
        select(Playbook).where(Playbook.playbook_id == playbook_id)
    )
    playbook = result.scalar_one_or_none()

    if playbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook {playbook_id} not found",
        )

    # Execute via response engine (pass playbook_id to ensure correct playbook runs)
    engine = ResponseEngine()
    execution_result = await engine.execute_playbook(db, incident_id, playbook_id=playbook_id)

    return StandardResponse(
        message=f"Playbook execution {execution_result.status}",
        data={
            "response_id": execution_result.response_id,
            "status": execution_result.status,
            "steps_total": execution_result.steps_total,
            "steps_completed": execution_result.steps_completed,
            "steps_failed": execution_result.steps_failed,
            "total_latency_ms": execution_result.total_latency_ms,
            "action_results": [
                {
                    "step_name": ar.step_name,
                    "action_type": ar.action_type,
                    "status": ar.status,
                    "latency_ms": ar.latency_ms,
                }
                for ar in execution_result.action_results
            ],
        },
    )
