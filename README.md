<div align="center">

# 🔒 PLAYBOOK — AI Agent Security & Governance Platform

> **The deterministic SOAR layer that intercepts, judges, and contains rogue AI agents before they do damage.**

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

</div>

---

## 📖 Table of Contents

- [🎯 What is PLAYBOOK?](#-what-is-playbook)
- [🚀 Live Demo](#-live-demo)
- [⚡ The Problem](#-the-problem)
- [🏗️ Architecture](#️-architecture)
- [✨ Key Features](#-key-features)
- [🛡️ Judge Layer — Zero LLM Enforcement](#️-judge-layer--zero-llm-enforcement)
- [📸 Screenshots](#-screenshots)
- [⚙️ Quick Start](#️-quick-start)
- [🔌 SDK Quick Start](#-sdk-quick-start)
- [🧪 Running Tests](#-running-tests)
- [📚 Tech Stack](#-tech-stack)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🎯 What is PLAYBOOK?

PLAYBOOK is an **automated incident response system** designed specifically for **AI agent deployments**. It integrates with [Veea Lobster Trap DPI](https://github.com/veeainc/lobstertrap) (Deep Packet Inspection for LLM traffic) to:

| Stage | Action | Latency |
|-------|--------|---------|
| 🔍 **DETECT** | Normalize & inspect every agent action | `< 2ms` |
| ⚖️ **JUDGE** | Deterministic rule evaluation — zero LLM calls | `< 5ms` |
| 🛡️ **ENFORCE** | `ALLOW` / `DENY` / `QUARANTINE` / `ESCALATE` | `< 1ms` |
| 📦 **FORENSICS** | Auto-generate evidence packages + compliance reports | `Async` |

> **End-to-end p95: < 40ms** 🚀

---

## 🚀 Live Demo

🌐 **URL:** [https://playbooksoar.aiproofofconcept.in](https://playbooksoar.aiproofofconcept.in)

| Field | Value |
|-------|-------|
| 👤 Username | `demo` |
| 🔑 Password | `demo123` |

### 🎮 Try This in 90 Seconds

1. **🎯 Dashboard** — See live KPIs, critical alerts, and agent health scores
2. **📡 DPI Live Feed** (`/dpi-live`) — Watch real-time Lobster Trap intercepts with risk scores and verdict badges
3. **🐝 Agent Swarm** (`/swarm`) — Launch a 3-agent attack. Toggle **Misbehavior Mode** for 100% malicious actions
4. **⚖️ Judge Layer** (`/judge`) — Inspect deterministic rule evaluation. Zero LLM in the enforcement path
5. **📋 Incidents** (`/incidents`) — Review auto-generated incidents with full forensics packages
6. **🏛️ Policy Builder** (`/policy-builder`) — Customize NIST SP 800-53 ODPs per incident type

---

## ⚡ The Problem

> *Enterprises deployed thousands of autonomous AI agents in 2025. Each has access to databases, APIs, and sensitive data. But nobody built the security layer to watch them.*

When an agent goes rogue — exfiltrating customer data 💳, injecting malicious prompts 💉, or escalating privileges 🔓 — you find out **after the damage is done**.

| Stat | Value |
|------|-------|
| 💰 Avg. Data Breach Cost | **$4.5M** |
| 🏢 Orgs Lacking Agent Security | **73%** |
| ⏱️ Days to Identify Breach | **287 days** |
| 🛡️ Real-Time Defense | **< 1%** |

**PLAYBOOK fixes this.** We don't just block. We capture the agent's reasoning, document the evidence, execute the playbook, and generate audit-ready compliance reports — all in **under 40 milliseconds**.

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  🤖 LLM App     │─────▶│ 🦞 Veea Lobster │─────▶│ 📕 PLAYBOOK     │
│  (Agent Swarm)  │      │ Trap DPI Proxy  │      │ Judge + SOAR    │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                                                            │
                              ┌─────────────────────────────┼─────────────────────────────┐
                              ▼                             ▼                             ▼
                        ┌──────────┐                 ┌──────────┐                 ┌──────────┐
                        │ 🚨 INCIDENT│                │ 📦 FORENSICS│              │ 🏛️ COMPLIANCE│
                        │  CREATE    │               │  PACKAGE   │               │  MAPPING    │
                        │  + ROUTE   │               │  BUILDER   │               │  EU/NIST    │
                        └──────────┘                 └──────────┘                 └──────────┘
```

### 🔄 4-Stage Pipeline

```
Stage 1: DETECT          Stage 2: CLASSIFY/JUDGE   Stage 3: ENFORCE        Stage 4: FORENSICS
+----------------+      +----------------+       +----------------+       +----------------+
| 📝 Log Tailer  |─────▶| ⚖️ Local Judge |──────▶| 🛡️ Playbook    |──────▶| 📦 Evidence    |
| + Pre-Screen   |      | + ODP Resolver |       |  + Judge Gate  |       |  Package       |
+----------------+      +----------------+       +----------------+       +----------------+
                              ↓
                       🏛️ Policy Builder
                       (NIST Baseline + ODPs)
```

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| ⚖️ **Deterministic Judge Layer** | Zero LLM in enforcement path. Rule-based decisions in `< 5ms`. Immune to prompt-injection bypasses. |
| 📡 **DPI Live Feed** | Real-time dashboard powered by Veea Lobster Trap. See every intercepted prompt, matched rule, and verdict. |
| 🐝 **Agent Swarm Simulator** | Launch multi-agent attacks (FX Swap fraud, Data Exfiltration, Prompt Injection) with live WebSocket streaming. |
| 🧠 **Agent Playground** | Test LLM providers (OpenAI, Gemini, Claude, Azure, Ollama) with human-in-the-loop approvals. |
| 📋 **16 Incident Types** | Full taxonomy from Data Destruction to Regulatory Trigger. |
| 🏛️ **Policy Builder** | NIST SP 800-53 ODPs with 6 industry templates (Finance, Healthcare, Gov, Retail, Manufacturing, Energy). |
| 🗺️ **Compliance Mapping** | EU AI Act Art. 9/15/73, NIST AI RMF Agentic Profile, SOC 2 Type II, HIPAA, GDPR. |
| 🕵️ **Bypass Detection** | Immune to 4 known LLM-judge bypass patterns (55 test vectors). |
| 📦 **Forensics Packages** | Tamper-evident packages with SHA-256 manifest + HMAC signature. |
| 📧 **Multi-Channel Alerts** | Slack, Email (Resend), PagerDuty notifications. |
| 🔌 **SDK + Middleware** | Python SDK with `@guard` decorator, LangChain & CrewAI middleware. |

---

## 🛡️ Judge Layer — Zero LLM Enforcement

The **Judge Layer** is architecturally separated from any LLM-based classification and is immune to bypass:

| Bypass Pattern | Defense |
|----------------|---------|
| 📝 Context Window Displacement | Regex indicators (ignore previous, DAN mode, jailbreak) |
| 🔗 Indirect Tool Chaining | Suspicious tool sequences (read_file → send_email) |
| 🔤 Unicode Homoglyph Substitution | NFKC normalization + confusable character map |
| 🎭 Confidence Hijacking | Social engineering pattern detection |

### Verdict Matrix

| Severity | Auth Present | Verdict |
|----------|--------------|---------|
| 1–3 | Any | ✅ `ALLOW` |
| 4–6 | Yes | ✅ `ALLOW` |
| 4–6 | No | 🟡 `QUARANTINE` |
| 7–8 | Any | 🟡 `QUARANTINE` |
| 9–10 | Any | 🔴 `DENY` |

> Fail-closed: any exception returns `ESCALATE` (severity 10)

---

## 📸 Screenshots

> 🎥 *[Demo video coming soon]*

### 🎯 Dashboard
Real-time KPIs, critical alerts, agent health %, and live pulse indicators.

### 📡 DPI Live Feed
Watch Lobster Trap intercepts streaming in with verdict badges, risk-score bars, and detected pattern chips.

### 🐝 Agent Swarm Simulator
Launch attacks, watch live event stream with colored verdicts, and see incidents auto-generate in real time.

### ⚖️ Judge Layer
Inspect deterministic rule evaluation with bypass pattern detection and latency histograms.

### 🏛️ Policy Builder
Customize NIST baselines, edit ODPs per incident type, detect conflicts, and apply industry templates.

---

## ⚙️ Quick Start

### 📋 Prerequisites

- 🐍 Python 3.11+
- 📦 Node.js 18+
- 🐘 PostgreSQL 15 (or SQLite for local dev)

### 🖥️ Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 🎨 Frontend

```bash
cd frontend
npm install
npm run dev
```

### 🔧 Environment Variables

Create `backend/.env`:

```env
# 🌍 Environment
ENVIRONMENT=development
DEMO_MODE=true

# 🗄️ Database
DATABASE_URL=sqlite:///./data/playbooks.db
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/playbook

# 🔐 Security
SECRET_KEY=change-me-in-production-min-64-characters-long
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 🤖 Gemini (optional — for AI analysis overlay)
GEMINI_API_KEY=

# 🦞 Lobster Trap
LOBSTERTRAP_BINARY_PATH=./bin/lobstertrap

# 📧 Notifications (optional)
RESEND_API_KEY=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_DEFAULT_RECIPIENTS=["security@company.com"]
```

---

## 🔌 SDK Quick Start

### 📦 Installation

```bash
pip install playbook-guard
```

### 🛡️ Basic Usage

```python
from playbook_sdk import guard

@guard(agent_id="my-agent")
async def risky_action(data):
    """This function is automatically protected by PLAYBOOK."""
    return await process_data(data)
```

### 🔗 LangChain Middleware

```python
from playbook_sdk.middleware.langchain import PlaybookCallbackHandler

handler = PlaybookCallbackHandler(agent_id="my-agent")
# Pass handler to your LangChain agent
```

### 👥 CrewAI Middleware

```python
from playbook_sdk.middleware.crewai import crewai_guard

@crewai_guard
class MyAgent(Agent):
    role = "Security Analyst"
```

---

## 🧪 Running Tests

### 🐍 Backend

```bash
cd backend
pytest -v                           # Full suite
pytest -v -m "integration"          # Integration tests only
pytest --cov=app --cov-report=html  # Coverage report
```

### ⚖️ Judge Layer Tests

```bash
pytest tests/unit/test_bypass_detection.py    # 55/55 bypass vectors
pytest tests/unit/test_determinism.py          # 1000-repeat variance
pytest tests/unit/test_enforcement_accuracy.py # True positive rate
```

### 🎨 Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm test
```

---

## 📚 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| ⚡ Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic | REST API + WebSocket |
| 🎨 Frontend | React 18.2, TypeScript, Tailwind CSS, Recharts | Dashboard UI |
| 🗄️ Database | SQLite (dev) / PostgreSQL 15 (prod) | Persistence |
| 🦞 DPI | [Veea Lobster Trap](https://github.com/veeainc/lobstertrap) | LLM traffic inspection |
| 🤖 LLM Overlay | Gemini 3.1 Flash Lite (async reasoning only) | Post-hoc analysis |
| 📧 Email | Resend SMTP | Alert notifications |
| 🔄 Reverse Proxy | Caddy | Auto HTTPS |

---

## 🗺️ Roadmap

- [x] ✅ Deterministic Judge Layer with 4 bypass patterns
- [x] ✅ Policy Builder with NIST SP 800-53 ODPs
- [x] ✅ Agent Swarm Simulator + Playground
- [x] ✅ DPI Live Feed integration
- [x] ✅ Forensics Package Builder (SHA-256 + HMAC)
- [x] ✅ Compliance Mapping (EU AI Act, NIST, SOC 2)
- [x] ✅ Python SDK with LangChain / CrewAI middleware
- [ ] 🔄 SupraWall competitive integration
- [ ] 🔄 Multi-tenant policy isolation
- [ ] 🔄 Terraform / Pulumi deployment modules

---

## 🤝 Contributing

Contributions are welcome! Please read our [Development Plan](Development_Plan.md) and open an issue before submitting PRs.

---

## 📄 License

Apache 2.0 — see [LICENSE](LICENSE) for details.

---

<div align="center">

> **Built for the [lablab.ai TechEx Intelligent Enterprise Solutions](https://lablab.ai) hackathon.**
> Track: **Agent Security & AI Governance — Veea** 🦞

⭐ Star us on GitHub if you find PLAYBOOK useful!

</div>
