---
name: db-seed
description: Seed the database with demo data and scenarios
---

Seed the database with demo data. Execute:

- `cd backend && python -m app.seed.all`

If the seed script fails, check:
1. Database is initialized and accessible
2. `backend/app/database.py` has a working engine
3. Tables are created (run `backend/app/main.py` lifespan or Alembic first)

After seeding, verify by querying key tables: users, incidents, agents, playbooks.
