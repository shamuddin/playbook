"""WebSocket connection manager for real-time incident broadcasting."""

import json
from typing import Dict, List, Optional, Set

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._filters: Dict[WebSocket, dict] = {}
        self._user_ids: Dict[WebSocket, Optional[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        self._filters[websocket] = {}
        self._user_ids[websocket] = user_id

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)
        self._filters.pop(websocket, None)
        self._user_ids.pop(websocket, None)

    def set_filter(self, websocket: WebSocket, filters: dict) -> None:
        self._filters[websocket] = filters

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients matching filters."""
        disconnected = []
        for ws in list(self._connections):
            try:
                # Simple filter check: if filters specify severity, match it
                filters = self._filters.get(ws, {})
                msg_severity = message.get("severity")
                if filters.get("severity") and msg_severity:
                    if msg_severity not in filters["severity"]:
                        continue
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    def get_user_id(self, websocket: WebSocket) -> Optional[str]:
        return self._user_ids.get(websocket)


# Global singleton — imported by routers
ws_manager = ConnectionManager()
