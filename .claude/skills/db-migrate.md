---
name: db-migrate
description: Run Alembic database migrations for the backend
---

Handle database migration tasks. Based on the user's request, run one of:

- **Upgrade**: `cd backend && alembic upgrade head`
- **Downgrade**: `cd backend && alembic downgrade -1`
- **Generate new migration**: `cd backend && alembic revision --autogenerate -m "description"`
- **Show current**: `cd backend && alembic current`
- **Show history**: `cd backend && alembic history`

If generating a new migration, first verify the models in `backend/app/models.py` reflect the intended schema. After generating, read the migration file to verify it looks correct before the user applies it.
