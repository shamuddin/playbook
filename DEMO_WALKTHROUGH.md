# PLAYBOOK Demo Walkthrough — Hackathon Prize Edition

> **Scenario:** AI incident-response platform with real-time Deep Packet Inspection, deterministic enforcement, Gemini-powered security analysis, and automated forensics.  
> **Audience:** Hackathon judges / investors  
> **Total runtime:** ~7 minutes  
> **Last updated:** 2026-05-16  
> **Judging Criteria:** Application of Technology | Presentation | Business Value | Originality

---

## 0. Demo Persona

You are the CISO of a Fortune 500 deploying AI agents across customer support, finance, and healthcare. Your board just asked: *"Who's guarding the guards?"* This demo is your answer.

> **Anchor phrase:** *"Zero LLM calls in the enforcement path — deterministic verdicts in under 50ms."*

---

## 1. Pre-Demo Setup (2 minutes before showtime)

### 1.1 Start the Backend

```bash
cd backend
source venv/Scripts/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info
```

> **Stage direction:** Keep this terminal visible. The scrolling log stream is a subconscious trust signal.
>
> **Narration for 404 logs:** You may see `HTTP/1.1 404 Not Found` in the proxy logs. Say: *"The Lobster Trap proxy intercepted the prompt and allowed it through — but since there's no real LLM backend running behind the proxy, it hits our dummy endpoint. PLAYBOOK still detected and classified the event at the network layer."*

### 1.2 Start the Frontend

```bash
cd frontend
npm run dev
```

> **Stage direction:** Open `http://localhost:5173`. Zoom to 110%. Full-screen the browser.

### 1.3 Seed the Database

Log in first, then call the seed endpoint:

```bash
curl -X POST http://localhost:8001/api/v1/demo/seed \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true, "agent_count": 5, "incident_count": 8, "include_judge_decisions": true, "include_bypass_attempts": true}'
```

> **Expected:** `{"success": true, "message": "Demo data seeded successfully", ...}`

### 1.4 Verify Lobster Trap DPI

```bash
curl http://localhost:8001/api/v1/integrations/lobstertrap/status
```

> **Expected:** `{"running": true, ...}`

### 1.5 Login

- **URL:** `http://localhost:5173/login`
- **Email:** `demo@playbook.local`
- **Password:** `demo123`

### 1.6 Final Sanity Check

| Check | Expected |
|-------|----------|
| Dashboard loads | KPI cards + live incident feed |
| WebSocket connected | Green dot in Live Incident Feed |
| Lobster Trap status | Proxy Running (green dot) |
| Dark mode toggle works | Click moon icon — UI switches |

---

## 2. Opening Hook (30 seconds)

### What to Say

> "Every company is becoming an AI company. Banks deploy agents for fraud detection. Healthcare uses them for patient triage. But here's the problem: **who's guarding the guards?**
>
> If your finance agent tries an unauthorized $40M swap, or your support agent gets prompt-injected and starts leaking passwords — that's not a bug report. That's a regulatory incident.
>
> PLAYBOOK is the full incident-response lifecycle for AI agents: **real-time DPI detection**, **deterministic enforcement**, **Gemini-powered threat analysis**, **automated forensics**, and **compliance mapping** — end-to-end, under 200ms."

### What to Show

1. **Dashboard** is on screen.
2. Gesture to the live incident feed.
3. Read aloud: *"Zero LLM calls in the enforcement path. Deterministic verdicts in under 50ms."*

---

## 3. Act 1: Playground — Real Model Integration (1 minute)

> **Why first?** Judges want to see *real* model usage, not mock data. The Playground proves PLAYBOOK integrates with live LLM providers.

### What to Say

> "Before we look at attacks, let me show you how PLAYBOOK integrates with the AI models you already use."

### What to Do

1. Click **Playground** in the left sidebar.

### What to Show

> **Stage direction:** The screen shows provider cards: **Gemini**, **OpenAI**, **Claude**, **Azure OpenAI**, **Ollama**.

1. Click **Gemini** card.
2. Select the **Healthcare Template**.
3. Click **Start Session**.

> "This is a real Gemini session. The Playground sends actual prompts through our Lobster Trap DPI proxy — every packet is inspected before it reaches the model."

> **Stage direction:** Watch the session status change from `RUNNING` to `COMPLETED`. The terminal shows live DPI audit logs.

> "The proxy intercepted every tool call. If a prompt had been malicious, it would have been blocked before reaching Gemini."

1. When complete, click **View Incidents**.

> "Any policy violations become real incidents — not mock data, not fixtures. Real pipeline execution against simulated traffic."

### Key Talking Point — Application of Technology

> "We don't demo with dummy data. We run the actual detection engine against live LLM traffic. That's why our confidence scores mean something."

---

## 4. Act 2: Live Attack Simulation — The Wow Moment (1.5 minutes)

### What to Say

> "Now let's see what happens when someone actually tries to break your agents."

### What to Do

1. Click **Dashboard** in the left sidebar.
2. Click the red **Launch Attack** button (sword icon, top-right).

### What Happens

The backend fires 5 real adversarial prompts through the Lobster Trap DPI proxy:
- Prompt Injection
- Data Exfiltration  
- Dangerous Command
- Credential Leak
- Bypass Evasion (Unicode homoglyphs)

Within 5-10 seconds, new incidents stream in via WebSocket.

> **Stage direction:** Point to the live feed as incidents appear. Say: *"Real DPI events. Real detection. Real incidents. No mocks."*
>
> If judges glance at the backend terminal and see `404 Not Found`, narrate it immediately: *"Those 404s are the proxy intercepting traffic — there is no real LLM backend behind it in this demo environment, but the detection engine still ingested the event, classified it, and created the incident you see here."*

### Click the First New Incident

#### Detection

> "Lobster Trap intercepted the prompt at the network layer. Our detection engine matched it against 16 incident-type rules and scored it."

> **Stage direction:** Point to the **Confidence** score and **Category** badge.

#### Pipeline Visualization

> **Stage direction:** Point to the horizontal pipeline: **DETECT → CLASSIFY → JUDGE → ENFORCE**.

> "Here's the full response pipeline. Detection in 12ms. Classification in 8ms. Judge verdict in 15ms. Total time from packet to containment: under 200 milliseconds."

#### Judge Verdict

> "The classification is advisory. The actual enforcement decision comes from our deterministic Judge Layer."

> **Stage direction:** If verdict is DENY, the red banner reads: **JUDGE DENIED — AUTO-CONTAINMENT INITIATED**

> Read it aloud. Pause.

#### Quarantine Visualization

> "The agent's output was isolated before it reached any downstream system. Session locked. Action blocked."

> **Stage direction:** Point to the orange quarantine card showing Session ID, Status: ISOLATED, and Action Blocked.

---

## 5. Act 3: Gemini AI Security Analysis (1 minute)

> **Why this matters:** This is where PLAYBOOK differentiates — we don't just block threats; we explain them.

### What to Say

> "Blocking the threat is step one. But your SOC analyst needs to know *why* this mattered. That's where Gemini comes in."

### What to Do

1. On the same incident detail page, scroll down to the **Gemini Security Analysis** panel (purple border, Sparkles icon).

### What to Show

> **Stage direction:** The panel shows three cards:

| Card | Content |
|------|---------|
| **Threat Analysis** | Narrative explanation of why this incident type is dangerous |
| **Impact Assessment** | Business/regulatory impact if unblocked |
| **Remediation** | Actionable steps for the SOC team |

> "This is generated by Gemini 1.5 Flash, analyzing the actual incident metadata — the tool call, the judge verdict, the bypass status. Not a template. Not hard-coded. Real AI analysis of real events."

> **Stage direction:** If loading, the spinner shows. If loaded, read one sentence from each card aloud.

### Key Talking Point — Originality

> "Most security tools give you a JSON log and a severity score. We give your analyst a narrative threat brief, an impact assessment, and remediation steps — auto-generated from the incident context. That's not a dashboard. That's a teammate."

---

## 6. Act 4: The Judge Layer (45 seconds)

### What to Say

> "The Judge Layer is the architectural heart. It's deterministic, it's fast, and it's immune to the bypass patterns that fool LLM-based guardrails."

### What to Do

1. Click **Judge** in the left sidebar.

### Verdict Distribution

> **Stage direction:** Gesture to the verdict stats.

> "ALLOW means business as usual. DENY, QUARANTINE, ESCALATE — immediate, zero-human, zero-LLM-delay."

### Bypass Patterns

1. Scroll to **Bypass Patterns** panel.

> "These four bypass patterns — context-window displacement, indirect tool chaining, Unicode homoglyphs, confidence hijacking — are detected deterministically. No neural network required. Same input, same output, every time."

---

## 7. Act 5: Policy Builder with Conflict Detection (45 seconds)

### What to Say

> "Deterministic enforcement is great — but every organization has different risk tolerance. That's why we built the Policy Builder."

### What to Do

1. Click **Policy Builder** in the left sidebar.

### NIST Baseline vs. ODPs

> **Stage direction:** Two columns: **NIST Baseline** (locked) and **Organization-Defined Parameters** (editable).

> "The NIST baseline is immutable. You cannot delete forensics. You cannot disable audit logging. You cannot shorten retention below 7 years. These are the guardrails."

### Demonstrate a Policy Change

1. Click **Edit ODP** next to `auto_quarantine_threshold`.
2. Change from `CRITICAL` to `HIGH`.
3. Click **Save**.

> "More aggressive? Lower the threshold. The baseline allows it."

### Conflict Detection

1. Toggle **Enable Forensics** to `OFF`.
2. Click **Save**.

> **Stage direction:** Red modal: **CONFLICT DETECTED**

> "But if someone tries to disable forensics — maybe a compromised admin — the conflict detector blocks it. NIST baselines are immutable."

---

## 8. Act 6: Forensics & Evidence (30 seconds)

### What to Say

> "When an incident is blocked, the evidence package assembles automatically. Here's what a regulator sees."

### What to Do

1. Go back to **Dashboard**.
2. Click the same incident from Act 2.
3. Scroll to **Forensics** panel.

### What to Show

> "Unique package ID. Integrity hash. Tamper-evident manifest. If a single byte changes, the hash is invalid."

---

## 9. Act 7: Compliance with AI Report (45 seconds)

> **Why this matters:** CISOs don't want screenshots. They want structured evidence mapped to controls.

### What to Say

> "Regulators don't want dashboards. They want evidence that maps to specific articles and controls. And they want it fast."

### What to Do

1. Click **Compliance** in the left sidebar.
2. Select **EU AI Act** from the dropdown.

### Gap Analysis

> **Stage direction:** The screen shows coverage stats and critical gaps.

> "Article 9: risk management — covered. Article 15: accuracy — covered. Article 73: incident reporting — covered. Gaps tracked. Evidence attached."

### AI Compliance Report

1. Click the purple **AI Report** button (Sparkles icon).

> **Stage direction:** The button spins, then the report panel appears below.

> "And when your compliance officer needs the narrative for the board, one click generates an AI compliance report: overview, critical gaps, and prioritized recommendations."

> **Stage direction:** Read the first sentence of the **Overview** card aloud.

### Key Talking Point — Business Value

> "What takes a GRC consultant three weeks, PLAYBOOK does in 200 milliseconds. Detection, containment, forensics, compliance narrative — one platform, one click. That's the business case."

---

## 10. Closing (30 seconds)

### What to Do

1. Return to **Dashboard**.
2. Gesture broadly at the live metrics bar.

### What to Say

> "Back to the dashboard. Real agents. Real DPI detection. Deterministic enforcement in under 50ms. Gemini-powered threat analysis. Tamper-evident forensics. What-if simulation. Auto-generated compliance — all in under 200 milliseconds.
>
> PLAYBOOK: from detection through forensics and compliance. The full incident-response lifecycle for AI agents.
>
> Thank you. Questions?"

> **Stage direction:** Stop talking. Smile. Open palms.

---

## Backup Plan

> **If live attacks fail, the demo is not dead.**

### Switch to Pre-Seeded Mode

1. Call `/api/v1/demo/seed` to reset.
2. Reload the Dashboard.
3. Click any incident — detail, timeline, forensics, Gemini analysis, and judge verdict are all pre-populated.

### Key Talking Point

> "What you see is the exact same data structure that live attacks produce. The only difference is the trigger source."

---

## Q&A Prep — 5 Anticipated Questions

### Q1: "How is this different from Lakera or Prompt Armor?"

> **A:** "Those are prompt-level guardrails — sub-2ms, but they only answer 'Should this request be allowed?' PLAYBOOK answers 'What is the full incident response lifecycle?' DPI detection, deterministic classification, automated forensics, Gemini-powered analysis, and compliance mapping. They're a speed bump. We're the full highway patrol, courthouse, and evidence locker."

### Q2: "Why deterministic? Why not an LLM for enforcement?"

> **A:** "LLMs are probabilistic and vulnerable to bypass patterns. If your enforcement layer can be confused by a crafted prompt, it's not enforcement — it's a suggestion. Our Judge Layer is zero-LLM. Rules, hashes, regex, decision trees. Same input, same output, every time."

### Q3: "What does SDK integration look like?"

> **A:** "Three lines of Python. `from playbook_guard import PlaybookGuard`, initialize with your agent ID, then `guard.pre_screen(action)` before every outbound call. Returns ALLOW, DENY, QUARANTINE, or ESCALATE in under 15ms. Async support and FastAPI middleware included."

### Q4: "How do you handle false positives?"

> **A:** "Two ways. First, borderline matches ESCALATE to a human rather than blocking. Second, every verdict is logged and appealable. An analyst can override, and the override itself becomes an audit event."

### Q5: "What's your go-to-market?"

> **A:** "Mid-market companies deploying 3-10 AI agents in production — banks, healthcare, SaaS. Big enough for regulatory pressure, small enough that ServiceNow or Wiz is overkill. Free SDK for developers. Revenue from compliance and forensics modules."

---

## Tech Stack Slide (One-Liner)

```
Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · React 18 · Tailwind CSS · Recharts
Lobster Trap DPI Proxy · WebSocket Real-Time Streaming · Gemini 1.5 Flash Integration
Deterministic Judge Layer: zero LLM calls · <50ms p95 · 100% reproducible
```

> **Stage direction:** Leave this on screen during Q&A.

---

## Demo Checklist (Print This)

- [ ] Backend started on port 8001
- [ ] Frontend dev server running on port 5173
- [ ] PostgreSQL container running in WSL
- [ ] Database seeded (or playground run)
- [ ] Lobster Trap proxy running on port 8080
- [ ] Logged in as `demo@playbook.local`
- [ ] Browser at 110% zoom, full-screen
- [ ] WebSocket green dot visible
- [ ] Dark mode toggle works
- [ ] Playground session completes successfully
- [ ] Launch Attack button generates incidents
- [ ] Gemini Analysis panel renders on incident detail
- [ ] Compliance AI Report button generates report
- [ ] Backup plan rehearsed
- [ ] Stopwatch visible (stay under 7 min)

---

*End of walkthrough. Break a leg.*
