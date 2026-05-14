"""Tests for the CrewAI middleware guard decorator."""

import pytest
from unittest.mock import AsyncMock, patch

from playbook_sdk.middleware.crewai import CrewAIGuard, crewai_guard
from playbook_sdk.exceptions import GuardBlockedError, GuardQuarantinedError


class FakeCrewAgent:
    """Fake CrewAI Agent for testing auto agent_id extraction."""
    role = "researcher-007"


class TestCrewAIGuard:
    @pytest.mark.asyncio
    async def test_allow_proceeds_normally(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "ALLOW", "confidence": 0.95}
            MockClient.return_value = client

            g = CrewAIGuard(agent_id="crew-test", endpoint="http://test")

            @g
            async def my_task():
                return "success"

            result = await my_task()
            assert result == "success"

    @pytest.mark.asyncio
    async def test_block_raises_error(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "BLOCK", "reason": "Too risky"}
            MockClient.return_value = client

            g = CrewAIGuard(agent_id="crew-test", endpoint="http://test")

            @g
            async def my_task():
                return "should not reach"

            with pytest.raises(GuardBlockedError, match="Too risky"):
                await my_task()

    @pytest.mark.asyncio
    async def test_quarantine_raises_error(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "QUARANTINE", "reason": "Suspicious"}
            MockClient.return_value = client

            g = CrewAIGuard(agent_id="crew-test", endpoint="http://test")

            @g
            async def my_task():
                return "should not reach"

            with pytest.raises(GuardQuarantinedError, match="Suspicious"):
                await my_task()

    @pytest.mark.asyncio
    async def test_escalate_proceeds_with_warning(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "ESCALATE", "reason": "Needs review"}
            MockClient.return_value = client

            g = CrewAIGuard(agent_id="crew-test", endpoint="http://test")

            @g
            async def my_task():
                return "proceeded"

            result = await my_task()
            assert result == "proceeded"

    @pytest.mark.asyncio
    async def test_on_block_callback(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "BLOCK", "reason": "Unsafe"}
            MockClient.return_value = client

            async def handle_block(verdict, *args, **kwargs):
                return {"blocked": True, "reason": verdict["reason"]}

            g = CrewAIGuard(
                agent_id="crew-test", endpoint="http://test", on_block=handle_block
            )

            @g
            async def my_task():
                return "should not reach"

            result = await my_task()
            assert result["blocked"] is True

    def test_sync_function_support(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "ALLOW"}
            MockClient.return_value = client

            g = CrewAIGuard(agent_id="crew-test", endpoint="http://test")

            @g
            def my_sync_task():
                return "sync success"

            result = my_sync_task()
            assert result == "sync success"

    def test_guard_factory(self):
        g = crewai_guard(agent_id="factory-test")
        assert isinstance(g, CrewAIGuard)
        assert g.agent_id == "factory-test"

    @pytest.mark.asyncio
    async def test_auto_agent_id_from_crewai_agent(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "ALLOW"}
            MockClient.return_value = client

            g = CrewAIGuard(endpoint="http://test")

            @g
            async def my_task(agent):
                return f"ran for {agent.role}"

            fake_agent = FakeCrewAgent()
            result = await my_task(fake_agent)
            assert result == "ran for researcher-007"

            # Verify the judge was called with the extracted role
            call_kwargs = client.judge.call_args.kwargs
            assert call_kwargs["agent_id"] == "researcher-007"

    @pytest.mark.asyncio
    async def test_auto_agent_id_fallback(self):
        with patch("playbook_sdk.middleware.crewai.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.judge.return_value = {"verdict": "ALLOW"}
            MockClient.return_value = client

            g = CrewAIGuard(agent_id="fallback-agent", endpoint="http://test")

            @g
            async def my_task():
                return "no agent arg"

            result = await my_task()
            assert result == "no agent arg"

            call_kwargs = client.judge.call_args.kwargs
            assert call_kwargs["agent_id"] == "fallback-agent"
