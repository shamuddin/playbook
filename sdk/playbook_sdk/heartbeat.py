"""Background heartbeat sender for agent health monitoring."""

import asyncio
import logging
from typing import Optional

from .client import PlaybookClient

logger = logging.getLogger("playbook.heartbeat")


class HeartbeatSender:
    """Background heartbeat sender for agent health monitoring."""

    def __init__(
        self,
        agent_id: str,
        interval: float = 60.0,  # seconds
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.agent_id = agent_id
        self.interval = interval
        self.client = PlaybookClient(endpoint=endpoint, api_key=api_key)
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def _loop(self) -> None:
        while self._running:
            try:
                await self.client.send_heartbeat(self.agent_id)
                logger.debug("Heartbeat sent for %s", self.agent_id)
            except Exception as e:
                logger.warning("Heartbeat failed: %s", e)
            await asyncio.sleep(self.interval)

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())
            logger.info(
                "Heartbeat started for %s (every %ss)", self.agent_id, self.interval
            )

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            logger.info("Heartbeat stopped for %s", self.agent_id)

    async def close(self) -> None:
        self.stop()
        await self.client.close()
