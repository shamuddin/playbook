---
name: websocket-test
description: Test WebSocket connectivity and real-time incident streaming
---

Test the WebSocket real-time infrastructure. Execute:

1. Start the backend
2. Connect WebSocket client to `ws://localhost:8000/ws/incidents?token=<jwt>`
3. Verify connection handshake succeeds
4. Trigger an incident (via API or seed data)
5. Verify incident appears on WebSocket within 5 seconds
6. Disconnect and reconnect; verify automatic reconnection
7. Connect 5+ concurrent clients; verify all receive broadcasts

Report latency metrics and any connection failures.
