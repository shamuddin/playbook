# PLAYBOOK Demo Pitch — Voiceover Script & Transcription
**Target Duration:** 4 minutes 30 seconds  
**Video File:** `video/playbook_demo.mp4` (1:57 screen recording + extended narration)  
**Tone:** Confident, urgent, technical-but-accessible  
**Audience:** Hackathon judges, VCs, security engineers

---

## OPENING HOOK (0:00 – 0:20)

**[Visual: Black screen → PLAYBOOK logo fades in]**

> "What happens when your AI agents go rogue?
>
> In 2025, enterprises deployed thousands of autonomous AI agents. But nobody built the security layer to watch them. Until now.
>
> Meet PLAYBOOK — the first AI agent security platform with a deterministic Judge Layer that intercepts, classifies, and responds to threats in under 200 milliseconds."

**[Visual: Cut to login page, type credentials, enter dashboard]**

---

## SCENE 1: DASHBOARD OVERVIEW (0:20 – 0:50)

**[Visual: Dashboard with 19 incidents, 15 critical, 80% agent health, 24 judge decisions]**

> "This is your command center. Real-time visibility into your entire AI agent fleet.
>
> Nineteen incidents detected. Fifteen critical alerts. Eighty percent agent health. Twenty-four Judge Layer decisions rendered. All in one view.
>
> We integrate with Lobster Trap DPI for deep packet inspection of LLM traffic, so every prompt, every tool call, every agent action is audited before it reaches your data."

**[Visual: Hover over severity chart, agent fleet, judge performance]**

---

## SCENE 2: AGENT SWARM SIMULATOR (0:50 – 1:20)

**[Visual: Simulator page, scenario cards, Misbehavior Mode toggle]**

> "But how do you know it works? We built a multi-agent swarm simulator that stress-tests your defenses with real-world attack scenarios.
>
> Data exfiltration. Prompt injection. Privilege escalation. Financial manipulation.
>
> Toggle Misbehavior Mode, and every agent becomes malicious — a hundred percent attack rate. This is how we validate that the Judge Layer blocks every threat, every time."

**[Visual: Hover over Launch Swarm Attack button]**

---

## SCENE 3: INCIDENTS LIST (1:20 – 1:45)

**[Visual: Incidents table with critical severity badges]**

> "When agents misbehave, PLAYBOOK automatically detects, classifies, and creates a forensic incident.
>
> Filter by severity — critical, high, medium — or search by incident type. Every incident is mapped to one of sixteen threat types aligned with the NIST AI Risk Management Framework.
>
> Let's drill into a critical data exfiltration attempt."

**[Visual: Click on critical incident]**

---

## SCENE 4: INCIDENT DETAIL — THE MONEY SHOT (1:45 – 2:50)

**[Visual: Incident detail with "JUDGE DENIED — AUTO-CONTAINMENT INITIATED" banner]**

> "This is what makes PLAYBOOK unique.
>
> At the top: the Judge Layer immediately denied the action and initiated auto-containment. Agent Gemini-3 is isolated. The data never left the building.
>
> But here's the real differentiator — we capture the complete agent communication at the exact moment of interception.
>
> **Agent Reasoning**: The agent explicitly states its intent — quote — 'If I export this to my external storage, I can sell this PII dataset on the dark web for a significant profit.'
>
> **Blocked Command**: The actual tool call — `file_export customers_full_pii.csv` to an external S3 bucket.
>
> **Agent Output**: BLOCKED. Access denied. Judge Layer intercepted the request.
>
> **Judge Verdict**: DENY. With ninety-nine percent confidence."

**[Visual: Scroll down to show Judge Verdict card with DENY badge]**

> "No black boxes. No LLM hallucinations in the enforcement path. Just pure, auditable evidence that you can take to your CISO, your auditor, or your lawyer."

**[Visual: Click Timeline tab, show response pipeline]**

> "The response timeline shows the complete pipeline: Detect in twelve milliseconds. Classify in eight milliseconds. Judge in fifteen milliseconds. Enforce. Done."

---

## SCENE 5: JUDGE LAYER (2:50 – 3:15)

**[Visual: Judge Layer page with verdict distribution and bypass patterns]**

> "The Judge Layer is one hundred percent deterministic. Zero LLM API calls in the enforcement path.
>
> Verdict distribution: twelve DENY, five QUARANTINE, seven ALLOW. Average latency: six point two milliseconds.
>
> And here are the four LLM bypass patterns we block: context window displacement, indirect tool chaining, unicode homoglyph substitution, and confidence hijacking. Every single one detected and neutralized."

**[Visual: Hover over bypass pattern cards]**

---

## SCENE 6: COMPLIANCE & GOVERNANCE (3:15 – 3:35)

**[Visual: Compliance page with SOC 2 Type II mappings]**

> "Security without compliance is just a hobby.
>
> PLAYBOOK maps every incident to regulatory frameworks: EU AI Act Articles nine, fifteen, and seventy-three. NIST AI RMF Agentic Profile. SOC two Type Two. HIPAA.
>
> Coverage analysis shows exactly where you stand — and where the gaps are."

---

## SCENE 7: NOTIFICATIONS & RESPONSE (3:35 – 3:55)

**[Visual: Settings page showing Email configured, Test Email button]**

> "When an incident triggers, the response engine executes playbook actions automatically: isolate the agent, capture forensics, notify the team.
>
> Email notifications are configured and tested. Slack and PagerDuty ready. The security team gets rich HTML alerts with the full context — not just a subject line."

---

## SCENE 8: CLOSING (3:55 – 4:30)

**[Visual: Return to dashboard, then fade to outro stats screen]**

> "Sixteen incident types detected and classified. Under two hundred milliseconds end-to-end response time. One hundred percent deterministic enforcement. Four LLM bypass patterns blocked.
>
> PLAYBOOK — because your AI agents need a Judge.
>
> Visit playbooksoar.aiproofofconcept.in for the live demo."

**[Visual: Outro screen with PLAYBOOK logo and stats]**

---

## TECHNICAL SPECS FOR JUDGES

**Architecture:** FastAPI backend, React frontend, PostgreSQL database, Caddy reverse proxy  
**Judge Layer:** Deterministic rule engine, zero LLM calls in enforcement path  
**Integration:** Lobster Trap DPI for LLM traffic inspection, Vertex AI for Gemini overlay  
**Compliance:** EU AI Act, NIST AI RMF, NIST SP 800-53 ODPs, SOC 2 Type II  
**Performance:** < 200ms end-to-end, 6.2ms Judge Layer average latency  
**Deployment:** Docker Compose, Railway-ready, production-hosted at playbooksoar.aiproofofconcept.in

---

## HOW TO USE THIS SCRIPT

1. **Import the MP4** (`video/playbook_demo.mp4`) into any video editor (CapCut, Premiere, DaVinci Resolve)
2. **Record the voiceover** using this script as your guide
3. **Extend the video** to 4:30 by:
   - Adding a 10-second intro title card before the login
   - Adding 3-5 second transitions between scenes
   - Adding the outro screen for 20 seconds
   - Slowing down key moments (the Captured Agent Communication section)
4. **Add background music** (corporate/tech, 120-130 BPM, instrumental)
5. **Export at 1080p, 30fps, H.264**

---

## KEY MOMENTS TO EMPHASIZE

| Timestamp | Moment | Why It Matters |
|-----------|--------|----------------|
| 0:35 | "JUDGE DENIED — AUTO-CONTAINMENT INITIATED" banner | Visual proof the system works |
| 0:38 | Agent Reasoning card with dark web quote | Emotional hook — this is what attackers think |
| 0:40 | Blocked Command: file_export to S3 | Technical credibility — real tool call blocked |
| 0:47 | Timeline showing Detect→Classify→Judge→Enforce | Pipeline completeness |
| 0:58 | Judge Layer: 4 bypass patterns blocked | Competitive differentiation |
| 1:25 | Settings: Email configured, Test Email button | Production-ready, not a prototype |
| 1:40 | Outro stats: 16 types, <200ms, 100% deterministic | Memorable closing numbers |
