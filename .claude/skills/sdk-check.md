---
name: sdk-check
description: Run SDK tests and linting for playbook-guard
---

Run the SDK quality check suite. Execute in order:

1. `cd sdk && ruff check .` - Lint SDK Python files
2. `cd sdk && ruff format --check .` - Check formatting
3. `cd sdk && pytest -x --tb=short` - Run SDK tests

If any step fails, report the exact error and suggest fixes. Check `sdk/pyproject.toml` for build/packaging issues.
