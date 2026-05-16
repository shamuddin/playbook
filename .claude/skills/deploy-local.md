---
name: deploy-local
description: Start the full local development stack
---

Start the full local development environment. Execute in parallel where possible:

**Backend:**
1. `cd backend && python -m app.main` or `uvicorn app.main:app --reload --port 8000`
2. Verify health: `curl http://localhost:8000/api/v1/health`

**Frontend:**
1. `cd frontend && npm run dev`
2. Verify: open `http://localhost:5173`

**Database:**
- SQLite: auto-created on startup
- PostgreSQL: ensure `DATABASE_URL` is set

**WebSocket:**
- Connect to `ws://localhost:8000/ws/incidents?token=<jwt>`

If any service fails to start, check logs and report the error.
