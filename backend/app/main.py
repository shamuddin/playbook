from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database import AsyncSessionLocal, engine
from app.models import Base
from app.routers import (
    compliance,
    demo,
    forensics,
    health,
    incidents,
    judge,
    playbooks,
    policy_builder,
    websocket,
)
from app.seed import seed_all

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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

    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="PLAYBOOK",
    description="Automated incident response system for AI agent deployments",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(incidents.router, prefix=settings.api_prefix)
app.include_router(judge.router, prefix=settings.api_prefix)
app.include_router(playbooks.router, prefix=settings.api_prefix)
app.include_router(policy_builder.router, prefix=settings.api_prefix)
app.include_router(forensics.router, prefix=settings.api_prefix)
app.include_router(compliance.router, prefix=settings.api_prefix)
app.include_router(demo.router, prefix=settings.api_prefix)
app.include_router(websocket.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "name": "PLAYBOOK",
        "version": "0.1.0",
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
    }
