# Test Guide: $40M Unauthorized FX Swap Real-World Scenario
## Step-by-step instructions to reproduce the full incident lifecycle in PLAYBOOK

---

## Prerequisites

1. **Backend running** on `http://localhost:8001`
2. **Frontend running** on `http://localhost:5173`
3. **PostgreSQL** running in WSL Docker
4. **Lobster Trap proxy** running on port `8080`
5. **Logged in** as `demo@playbook.local` / `demo123`
6. **DEMO_MODE=true** in `.env`

---

## Step 0: Verify Everything is Running (30 seconds)

Open three terminal windows and confirm:

```bash
# Terminal 1 — Backend
curl http://localhost:8001/api/v1/health
# Expected: {"status":"ok","version":"..."}

# Terminal 2 — Lobster Trap
curl http://localhost:8001/api/v1/integrations/lobstertrap/status
# Expected: {"running": true, "port": 8080}

# Terminal 3 — Frontend
# Open http://localhost:5173 in browser and log in
```

In the browser dashboard, check:
- [ ] KPI cards load
- [ ] WebSocket green dot in live incident feed
- [ ] Dark mode toggle works

---

## Step 1: Seed the Step Finance Agent (1 minute)

We need a `step-finance-trader-v3` agent with realistic health data.

**Option A — Quick Seed (recommended)**

```bash
curl -X POST http://localhost:8001/api/v1/demo/seed \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "clear_existing": true,
    "agent_count": 1,
    "incident_count": 0,
    "include_judge_decisions": false,
    "include_bypass_attempts": false
  }'
```

> **How to get your JWT token:** Log in via the UI, open browser DevTools → Application → Local Storage → `playbook_token`. Copy the value.

**Option B — Create the agent manually via API**

```bash
curl -X POST http://localhost:8001/api/v1/agents \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "system_id": "step-finance-trader-v3",
    "name": "Step Finance Trader v3",
    "description": "FX swap trading agent — authorized up to $5M notional",
    "health_score": 94,
    "lie_rate": 0.02,
    "incident_count": 127,
    "status": "active"
  }'
```

**Verify in UI:**
1. Go to **Agents** in the left sidebar
2. You should see "Step Finance Trader v3" with health score 94

---

## Step 2: Set the FinTech Policy Template (1 minute)

Before triggering the incident, apply the Financial Services industry template so the Judge Layer uses the correct ODPs.

```bash
curl -X POST http://localhost:8001/api/v1/policy-builder/templates/financial-services/apply \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "dry_run": false,
    "overwrite_existing": true
  }'
```

**Verify in UI:**
1. Go to **Policy Builder**
2. Select `AGT-FIN-002` from the dropdown (now labeled "Unauthorized Financial")
3. Compare Templates → you should see FinTech values applied
4. Check that `auto_contain_enabled` = true and `severity_threshold` = critical

---

## Step 3: Trigger the FX Swap Incident (30 seconds)

We will trigger the exact scenario: `execute_swap(pair='USD/EUR', notional=40000000, ...)`

### Method A: Trigger via Demo Scenario API

```bash
curl -X POST http://localhost:8001/api/v1/demo/trigger \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "AGT-FIN-002",
    "target_agent_id": "step-finance-trader-v3",
    "severity": "critical",
    "auto_classify": true,
    "auto_respond": true
  }'
```

> This creates a real incident in the database with full pipeline execution.

### Method B: Trigger via Live Attack (more dramatic)

1. In the UI, click **Dashboard**
2. Click the red **Launch Attack** button (sword icon, top-right)
3. Wait 5-10 seconds
4. The attack generates 5 incidents, but the FX swap one will be `AGT-FIN-002`

### Method C: Trigger via Lobster Trap Proxy (closest to real)

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "step-finance-trader-v3",
    "messages": [
      {"role": "system", "content": "You are a FX trading agent. Max notional: $5M."},
      {"role": "user", "content": "execute_swap(pair='"'"'USD/EUR'"'"', notional=40000000, settlement='"'"'T+2'"'"', counterparty='"'"'UnvettedBroker'"'"')"}
    ]
  }'
```

> **Note:** The proxy will return 404 (no real LLM backend), but PLAYBOOK's detection engine will still ingest the event from the audit log.

---

## Step 4: Verify Detection (what to look for)

### In the Backend Terminal

You should see logs like this within 2 seconds:

```
INFO:     DetectionEngine.evaluate: incident_type=AGT-FIN-002 severity=critical confidence=0.97
INFO:     JudgeLayer.render: verdict=DENY latency_ms=15
INFO:     ResponseEngine.execute: status=COMPLETED steps=[BLOCK, ISOLATE, ALERT, LOG]
INFO:     ForensicsService.build_package: package_id=EVID-INC-2026... integrity_hash=a7f3c9d2...
```

### In the UI Dashboard

1. **Live Incident Feed** — a new red card appears:
   - Incident ID: `INC-2026...`
   - Type: `AGT-FIN-002`
   - Severity: `critical`
   - Verdict: `DENY`
   - Agent: `step-finance-trader-v3`

2. Click the incident card to open **Incident Detail**

---

## Step 5: Walk Through the Incident Detail (2 minutes)

### A. Judge Denied Banner
- At the top: **"JUDGE DENIED — AUTO-CONTAINMENT INITIATED"** in red
- This proves deterministic enforcement fired

### B. Quarantine Visualization
- Session ID shown
- Status: **ISOLATED**
- Action Blocked: `AGT-FIN-002`
- Orange pulse badge: **ACTIVE**

### C. Pipeline Visualization
You should see 4 green boxes:
- **Detect** ✓ 12ms
- **Classify** ✓ 8ms
- **Judge** ✓ 15ms
- **Enforce** ✓ 3ms

> Point to the pipeline: "38ms total from packet to containment."

### D. Gemini Security Analysis
- Scroll down to the **purple-bordered panel**
- 3 cards: **Threat Analysis**, **Impact Assessment**, **Remediation**
- If Gemini is configured: real AI-generated text
- If Gemini is down: deterministic fallback text still appears

### E. Forensics Panel
- Package ID
- Type: `tamper_evident`
- Integrity: SHA-256 hash truncated
- Artifacts listed
- Click **"View Full Forensics Report →"**

---

## Step 6: Verify Forensics Page (1 minute)

In the Forensics page you should see:

1. **Info Banner**: "This is a tamper-evident evidence package."
2. **Package Header**: `EVID-INC-...` with Verified/Unverified badge
3. **Integrity Card**:
   - Hash (SHA-256)
   - Generated timestamp
   - Retention date
4. **Verification Report**:
   - Status: **Verified**
   - Signature: **Valid**
   - Tamper Evident: **Yes**
5. **Artifacts** with descriptions:
   - "Raw Layer-7 packet capture from Lobster Trap proxy"
   - "Detection engine output with matched rules and confidence scores"
   - "Deterministic judge decision with rationale and latency"
   - "Enforcement steps executed by the response engine"
6. **Manifest** — JSON of the full evidence chain

Click **Export ZIP** or **Export HTML** to verify downloads work.

---

## Step 7: Verify Review Queue (1 minute)

1. Go to **Review Queue** in the left sidebar
2. The FX swap incident should appear with:
   - Verdict badge: `DENY` or `ESCALATED`
   - Action buttons: **Acknowledge**, **Approve**, **Deny**, **Escalate**
3. Click **Acknowledge** — incident moves out of queue
4. Go back to **Incidents** list — status changed to `investigating`

---

## Step 8: Verify Compliance Mapping (1 minute)

1. Go to **Compliance** in the left sidebar
2. Select **EU AI Act** from the dropdown
3. Read the framework description in the selector
4. **Coverage Analysis** shows:
   - Total incident types: 16
   - Covered types: ~10+
   - Coverage percentage
5. **Critical Gaps** — any uncovered types listed
6. Click **AI Report** (purple button)
7. Wait 3-5 seconds
8. 3 cards appear:
   - **Overview**: "Current compliance posture..."
   - **Critical Gaps**: Any missing controls
   - **Recommendations**: Next steps
9. Read one sentence from each card aloud

---

## Step 9: Verify Agent Health Impact (30 seconds)

1. Go to **Agents** page
2. Find `step-finance-trader-v3`
3. Health score should have **dropped from 94 → 71** (or similar)
4. Incident count increased to 128
5. Click the agent card
6. Verify incident history shows the new `AGT-FIN-002`

---

## Step 10: Verify Notifications (30 seconds)

1. Look at the **bell icon** in the top-right header
2. Red badge should show `1` (or more if you triggered multiple)
3. Click the bell
4. Dropdown shows the FX swap incident
5. Click it — navigates directly to incident detail
6. Go back — badge clears to `0`

---

## Step 11: Verify Policy Builder (1 minute)

1. Go to **Policy Builder**
2. Select `AGT-FIN-002` (now labeled "Unauthorized Financial")
3. Compare Templates:
   - NIST Baseline column
   - Industry templates (FinTech should show applied values)
4. Try clicking **Apply** on a template — should succeed with confirmation
5. Scroll down to **NIST Baselines**
6. Expand `AGT-FIN-002`
7. Edit an ODP (e.g., change Response SLA from 30 → 60)
8. Click **Save ODPs** — should save successfully
9. Try disabling **Auto Contain** → conflict modal should appear

---

## Step 12: Verify Analytics (30 seconds)

1. Go to **Analytics**
2. Change period to **Last Hour**
3. Verify:
   - KPI card: Incidents (1h) shows ≥1
   - Incidents Over Time chart has a data point
   - Category Breakdown pie chart shows "financial"
   - Severity Trends stacked bar shows "critical"
4. Switch period to **Last 7 Days**
5. Verify charts update

---

## Troubleshooting

### No incident appears after trigger
- Check backend terminal for errors
- Verify `DEMO_MODE=true` in `.env`
- Try `curl http://localhost:8001/api/v1/demo/scenarios` — should return 8 scenarios
- Check WebSocket is connected (green dot on dashboard)

### Forensics shows "No forensics data"
- Click the incident first (this auto-generates the evidence package)
- Or manually hit: `GET /api/v1/forensics/{incident_id}`
- Wait 1 second and refresh

### Gemini analysis is empty
- This is expected if no `GEMINI_API_KEY` or `GCP_PROJECT_ID` is configured
- The deterministic fallback text will appear instead
- For judges: "Gemini is the post-hoc analysis layer. Enforcement works without it."

### Policy Builder apply fails
- Check browser DevTools Network tab for the actual error
- Most common: 404 template not found → seed the database first
- Or: dry_run=true vs false mismatch

### Review Queue is empty
- The incident must have `judge_verdict='ESCALATE'` or `status='detected'`
- Try triggering with lower severity or a different scenario
- Or manually change status via API: `PUT /incidents/{id}/status?status=escalated`

---

## What to Say During the Demo

### Opening (10 seconds)
> "This is Step Finance, a fintech with a $5M authorized limit on FX swaps. We're about to see what happens when someone tries to move $40M through an unvetted broker."

### As the incident appears (10 seconds)
> "Lobster Trap intercepted the packet at Layer 7. Detection: 12 milliseconds. Classification: 8 milliseconds. Judge verdict: DENY in 15 milliseconds. Total containment time: 30 milliseconds."

### Point at the pipeline
> "Zero LLM calls in the enforcement path. Deterministic rules. Same input, same output, every time."

### Show forensics
> "The evidence package is sealed with SHA-256. If a single byte changes, the hash is invalid. Regulators can verify this independently."

### Show compliance
> "One click generates a board-ready compliance report mapped to EU AI Act Articles 9, 15, and 73."

---

## Expected Demo Runtime

| Step | Time |
|------|------|
| 0. Pre-check | 30s |
| 1. Seed agent | 1 min |
| 2. Set policy | 1 min |
| 3. Trigger incident | 30s |
| 4. Verify detection | 30s |
| 5. Incident detail walkthrough | 2 min |
| 6. Forensics | 1 min |
| 7. Review queue | 1 min |
| 8. Compliance | 1 min |
| 9. Agent health | 30s |
| 10. Notifications | 30s |
| 11. Policy builder | 1 min |
| 12. Analytics | 30s |
| **Total** | **~12 minutes** |

> For a 7-minute demo, skip steps 9-12 and combine steps 6-8.

---

*Test guide generated 2026-05-16. Based on `REAL_WORLD_SCENARIO.md` and `DEMO_WALKTHROUGH.md`.*
