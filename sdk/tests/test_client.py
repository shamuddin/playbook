"""Tests for the PlaybookClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from playbook_sdk.client import PlaybookClient


class TestPlaybookClient:
    def test_init_defaults(self):
        with patch.dict("os.environ", {}, clear=True):
            client = PlaybookClient()
            assert client.endpoint == "http://localhost:8000"
            assert client.api_key == ""
            assert client.timeout == 5.0

    def test_init_from_env(self):
        with patch.dict(
            "os.environ",
            {"PLAYBOOK_ENDPOINT": "https://test.com", "PLAYBOOK_API_KEY": "key123"},
        ):
            client = PlaybookClient()
            assert client.endpoint == "https://test.com"
            assert client.api_key == "key123"

    def test_init_explicit(self):
        client = PlaybookClient(endpoint="https://explicit.com", api_key="abc")
        assert client.endpoint == "https://explicit.com"
        assert client.api_key == "abc"

    def test_headers_without_api_key(self):
        client = PlaybookClient()
        headers = client._get_headers()
        assert headers == {"Content-Type": "application/json"}

    def test_headers_with_api_key(self):
        client = PlaybookClient(api_key="secret")
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer secret"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_judge(self):
        client = PlaybookClient(endpoint="http://test", api_key="key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"verdict": "BLOCK"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            result = await client.judge(
                agent_id="agent-001",
                action_type="tool_call",
                action_details={"tool": "test"},
            )
            assert result["verdict"] == "BLOCK"

    @pytest.mark.asyncio
    async def test_report_incident(self):
        client = PlaybookClient(endpoint="http://test", api_key="key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"incident_id": "INC-123"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            result = await client.report_incident(
                agent_id="agent-001",
                incident_type="AGT-DEL-001",
                severity="critical",
                description="Test incident",
            )
            assert result["incident_id"] == "INC-123"

    @pytest.mark.asyncio
    async def test_send_heartbeat(self):
        client = PlaybookClient(endpoint="http://test", api_key="key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"status": "online"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.client, "post", return_value=mock_response):
            result = await client.send_heartbeat("agent-001", health_score=95.0)
            assert result["status"] == "online"

    @pytest.mark.asyncio
    async def test_close(self):
        client = PlaybookClient(endpoint="http://test")
        # Access client property to create internal client
        _ = client.client
        await client.close()
        assert client._client is None or client._client.is_closed
