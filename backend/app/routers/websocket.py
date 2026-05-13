"""WebSocket endpoint for real-time incident updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/incidents")
async def incidents_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time incident updates.

    Clients receive broadcasts for new incidents and can subscribe with filters.
    """
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "event_type": "connection_established",
            "message": "Connected to PLAYBOOK incident feed",
            "active_connections": ws_manager.active_connections,
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
