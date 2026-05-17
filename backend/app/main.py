import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database import AsyncSessionLocal, engine
from app.models import Agent, Base, PlaygroundSession, PlaygroundSessionStatus, utc_now
from app.core.security import get_current_user
from app.routers import (
    agents,
    auth,
    compliance,
    dashboard,
    demo,
    forensics,
    gemini,
    health,
    incidents,
    integrations,
    judge,
    lobstertrap,
    playbooks,
    playground,
    policy_builder,
    swarm,
    websocket,
)
from app.seed import seed_all
from app.services.detect.tailer import LogTailer

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Reset orphaned playground sessions (backend restarted while running)
    async with AsyncSessionLocal() as db:
        from sqlalchemy import update
        try:
            result = await db.execute(
                update(PlaygroundSession)
                .where(PlaygroundSession.status == PlaygroundSessionStatus.RUNNING)
                .values(status=PlaygroundSessionStatus.ERROR, stopped_at=utc_now())
            )
            await db.commit()
            if result.rowcount:
                print(f"[startup] Reset {result.rowcount} orphaned playground session(s) to ERROR")
                # Only mark playground-scoped agents offline since their session died
                await db.execute(
                    update(Agent)
                    .where(Agent.status == "online", Agent.system_id.like("pg-%"))
                    .values(status="offline")
                )
                await db.commit()
                print("[startup] Mirrored playground agents marked offline")
        except Exception as exc:
            print(f"[startup] Warning: failed to reset orphaned sessions: {exc}")

    # Seed reference data if configured
    if settings.is_demo_mode or settings.seed_on_startup:
        async with AsyncSessionLocal() as session:
            try:
                seeded = await seed_all(session)
                for table, count in seeded.items():
                    if count:
                        print(f"[seed] {table}: +{count} records")
            except Exception as exc:
                print(f"[seed] Warning: seeding failed: {exc}")

    # Initialize detection engine for tailer and Lobster Trap
    from app.services.detect import normalize_event
    from app.services.detect.engine import DetectionEngine
    from app.services.detect.incident_factory import IncidentFactory
    from app.services.websocket_manager import ws_manager

    engine_inst = DetectionEngine()

    # Start log tailer in demo/development mode
    tailer = None
    heartbeat_task = None
    lobstertrap_task = None
    if settings.is_demo_mode or settings.is_development:
        async def _on_event(event):
            """Process tailer events through detection pipeline."""
            async with AsyncSessionLocal() as session:
                try:
                    detection = engine_inst.evaluate(event)
                    if detection.incident_type is None:
                        return
                    incident = await IncidentFactory.create_incident(session, event, detection)
                    await session.commit()
                    await ws_manager.broadcast({
                        "event_type": "incident_detected",
                        "incident_id": incident.incident_id,
                        "severity": incident.severity,
                        "category": incident.category,
                        "incident_type": incident.incident_type,
                        "confidence": incident.confidence,
                        "agent_id": incident.agent_id,
                        "swarm_id": incident.swarm_id,
                        "timestamp": incident.created_at.isoformat(),
                    })
                except Exception as exc:
                    print(f"[tailer] Error processing event: {exc}")

        tailer = LogTailer(on_event=_on_event)
        await tailer.start()
        print(f"[tailer] Started monitoring: {tailer.log_dir}")

    # --- Lobster Trap integration ---
    if settings.lobstertrap_enabled:
        binary_path = Path(settings.lobstertrap_binary_path)
        if os.name == "nt" and not str(binary_path).endswith(".exe"):
            binary_path = Path(str(binary_path) + ".exe")
        if not binary_path.exists():
            # Try repo root fallback
            repo_root = Path(__file__).resolve().parents[2]
            alt = repo_root / binary_path
            if alt.exists():
                binary_path = alt
        if binary_path.exists():
            from app.services.lobstertrap_integration import (
                read_lobstertrap_logs,
                start_lobstertrap_proxy,
            )

            lt_status = await start_lobstertrap_proxy()
            print(f"[lobstertrap] Proxy started: {lt_status}")

            async def _on_lt_event(event):
                async with AsyncSessionLocal() as session:
                    try:
                        detection = engine_inst.evaluate(event)
                        if detection.incident_type is None:
                            return
                        incident = await IncidentFactory.create_incident(
                            session, event, detection
                        )
                        # Create JudgeDecision for Lobster Trap events
                        from app.models import JudgeDecision
                        verdict = "DENY" if "block_" in str(detection.matched_rules) else "QUARANTINE"
                        decision = JudgeDecision(
                            decision_id=f"JDG-{uuid.uuid4().hex[:12].upper()}",
                            incident_id=incident.id,
                            agent_id="lobstertrap-proxy",
                            verdict=verdict,
                            severity_score=round(detection.confidence * 100, 1),
                            confidence=round(detection.confidence, 2),
                            matched_rules=detection.matched_rules or [],
                            bypass_patterns_detected=[],
                            rationale=f"Lobster Trap DPI rule matched: {detection.matched_rules}",
                            latency_ms=detection.latency_ms,
                        )
                        session.add(decision)
                        await session.flush()
                        incident.judge_decision_id = decision.id
                        await session.commit()
                        await ws_manager.broadcast({
                            "event_type": "incident_detected",
                            "source": "lobstertrap",
                            "incident_id": incident.incident_id,
                            "severity": incident.severity,
                            "category": incident.category,
                            "incident_type": incident.incident_type,
                            "confidence": incident.confidence,
                            "agent_id": incident.agent_id,
                            "swarm_id": incident.swarm_id,
                            "timestamp": incident.created_at.isoformat(),
                        })
                    except Exception as exc:
                        print(f"[lobstertrap] Error processing event: {exc}")

            lobstertrap_task = asyncio.create_task(
                read_lobstertrap_logs(on_event=_on_lt_event)
            )
            print("[lobstertrap] Started log reader")
        else:
            print(f"[lobstertrap] Binary not found at {binary_path}")

    if settings.is_demo_mode or settings.is_development:
        # Start WebSocket heartbeat
        async def _heartbeat():
            while True:
                try:
                    await asyncio.sleep(30)
                    await ws_manager.broadcast({
                        "event_type": "SYSTEM_STATUS",
                        "status": "healthy",
                        "components": {
                            "api": "healthy",
                            "database": "healthy",
                            "websocket": "healthy",
                        },
                        "active_connections": ws_manager.active_connections,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    print(f"[heartbeat] Error: {exc}")

        heartbeat_task = asyncio.create_task(_heartbeat())
        print("[heartbeat] Started WebSocket status heartbeat (30s)")

    yield

    # Shutdown
    if lobstertrap_task is not None:
        lobstertrap_task.cancel()
        try:
            await lobstertrap_task
        except asyncio.CancelledError:
            pass
        print("[lobstertrap] Stopped log reader")
        from app.services.lobstertrap_integration import stop_lobstertrap_proxy
        await stop_lobstertrap_proxy()
        print("[lobstertrap] Stopped proxy")
    if heartbeat_task is not None:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        print("[heartbeat] Stopped")
    if tailer is not None:
        await tailer.stop()
        print("[tailer] Stopped")
    await engine.dispose()


app = FastAPI(
    title="PLAYBOOK",
    description="Automated incident response system for AI agent deployments",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — restricted to configured frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

# Routers — public first (no auth required)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(demo.router, prefix=settings.api_prefix)

# Protected routers (JWT auth required)
_auth_dep = [Depends(get_current_user)]
app.include_router(incidents.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(judge.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(playbooks.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(policy_builder.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(forensics.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(compliance.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(agents.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(dashboard.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(integrations.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(lobstertrap.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(playground.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(swarm.router, prefix=settings.api_prefix, dependencies=_auth_dep)
app.include_router(gemini.router, prefix=settings.api_prefix, dependencies=_auth_dep)
# WebSocket router handles auth internally via query params — don't apply HTTP Bearer deps
app.include_router(websocket.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "name": "PLAYBOOK",
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
