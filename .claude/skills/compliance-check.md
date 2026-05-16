---
name: compliance-check
description: Verify compliance mappings and policy builder integrity
---

Run compliance and policy validation. Execute:

1. `cd backend && pytest tests/unit/test_policy_builder.py -v`
2. Verify `resolved_policies` SQL view exists and returns correct data
3. Check `backend/app/routers/compliance.py` for EU AI Act, NIST, SOC2, HIPAA mappings
4. Verify all `judge_decisions` are linked to `compliance_mappings`
5. Ensure `evidence_packages` have integrity hashes
6. Check audit log (`audit_log` table) is populated and immutable

Report any gaps in compliance coverage.
