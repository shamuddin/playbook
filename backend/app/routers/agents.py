"""Agent API router.

Endpoints for agent fleet management, health monitoring, and trend analysis.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Agent, AgentHealthHistory, Incident
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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all monitored agents with filtering and pagination."""
    query = select(Agent)

    if type:
        # Agent model doesn't have a type column; filter by name pattern for now
        pass
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

    # Count total
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    agents = result.scalars().all()

    def _agent_status(agent: Agent) -> str:
        if agent.health_score >= 80:
            return "healthy"
        elif agent.health_score >= 50:
            return "degraded"
        return "critical"

    def _agent_dict(agent: Agent) -> dict:
        return {
            "id": agent.id,
            "system_id": agent.system_id,
            "name": agent.name,
            "description": agent.description,
            "health_score": agent.health_score,
            "lie_rate": agent.lie_rate,
            "incident_count": agent.incident_count,
            "bypass_attempt_count": agent.bypass_attempt_count,
            "judge_decision_count": agent.judge_decision_count,
            "judge_decision_rate": round(agent.judge_decision_count / max(agent.incident_count, 1), 3),
            "suprawall_connected": agent.suprawall_connected,
            "is_active": agent.is_active,
            "status": _agent_status(agent),
            "last_seen": agent.updated_at.isoformat() if agent.updated_at else None,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
        }

    return StandardResponse(
        data={
            "items": [_agent_dict(agent) for agent in agents],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message=f"Found {len(agents)} agents",
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

    # Get incident stats for this agent
    incident_result = await db.execute(
        select(func.count(Incident.id)).where(Incident.event_id == agent.system_id)
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

    # Compute risk score based on incident history
    risk_score = max(
        0,
        100
        - (agent.incident_count * 5)
        - (agent.bypass_attempt_count * 25)
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
    availability = max(0, 100 - (agent.incident_count * 3))
    response_quality = max(0, 100 - int(agent.lie_rate * 100))
    compliance = max(0, 100 - (agent.bypass_attempt_count * 20))

    return StandardResponse(
        data={
            "agent_id": agent_id,
            "system_id": agent.system_id,
            "health_score": agent.health_score,
            "risk_score": risk_score,
            "lie_rate": agent.lie_rate,
            "status": status_str,
            "incident_count": agent.incident_count,
            "bypass_attempt_count": agent.bypass_attempt_count,
            "judge_decision_count": agent.judge_decision_count,
            "judge_decision_rate": round(agent.judge_decision_count / max(agent.incident_count, 1), 3),
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
