"""WebSocket endpoint for real-time incident updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import get_current_user_ws
from app.database import AsyncSessionLocal
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/incidents")
async def incidents_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time incident updates.

    Clients receive broadcasts for new incidents and can subscribe with filters.
    Authentication via query parameter: ?token=<jwt>
    """
    async with AsyncSessionLocal() as db:
        current_user = await get_current_user_ws(websocket, db)
        if not current_user:
            await websocket.close(code=4001, reason="Authentication required")
            return

    await ws_manager.connect(websocket, user_id=current_user.id)
    try:
        await websocket.send_json({
            "event_type": "connection_established",
            "message": "Connected to PLAYBOOK incident feed",
            "active_connections": ws_manager.active_connections,
            "user_id": current_user.id,
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                filters = data.get("filters", {})
                ws_manager.set_filter(websocket, filters)
                await websocket.send_json({
                    "event_type": "subscribed",
                    "filters": filters,
                })
            elif action == "unsubscribe":
                ws_manager.set_filter(websocket, {})
                await websocket.send_json({
                    "event_type": "unsubscribed",
                })
            elif action == "ping":
                await websocket.send_json({"event_type": "pong"})
            else:
                await websocket.send_json({
                    "event_type": "error",
                    "message": f"Unknown action: {action}",
                })

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
