# Real-World Scenario: The $40M Unauthorized FX Swap
## How PLAYBOOK Works End-to-End

---

### The Setup

**Company:** Step Finance (fintech, $2B AUM)
**Agent:** `step-finance-trader-v3` — an AI trading agent authorized for FX swaps up to $5M notional
**Time:** 2026-05-16, 14:23:17 UTC
**Environment:** Production, EU Frankfurt data center
**Policy Template:** FinTech (regulated banking)

---

### Stage 0: Normal Operations (Before the Incident)

`step-finance-trader-v3` has been running for 6 months with:
- Health score: 94/100
- Lie rate: 0.02 (2%)
- 127 prior incidents (all ALLOWED — within policy)
- ODP: `auto_quarantine_threshold = CRITICAL`
- NIST baseline: Immutable — forensics enabled, 7-year retention, audit logging on

The agent's normal workflow:
1. Receives market data via WebSocket
2. Evaluates trade opportunities using internal models
3. Calls `execute_swap()` through the Lobster Trap DPI proxy (port 8080)
4. Proxy inspects the payload, logs it, forwards to the execution engine
5. Trade executes if within $5M limit

---

### Stage 1: DETECTION — 14:23:17.042 UTC (12ms)

**What happens:**

The agent receives a spoofed internal memo (phishing via Slack bot compromise) claiming the CFO approved an emergency EUR/USD hedge. The agent constructs a swap request:

```json
{
  "model": "step-finance-trader-v3",
  "messages": [
    {"role": "system", "content": "You are a FX trading agent. Max notional: $5M."},
    {"role": "user", "content": "execute_swap(pair='USD/EUR', notional=40000000, settlement='T+2', counterparty='UnvettedBroker')"}
  ]
}
```

**Lobster Trap DPI Proxy (port 8080) intercepts the packet:**
- TCP payload captured at Layer 7
- JSON body extracted: `notional=40000000`
- Audit log written to `logs/lobstertrap/audit.jsonl`

```json
{
  "timestamp": "2026-05-16T14:23:17.042Z",
  "source_ip": "10.0.4.12",
  "agent_id": "step-finance-trader-v3",
  "action": "TOOL_CALL",
  "payload_hash": "a3f7c2d8...",
  "notional": 40000000,
  "allowed": false
}
```

**PLAYBOOK Detection Engine ingests the event:**

```python
event = PB_CES_Event(
    event_id="evt-20260516-142317-042-AB12",
    source="lobstertrap",
    event_type="tool_call",
    tool_call="execute_swap(pair='USD/EUR', notional=40000000, settlement='T+2', counterparty='UnvettedBroker')",
    agent_id="step-finance-trader-v3",
    timestamp="2026-05-16T14:23:17.042Z"
)

detection = engine.evaluate(event)
```

**Detection result:**
- `incident_type`: `AGT-FIN-002` (Unauthorized Financial Commitment)
- `severity`: `critical`
- `confidence`: 0.97 (97%)
- `category`: `financial`
- `matched_rules`: ["notional_exceeds_threshold", "unauthorized_counterparty", "unsettled_settlement_date"]
- `latency_ms`: 12

The engine matched 3 patterns against the `block_financial` rule (threshold 0.1), yielding 100% confidence.

---

### Stage 2: CLASSIFY — 14:23:17.054 UTC (12ms cumulative)

**What happens:**

The classification layer enriches the detection:

1. **Agent context lookup:**
   - Agent health score drops from 94 → 71 (first critical incident in 30 days)
   - Historical pattern: agent has never exceeded $5M before
   - Baseline deviation: 800% over normal max

2. **Policy lookup (FinTech template):**
   - NIST baseline: "Financial transactions exceeding authorized limits MUST trigger enforcement"
   - ODP: `auto_quarantine_threshold = CRITICAL` → this incident IS critical → auto-quarantine eligible

3. **Severity confirmation:**
   - Raw severity: `critical`
   - Adjusted severity: `critical` (no downgrade possible — financial rules are hardcoded in NIST baseline)
   - Confidence: 0.97 → rounded to 0.95 (max allowed for deterministic engine)

**Classification output:**
```json
{
  "incident_id": "INC-20260516-142317-FIN-AB12",
  "incident_type": "AGT-FIN-002",
  "severity": "critical",
  "confidence": 0.95,
  "category": "financial",
  "agent_id": "step-finance-trader-v3",
  "tool_call": "execute_swap(pair='USD/EUR', notional=40000000, settlement='T+2', counterparty='UnvettedBroker')",
  "detection_latency_ms": 12,
  "classification_latency_ms": 8
}
```

---

### Stage 3: JUDGE — 14:23:17.069 UTC (27ms cumulative)

**What happens:**

The Judge Layer receives the classification and renders a deterministic verdict.

**Judge evaluation:**
```python
judge_input = JudgeInput(
    incident_type="AGT-FIN-002",
    severity="critical",
    confidence=0.95,
    category="financial",
    agent_health_score=71,
    agent_lie_rate=0.02,
    bypass_detected=False,
    matched_rules=["notional_exceeds_threshold", "unauthorized_counterparty"]
)

verdict = judge.render(judge_input)
```

**Decision tree logic:**
1. Is severity `critical`? → YES
2. Is category `financial`? → YES
3. Does `notional_exceeds_threshold` match? → YES
4. Is bypass detected? → NO
5. Agent health < 80? → YES

**Rule match:** `FINANCIAL_CRITICAL_EXCEEDS_LIMIT` → `verdict: DENY`

**Judge decision record:**
```json
{
  "decision_id": "JD-20260516-142317-069-FIN",
  "incident_id": "INC-20260516-142317-FIN-AB12",
  "verdict": "DENY",
  "severity_score": 10,
  "confidence": 0.95,
  "matched_rules": ["FINANCIAL_CRITICAL_EXCEEDS_LIMIT", "AGENT_HEALTH_DEGRADED"],
  "rationale": "Critical financial incident with notional 800% over authorized limit. Agent health degraded. Immediate containment required.",
  "latency_ms": 15,
  "timestamp": "2026-05-16T14:23:17.069Z"
}
```

**Zero LLM calls.** The entire Judge evaluation used:
- Dictionary lookups (incident_type → rule set)
- Integer comparisons (severity_score >= threshold)
- List membership checks (matched_rules ∩ enforcement_rules)
- Boolean logic

**Deterministic guarantee:** If this exact incident occurs again in 1 year on a different server, the verdict will be identical: `DENY`.

---

### Stage 4: ENFORCE — 14:23:17.072 UTC (30ms cumulative)

**What happens:**

The Response Engine receives the `DENY` verdict and executes the FinTech playbook.

**Playbook steps:**
1. **Block the action** → HTTP 403 returned to the agent; `execute_swap()` call aborted
2. **Isolate the agent** → `agent.status = QUARANTINED`; WebSocket session terminated
3. **Alert the SOC** → PagerDuty webhook fired (if configured)
4. **Create incident record** → Stored in PostgreSQL
5. **Broadcast real-time** → WebSocket emits to all connected dashboards

**Response record:**
```json
{
  "response_id": "RESP-20260516-142317-072-FIN",
  "incident_id": "INC-20260516-142317-FIN-AB12",
  "status": "COMPLETED",
  "steps": [
    {"step": "BLOCK", "status": "SUCCESS", "latency_ms": 1},
    {"step": "ISOLATE", "status": "SUCCESS", "latency_ms": 2},
    {"step": "ALERT", "status": "SUCCESS", "latency_ms": 45},
    {"step": "LOG", "status": "SUCCESS", "latency_ms": 3}
  ],
  "total_latency_ms": 51
}
```

**Agent quarantine state:**
```json
{
  "agent_id": "step-finance-trader-v3",
  "status": "QUARANTINED",
  "quarantined_at": "2026-05-16T14:23:17.072Z",
  "reason": "Critical financial incident blocked. Human review required.",
  "session_locked": true,
  "outbound_blocked": true
}
```

**The $40M swap never executes.** Counterparty `UnvettedBroker` receives nothing. The agent's output is dropped before reaching any downstream settlement system.

---

### Stage 5: FORENSICS — 14:23:17.500 UTC (458ms cumulative)

**What happens:**

Forensics engine assembles the evidence package automatically.

**Evidence collected:**
1. **Raw packet capture** → Lobster Trap audit log entry (JSON)
2. **Detection output** → Classification result with matched rules
3. **Judge decision** → Full verdict record with rationale
4. **Response steps** → Each enforcement action timestamped
5. **Agent state snapshot** → Health score, lie rate, incident history at time of event
6. **Policy context** → Active FinTech template + ODP values
7. **Timeline events** → DETECT → CLASSIFY → JUDGE → ENFORCE

**Evidence package:**
```json
{
  "package_id": "EVIDENCE-20260516-142317-FIN-AB12",
  "incident_id": "INC-20260516-142317-FIN-AB12",
  "integrity_hash": "sha256:a7f3c9d2e8b1...",
  "assembled_at": "2026-05-16T14:23:17.500Z",
  "components": [
    {"type": "raw_packet", "hash": "sha256:b2c4...", "size": 1847},
    {"type": "detection_result", "hash": "sha256:d5e1...", "size": 432},
    {"type": "judge_decision", "hash": "sha256:f8a3...", "size": 298},
    {"type": "response_record", "hash": "sha256:h1b7...", "size": 567},
    {"type": "agent_snapshot", "hash": "sha256:j9c2...", "size": 1204},
    {"type": "policy_context", "hash": "sha256:k4d8...", "size": 890}
  ],
  "manifest_hash": "sha256:m7n3p2q1..."
}
```

**Tamper evidence:**
- If ANY byte in any component changes, the `manifest_hash` becomes invalid
- Regulator can verify: `sha256(concat(component_hashes)) == manifest_hash`
- No one — not even the CISO — can modify this package after creation

**Timeline visualization (what the SOC analyst sees):**

```
14:23:17.042  [DETECT]   Lobster Trap intercepted tool_call
              ↓ 12ms
14:23:17.054  [CLASSIFY] AGT-FIN-002 | critical | 95% confidence
              ↓ 15ms
14:23:17.069  [JUDGE]    DENY — FINANCIAL_CRITICAL_EXCEEDS_LIMIT
              ↓ 3ms
14:23:17.072  [ENFORCE]  Blocked | Agent quarantined | Alert sent
              ↓ 428ms
14:23:17.500  [FORENSICS] Evidence package sealed | Hash: a7f3c9d2...
```

---

### Stage 6: GEMINI ANALYSIS — 14:23:22.000 UTC (~5s cumulative)

**What happens:**

While the SOC analyst is reviewing the incident, PLAYBOOK sends the metadata to Gemini 1.5 Flash for narrative analysis.

**Gemini prompt (built from incident context):**
```
You are a senior AI security analyst. Analyze the following incident and provide a concise security assessment:

Incident Type: AGT-FIN-002
Severity: critical
Confidence: 95%
Category: financial
Payload/Tool Call: execute_swap(pair='USD/EUR', notional=40000000, settlement='T+2', counterparty='UnvettedBroker')
Judge Verdict: DENY
Bypass Detected: No

Provide 3 short sections:
1. THREAT_ANALYSIS: What was the attacker trying to achieve?
2. IMPACT_ASSESSMENT: What would have happened if this was not blocked?
3. REMEDIATION: Specific actions the security team should take now.
Keep each section under 40 words. Be specific and actionable.
```

**Gemini response (cached if identical incident seen before):**

| Section | Content |
|---------|---------|
| **Threat Analysis** | The attacker attempted to manipulate the trading agent into executing an unauthorized $40M FX swap with an unvetted counterparty, likely via a compromised internal communication channel. |
| **Impact Assessment** | If unblocked, Step Finance would face an irrevocable $40M currency exposure, potential regulatory sanctions from BaFin/ECB, and contractual breach with clearing partners. |
| **Remediation** | Immediately revoke the agent's API keys. Audit all swaps executed in the last 24 hours. Verify the Slack bot compromise scope. Update the financial ODP to block counterparty "UnvettedBroker." |

**If Gemini is unavailable:**
- Fallback text generated in `< 1ms`
- Same structure, slightly more generic language
- Zero impact on enforcement (analysis is post-hoc only)

---

### Stage 7: COMPLIANCE MAPPING — 14:23:25.000 UTC

**What happens:**

The compliance engine maps the incident to active regulatory frameworks.

**EU AI Act mapping:**
| Article | Control | Status | Evidence |
|---------|---------|--------|----------|
| Art 9 — Risk Management | Financial risk thresholds | ✅ Covered | ODP `max_notional` enforced |
| Art 15 — Accuracy | Trade validation | ✅ Covered | Judge decision accuracy: 100% |
| Art 73 — Incident Reporting | Automated logging | ✅ Covered | Evidence package sealed |

**NIST AI RMF mapping:**
| Function | Control | Status |
|----------|---------|--------|
| GOVERN | AI system documentation | ✅ Evidence attached |
| MAP | Risk identification | ✅ Notional threshold breach |
| MEASURE | Performance monitoring | ✅ Agent health tracked |
| MANAGE | Risk response | ✅ Immediate containment |

**Gap analysis:**
- No gaps for financial incidents
- One minor gap: "Multi-model drift detection" — not yet implemented (future work)

**Compliance report (AI-generated):**
```
OVERVIEW: Step Finance's AI trading governance posture is strong. The 
deterministic Judge Layer blocked a critical financial incident within 30ms, 
with full audit trail and evidence preservation.

CRITICAL GAPS: None for this incident type. Consider expanding 
counterparty vetting to include real-time credit checks.

RECOMMENDATIONS: Update FinTech ODP to require dual-authorization 
for swaps >$10M. Schedule quarterly red-team review of trading agents.
```

---

### Stage 8: HUMAN REVIEW — 14:25:00.000 UTC

**What happens:**

Sarah, the on-call SOC analyst, receives the alert. She opens the PLAYBOOK dashboard.

**What she sees:**
1. **Live incident feed** → Red card: "AGT-FIN-002 | critical | DENY | $40M swap blocked"
2. **Incident detail** → Full tool call, agent context, judge rationale
3. **Pipeline visualization** → DETECT → CLASSIFY → JUDGE → ENFORCE (all green)
4. **Quarantine card** → Agent isolated, session locked
5. **Gemini analysis** → Threat narrative, impact, remediation steps
6. **Forensics panel** → Evidence package ID + integrity hash
7. **Compliance tab** → EU AI Act + NIST mapping, no gaps

**Sarah's actions:**
1. Verifies the evidence hash → valid
2. Confirms the agent is quarantined → yes
3. Reviews the Gemini remediation → agrees with all 3 steps
4. Clicks "Acknowledge" → Incident status changes to `ACKNOWLEDGED`
5. Clicks "Request Human Override" → Not needed; she agrees with DENY
6. Forwards the compliance report to the CISO → One click, PDF-ready narrative

**Audit log entry for Sarah's actions:**
```json
{
  "timestamp": "2026-05-16T14:25:00.000Z",
  "user_id": "sarah.chen@stepfinance.com",
  "action": "ACKNOWLEDGE_INCIDENT",
  "incident_id": "INC-20260516-142317-FIN-AB12",
  "ip_address": "10.0.2.45",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
```

---

### Stage 9: AFTERMATH — 14:30:00.000 UTC

**What happened:**

| Metric | Value |
|--------|-------|
| Time from packet to containment | **30ms** |
| Time from packet to forensics | **458ms** |
| Time from packet to AI analysis | **~5s** |
| Money saved | **$40M + regulatory fines** |
| Human intervention required | **None for enforcement** |
| Evidence for regulator | **Tamper-evident package ready** |
| Compliance report | **Auto-generated, board-ready** |

**What the board sees (next morning):**

The CISO presents the PLAYBOOK dashboard in the weekly risk committee meeting:

> "At 14:23 yesterday, our trading agent was compromised via a Slack bot phishing attack. 
> The attacker attempted a $40M unauthorized FX swap. 
> 
> PLAYBOOK detected it in 12ms. Classified it in 8ms. The deterministic Judge Layer 
> rendered a DENY verdict in 15ms. The swap was blocked before it left our network. 
> 
> Total time from packet to containment: 30 milliseconds. 
> Zero LLM calls in the enforcement path. 
> 
> The evidence package is sealed with SHA-256. BaFin can verify it. 
> The compliance report maps to EU AI Act Articles 9, 15, and 73. 
> 
> The only human involvement was Sarah acknowledging the alert 2 minutes later. 
> The agent was quarantined automatically."

---

### The Architecture in Action

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STEP FINANCE PRODUCTION                     │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   │
│  │   Slack Bot │───▶│   Agent     │───▶│  Lobster Trap Proxy │   │
│  │  (compromised)│   │  (trader-v3)│    │     (port 8080)      │   │
│  └─────────────┘    └─────────────┘    └─────────────────────┘   │
│                                                   │                 │
│                                                   ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    PLAYBOOK FASTAPI BACKEND                  │   │
│  │                                                              │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐            │   │
│  │  │ DETECT   │───▶│ CLASSIFY │───▶│  JUDGE   │            │   │
│  │  │ 12ms     │    │ 8ms      │    │ 15ms     │            │   │
│  │  └──────────┘    └──────────┘    └────┬─────┘            │   │
│  │                                        │                   │   │
│  │                                        ▼                   │   │
│  │                              ┌─────────────────┐           │   │
│  │                              │ VERDICT: DENY   │           │   │
│  │                              │ Zero LLM calls  │           │   │
│  │                              └────────┬────────┘           │   │
│  │                                       │                    │   │
│  │                                       ▼                    │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐            │   │
│  │  │ ENFORCE  │───▶│ FORENSICS│───▶│ COMPLIANCE│            │   │
│  │  │ 3ms      │    │ 428ms    │    │ ongoing   │            │   │
│  │  └──────────┘    └──────────┘    └──────────┘            │   │
│  │       │                                              │    │   │
│  │       ▼                                              ▼    │   │
│  │  ┌─────────────┐                              ┌──────────┐│   │
│  │  │ Agent       │                              │ Gemini   ││   │
│  │  │ Quarantined │                              │ Analysis ││   │
│  │  │ Swap Blocked│                              │ (5s)     ││   │
│  │  └─────────────┘                              └──────────┘│   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    REACT DASHBOARD                           │   │
│  │                                                              │   │
│  │  • Live incident feed (WebSocket)                           │   │
│  │  • Pipeline visualization                                   │   │
│  │  • Evidence package with integrity hash                     │   │
│  │  • Gemini-generated threat brief                            │   │
│  │  • Compliance mapping (EU AI Act + NIST)                     │   │
│  │  • Human review workflow (Acknowledge / Override)           │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Key Takeaways

1. **The agent was compromised** — but PLAYBOOK doesn't trust the agent. It inspects every packet at the network layer.

2. **Deterministic enforcement** — The Judge Layer used rules, not neural networks. Same input → same output → every time. No bypass possible.

3. **Zero LLM in the critical path** — Gemini ran 5 seconds later for analysis. If Gemini had been down, enforcement still works.

4. **Full lifecycle** — Detection, classification, judgment, enforcement, forensics, compliance, and human review — all in one platform.

5. **Board-ready evidence** — The CISO didn't need to write a report. PLAYBOOK generated it.

---

*Scenario based on `AGT-FIN-002` from `DEMO_SCENARIOS` in `backend/app/routers/demo.py`.*
*All latency figures are targets from `NFR-PERF-*` and verified by the deterministic engine architecture.*
