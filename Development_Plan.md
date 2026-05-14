# PLAYBOOK Development Plan

> **Version:** 1.1  
> **Date:** 2026-05-12  
> **Scope:** Full implementation of the PLAYBOOK automated incident response system from documentation-only to deployable MVP  
> **Estimated Effort:** 9 phases (~2–3 weeks of focused development, or 128 engineering hours in hackathon compression)  
> **Authority:** Aligned with `AGENTS.md` v1.2 and the 2026 specification documents (`PLAYBOOK_Functional_Requirements.md`, `PLAYBOOK_AI_Agent_Documentation.md`, `PLAYBOOK_EU_AI_Act_NIST_Compliance_Mapping.md`, `CUSTOM_POLICY_BUILDER_Design.md`)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Development Philosophy & Constraints](#2-development-philosophy--constraints)
3. [Phase Overview](#3-phase-overview)
4. [Phase 0: Foundation & Scaffolding](#phase-0-foundation--scaffolding)
5. [Phase 1: Core Pipeline — DETECT](#phase-1-core-pipeline--detect)
6. [Phase 2: Core Pipeline — CLASSIFY + JUDGE](#phase-2-core-pipeline--classify--judge)
7. [Phase 3: Response Engine & Playbooks](#phase-3-response-engine--playbooks)
8. [Phase 4: Forensics & Evidence](#phase-4-forensics--evidence)
9. [Phase 5: Dashboard & Frontend](#phase-5-dashboard--frontend)
10. [Phase 6: DEMO_MODE & Demo Scenarios](#phase-6-demo_mode--demo-scenarios)
11. [Phase 7: Integration & External APIs](#phase-7-integration--external-apis)
12. [Phase 8: Policy Builder & ODP System](#phase-8-policy-builder--odp-system)
13. [Phase 9: Testing, Validation & Deployment](#phase-9-testing-validation--deployment)
14. [Risk Register](#risk-register)
15. [Appendix A: File Budget](#appendix-a-file-budget)
16. [Appendix B: Decision Log](#appendix-b-decision-log)

---

## 1. Executive Summary

PLAYBOOK is an automated incident response system for AI agent deployments. Its core architectural bet is the **Judge Layer pattern**: a deterministic, rule-based enforcement layer that intercepts every proposed agent action before execution and renders an irreversible decision — ALLOW, DENY, QUARANTINE, or ESCALATE.

This plan takes the project from its current documentation-only state to a deployable MVP with:
- A working 4-stage pipeline (DETECT → CLASSIFY/JUDGE → ENFORCE → FORENSICS)
- A deterministic Judge Layer with ODP Resolution Engine, immune to 4 known LLM-judge bypass patterns
- A **Custom Policy Builder** implementing NIST SP 800-53 Organization-Defined Parameters (ODPs)
- A React-based real-time incident dashboard with Policy Builder UI
- 6 pre-built demo scenarios (20 synthetic incidents) for hackathon presentation
- Railway deployment with zero-external-dependency DEMO_MODE
- 55/55 bypass detection test vectors

---

## 2. Development Philosophy & Constraints

### Non-Negotiable Architectural Rules

| # | Rule | Violation Consequence |
|---|------|----------------------|
| R1 | **Zero LLM API calls in `judge/` or `classify/` enforcement path** | P0 defect — immediate rollback |
| R2 | **Judge Layer must fail-closed** (block all actions on crash) | P0 defect |
| R3 | **Deterministic enforcement: identical input = identical decision** | P0 defect |
| R4 | **Every pipeline stage writes to SQLite** (durability + audit trail) | P1 defect |
| R5 | **DEMO_MODE must run without network access** | P1 defect |
| R6 | **All `/api/*` except `/health` require JWT Bearer tokens** | P1 defect |
| R7 | **Bypass detection: 55/55 test vectors must pass** | Blocks release |
| R8 | **End-to-end latency ≤ 200ms (p95), hard ceiling 500ms** | Blocks release |

### Resource Constraints

| Resource | Limit | Impact |
|----------|-------|--------|
| Python files | ≤ 50 | Strict modularization required |
| React components | ≤ 40 | Reusable component design |
| Railway RAM | 512 MB | FastAPI ≤ 256MB, React ≤ 64MB, SQLite ≤ 128MB |
| Railway disk | 1 GB | SQLite ≤ 500MB, logs ≤ 70MB, auto-purge at 480MB |
| Railway CPU | 1 shared vCPU | Single-threaded async optimization |
| Railway sleep | 30 min idle | UptimeRobot ping every 5 min required |
| Engineering hours | 128 (8 days × 16 hrs) | `TODO(hackathon)` markers for deferred work |

### Document Authority Hierarchy

When specifications conflict, precedence is:
1. `AGENTS.md` v1.2 (this file's master context)
2. `PLAYBOOK_AI_Agent_Documentation.md` (2026-06-15)
3. `PLAYBOOK_Functional_Requirements.md` (2026-05-15)
4. `PLAYBOOK_EU_AI_Act_NIST_Compliance_Mapping.md` (2026-05-11)
5. `PLAYBOOK_API_Documentation.md` (2026)
6. `PLAYBOOK_Non_Functional_Requirements.md` (2026)
7. `PLAYBOOK_Deployment_Guide.md` (2025-01-15 — being updated)
8. `PLAYBOOK_Technical_Specification.md` (2025-01-15 — being updated)

---

## 3. Phase Overview

| Phase | Name | Duration | Key Deliverable | Validation Gate |
|-------|------|----------|-----------------|-----------------|
| **0** | Foundation & Scaffolding | 1–2 days | Repo structure, 20-table DB schema, CI/CD, `.env`, Docker | `alembic upgrade head` succeeds |
| **1** | DETECT — Log Ingestion & Anomaly Detection | 1–2 days | Log tailer, parser, anomaly scoring | 10,000 EPS burst, <10ms detection |
| **2** | CLASSIFY + JUDGE — Deterministic Enforcement | 2–3 days | Judge Layer, 16-type taxonomy, ODP resolver, ALLOW/DENY/QUARANTINE/ESCALATE | Target: <40ms core, <50ms p95, 1000× determinism = 0 variance |
| **3** | RESPOND — Playbook Engine | 1–2 days | YAML playbook loader, action executor, Lobster Trap CLI wrapper | Playbook resolve <50ms, action audit |
| **4** | FORENSICS — Timeline & Evidence | 1–2 days | Timeline builder, evidence packages, SHA-256 signing | Package integrity verifiable |
| **5** | Dashboard & Frontend | 2–3 days | React dashboard, WebSocket real-time feed, incident views | Lighthouse ≥ 70, WebSocket <500ms propagation |
| **6** | DEMO_MODE & Demo Scenarios | 1 day | 6 pre-seeded scenarios (20 incidents), offline operation, demo script alignment | Runs without network, 6 scenarios visible |
| **7** | Integration — Gemini, SupraWall, Compliance | 1–2 days | Gemini cache overlay, SupraWall webhook, EU AI Act export | Cache hit ≥ 89%, async only |
| **8** | Policy Builder & ODP System | 2–3 days | NIST baselines, ODP editor, conflict detection, 6 industry templates | 12 baselines, 6 templates, conflict detection <500ms |
| **9** | Testing, Validation & Deployment | 2–3 days | 55/55 bypass tests, Policy Builder tests, V-001–V-057 checklist, Railway deploy | All gates pass |

**Critical Path:** Phase 0 → 1 → 2 → 3 → 4 → 5 → 9  
**Parallel Tracks:** Phase 6 (DEMO_MODE) can overlap with Phases 3–5. Phase 7 (Integrations) runs parallel to Phases 4–5. Phase 8 (Policy Builder) can overlap with Phases 5–7.

---

## Phase 0: Foundation & Scaffolding

**Goal:** Establish repository structure, tooling, CI/CD, and configuration management. No business logic yet.

### 0.1 Repository Structure

Create the scaffold:

```
playbook/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI factory
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models.py            # 20 ORM tables + 1 view
│   │   ├── schemas.py           # Pydantic request/response
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Pydantic Settings
│   │   │   ├── logging.py       # Structured JSON logging
│   │   │   ├── security.py      # JWT, password hashing
│   │   │   └── constants.py     # Enums, limits, defaults
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py        # GET /api/v1/health
│   │   │   ├── incidents.py     # CRUD + list + filter
│   │   │   ├── judge.py         # /judge/evaluate, /judge/decisions
│   │   │   ├── playbooks.py     # List, get definition
│   │   │   ├── policy_builder.py # 14 Policy Builder endpoints
│   │   │   ├── forensics.py     # Export packages
│   │   │   ├── demo.py          # Seed/reset (DEMO_MODE only)
│   │   │   ├── compliance.py    # Mapping, report export
│   │   │   └── websocket.py     # WS endpoint registration
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── log_tailer.py    # File watcher (watchdog)
│   │   │   ├── anomaly_detection.py
│   │   │   ├── classification.py
│   │   │   ├── judge_agent.py   # Deterministic enforcement
│   │   │   ├── response_engine.py
│   │   │   ├── forensics.py     # Package builder
│   │   │   ├── policy_builder.py # NIST baselines + ODP CRUD
│   │   │   └── gemini_cache.py  # Cache read/write
│   │   ├── judge/               # ISOLATED — zero LLM calls
│   │   │   ├── __init__.py
│   │   │   ├── engine.py        # Core rule evaluator
│   │   │   ├── rules.py         # Rule definitions
│   │   │   ├── bypass_detector.py
│   │   │   └── decision.py      # ALLOW/DENY/QUARANTINE/ESCALATE
│   │   └── policy/              # Policy Builder — NIST ODPs
│   │       ├── __init__.py
│   │       ├── baseline_loader.py
│   │       ├── odp_resolver.py
│   │       └── conflict_detector.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   └── integration/
│   ├── policies/                # YAML playbook definitions
│   ├── scripts/
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── Dockerfile
│   └── Procfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.template
├── .env.example
├── .gitignore
├── railway.json
├── README.md
└── AGENTS.md
```

### 0.2 Tooling & Configuration

- [ ] `requirements.txt` with pinned versions (FastAPI 0.109+, SQLAlchemy 2.0+, etc.)
- [ ] `package.json` with React 18.2+, Vite 5.0+, Tailwind 3.4+, Recharts 2.10+
- [ ] `pytest.ini` with `asyncio_mode=auto`, coverage fail-under=60, markers
- [ ] `ruff` configuration in `pyproject.toml`
- [ ] `mypy` configuration
- [ ] GitHub Actions CI: lint → test → build Docker image
- [ ] `.env.template` with all required + optional variables (see AGENTS.md v1.2)
- [ ] `.gitignore` for Python, Node, Docker, SQLite, evidence, logs

### 0.3 Database Schema (Alembic Migration #1)

Implement all **20 tables + 1 view** from `PLAYBOOK_Database_Schema.md` (v1.2):

**Core Pipeline (11 tables):**
1. `incidents` — primary tracking (16 types, 5 statuses, 4 severities)
2. `agents` — monitored AI agents with health scores
3. `playbooks` — incident response definitions
4. `playbook_actions` — ordered actions within playbooks
5. `evidence_packages` — tamper-evident forensic archives
6. `audit_log` — append-only tamper-evident trail
7. `gemini_cache` — cached API responses
8. `agent_health_history` — time-series health metrics
9. `detection_rules` — heuristic anomaly rules
10. `demo_scenarios` — pre-built demo/training data
11. `compliance_mappings` — EU AI Act / NIST mappings

**Judge Layer (4 tables):**
12. `judge_decisions` — immutable deterministic verdicts
13. `bypass_patterns` — known bypass pattern definitions
14. `bypass_attempts` — log of detected bypasses
15. `suprawall_events` — external SupraWall correlation

**Policy Builder (5 tables + 1 view):**
16. `nist_baselines` — immutable NIST baseline policies
17. `organization_odps` — Organization-Defined Parameters
18. `policy_versions` — ODP change history (append-only)
19. `industry_templates` — pre-configured ODP sets
20. `odp_conflicts` — ODP-NIST conflict detection
21. `resolved_policies` (VIEW) — effective policy overlay per incident type

**Validation:** `alembic upgrade head` succeeds; all tables created with correct indexes.

### 0.4 FastAPI Skeleton

- [ ] `main.py` with lifespan events, CORS, exception handlers
- [ ] `database.py` with SQLAlchemy async engine, session dependency
- [ ] `core/config.py` with Pydantic Settings parsing all env vars
- [ ] `core/logging.py` with JSON structured logs, `incident_id` correlation
- [ ] `core/security.py` with JWT creation/validation (HS256, 24h expiry)
- [ ] `core/constants.py` with enums, limits, defaults
- [ ] `routers/health.py` returning `{ status, timestamp, version, components }`
- [ ] `routers/policy_builder.py` — 14 Policy Builder endpoints scaffold

**Validation:** `uvicorn app.main:app` starts; `GET /api/v1/health` returns 200.

---

## Phase 1: Core Pipeline — DETECT

**Goal:** Ingest Lobster Trap logs, normalize to PB-CES, detect anomalies, create incident candidates.

### 1.1 Log Tailer Service (`services/log_tailer.py`)

- [ ] `watchdog` observer on `LOBSTERTRAP_LOG_DIR` (`/var/log/lobstertrap/*.log`)
- [ ] Handle `IN_MODIFY`, `IN_MOVED_TO`, `IN_CREATE`
- [ ] Parse JSON Lines format; extract 23 metadata fields
- [ ] Normalize to **PB-CES** (Playbook Common Event Schema)
- [ ] Push to async queue (`asyncio.Queue`)
- [ ] Circuit breaker: 3 ingestion failures → exponential backoff

**Key metadata fields to extract:**
- `session_id`, `timestamp`, `agent_id`, `tool_name`, `tool_parameters`
- `intent_category`, `risk_score` (0–100)
- `contains_injection_patterns`, `contains_pii`, `contains_credentials`
- `contains_exfiltration`, `contains_system_commands`
- `prompt_length`, `response_length`, `latency_ms`

### 1.2 Anomaly Detection Engine (`services/anomaly_detection.py`)

- [ ] Static signature rules: 16 incident type matchers
- [ ] Dynamic behavioral baseline: per-session 7-day rolling average; trigger on > 3σ deviation
- [ ] Composite scoring: weighted sum → `anomaly_score` (0.0–100.0)
- [ ] Threshold: `ANOMALY_THRESHOLD` (default 25.0)
- [ ] Output: `IncidentCandidate` with `event_id`, `score`, `triggered_rules[]`, `severity`

**16 Incident Type Taxonomy (canonical):**

| ID | Type | Default Severity | Playbook |
|----|------|-----------------|----------|
| AGT-DEL-001 | Data Destruction | CRITICAL | PBP-001 |
| AGT-FIN-002 | Unauthorized Financial | CRITICAL | PBP-002 |
| AGT-PER-003 | Permission Escalation | HIGH | PBP-003 |
| AGT-HRM-004 | Harmful Output | HIGH | PBP-004 |
| AGT-EXT-005 | Data Exfiltration | CRITICAL | PBP-005 |
| AGT-INJ-006 | Prompt Injection | HIGH | PBP-006 |
| AGT-HAL-007 | Hallucination Cascade | MEDIUM | PBP-007 |
| AGT-CRE-008 | Credential Exposure | HIGH | PBP-008 |
| AGT-RAT-009 | Rate Limit Abuse | MEDIUM | PBP-009 |
| AGT-DRF-010 | Model Drift | MEDIUM | PBP-010 |
| AGT-TLM-011 | Tool Misuse | MEDIUM | PBP-011 |
| AGT-GAP-012 | Coverage Gap | LOW | PBP-012 |
| AGT-SPY-013 | Systematic Espionage | HIGH | PBP-013 |
| AGT-BYP-014 | Guardrail Bypass | CRITICAL | PBP-014 |
| AGT-PRV-015 | Privacy Violation | HIGH | PBP-015 |
| AGT-REG-016 | Regulatory Trigger | HIGH | PBP-016 |

> **Schema Gap:** `PLAYBOOK_Database_Schema.md` (v1.2) currently implements **12 type codes** (AGT-DEL-001 through AGT-GAP-012). The 4 additional types (AGT-SPY-013, AGT-BYP-014, AGT-PRV-015, AGT-REG-016) must be added during Phase 0 migration #2.

### 1.3 Database Write Path

- [ ] Every `RawEvent` → `raw_events` table
- [ ] Every `AnomalyScore` → `anomaly_scores` table
- [ ] If `is_anomaly=true`, create `incident` record with status `detected`
- [ ] Write `timeline_event` for each stage transition

**Validation:**
- Inject 10,000 synthetic log lines → all processed, no loss
- Burst test: 10,000 EPS for 5 seconds → queue doesn't overflow
- Detection latency: p95 ≤ 10ms

---

## Phase 2: Core Pipeline — CLASSIFY + JUDGE

**Goal:** Build the deterministic Judge Layer — the architectural heart of PLAYBOOK. This is the highest-risk, highest-priority phase.

### 2.1 Classification Engine (`services/classification.py`)

- [ ] Local rule-based classifier (zero LLM dependency)
- [ ] Input: `IncidentCandidate` + 23 metadata fields
- [ ] Output: `ClassifiedIncident` with:
  - `incident_type` (one of 16)
  - `severity` (LOW/MEDIUM/HIGH/CRITICAL)
  - `confidence` (0.0–1.0)
  - `regulatory_tags` (EU AI Act Art. 9/15/73, HIPAA, NIST controls)
  - `playbook_id` (auto-assigned based on type)
  - `local_rule_id` (which rule triggered)
- [ ] If confidence < 0.70, flag for human review
- [ ] Results immutable and versioned

### 2.2 Judge Layer (`judge/` module)

**This module MUST contain zero LLM API calls. Any violation is a P0 defect.**

#### 2.2.1 Rule Engine (`judge/engine.py`)

- [ ] 23-field heuristic evaluator
- [ ] **ODP Resolution Engine** — before rendering verdict, merge NIST baselines with organizational ODPs:
  - Load NIST baseline for incident type
  - Load organizational ODPs (8 keys per type)
  - Detect conflicts (WARNING for deviations, BLOCKED for missing required fields)
  - Resolve merged policy
- [ ] Severity scoring matrix (1–10) with modifiers:
  - Repeat offender: +2
  - Business hours: −1
  - Dual-auth present: −2
  - No auth: +3
- [ ] Decision matrix:

| Severity | Auth | Decision |
|----------|------|----------|
| 1–3 | Any | ALLOW |
| 4–6 | Valid | ALLOW with logging |
| 4–6 | Missing | QUARANTINE |
| 7–8 | Any | QUARANTINE or ESCALATE |
| 9–10 | Any | DENY or ESCALATE |

#### 2.2.2 Bypass Detector (`judge/bypass_detector.py`)

Immune to 4 known patterns by design:

| Pattern | Also Known As | Defense Mechanism |
|---------|---------------|-------------------|
| **Context Window Displacement** | RoleSwap | Judge operates on structured metadata (booleans, ints, enums), not natural language content. Prompt length is a signal, not parsed content. |
| **Indirect Tool Chaining** | Separator | Composite pattern detection: if `tool_a` → `tool_b` → `tool_c` within session window matches known chain signatures → DENY. |
| **Unicode Homoglyph Substitution** | Base64 / Encoding | NFKC normalization + TR39 confusables check on all string fields before rule matching. |
| **Confidence Hijacking** | SocialEngineering | Binary enforcement for known patterns; confidence score is advisory only — the rule engine makes the decision. |

- [ ] 55 test vectors covering all 4 patterns
- [ ] 100% detection rate required (0 false negatives on known patterns)

#### 2.2.3 Decision Renderer (`judge/decision.py`)

- [ ] Returns one of: `ALLOW`, `DENY`, `QUARANTINE`, `ESCALATE`
- [ ] Every decision logged to `judge_decisions` table with:
  - `decision_id`, `incident_id`, `timestamp`
  - `verdict`, `severity_score`, `confidence`
  - `matched_rules[]`, `bypass_patterns_detected[]`
  - `rationale` (human-readable rule trace)
  - `latency_ms`
- [ ] **Fails-closed:** on any exception → `ESCALATE`

### 2.3 API Endpoints

- [ ] `POST /api/v1/judge/evaluate` — evaluate a proposed action
- [ ] `GET /api/v1/judge/decisions/{agent_id}` — decision history
- [ ] `GET /api/v1/judge/stats` — aggregate metrics
- [ ] `GET /api/v1/judge/bypass-attempts` — detected bypass log
- [ ] `GET /api/v1/judge/bypass-patterns` — pattern definitions

### 2.4 Classification Overlay (Gemini Cache)

- [ ] `services/gemini_cache.py` — read-only cache lookup
- [ ] Cache key: SHA-256 of normalized metadata + judge verdict
- [ ] Cache hit → enrich narrative only; **never override decision**
- [ ] Cache miss → fall back to local classification (no API call in enforcement path)

**Validation:**
- 1,000 repeated classifications of identical prompt → 0 variance (V-013)
- 55 bypass test vectors → 55/55 pass (V-019)
- Judge latency: p95 ≤ 50ms, p99 ≤ 100ms (V-010)
- Code audit of `judge/` and `classify/` → zero LLM API calls (V-012)
- Disconnect Gemini → 100% enforcement continues, zero latency impact (V-018, V-029)

---

## Phase 3: Response Engine & Playbooks

**Goal:** Execute automated responses based on Judge decisions and NIST IR 8346 playbooks.

### 3.1 Playbook Library (`policies/`)

Create 16 YAML playbooks (one per incident type):

```yaml
# policies/PBP-001-data-destruction.yaml
playbook_id: PBP-001
name: Data Destruction Response
version: "1.0"
incident_type: AGT-DEL-001
triggers:
  severity: [CRITICAL, HIGH]
actions:
  - step: 1
    name: Immediate Deny
    action: DENY
    target: agent_tool_execution
    timeout_seconds: 5
  - step: 2
    name: Quarantine Agent
    action: QUARANTINE
    target: agent_session
    timeout_seconds: 10
  - step: 3
    name: Alert Security Team
    action: NOTIFY
    target: security_team
    channel: webhook
    timeout_seconds: 30
  - step: 4
    name: Capture Forensics
    action: FORENSICS
    target: incident_record
    timeout_seconds: 60
escalation:
  if_step_fails: [1, 2]
  action: PAGE_ONCALL
sla:
  response_time_seconds: 30
  resolution_time_minutes: 60
```

**Actions available:** `DENY`, `QUARANTINE`, `RATE_LIMIT`, `HUMAN_REVIEW`, `NOTIFY`, `FORENSICS`, `ISOLATE`, `LOG_EXTENDED`

### 3.2 Playbook Engine (`services/response_engine.py`)

- [ ] YAML loader with validation (checksum on load)
- [ ] Playbook resolver: incident type → active playbook < 50ms
- [ ] Action executor with timeout handling
- [ ] Step-level logging: `cli_stdout`, `cli_stderr`, `returncode`
- [ ] Individual action failures logged; execution continues (fail-open for safety)
- [ ] Integration with Lobster Trap CLI: `lobstertrap test`, `lobstertrap serve --reload`

### 3.3 Lobster Trap CLI Wrapper

- [ ] `asyncio.create_subprocess_exec` wrapper
- [ ] Commands: `--version`, `test --policy-file`, `serve --policy-file --reload`, `status`
- [ ] CLI timeout: 10s for test, 30s for serve
- [ ] Circuit breaker: 5 failures → open, 60s recovery

### 3.4 Human Review Queue

- [ ] `GET /api/v1/review-queue` — list pending tasks
- [ ] `POST /api/v1/review/{task_id}/approve` — with optional override action
- [ ] `POST /api/v1/review/{task_id}/reject` — revert to block
- [ ] `POST /api/v1/review/{task_id}/escalate` — page on-call
- [ ] SLA deadline tracking per task

**Validation:**
- Playbook resolution < 50ms
- DENY blocks tool call before destination
- Action results recorded in timeline within 100ms
- All 16 playbooks load and validate

---

## Phase 4: Forensics & Evidence

**Goal:** Build tamper-evident forensic timelines and evidence packages.

### 4.1 Timeline Builder (`services/forensics.py`)

- [ ] Reconstruct chronology from 5 minutes pre-trigger through resolution
- [ ] Millisecond-precision ordering
- [ ] Correlation IDs linking related events
- [ ] Events from all sources: Lobster Trap, Judge Layer, response actions, SupraWall
- [ ] Immutable after sealing (cryptographic signature)

### 4.2 Evidence Package Generation

- [ ] Assemble 5 artifact categories:
  1. **Logs** — raw events, parsed events, audit trail
  2. **Context** — agent state, session history, metadata
  3. **Classification** — incident type, severity, confidence, regulatory tags
  4. **Response** — playbook executed, actions taken, outcomes
  5. **Compliance** — EU AI Act mapping, NIST control alignment
- [ ] SHA-256 manifest of all files
- [ ] Digital signature with `SECRET_KEY`
- [ ] Export formats: JSON (machine), ZIP (combined), PDF (human-readable), STIX 2.1 (threat intel)

### 4.3 API Endpoints

- [ ] `GET /api/v1/forensics/{incident_id}` — JSON package
- [ ] `GET /api/v1/forensics/{incident_id}/export` — ZIP download
- [ ] `GET /api/v1/incidents/{id}/timeline` — timeline events

**Validation:**
- Package integrity verifiable independently
- Timeline includes all events from 5 min pre-trigger
- PDF export human-readable
- Evidence retention: 2,555 days (7 years)

---

## Phase 5: Dashboard & Frontend

**Goal:** Real-time React dashboard for incident visibility, agent health, and compliance overview.

### 5.1 Pages & Components

| Page | Route | Key Components |
|------|-------|----------------|
| **Incident Feed** | `/incidents` | Real-time table, severity badges, filters |
| **Incident Detail** | `/incidents/:id` | Timeline, metadata, judge rationale, actions |
| **Judge Panel** | `/judge` | Decision distribution, latency graph, bypass log |
| **Agent Health** | `/agents` | Health score (0–100), trend graph, fleet ranking |
| **Compliance** | `/compliance` | Mapping matrix, gap analysis, export buttons |
| **Human Review** | `/review` | Queue table, approve/reject/escalate buttons |
| **Settings** | `/settings` | Config view, demo toggle, purge controls |

### 5.2 Real-Time Features

- [ ] WebSocket connection to `ws://localhost:8000/api/v1/ws/incidents`
- [ ] Server events: `INCIDENT_CREATED`, `INCIDENT_CLASSIFIED`, `INCIDENT_RESPONDED`, `HUMAN_REVIEW_REQUIRED`
- [ ] Client filters: severity, type, agent_id, status
- [ ] Auto-reconnect with exponential backoff
- [ ] New incident toast notification (< 2 seconds)

### 5.3 Data Visualization

- [ ] Severity distribution pie/bar chart (Recharts)
- [ ] Incident trend line chart (7/30/90 days)
- [ ] Agent health score trend
- [ ] Judge latency histogram
- [ ] Compliance coverage heatmap

### 5.4 Styling & UX

- [ ] Tailwind CSS with custom color tokens:
  - CRITICAL: `red-600`
  - HIGH: `orange-500`
  - MEDIUM: `yellow-400`
  - LOW: `blue-400`
  - ALLOW: `green-500`
  - DENY: `red-600`
  - QUARANTINE: `orange-500`
  - ESCALATE: `purple-500`
- [ ] Responsive: usable at 375px width (mobile)
- [ ] Loading states, error boundaries, empty states
- [ ] Dark mode support (optional, post-MVP)

**Validation:**
- Lighthouse score ≥ 70
- First load ≤ 3s (uncached), repeat ≤ 1.5s
- WebSocket propagation delay ≤ 500ms
- Mobile responsive

---

## Phase 6: DEMO_MODE & Demo Scenarios

**Goal:** Create a self-contained demo mode that runs without network and pre-seeds realistic incidents.

### 6.1 DEMO_MODE Architecture

- [ ] `DEMO_MODE=true` disables ALL live API calls
- [ ] `GEMINI_API_KEY` must be unset or ignored
- [ ] Loads synthetic incidents from `backend/tests/fixtures/demo_scenarios/`
- [ ] Judge Layer uses static rules (identical to production)
- [ ] All pipeline stages operational with simulated data

### 6.2 Six Pre-Built Scenarios

| # | Scenario | Incident Type | Severity | Key Demo Moment |
|---|----------|---------------|----------|-----------------|
| 1 | **PocketOS Deletion** | AGT-DEL-001 | CRITICAL | Database DROP TABLE blocked in 9 seconds |
| 2 | **Step Finance $40M** | AGT-FIN-002 | CRITICAL | Unauthorized transfer quarantined |
| 3 | **Meta Permission Exposure** | AGT-PER-003 | HIGH | OAuth scope escalation detected |
| 4 | **UnitedHealth Denials** | AGT-HRM-004 | HIGH | Harmful care denial output flagged |
| 5 | **Replit Record Deletion** | AGT-EXT-005 | CRITICAL | Mass record access → exfiltration pattern |
| 6 | **Organization Policy Switching** | AGT-EXT-005 | CRITICAL | Same incident under 3 templates: HIPAA (CRITICAL, CEO paged) → SaaS Startup (MEDIUM, basic logs) → FinTech (conditional PCI-DSS) |

### 6.3 Demo Endpoints

- [ ] `POST /api/v1/demo/seed` — load all 6 scenarios (403 unless DEMO_MODE)
- [ ] `POST /api/v1/demo/reset` — purge demo data, restore clean state
- [ ] `POST /api/v1/demo/trigger` — inject a specific scenario by ID

### 6.4 Demo Script Alignment (v3.0 — 180 seconds)

Ensure these UI elements are prominent and fast (< 2s load):

**Part 1 — The Judge Layer (0:30–1:15):**
- [ ] Judge decision panel with 4 DENY decisions + rationale
- [ ] 4 bypass pattern renders with correct labels
- [ ] Lobster Trap quarantine visualization

**Part 2 — The Incident Response (1:15–2:00):**
- [ ] Forensic capture auto-generation
- [ ] NIST SP 800-61r2 classification card
- [ ] Timeline: Trigger → Judge (<50ms) → Quarantine (67ms) → Forensics (89ms) → Health Update (124ms) → NIST (156ms)

**Part 3 — Custom Policy Builder (2:00–2:40):**
- [ ] Same incident under 3 template switches: HIPAA / SaaS Startup / FinTech
- [ ] ODP badges and "6 Industry Templates" metric
- [ ] Policy Conflict warnings (if any)

**Part 4 — Agent Health Profile (2:40–2:55):**
- [ ] Agent Health Dashboard: lie rate 4.2%, risk score 73/100
- [ ] Policy version badge

**Close (2:55–3:00):**
- [ ] Design partner ask + QR code

**Validation:**
- Runs without network access
- 6 scenarios visible within 2 seconds of page load
- Zero Gemini API calls (verified in logs)
- All 4 bypass patterns visually demonstrated

---

## Phase 8: Policy Builder & ODP System

**Goal:** Implement NIST SP 800-53 Organization-Defined Parameters (ODPs) — the first AI security product to do so natively.

### 8.1 NIST Baseline Templates (`data/nist_baselines.json`)

- [ ] 12 immutable NIST baseline policies (one per incident type)
- [ ] Each baseline defines: severity, auto-contain, escalation contacts, response SLA, forensic level, notify targets, compliance report, record threshold
- [ ] Baselines are reference data — immutable by design
- [ ] Version tracking for NIST updates

### 8.2 Organization-Defined Parameters (`app/policy/`)

- [ ] `policy_builder.py` — CRUD for ODPs
- [ ] 8 ODP keys per incident type:
  1. `severity_threshold`
  2. `auto_contain_enabled`
  3. `escalation_contacts`
  4. `response_time_sla`
  5. `forensic_level`
  6. `notify_targets`
  7. `compliance_report`
  8. `record_threshold`
- [ ] Per-organization isolation
- [ ] Versioning with full provenance (who, what, when, from→to)
- [ ] Rollback within 30 seconds

### 8.3 Visual Policy Builder UI (React)

- [ ] Side-by-side layout: read-only NIST baseline panel + editable ODP panel
- [ ] Inline conflict warnings (WARNING for deviations, BLOCKED for missing required fields)
- [ ] Preview/Test modes
- [ ] 6 industry templates: HIPAA, SOC2, PCI-DSS, GDPR, Financial Services, SaaS Startup
- [ ] Template application < 10 seconds
- [ ] Rollback within 30 seconds

### 8.4 Policy Conflict Detection

- [ ] 7 conflict rules:
  - `SEVERITY_DOWNGRADE` — ODP lowers severity below baseline
  - `MISSING_REQUIRED` — Required ODP not set
  - `VALUE_MISMATCH` — ODP contradicts baseline
  - `THRESHOLD_VIOLATION` — Numeric ODP outside acceptable range
- [ ] Conflict severity: WARNING or CRITICAL
- [ ] Detection latency: < 500ms

### 8.5 Resolved Policy View

- [ ] `resolved_policies` VIEW (8 LEFT JOINs) computes effective policy per incident type
- [ ] Sub-millisecond resolution at query time
- [ ] Used by Judge Layer before rendering verdicts

### 8.6 API Endpoints (14 total)

- [ ] `GET /api/v1/policy-builder/nist-baseline` — list all baselines
- [ ] `GET /api/v1/policy-builder/nist-baseline/{type}` — single baseline
- [ ] `GET /api/v1/policy-builder/odps` — list all ODPs
- [ ] `GET /api/v1/policy-builder/odps/{type}` — ODPs for incident type
- [ ] `PUT /api/v1/policy-builder/odps/{type}` — update ODPs
- [ ] `PUT /api/v1/policy-builder/odps/bulk` — bulk update
- [ ] `POST /api/v1/policy-builder/validate` — validate ODPs
- [ ] `GET /api/v1/policy-builder/resolve/{type}` — resolved policy
- [ ] `GET /api/v1/policy-builder/templates` — list industry templates
- [ ] `POST /api/v1/policy-builder/templates/{id}/apply` — apply template
- [ ] `GET /api/v1/policy-builder/versions` — version history
- [ ] `POST /api/v1/policy-builder/versions/{id}/rollback` — rollback
- [ ] `GET /api/v1/policy-builder/conflicts` — list conflicts
- [ ] `POST /api/v1/policy-builder/conflicts/{id}/resolve` — resolve conflict

**Validation:**
- 12 NIST baselines load and validate
- 6 industry templates apply in < 10s
- Conflict detection < 500ms
- Rollback works within 30s
- `resolved_policies` VIEW returns correct merged policy

---

## Phase 7: Integration & External APIs

**Goal:** Integrate with Gemini Pro (async only), SupraWall, and build compliance exports.

### 7.1 Gemini Pro Cache Population (Async Overlay)

**CRITICAL: Gemini is NEVER in the enforcement path. It runs post-hoc or asynchronously only.**

- [ ] `scripts/populate_gemini_cache.py` — offline cache builder
- [ ] `services/gemini_cache.py` — read-only cache lookup in hot path
- [ ] Circuit breaker: 5 failures → open, 300s recovery
- [ ] Fallback: on any failure, skip enrichment; pipeline continues unchanged
- [ ] Cache key: SHA-256 of normalized metadata + judge verdict
- [ ] Cache TTL: 24 hours; max 1000 entries

### 7.2 SupraWall Integration

- [ ] `POST /api/v1/integrations/suprawall/events` — webhook endpoint
- [ ] Event correlation by `session_id` or `client_ip`
- [ ] Unified timeline: SupraWall + Lobster Trap + Judge Layer
- [ ] Side-by-side decision comparison in evidence packages
- [ ] Graceful degradation if SupraWall absent

### 7.3 Compliance Exports

- [ ] EU AI Act Article 73 report (JSON + PDF)
  - Auto-generated for CRITICAL/HIGH incidents
  - Mandatory fields: incident ID, timestamp, classification, impact, actions taken, evidence references
  - Alerts compliance officer within 1 hour
- [ ] NIST AI RMF mapping matrix (CSV/JSON)
- [ ] HIPAA breach assessment (healthcare deployments)

**Validation:**
- Cache hit rate ≥ 89%
- Gemini timeout has zero enforcement impact
- SupraWall events appear in dashboard within 2 seconds
- EU AI Act export contains all mandatory fields

---

## Phase 9: Testing, Validation & Deployment

**Goal:** Achieve production readiness through comprehensive testing and deploy to Railway.

### 9.1 Test Suites

#### Unit Tests (≥ 70% coverage target, 60% hard floor)

| Module | Target | Tests |
|--------|--------|-------|
| `log_tailer.py` | 90% | File watching, parsing, queue handling |
| `anomaly_detection.py` | 95% | All heuristic rules, scoring, thresholds |
| `classification.py` | 90% | Rule matching, severity assignment |
| `judge/engine.py` | 95% | Decision matrix, ODP resolution, edge cases |
| `judge/bypass_detector.py` | 100% | All 400 vectors |
| `response_engine.py` | 85% | Playbook execution, timeouts |
| `forensics.py` | 85% | Package building, signing, export |
| `gemini_cache.py` | 90% | Cache key gen, hit/miss |
| `policy_builder.py` | 85% | NIST baseline loading, ODP CRUD, conflict detection |
| `api/` routers | 85% | All endpoint handlers |

#### Integration Tests

- [ ] `test_full_pipeline.py` — DETECT → CLASSIFY → JUDGE → RESPOND → FORENSICS
- [ ] `test_websocket.py` — connect, filter, receive events, heartbeat
- [ ] `test_demo_mode.py` — seed, verify 6 scenarios (20 incidents), reset
- [ ] `test_lobster_trap_e2e.py` — CLI wrapper, policy validation
- [ ] `test_policy_builder_e2e.py` — baseline load, ODP edit, template apply, conflict detect, rollback

#### Mandatory Test Files

- [ ] `test_bypass_detection.py` — **55/55 must pass for CI/CD green**
- [ ] `test_enforcement_accuracy.py` — 100% true positive rate
- [ ] `test_competitive_bypass.py` — reproduces SupraWall test conditions
- [ ] `test_determinism.py` — 1,000 repeats, 0 variance
- [ ] `test_policy_builder.py` — baseline immutability, ODP resolution, conflict detection, versioning integrity

### 9.2 Validation Checklist (V-001 through V-057)

Execute all 57 validation items from `PLAYBOOK_Non_Functional_Requirements.md` Appendix A. Key gates:

| ID | Requirement | Pass Criteria |
|----|-------------|---------------|
| V-012 | Zero LLM in enforcement | Code audit of `judge/` and `classify/` |
| V-013 | Determinism | 1,000 repeats, 0 variance |
| V-014–017 | Bypass patterns | 100% detection on all 4 patterns |
| V-019 | Bypass test suite | 55/55 pass |
| V-021 | SQLCipher encryption | `hexdump` shows non-printable |
| V-028 | Uptime | ≥ 95% over 24h |
| V-030 | DEMO_MODE | Dashboard loads with incidents; Judge works |
| V-041 | File count | ≤ 50 Python, ≤ 40 React |
| V-042 | Coverage | Python ≥ 60%, React ≥ 40% |
| V-053 | Health endpoint | `GET /api/health` returns 200 with all checks ok |

### 9.3 Performance Validation

- [ ] k6 load test: 50 users / 5 minutes
- [ ] p95 latency targets met per endpoint
- [ ] RAM ≤ 512MB sustained (`docker stats`)
- [ ] SQLite ≤ 500MB at 500K incidents
- [ ] Lighthouse CI score ≥ 70

### 9.4 Security Audit

- [ ] JWT validation on all protected endpoints
- [ ] Rate limiting: 100 req/min per IP
- [ ] Input fuzzing: all invalid inputs rejected
- [ ] Prompt injection payloads sanitized
- [ ] Log inspection: no PII, correct permissions
- [ ] Policy files not exposed via API
- [ ] `DELETE /api/incidents/purge` works within 30s
- [ ] Policy files not exposed via API (HTTP 404)

### 9.5 Deployment

#### Railway (Primary)

- [ ] `railway.json` with Nixpacks builder
- [ ] `Procfile`: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`
- [ ] `runtime.txt`: `python-3.11.7`
- [ ] Health check: `GET /api/v1/health`, 30s timeout
- [ ] Restart policy: `ON_FAILURE`, max 3 retries
- [ ] Environment: `DEBUG=false`, `DEMO_MODE=true` (for demo day)
- [ ] UptimeRobot ping every 5 minutes to `/api/v1/health`

#### Docker (Local)

- [ ] `docker-compose up` starts full stack in ≤ 30s
- [ ] Backend healthcheck every 30s
- [ ] Frontend nginx proxies `/api/` and `/ws/` to backend

#### Verification

- [ ] `railway up` completes without errors
- [ ] Health endpoint 200
- [ ] `GET /api/v1/incidents` returns data
- [ ] WebSocket connects
- [ ] Service stays awake > 30 minutes
- [ ] Policy Builder endpoints respond
- [ ] `GET /api/v1/policy-builder/resolve/{type}` returns merged policy

---

## Phase 10: SDK & Middleware (Post-MVP)

**Goal:** Deliver the `playbook-guard` Python SDK and LangChain/CrewAI middleware integrations.

### 10.1 Python SDK (`sdk/`)

- [x] `PlaybookClient` — async HTTP client with JWT auth, retry logic
- [x] `@guard` decorator — wraps functions with Judge Layer evaluation
- [x] `HeartbeatSender` — background health pings
- [x] `GuardBlockedError` / `GuardQuarantinedError` exceptions
- [x] Environment-based configuration (`PLAYBOOK_API_KEY`, `PLAYBOOK_ENDPOINT`)

### 10.2 Middleware Integrations

- [x] **LangChain**: `PlaybookCallbackHandler` — intercepts `on_tool_start` / `on_llm_start`
- [x] **CrewAI**: `CrewAIGuard` / `crewai_guard` — auto-extracts `agent_id` from `Agent.role`

### 10.3 SDK Distribution

- [x] `pyproject.toml` with `playbook-guard` package name
- [x] `sdk/tests/` — unit tests for client, guard, heartbeat, middleware
- [ ] PyPI publication (post-hackathon)

**Validation:**
- SDK unit tests pass (46 tests)
- `@guard` correctly blocks/allows/quarantines based on mock verdicts
- Middleware attaches to LangChain/CrewAI without breaking existing flows

---

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R-001 | Judge Layer latency exceeds 50ms | Medium | Critical | Profile early; optimize rule evaluation order; cache compiled rules |
| R-002 | Bypass test vectors < 55/55 | Low | Critical | Build detector incrementally with tests; fuzz with generated variants |
| R-003 | Railway 512MB RAM insufficient | Medium | High | Memory budget per component; test with `docker stats`; shed load at 80% |
| R-004 | SQLite single-writer bottleneck | Medium | Medium | WAL mode; batch writes every 100ms; async queue for DB ops |
| R-005 | Frontend bundle > 500KB | Low | Medium | Code splitting; lazy load charts; tree-shake Recharts |
| R-006 | Gemini cache miss during demo | Medium | Medium | Pre-populate 50+ entries; DEMO_MODE never calls live API |
| R-007 | Lobster Trap CLI unavailable | Low | High | Mock CLI wrapper for development; graceful degradation |
| R-008 | 8-day timeline compression | High | High | `TODO(hackathon)` markers; defer P2 features; parallel tracks |
| R-009 | WebSocket reliability on Railway | Medium | Medium | Auto-reconnect with backoff; fallback to polling |
| R-010 | Compliance export format rejected | Low | Low | Validate against EU AI Act schema; test with sample regulator |
| R-011 | Policy Builder adds >8 React files | Medium | Medium | Merge components; defer marketplace/multi-tenant to post-hackathon |
| R-012 | DB schema has only 12 of 16 types | Medium | High | Add 4 missing types in Alembic migration #2 |
| R-013 | DEMO-006 changed mid-project | Low | Medium | Update demo data fixtures; rehearse new script flow |
| R-014 | NIST baseline immutability violated | Low | Critical | Schema-level CHECK constraints; application-layer guards; audit triggers |

---

## Appendix A: File Budget

### Python Files (Target: ≤ 50)

```
backend/app/
  __init__.py                           # 1
  main.py                               # 2
  database.py                           # 3
  models.py                             # 4
  schemas.py                            # 5
  core/
    __init__.py                         # 6
    config.py                           # 7
    logging.py                          # 8
    security.py                         # 9
    constants.py                        # 10
  routers/
    __init__.py                         # 11
    health.py                           # 12
    incidents.py                        # 13
    judge.py                            # 14
    playbooks.py                        # 15
    forensics.py                        # 16
    demo.py                             # 17
    compliance.py                       # 18
    websocket.py                        # 19
  services/
    __init__.py                         # 20
    log_tailer.py                       # 21
    anomaly_detection.py                # 22
    classification.py                   # 23
    response_engine.py                  # 24
    forensics.py                        # 25
    gemini_cache.py                     # 26
  judge/
    __init__.py                         # 27
    engine.py                           # 28
    rules.py                            # 29
    bypass_detector.py                  # 30
    decision.py                         # 31
backend/alembic/env.py                  # 32
backend/tests/conftest.py             # 33
backend/tests/unit/test_*.py (×11)    # 34–44
backend/tests/integration/test_*.py (×5) # 45–49
backend/scripts/populate_gemini_cache.py # 50
```

### React Components (Target: ≤ 40)

```
frontend/src/
  components/
    Layout.tsx                          # 1
    Sidebar.tsx                         # 2
    Header.tsx                          # 3
    IncidentTable.tsx                   # 4
    IncidentCard.tsx                    # 5
    SeverityBadge.tsx                   # 6
    StatusBadge.tsx                     # 7
    JudgeDecisionBadge.tsx              # 8
    Timeline.tsx                        # 9
    TimelineEvent.tsx                   # 10
    HealthScore.tsx                     # 11
    HealthTrendChart.tsx                # 12
    SeverityDistributionChart.tsx       # 13
    IncidentTrendChart.tsx              # 14
    ComplianceHeatmap.tsx               # 15
    BypassPatternCard.tsx               # 16
    PolicyBuilderPanel.tsx              # 17
    ODPConflictBadge.tsx                # 18
    IndustryTemplateSelector.tsx        # 19
    LoadingSpinner.tsx                  # 20
    ErrorBoundary.tsx                   # 21
    Toast.tsx                           # 22
    FilterBar.tsx                       # 23
    SearchInput.tsx                     # 24
    Pagination.tsx                      # 25
    WebSocketProvider.tsx               # 26
  pages/
    IncidentsPage.tsx                   # 27
    IncidentDetailPage.tsx              # 28
    JudgePage.tsx                       # 29
    AgentHealthPage.tsx                 # 30
    CompliancePage.tsx                  # 31
    PolicyBuilderPage.tsx               # 32
    ReviewQueuePage.tsx                 # 33
    SettingsPage.tsx                    # 34
  hooks/
    useWebSocket.ts                     # 35
    useIncidents.ts                     # 36
    useIncident.ts                      # 37
    useJudgeStats.ts                    # 38
    useHealthScores.ts                  # 39
  services/
    api.ts                              # 40
    auth.ts                             # 41
  types/
    index.ts                            # 42
  utils/
    formatters.ts                       # 43
  App.tsx                               # (not counted as component)
  main.tsx                              # (not counted as component)
```

---

## Appendix B: Decision Log

| # | Decision | Rationale | Date | Reversible? |
|---|----------|-----------|------|-------------|
| D-001 | SQLite over PostgreSQL | Railway 512MB constraint; single-node architecture; WAL mode sufficient | 2026-05-12 | Yes — migration path documented |
| D-002 | Deterministic Judge over LLM-as-Judge | Compliance (EU AI Act Art. 15); 100% reproducibility; immunity to bypass | 2026-05-12 | No — core architectural bet |
| D-003 | JWT over OAuth2 | Single-node deployment; no identity provider available; upgrade path documented | 2026-05-12 | Yes — OAuth2 middleware planned |
| D-004 | 16 incident types (not 8 or 12) | `PLAYBOOK_Functional_Requirements.md` (2026-05-15) is authoritative over older docs | 2026-05-12 | Yes — taxonomy extensible |
| D-005 | Python ≤ 50 files, React ≤ 40 files | NFR V-041; hackathon scope control; forces modular design | 2026-05-12 | Yes — post-hackathon expansion allowed |
| D-006 | DEMO_MODE: 6 scenarios (not 20) | Demo Script specifies 6 scenarios; NFR says 20 synthetic incidents total | 2026-05-12 | Yes — 6 scenarios = 20 incidents |
| D-007 | Bypass patterns: 4 canonical (not 6+) | `AGENTS.md` v1.1 and NFR specify 4; Demo Script's additional 2 are variants | 2026-05-12 | No — 4 is the validated set |
| D-008 | Railway sleep = 30 min | `PLAYBOOK_Deployment_Guide.md` specifies 30 min; NFR silent on duration | 2026-05-12 | N/A |
| D-009 | Token expiry = 60m (API doc), 24h (NFR) | `PLAYBOOK_API_Documentation.md` says 60m; NFR says 24h; use 24h prod, 60m dev | 2026-05-12 | Yes — configurable |
| D-010 | Rate limit = 60 req/min (API doc default) | `PLAYBOOK_API_Documentation.md` specifies 60; NFR specifies 100; use 100 for production | 2026-05-12 | Yes — configurable via env |
| D-011 | Policy Builder is P0 (not P2) | `PLAYBOOK_Functional_Requirements.md` v1.2 elevates Policy Builder to P0 | 2026-05-12 | No — core differentiator |
| D-012 | Database schema: 20 tables + 1 view | `PLAYBOOK_Database_Schema.md` v1.2 expands from 10 to 20 tables | 2026-05-12 | Yes — Alembic migration #2 |
| D-013 | DEMO-006 = Policy Switching (not Bypass) | `PLAYBOOK_Demo_Script_and_Presentation.md` v3.0 replaced bypass demo with Policy Builder demo | 2026-05-12 | Yes — scenario fixtures updated |
| D-014 | Honest market claim revised | `RESEARCH_SYNTHESIS_HONEST.md` revises $15B→$1.72B and identifies real competitors | 2026-05-12 | Yes — claims updated in pitch |
| D-015 | 12 NIST baselines (not 16) | NIST baselines cover 12 of 16 incident types; 4 additional types lack baselines in v1.0 | 2026-05-12 | Yes — baselines extensible |

---

*End of Development Plan v1.0*
