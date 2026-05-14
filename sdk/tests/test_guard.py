"""Tests for the @guard decorator."""

import pytest
from unittest.mock import AsyncMock, patch

from playbook_sdk.guard import Guard, guard
from playbook_sdk.exceptions import GuardBlockedError, GuardQuarantinedError


class TestGuardDecorator:
    @pytest.mark.asyncio
    async def test_allow_proceeds_normally(self):
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "ALLOW",
                "confidence": 0.95,
            }
            MockClient.return_value = client

            g = Guard(agent_id="test", endpoint="http://test")

            @g
            async def my_action():
                return "success"

            result = await my_action()
            assert result == "success"

    @pytest.mark.asyncio
    async def test_block_raises_error(self):
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "BLOCK",
                "reason": "Too risky",
            }
            MockClient.return_value = client

            g = Guard(agent_id="test", endpoint="http://test")

            @g
            async def my_action():
                return "should not reach"

            with pytest.raises(GuardBlockedError, match="Too risky"):
                await my_action()

    @pytest.mark.asyncio
    async def test_quarantine_raises_error(self):
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "QUARANTINE",
                "reason": "Suspicious pattern",
            }
            MockClient.return_value = client

            g = Guard(agent_id="test", endpoint="http://test")

            @g
            async def my_action():
                return "should not reach"

            with pytest.raises(GuardQuarantinedError, match="Suspicious pattern"):
                await my_action()

    @pytest.mark.asyncio
    async def test_escalate_proceeds_with_warning(self):
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "ESCALATE",
                "reason": "Needs review",
            }
            MockClient.return_value = client

            g = Guard(agent_id="test", endpoint="http://test")

            @g
            async def my_action():
                return "proceeded"

            result = await my_action()
            assert result == "proceeded"

    @pytest.mark.asyncio
    async def test_on_block_callback(self):
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {
                "verdict": "BLOCK",
                "reason": "Unsafe",
            }
            MockClient.return_value = client

            async def handle_block(verdict, *args, **kwargs):
                return {"blocked": True, "reason": verdict["reason"]}

            g = Guard(agent_id="test", endpoint="http://test", on_block=handle_block)

            @g
            async def my_action():
                return "should not reach"

            result = await my_action()
            assert result["blocked"] is True

    def test_sync_function_support(self):
        with patch("playbook_sdk.guard.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "ALLOW"}
            MockClient.return_value = client

            g = Guard(agent_id="test", endpoint="http://test")

            @g
            def my_sync_action():
                return "sync success"

            result = my_sync_action()
            assert result == "sync success"

    def test_guard_factory(self):
        g = guard(agent_id="factory-test")
        assert isinstance(g, Guard)
        assert g.agent_id == "factory-test"
