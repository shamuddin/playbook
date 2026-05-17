"""WebSocket connection manager for real-time incident broadcasting."""

import asyncio
import json
from typing import Dict, List, Optional, Set

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._filters: Dict[WebSocket, dict] = {}
        self._user_ids: Dict[WebSocket, Optional[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> None:
        async with self._lock:
            self._connections.add(websocket)
            self._filters[websocket] = {}
            self._user_ids[websocket] = user_id

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
            self._filters.pop(websocket, None)
            self._user_ids.pop(websocket, None)

    async def set_filter(self, websocket: WebSocket, filters: dict) -> None:
        async with self._lock:
            self._filters[websocket] = filters

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients matching filters."""
        disconnected: List[WebSocket] = []
        async with self._lock:
            connections_snapshot = list(self._connections)
            for ws in connections_snapshot:
                try:
                    # Simple filter check: if filters specify severity, match it
                    filters = self._filters.get(ws, {})
                    msg_severity = message.get("severity")
                    if filters.get("severity") and msg_severity is not None:
                        if msg_severity not in filters["severity"]:
                            continue
                    try:
                        await ws.send_json(message)
                    except Exception as exc:
                        print(f"[ws] Send error: {exc}")
                        disconnected.append(ws)
                except Exception:
                    disconnected.append(ws)

            # Clean up disconnected clients
            for ws in disconnected:
                self._connections.discard(ws)
                self._filters.pop(ws, None)
                self._user_ids.pop(ws, None)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def get_user_id(self, websocket: WebSocket) -> Optional[str]:
        async with self._lock:
            return self._user_ids.get(websocket)


# Global singleton — imported by routers
ws_manager = ConnectionManager()
