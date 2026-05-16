---
name: full-check
description: Run all project checks across backend, frontend, and SDK
---

Run the complete project quality check suite across all three modules. Execute in order:

1. **Backend**: `cd backend && ruff check . && mypy . && pytest -x --tb=short`
2. **Frontend**: `cd frontend && npm run lint && npm run typecheck && npm run test -- --run`
3. **SDK**: `cd sdk && ruff check . && pytest -x --tb=short`

Run all three modules even if one fails, then provide a consolidated report of all failures. Do not fix issues unless explicitly asked.
