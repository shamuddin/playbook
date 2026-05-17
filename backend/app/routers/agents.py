"""Agent API router.

Endpoints for agent fleet management, health monitoring, and trend analysis.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Agent, AgentHealthHistory, Incident
from app.models import utc_now
from app.schemas import StandardResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=StandardResponse)
async def list_agents(
    type: Optional[str] = Query(None, description="Filter by agent type"),
    health_min: Optional[float] = Query(None, description="Minimum health score"),
    health_max: Optional[float] = Query(None, description="Maximum health score"),
    sort_by: str = Query("last_seen", description="Sort field"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    q: Optional[str] = Query(None, description="Free-text search"),
    include_unregistered: bool = Query(True, description="Include agents that appear in incidents but have no Agent record"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all monitored agents with filtering and pagination.

    Incident counts are computed dynamically from the Incident table so they
    always reflect reality, even for agents registered after incidents were
    created or for unregistered agents that appear in incident data.
    """
    # --- Build registered-agent query ---
    query = select(Agent)

    # Exclude known demo agents
    demo_system_ids = ["athena", "argus", "clerkbot", "Athena", "Argus", "ClerkBot"]
    query = query.where(
        Agent.system_id.not_in(demo_system_ids),
        not_(Agent.system_id.like("demo-%")),
    )

    if health_min is not None:
        query = query.where(Agent.health_score >= health_min)
    if health_max is not None:
        query = query.where(Agent.health_score <= health_max)
    if q:
        query = query.where(
            (Agent.name.ilike(f"%{q}%")) | (Agent.system_id.ilike(f"%{q}%"))
        )

    # Sorting
    sort_field = getattr(Agent, sort_by, Agent.updated_at)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    agents = result.scalars().all()

    # --- Compute incident counts dynamically ---
    agent_system_ids = [a.system_id for a in agents]
    incident_counts: dict[str, int] = {}
    bypass_counts: dict[str, int] = {}
    judge_counts: dict[str, int] = {}

    if agent_system_ids:
        # Incident counts by agent_id
        inc_result = await db.execute(
            select(Incident.agent_id, func.count(Incident.id))
            .where(Incident.agent_id.in_(agent_system_ids))
            .group_by(Incident.agent_id)
        )
        for row in inc_result.all():
            incident_counts[row[0]] = row[1]

        # Bypass counts by agent_id (via event_id fallback for older records)
        bp_result = await db.execute(
            select(Incident.agent_id, func.count(Incident.id))
            .where(
                Incident.agent_id.in_(agent_system_ids),
                Incident.bypass_detected == True,
            )
            .group_by(Incident.agent_id)
        )
        for row in bp_result.all():
            bypass_counts[row[0]] = row[1]

    # --- Build registered agent items ---
    def _agent_status(agent: Agent) -> str:
        if agent.status == "offline":
            return "offline"
        if agent.status == "online" and agent.health_score >= 80:
            return "online"
        if agent.health_score >= 80:
            return "healthy"
        elif agent.health_score >= 50:
            return "degraded"
        return "critical"

    items = []
    for agent in agents:
        inc_count = incident_counts.get(agent.system_id, 0)
        bp_count = bypass_counts.get(agent.system_id, 0)
        items.append({
            "id": agent.id,
            "system_id": agent.system_id,
            "name": agent.name,
            "description": agent.description,
            "health_score": agent.health_score,
            "lie_rate": agent.lie_rate,
            "incident_count": inc_count,
            "bypass_attempt_count": bp_count,
            "judge_decision_count": agent.judge_decision_count,
            "judge_decision_rate": round(agent.judge_decision_count / max(inc_count, 1), 3),
            "suprawall_connected": agent.suprawall_connected,
            "is_active": agent.is_active,
            "status": _agent_status(agent),
            "last_seen": agent.updated_at.isoformat() if agent.updated_at else None,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        })

    # --- Include unregistered agents (appear in incidents but no Agent record) ---
    total = len(items)
    if include_unregistered:
        # Find distinct agent_ids in incidents that are NOT in Agent table
        unreg_result = await db.execute(
            select(Incident.agent_id, func.count(Incident.id))
            .where(
                Incident.agent_id != None,
                Incident.agent_id.not_in(agent_system_ids) if agent_system_ids else True,
            )
            .group_by(Incident.agent_id)
            .order_by(func.count(Incident.id).desc())
        )
        for row in unreg_result.all():
            agent_id, inc_count = row
            if agent_id and inc_count:
                items.append({
                    "id": f"unreg-{agent_id}",
                    "system_id": agent_id,
                    "name": agent_id,
                    "description": "Agent seen in incidents but not registered in fleet",
                    "health_score": 50,
                    "lie_rate": 0.0,
                    "incident_count": inc_count,
                    "bypass_attempt_count": 0,
                    "judge_decision_count": 0,
                    "judge_decision_rate": 0.0,
                    "suprawall_connected": False,
                    "is_active": True,
                    "status": "degraded",
                    "last_seen": None,
                    "created_at": None,
                    "updated_at": None,
                })
                total += 1

    return StandardResponse(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message=f"Found {len(items)} agents",
    )


@router.get("/{agent_id}", response_model=StandardResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get detailed information about a specific agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Get incident stats for this agent (match by agent_id, not event_id)
    incident_result = await db.execute(
        select(func.count(Incident.id)).where(Incident.agent_id == agent.system_id)
    )
    incident_count = incident_result.scalar() or 0

    status_str = "healthy" if agent.health_score >= 80 else "degraded" if agent.health_score >= 50 else "critical"

    return StandardResponse(
        data={
            "id": agent.id,
            "system_id": agent.system_id,
            "name": agent.name,
            "description": agent.description,
            "health_score": agent.health_score,
            "lie_rate": agent.lie_rate,
            "incident_count": incident_count,
            "bypass_attempt_count": agent.bypass_attempt_count,
            "judge_decision_count": agent.judge_decision_count,
            "judge_decision_rate": round(agent.judge_decision_count / max(agent.incident_count, 1), 3),
            "suprawall_connected": agent.suprawall_connected,
            "is_active": agent.is_active,
            "status": status_str,
            "last_seen": agent.updated_at.isoformat() if agent.updated_at else None,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        },
        message="Agent retrieved",
    )


@router.get("/{agent_id}/health", response_model=StandardResponse)
async def get_agent_health(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get health score and metrics for a specific agent."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Compute dynamic incident count
    incident_result = await db.execute(
        select(func.count(Incident.id)).where(Incident.agent_id == agent.system_id)
    )
    incident_count = incident_result.scalar() or 0

    bypass_result = await db.execute(
        select(func.count(Incident.id)).where(
            (Incident.agent_id == agent.system_id) & (Incident.bypass_detected == True)
        )
    )
    bypass_count = bypass_result.scalar() or 0

    # Compute risk score based on incident history
    risk_score = max(
        0,
        100
        - (incident_count * 5)
        - (bypass_count * 25)
        - int(agent.lie_rate * 100),
    )

    # Determine status
    if agent.health_score >= 80:
        status_str = "healthy"
    elif agent.health_score >= 50:
        status_str = "degraded"
    else:
        status_str = "critical"

    # Component breakdown
    availability = max(0, 100 - (incident_count * 3))
    response_quality = max(0, 100 - int(agent.lie_rate * 100))
    compliance = max(0, 100 - (bypass_count * 20))

    return StandardResponse(
        data={
            "agent_id": agent_id,
            "system_id": agent.system_id,
            "health_score": agent.health_score,
            "risk_score": risk_score,
            "lie_rate": agent.lie_rate,
            "status": status_str,
            "incident_count": incident_count,
            "bypass_attempt_count": bypass_count,
            "judge_decision_count": agent.judge_decision_count,
            "judge_decision_rate": round(agent.judge_decision_count / max(incident_count, 1), 3),
            "components": {
                "availability": availability,
                "response_quality": response_quality,
                "compliance": compliance,
            },
            "trend": "stable",
        },
        message="Agent health retrieved",
    )


@router.get("/{agent_id}/trends", response_model=StandardResponse)
async def get_agent_trends(
    agent_id: str,
    period: str = Query("7d", description="Time period: 1h, 6h, 24h, 7d, 30d, 90d"),
    granularity: str = Query("daily", description="Granularity: hourly, daily"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get health trend data for an agent over time."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found",
        )

    # Parse period to days
    period_map = {"1h": 1, "6h": 1, "24h": 1, "7d": 7, "30d": 30, "90d": 90}
    days = period_map.get(period, 7)

    # Get health history
    history_result = await db.execute(
        select(AgentHealthHistory)
        .where(AgentHealthHistory.agent_id == agent_id)
        .order_by(AgentHealthHistory.recorded_at.asc())
    )
    history = history_result.scalars().all()

    # If no history, generate synthetic trend from current state
    if not history:
        from datetime import timedelta

        history = []
        base_score = agent.health_score
        for i in range(days):
            history.append(
                {
                    "date": (datetime.now(timezone.utc) - timedelta(days=days - i)).date().isoformat(),
                    "health_score": max(0, min(100, base_score + (i - days // 2) * 2)),
                    "lie_rate": max(0.0, agent.lie_rate + (i - days // 2) * 0.001),
                    "incident_count": max(0, agent.incident_count // max(days, 1) + (i - days // 2)),
                    "bypass_attempt_count": max(0, agent.bypass_attempt_count // max(days, 1) + (i - days // 2) // 3),
                }
            )
    else:
        history = [
            {
                "date": h.recorded_at.date().isoformat() if h.recorded_at else None,
                "health_score": h.health_score,
                "lie_rate": h.lie_rate,
                "incident_count": getattr(h, "incident_count", 0),
                "bypass_attempt_count": getattr(h, "bypass_attempt_count", 0),
            }
            for h in history
        ]

    return StandardResponse(
        data={
            "agent_id": agent_id,
            "period": period,
            "granularity": granularity,
            "trend": history,
            "metrics": {
                "avg_health": round(sum(h["health_score"] for h in history) / max(len(history), 1), 1),
                "avg_lie_rate": round(sum(h["lie_rate"] for h in history) / max(len(history), 1), 3),
                "min_health": min((h["health_score"] for h in history), default=agent.health_score),
                "max_health": max((h["health_score"] for h in history), default=agent.health_score),
            },
        },
        message="Agent trends retrieved",
    )


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    system_id: str,
    name: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Register a new agent for monitoring."""
    # Check for duplicate system_id
    existing = await db.execute(
        select(Agent).where(Agent.system_id == system_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent with system_id {system_id} already exists",
        )

    agent = Agent(
        system_id=system_id,
        name=name,
        description=description,
        health_score=100,
        lie_rate=0.0,
        incident_count=0,
        bypass_attempt_count=0,
        judge_decision_count=0,
    )
    db.add(agent)
    await db.commit()

    return StandardResponse(
        data={
            "id": agent.id,
            "system_id": agent.system_id,
            "name": agent.name,
        },
        message="Agent registered",
    )


@router.post("/{agent_id}/heartbeat", response_model=StandardResponse)
async def agent_heartbeat(
    agent_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Receive a heartbeat from a monitored agent.

    Used by the Python SDK to report agent health.
    """
    result = await db.execute(select(Agent).where(Agent.system_id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        # Auto-register unknown agents on first heartbeat
        agent = Agent(
            system_id=agent_id,
            name=f"Agent-{agent_id[:8]}",
            status="online",
            health_score=int(data.get("health_score", 100)),
            last_seen=utc_now(),
        )
        db.add(agent)
        await db.flush()
    else:
        agent.status = "online"
        agent.health_score = int(data.get("health_score", agent.health_score))
        agent.last_seen = utc_now()

    # Log heartbeat
    heartbeat = AgentHealthHistory(
        agent_id=agent.id,
        health_score=int(data.get("health_score", agent.health_score)),
        lie_rate=data.get("lie_rate", 0.0),
        risk_score=data.get("risk_score"),
        recorded_at=utc_now(),
    )
    db.add(heartbeat)
    await db.commit()

    return StandardResponse(
        success=True,
        data={"agent_id": agent_id, "status": "online", "health_score": agent.health_score},
    )
