# PLAYBOOK Pitch — Quick Reference Card
**For live delivery or video recording. Print this or keep it on a second monitor.**

---

## THE ONE-LINER
> "PLAYBOOK is the first AI agent security platform with a deterministic Judge Layer that intercepts, classifies, and responds to threats in under 200ms."

---

## THE PROBLEM (15 sec)
- Enterprises deploy thousands of AI agents
- Nobody watches what they do
- Agent goes rogue → data exfiltration → regulatory fine → reputational damage
- Current guardrails (like SupraWall) only ask "should this request be allowed?"
- PLAYBOOK answers: "What is the full incident response lifecycle?"

---

## THE SOLUTION (30 sec)
- **Detect**: Lobster Trap DPI intercepts LLM traffic
- **Classify**: 16 incident types mapped to NIST AI RMF
- **Judge**: Deterministic layer — zero LLM calls in enforcement
- **Enforce**: Auto-containment, isolation, playbook execution
- **Forensics**: Complete evidence package, SHA-256 verified

---

## THE MONEY SHOT (45 sec)
**Show the incident detail page. Point at:**
1. Red "JUDGE DENIED" banner
2. Agent reasoning: "sell PII on dark web"
3. Blocked command: `file_export customers_full_pii.csv`
4. Judge verdict: DENY, 99% confidence
5. Response timeline: Detect→Classify→Judge→Enforce

**Say:** "This is not a mockup. This is the actual blocked agent communication. We captured the reasoning, the tool call, and the interception in real time."

---

## KEY NUMBERS TO MEMORIZE
| Metric | Value | Context |
|--------|-------|---------|
| Incident types | 16 | Aligned with NIST AI RMF |
| End-to-end latency | < 200ms | P95, hard ceiling 500ms |
| Judge Layer latency | 6.2ms avg | Deterministic, zero LLM |
| Playbook success rate | 100% | 17/17 active |
| Bypass patterns blocked | 4/4 | Context displacement, tool chaining, homoglyphs, confidence hijacking |
| Total decisions | 24 | Deny 50%, Quarantine 21%, Allow 29% |

---

## COMPETITIVE POSITIONING
| Competitor | What they do | What PLAYBOOK does |
|------------|--------------|-------------------|
| SupraWall (Apache 2.0) | Single-request guardrail (~1.2ms) | Full incident lifecycle |
| Swimlane Turbine | General SOC platform | AI-native pipeline |
| ServiceNow AI Control Tower | Governance dashboard | Runtime enforcement + forensics |
| Pragatix/AGAT | Runtime enforcement | Deterministic Judge Layer + ODPs |

**Say:** "SupraWall answers 'should this single request be allowed?' PLAYBOOK answers 'what is the full incident response lifecycle — from detection through forensics and compliance reporting?'"

---

## COMPLIANCE MAPPINGS
- EU AI Act (Articles 9, 15, 73)
- NIST AI RMF Agentic Profile
- NIST SP 800-53 ODPs
- NIST AI 600-1 GenAI Profile
- SOC 2 Type II
- HIPAA 45 CFR 164.306

---

## LIVE DEMO CHECKLIST
Before presenting, verify:
- [ ] Backend running: `docker compose ps` shows healthy
- [ ] Frontend accessible: https://playbooksoar.aiproofofconcept.in loads
- [ ] Login works: demo@playbook.local / demo123
- [ ] Dashboard loads with 19 incidents
- [ ] Incident detail shows Judge DENY verdict
- [ ] Judge Layer page shows 4 bypass patterns
- [ ] Compliance page loads
- [ ] Settings show Email configured
- [ ] Outro screen loads at /outro

---

## IF JUDGES ASK...

**"How is this different from a SIEM?"**
> "SIEMs log events. PLAYBOOK intercepts and enforces. The Judge Layer blocks actions before they execute. A SIEM tells you what happened. PLAYBOOK stops it from happening."

**"Why deterministic and not LLM-based?"**
> "Because LLMs can be bypassed. Context window displacement, confidence hijacking — we've proven it. Deterministic rules are immune. Zero LLM calls in the enforcement path."

**"What's the business model?"**
> "SaaS per-agent pricing. Enterprise tier includes custom Policy Builder with NIST ODPs. On-prem option for regulated industries."

**"Is this production-ready?"**
> "This IS production. Hosted on Railway. Docker Compose deployment. Caddy reverse proxy. PostgreSQL database. Resend email. Real incidents. Real verdicts."

**"What about false positives?"**
> "The Judge Layer allows legitimate traffic — 29.2% allow rate. The deterministic engine has tunable thresholds. For edge cases, we have a human review queue."

---

## CONTACT
- **Demo URL**: https://playbooksoar.aiproofofconcept.in
- **Login**: demo@playbook.local / demo123
- **Video**: `video/playbook_demo.mp4`
- **Script**: `PITCH_DECK_SCRIPT.md`
- **Transcription**: `VIDEO_TRANSCRIPTION.md`
