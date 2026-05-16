---
name: frontend-check
description: Run frontend linting, type checking, and tests for the React app
---

Run the complete frontend quality check suite. Execute in order:

1. `cd frontend && npm run lint` - ESLint check
2. `cd frontend && npm run typecheck` - TypeScript type checking
3. `cd frontend && npm run test -- --run` - Run vitest tests once

If any step fails, report the exact error and suggest fixes. Do not proceed to the next step if the current one fails.
