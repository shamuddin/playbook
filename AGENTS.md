# AGENTS.md — PLAYBOOK Project

> **Implementation Status:** Backend (FastAPI + SQLAlchemy), frontend (React/Vite), Python SDK (`playbook-guard`), and Alembic migrations are implemented. See `backend/`, `frontend/`, and `sdk/` directories.

---

## Project Overview

**PLAYBOOK** is an automated incident response system designed specifically for AI agent deployments. It integrates with **Lobster Trap DPI** (Deep Packet Inspection for LLM traffic) to detect, classify, respond to, and forensically document security incidents in real time.

The system's core architectural bet is the **Judge Layer pattern** (as articulated by Nate B Jones, May 2026): a deterministic, rule-based enforcement layer that intercepts every proposed agent action before execution and renders an irreversible decision — ALLOW, DENY, QUARANTINE, or ESCALATE. The Judge Layer operates at **three points** in the pipeline:
1. **Judge Pre-Screen** (embedded in Detect Agent) — lightweight bypass detection on every log line
2. **Local Judge** (embedded in Classify Agent, Stage 2/3) — full deterministic enforcement decision
3. **Judge Gate** (wrapped around Enforcement Agent) — every playbook action verified before execution

The Judge Layer is architecturally separated from any LLM-based classification and is immune to the four known LLM-judge bypass patterns:

1. Context window displacement (also: RoleSwap)
2. Indirect tool chaining (also: Separator)
3. Unicode homoglyph substitution (also: Base64/encoding)
4. Confidence hijacking (also: SocialEngineering)

> **Note on terminology:** The AI Agent Documentation uses "Classify Agent" and "Judge" interchangeably because the Local Judge is embedded within the Classify Agent. In implementation terms, `app/classify/` contains the deterministic rule engine that produces both the incident taxonomy/severity AND the enforcement verdict (ALLOW/DENY/QUARANTINE/ESCALATE). The `app/judge/` module provides the formal rule definitions, bypass detectors, and decision renderer. Both modules share the same architectural constraint: **zero LLM API calls**.

> **Policy Builder (new in v1.2):** PLAYBOOK now includes a **Custom Policy Builder** implementing NIST SP 800-53 Organization-Defined Parameters (ODPs). This enables organizations to customize incident response parameters (severity thresholds, auto-contain, escalation contacts, etc.) while maintaining immutable NIST baselines. The Policy Builder feeds into the Judge Layer's ODP Resolution Engine before rendering verdicts.

**Key differentiator vs. SupraWall (discovered competitor, Apache 2.0, April 2026):**
- SupraWall answers: *"Should this single request be allowed?"* (guardrail, ~1.2ms)
- PLAYBOOK answers: *"What is the full incident response lifecycle — from detection through forensics and compliance reporting?"* (NIST playbook execution, evidence packaging, EU AI Act mapping, ODP policy customization)

**Honest competitive position:** PLAYBOOK is an early implementation aligning with NIST AI RMF Agentic Profile concepts. It integrates with Lobster Trap DPI for automated containment. Competitors include SupraWall (Apache 2.0, sub-2ms guardrail), Swimlane Turbine (general SOC), ServiceNow AI Control Tower (governance), Pragatix/AGAT (runtime enforcement), and Wiz Defend (cloud-focused).

### 4-Stage Pipeline

```
Stage 1: DETECT          Stage 2: CLASSIFY/JUDGE   Stage 3: ENFORCE        Stage 4: FORENSICS
+----------------+      +----------------+       +----------------+       +----------------+
| Log Tailer     |----->| Local Judge    |------>| Actor (Playbook|------>| Evidence       |
| + Judge Pre-   |      | + Gemini Cache |       |  + Judge Gate) |       | Package        |
|   Screen       |      | + ODP Resolver |       |                |       | Builder        |
+----------------+      +----------------+       +----------------+       +----------------+
                              ↓
                       Policy Builder
                       (NIST Baseline + ODPs)
```

- **Incident taxonomy:** The canonical classification schema defines **16 incident types** (e.g., `prompt_injection`, `data_exfiltration`, `privilege_escalation`, `jailbreak_attempt`, etc.), aligning with `PLAYBOOK_Functional_Requirements.md` and the Compliance Mapping. Earlier documents (Technical Specification, Demo Script) reference 8 or 12 types; these are being updated.
- **Throughput target:** 100 events/second (single-threaded async)
- **Latency targets (per stage):
  - Detection (Lobster Trap DPI): ≤ 10ms
  - Classification (Judge Layer): ≤ 50ms (p95)
  - Response (playbook execution): ≤ 150ms
  - **Total end-to-end (p95):** ≤ 200ms
  - **Hard ceiling:** 500ms
- **Ordering:** Strict FIFO within a single session; parallel across sessions

### Document Inventory (this repo)

| File | Purpose | Lines (approx) |
|------|---------|----------------|
| `PLAYBOOK_Technical_Specification.md` | Full system architecture, component specs, data models, API spec, testing strategy | 3,698 |
| `PLAYBOOK_Functional_Requirements.md` | Use cases, feature requirements (FEAT-001 through FEAT-028), user stories, acceptance criteria | 3,314 |
| `PLAYBOOK_AI_Agent_Documentation.md` | Multi-agent architecture, Judge Layer pattern, agent orchestration, prompt library, performance targets | 5,929 |
| `PLAYBOOK_API_Documentation.md` | REST API & WebSocket protocol, data models, endpoint definitions, error handling, rate limiting, Policy Builder endpoints | 7,411 |
| `PLAYBOOK_Deployment_Guide.md` | Local setup, Railway deployment, Docker, environment variables, verification checklist | 2,253 |
| `PLAYBOOK_Integration_Guide.md` | Lobster Trap DPI integration, Gemini Pro integration, SupraWall integration, Judge Layer code, TerraFabric (future) | 7,054 |
| `PLAYBOOK_Non_Functional_Requirements.md` | Performance SLAs, deterministic enforcement requirements, security, reliability, scalability, compliance | 1,019 |
| `PLAYBOOK_Demo_Script_and_Presentation.md` | 3-minute hackathon demo script, slide deck, backup plans, Q&A preparation, Policy Builder demo | 1,285 |
| `PLAYBOOK_EU_AI_Act_NIST_Compliance_Mapping.md` | Regulatory mapping to EU AI Act Articles 9/15/73, NIST AI RMF Agentic Profile, NIST AI 600-1 GenAI Profile, SOC 2 Type II | 1,970 |
| `PLAYBOOK_Database_Schema.md` | SQLite database schema (v1.2, 20 tables + 1 view, WAL mode, FK enforced) | 3,924 |
| `CUSTOM_POLICY_BUILDER_Design.md` | NIST SP 800-53 ODP system design, 8 features, visual builder, industry templates | 285 |
| `RESEARCH_SYNTHESIS_HONEST.md` | Honest market analysis, competitive positioning, revised claims and score | 95 |
| `VIDEO_ANALYSIS_Nate_B_Jones.md` | Video content analysis, Judge Layer validation, SupraWall discovery, bypass patterns | 166 |

> **Document freshness note:** Where conflicts exist between documents, the most recent versions are authoritative: `PLAYBOOK_AI_Agent_Documentation.md` (2026-06-15), `PLAYBOOK_Functional_Requirements.md` (2026-05-15), and `PLAYBOOK_EU_AI_Act_NIST_Compliance_Mapping.md` (2026-05-11). Older documents (e.g., Technical Specification and Deployment Guide, dated 2025-01-15) are being updated. The new `PLAYBOOK_Database_Schema.md` (v1.2), `CUSTOM_POLICY_BUILDER_Design.md`, and `RESEARCH_SYNTHESIS_HONEST.md` are current as of 2026-05-12.

---

## Intended Technology Stack

The documentation specifies the following stack for implementation:

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Runtime** | Python | 3.11+ | Core application language |
| **Web Framework** | FastAPI | 0.109+ | REST API + WebSocket server |
| **Database** | SQLite | 3.40+ | Local persistence (embedded) |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction layer |
| **Migrations** | Alembic | 1.13+ | Schema versioning |
| **Async Tasks** | asyncio / Celery (optional) | — | Background processing |
| **File Watching** | watchdog | 3.0+ | Log file monitoring (cross-platform) |
| **LLM Client** | google-generativeai | 0.5+ | Gemini Pro API (cache population only) |
| **CLI Subprocess** | asyncio.create_subprocess_exec | stdlib | Lobster Trap CLI invocation |
| **YAML Processing** | PyYAML | 6.0+ | Policy read/write |
| **Frontend** | React | 18.2+ | Dashboard UI |
| **UI Framework** | Tailwind CSS | 3.4+ | Styling |
| **Charts** | Recharts | 2.10+ | Data visualization |
| **Build Tool** | Vite | 5.0+ | Frontend bundling |
| **Testing** | pytest | 7.4+ | Unit + integration tests |
| **Testing** | pytest-asyncio | 0.21+ | Async test support |
| **Linting** | ruff | 0.1+ | Python linting and formatting |
| **Type Checking** | mypy | 1.7+ | Static type checking |

**Note:** None of these dependencies are present in this repository yet. They are specified for future implementation.

---

## Intended Repository Structure

Per the Deployment Guide, the implemented repository should look like:

```
playbook/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI entry point
│   │   ├── database.py      # SQLite/SQLAlchemy setup
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/         # API route modules
│   │   ├── services/        # Business logic
│   │   └── core/            # Config, logging, utils
│   ├── alembic/             # Database migrations
│   ├── policies/            # YAML playbook definitions
│   ├── tests/               # pytest suite
│   ├── scripts/             # Helper scripts
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/                # React application
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.template            # Environment variable template
├── .gitignore
└── README.md
```

---

## Key Configuration (Expected)

When implemented, the project will use environment variables (no hardcoded config). Critical variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | `development` | `development`, `staging`, or `production` |
| `DEMO_MODE` | Yes | `false` | If `true`, disables live API calls and loads pre-built incidents |
| `DATABASE_URL` | Yes | `sqlite:///./playbooks.db` | SQLite connection string |
| `GEMINI_API_KEY` | Conditional | — | Required unless `DEMO_MODE=true` |
| `LOBSTERTRAP_BINARY_PATH` | Yes | `./bin/lobstertrap` | Path to Lobster Trap executable |
| `SECRET_KEY` | Yes | — | JWT signing key (≥ 64 chars recommended; ≥ 256 bits / 32 bytes minimum) |
| `ANOMALY_THRESHOLD` | No | `25.0` | Score threshold for incident creation |
| `PLAYBOOK_DIR` | Yes | `./policies` | Directory containing playbook YAML files |
| `JUDGE_DETERMINISTIC_MODE` | No | `true` | Force deterministic-only classification (no Gemini LLM calls in enforcement path) |
| `JUDGE_BYPASS_DETECTION` | No | `true` | Enable bypass pattern detection in Judge Layer |
| `API_PREFIX` | No | `/api/v1` | API route prefix |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Comma-separated allowed origins for CORS |
| `RETAIN_FULL_PROMPTS` | No | `false` | Store complete prompt text (default false for privacy) |
| `EVIDENCE_STORE_PATH` | Yes | `./evidence` | Directory for evidence packages |
| `SQLCIPHER_KEY` | Conditional | — | Required for encrypted SQLite (≥ 32 bytes). Plaintext permitted only when `DEMO_MODE=true` |
| `POLICY_BUILDER_ENABLED` | No | `true` | Enable NIST ODP Policy Builder endpoints |
| `NIST_BASELINE_PATH` | Yes | `./data/nist_baselines.json` | NIST baseline policy definitions |
| `ODP_DEFAULTS_PATH` | Yes | `./data/odp_defaults.json` | Default ODP values per incident type |

A complete `.env.template` is documented in `PLAYBOOK_Deployment_Guide.md`. **Note:** The Deployment Guide's `.env.template` currently omits `SQLCIPHER_KEY`; this must be added for production deployments.

---

## Build and Test Commands (Expected)

When the codebase is implemented, the documented build/test workflow is:

### Backend

```bash
# Setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
alembic upgrade head

# Run (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

# Run (production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Development
npm run build    # Production build
```

### Testing

```bash
# Backend (from backend/ with venv activated)
pytest -v                           # Full suite
pytest -v -m "integration"          # Integration tests only
pytest -v -m "unit"                 # Unit tests only
pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend
npm test
```

### Linting / Type Checking

```bash
# Python
ruff check .
ruff format .
mypy app/
```

---

## Code Organization & Module Divisions

When implemented, the backend should be organized as:

| Module | Responsibility |
|--------|--------------|
| `app/main.py` | FastAPI application factory, lifespan events |
| `app/database.py` | SQLAlchemy engine, session management |
| `app/models.py` | SQLAlchemy ORM models (incidents, timeline, judge_decisions, etc.) |
| `app/schemas.py` | Pydantic request/response models |
| `app/core/config.py` | Pydantic Settings, env var validation |
| `app/core/logging.py` | Structured JSON logging setup |
| `app/routers/` | API route modules (incidents, agents, judge, playbooks, policy-builder, compliance, demo) |
| `app/services/` | Business logic (log tailer, anomaly detection, classification, judge agent, forensics, policy builder) |
| `app/judge/` | **Deterministic Judge Layer** — rule definitions, bypass detectors, decision renderer; zero LLM calls |
| `app/policy/` | **Policy Builder** — NIST baseline loader, ODP resolver, conflict detector, versioning engine |

**Critical architectural rule:** The `judge/`, `classify/`, and `policy/` enforcement modules must contain **zero LLM API calls**. All enforcement decisions are deterministic. The Gemini Pro overlay runs asynchronously or post-hoc and can never block or override the enforcement path.

> **Note:** The `PLAYBOOK_Database_Schema.md` (v1.2) defines **20 tables + 1 view** for the production schema. This expands the original 10-table design with: `judge_decisions`, `bypass_patterns`, `bypass_attempts`, `suprawall_events`, `nist_baselines`, `organization_odps`, `policy_versions`, `industry_templates`, `odp_conflicts`, plus supporting tables (`agents`, `playbook_actions`, `audit_log`, `gemini_cache`, `agent_health_history`, `detection_rules`, `demo_scenarios`, `compliance_mappings`). The `resolved_policies` VIEW computes the effective policy per incident type by merging NIST baselines with organizational ODPs.

> **Note:** The `PLAYBOOK_Technical_Specification.md` (Section 5.2) currently lists all API endpoints with `Auth: None`. This is a documentation error — all endpoints except `GET /api/health` require valid Bearer tokens per `PLAYBOOK_API_Documentation.md` and the Security Considerations below.

---

## Testing Strategy

The documentation specifies the following test requirements:

| Test Category | Target | Minimum |
|---------------|--------|---------|
| Unit tests (Python) | >= 70% line coverage | 60% hard floor |
| Unit tests (React) | >= 50% component coverage | 40% hard floor |
| Integration tests | All API endpoints (>= 10 cases) | 8 cases minimum |
| E2E tests | Critical path: create -> classify -> respond -> resolve | 1 complete flow |
| Load tests | 10 concurrent users, 60 seconds | Performed at least once |
| **Bypass detection tests** | All 4 bypass patterns (55 test vectors) | **55/55 must pass** |
| **Determinism tests** | 1000 repeated classifications of identical prompts | 0 variance |
| **Policy Builder tests** | NIST baseline immutability, ODP conflict detection, resolved policy correctness | All pass |
| **Red-team tests** | ≥50 adversarial tests covering all 16 incident types | ≥94% detection rate |

**Mandatory test suites:**
- `test_bypass_detection.py` — must pass 55/55 for CI/CD green
- `test_enforcement_accuracy.py` — must maintain 100% true positive rate
- `test_competitive_bypass.py` — automated test reproducing SupraWall test conditions (future)
- `test_policy_builder.py` — NIST baseline/ODP resolution, conflict detection, versioning

**Additional validation:** See `PLAYBOOK_Non_Functional_Requirements.md` Appendix A for the complete 57-item Validation Checklist (V-001 through V-057) with specific pass criteria.

---

## Security Considerations

1. **Deterministic Enforcement Path:** No LLM inference is permitted in the enforcement path (`judge/` or `classify/` modules). Any LLM dependency in enforcement is a **P0 defect**.
2. **JWT Authentication:** Bearer token (HS256) with `SECRET_KEY` ≥ 64 characters (≥ 256 bits / 32 bytes minimum). Token expiry: **24 hours** in production; 60 minutes acceptable for development. All `/api/*` endpoints except `/api/health` require valid tokens.
3. **Input Validation:** JSON schema validation on all inputs; NFKC + TR39 confusables normalization before pattern matching; max prompt length 10,000 chars; control character stripping.
4. **Data Encryption at Rest:** SQLCipher AES-256-CBC with PBKDF2-HMAC-SHA256 (256,000 iterations). `SQLCIPHER_KEY` env var required (≥ 32 bytes entropy). Plaintext SQLite permitted **only** when `DEMO_MODE=true`.
5. **PII Handling:** Auto-redaction before Gemini API transmission; regex scan for email/SSN patterns; `RETAIN_FULL_PROMPTS=false` by default.
6. **Log Security:** `chmod 750` on log directories; mask prompt content beyond first 50 chars; no PII in application logs.
7. **GDPR / EU AI Act:** Auto-purge incident records and audit logs older than 90 days; `DELETE /api/incidents/purge` endpoint; consent logging for all exports. **Evidence packages retained for 2,555 days (7 years)** per compliance requirements. Full prompts purged after 30 days unless `RETAIN_FULL_PROMPTS=true`.

---

## Compliance & Regulatory Mapping

PLAYBOOK is designed to map to:

- **EU AI Act** (Regulation (EU) 2024/1689): Articles 9 (Risk Management), 15 (Accuracy/Robustness), 73 (Incident Reporting)
- **NIST AI RMF Agentic Profile:** AG-GV.1, AG-MG.1, AG-RS.1, AG-MT.1, AG-RB.1, AG-TR.1
- **NIST AI RMF Judge Governance (proposed):** AG-JG.1 — PLAYBOOK is an early implementation
- **NIST AI 600-1 GenAI Profile:** Map 1.1, Measure 2.1, Manage 3.1 — FULLY ALIGNED
- **NIST SP 800-53:** Organization-Defined Parameters (ODPs) — first AI security product implementation
- **NIST SP 800-61r2:** Computer Security Incident Handling Guide — playbook mapping
- **HIPAA 45 CFR 164.306:** Security standards for ePHI
- **ISO/IEC 23053:2022:** Framework for AI systems using ML
- **SOC 2 Type II:** CC6.1, CC7.2, CC7.3 — ALIGNED/FULLY ALIGNED

Full mapping tables are in `PLAYBOOK_EU_AI_Act_NIST_Compliance_Mapping.md`.

---

## Deployment Targets

| Target | Method | Validation |
|--------|--------|------------|
| **Railway (primary)** | GitHub repo -> Railway template; auto-deploy on push to `main` | Health check passes within 60s |
| **Local Docker** | `docker compose up` | Full stack starts in <= 30s |
| **Local bare metal** | `pip install -r requirements.txt && uvicorn app.main:app` | Starts in <= 10s |
| **DEMO_MODE** | `DEMO_MODE=true` env var; zero external dependencies | Runs without network access; pre-seeds 6 demo scenarios (20 synthetic incidents total) |

**Railway free tier constraints:** 512MB RAM, 1GB disk, shared vCPU, sleeps after 30 min idle (use UptimeRobot to ping `/api/v1/health` every 5 min to prevent sleep).

---

## Development Conventions

- **Python:** PEP 8, absolute imports only, max 50 lines per function, max 200 lines per class
- **React:** Airbnb ESLint conventions
- **Naming:** `snake_case` for Python; `camelCase` for React/TypeScript
- **Comments:** Every non-obvious algorithm; every external API call; every env var usage
- **TODOs:** Use `TODO(hackathon)` markers for explicitly scoped technical debt
- **File count targets:** <= 50 Python files, <= 40 React component files. The Policy Builder UI adds ~8 React components; consider merging or deferring marketplace/multi-tenant features to stay under budget.

---

## Language & Tone

All documentation and comments in this project are written in **English** (US). Code comments, commit messages, and documentation should maintain a professional, precise tone appropriate for security infrastructure software.

---

*Last updated: 2026-05-12*
*AGENTS.md version: 1.2*
