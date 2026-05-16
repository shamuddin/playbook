---
name: pipeline-test
description: Run the full DETECT->JUDGE->ENFORCE->FORENSICS pipeline tests
---

Run the full pipeline integration test and verify all stages. Execute:

1. `cd backend && pytest tests/integration/test_full_pipeline.py -v`
2. `cd backend && pytest tests/integration/test_incidents.py -v`
3. `cd backend && pytest tests/integration/test_policy_builder_e2e.py -v`

Verify the pipeline completes all 4 stages:
- DETECT: Event ingestion and anomaly detection
- JUDGE: Deterministic decision rendering
- ENFORCE: Playbook action execution
- FORENSICS: Evidence package generation

If the pipeline fails, identify which stage broke and why.
