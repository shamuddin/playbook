"""Tests for the HeartbeatSender."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from playbook_sdk.heartbeat import HeartbeatSender


class TestHeartbeatSender:
    @pytest.mark.asyncio
    async def test_start_stop(self):
        with patch("playbook_sdk.heartbeat.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.send_heartbeat = AsyncMock(return_value={"status": "online"})
            MockClient.return_value = client

            sender = HeartbeatSender(agent_id="agent-001", interval=0.1)
            sender.start()
            assert sender._running is True

            await asyncio.sleep(0.25)
            sender.stop()
            assert sender._running is False
            assert client.send_heartbeat.call_count >= 1

    @pytest.mark.asyncio
    async def test_heartbeat_failure_logged(self):
        with patch("playbook_sdk.heartbeat.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.send_heartbeat = AsyncMock(side_effect=Exception("Network error"))
            MockClient.return_value = client

            sender = HeartbeatSender(agent_id="agent-001", interval=0.1)
            sender.start()
            await asyncio.sleep(0.25)
            sender.stop()

            assert client.send_heartbeat.call_count >= 1

    @pytest.mark.asyncio
    async def test_close(self):
        with patch("playbook_sdk.heartbeat.PlaybookClient") as MockClient:
            client = AsyncMock()
            client.close = AsyncMock()
            MockClient.return_value = client

            sender = HeartbeatSender(agent_id="agent-001")
            sender.start()
            await sender.close()
            assert sender._running is False
            client.close.assert_awaited_once()
