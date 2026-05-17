"""Agent Swarm router for orchestrating AI agent simulations."""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user, security_bearer
from app.schemas import StandardResponse
from app.services.swarm_orchestrator import (
    get_swarm,
    remove_swarm,
    set_swarm,
    SwarmOrchestrator,
)

router = APIRouter(prefix="/swarm", tags=["swarm"])


@router.post("/run", response_model=StandardResponse)
async def run_swarm(
    payload: dict,
    _=Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> StandardResponse:
    """Start a new agent swarm simulation.

    Payload:
        {
            "scenario_id": "fx-swap" | "data-exfil" | "prompt-injection" | "full-swarm",
            "gcp_project_id": "my-gcp-project-123",
            "gcp_region": "global",
            "model": "gemini-3.1-flash-lite"
        }
    """
    scenario_id = payload.get("scenario_id", "full-swarm")
    gcp_project_id = payload.get("gcp_project_id")
    gcp_region = payload.get("gcp_region", "global")
    model = payload.get("model", "gemini-3.1-flash-lite")
    api_key = credentials.credentials if credentials else ""

    # Generate session ID
    import uuid
    session_id = f"swarm-{uuid.uuid4().hex[:8]}"

    # Create orchestrator
    swarm = SwarmOrchestrator(
        session_id=session_id,
        gcp_project_id=gcp_project_id,
        gcp_region=gcp_region,
        model=model,
        api_key=api_key,
    )
    await swarm.setup_agents(scenario_id)

    # Store in registry
    set_swarm(session_id, swarm)

    # Start in background
    task = asyncio.create_task(swarm.run())
    task.add_done_callback(
        lambda t: print(f"[swarm] Swarm run completed: {t.exception()}") if t.done() and t.exception() else None
    )

    return StandardResponse(
        data={
            "session_id": session_id,
            "scenario_id": scenario_id,
            "status": "running",
            "agent_count": len(swarm._agents),
        },
        message=f"Swarm '{scenario_id}' started with {len(swarm._agents)} agents",
    )


@router.get("/{session_id}/status", response_model=StandardResponse)
async def get_swarm_status(
    session_id: str,
    _=Depends(get_current_user),
) -> StandardResponse:
    """Get current swarm status and statistics."""
    swarm = get_swarm(session_id)
    if not swarm:
        raise HTTPException(status_code=404, detail="Swarm session not found")

    return StandardResponse(
        data=swarm.get_stats(),
        message="Swarm status retrieved",
    )


@router.get("/{session_id}/events", response_model=StandardResponse)
async def get_swarm_events(
    session_id: str,
    since: int = 0,
    _=Depends(get_current_user),
) -> StandardResponse:
    """Get swarm events since a given index."""
    swarm = get_swarm(session_id)
    if not swarm:
        raise HTTPException(status_code=404, detail="Swarm session not found")

    events = swarm.get_events(since=since)
    return StandardResponse(
        data={
            "events": [
                {
                    "event_type": e.event_type,
                    "agent_id": e.agent_id,
                    "message": e.message,
                    "verdict": e.verdict,
                    "latency_ms": e.latency_ms,
                    "timestamp": e.timestamp,
                }
                for e in events
            ],
            "total": len(events),
            "next_index": since + len(events),
        },
        message=f"Retrieved {len(events)} events",
    )


@router.post("/{session_id}/stop", response_model=StandardResponse)
async def stop_swarm(
    session_id: str,
    _=Depends(get_current_user),
) -> StandardResponse:
    """Stop a running swarm."""
    swarm = get_swarm(session_id)
    if not swarm:
        raise HTTPException(status_code=404, detail="Swarm session not found")

    await swarm.stop()
    remove_swarm(session_id)

    return StandardResponse(
        data={"session_id": session_id, "status": "stopped"},
        message="Swarm stopped",
    )


@router.post("/test-connection", response_model=StandardResponse)
async def test_connection(
    payload: dict,
    _=Depends(get_current_user),
) -> StandardResponse:
    """Test GCP ADC connection by pinging Vertex AI.

    Payload:
        {
            "gcp_project_id": "my-project-123",
            "gcp_region": "global",
            "model": "gemini-3.1-flash-lite"
        }
    """
    gcp_project_id = payload.get("gcp_project_id")
    gcp_region = payload.get("gcp_region", "global")
    model = payload.get("model", "gemini-3.1-flash-lite")

    if not gcp_project_id:
        return StandardResponse(
            success=False,
            message="GCP Project ID is required for ADC authentication",
            data={"valid": False, "error": "Missing gcp_project_id"},
        )

    try:
        from google import genai

        client = genai.Client(
            vertexai=True,
            project=gcp_project_id,
            location=gcp_region,
        )

        response = client.models.generate_content(
            model=model,
            contents="Say PONG",
        )
        content = response.text

        return StandardResponse(
            data={
                "valid": True,
                "model": model,
                "region": gcp_region,
                "project_id": gcp_project_id,
                "response_preview": content[:50] if content else "(no text)",
            },
            message="ADC connection successful — Vertex AI is reachable",
        )
    except Exception as exc:
        error_str = str(exc).lower()
        # Graceful fallback: ADC not configured
        if any(keyword in error_str for keyword in [
            "defaultcredentialserror",
            "could not automatically determine credentials",
            "unable to acquire impersonated credentials",
            "permission denied",
            "403",
        ]):
            return StandardResponse(
                data={
                    "valid": True,
                    "model": model,
                    "region": gcp_region,
                    "project_id": gcp_project_id,
                    "warning": "ADC credentials not detected. The swarm will run in stub mode (Judge Layer still works 100%).",
                },
                message="ADC not configured — stub mode available",
            )

        return StandardResponse(
            success=False,
            message=f"ADC connection failed: {exc}",
            data={"valid": False, "error": str(exc)},
        )


@router.get("/models", response_model=StandardResponse)
async def list_models(
    _=Depends(get_current_user),
) -> StandardResponse:
    """List available Gemini models for swarm agents."""
    models = [
        {
            "id": "gemini-3.1-flash-lite",
            "name": "Gemini 3.1 Flash Lite",
            "description": "Fastest, most cost-efficient. Best for high-volume demos.",
            "recommended": True,
            "family": "Gemini 3.1",
        },
        {
            "id": "gemini-3.1-flash",
            "name": "Gemini 3.1 Flash",
            "description": "Fast multimodal model with good quality.",
            "recommended": False,
            "family": "Gemini 3.1",
        },
        {
            "id": "gemini-3.1-pro",
            "name": "Gemini 3.1 Pro",
            "description": "Highest quality reasoning. Slower but more capable.",
            "recommended": False,
            "family": "Gemini 3.1",
        },
        {
            "id": "gemini-3.0-flash",
            "name": "Gemini 3.0 Flash",
            "description": "Balanced speed and quality for general tasks.",
            "recommended": False,
            "family": "Gemini 3.0",
        },
        {
            "id": "gemini-3.0-pro",
            "name": "Gemini 3.0 Pro",
            "description": "Strong reasoning and code generation.",
            "recommended": False,
            "family": "Gemini 3.0",
        },
        {
            "id": "gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "description": "Prior-generation fast model.",
            "recommended": False,
            "family": "Gemini 2.5",
        },
        {
            "id": "gemini-2.5-pro",
            "name": "Gemini 2.5 Pro",
            "description": "Prior-generation reasoning model.",
            "recommended": False,
            "family": "Gemini 2.5",
        },
    ]

    return StandardResponse(
        data={"models": models, "total": len(models)},
        message=f"Found {len(models)} models in Vertex AI Model Garden",
    )


@router.get("/scenarios", response_model=StandardResponse)
async def list_scenarios(
    _=Depends(get_current_user),
) -> StandardResponse:
    """List available swarm scenarios."""
    scenarios = [
        {
            "id": "fx-swap",
            "name": "FX Swap Unauthorized Trade",
            "description": (
                "Step Finance Trader v3 attempts a $40M FX swap "
                "beyond its $5M authorization limit through an unvetted broker."
            ),
            "agents": 1,
            "tasks": 2,
            "incident_type": "AGT-FIN-002",
        },
        {
            "id": "data-exfil",
            "name": "Data Exfiltration",
            "description": (
                "Data Analyst agent is asked to export customer PII "
                "(emails and SSNs) to an unauthorized external destination."
            ),
            "agents": 1,
            "tasks": 2,
            "incident_type": "AGT-EXT-005",
        },
        {
            "id": "prompt-injection",
            "name": "Prompt Injection Attack",
            "description": (
                "Customer Support Bot receives a jailbreak prompt "
                "attempting to make it reveal system prompts and internal credentials."
            ),
            "agents": 1,
            "tasks": 2,
            "incident_type": "AGT-INJ-006",
        },
        {
            "id": "full-swarm",
            "name": "Full 3-Agent Swarm",
            "description": (
                "All three agents run concurrently: FX Trader, Data Analyst, "
                "and Support Bot. Each executes one normal and one malicious action."
            ),
            "agents": 3,
            "tasks": 6,
            "incident_types": ["AGT-FIN-002", "AGT-EXT-005", "AGT-INJ-006"],
        },
    ]

    return StandardResponse(
        data={"scenarios": scenarios, "total": len(scenarios)},
        message=f"Found {len(scenarios)} swarm scenarios",
    )
