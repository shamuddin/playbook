"""Tests for the notification service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.notification_service import NotificationChannel, NotificationResult, NotificationService


class TestNotificationService:
    @pytest.fixture
    def service(self):
        return NotificationService()

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.is_closed = False
        return client

    # ------------------------------------------------------------------
    # Slack
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_slack_success(self, service, mock_client):
        service._client = mock_client
        mock_client.post = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        with patch.object(service.settings, "slack_webhook_url", "https://hooks.slack.com/test"):
            result = await service.send("slack", {"title": "Alert", "body": "Test"})

        assert result.channel == "slack"
        assert result.success is True
        assert "200" in result.detail

    @pytest.mark.asyncio
    async def test_send_slack_missing_config(self, service):
        with patch.object(service.settings, "slack_webhook_url", None):
            result = await service.send("slack", {"title": "Alert"})

        assert result.success is False
        assert "not configured" in result.detail

    @pytest.mark.asyncio
    async def test_send_slack_http_error(self, service, mock_client):
        service._client = mock_client
        mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad request",
            request=MagicMock(),
            response=MagicMock(status_code=400),
        ))

        with patch.object(service.settings, "slack_webhook_url", "https://hooks.slack.com/test"):
            result = await service.send("slack", {"title": "Alert"})

        assert result.success is False
        assert "HTTP" in result.detail or "Bad request" in result.detail

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_email_missing_config(self, service):
        with patch.object(service.settings, "smtp_host", None):
            result = await service.send("email", {"title": "Alert", "body": "Test"})

        assert result.success is False
        assert "incomplete" in result.detail

    @pytest.mark.asyncio
    async def test_send_email_success(self, service):
        with (
            patch.object(service.settings, "smtp_host", "smtp.test.com"),
            patch.object(service.settings, "smtp_port", 587),
            patch.object(service.settings, "smtp_user", "user"),
            patch.object(service.settings, "smtp_password", "pass"),
            patch.object(service.settings, "smtp_from", "from@test.com"),
            patch.object(service.settings, "notification_default_recipients", ["to@test.com"]),
            patch("app.services.notification_service.asyncio.to_thread", new_callable=AsyncMock) as mock_thread,
        ):
            result = await service.send("email", {"title": "Alert", "body": "Test"})

        assert result.channel == "email"
        assert result.success is True
        assert result.detail == "Sent"
        mock_thread.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_email_failure(self, service):
        with (
            patch.object(service.settings, "smtp_host", "smtp.test.com"),
            patch.object(service.settings, "smtp_from", "from@test.com"),
            patch.object(service.settings, "notification_default_recipients", ["to@test.com"]),
            patch("app.services.notification_service.asyncio.to_thread", new_callable=AsyncMock) as mock_thread,
        ):
            mock_thread.side_effect = Exception("SMTP error")
            result = await service.send("email", {"title": "Alert", "body": "Test"})

        assert result.success is False
        assert "SMTP error" in result.detail

    # ------------------------------------------------------------------
    # PagerDuty
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_pagerduty_success(self, service, mock_client):
        service._client = mock_client
        mock_client.post = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"dedup_key": "pd-key-123"}
        mock_client.post.return_value = mock_response

        with patch.object(service.settings, "pagerduty_routing_key", "test-key"):
            result = await service.send("pagerduty", {"title": "Alert", "body": "Test"})

        assert result.channel == "pagerduty"
        assert result.success is True
        assert "pd-key-123" in result.detail

    @pytest.mark.asyncio
    async def test_send_pagerduty_missing_config(self, service):
        with patch.object(service.settings, "pagerduty_routing_key", None):
            result = await service.send("pagerduty", {"title": "Alert"})

        assert result.success is False
        assert "not configured" in result.detail

    @pytest.mark.asyncio
    async def test_send_pagerduty_http_error(self, service, mock_client):
        service._client = mock_client
        mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Bad request",
            request=MagicMock(),
            response=MagicMock(status_code=400),
        ))

        with patch.object(service.settings, "pagerduty_routing_key", "test-key"):
            result = await service.send("pagerduty", {"title": "Alert"})

        assert result.success is False

    # ------------------------------------------------------------------
    # Multi-channel & edge cases
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_send_multi(self, service):
        with patch.object(service, "send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = [
                NotificationResult("slack", True, "ok"),
                NotificationResult("email", False, "fail"),
            ]
            results = await service.send_multi(
                channels=["slack", "email"],
                message={"title": "Alert"},
            )

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    @pytest.mark.asyncio
    async def test_send_unknown_channel(self, service):
        result = await service.send("telegram", {"title": "Alert"})
        assert result.success is False
        assert "Unknown channel" in result.detail

    def test_map_severity(self):
        assert NotificationService._map_severity("critical") == "critical"
        assert NotificationService._map_severity("high") == "error"
        assert NotificationService._map_severity("medium") == "warning"
        assert NotificationService._map_severity("low") == "info"
        assert NotificationService._map_severity("unknown") == "warning"

    @pytest.mark.asyncio
    async def test_close(self, service):
        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.aclose = AsyncMock()
        service._client = mock_client
        await service.close()
        mock_client.aclose.assert_awaited_once()
