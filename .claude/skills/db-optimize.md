---
name: db-optimize
description: Analyze hot queries, validate indexes, and check migration safety
---

Run a database reliability audit on PostgreSQL (or SQLite if PostgreSQL is unavailable). Focus on incident ingestion, forensics aggregation, and migration reversibility.

1. **Hot query analysis**: Identify the 5 most-queried tables (`incidents`, `timeline_events`, `judge_decisions`, `evidence_packages`, `agents`). Check for missing indexes on `created_at`, `incident_type`, `status`, and foreign keys.
2. **N+1 detection**: Review `backend/app/services/forensics.py` and `backend/app/routers/incidents.py` for SQLAlchemy relationship access in loops. Flag any lazy-loading or unbatched queries.
3. **Explain plan**: For each flagged query, run `EXPLAIN ANALYZE` equivalent via SQLAlchemy or raw SQL. Report sequential scans and estimated vs. actual row counts.
4. **Migration safety**: Run `cd backend && alembic current` to verify head, then `alembic downgrade -1` followed by `alembic upgrade +1`. Confirm no data loss and reversible DDL.
5. **Pool sizing**: Review `backend/app/core/config.py` for `database_pool_size` and `database_max_overflow`. Recommend values based on expected concurrency (100 WebSocket connections + detection ingestion).
6. **Write throughput**: If on PostgreSQL, run a 1,000-event insert benchmark via asyncpg. Measure transactions per second and connection wait time.
