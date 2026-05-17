---
name: red-team-test
description: Run adversarial bypass detection tests and measure escape rates
---

Run the red-team adversarial validation suite against the Judge Layer and Detection Engine. Verify coverage against all 16 incident types and report escape rates.

1. **Existing vectors**: Run `cd backend && pytest tests/unit/test_bypass_detection.py -v` and record pass/fail counts.
2. **Determinism**: Run `cd backend && pytest tests/unit/test_determinism.py -v` and confirm 1,000 iterations produce zero variance.
3. **Incident type coverage**: Cross-reference `backend/app/core/constants.py` incident types (AGT-DEL through AGT-POL) with test cases. Report gaps where no adversarial test exists.
4. **Escape rate analysis**: For each of the 4 bypass classes in `bypass_detector.py`, calculate escape rate = (undetected bypasses / total attempts). Target < 2%.
5. **Novel pattern proposal**: If escape rate > 2%, propose 2–3 new bypass variants with reproduction code and expected vs. actual verdicts.
6. **Regression**: Run `cd backend && pytest tests/unit/test_judge_engine.py -v` to ensure defensive changes did not break deterministic ALLOW/DENY/QUARANTINE/ESCALATE behavior.
