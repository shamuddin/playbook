# PLAYBOOK Skills & Agents Catalog

This directory contains custom Claude Code skills and agent role definitions for the PLAYBOOK project.

## Skills (13)

Located in `.claude/skills/`. Invoke with `/skill-name`.

| Skill | Purpose |
|-------|---------|
| `backend-check` | Run ruff, mypy, pytest on backend |
| `frontend-check` | Run eslint, typecheck, vitest on frontend |
| `full-check` | Run all checks across backend + frontend + SDK |
| `db-migrate` | Run Alembic migrations (upgrade/downgrade/generate) |
| `db-seed` | Seed database with demo data |
| `security-scan` | OWASP-style security sweep across codebase |
| `sdk-check` | Run SDK lint and tests |
| `judge-test` | Run judge engine + bypass detection + determinism tests |
| `pipeline-test` | Run full DETECT->JUDGE->ENFORCE->FORENSICS integration tests |
| `compliance-check` | Verify compliance mappings and policy builder integrity |
| `seed-and-verify` | Seed DB and verify all tables are populated |
| `deploy-local` | Start the full local development stack (backend + frontend + DB) |
| `websocket-test` | Test WebSocket connectivity and real-time incident streaming |

## Agents (24)

Located in `.claude/agents/`. Reference these prompts when spawning parallel `Agent` tool calls.

### Core Development
| Agent | Specialty | Key Files |
|-------|-----------|-----------|
| **backend-agent** | FastAPI/SQLAlchemy/Python | `backend/app/` |
| **frontend-agent** | React/TypeScript/Vite/Tailwind | `frontend/src/` |
| **database-agent** | SQLAlchemy 2.0/Alembic/PostgreSQL | `backend/app/models.py`, `backend/app/database.py` |
| **sdk-agent** | Python packaging/SDK design | `sdk/playbook_sdk/` |
| **config-agent** | Pydantic Settings/env management | `backend/app/core/config.py`, `frontend/src/utils/config.ts` |

### Quality & Security
| Agent | Specialty | Key Files |
|-------|-----------|-----------|
| **test-agent** | pytest/vitest automation | `*/tests/` |
| **security-agent** | OWASP/JWT/bypass detection | `backend/app/core/security.py`, `backend/app/judge/` |
| **qa-agent** | End-to-end validation/regression | Full pipeline |
| **ui-ux-agent** | Accessibility/responsive/performance | `frontend/src/pages/`, `frontend/src/components/` |
| **auth-agent** | JWT/RBAC/session management | `backend/app/routers/auth.py`, `backend/app/core/security.py` |

### Pipeline Stages
| Agent | Specialty | Key Files |
|-------|-----------|-----------|
| **detect-engine-agent** | Anomaly detection/log ingestion | `backend/app/services/detect/engine.py` |
| **judge-agent** | Deterministic rule engines/AI safety | `backend/app/judge/` |
| **response-engine-agent** | Playbook execution/orchestration | `backend/app/services/response_engine.py` |
| **forensics-agent** | Evidence/integrity/chain-of-custody | `backend/app/services/forensics.py` |

### Domain Specialists
| Agent | Specialty | Key Files |
|-------|-----------|-----------|
| **incident-agent** | Incident lifecycle/SLA management | `backend/app/routers/incidents.py`, `frontend/src/pages/IncidentsPage.tsx` |
| **policy-builder-agent** | NIST controls/ODPs/policy versioning | `backend/app/routers/policy_builder.py` |
| **compliance-agent** | EU AI Act/NIST/regulatory mapping | `backend/app/routers/compliance.py` |
| **analytics-agent** | Dashboards/KPIs/data visualization | `backend/app/routers/dashboard.py`, `frontend/src/pages/DashboardPage.tsx` |
| **websocket-agent** | Real-time/WebSocket/event streaming | `backend/app/routers/websocket.py`, `frontend/src/hooks/useWebSocket.ts` |
| **playground-agent** | Multi-agent simulation/sandboxing | `backend/app/services/playground/`, `frontend/src/pages/PlaygroundPage.tsx` |
| **gemini-agent** | LLM reasoning overlay/cache | `backend/app/services/gemini_reasoning.py`, `backend/app/routers/gemini.py` |
| **lobstertrap-agent** | DPI/proxy/log ingestion | `backend/app/services/lobstertrap_integration.py` |

### Support
| Agent | Specialty | Key Files |
|-------|-----------|-----------|
| **docs-agent** | Technical writing/documentation | `README.md`, `projectdocs/` |
| **devops-agent** | Docker/deployment/infrastructure | `docker-compose.yml` |

## Usage

### Running a Skill
```
/backend-check
/frontend-check
/full-check
/judge-test
/pipeline-test
/compliance-check
/seed-and-verify
/deploy-local
/websocket-test
```

### Spawning Parallel Agents
When you have a complex task spanning multiple domains, spawn agents in parallel:

```
Agent({
  description: "Backend feature work",
  subagent_type: "general-purpose",
  prompt: "[Read .claude/agents/backend-agent.md, then implement...]"
})
Agent({
  description: "Frontend feature work",
  subagent_type: "general-purpose",
  prompt: "[Read .claude/agents/frontend-agent.md, then implement...]"
})
```

### Parallel Execution Strategy
For maximum throughput on large tasks:
1. **Split by domain**: Backend + Frontend + Tests in parallel
2. **Split by layer**: API + DB + UI + Security in parallel
3. **Split by feature**: Multiple features worked simultaneously
4. **Always include a test-agent** to validate concurrently
5. **Always include a security-agent** for auth/judge changes

### Recommended Agent Combinations

**New Feature Development:**
- backend-agent + frontend-agent + test-agent (parallel)

**Security Hardening:**
- security-agent + auth-agent + judge-agent + bypass-test (parallel)

**Database Changes:**
- database-agent + backend-agent + test-agent (sequential: DB first)

**Full Pipeline Validation:**
- detect-engine-agent + judge-agent + response-engine-agent + forensics-agent + pipeline-test (parallel)

**Compliance Audit:**
- compliance-agent + policy-builder-agent + forensics-agent + compliance-check (parallel)

**Release Prep:**
- full-check + security-scan + compliance-check + test-agent (parallel)
