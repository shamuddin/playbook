"""Integrations API router — SupraWall webhook and third-party connectors."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Incident, SuprawallEvent
from app.schemas import NotificationTestRequest, NotificationTestResponse, StandardResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/suprawall/events", response_model=StandardResponse)
async def receive_suprawall_event(
    event: dict,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Receive SupraWall webhook events.

    SupraWall sends guardrail events (blocked requests, schema violations,
    input/output filtering decisions) for correlation with PLAYBOOK incidents.
    """
    # Extract SupraWall event fields
    session_id = event.get("session_id") or event.get("client_id")
    decision = event.get("decision", "BLOCKED")
    risk_score = event.get("risk_score")
    latency_ms = event.get("latency_ms")
    framework = event.get("framework", "suprawall")
    matched_rules = event.get("matched_rules", [])

    # Store the raw event
    sw_event = SuprawallEvent(
        event_id=event.get("event_id", f"SW-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"),
        external_event_id=event.get("external_event_id"),
        decision=decision,
        session_id=session_id,
        client_ip=event.get("client_ip"),
        prompt_hash=event.get("prompt_hash"),
        matched_rules=matched_rules,
        risk_score=risk_score,
        latency_ms=latency_ms,
        framework=framework,
        raw_data=event,
    )
    db.add(sw_event)
    await db.flush()
    await db.commit()

    # Attempt correlation with existing incidents by session_id
    correlated_incident = None
    if session_id:
        result = await db.execute(
            select(Incident).where(Incident.event_id == session_id)
        )
        correlated_incident = result.scalar_one_or_none()

    return StandardResponse(
        data={
            "event_id": sw_event.event_id,
            "session_id": session_id,
            "correlated_incident_id": (
                correlated_incident.incident_id if correlated_incident else None
            ),
            "status": "stored",
        },
        message="SupraWall event received and stored",
    )


@router.get("/suprawall/events", response_model=StandardResponse)
async def list_suprawall_events(
    session_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List received SupraWall events with optional filtering."""
    query = select(SuprawallEvent).order_by(SuprawallEvent.created_at.desc()).limit(limit)

    if session_id:
        query = query.where(SuprawallEvent.session_id == session_id)
    if event_type:
        query = query.where(SuprawallEvent.event_type == event_type)

    result = await db.execute(query)
    events = result.scalars().all()

    data = [
        {
            "event_id": e.event_id,
            "external_event_id": e.external_event_id,
            "session_id": e.session_id,
            "decision": e.decision,
            "framework": e.framework,
            "risk_score": e.risk_score,
            "latency_ms": e.latency_ms,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]

    return StandardResponse(
        data={"events": data, "total": len(data)},
        message=f"Found {len(data)} SupraWall events",
    )


@router.get("/suprawall/correlate/{incident_id}", response_model=StandardResponse)
async def correlate_suprawall_with_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Find SupraWall events correlated with a PLAYBOOK incident."""
    # Find incident
    result = await db.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    # Find SupraWall events by session_id correlation
    session_id = incident.event_id
    sw_events = []
    if session_id:
        sw_result = await db.execute(
            select(SuprawallEvent)
            .where(SuprawallEvent.session_id == session_id)
            .order_by(SuprawallEvent.created_at.desc())
        )
        sw_events = sw_result.scalars().all()

    return StandardResponse(
        data={
            "incident_id": incident_id,
            "session_id": session_id,
            "suprawall_events": [
                {
                    "event_id": e.event_id,
                    "external_event_id": e.external_event_id,
                    "decision": e.decision,
                    "framework": e.framework,
                    "risk_score": e.risk_score,
                    "latency_ms": e.latency_ms,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in sw_events
            ],
            "correlation_count": len(sw_events),
        },
        message=f"Found {len(sw_events)} correlated SupraWall events",
    )


@router.post("/notifications/test", response_model=StandardResponse)
async def test_notification(
    request: NotificationTestRequest,
) -> StandardResponse:
    """Send a test notification to a configured channel.

    Used to verify that Slack, Email, or PagerDuty integrations are working.
    """
    service = NotificationService()
    message = {
        "title": request.message,
        "body": f"Test notification sent via {request.channel}",
        "severity": request.severity or "high",
        "incident_id": request.incident_id or "TEST-001",
    }
    result = await service.send(request.channel, message)
    await service.close()

    return StandardResponse(
        success=result.success,
        data=NotificationTestResponse(
            channel=result.channel,
            success=result.success,
            detail=result.detail,
        ).model_dump(),
        message="Notification sent" if result.success else "Notification failed",
    )
