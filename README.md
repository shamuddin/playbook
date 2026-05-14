# PLAYBOOK

> Automated incident response system for AI agent deployments.

## Overview

PLAYBOOK implements the **Judge Layer pattern** — a deterministic, rule-based enforcement layer that intercepts every proposed agent action before execution and renders an irreversible decision: **ALLOW**, **DENY**, **QUARANTINE**, or **ESCALATE**.

### Key Features

- **4-Stage Pipeline**: DETECT → CLASSIFY/JUDGE → ENFORCE → FORENSICS
- **Deterministic Judge Layer**: Zero LLM in enforcement path, Target: <40ms core latency (unverified)
- **Policy Builder**: NIST SP 800-53 Organization-Defined Parameters (ODPs) with 6 industry templates
- **16 Incident Types**: Full taxonomy from Data Destruction to Regulatory Trigger
- **Bypass Detection**: Immune to 4 known LLM-judge bypass patterns (55 test vectors)
- **Compliance Mapping**: EU AI Act Art. 9/15/73, NIST AI RMF Agentic Profile, SOC 2 Type II

> **Beta — not production ready.** Single-tenant only. Review security considerations before deploying.

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

### SDK Installation

```bash
pip install playbook-guard
```

```python
from playbook_sdk import guard

@guard(agent_id="my-agent")
async def risky_action(data):
    # Your logic here
    pass
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
| Database | SQLite (default) or PostgreSQL (async via aiosqlite / asyncpg) |
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
