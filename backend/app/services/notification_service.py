"""Notification service for PLAYBOOK.

Sends alerts through Slack (webhook), Email (SMTP), and PagerDuty (Events API v2).
All external calls are async. Missing configuration is handled gracefully — the
service logs a warning and returns a failed result instead of raising.
"""

import json
import logging
import asyncio
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Any, Optional

import httpx
from app.core.config import get_settings

logger = logging.getLogger("playbook.notifications")


class NotificationChannel(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"


@dataclass
class NotificationResult:
    channel: str
    success: bool
    detail: str = ""


class NotificationService:
    """Dispatch notifications to external channels.

    Usage:
        service = NotificationService()
        results = await service.send_multi(
            channels=["slack", "email"],
            message={"title": "Incident Alert", "body": "..."},
        )
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        self.settings = get_settings()
        self._client = client

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send(
        self,
        channel: str,
        message: dict[str, Any],
    ) -> NotificationResult:
        """Send a notification to a single channel."""
        try:
            channel_enum = NotificationChannel(channel.lower())
        except ValueError:
            return NotificationResult(
                channel=channel,
                success=False,
                detail=f"Unknown channel: {channel}",
            )

        if channel_enum == NotificationChannel.SLACK:
            return await self._send_slack(message)
        if channel_enum == NotificationChannel.EMAIL:
            return await self._send_email(message)
        if channel_enum == NotificationChannel.PAGERDUTY:
            return await self._send_pagerduty(message)

        return NotificationResult(channel=channel, success=False, detail="Unreachable")

    async def send_multi(
        self,
        channels: list[str],
        message: dict[str, Any],
    ) -> list[NotificationResult]:
        """Send a notification to multiple channels concurrently."""
        tasks = [self.send(ch, message) for ch in channels]
        return await asyncio.gather(*tasks)

    # ------------------------------------------------------------------
    # Slack
    # ------------------------------------------------------------------

    async def _send_slack(self, message: dict[str, Any]) -> NotificationResult:
        webhook_url = self.settings.slack_webhook_url
        if not webhook_url:
            logger.warning("Slack webhook URL not configured; skipping notification")
            return NotificationResult(
                channel="slack",
                success=False,
                detail="Slack webhook URL not configured",
            )

        payload = {
            "text": message.get("title", "PLAYBOOK Alert"),
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": message.get("title", "PLAYBOOK Alert"),
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message.get("body", "")},
                },
            ],
        }

        try:
            resp = await self.client.post(webhook_url, json=payload)
            resp.raise_for_status()
            return NotificationResult(
                channel="slack",
                success=True,
                detail=f"Slack responded {resp.status_code}",
            )
        except httpx.HTTPStatusError as exc:
            logger.warning("Slack notification failed: %s", exc)
            return NotificationResult(
                channel="slack",
                success=False,
                detail=f"HTTP {exc.response.status_code}",
            )
        except Exception as exc:
            logger.warning("Slack notification failed: %s", exc)
            return NotificationResult(channel="slack", success=False, detail=str(exc))

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    async def _send_email(self, message: dict[str, Any]) -> NotificationResult:
        host = self.settings.smtp_host
        port = self.settings.smtp_port
        user = self.settings.smtp_user
        password = self.settings.smtp_password
        from_addr = self.settings.smtp_from
        to_addrs = message.get("to", self.settings.notification_default_recipients)

        if not host or not from_addr or not to_addrs:
            logger.warning("SMTP not fully configured; skipping email notification")
            return NotificationResult(
                channel="email",
                success=False,
                detail="SMTP configuration incomplete",
            )

        subject = message.get("title", "PLAYBOOK Alert")
        body_text = message.get("body", "")
        body_html = message.get("html_body", "")

        # Build multipart message (HTML + plain text fallback)
        if body_html:
            mime = MIMEMultipart("alternative")
            mime.attach(MIMEText(body_text, "plain", "utf-8"))
            mime.attach(MIMEText(body_html, "html", "utf-8"))
        else:
            mime = MIMEText(body_text, "plain", "utf-8")

        mime["Subject"] = subject
        mime["From"] = from_addr
        mime["To"] = ", ".join(to_addrs) if isinstance(to_addrs, list) else to_addrs

        def _send_sync() -> None:
            import smtplib

            with smtplib.SMTP(host, port) as server:
                if user and password:
                    server.starttls()
                    server.login(user, password)
                server.send_message(mime)

        try:
            await asyncio.to_thread(_send_sync)
            return NotificationResult(channel="email", success=True, detail="Sent")
        except Exception as exc:
            logger.warning("Email notification failed: %s", exc)
            return NotificationResult(channel="email", success=False, detail=str(exc))

    # ------------------------------------------------------------------
    # PagerDuty
    # ------------------------------------------------------------------

    async def _send_pagerduty(self, message: dict[str, Any]) -> NotificationResult:
        routing_key = self.settings.pagerduty_routing_key
        if not routing_key:
            logger.warning("PagerDuty routing key not configured; skipping notification")
            return NotificationResult(
                channel="pagerduty",
                success=False,
                detail="PagerDuty routing key not configured",
            )

        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "dedup_key": message.get("incident_id", "playbook-alert"),
            "payload": {
                "summary": message.get("title", "PLAYBOOK Alert"),
                "severity": self._map_severity(message.get("severity", "warning")),
                "source": "PLAYBOOK",
                "custom_details": {
                    "body": message.get("body", ""),
                    **message.get("extra", {}),
                },
            },
        }

        try:
            resp = await self.client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            return NotificationResult(
                channel="pagerduty",
                success=True,
                detail=f"Event key: {data.get('dedup_key', 'unknown')}",
            )
        except httpx.HTTPStatusError as exc:
            logger.warning("PagerDuty notification failed: %s", exc)
            return NotificationResult(
                channel="pagerduty",
                success=False,
                detail=f"HTTP {exc.response.status_code}",
            )
        except Exception as exc:
            logger.warning("PagerDuty notification failed: %s", exc)
            return NotificationResult(
                channel="pagerduty", success=False, detail=str(exc)
            )

    @staticmethod
    def _map_severity(sev: str) -> str:
        mapping = {
            "critical": "critical",
            "high": "error",
            "medium": "warning",
            "low": "info",
        }
        return mapping.get(sev.lower(), "warning")
