# PLAYBOOK

> Automated incident response system for AI agent deployments.

## Overview

PLAYBOOK implements the **Judge Layer pattern** — a deterministic, rule-based enforcement layer that intercepts every proposed agent action before execution and renders an irreversible decision: **ALLOW**, **DENY**, **QUARANTINE**, or **ESCALATE**.

### Key Features

- **4-Stage Pipeline**: DETECT → CLASSIFY/JUDGE → ENFORCE → FORENSICS
- **Deterministic Judge Layer**: Zero LLM in enforcement path, <40ms core latency
- **Policy Builder**: NIST SP 800-53 Organization-Defined Parameters (ODPs) with 6 industry templates
- **16 Incident Types**: Full taxonomy from Data Destruction to Regulatory Trigger
- **Bypass Detection**: Immune to 4 known LLM-judge bypass patterns (400/400 tests)
- **Compliance Mapping**: EU AI Act Art. 9/15/73, NIST AI RMF Agentic Profile, SOC 2 Type II

## Quick Start

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Architecture

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

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | React 18.2, TypeScript, Tailwind CSS, Recharts |
| Database | SQLite 3.40+ (WAL mode, async via aiosqlite) |
| DPI | Lobster Trap |
| LLM Overlay | Gemini Pro (async only, never in enforcement) |

## Documentation

See `projectdocs/` for full specification:

- `PLAYBOOK_Functional_Requirements.md` — Features FEAT-001 through FEAT-028
- `PLAYBOOK_Technical_Specification.md` — Architecture & data models
- `PLAYBOOK_API_Documentation.md` — REST API & WebSocket protocol
- `PLAYBOOK_Database_Schema.md` — 20 tables + 1 view
- `CUSTOM_POLICY_BUILDER_Design.md` — NIST ODP system design

## License

TBD
