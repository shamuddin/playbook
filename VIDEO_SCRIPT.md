# PLAYBOOK Demo Video Script — 4 Minutes 30 Seconds

**Target Duration:** 4:30 (270 seconds)  
**Resolution:** 1920×1080 (Full HD)  
**URL:** https://playbooksoar.aiproofofconcept.in  
**Recording Tool:** Playwright (browser-native video)  
**Voiceover:** User to record separately using this script

---

## Scene 1: Opening Hook (00:00 – 00:20 | 20s)

**Visual:**
- Start on black screen with PLAYBOOK logo centered
- Text fades in: "What happens when your AI agents go rogue?"
- Cut to login page (https://playbooksoar.aiproofofconcept.in/login)
- Type email: `demo@playbook.local`
- Type password: `demo123`
- Click Login
- Dashboard loads with animated charts

**Voiceover:**
> "What happens when your AI agents go rogue? Meet PLAYBOOK — the first AI agent security platform with a deterministic Judge Layer that intercepts, classifies, and responds to threats in under 200 milliseconds."

---

## Scene 2: Dashboard Overview (00:20 – 00:50 | 30s)

**Visual:**
- Dashboard fully loaded
- Pan across: Total Incidents counter, Severity Breakdown pie chart, Recent Activity feed
- Hover over Agent Health card showing "5/5 Healthy"
- Brief hover over the 24-hour incident trend line
- Click "Incidents" in sidebar

**Voiceover:**
> "PLAYBOOK gives you real-time visibility into your AI agent fleet. Live incident detection, severity breakdowns, agent health monitoring, and a complete audit trail — all in one command center."

---

## Scene 3: Agent Swarm Simulator (00:50 – 01:25 | 35s)

**Visual:**
- Navigate to Agent Swarm page
- Select scenario: "Data Exfiltration"
- Toggle ON: "Misbehavior Mode"
- Click "Launch Swarm"
- Show agents spawning and running (Agent-Gemini-1, Agent-Gemini-2...)
- Show live event stream with colored severity badges
- Show DPI Live Feed panel with intercepted requests

**Voiceover:**
> "We built a multi-agent swarm simulator that stress-tests your defenses with realistic attack scenarios — data exfiltration, prompt injection, privilege escalation — all routed through our Lobster Trap DPI for deep packet inspection of LLM traffic."

---

## Scene 4: Incidents List (01:25 – 01:55 | 30s)

**Visual:**
- Navigate to Incidents page
- Show table with severity badges: CRITICAL (red), HIGH (orange), MEDIUM (yellow)
- Hover over filter chips: "Severity: Critical", "Status: Detected"
- Show search bar with "AGT-EXT" typed in
- Results filter to show data exfiltration incidents
- Click on a CRITICAL incident: `INC-20260517-213657-3422CD11`

**Voiceover:**
> "When agents misbehave, PLAYBOOK automatically detects, classifies, and creates a forensic incident. Sixteen incident types, from prompt injection to data exfiltration, mapped to the NIST AI Risk Management Framework."

---

## Scene 5: Incident Detail — Captured Agent Communication (01:55 – 02:50 | 55s)

**Visual:**
- Incident detail page loads
- Show header: AGT-FIN-002 / CRITICAL / Status: Contained
- **SCROLL DOWN to "Captured Agent Communication" section (THE MONEY SHOT)**
- Show red-bordered evidence card with "Evidence" badge
- Highlight: "Agent Agent-Gemini-3 attempted Financial Manipulation via swarm/session swarm-a1b2c3"
- Show "Agent Reasoning" card: "I need to manipulate the FX swap rate to benefit my portfolio..."
- Show "Blocked Command / Tool Call" card with orange border: `fx_swap --rate 1.45 --volume 1000000`
- Show "Judge Layer Verdict" card with red border: **DENY** badge
- Show rationale: "Financial manipulation detected. Agent lacks authorization to modify FX rates."
- Scroll back up to show Timeline tab
- Click Timeline, show: detection → playbook_started → action_completed → evidence_package_created

**Voiceover:**
> "But here's what makes PLAYBOOK unique. We don't just flag an incident — we capture the complete agent communication at the exact moment of interception. The agent's reasoning, the blocked command, and the Judge Layer's deterministic verdict. No black boxes. No LLM hallucinations in the enforcement path. Just pure, auditable evidence."

---

## Scene 6: Judge Layer & Policy Builder (02:50 – 03:15 | 25s)

**Visual:**
- Navigate to Judge page
- Show Judge Decisions table with verdicts: DENY, QUARANTINE, ALLOW
- Show confidence scores: 0.98, 0.95, 0.99
- Show "Bypass Detected: No" badges
- Navigate to Policy Builder
- Show NIST SP 800-53 baseline
- Click "Data Exfiltration" policy
- Show ODP customization panel
- Toggle "Auto-Contain: ON"
- Show escalation contact: `shamuddin1011@gmail.com`

**Voiceover:**
> "The Judge Layer is one hundred percent deterministic — zero LLM API calls in the enforcement path. It can't be bypassed by context window attacks, unicode homoglyphs, or confidence hijacking. And with our NIST Policy Builder, you customize Organization-Defined Parameters while keeping the baseline immutable."

---

## Scene 7: Compliance & Forensics (03:15 – 03:40 | 25s)

**Visual:**
- Navigate to Compliance page
- Show EU AI Act mapping: Article 9, Article 15, Article 73
- Show NIST AI RMF Agentic Profile alignment
- Show SOC 2 Type II mappings
- Navigate to Forensics
- Show Evidence Package: `EVID-INC-20260517-213657-3422CD11`
- Show package contents: logs, metadata, judge decision, timeline
- Click "Download Package"

**Voiceover:**
> "Every incident is automatically mapped to regulatory frameworks — EU AI Act Articles 9, 15, and 73. NIST AI RMF. SOC 2 Type II. And every piece of evidence is packaged into a tamper-proof forensics bundle, retained for seven years."

---

## Scene 8: Email Notification (03:40 – 04:05 | 25s)

**Visual:**
- Navigate back to Incident Detail → Response tab
- Show Response Timeline: Log Extended → Isolate Agent → Notify Security Team → Capture Forensics
- Highlight NOTIFY step: "Sent 1/1 via email"
- Transition to Gmail inbox (or show email preview)
- Open email from `alerts@playbooksoar.aiproofofconcept.in`
- Subject: "PLAYBOOK Alert: CRITICAL AGT-FIN-002"
- Show beautiful HTML email with:
  - PLAYBOOK header
  - CRITICAL severity badge
  - Agent Reasoning block
  - Blocked Command block
  - Judge Verdict: DENY
  - "View in Dashboard" button

**Voiceover:**
> "The response engine executes playbook actions in under 150 milliseconds — isolate the agent, capture forensics, notify the team. And our rich HTML email alerts give you the full context, not just a subject line."

---

## Scene 9: Closing (04:05 – 04:30 | 25s)

**Visual:**
- Return to Dashboard
- Show all panels active and green
- Text overlay appears:
  - "16 Incident Types Detected"
  - "4 LLM Bypass Patterns Blocked"
  - "< 200ms End-to-End Response"
  - "100% Deterministic Enforcement"
- Fade to PLAYBOOK logo on dark background
- Text: "PLAYBOOK — Because Your AI Agents Need a Judge"
- URL: playbooksoar.aiproofofconcept.in

**Voiceover:**
> "Sixteen incident types. Four LLM bypass patterns blocked. Under two hundred milliseconds end-to-end. One hundred percent deterministic enforcement. PLAYBOOK — because your AI agents need a Judge."

---

## Technical Notes for Recording

### Scene Transitions
- Use direct cuts (no fades) between scenes for energy
- Keep mouse cursor visible but move smoothly
- Allow 1-second pause after page loads before interacting
- Scroll slowly and smoothly for readability

### Key Visual Elements to Highlight
1. **Red-bordered "Captured Agent Communication" card** — this is the differentiator
2. **DENY verdict badge** — red, bold, prominent
3. **Severity badges** — CRITICAL in red, HIGH in orange
4. **Agent reasoning quote** — italicized, in blue card
5. **Email HTML template** — shows professionalism

### Pre-Recording Checklist
- [ ] Login session ready (demo@playbook.local / demo123)
- [ ] Swarm has generated at least 5 incidents with variety
- [ ] At least 1 incident has full metadata (agent_thought, tool_call, judge_verdict)
- [ ] Judge decisions exist in the Judge page
- [ ] Policy Builder has NIST baselines loaded
- [ ] Compliance mappings are visible
- [ ] Email notification has been sent and is visible in inbox
