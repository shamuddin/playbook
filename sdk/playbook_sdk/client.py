"""HTTP client for the PLAYBOOK API."""

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger("playbook")


class PlaybookClient:
    """HTTP client for the PLAYBOOK API."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 5.0,
    ):
        self.endpoint = (
            endpoint or os.environ.get("PLAYBOOK_ENDPOINT", "http://localhost:8000")
        ).rstrip("/")
        self.api_key = api_key or os.environ.get("PLAYBOOK_API_KEY", "")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.endpoint,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def judge(
        self,
        agent_id: str,
        action_type: str,
        action_details: dict[str, Any],
        agent_context: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Submit an action to the Judge Layer for evaluation."""
        action_summary = action_details.get("action_summary", str(action_details))
        payload = {
            "action": action_summary,
            "agent_id": agent_id,
            "session_id": agent_context.get("session_id") if agent_context else None,
            "metadata": metadata or {},
        }
        resp = await self.client.post("/api/v1/judge/evaluate", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def report_incident(
        self,
        agent_id: str,
        incident_type: str,
        severity: str,
        description: str,
        details: Optional[dict] = None,
    ) -> dict:
        """Report an incident to PLAYBOOK."""
        payload = {
            "incident_type": incident_type,
            "severity": severity,
            "confidence": details.get("confidence", 0.9) if details else 0.9,
            "category": details.get("category", "unknown") if details else "unknown",
            "event_id": details.get("event_id", "") if details else "",
        }
        resp = await self.client.post("/api/v1/incidents", json=payload)
        resp.raise_for_status()
        return resp.json()["data"]

    async def send_heartbeat(self, agent_id: str, health_score: float = 100.0) -> dict:
        """Send a heartbeat from a monitored agent."""
        payload = {"health_score": health_score}
        resp = await self.client.post(
            f"/api/v1/agents/{agent_id}/heartbeat", json=payload
        )
        resp.raise_for_status()
        return resp.json()["data"]
