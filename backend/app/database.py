from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()


def _normalize_database_url(url: str) -> str:
    """Add async driver prefix if missing."""
    if url.startswith("sqlite:///") and "+aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://")
    return url


def _is_sqlite(url: str) -> bool:
    return "sqlite" in url.split("://", 1)[0]


def _build_engine(
    database_url: str,
    debug: bool = False,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    """Create an async engine with DB-appropriate pooling."""
    if _is_sqlite(database_url):
        return create_async_engine(
            database_url,
            echo=debug,
            poolclass=NullPool,
            future=True,
        )
    return create_async_engine(
        database_url,
        echo=debug,
        pool_size=pool_size,
        max_overflow=max_overflow,
        future=True,
    )


database_url = _normalize_database_url(settings.database_url)
engine = _build_engine(
    database_url,
    debug=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
