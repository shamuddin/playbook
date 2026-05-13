"""Incident API router.

Endpoints for incident CRUD, classification, response triggering, and timeline.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import get_db
from app.models import Incident, IncidentMetadata, TimelineEvent
from app.schemas import (
    EventIngestRequest,
    IncidentCreate,
    IncidentFilter,
    IncidentListResponse,
    IncidentResponse,
    StandardResponse,
    TimelineEventResponse,
)
from app.models import EvidencePackage
from app.services.detect import DetectionEngine, IncidentFactory, normalize_event
from app.services.forensics import ForensicsService
from app.services.response_engine import ResponseEngine
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/incidents", tags=["incidents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_incident_or_404(
    db: AsyncSession, incident_id: str
) -> Incident:
    """Fetch an incident by its public incident_id, raising 404 if not found."""
    result = await db.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )
    return incident


def _incident_to_response(incident: Incident) -> IncidentResponse:
    """Convert an Incident model to an IncidentResponse schema."""
    return IncidentResponse(
        id=incident.id,
        incident_id=incident.incident_id,
        event_id=incident.event_id,
        status=incident.status,
        severity=incident.severity,
        category=incident.category,
        incident_type=incident.incident_type,
        confidence=incident.confidence,
        playbook_id=incident.playbook_id,
        response_status=incident.response_status,
        forensics_status=incident.forensics_status,
        judge_verdict=None,
        bypass_detected=incident.bypass_detected,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Create a new incident manually (bypassing the detection engine).

    Use /ingest to auto-detect from a raw event.
    """
    incident = Incident(
        incident_id=IncidentFactory._generate_incident_id(),
        event_id=data.event_id,
        status="detected",
        severity=data.severity,
        category=data.category,
        incident_type=data.incident_type,
        confidence=data.confidence,
        deterministic_classification=True,
        response_status="pending",
        forensics_status="pending",
    )
    db.add(incident)
    await db.flush()

    # Add metadata if provided
    if data.metadata:
        meta = IncidentMetadata(
            incident_id=incident.id,
            full_metadata_json=data.metadata,
        )
        db.add(meta)

    # Add detection timeline event
    timeline = TimelineEvent(
        incident_id=incident.id,
        stage="detect",
        event_type="manual_creation",
        event_description=f"Manually created incident with severity {data.severity}",
        source_component="api",
    )
    db.add(timeline)
    await db.commit()

    return _incident_to_response(incident)


@router.post(
    "/ingest",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_event(
    request: EventIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Ingest a raw agent event, run detection, and create an incident.

    This is the primary entry point for the DETECT pipeline.
    """
    # Normalize the event
    try:
        event = normalize_event(request.event_data, source_hint=request.source)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Event normalization failed: {exc}",
        )

    # Run detection engine
    engine = DetectionEngine()
    detection = engine.evaluate(event)

    # If no match, still create a low-confidence incident (coverage gap)
    if detection.incident_type is None:
        detection.incident_type = "AGT-GAP-012"
        detection.incident_type_name = "Coverage Gap"
        detection.severity = "low"
        detection.confidence = 0.1
        detection.anomaly_score = 10.0
        detection.category = "coverage"

    # Create incident
    incident = await IncidentFactory.create_incident(db, event, detection)
    await db.commit()

    # Broadcast to WebSocket clients
    await ws_manager.broadcast({
        "event_type": "incident_detected",
        "incident_id": incident.incident_id,
        "severity": incident.severity,
        "category": incident.category,
        "incident_type": incident.incident_type,
        "confidence": incident.confidence,
        "timestamp": incident.created_at.isoformat(),
    })

    return _incident_to_response(incident)


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Free-text search"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> IncidentListResponse:
    """List incidents with filtering and pagination."""
    query = select(Incident)

    if status:
        query = query.where(Incident.status == status)
    if severity:
        query = query.where(Incident.severity == severity)
    if category:
        query = query.where(Incident.category == category)
    if q:
        query = query.where(
            (Incident.incident_id.ilike(f"%{q}%"))
            | (Incident.incident_type.ilike(f"%{q}%"))
            | (Incident.event_id.ilike(f"%{q}%"))
        )

    # Get total count
    count_query = select(Incident.id).select_from(Incident)
    if status:
        count_query = count_query.where(Incident.status == status)
    if severity:
        count_query = count_query.where(Incident.severity == severity)
    if category:
        count_query = count_query.where(Incident.category == category)
    if q:
        count_query = count_query.where(
            (Incident.incident_id.ilike(f"%{q}%"))
            | (Incident.incident_type.ilike(f"%{q}%"))
            | (Incident.event_id.ilike(f"%{q}%"))
        )
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.order_by(Incident.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    incidents = result.scalars().all()

    return IncidentListResponse(
        data=[_incident_to_response(inc) for inc in incidents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Get a single incident by its public incident_id."""
    incident = await _get_incident_or_404(db, incident_id)
    return _incident_to_response(incident)


@router.post("/{incident_id}/classify", response_model=IncidentResponse)
async def classify_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Re-classify an incident by re-running the detection engine on its stored event data.

    Updates severity, confidence, and category. Adds a timeline event.
    """
    incident = await _get_incident_or_404(db, incident_id)

    # Retrieve stored metadata to reconstruct the event
    meta_result = await db.execute(
        select(IncidentMetadata).where(IncidentMetadata.incident_id == incident.id)
    )
    metadata = meta_result.scalar_one_or_none()

    if metadata is None or not metadata.full_metadata_json:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incident has no stored metadata for re-classification",
        )

    stored = metadata.full_metadata_json
    event_data = stored.get("event_raw", {})
    event_source = stored.get("event", {}).get("source", "generic")

    # Re-normalize and detect
    try:
        event = normalize_event(event_data, source_hint=event_source)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Re-normalization failed: {exc}",
        )

    engine = DetectionEngine()
    detection = engine.evaluate(event)

    if detection.incident_type is None:
        detection.incident_type = "AGT-GAP-012"
        detection.severity = "low"
        detection.confidence = 0.1
        detection.category = "coverage"

    # Update incident
    incident.severity = detection.severity
    incident.confidence = detection.confidence
    incident.category = detection.category
    incident.incident_type = detection.incident_type or "AGT-GAP-012"
    incident.local_rule_id = detection.matched_rules[0] if detection.matched_rules else None
    incident.status = "classified"

    # Add classification timeline event
    await IncidentFactory.add_classification_timeline_event(
        db, incident, detection, classified_by="api"
    )
    await db.commit()

    # Broadcast classification complete
    await ws_manager.broadcast({
        "event_type": "INCIDENT_CLASSIFIED",
        "incident_id": incident.incident_id,
        "severity": incident.severity,
        "category": incident.category,
        "incident_type": incident.incident_type,
        "confidence": incident.confidence,
        "timestamp": incident.updated_at.isoformat() if incident.updated_at else None,
    })

    return _incident_to_response(incident)


@router.post("/{incident_id}/respond", response_model=StandardResponse)
async def respond_to_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Trigger playbook response for an incident.

    Executes the full playbook via the Response Engine.
    """
    incident = await _get_incident_or_404(db, incident_id)

    if incident.response_status == "completed":
        return StandardResponse(
            message="Response already completed",
            data={"incident_id": incident_id, "status": "completed"},
        )

    # Execute playbook via response engine
    engine = ResponseEngine()
    result = await engine.execute_playbook(db, incident_id)

    # Broadcast completion
    await ws_manager.broadcast({
        "event_type": "incident_responded",
        "incident_id": incident_id,
        "response_id": result.response_id,
        "status": result.status,
        "steps_completed": result.steps_completed,
        "steps_failed": result.steps_failed,
    })

    status_str = result.status.value if hasattr(result.status, "value") else str(result.status)
    return StandardResponse(
        message=f"Playbook execution {status_str}",
        data={
            "incident_id": incident_id,
            "response_id": result.response_id,
            "status": status_str,
            "steps_total": result.steps_total,
            "steps_completed": result.steps_completed,
            "steps_failed": result.steps_failed,
            "total_latency_ms": result.total_latency_ms,
        },
    )


@router.put("/{incident_id}/status", response_model=IncidentResponse)
async def update_incident_status(
    incident_id: str,
    status: str,
    db: AsyncSession = Depends(get_db),
) -> IncidentResponse:
    """Update the status of an incident (human review action)."""
    incident = await _get_incident_or_404(db, incident_id)

    valid_statuses = {"new", "detected", "classified", "responding", "resolved", "escalated"}
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: {status}. Must be one of {valid_statuses}",
        )

    incident.status = status
    await db.commit()

    # Broadcast status update via WebSocket
    await ws_manager.broadcast({
        "event_type": "incident_status_updated",
        "incident_id": incident_id,
        "status": status,
        "timestamp": incident.updated_at.isoformat() if incident.updated_at else None,
    })

    return _incident_to_response(incident)


@router.get("/{incident_id}/timeline", response_model=list[TimelineEventResponse])
async def get_timeline(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TimelineEventResponse]:
    """Get the timeline of events for an incident."""
    incident = await _get_incident_or_404(db, incident_id)

    result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.incident_id == incident.id)
        .order_by(TimelineEvent.timestamp.asc())
    )
    events = result.scalars().all()

    return [
        TimelineEventResponse(
            id=evt.id,
            timestamp=evt.timestamp,
            stage=evt.stage,
            event_type=evt.event_type,
            event_description=evt.event_description,
            source_component=evt.source_component,
            details_json=evt.details_json,
        )
        for evt in events
    ]


@router.get("/{incident_id}/forensics", response_model=StandardResponse)
async def get_incident_forensics(
    incident_id: str,
    format: str = Query("json", description="Output format: json, stix, verify"),
    include_raw_logs: bool = Query(False, description="Include raw system log dumps"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get forensic evidence package for an incident (API spec endpoint).

    This is the canonical endpoint per API documentation.
    """
    incident = await _get_incident_or_404(db, incident_id)

    ev_result = await db.execute(
        select(EvidencePackage).where(EvidencePackage.incident_id == incident.id)
    )
    evidence = ev_result.scalar_one_or_none()

    if evidence is None:
        service = ForensicsService()
        evidence = await service.build_package(db, incident_id)
        await db.commit()

    service = ForensicsService()

    if format.lower() == "stix":
        data = service.export_stix(evidence)
        message = "Evidence package exported as STIX 2.1"
    elif format.lower() == "verify":
        data = service.verify_package(evidence)
        message = "Evidence package integrity verification complete"
    else:
        data = {
            "package_id": evidence.package_id,
            "incident_id": incident_id,
            "package_type": evidence.package_type,
            "integrity_hash": evidence.integrity_hash,
            "is_verified": evidence.is_verified,
            "generated_at": evidence.created_at.isoformat() if evidence.created_at else None,
            "retention_until": evidence.retention_until.isoformat() if evidence.retention_until else None,
            "artifacts": list(evidence.package_data.get("artifacts", {}).keys()),
            "manifest": evidence.package_data.get("manifest", {}),
            "signature": evidence.package_data.get("signature", {}),
        }
        if include_raw_logs:
            data["raw_logs"] = evidence.package_data.get("artifacts", {}).get("audit", [])
        message = "Evidence package retrieved"

    return StandardResponse(data=data, message=message)
