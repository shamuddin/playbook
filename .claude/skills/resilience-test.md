---
name: resilience-test
description: Inject failures and verify graceful degradation across dependencies
---

Run failure-injection experiments against PLAYBOOK dependencies (Gemini, PostgreSQL, WebSocket) and verify graceful degradation per NFR-REL-004 and NFR-REL-006.

1. **Steady state**: Confirm all health checks pass (`/health`, `/api/v1/health`) and WebSocket connects successfully before injecting faults.
2. **Gemini blackout**: Block outbound Gemini DNS or drop `GEMINI_API_KEY`. Submit an incident requiring enrichment. Verify the app returns HTTP 200 with a deterministic fallback rationale (not 500).
3. **DB disconnect**: Temporarily pause the PostgreSQL container or rename the SQLite file. Verify the backend health endpoint returns 503 within 3 retries and does not crash.
4. **WebSocket kill**: Kill the WebSocket manager task. Verify incident creation via REST still succeeds and events are queued (not lost) until the manager recovers.
5. **Circuit breaker**: If a circuit breaker exists, trigger it by forcing 5 consecutive Gemini failures. Verify it opens and recovers with exponential backoff.
6. **Rollback**: Restore all services. Confirm steady-state metrics return to baseline within 60 seconds. Report any permanent data corruption or stale connections.
