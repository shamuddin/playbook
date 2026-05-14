"""Tests for database configuration and URL normalization."""

import pytest
from unittest.mock import patch

from sqlalchemy.pool import NullPool


class TestDatabaseConfig:
    def test_normalize_sqlite_url(self):
        from app.database import _normalize_database_url

        assert _normalize_database_url("sqlite:///./data/playbooks.db") == "sqlite+aiosqlite:///./data/playbooks.db"

    def test_normalize_postgresql_url(self):
        from app.database import _normalize_database_url

        assert (
            _normalize_database_url("postgresql://user:pass@localhost/playbook")
            == "postgresql+asyncpg://user:pass@localhost/playbook"
        )

    def test_normalize_already_async_url(self):
        from app.database import _normalize_database_url

        # Should pass through unchanged
        assert (
            _normalize_database_url("sqlite+aiosqlite:///./test.db")
            == "sqlite+aiosqlite:///./test.db"
        )
        assert (
            _normalize_database_url("postgresql+asyncpg://localhost/db")
            == "postgresql+asyncpg://localhost/db"
        )

    def test_is_sqlite(self):
        from app.database import _is_sqlite

        assert _is_sqlite("sqlite+aiosqlite:///./test.db") is True
        assert _is_sqlite("postgresql+asyncpg://localhost/db") is False

    def test_sqlite_engine_uses_null_pool(self):
        with patch("app.database.create_async_engine") as mock_engine:
            from app.database import _build_engine
            _build_engine("sqlite+aiosqlite:///./test.db")

            call = mock_engine.call_args
            assert call.kwargs.get("poolclass") == NullPool

    def test_postgresql_engine_uses_standard_pool(self):
        with patch("app.database.create_async_engine") as mock_engine:
            from app.database import _build_engine
            _build_engine("postgresql+asyncpg://user:pass@localhost/playbook")

            call = mock_engine.call_args
            assert "poolclass" not in call.kwargs
            assert call.kwargs.get("pool_size") == 5

    def test_config_pool_size_validation(self):
        from app.core.config import Settings

        with pytest.raises(ValueError, match="database_pool_size must be between 1 and 20"):
            Settings(database_pool_size=0)

        with pytest.raises(ValueError, match="database_pool_size must be between 1 and 20"):
            Settings(database_pool_size=21)

        # Valid values should work
        s = Settings(database_pool_size=5)
        assert s.database_pool_size == 5
        s = Settings(database_pool_size=20)
        assert s.database_pool_size == 20
