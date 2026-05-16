---
name: seed-and-verify
description: Seed database and verify data integrity
---

Seed the database and verify seeded data. Execute:

1. `cd backend && python -m app.seed.all`
2. Query `users` table: ensure at least 1 admin user exists
3. Query `incidents` table: ensure demo incidents exist
4. Query `agents` table: ensure demo agents exist
5. Query `playbooks` table: ensure default playbooks exist
6. Query `detection_rules` table: ensure rules are loaded
7. Query `nist_baselines` table: ensure baselines exist

If any table is empty after seeding, investigate the seed script.
