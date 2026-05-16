"""Agent Simulator Playground router.

Provides endpoints to create, configure, and run simulated agent swarms
against the PLAYBOOK Judge Layer with real-time event streaming.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PlaygroundAgent, PlaygroundEvent, PlaygroundSession, PlaygroundSessionStatus
from app.core.security import get_current_user
from app.schemas import StandardResponse
from app.services.playground.engine import PlaygroundEngine, get_engine, remove_engine, set_engine
from app.services.playground.llm_providers import get_available_providers, LLMProviderFactory
from app.services.playground.templates import get_template, list_templates

router = APIRouter(prefix="/playground", tags=["playground"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _validate_provider_config(provider_name: str, config: dict) -> tuple[bool, str]:
    provider = LLMProviderFactory.create(provider_name, config)
    try:
        if provider_name in ("ollama", "ollama_cloud"):
            models = await provider.list_models()
            return (len(models) > 0, "No models found")
        else:
            resp = await provider.chat_completion(
                system_prompt="You are a test bot.",
                messages=[{"role": "user", "content": "Say PONG"}],
                json_mode=False,
            )
            if resp.error:
                return (False, resp.error)
            return (True, "")
    except Exception as exc:
        return (False, str(exc))


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

@router.get("/providers", response_model=StandardResponse)
async def list_providers() -> StandardResponse:
    """List all supported LLM providers with configuration metadata."""
    return StandardResponse(
        data={"providers": get_available_providers()},
        message="Available LLM providers retrieved",
    )


@router.post("/providers/validate", response_model=StandardResponse)
async def validate_provider_config(payload: dict) -> StandardResponse:
    """Test a provider configuration.

    For Ollama providers, validates by listing models (no chat needed).
    For other providers, sends a simple ping prompt.
    """
    provider_name = payload.get("provider_name", "openai")
    config = payload.get("config", {})

    try:
        provider = LLMProviderFactory.create(provider_name, config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # For Ollama (local + cloud), try list_models first — it's faster and
    # doesn't require knowing a valid model name upfront.
    if provider_name in ("ollama", "ollama_cloud"):
        models = await provider.list_models()
        if models:
            return StandardResponse(
                data={
                    "provider": provider_name,
                    "models_found": len(models),
                    "first_model": models[0]["id"],
                    "latency_ms": 0.0,
                },
                message="Provider configuration is valid",
            )
        # If list_models returned empty, fall through to chat ping as a last resort

    resp = await provider.chat_completion(
        system_prompt="You are a helpful assistant. Reply with exactly: PONG",
        messages=[{"role": "user", "content": "Ping"}],
        json_mode=False,
        temperature=0.0,
    )

    if resp.error:
        return StandardResponse(
            success=False,
            message=f"Provider validation failed: {resp.error}",
            data={"provider": provider_name, "error": resp.error},
        )

    return StandardResponse(
        data={
            "provider": provider_name,
            "model": resp.model,
            "response_preview": resp.content[:200],
            "latency_ms": round(resp.latency_ms, 2),
        },
        message="Provider configuration is valid",
    )


@router.post("/providers/models", response_model=StandardResponse)
async def list_provider_models(payload: dict) -> StandardResponse:
    """List available models for a given provider configuration."""
    provider_name = payload.get("provider_name", "openai")
    config = payload.get("config", {})

    try:
        provider = LLMProviderFactory.create(provider_name, config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    models = await provider.list_models()
    return StandardResponse(
        data={"provider": provider_name, "models": models},
        message=f"Retrieved {len(models)} models for {provider_name}",
    )


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@router.get("/templates", response_model=StandardResponse)
async def get_templates() -> StandardResponse:
    """List available industry templates."""
    return StandardResponse(
        data={"templates": list_templates()},
        message="Industry templates retrieved",
    )


@router.get("/templates/{template_id}", response_model=StandardResponse)
async def get_template_detail(template_id: str) -> StandardResponse:
    """Get full definition of an industry template."""
    tpl = get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
    return StandardResponse(data=tpl, message=f"Template {template_id} retrieved")


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@router.post("/sessions", response_model=StandardResponse)
async def create_session(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> StandardResponse:
    """Create a new playground session.

    Payload::

        {
            "name": "My Simulation",
            "description": "...",
            "provider_name": "openai",
            "provider_config": {"api_key": "sk-...", "model": "gpt-4o-mini"},
            "industry_template": "healthcare",
            "agents": [
                {
                    "name": "DiagBot",
                    "role": "clinical_diagnosis",
                    "risk_level": "critical",
                    "system_prompt": "...",
                    "situations": ["..."],
                    "actions": [
                        {"name": "suggest_diagnosis", "metadata": {...}, "is_malicious": false}
                    ]
                }
            ]
        }
    """
    provider_name = payload.get("provider_name", "openai")
    provider_config = payload.get("provider_config", {})
    is_valid, error = await _validate_provider_config(provider_name, provider_config)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Provider validation failed: {error}")

    session = PlaygroundSession(
        name=payload.get("name", "Untitled Session"),
        description=payload.get("description"),
        provider_name=payload.get("provider_name", "openai"),
        provider_config=payload.get("provider_config", {}),
        industry_template=payload.get("industry_template"),
        status=PlaygroundSessionStatus.PENDING,
    )
    db.add(session)
    await db.flush()

    # Add agents
    for agent_data in payload.get("agents", []):
        agent = PlaygroundAgent(
            session_id=session.id,
            name=agent_data["name"],
            role=agent_data["role"],
            risk_level=agent_data.get("risk_level", "medium"),
            system_prompt=agent_data["system_prompt"],
            actions=agent_data.get("actions", []),
            situations=agent_data.get("situations", []),
            is_active=agent_data.get("is_active", True),
        )
        db.add(agent)

    await db.commit()

    return StandardResponse(
        data={
            "session_id": session.id,
            "name": session.name,
            "status": session.status.value,
            "agent_count": len(payload.get("agents", [])),
        },
        message="Playground session created",
    )


@router.get("/sessions", response_model=StandardResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List playground sessions with pagination."""
    count_result = await db.execute(select(PlaygroundSession.id))
    total = len(count_result.scalars().all())

    result = await db.execute(
        select(PlaygroundSession)
        .order_by(PlaygroundSession.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    sessions = result.scalars().all()

    return StandardResponse(
        data={
            "items": [
                {
                    "id": s.id,
                    "name": s.name,
                    "status": s.status.value,
                    "provider_name": s.provider_name,
                    "industry_template": s.industry_template,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in sessions
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message=f"Found {total} playground sessions",
    )


@router.get("/sessions/{session_id}", response_model=StandardResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get session details including agents."""
    result = await db.execute(select(PlaygroundSession).where(PlaygroundSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    agent_result = await db.execute(
        select(PlaygroundAgent).where(PlaygroundAgent.session_id == session_id)
    )
    agents = agent_result.scalars().all()

    return StandardResponse(
        data={
            "id": session.id,
            "name": session.name,
            "description": session.description,
            "status": session.status.value,
            "provider_name": session.provider_name,
            "provider_config": session.provider_config,
            "industry_template": session.industry_template,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role,
                    "risk_level": a.risk_level,
                    "situations": a.situations,
                    "actions": a.actions,
                    "is_active": a.is_active,
                }
                for a in agents
            ],
        },
        message="Session retrieved",
    )


@router.get("/sessions/{session_id}/events", response_model=StandardResponse)
async def get_session_events(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get historical events for a playground session."""
    result = await db.execute(select(PlaygroundSession).where(PlaygroundSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    count_result = await db.execute(
        select(PlaygroundEvent).where(PlaygroundEvent.session_id == session_id)
    )
    total = len(count_result.scalars().all())

    event_result = await db.execute(
        select(PlaygroundEvent)
        .where(PlaygroundEvent.session_id == session_id)
        .order_by(PlaygroundEvent.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    events = event_result.scalars().all()

    return StandardResponse(
        data={
            "items": [
                {
                    "event_id": e.id,
                    "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
                    "agent_id": e.agent_id,
                    "agent_name": e.agent_name,
                    "payload": e.payload,
                    "timestamp": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message=f"Retrieved {len(events)} events",
    )


@router.post("/sessions/{session_id}/start", response_model=StandardResponse)
async def start_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Start the simulation for a session."""
    result = await db.execute(select(PlaygroundSession).where(PlaygroundSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == PlaygroundSessionStatus.RUNNING:
        return StandardResponse(success=False, message="Session is already running")

    # Stop any existing engine for this session
    old_engine = get_engine(session_id)
    if old_engine:
        await old_engine.stop()
        remove_engine(session_id)

    # Create and start new engine
    engine = PlaygroundEngine(session_id)
    await engine.load_from_db(db)
    set_engine(session_id, engine)

    session.status = PlaygroundSessionStatus.RUNNING
    from app.models import utc_now
    session.started_at = utc_now()
    await db.commit()

    # Start engine in background
    import asyncio
    asyncio.create_task(engine.start())

    return StandardResponse(
        data={"session_id": session_id, "status": "running", "agent_count": len(engine.agents)},
        message="Simulation started",
    )


@router.post("/sessions/{session_id}/stop", response_model=StandardResponse)
async def stop_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Stop the simulation for a session."""
    result = await db.execute(select(PlaygroundSession).where(PlaygroundSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = get_engine(session_id)
    if engine:
        await engine.stop()
        remove_engine(session_id)

    session.status = PlaygroundSessionStatus.COMPLETED
    from app.models import utc_now
    session.stopped_at = utc_now()
    await db.commit()

    return StandardResponse(
        data={"session_id": session_id, "status": "completed"},
        message="Simulation stopped",
    )


@router.delete("/sessions/{session_id}", response_model=StandardResponse)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Delete a session and all its agents/events."""
    result = await db.execute(select(PlaygroundSession).where(PlaygroundSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = get_engine(session_id)
    if engine:
        await engine.stop()
        remove_engine(session_id)

    await db.delete(session)
    await db.commit()

    return StandardResponse(data={"deleted": True}, message="Session deleted")


@router.post("/sessions/from-template", response_model=StandardResponse)
async def create_from_template(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
) -> StandardResponse:
    """Create a session from an industry template.

    Payload::

        {
            "template_id": "healthcare",
            "provider_name": "openai",
            "provider_config": {"api_key": "sk-...", "model": "gpt-4o-mini"}
        }
    """
    provider_name = payload.get("provider_name", "openai")
    provider_config = payload.get("provider_config", {})
    is_valid, error = await _validate_provider_config(provider_name, provider_config)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Provider validation failed: {error}")

    template_id = payload.get("template_id")
    tpl = get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    session = PlaygroundSession(
        name=tpl["name"],
        description=tpl["description"],
        provider_name=payload.get("provider_name", "openai"),
        provider_config=payload.get("provider_config", {}),
        industry_template=template_id,
        status=PlaygroundSessionStatus.PENDING,
    )
    db.add(session)
    await db.flush()

    for agent_data in tpl.get("agents", []):
        agent = PlaygroundAgent(
            session_id=session.id,
            name=agent_data["name"],
            role=agent_data["role"],
            risk_level=agent_data.get("risk_level", "medium"),
            system_prompt=agent_data["system_prompt"],
            actions=agent_data.get("actions", []),
            situations=agent_data.get("situations", []),
            is_active=True,
        )
        db.add(agent)

    await db.commit()

    return StandardResponse(
        data={
            "session_id": session.id,
            "name": session.name,
            "template_id": template_id,
            "agent_count": len(tpl.get("agents", [])),
        },
        message=f"Session created from template {template_id}",
    )


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str, _=Depends(get_current_user)):
    engine = get_engine(session_id)
    if not engine:
        raise HTTPException(status_code=404, detail="Session not running")
    return StandardResponse(data={
        "running": engine.running,
        "awaiting_human_approval": engine.awaiting_human_approval is not None,
        "approval_data": engine.awaiting_human_approval,
    })


@router.post("/sessions/{session_id}/approve", response_model=StandardResponse)
async def approve_action(session_id: str, _=Depends(get_current_user)):
    engine = get_engine(session_id)
    if not engine or not engine.awaiting_human_approval:
        raise HTTPException(status_code=400, detail="No action awaiting approval")
    engine.submit_human_decision("approve")
    return StandardResponse(message="Action approved")


@router.post("/sessions/{session_id}/deny", response_model=StandardResponse)
async def deny_action(session_id: str, _=Depends(get_current_user)):
    engine = get_engine(session_id)
    if not engine or not engine.awaiting_human_approval:
        raise HTTPException(status_code=400, detail="No action awaiting approval")
    engine.submit_human_decision("deny")
    return StandardResponse(message="Action denied")


@router.post("/provider-validation-status", response_model=StandardResponse)
async def check_provider_validation(payload: dict, _=Depends(get_current_user)):
    provider_name = payload.get("provider_name", "openai")
    config = payload.get("config", {})
    is_valid, error = await _validate_provider_config(provider_name, config)
    return StandardResponse(data={"valid": is_valid, "error": error})
