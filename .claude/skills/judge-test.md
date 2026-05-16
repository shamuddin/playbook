---
name: judge-test
description: Run all judge engine and bypass detection tests
---

Run the complete judge layer test suite. Execute:

1. `cd backend && pytest tests/unit/test_judge_engine.py -v`
2. `cd backend && pytest tests/unit/test_bypass_detection.py -v`
3. `cd backend && pytest tests/unit/test_determinism.py -v`
4. `cd backend && pytest tests/unit/test_enforcement_accuracy.py -v`

If any test fails, report the exact failure with file and line number. Judge engine must remain deterministic; any non-deterministic behavior is a critical bug.
