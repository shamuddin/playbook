from typing import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import create_access_token, get_password_hash
from app.database import get_db
from app.main import app
from app.models import Base, User, UserRole

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create and drop tables for each test."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def seeded_db(db_session):
    """Seed reference data (rules, playbooks, baselines, bypass patterns)."""
    from app.seed import seed_all
    await seed_all(db_session)
    yield db_session


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_app(db_session) -> FastAPI:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest_asyncio.fixture
async def seeded_test_app(db_session) -> FastAPI:
    """App fixture with seeded reference data."""
    from app.seed import seed_all
    await seed_all(db_session)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest_asyncio.fixture
async def seeded_async_client(seeded_test_app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=seeded_test_app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_async_client(seeded_test_app, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated async client with a test user and valid JWT token."""
    # Create test user
    test_user = User(
        email="test@playbook.local",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(test_user)
    await db_session.commit()

    # Generate JWT token
    token = create_access_token(data={"sub": test_user.id, "email": test_user.email, "role": test_user.role.value})

    async with AsyncClient(
        transport=ASGITransport(app=seeded_test_app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client
