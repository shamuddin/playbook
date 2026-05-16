---
name: backend-check
description: Run backend linting, type checking, and tests for the FastAPI app
---

Run the complete backend quality check suite. Execute in order:

1. `cd backend && ruff check .` - Lint all Python files
2. `cd backend && ruff format --check .` - Check formatting
3. `cd backend && mypy .` - Type check with mypy
4. `cd backend && pytest -x --tb=short` - Run tests, fail fast

If any step fails, report the exact error and suggest fixes. Do not proceed to the next step if the current one fails.
