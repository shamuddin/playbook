"""Demo endpoints for loading scenarios and triggering events."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import INCIDENT_TYPES
from app.database import get_db
from app.models import (
    Agent,
    AuditLog,
    BypassAttempt,
    DetectionRule,
    EvidencePackage,
    HumanReviewTask,
    Incident,
    IncidentMetadata,
    JudgeDecision,
    NistBaseline,
    Playbook,
    PlaybookAction,
    ResponseRecord,
    ResponseStep,
    TimelineEvent,
)
from app.schemas import DemoSeedRequest, DemoSeedResponse, StandardResponse
from app.seed import seed_all

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
    """Seed demo data including reference tables and sample incidents.

    Only available in DEMO_MODE.
    """
    require_demo_mode()

    # Seed reference data (rules, playbooks, baselines)
    seeded = await seed_all(db)

    # Create sample agents
    agents = []
    for i in range(3):
        agent = Agent(
            system_id=f"demo-agent-{i+1}",
            name=f"Demo Agent {i+1}",
            description=f"Sample agent for demo purposes",
            health_score=100 - (i * 20),
        )
        db.add(agent)
        agents.append(agent)
    await db.flush()

    # Load rules from DB for incident creation
    from app.services.detect.engine import DetectionEngine

    engine = DetectionEngine()
    rules_loaded = await engine.load_rules_from_db(db)
    if rules_loaded == 0:
        # Fall back to static rules if DB is empty
        pass

    # Create a sample incident for each severity level
    from app.services.detect.incident_factory import IncidentFactory
    from app.services.detect.normalizer import PB_CES_Event

    demo_events = [
        ("AGT-DEL-001", "DROP TABLE customers", "critical"),
        ("AGT-INJ-006", "Ignore previous instructions", "high"),
        ("AGT-CRE-008", "password: secret123", "critical"),
        ("AGT-RAT-009", "rate limit exceeded", "medium"),
        ("AGT-HAL-007", "conflicting information detected", "medium"),
    ]

    incidents_created = 0
    for inc_type, tool_call, _ in demo_events:
        event = PB_CES_Event(
            event_id=f"demo-evt-{inc_type}",
            source="demo",
            event_type="demo_trigger",
            tool_call=tool_call,
        )
        detection = engine.evaluate(event)
        if detection.incident_type is None:
            detection.incident_type = inc_type
            detection.severity = "medium"
            detection.confidence = 0.5
            detection.category = "demo"
        await IncidentFactory.create_incident(db, event, detection)
        incidents_created += 1

    await db.commit()

    total_seeded = sum(seeded.values())
    return DemoSeedResponse(
        scenarios_seeded=total_seeded,
        incidents_created=incidents_created,
    )


@router.post("/reset")
async def reset_demo_data(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Reset all demo data (incidents, metadata, timeline, agents).

    Only available in DEMO_MODE. Preserves reference data (rules, playbooks, baselines).
    """
    require_demo_mode()

    # Delete in dependency order to avoid FK violations
    tables_in_order = [
        HumanReviewTask,
        ResponseStep,
        ResponseRecord,
        EvidencePackage,
        TimelineEvent,
        IncidentMetadata,
        AuditLog,
        BypassAttempt,
        JudgeDecision,
        Incident,
        Agent,
    ]

    deleted_counts = {}
    for table in tables_in_order:
        result = await db.execute(delete(table))
        deleted_counts[table.__tablename__] = result.rowcount

    await db.commit()

    total_deleted = sum(deleted_counts.values())
    return StandardResponse(
        message=f"Demo data reset. Removed {total_deleted} records from {len(deleted_counts)} tables.",
        data=deleted_counts,
    )


@router.post("/trigger")
async def trigger_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Trigger a specific demo scenario by incident type code.

    Only available in DEMO_MODE.
    """
    require_demo_mode()

    # Validate scenario_id is a known incident type
    if scenario_id not in INCIDENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scenario: {scenario_id}. Must be one of {list(INCIDENT_TYPES.keys())}",
        )

    from app.services.detect.engine import DetectionEngine
    from app.services.detect.incident_factory import IncidentFactory
    from app.services.detect.normalizer import PB_CES_Event

    # Load engine with DB rules if available
    engine = DetectionEngine()
    await engine.load_rules_from_db(db)

    # Find a matching rule to get a sample pattern
    sample_tool_call = f"demo scenario {scenario_id}"
    for rule in engine._rules:
        if rule["incident_type"] == scenario_id and rule.get("patterns"):
            sample_tool_call = rule["patterns"][0].replace(r"\s+", " ").replace(r"\s*", " ")
            break

    event = PB_CES_Event(
        event_id=f"demo-trigger-{scenario_id}",
        source="demo",
        event_type="scenario_trigger",
        tool_call=sample_tool_call,
    )
    detection = engine.evaluate(event)

    # Ensure detection has values
    if detection.incident_type is None:
        detection.incident_type = scenario_id
        detection.incident_type_name = INCIDENT_TYPES[scenario_id]
        detection.severity = "high"
        detection.confidence = 0.5
        detection.category = "demo"

    incident = await IncidentFactory.create_incident(db, event, detection)
    await db.commit()

    # Broadcast via WebSocket
    from app.services.websocket_manager import ws_manager

    await ws_manager.broadcast({
        "event_type": "demo_scenario_triggered",
        "incident_id": incident.incident_id,
        "scenario_id": scenario_id,
        "severity": incident.severity,
        "timestamp": incident.created_at.isoformat(),
    })

    return StandardResponse(
        message=f"Scenario {scenario_id} triggered: {INCIDENT_TYPES[scenario_id]}",
        data={
            "scenario_id": scenario_id,
            "incident_id": incident.incident_id,
            "severity": incident.severity,
        },
    )
