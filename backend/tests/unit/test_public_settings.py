"""Tests for the public settings endpoint."""

import pytest
from unittest.mock import MagicMock, patch


class TestPublicSettings:
    @pytest.mark.asyncio
    async def test_public_settings_structure(self, async_client):
        mock_settings = MagicMock()
        mock_settings.environment = "testing"
        mock_settings.demo_mode = False
        mock_settings.slack_webhook_url = "https://hooks.slack.com/test"
        mock_settings.smtp_host = "smtp.test.com"
        mock_settings.smtp_from = "from@test.com"
        mock_settings.pagerduty_routing_key = None

        with patch("app.core.config.get_settings", return_value=mock_settings):
            response = await async_client.get("/api/v1/settings/public")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        payload = data["data"]
        assert payload["environment"] == "testing"
        assert payload["demo_mode"] is False
        assert payload["version"] == "0.1.0"
        notifications = payload["notifications"]
        assert notifications["slack"] is True
        assert notifications["email"] is True
        assert notifications["pagerduty"] is False

    @pytest.mark.asyncio
    async def test_public_settings_no_auth_required(self, async_client):
        response = await async_client.get("/api/v1/settings/public")
        assert response.status_code == 200
