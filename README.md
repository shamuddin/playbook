# PLAYBOOK

> **The SOAR layer that turns Veea Lobster Trap intercepts into automated compliance actions.**

PLAYBOOK is an AI Agent Security & Governance platform built for the modern enterprise. It intercepts every proposed agent action through a deterministic **Judge Layer**, renders real-time verdicts (ALLOW / DENY / QUARANTINE / ESCALATE), and automatically generates incidents, forensics packages, and compliance artifacts — all in under 40ms.

**Built for the Veea ecosystem.** PLAYBOOK consumes deep prompt inspection (DPI) telemetry from [Veea Lobster Trap](https://github.com/veeainc/lobstertrap) and transforms raw intercepts into structured governance workflows. When Lobster Trap detects a jailbreak, PII exfiltration, or unauthorized system command, PLAYBOOK immediately classifies the threat, creates a forensics-ready incident, and routes alerts to the right stakeholders.

---

## Why Veea + PLAYBOOK Wins

| Capability | Veea Lobster Trap | PLAYBOOK | Together |
|------------|-------------------|----------|----------|
| Deep Prompt Inspection (DPI) | ✅ Real-time LLM traffic analysis | — | ✅ End-to-end visibility |
| Threat Detection | ✅ Pattern + heuristic matching | ✅ Deterministic Judge Layer | ✅ Defense in depth |
| Incident Response | — | ✅ Auto-create + classify + route | ✅ Zero-touch SOAR |
| Forensics & Evidence | — | ✅ Chain-of-custody audit trail | ✅ Court-ready packages |
| Compliance Mapping | — | ✅ NIST AI RMF, EU AI Act, SOC 2 | ✅ Audit-ready out of the box |
| Policy Builder | — | ✅ NIST SP 800-53 ODP templates | ✅ CISO-friendly configuration |

**The partnership narrative:** Lobster Trap *sees* the threat. PLAYBOOK *acts* on it. Together they close the loop from detection to remediation without human latency.

---

## Live Demo

**URL:** [https://playbooksoar.aiproofofconcept.in](https://playbooksoar.aiproofofconcept.in)

**Demo Credentials:**
- Username: `demo`
- Password: `demo123`

**What to try in 90 seconds:**
1. **DPI Live Feed** (`/dpi-live`) — Watch real-time Lobster Trap intercepts streaming in with risk scores, matched rules, and verdict badges.
2. **Simulator** (`/swarm`) — Launch a 3-agent swarm attack. Toggle **Misbehavior Mode** to force 100% malicious actions. See every block create a live incident in real time.
3. **Judge Layer** (`/judge`) — Inspect deterministic rule evaluation. Zero LLM in the enforcement path.
4. **Incidents** (`/incidents`) — Review auto-generated incidents with full forensics packages.

---

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  LLM Application │─────▶│ Veea Lobster    │─────▶│  PLAYBOOK       │
│  (Agent Swarm)   │      │ Trap DPI Proxy  │      │  Judge Layer    │
└─────────────────┘      └─────────────────┘      │  + SOAR Engine  │
                                                  └─────────────────┘
                                                           │
                              ┌────────────────────────────┼────────────────────────────┐
                              ▼                            ▼                            ▼
                        ┌──────────┐                ┌──────────┐                ┌──────────┐
                        │ INCIDENT │                │ FORENSICS│                │ COMPLIANCE│
                        │ CREATE   │                │ PACKAGE  │                │ MAPPING   │
                        │ + ROUTE  │                │ BUILDER  │                │ (EU/NIST) │
                        └──────────┘                └──────────┘                └──────────┘
```

**4-Stage Pipeline:**

| Stage | Function | Latency |
|-------|----------|---------|
| 1. DETECT | Normalize agent action → PB-CES event | < 2ms |
| 2. CLASSIFY/JUDGE | Deterministic rule evaluation | < 5ms |
| 3. ENFORCE | ALLOW / DENY / QUARANTINE / ESCALATE | < 1ms |
| 4. FORENSICS | Incident + evidence + chain-of-custody | Async |

---

## Key Features

- **Deterministic Judge Layer** — Zero LLM in the enforcement path. Rule-based decisions in < 5ms. Immune to prompt-injection bypasses.
- **DPI Live Feed** — Real-time dashboard powered by Veea Lobster Trap. See every intercepted prompt, matched rule, risk score, and verdict as it happens.
- **Agent Swarm Simulator** — Launch multi-agent attack scenarios (FX Swap fraud, Data Exfiltration, Prompt Injection) with live WebSocket streaming. Toggle Misbehavior Mode for pure attack simulation.
- **16 Incident Types** — Full taxonomy from Data Destruction to Regulatory Trigger (AGT-FIN-001 through AGT-GOV-016).
- **Policy Builder** — NIST SP 800-53 Organization-Defined Parameters (ODPs) with 6 industry templates (Finance, Healthcare, Government, Retail, Manufacturing, Energy).
- **Compliance Mapping** — EU AI Act Art. 9/15/73, NIST AI RMF Agentic Profile, SOC 2 Type II.
- **Bypass Detection** — Immune to 4 known LLM-judge bypass patterns (55 test vectors).

---

## Screenshots

### DPI Live Feed
Real-time intercepts from Veea Lobster Trap with verdict badges, risk-score bars, and detected pattern chips.

> *[Screenshot: DPI Live Feed showing BLOCKED jailbreak attempt with 95 risk score]*

### Agent Swarm Simulator
Launch attacks, watch live event stream, and see incidents auto-generate in real time.

> *[Screenshot: Swarm running with 3 agents, Misbehavior Mode ON, 6 events, 3 blocked]*

### Judge Layer
Deterministic rule evaluation with zero LLM in the enforcement path.

> *[Screenshot: Judge Layer showing ALLOW vs DENY rationale with matched rules]*

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (or SQLite for local dev)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment Variables

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/playbook
SECRET_KEY=your-secret-key
RESEND_API_KEY=re_xxxxxxxx
NOTIFICATION_DEFAULT_RECIPIENTS=["security@company.com"]
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

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, asyncpg |
| Frontend | React 18.2, TypeScript, Tailwind CSS, Recharts, Lucide |
| Database | SQLite (dev) / PostgreSQL 15 (production) |
| DPI | [Veea Lobster Trap](https://github.com/veeainc/lobstertrap) |
| LLM Overlay | Gemini 3.1 Flash Lite via Vertex AI ADC (async reasoning only) |
| Email | Resend SMTP |
| Reverse Proxy | Caddy (auto HTTPS) |

---

## Documentation

See `projectdocs/` for full specification:

- `PLAYBOOK_Functional_Requirements.md` — Features FEAT-001 through FEAT-028
- `PLAYBOOK_Technical_Specification.md` — Architecture & data models
- `PLAYBOOK_API_Documentation.md` — REST API & WebSocket protocol
- `PLAYBOOK_Database_Schema.md` — 20 tables + 1 view
- `CUSTOM_POLICY_BUILDER_Design.md` — NIST ODP system design

---

## License

TBD

---

> **Built for the [lablab.ai TechEx Intelligent Enterprise Solutions](https://lablab.ai) hackathon.**
> Track: **Agent Security & AI Governance — Veea**
