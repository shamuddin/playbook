"""Integration tests for the PLAYBOOK SDK against a mock backend."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from playbook_sdk.client import PlaybookClient
from playbook_sdk.guard import Guard, guard
from playbook_sdk.exceptions import GuardBlockedError


class TestSDKIntegration:
    """Integration-style tests that verify end-to-end SDK behavior."""

    @pytest.mark.asyncio
    async def test_client_judge_happy_path(self):
        """Full flow: client creates token → judges action → receives ALLOW."""
        with patch("playbook_sdk.client.httpx.AsyncClient") as MockClient:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": {
                    "verdict": "ALLOW",
                    "confidence": 0.95,
                    "severity_score": 2,
                    "rationale": "Low risk action",
                }
            }
            mock_resp.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_http

            client = PlaybookClient(endpoint="http://test", api_key="test-key")
            result = await client.judge(
                agent_id="agent-001",
                action_type="tool_call",
                action_details={"function": "read_file", "args_count": 1},
            )
            assert result["verdict"] == "ALLOW"
            assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_guard_blocks_destructive_action(self):
        """Guard decorator blocks a destructive action via the SDK."""
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "BLOCK",
                "reason": "Data destruction not allowed",
                "severity_score": 10,
            }
            MockClient.return_value = client

            g = Guard(agent_id="agent-001", endpoint="http://test")

            @g
            async def delete_database():
                return "deleted"

            with pytest.raises(GuardBlockedError, match="Data destruction not allowed"):
                await delete_database()

    @pytest.mark.asyncio
    async def test_guard_allows_benign_action(self):
        """Guard decorator allows a benign action."""
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "ALLOW",
                "confidence": 0.95,
            }
            MockClient.return_value = client

            g = Guard(agent_id="agent-001", endpoint="http://test")

            @g
            async def read_status():
                return {"status": "ok"}

            result = await read_status()
            assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_guard_with_custom_on_block(self):
        """Guard with custom on_block callback returns fallback instead of raising."""
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "BLOCK",
                "reason": "Unsafe",
            }
            MockClient.return_value = client

            async def fallback(verdict, *args, **kwargs):
                return {"blocked": True, "fallback": "safe_default"}

            g = Guard(agent_id="agent-001", endpoint="http://test", on_block=fallback)

            @g
            async def risky_operation():
                return "done"

            result = await risky_operation()
            assert result["blocked"] is True
            assert result["fallback"] == "safe_default"

    def test_sync_guard_integration(self):
        """Sync function guarded correctly."""
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "ALLOW",
                "confidence": 0.9,
            }
            MockClient.return_value = client

            g = guard(agent_id="sync-agent", endpoint="http://test")

            @g
            def sync_action():
                return "sync_success"

            result = sync_action()
            assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_client_heartbeat(self):
        """Heartbeat sends correct payload."""
        with patch("playbook_sdk.client.httpx.AsyncClient") as MockClient:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": {"status": "ok"}}
            mock_resp.raise_for_status.return_value = None

            mock_http = AsyncMock()
            mock_http.post.return_value = mock_resp
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_http

            client = PlaybookClient(endpoint="http://test", api_key="key")
            result = await client.send_heartbeat(agent_id="agent-001")
            assert result["status"] == "ok"
