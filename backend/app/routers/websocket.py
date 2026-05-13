from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/incidents")
async def incidents_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time incident updates."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "event_type": "connection_established",
            "message": "Connected to PLAYBOOK incident feed",
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                await websocket.send_json({
                    "event_type": "subscribed",
                    "filters": data.get("filters", {}),
                })
            elif action == "unsubscribe":
                await websocket.send_json({
                    "event_type": "unsubscribed",
                })
            elif action == "pong":
                pass  # Heartbeat acknowledged
            else:
                await websocket.send_json({
                    "event_type": "error",
                    "message": f"Unknown action: {action}",
                })

    except WebSocketDisconnect:
        pass
