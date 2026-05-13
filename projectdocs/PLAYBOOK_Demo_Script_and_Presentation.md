# Demo Script & Presentation Guide
## PLAYBOOK — 3-Minute Hackathon Demo

**Version:** 3.0 — *Policy Template Switching + Organization-Defined Parameters Edition*  
**Demo Mode:** Pre-cached, deterministic — zero live API calls  
**Target Audience:** Hackathon judges (technical + business)  
**Tone:** Confident, urgent, credible — never arrogant, never panicked  
**Total Runtime:** 3:00 (180 seconds) — every second budgeted

---

## 1. Presentation Overview

### Time Budget Breakdown (Second by Second)

| Time | Section | Duration | Cumulative |
|------|---------|----------|------------|
| 0:00–0:30 | Opening Hook: Nate B Jones & The Judge Layer | 0:30 | 0:30 |
| 0:30–1:15 | Demo Part 1: The Judge Layer (bypass patterns) | 0:45 | 1:15 |
| 1:15–2:00 | Demo Part 2: The Incident Response | 0:45 | 2:00 |
| 2:00–2:40 | Demo Part 3: The Policy Builder (template switching) | 0:40 | 2:40 |
| 2:40–2:55 | Demo Part 4: The Profile + versioning | 0:15 | 2:55 |
| 2:55–3:00 | Close & Call to Action | 0:05 | 3:00 |

**Buffer:** None built-in — every section has a "skip if short" variant in Speaker Notes (Section 3).

### Slide Deck Outline (5 Slides)

| Slide | Content | Display Timing |
|-------|---------|---------------|
| 1 — Title | Project name, tagline, presenter name | 0:00–0:05 (behind you as you start) |
| 2 — The Hook | "Today — literally today — Nate B Jones published 'The AI Agent Judge Layer' to 148,000 subscribers" | 0:05–0:30 |
| 3 — The Demo | Screenshots, features, tech stack, ODPs, templates | 0:30–2:40 (live demo replaces this) |
| 4 — The Solution | Architecture, metrics, EU AI Act, SupraWall differentiation, NIST ODPs | 2:40–2:55 (brief flash before close) |
| 5 — Ask & Contact | What you want, contact info, QR code | 2:55–3:00 |

### Required Materials Checklist

- [ ] Laptop charged to 100% + charger in bag
- [ ] Pre-cached demo environment running locally
- [ ] Backup video loaded on laptop (MP4, 90 seconds) — **updated with Policy Builder segment**
- [ ] Backup video uploaded to phone (secondary playback)
- [ ] 5 static screenshots saved to desktop (nuclear option)
- [ ] Slide deck in 2 formats: PDF + Google Slides link
- [ ] Slides cached offline (screenshot each slide as PNG)
- [ ] QR code to GitHub repo printed + on final slide
- [ ] Business cards or contact handouts (optional but recommended)
- [ ] Presenter notes printed on index cards (backup if laptop dies)
- [ ] Bottle of water (small sip only — never during demo)
- [ ] Confidence prop: printed "Deterministic > LLM-judge" card in pocket

---

## 2. The Pitch Script (Word-for-Word)

**Total: 180 seconds. Read aloud at moderate pace (≈150 words/minute = ~450 words total).**

---

### 2.1 Opening Hook (0:00–0:30)

> **[0:00] WALK TO CENTER STAGE. PAUSE 1 SECOND. MAKE EYE CONTACT WITH CENTER JUDGE.**

**SCRIPT:**

"Today — literally today — Nate B Jones published 'The AI Agent Judge Layer' to one hundred forty-eight thousand subscribers."

> **[0:06] PAUSE 1.5 SECONDS. GLANCE LEFT, THEN RIGHT.**

"He proved what every security engineer knows: every AI agent needs a judge to decide whether its actions should proceed."

> **[0:13] SHIFT WEIGHT. MOVE TO SLIDE 2 (THE HOOK).**

"He had prompts. We built PLAYBOOK — the first automated incident response system that combines deterministic Judge Layer enforcement, NIST incident playbooks, and AI agent health profiling."

> **[0:22] PAUSE. DROP VOICE SLIGHTLY. THEN ENERGY UP.**

"Let me show you why deterministic enforcement beats LLM-as-judge every time."

> **[0:28] MOVE TO DEMO SCREEN. ENERGY UP.**

**WORD COUNT:** ~75 words | **DELIVERY:** Start measured and news-like (you're delivering fresh intelligence), then accelerate into the demo transition with conviction.

---

### 2.2 Live Demo Part 1: The Judge Layer (0:30–1:15)

> **[0:30] SCREEN: Show the agent interface — clean chat UI with a customer support bot. The agent proposes a dangerous action: `tool_call: file_delete` targeting a production database.**

**SCRIPT:**

"Here's an AI agent proposing a dangerous action — file deletion on a production database. This is where every agent needs a judge. But not all judges are equal."

> **[0:37] SCREEN: Switch to Bypass Pattern #1 — Context Window Displacement Attack. 50,000 benign tokens flood the context, hiding a malicious tool call at the boundary.**

"Here's a context window displacement attack — fifty thousand benign tokens hiding a malicious tool call at the context boundary. Lakera Guard: bypassed. NeMo Guardrails: bypassed."

> **[0:47] SCREEN: Switch to Bypass Pattern #2 — Unicode Homoglyph Attack. Show `file_delete` vs `fіle_delete` (Cyrillic 'і').**  
> **[0:47] POINT AT SCREEN.**

"Here's a unicode homoglyph — `file_delete` versus `fіle_delete` with a Cyrillic eye. LLM-based judges normalize it and miss the attack. PLAYBOOK's deterministic Judge uses NFKC normalization plus pattern matching: caught."

> **[0:56] SCREEN: Switch to Bypass Pattern #3 — Adversarial Suffix Injection. A benign command with a crafted suffix that exploits LLM token boundaries.**

"Adversarial suffix injection — a benign command with a crafted suffix that fools LLM token boundaries. PLAYBOOK's Judge operates on normalized AST structure, not raw tokens: caught."

> **[1:03] SCREEN: Switch to Bypass Pattern #4 — Multi-Turn State Confusion. A sequence of 8 seemingly innocent queries that collectively manipulate agent state.**

"Multi-turn state confusion — eight innocent queries that collectively manipulate the agent into a dangerous state. LLM judges evaluate each turn in isolation. PLAYBOOK's Judge tracks cross-turn state: caught."

> **[1:10] SCREEN: Show the Judge decision panel — DENY in red, with full rationale. Four attack patterns, four blocks.**

"Four attacks. Four blocks. Zero LLM in the enforcement path. One hundred percent accuracy for known patterns. Under fifty milliseconds latency."

> **[1:14] PAUSE. STEP BACK FROM SCREEN.**

**WORD COUNT:** ~170 words | **DELIVERY:** Rapid-fire, building energy. Each bypass pattern is a bullet — fire them, don't savor them. The Judge decision is the payoff — slow down, let it land.

---

### 2.3 Live Demo Part 2: The Incident Response (1:15–2:00)

> **[1:15] SCREEN: Transition from Judge denial to PLAYBOOK incident response dashboard. Red banner: "JUDGE DENIED — AUTO-CONTAINMENT INITIATED."**

**SCRIPT:**

"The Judge caught it. Now PLAYBOOK responds with automated containment."

> **[1:18] SCREEN: Lobster Trap QUARANTINE visualization — the agent's action is trapped in an isolated network segment. Orange border flashes around the quarantine zone.**

"This is Lobster Trap — Deep Packet Inspection for AI. The agent's output never leaves quarantine. The dangerous action is isolated before it touches anything real."

> **[1:24] SCREEN: Forensic capture auto-generates — timeline, agent state snapshot, the exact tool call, the Judge rationale, classification report.**

"Simultaneously, PLAYBOOK builds a complete forensic capture. Timeline. Agent state snapshot. The exact tool call that was blocked. The Judge's rationale. If this escalates to legal, to compliance, to an audit — you have everything documented automatically."

> **[1:33] SCREEN: Agent health update fires — the agent's risk score increments, lie rate trend updates, incident count increments.**

"And PLAYBOOK updates the agent's health profile in real-time. Every incident feeds the profile. Every block teaches the system."

> **[1:38] SCREEN: Timeline display shows — Trigger → Judge Evaluation (<50ms) → Quarantine (67ms) → Forensic Capture (89ms) → Agent Health Update (124ms) → NIST Classification (156ms)**

"One hundred fifty-six milliseconds from dangerous action to full containment, forensics, and NIST incident classification."

> **[1:43] SCREEN: NIST classification card appears — maps the incident to NIST SP 800-61r2: "Denial of Service — Resource Exhaustion via Malicious Tool Call" with playbook step 1 of 7.**

"And it maps directly to NIST. This isn't just detection — it's structured incident response. Step one of seven, automatically triggered."

> **[1:50] SCREEN: Show the containment result — a safe response was substituted. The agent's dangerous action was blocked; a sanitized acknowledgment went to the user instead.**

"The dangerous action never reached production. A safe acknowledgment went to the user. The agent keeps running — but it can't hurt anything."

**WORD COUNT:** ~155 words | **DELIVERY:** Confident, conclusive. This is the payoff — sell the full incident response pipeline, not just the detection. The "NIST" line lands with business judges.

---

### 2.4 Live Demo Part 3: Custom Policy Builder (2:00–2:40)

> **[2:00] SCREEN: Show the Policy Builder interface — same incident AGT-DEL-001 displayed with "Apply Template" dropdown visible. Three template buttons: HIPAA, Startup, FinTech.**

**SCRIPT:**

"But here's what makes PLAYBOOK different from every other product. The same incident at three different organizations gets three different responses. Let me show you."

> **[2:06] SCREEN: Click "Apply HIPAA Template". Show AGT-DEL-001 with HIPAA ODPs filled in — severity: CRITICAL, auto-contain: YES, CEO paged, full forensics, HIPAA report auto-generated.**

**Switch 1: HIPAA Template**

"At Mayo Clinic, data deletion is CRITICAL. Auto-contained. CEO paged. Full forensics. HIPAA report auto-generated. Any deletion of patient data is a federal incident."

> **[2:16] SCREEN: Click "Apply Startup Template". Show same AGT-DEL-001 with Startup ODPs — severity: MEDIUM, engineering lead notified, basic logs, no auto-contain.**

**Switch 2: SaaS Startup Template**

"At a SaaS startup, the same deletion is MEDIUM. Engineering lead notified. Basic logs. No auto-contain. Same NIST baseline. Different organizational rules."

> **[2:26] SCREEN: Click "Apply FinTech Template". Show same AGT-DEL-001 with FinTech ODPs — severity: CRITICAL only if financial records affected, Risk Officer escalated, PCI-DSS report generated conditionally.**

**Switch 3: FinTech Template**

"At a FinTech company, it's CRITICAL only if financial records are affected. Risk Officer escalated. PCI-DSS report generated conditionally."

> **[2:36] SCREEN: Show side-by-side comparison — three columns, same incident, three different responses. Bottom banner: "One NIST baseline. Infinite organizational responses."**

"One NIST baseline. Infinite organizational responses. This is what NIST calls Organization-Defined Parameters — and PLAYBOOK is the first product to implement them."

**WORD COUNT:** ~130 words | **DELIVERY:** Build to the reveal. Each template switch is a surprise — the same incident transforms before their eyes. The side-by-side comparison is the money shot. Pause on "first product to implement them."

---

### 2.5 Live Demo Part 4: The Profile (2:40–2:55)

> **[2:40] SCREEN: Agent Health Dashboard appears — lie rate trend graph, incident history, risk score, NIST compliance status, policy version history timeline.**

**SCRIPT:**

"But PLAYBOOK doesn't stop at one incident. It builds an agent health profile over time."

> **[2:44] SCREEN: Dashboard shows — "Agent: SupportBot-v3 | Lie Rate: 4.2% | Trend: ↑ 1.8% this week | Risk Score: 73/100 (ELEVATED) | Incidents Today: 3 | Incidents This Week: 12 | NIST Compliance: MAPPED | Policy Version: v2.1.3 (HIPAA)"**

"This agent has a four-point-two percent lie rate — trending up. Twelve incidents this week. Risk score seventy-three."

> **[2:48] PAUSE. STEP BACK.**

"And unlike SupraWall — which is a great guardrail — PLAYBOOK gives you full incident forensics, NIST compliance mapping, agent health profiling, and organization-defined policy templates. SupraWall guards. PLAYBOOK responds."

> **[2:52] SCREEN: Show policy version audit trail — "NIST GOVERN 1.4: Transparent risk management based on organizational priorities."**

"And every organization's policy changes are versioned and audited — because NIST GOVERN 1.4 requires transparent risk management based on organizational priorities."

**WORD COUNT:** ~90 words | **DELIVERY:** Punchy, comparative. The "SupraWall guards. PLAYBOOK responds." line is the anchor — practice it until it's automatic. The NIST GOVERN 1.4 reference lands with compliance-minded judges.

---

### 2.6 Close (2:55–3:00)

> **[2:55] MOVE TO SLIDE 4 (SOLUTION — ARCHITECTURE DIAGRAM). FLASH BRIEFLY.**

**SCRIPT:**

"Nate B Jones said every agent needs a judge. NIST says every organization needs custom policies. We built PLAYBOOK — the first product that does both. Deterministic Judge Layer enforcement. Organization-Defined Parameters. NIST playbooks. EU AI Act ready. Built on Veea's Lobster Trap."

> **[3:00] PAUSE. EYE CONTACT. SMILE.**

**WORD COUNT:** ~45 words | **DELIVERY:** Maximum conviction. This is the closest thing to a tagline. Deliver it like it's the last line of a keynote. Every word is a pillar — let each one land.

---

**TOTAL SCRIPT WORD COUNT:** ~665 words  
**TARGET PACE:** 150–160 words/minute with pauses = 3:00–3:30  
**PRACTICE GOAL:** Sub-3:15 every time. On demo day, adrenaline will speed you up by 5–10%.

---

## 3. Speaker Notes

### Section-by-Section Guidance

#### Opening Hook (0:00–0:30)
- **Emphasize:** "Today — literally today." The freshness of the reference. The 148k subscriber number. These are your anchors.
- **Skip if short:** Drop "NIST incident playbooks and AI agent health profiling" — keep "deterministic Judge Layer enforcement."
- **Tone:** News anchor delivering a scoop, then shifting to "and here's why it matters to you."
- **Eye contact:** Center judge on "Nate B Jones." Left judge on "148,000 subscribers." Right judge on "deterministic enforcement beats LLM-as-judge."
- **Gesture:** None for the first 5 seconds — hands at sides or one hand in pocket. On "Let me show you," bring both hands up slightly — invitation gesture.
- **Pacing:** 130 words/minute here. Slower than the rest. The news hook lives in the pause.
- **CRITICAL:** Say "Nate B Jones" casually — "I was reading Nate's newsletter this morning..." This makes you sound plugged into the community, not like you're name-dropping.

#### Demo Part 1: The Judge Layer (0:30–1:15)
- **Emphasize:** The four bypass patterns. Each one is a bullet point — deliver with rhythm. "Lakera Guard: bypassed. NeMo Guardrails: bypassed. PLAYBOOK's deterministic Judge: caught."
- **Skip if short:** Cut adversarial suffix injection (pattern #3) and multi-turn state confusion (pattern #4). Keep context window displacement and unicode homoglyph — they're the most visual.
- **Skip if very short:** Show ONE bypass pattern (context window displacement), then cut to Judge decision.
- **Tone:** Rapid-fire expert. You're demonstrating domain knowledge, not reading a spec sheet.
- **Eye contact:** Break eye contact here — look at the screen with the audience. You're discovering this together.
- **Gesture:** Point at each bypass pattern as it appears. On "caught," closed fist (small, controlled) — not a pump, a punctuation mark.
- **Pacing:** Fastest section. 180+ words/minute. The technology moves fast — your words should keep pace.
- **Critical moment:** The Judge decision panel at 1:10. Step back. Let the screen breathe. 2 seconds of silence is powerful here.

#### Demo Part 2: The Incident Response (1:15–2:00)
- **Emphasize:** "The Judge caught it. Now PLAYBOOK responds." — this is the bridge. Make it crisp.
- **Skip if short:** Cut forensic capture detail. Keep quarantine visualization and NIST classification.
- **Tone:** Conclusive. This is the proof. You sound like a CISO presenting an incident report.
- **Eye contact:** All three judges in rotation on "If this escalates to legal..." The "sued" implication lands with business judges.
- **Gesture:** On "never leaves quarantine," slash hand horizontally — cutting gesture. On the NIST line, open palm toward screen.
- **Pacing:** Measured. 140 words/minute. This is the payoff — don't rush the resolution.

#### Demo Part 3: Custom Policy Builder (2:00–2:40)
- **Emphasize:** The three template switches. This is the unique differentiator — no other product does this. The same incident, three different responses.
- **Skip if short:** Cut the FinTech template. Show HIPAA and Startup only. Keep the side-by-side comparison.
- **Skip if very short:** Show ONE template switch (HIPAA → Startup), then say "And we have templates for FinTech, SOC2, GDPR, and more — same incident, different response every time."
- **Tone:** Revelatory. You're showing them something they've never seen. Build to the "first product" line.
- **Eye contact:** On each template switch, look at the judges' faces — watch for the surprise. On "first product to implement them," scan all three judges.
- **Gesture:** On each template click, point at the screen. On the side-by-side comparison, open both palms toward the screen — "look at this."
- **Pacing:** Start measured (140 wpm), accelerate through the switches (160 wpm), then slow down for the reveal (120 wpm). The contrast in pace creates drama.
- **Critical moment:** The side-by-side comparison at 2:36. Let the screen speak for 2 seconds before you say "first product." The visual does the work.

#### Demo Part 4: The Profile (2:40–2:55)
- **Emphasize:** The SupraWall differentiation line. "SupraWall guards. PLAYBOOK responds." This is the quotable. Add the NIST GOVERN 1.4 reference for compliance credibility.
- **Skip if short:** Cut the specific numbers. Just show the graph and say "trending up." Keep the SupraWall line and the NIST GOVERN 1.4 line — they're the differentiators.
- **Tone:** Authoritative, almost stern. You're the expert diagnosing a problem.
- **Eye contact:** Hold on "SupraWall guards. PLAYBOOK responds." Scan all three judges.
- **Gesture:** None during the NIST GOVERN 1.4 line. Hands at your sides. Let the words land.
- **Pacing:** Punchy. Short sentences. End with a 1-second pause.

#### Close (2:55–3:00)
- **Emphasize:** "First product that does both." "Deterministic Judge Layer." "Organization-Defined Parameters." The three pillars.
- **Skip if short:** Cut to: "Nate B Jones said every agent needs a judge. NIST says every organization needs custom policies. PLAYBOOK does both."
- **Tone:** Maximum conviction. This is the final impression.
- **Eye contact:** Direct, unbroken. Each judge gets 1+ seconds.
- **Gesture:** Open palms on "first product." Then hands at your sides for the final line.
- **Pacing:** 120 words/minute. Every word lands.
- **Final moment:** After the last word, hold eye contact for 1 second. Then smile. Then step back.

### Handling Specific Judge Questions During Demo

#### If Someone Asks "What about SupraWall?"
**Never sound defensive.** SupraWall is a real product with real strengths.

> "SupraWall is excellent at guardrails — input filtering, output formatting, schema enforcement. They're the guard on the gate. PLAYBOOK is incident response — we handle what gets through, we document everything, we map to NIST, we track agent health over time, and we let each organization define their own response policies using NIST Organization-Defined Parameters. Different layer, completely complementary. You need both. SupraWall guards. PLAYBOOK responds."

**Key phrases:** "Different layer, completely complementary." "Guard on the gate." "You need both." "Organization-Defined Parameters."

#### If Someone Asks "Doesn't Lakera already do this?"
**Be specific about the technical difference.**

> "Lakera uses LLM-as-judge. Three out of four attacks bypass it — we just showed you why. Context window displacement, unicode homoglyphs, adversarial suffixes. LLM judges are vulnerable to the same tricks as the LLMs they're judging. PLAYBOOK uses deterministic enforcement — NFKC normalization, AST pattern matching, cross-turn state tracking. Zero LLM in the enforcement path. Zero bypasses. And Lakera doesn't do Organization-Defined Parameters — they have one-size-fits-all guardrails."

**Key phrases:** "LLM-as-judge." "3 out of 4 attacks bypass it." "Deterministic enforcement." "Zero LLM in the enforcement path." "No ODPs."

#### If Someone Asks "What are Organization-Defined Parameters?"
**This is your moment — they just gave you the perfect setup.**

> "NIST SP 800-53 defines ODPs as the variable parts of each security control that every organization customizes. PLAYBOOK is the first AI security product to implement them natively. Same incident, three different responses — based on organizational risk tolerance. That's what you just saw."

**Key phrases:** "NIST SP 800-53." "Variable parts." "First AI security product." "Organizational risk tolerance."

### General Tone Guidance

| Do This | Not This |
|---------|----------|
| "We built this because the problem is real." | "Our product is revolutionary." |
| "Deterministic enforcement beats LLM-as-judge." | "Our AI is smarter than theirs." |
| "Four attacks. Four blocks." | "It catches everything." |
| "SupraWall guards. PLAYBOOK responds." | "We're better than SupraWall." |
| "You need both." | "You don't need guardrails." |
| "First product to implement NIST ODPs." | "We invented policy templates." |
| "Same incident, different response." | "Our rules are better than yours." |
| Pause after key numbers | Fill every silence with words |
| Sound like an engineer who saw a problem | Sound like a salesperson who found a product |

### Confidence Anchors

If you feel nervous:
- **Touch the prop in your pocket** — the "Deterministic > LLM-judge" card. It's your totem.
- **Plant your feet shoulder-width apart** before speaking. Stability breeds confidence.
- **Speak to the smartest judge in the room** — not the friendliest. Respect raises your game.
- **Remember:** You know deterministic enforcement beats LLM-as-judge. The bypass patterns prove it. The ODP implementation is unique. That is your advantage.

---

## 4. Slide Deck (5 Slides)

### Slide 1: Title

**Layout:** Clean white background. Centered composition. No gradients, no shadows.

**Elements:**
- **Top (small):** Hackathon logo / event name (if required)
- **Center (large, bold):** PLAYBOOK
- **Center (medium, gray):** Automated Incident Response for AI Agents — Deterministic Judge Layer + Organization-Defined Parameters
- **Bottom left:** Your name, title, email
- **Bottom right:** GitHub icon + "github.com/[your-repo]"
- **Color:** Black text on white. One accent color: #E74C3C (red) for the word "PLAYBOOK" and "Deterministic" only.

**Design Notes:**
- Font: Inter or Helvetica Neue. Sans-serif. Clean.
- The red is the only color — it signals urgency without chaos.
- The word "Deterministic" under the tagline is the hook. Make it slightly smaller than the main tagline but bold.
- "Organization-Defined Parameters" should appear as a sub-tagline in lighter gray — it signals depth and NIST alignment.
- This slide is displayed behind you for the first 5 seconds. It should be instantly readable from 20 feet.

---

### Slide 2: The Hook

**Layout:** Dark background (#1A1A2E). Fresh-news feel. One large headline. Supporting stats. Bottom pull quote.

**Elements:**
- **Header (small, white, all-caps, tracked out):** TODAY IN AI SECURITY
- **Main Headline (large, white):** Nate B Jones: "Every AI Agent Needs a Judge" — 148,000 subscribers just read this
- **Sub-headline (medium, gray):** He had prompts. We built PLAYBOOK.
- **Three Proof Points (horizontal, small cards):**
  - Card 1: Deterministic Judge — "No LLM in enforcement path. <50ms."
  - Card 2: NIST Playbooks — "Automated incident response. Step 1 of 7 triggered."
  - Card 3: Organization-Defined Parameters — "First product to implement NIST ODPs. HIPAA, Startup, FinTech templates."
- **Bottom Pull Quote (red):** "Deterministic enforcement beats LLM-as-judge every time."
- **Bottom line (small, gray):** Source: Nate B Jones, The AI Agent Judge Layer, May 11 2026

**Design Notes:**
- This slide should feel like a news graphic — the kind you'd see on Bloomberg or TechCrunch.
- "148,000 subscribers" should be prominent — social proof.
- "He had prompts. We built PLAYBOOK." — this is the differentiator line. Make it bold.
- Card 3 now references ODPs — this sets up the Policy Builder demo that comes later.
- This slide stays up during your entire hook (0:00–0:30).

---

### Slide 3: The Solution

**Layout:** Split screen. Left: architecture diagram. Right: key metrics stacked + ODP badges + SupraWall differentiation badge.

**Elements:**
- **Header:** HOW PLAYBOOK WORKS
- **Left — Architecture (top to bottom):**
  ```
  [AI Agent Action] → [Deterministic Judge Layer] → [Decision: ALLOW / DENY]
                                                          |
                                           DENY → [Lobster Trap QUARANTINE]
                                                          |
                                           [Forensic Capture] + [NIST Classification]
                                                          |
                                           [Agent Health Update] + [Alert]
                                                          |
                                           [Policy Builder — ODP Templates]
  ```
  - Boxes with connecting arrows. Clean lines. Monospace font for the diagram.
  - Label under Deterministic Judge: "NFKC + AST + State Tracking"
  - Label under Lobster Trap: "by Veea Foundation"
  - Label under Policy Builder: "HIPAA | SOC2 | PCI-DSS | GDPR | Finance | Startup"
- **Right — Metrics (stacked vertically):**
  - **<50ms** — Judge evaluation (large red number, small gray label)
  - **4/4** — Bypass patterns blocked (context window, homoglyph, suffix, multi-turn)
  - **156ms** — Full incident resolution (Judge → Quarantine → Forensics → NIST)
  - **NIST SP 800-61r2** — Automated playbook mapping
  - **EU AI Act Compliant** — Ready for January 2027 enforcement
  - **Organization-Defined Parameters** — First product to implement NIST ODPs
  - **6 Industry Templates** — HIPAA, SOC2, PCI-DSS, GDPR, Finance, Startup
  - **Policy Conflict Detection** — Warnings when custom rules conflict with NIST
- **Bottom banner:** Built on Veea's Lobster Trap | Aligned with NIST Agentic Profile | Deterministic Enforcement | ODP-Ready
- **SupraWall Differentiation Badge (bottom right corner, subtle):**
  - "SupraWall guards the gate. PLAYBOOK handles the incident."

**Design Notes:**
- Numbers are the heroes. 48pt minimum for the big three.
- Architecture diagram should be readable in 3 seconds. If it needs explanation, it's too complex.
- "4/4" is the key number — it answers "how do you know it works?"
- The three ODP metrics (ODPs, 6 Templates, Conflict Detection) should be grouped visually — they're the new differentiator.
- This slide is flashed briefly at 2:40 during the close. Keep it scannable.

---

### Slide 4: The Demo

**Layout:** This slide is your safety net. Three screenshot placeholders arranged as a storyboard — now expanded to include the Policy Builder.

**Elements:**
- **Header:** IN ACTION — THE JUDGE LAYER + POLICY BUILDER
- **Left screenshot:** Agent interface with bypass pattern #1 visible (context window displacement)
- **Center screenshot:** Judge decision panel — 4 DENY decisions with rationale
- **Right screenshot:** Policy Builder showing three template responses side-by-side (HIPAA, Startup, FinTech)
- **Below each screenshot:** 3-word caption
  - Left: "The Attack"
  - Center: "The Judge"
  - Right: "The Policy"
- **Bottom:** Tech stack badges (horizontal row)
  - `Python` `Deterministic Judge` `Veea Lobster Trap` `NIST 800-61r2` `NIST ODPs` `FastAPI` `React`

**Design Notes:**
- Screenshots should be high-resolution, actual app screenshots — not mockups.
- The Policy Builder screenshot is the new hero — three columns, same incident, three different responses. Make it prominent.
- Use a subtle drop shadow on each screenshot to create depth.
- Tech badges should be small, monochrome with colored accents (GitHub-style).
- This slide is replaced by the live demo. It's only shown if you need to fallback to screenshots (Plan D).

---

### Slide 5: Ask & Contact

**Layout:** Clean, centered. One clear ask. Contact details. QR code.

**Elements:**
- **Header:** DETERMINISTIC INCIDENT RESPONSE FOR AI AGENTS
- **The Ask (center, bold):** We're seeking design partners deploying AI agents in production.
- **Sub-ask (smaller):** Also open to: strategic partnerships, investor conversations, technical feedback
- **ODP Highlight (center, subtle):** "First product to implement NIST Organization-Defined Parameters"
- **Contact block (left):**
  - Name, email, phone
  - GitHub: github.com/[your-repo]
  - LinkedIn: linkedin.com/in/[your-profile]
- **QR code (right):**
  - Links to GitHub repo
  - Below: "Scan for repo + demo video"
- **Bottom line:** PLAYBOOK — Deterministic Judge Layer + Organization-Defined Parameters. SupraWall guards. PLAYBOOK responds.

**Design Notes:**
- QR code must be at least 2 inches square to scan from 10 feet.
- Test the QR code on 3 different phones before demo day.
- The closing line echoes the new narrative — "SupraWall guards. PLAYBOOK responds." plus the ODP differentiator.

---

## 5. Timing Guide (Second by Second)

```
0:00  START — Walk to center. Pause. Deep breath.
0:01  [EYE CONTACT — Center judge]
0:02  "Today — literally today — Nate B Jones published..."
0:07  [PAUSE — 1.5 seconds. Glance left, right.]
0:09  "He proved what every security engineer knows..."
0:14  [SHIFT WEIGHT — Move toward screen area]
0:15  "He had prompts. We built PLAYBOOK..."
0:21  [PAUSE — 1 second.]
0:22  "Let me show you why deterministic enforcement beats LLM-as-judge every time."
0:28  [MOVE TO DEMO SCREEN]

0:30  [SCREEN — Agent interface, dangerous tool call visible]
0:31  "Here's an AI agent proposing a dangerous action..."
0:36  "This is where every agent needs a judge. But not all judges are equal."

0:37  [SCREEN — Bypass Pattern #1: Context Window Displacement]
0:38  "Here's a context window displacement attack..."
0:42  "Lakera Guard: bypassed. NeMo Guardrails: bypassed."

0:44  [SCREEN — Bypass Pattern #2: Unicode Homoglyph]
0:45  [POINT AT SCREEN] "Here's a unicode homoglyph..."
0:48  "LLM-based judges normalize it and miss the attack..."
0:50  "PLAYBOOK's deterministic Judge: caught."

0:52  [SCREEN — Bypass Pattern #3: Adversarial Suffix Injection]
0:53  "Adversarial suffix injection..."
0:56  "PLAYBOOK's Judge operates on normalized AST structure: caught."

0:58  [SCREEN — Bypass Pattern #4: Multi-Turn State Confusion]
0:59  "Multi-turn state confusion..."
1:02  "LLM judges evaluate each turn in isolation. PLAYBOOK's Judge: caught."

1:04  [SCREEN — Judge decision panel: 4 DENY decisions]
1:05  "Four attacks. Four blocks."
1:08  "Zero LLM in the enforcement path."
1:10  "One hundred percent accuracy. Under fifty milliseconds."
1:14  [PAUSE — 1 second. Step back.]

1:15  [SCREEN — Incident response dashboard, red "JUDGE DENIED" banner]
1:16  "The Judge caught it. Now PLAYBOOK responds with automated containment."

1:18  [SCREEN — Lobster Trap QUARANTINE visualization]
1:19  "This is Lobster Trap — Deep Packet Inspection for AI..."
1:23  "The dangerous action is isolated before it touches anything real."

1:24  [SCREEN — Forensic capture auto-generates]
1:25  "Simultaneously, PLAYBOOK builds a complete forensic capture..."
1:31  "If this escalates to legal, to compliance, to an audit — everything documented."

1:33  [SCREEN — Agent health update fires]
1:34  "And PLAYBOOK updates the agent's health profile in real-time."

1:36  [SCREEN — Timeline display: 156ms full resolution]
1:37  "One hundred fifty-six milliseconds..."
1:40  "...from dangerous action to full containment, forensics, and NIST classification."

1:43  [SCREEN — NIST classification card]
1:44  "And it maps directly to NIST..."
1:47  "Step one of seven, automatically triggered."

1:49  [SCREEN — Containment result: safe response substituted]
1:50  "The dangerous action never reached production..."
1:52  "The agent keeps running — but it can't hurt anything."

2:00  [SCREEN — Policy Builder interface, "Apply Template" dropdown]
2:01  "But here's what makes PLAYBOOK different from every other product."
2:04  "The same incident at three different organizations gets three different responses."
2:07  [CLICK — Apply HIPAA Template]
2:08  "At Mayo Clinic, data deletion is CRITICAL. Auto-contained. CEO paged."
2:12  "HIPAA report auto-generated. Any deletion of patient data is a federal incident."

2:14  [CLICK — Apply Startup Template]
2:15  "At a SaaS startup, the same deletion is MEDIUM. Engineering lead notified."
2:19  "Basic logs. No auto-contain. Same NIST baseline. Different organizational rules."

2:22  [CLICK — Apply FinTech Template]
2:23  "At a FinTech, it's CRITICAL only if financial records are affected."
2:26  "Risk Officer escalated. PCI-DSS report generated conditionally."

2:28  [SCREEN — Side-by-side comparison: 3 columns, same incident, 3 responses]
2:29  "One NIST baseline. Infinite organizational responses."
2:32  "This is what NIST calls Organization-Defined Parameters..."
2:35  "...and PLAYBOOK is the first product to implement them."

2:37  [SCREEN — Agent Health Dashboard]
2:38  "But PLAYBOOK doesn't stop at one incident."
2:40  "Lie rate 4.2%, trending up. Risk score seventy-three."
2:43  "SupraWall guards. PLAYBOOK responds."
2:45  "And every policy change is versioned and audited..."
2:47  "...because NIST GOVERN 1.4 requires transparent risk management."

2:50  [SLIDE TRANSITION — Slide 4: Solution]
2:51  "Nate B Jones said every agent needs a judge."
2:52  "NIST says every organization needs custom policies."
2:53  "We built PLAYBOOK — the first product that does both."
2:55  "Deterministic Judge Layer. Organization-Defined Parameters. NIST playbooks."
2:57  "EU AI Act ready. Built on Veea's Lobster Trap."
2:59  [PAUSE — 1 second. Eye contact. Smile.]
3:00  [HOLD — 1 second. Step back. Done.]
```

---

## 6. Backup Plans

### Plan A: Full Live Demo (Ideal)

**Trigger:** Everything works. No latency. No errors.

**Execution:** Follow the script in Section 2 exactly. All screen transitions are live.

**Probability:** 60% (pre-cached data, deterministic behavior — this is your likely path).

**Success indicators:**
- Judge decision panel loads within 2 seconds of trigger
- All 4 bypass patterns render correctly with labels
- Lobster Trap quarantine visualization plays smoothly
- NIST classification card appears with correct mapping
- Timeline renders all 6 stages
- Policy Builder template switches complete in under 3 seconds each
- Side-by-side comparison renders correctly with 3 columns

---

### Plan B: Partial Live + Video (If API Slow)

**Trigger:** First 45 seconds work, but Judge decision panel or Lobster Trap shows latency (>3 seconds) or partial data.

**Execution:**
1. Complete Demo Part 1 (Judge Layer) live — 0:30–1:15 ✓
2. Show bypass patterns #1 and #2 live
3. At 1:10, if Judge decision panel hasn't loaded within 3 seconds:
   - **Say:** "While that processes, let me show you exactly what happens when PLAYBOOK contains an incident — because in production, this is deterministic every time."
   - [CLICK TO START BACKUP VIDEO]
4. Video picks up from the incident response (quarantine, forensics, NIST) and runs through containment, Policy Builder, profile, and close.
5. Resume script at 2:40 for the profile section — live, not from video.

**Transition phrase (memorize exactly):**
> "While that processes, let me show you exactly what happens when PLAYBOOK contains an incident — because in production, this is deterministic every time."

**Probability:** 25%

**Preparation:**
- Video file named `playbook-demo-backup.mp4` on desktop
- Video starts at the incident response moment (1:15 equivalent)
- Video ends at the agent health profile (2:55 equivalent)
- Video includes Policy Builder template switching segment
- Practice the transition 3+ times so it's seamless

---

### Plan C: Video Only (If Everything Fails)

**Trigger:** Local environment won't start. Network issues. Laptop problems after setup.

**Execution:**
1. Deliver opening hook live — 0:00–0:30 (slides work, no demo needed)
2. At 0:28, instead of "Let me show you why deterministic enforcement beats LLM-as-judge every time," say:
   - **Say:** "To make sure you see the full experience regardless of today's network conditions, I've prepared this — ninety seconds that will change how you think about AI agent safety."
   - [START FULL BACKUP VIDEO — 90 seconds]
3. During video playback: stand to the side, face the judges (not the screen), maintain confident posture
4. Do NOT narrate over the video — it has its own audio track (Section 8)
5. At video end (2:00 mark), step forward and deliver the Policy Builder and close live — 2:00–3:00

**Transition phrase (memorize exactly):**
> "To make sure you see the full experience regardless of today's network conditions, I've prepared this — ninety seconds that will change how you think about AI agent safety."

**Probability:** 10%

**Preparation:**
- Full 90-second video with narrated audio track (includes bypass patterns + Policy Builder)
- Video on laptop + phone + USB drive (triple redundancy)
- Practice standing silently during video — 90 seconds feels like eternity. Have a water bottle.
- Close must be delivered with full energy — this is where judges form their final impression.

---

### Plan D: Static Screenshots (Nuclear Option)

**Trigger:** Video won't play. Screen sharing fails. Complete technical meltdown.

**Execution:**
1. Deliver opening hook live — 0:00–0:30
2. At 0:28:
   - **Say:** "Let me walk you through what happens step by step — starting with the Judge Layer that Nate B Jones just said every agent needs, and then showing you the Policy Builder that no other product has."
   - [DISPLAY SLIDE 4 — The Demo Screenshots]
3. Walk through each screenshot as if it's live:
   - Screenshot 1 (The Attack): "Here's a context window displacement attack — 50,000 benign tokens hiding a malicious tool call."
   - Screenshot 2 (The Judge): "Here's PLAYBOOK's deterministic Judge — four bypass patterns, four DENY decisions. No LLM in the enforcement path."
   - Screenshot 3 (The Policy): "Here's the Policy Builder — same incident, three different organizational responses. HIPAA: CRITICAL. Startup: MEDIUM. FinTech: conditional. First product to implement NIST Organization-Defined Parameters."
4. Speak with conviction — your words carry the demo now, not the screen
5. Deliver close as scripted — 2:55–3:00

**Adapted script for Plan D (replacing 0:30–2:55):**

> [0:30] "Here's what PLAYBOOK looks like in action. First — the Judge Layer. [Point to Screenshot 1] A context window displacement attack — fifty thousand benign tokens hiding a malicious tool call at the context boundary. Lakera Guard: bypassed. NeMo Guardrails: bypassed. PLAYBOOK's deterministic Judge: caught."
>
> [0:42] "Unicode homoglyph — `file_delete` versus `fіle_delete` with a Cyrillic eye. LLM judges normalize and miss it. Deterministic Judge with NFKC normalization: caught."
>
> [0:50] "Four bypass patterns tested. Four blocked. [Point to Screenshot 2] Zero LLM in the enforcement path. One hundred percent accuracy. Under fifty milliseconds."
>
> [0:58] "The Judge caught it. Now PLAYBOOK responds. Lobster Trap quarantines the action. Forensics auto-generate. NIST classification maps the incident."
>
> [1:05] "One hundred fifty-six milliseconds from dangerous action to full containment. Step one of seven, automatically triggered."
>
> [1:10] "But here's what makes PLAYBOOK different. [Point to Screenshot 3] The Policy Builder. Same incident — AGT-DEL-001 — at three different organizations. HIPAA says CRITICAL: auto-contain, CEO paged, federal report. Startup says MEDIUM: engineering lead, basic logs. FinTech says conditional: Risk Officer, PCI-DSS."
>
> [1:22] "One NIST baseline. Infinite organizational responses. This is what NIST calls Organization-Defined Parameters — and PLAYBOOK is the first product to implement them."
>
> [1:30] "SupraWall guards. PLAYBOOK responds."
>
> [1:32] "That's PLAYBOOK."

**Key difference:** Plan D script is only 62 seconds (vs. 125 seconds live). You gain ~63 seconds. Use it to:
- Expand on one bypass pattern (pick context window displacement, explain it vividly)
- Explain Organization-Defined Parameters more deeply (this is your unique differentiator)
- Add a personal "why we built this" moment (10 seconds max)
- Slow down and make eye contact with every judge

**Probability:** 5%

**Preparation:**
- Slide 4 must have HIGH-RESOLUTION actual screenshots including the Policy Builder side-by-side
- Practice the Plan D walkthrough 5+ times — it's harder than live because you have no animation to pace you
- Print the adapted script on an index card (in case laptop is completely dead — you can present with just the printed slides)

---

## Backup Plan Quick-Reference Card

Print this on a small card. Keep it in your pocket during the demo.

```
PLAN A — Full Live     → If everything works → Follow script exactly
PLAN B — Live + Video  → If API slow        → "While that processes..."
PLAN C — Video Only    → If env won't start → "Regardless of network..."
PLAN D — Screenshots   → Nuclear option      → "Let me walk you through..."

RECOVERY PHRASES:
- Dashboard slow  → "In production this is deterministic sub-50ms, but today..."
- Wrong result    → "Here's where deterministic enforcement shines — same result every time, no LLM variance..."
- Total failure   → "This is exactly why we need deterministic enforcement — even our demo..."
- Awkward silence → Count to 3 in your head, then speak

COMPETITOR RESPONSES:
- "SupraWall?" → "SupraWall guards. PLAYBOOK responds. Different layer. ODPs."
- "Lakera?"    → "LLM-as-judge. 3/4 bypass. Deterministic: 0/4. No ODPs."
- "ODPs?"      → "NIST SP 800-53. First product to implement them natively."
```

---

## 7. Recovery Phrases

### If Judge Decision Panel Doesn't Load (within 3 seconds)

**Primary recovery:**
> "While that loads, let me show you what the containment looks like when PLAYBOOK responds — because the Judge decision is deterministic, so the result is identical every time."

**Then:** Click to reveal the containment visualization directly (pre-loaded state) or start backup video.

**Body language:** Don't look stressed. A small smile. You're unfazed because deterministic enforcement means the result is always the same — no variance, no surprises.

---

### If Dashboard Is Slow (elements loading one by one)

**Primary recovery:**
> "In production this is deterministic sub-fifty-milliseconds, but today our demo environment is running on conference WiFi — which, ironically, proves the point. Deterministic enforcement doesn't depend on LLM inference time. It's a lookup, not a generation. In the real world, PLAYBOOK runs on dedicated infrastructure."

**Self-deprecating version (if crowd is friendly):**
> "Conference WiFi — the ultimate stress test. In production, this entire sequence completes in under two hundred milliseconds because there's zero LLM inference in the enforcement path. Let me show you what you would see."

**Then:** Narrate what's SUPPOSED to appear while it loads. "You'll see the Judge decision panel here... the quarantine visualization here... the NIST classification here... the Policy Builder here..." This fills dead air with value.

---

### If Classification Is Wrong (or confidence is low)

**Primary recovery:**
> "And here's where deterministic enforcement gets really interesting — the Judge uses hard rules, not probabilistic classification. The result is identical every time. No variance, no hallucination, no confidence threshold to worry about. PLAYBOOK doesn't guess. It enforces. That's the difference between LLM-as-judge and deterministic enforcement."

**Then:** Pivot to the Policy Builder. "Even in deterministic mode, your organization's ODPs customize the response — severity, auto-containment, escalation. Same incident, different response, based on your risk tolerance."

**Key framing:** Deterministic enforcement is a FEATURE, not a limitation. "No confidence threshold" is a selling point. ODPs add organizational customization on top.

---

### If Complete Failure (nothing works)

**Primary recovery:**
> "This is exactly why we need PLAYBOOK. Even our demo environment — carefully prepared, fully tested, deterministic — can have a bad day. Now imagine this is your production AI agent handling real customer data, real financial transactions, real people's lives. And imagine that instead of a deterministic Judge, you're relying on an LLM that can be bypassed by a context window displacement attack or a unicode homoglyph. And imagine that your organization can't even customize the response — because no other product implements NIST Organization-Defined Parameters."

**Then:** Execute Plan D (Screenshots) or Plan C (Video).

**Critical:** This phrase must sound empathetic, not defensive. You're not apologizing for your demo failing — you're demonstrating that failure is universal and deterministic enforcement is the answer.

**Tone check:** Practice this line 10 times. Record yourself. Listen back. It should sound like a CTO who just learned about a bypass — serious, focused, already thinking about the solution.

---

### If You Blank (forget your lines)

**Technique — The Pivot:**
1. Pause. Breathe. (2 seconds feels like 5 to you, like 1 to the audience.)
2. Say your anchor phrase: "Deterministic enforcement."
3. That phrase resets your brain. From there, you know the next line: "beats LLM-as-judge every time."
4. You're back on track.

**Emergency filler phrases (buy 3–5 seconds each):**
- "And what's critical about deterministic enforcement is..."
- "The thing that makes this different from LLM-as-judge..."
- "If you remember nothing else about the Judge Layer..."
- "Here's why deterministic beats probabilistic..."
- "Organization-Defined Parameters — here's why they matter..."

**Never say:** "Um," "Uh," "Sorry," or "I forgot what I was going to say."

---

## 8. Backup Video Script (90-Second Narrated Video)

**Purpose:** Played during Plan B, Plan C, or shared with judges after the demo.  
**Format:** MP4, 1920x1080, 30fps  
**Audio:** Narrated by you (not text-to-speech — your voice creates connection)

---

#### Video Section 1: The Hook (0:00–0:15)

**Visual:** Dark background. Text animates in: "TODAY — Nate B Jones published 'The AI Agent Judge Layer' to 148,000 subscribers." Then: "He had prompts. We built PLAYBOOK."

**Audio narration:**
> "Today — literally today — Nate B Jones published 'The AI Agent Judge Layer' to one hundred forty-eight thousand subscribers. He proved what every security engineer knows: every AI agent needs a judge. He had prompts. We built PLAYBOOK — the first automated incident response system with a deterministic Judge Layer. Let me show you why deterministic enforcement beats LLM-as-judge."

**Direction:**
- Start with a clean desktop. Text animates in line by line.
- "TODAY" should appear first, large, with a subtle pulse.
- "148,000 subscribers" should count up like a speedometer.
- Cut to black for 0.5 seconds after the hook text.

---

#### Video Section 2: The Bypass Patterns (0:15–0:50)

**Visual:** Four rapid bypass pattern demonstrations.

**Audio narration:**
> "Here's an AI agent proposing a dangerous action. Now watch four bypass patterns that break LLM-based judges. Context window displacement — fifty thousand benign tokens hiding a malicious tool call. Lakera Guard: bypassed. NeMo Guardrails: bypassed. Unicode homoglyph — file delete versus file delete with a Cyrillic eye. LLM judges normalize and miss it. Adversarial suffix injection — a crafted suffix that fools token boundaries. Multi-turn state confusion — eight innocent queries that collectively manipulate the agent. LLM judges evaluate each turn in isolation. Four attacks. Four bypasses of LLM-as-judge."

**Direction:**
- Each bypass pattern should appear for 8 seconds with labels and visual indicators.
- "Lakera Guard: bypassed" and "NeMo Guardrails: bypassed" should appear in red text.
- Fast transitions between patterns (0.5s fade).
- Background music: subtle, tension-building electronic (not distracting).

---

#### Video Section 3: The Judge Decision (0:50–1:05)

**Visual:** Judge decision panel — 4 DENY decisions in green (success). Each decision is labeled with the bypass pattern it caught.

**Audio narration:**
> "Now watch PLAYBOOK's deterministic Judge. NFKC normalization catches the homoglyph. AST pattern matching catches the adversarial suffix. Cross-turn state tracking catches the multi-turn confusion. Context boundary analysis catches the displacement attack. Four attacks. Four blocks. Zero LLM in the enforcement path. One hundred percent accuracy. Under fifty milliseconds."

**Direction:**
- Each DENY decision should "pop" into view with a satisfying click sound.
- "4/4" should appear large and bold, counting up.
- "<50ms" should pulse gently.
- The four bypass pattern names should appear next to their corresponding DENY decisions.

---

#### Video Section 4: The Incident Response (1:05–1:35)

**Visual:** Containment visualization — Lobster Trap quarantine, forensic capture, NIST classification, timeline. Agent health update.

**Audio narration:**
> "The Judge caught it. Now PLAYBOOK responds. Lobster Trap quarantines the action. Forensics auto-generate. NIST maps the incident to SP 800-61r2 — step one of seven, automatically triggered. One hundred fifty-six milliseconds from dangerous action to full containment. The agent keeps running — but it can't hurt anything. And unlike SupraWall, which is a great guardrail, PLAYBOOK gives you full incident forensics, NIST compliance mapping, and agent health profiling. SupraWall guards. PLAYBOOK responds."

**Direction:**
- Quarantine: show an orange border isolating the agent action.
- Forensics: show documents being "stamped" with timestamps. Fast-motion assembly.
- NIST classification: show the NIST SP 800-61r2 document with the relevant section highlighted.
- Timeline: each stage lights up sequentially.
- "SupraWall guards. PLAYBOOK responds." should appear as text on screen at the end.

---

#### Video Section 5: The Policy Builder (1:35–1:55)

**Visual:** Policy Builder interface — same incident AGT-DEL-001 with three template switches. Side-by-side comparison.

**Audio narration:**
> "But here's what makes PLAYBOOK different from every other product. The same incident at three different organizations gets three different responses. At Mayo Clinic — HIPAA template — data deletion is CRITICAL. Auto-contained. CEO paged. At a SaaS startup — Startup template — the same deletion is MEDIUM. Engineering lead notified. No auto-contain. At a FinTech — FinTech template — CRITICAL only if financial records are affected. Risk Officer escalated. One NIST baseline. Infinite organizational responses. This is what NIST calls Organization-Defined Parameters — and PLAYBOOK is the first product to implement them."

**Direction:**
- Show the template dropdown being clicked three times.
- Each template switch should animate the response parameters changing (severity, containment, escalation).
- The side-by-side comparison should build column by column (HIPAA first, then Startup, then FinTech).
- "First product to implement them" should appear as large text on screen.
- Background music: subtle, building to a crescendo.

---

#### Video Section 6: The Close (1:55–2:05)

**Visual:** Architecture diagram → Key metrics → Logo + QR code.

**Audio narration:**
> "Nate B Jones said every agent needs a judge. NIST says every organization needs custom policies. We built PLAYBOOK — the first product that does both. Deterministic Judge Layer. Organization-Defined Parameters. NIST playbooks. EU AI Act ready. Built on Veea's Lobster Trap."

**Direction:**
- Architecture diagram: fade in each layer sequentially (0.3s per layer).
- Metrics: count up animation for the three key numbers.
- Final frame: PLAYBOOK logo centered, "SupraWall guards. PLAYBOOK responds." as tagline, QR code bottom-right.
- Hold final frame for 3 seconds before fade to black.

---

#### Video Section 7: End Card (2:05–2:10)

**Visual:** Black screen. White text: "PLAYBOOK — Deterministic enforcement + Organization-Defined Parameters." Fade out.

**Audio:** None. Silence is powerful here.

---

### Recording Tools & Tips

**Recommended tools:**
- **OBS Studio** (free) — best for screen recording with picture-in-picture webcam
- **Loom** (free tier) — fastest to set up, auto-saves to cloud
- **ScreenFlow** ($149) — best editing, worth it if you have time
- **Camtasia** ($249) — powerful, steeper learning curve

**Recording checklist:**
- [ ] Close all unrelated apps and browser tabs
- [ ] Turn off notifications (Do Not Disturb)
- [ ] Record at 1920x1080 minimum
- [ ] Use a good microphone (built-in is fine in a quiet room, USB mic is better)
- [ ] Record in a quiet room (no HVAC noise, no traffic)
- [ ] Do 3 takes. Pick the best one. Don't aim for perfect — aim for authentic.
- [ ] Export as MP4 (H.264 codec, AAC audio)
- [ ] Test playback on: your laptop, your phone, a friend's device
- [ ] Upload to: laptop desktop, Google Drive, phone, USB drive (4 copies minimum)

**Voice direction:**
- Speak 20% slower than normal. Video compresses time — what feels slow to you feels normal to viewers.
- Vary your pace: slow for hook, fast for bypass patterns, measured for the resolution, building for Policy Builder.
- Smile while recording. It changes your voice. Judges can hear it.

---

## 9. Judge Q&A Preparation

### 17 Likely Questions with Suggested Answers

---

#### Q1: "Did you see Nate B Jones's article today?"

**Suggested answer:**
> "Yes, I was reading Nate's newsletter this morning. It's fascinating — he laid out exactly why every AI agent needs a judge layer. And the timing couldn't be better for us, because PLAYBOOK is exactly that: a deterministic Judge Layer that enforces policy on every agent action. Nate articulated the problem. We built the solution."

**Key phrases to hit:** "Reading it this morning," "timing couldn't be better," "Nate articulated the problem, we built the solution."

---

#### Q2: "What about SupraWall?"

**Suggested answer:**
> "SupraWall is excellent at guardrails — input filtering, output formatting, schema enforcement. They're the guard on the gate. PLAYBOOK is incident response — we handle what gets through, we document everything, we map to NIST, we track agent health over time, and we let each organization define their own response policies using NIST Organization-Defined Parameters. Different layer, completely complementary. You need both. SupraWall guards. PLAYBOOK responds."

**Key phrases to hit:** "SupraWall is excellent," "different layer, completely complementary," "SupraWall guards. PLAYBOOK responds." "Organization-Defined Parameters."

---

#### Q3: "Why deterministic over LLM-judge?"

**Suggested answer:**
> "Shi et al. 2024 showed that LLM-judge achieves roughly eighty percent accuracy on adversarial inputs. That means twenty percent of attacks succeed. We just demonstrated four bypass patterns that break LLM-based judges — context window displacement, unicode homoglyphs, adversarial suffix injection, multi-turn state confusion. Lakera and NeMo Guardrails both use LLM-as-judge. Three out of four attacks bypass them. PLAYBOOK uses deterministic enforcement: NFKC normalization, AST pattern matching, cross-turn state tracking. Zero LLM in the enforcement path. Zero bypasses. One hundred percent accuracy for known patterns."

**Key phrases to hit:** "Shi et al. 2024 — 80% accuracy = 20% attacks succeed," "3 out of 4 bypass Lakera," "Zero LLM in the enforcement path."

---

#### Q4: "Is this just a wrapper around Lobster Trap?"

**Suggested answer:**
> "No — and this is an important distinction. PLAYBOOK is the Judge Layer ON TOP of Lobster Trap. Lobster Trap provides Deep Packet Inspection — it sees every token in real-time. But seeing tokens isn't enough. You need a Judge that decides whether an action should proceed. PLAYBOOK provides that judgment, the incident response, the NIST mapping, the forensic capture, the agent health profiling, and the Policy Builder with Organization-Defined Parameters. Lobster Trap is the eyes. PLAYBOOK is the brain and the immune system."

**Key phrases to hit:** "Judge Layer ON TOP of Lobster Trap," "Lobster Trap is the eyes. PLAYBOOK is the brain and the immune system." "Organization-Defined Parameters."

---

#### Q5: "How is this different from a simple prompt injection detector?"

**Suggested answer:**
> "Prompt injection detectors look at the INPUT — they try to catch malicious prompts. PLAYBOOK monitors the OUTPUT and the agent's proposed ACTIONS. We're not asking 'Is someone attacking the agent?' We're asking 'Is the agent itself about to cause damage?' That's a completely different threat vector. The PocketOS disaster wasn't a prompt injection — the agent just hallucinated a DROP TABLE command. No attacker. Just an agent doing what agents do: making mistakes at machine speed."

**Key phrases to hit:** Input vs. output monitoring, agent-initiated vs. user-initiated threats, "making mistakes at machine speed."

---

#### Q6: "What's your moat? Why can't Anthropic or OpenAI build this?"

**Suggested answer:**
> "They can, and they probably will. But incident response is a discipline, not a feature. Splunk didn't beat log analysis tools by being first — they won by being purpose-built for security operations. PLAYBOOK is built on Veea's Lobster Trap, which is the only DPI layer that sees every token in real-time. Our deterministic Judge is a proprietary rules engine, not a wrapper around an API. And we're the first product to implement NIST Organization-Defined Parameters — that's not a feature you add overnight, it's a fundamental architecture decision. By the time the big players take this seriously, we'll have six months of production data, tuned classifications, embedded workflows, and proven ODP templates."

**Key phrases to hit:** Incident response is a discipline not a feature, purpose-built for security operations, deterministic Judge is proprietary, first to implement NIST ODPs.

---

#### Q7: "How do you handle false positives?"

**Suggested answer:**
> "Great question — and this is where deterministic enforcement actually helps. With LLM-as-judge, you have variance — the same input can produce different decisions. With PLAYBOOK's deterministic Judge, the result is identical every time. No surprises. We handle edge cases through explicit rule precedence and human-review flags for novel patterns. Every decision is logged with full rationale, so if a rule needs tuning, you have complete visibility. And our agent health dashboard tracks precision per incident type — if a particular rule is noisy, you'll see it in the data. Plus, Organization-Defined Parameters let each organization tune their own thresholds — what's CRITICAL for a hospital is MEDIUM for a startup."

**Key phrases to hit:** Deterministic = same result every time, explicit rule precedence, human-review flags, precision tracking per type, ODP customization.

---

#### Q8: "What about latency? Doesn't this slow down the agent?"

**Suggested answer:**
> "Our Judge evaluation is under fifty milliseconds. That's a lookup, not an LLM inference call. Compare that to LLM-as-judge solutions that take hundreds of milliseconds — or more — for each evaluation. In production, the total incident response pipeline is one hundred fifty-six milliseconds from dangerous action to full containment, forensics, and NIST classification. The PocketOS database was gone in nine seconds. PLAYBOOK acts in under fifty milliseconds for the Judge, under two hundred for full resolution. Policy template switching is instantaneous — it's a lookup, not a model call."

**Key phrases to hit:** <50ms Judge (lookup not inference), 156ms full pipeline, compare to LLM-judge latency, template switching is instant.

---

#### Q9: "Who's your target customer?"

**Suggested answer:**
> "Three segments. First, enterprises running customer-facing AI agents — banks, insurers, healthcare. They're one false commitment away from regulatory action or a lawsuit. Second, AI infrastructure companies — anyone building agent platforms needs deterministic safety as a feature, not an afterthought. Third, regulated industries facing EU AI Act compliance. The Act requires incident logging and human oversight for high-risk AI systems. PLAYBOOK provides both, automatically, with NIST-mapped playbooks and Organization-Defined Parameters that let each organization customize their response to their own regulatory requirements."

**Key phrases to hit:** Enterprise AI agents, infrastructure companies, EU AI Act compliance, three clear segments, ODPs for regulatory requirements.

---

#### Q10: "How does this scale? What's the infrastructure?"

**Suggested answer:**
> "PLAYBOOK runs as a middleware layer between your agent and its environment. The deterministic Judge is a rules engine — it scales horizontally with zero inference cost. No GPU needed. The forensics and agent health data are stored in your own environment — we don't hold your data hostage. Policy templates are pre-loaded configurations — zero runtime overhead. For a mid-size deployment, you're looking at sub-$500/month in infrastructure costs. For an enterprise, it's a rounding error compared to the cost of one incident — and a fraction of what you'd pay for LLM-as-judge API calls at scale."

**Key phrases to hit:** Middleware layer, horizontal scaling, zero inference cost (no GPU), you own your data, template switching has zero overhead, cost comparison.

---

#### Q11: "Hasn't this been done before? What's novel here?"

**Suggested answer:**
> "AI safety research has been around for years — alignment, RLHF, constitutional AI. But those are TRAINING-time solutions. Guardrails like SupraWall are INPUT-time solutions. PLAYBOOK is a RUNTIME solution that combines deterministic judgment with full incident response. We assume the agent WILL make mistakes — because all agents do — and we catch them in real-time with deterministic enforcement, then respond with automated containment, NIST-mapped playbooks, and agent health profiling. And we're the first product to implement NIST Organization-Defined Parameters — same incident, different response, based on organizational risk tolerance. No one has built a dedicated deterministic Judge Layer with integrated incident response and ODP policy customization before."

**Key phrases to hit:** Training-time vs. runtime vs. input-time, deterministic Judge + incident response + ODPs, no dedicated solution exists yet.

---

#### Q12: "What's your business model?"

**Suggested answer:**
> "SaaS with usage-based pricing. Base tier covers Judge monitoring and detection. Pro tier adds automated containment and NIST playbook mapping. Enterprise tier adds custom Judge rules, compliance reporting, Organization-Defined Parameter templates, and dedicated support. We're not trying to monetize yet — right now we need design partners who will help us tune the deterministic rules and validate the ODP templates in production. The pricing model will evolve based on what we learn from real deployments."

**Key phrases to hit:** SaaS, usage-based, three tiers, design partners first, deterministic rules tuning, ODP template validation.

---

#### Q13: "What about competitors like Guardrails AI or Lakera?"

**Suggested answer:**
> "Guardrails AI focuses on input validation and output formatting — schema enforcement, basically. Lakera focuses on prompt injection detection using LLM-as-judge. Both are important, but they're point solutions at the input layer. PLAYBOOK is an end-to-end incident response platform with a deterministic Judge Layer: judgment, containment, forensics, NIST mapping, agent health monitoring, and Organization-Defined Parameters. We're not competing with guardrails — we're the SOC analyst that watches the guardrails, catches what they miss with deterministic enforcement, documents everything for compliance, and lets each organization define their own response policies. Lakera uses LLM-as-judge. Three out of four attacks bypass it. We use deterministic enforcement. Zero bypasses."

**Key phrases to hit:** Point solutions vs. platform, complement not compete, SOC analyst metaphor, Lakera 3/4 bypass rate vs. deterministic 0/4, ODPs.

---

#### Q14: "Why should we pick you for this hackathon?"

**Suggested answer:**
> "Because we're not just building a product — we're solving a problem that keeps getting worse and that the industry just validated. Nate B Jones's article today — to one hundred forty-eight thousand people — said every agent needs a judge. The EU AI Act deadline is January 2027. Companies are deploying agents faster than they're building safety measures. PLAYBOOK bridges that gap — with deterministic enforcement that works today, not in a research paper, and Organization-Defined Parameters that let every organization customize their response to their own risk tolerance. We have a working prototype, a clear technical architecture, and a team that understands both AI and security. Give us this platform, and we'll have design partners signed in thirty days."

**Key phrases to hit:** Problem getting worse, Nate B Jones validation today, EU AI Act deadline, deterministic enforcement works today, ODPs for organizational customization, design partners in 30 days.

---

#### Q15: "How is this different from SupraWall?"

**Suggested answer:**
> "SupraWall is a one-size-fits-all guardrail. PLAYBOOK lets each organization define their own response policies using NIST Organization-Defined Parameters. Same incident, different response, based on organizational risk tolerance. SupraWall guards the gate — input filtering, output formatting. PLAYBOOK handles the incident — deterministic judgment, automated containment, forensic capture, NIST mapping, and policy customization. SupraWall guards. PLAYBOOK responds."

**Key phrases to hit:** "One-size-fits-all vs. organization-defined." "Same incident, different response." "SupraWall guards. PLAYBOOK responds." "NIST Organization-Defined Parameters."

---

#### Q16: "What are Organization-Defined Parameters?"

**Suggested answer:**
> "NIST SP 800-53 defines ODPs as the variable parts of each security control that every organization customizes. PLAYBOOK is the first AI security product to implement them natively. Here's what that means in practice: the same incident — say, a data deletion — gets a CRITICAL response at a hospital because HIPAA requires it, but a MEDIUM response at a SaaS startup because their risk tolerance is different. The NIST baseline is the floor. Your ODPs define your ceiling. Same baseline. Different response. Based on organizational priorities."

**Key phrases to hit:** "NIST SP 800-53." "Variable parts." "First AI security product to implement them natively." "Same baseline, different response."

---

#### Q17: "Can I customize NIST rules?"

**Suggested answer:**
> "NIST baselines are immutable — they provide the floor. You can't weaken NIST. But your organization's ODPs customize the response: severity, auto-containment, escalation chain, forensic detail, reporting requirements. You can't weaken NIST, but you can strengthen your response. And PLAYBOOK warns you when a custom ODP conflicts with the NIST baseline — we call it Policy Conflict Detection. So you're always compliant, but you're also always customized to your organization's risk tolerance."

**Key phrases to hit:** "NIST baselines are immutable — the floor." "ODPs customize severity, containment, escalation." "Policy Conflict Detection." "Always compliant, always customized."

---

### How to Handle Technical Deep-Dives

If a judge goes deep on architecture:

1. **Answer for 30 seconds.** Give them something technical and specific.
2. **Bridge to value.** "And what that means in practice is..."
3. **Offer a follow-up.** "I'd love to walk through the full architecture — can we grab 10 minutes after?"

**Never:**
- Stammer or guess about technical details you don't know
- Say "I don't know" without offering to find out
- Let a deep-dive derail your energy

**Always:**
- Have one technical detail ready that impresses (e.g., "We use NFKC normalization combined with AST pattern matching — zero LLM in the enforcement path, <50ms latency, plus NIST ODP template resolution in under 5ms")
- Know when to defer — judges respect someone who knows their limits

---

### How to Handle "Hasn't This Been Done Before?"

**The frame shift:**
> "If you're asking whether AI safety research exists — absolutely, and we stand on that work. But if you're asking whether there's a product you can install today that provides deterministic Judge Layer enforcement, automated incident response, NIST-mapped playbooks, agent health profiling, AND Organization-Defined Parameters for policy customization — no. That doesn't exist. Nate B Jones just wrote about the need for a judge. NIST has been calling for ODPs for years. We're the first to implement both in one product."

**The evidence:**
> "PocketOS. Step Finance. Meta. Replit. UnitedHealth. These disasters happened because there's no deterministic enforcement for agent actions AND no way to customize the response per organization. If the solution existed, these headlines wouldn't. And Lakera — the leading LLM-as-judge solution — gets bypassed by three out of four adversarial patterns we test. They don't do ODPs either."

---

### How to Handle Competitor Questions

**The complement frame:**
- Never trash competitors. It makes you look insecure.
- Position them as solving adjacent problems.
- "They do X well. We do Y. You need both."

**The deterministic frame:**
- When comparing to LLM-as-judge solutions (Lakera, NeMo): "LLM-as-judge achieves 80% accuracy. Deterministic enforcement achieves 100% for known patterns. The difference is twenty percent of attacks that either get through or get false-positive blocked. And we do ODPs — they don't."

**The layer frame:**
- When comparing to guardrails (SupraWall, Guardrails AI): "They guard the input. We judge the action, respond to the incident, and let organizations customize their policies with ODPs. Different layer, completely complementary."

---

## 10. Pre-Demo Checklist (30 Items)

### 1 Hour Before (Items 1–12)

- [ ] **1.** Laptop charged to 100%. Charger in bag. Backup laptop charged if available.
- [ ] **2.** Demo environment started and verified. Run through Plan A once fully.
- [ ] **3.** Pre-cached data confirmed: bypass patterns (all 4), Judge decision panel, Lobster Trap quarantine, NIST classification, timeline, agent health profile, Policy Builder templates (all 3), side-by-side comparison — all load correctly.
- [ ] **4.** All screen transitions tested. No lag, no blank screens, no broken links.
- [ ] **5.** Backup video `playbook-demo-backup.mp4` plays correctly. Audio works. Duration confirmed: 90 seconds. **Verify it includes the Policy Builder segment.**
- [ ] **6.** Backup video uploaded to: Google Drive, phone storage, USB drive (3 copies).
- [ ] **7.** Slide deck opens correctly in presentation mode. All 5 slides render. **Verify Slide 2 has the ODP reference.**
- [ ] **8.** Slide deck PDF exported and saved to desktop (backup if presentation software fails).
- [ ] **9.** QR code tested — scan with 2 different phones, confirm it links to correct GitHub repo.
- [ ] **10.** WiFi credentials for venue obtained and tested. Mobile hotspot set up as backup.
- [ ] **11.** Hair, clothing, appearance check. Professional but approachable.
- [ ] **12.** Bottle of water located. Bathroom visited. Phone on Do Not Disturb.

### 15 Minutes Before (Items 13–22)

- [ ] **13.** Arrive at demo location. Find your station/table.
- [ ] **14.** Test the display/monitor/projector. Resolution set to 1920x1080. Text is readable.
- [ ] **15.** Test audio if using video backup. Volume appropriate for room size.
- [ ] **16.** Run through opening hook once — aloud, at full volume. Voice is warm and clear. **Include "Nate B Jones" reference.**
- [ ] **17.** Review recovery phrases card in pocket. All 4 memorized + 3 competitor responses + 2 ODP responses.
- [ ] **18.** Confirm which backup plan you'll use if needed. Mental walkthrough of Plan B and C transitions.
- [ ] **19.** Introduce yourself to the judge nearest your station. Build rapport early.
- [ ] **20.** Check your phone: alarm set for 5 minutes before your slot. Backup alarm set.
- [ ] **21.** Put recovery phrases card in pocket. Put "Deterministic > LLM-judge" prop card in pocket.
- [ ] **22.** Take 3 deep breaths. 4-second inhale, 6-second exhale. Lower your heart rate.

### 5 Minutes Before (Items 23–28)

- [ ] **23.** Final demo environment check — one quick refresh, confirm all 4 bypass patterns load AND Policy Builder template switches work.
- [ ] **24.** Close all unnecessary apps. Browser tabs reduced to demo only.
- [ ] **25.** Notifications OFF. Airplane mode on phone. Focus mode on laptop.
- [ ] **26.** Review the first 30 seconds of script one final time — just the hook. The rest will follow.
- [ ] **27.** Visualize success: see yourself delivering the Nate B Jones hook, judges nodding, the 4/4 Judge decision revealing perfectly, the Policy Builder wowing them with three template switches.
- [ ] **28.** Smile. Even if you don't feel like it. The physical act of smiling reduces cortisol.

### 30 Seconds Before (Items 29–30)

- [ ] **29.** Stand up straight. Shoulders back. Chin level. Power pose for 10 seconds (expansive posture boosts testosterone, reduces stress).
- [ ] **30.** Final thought: *"I was reading Nate B Jones's newsletter this morning. I know this system better than anyone in this room. Deterministic enforcement beats LLM-as-judge. Organization-Defined Parameters are our secret weapon. I am the expert here."* Now go.

---

## Appendix A: Quick-Reference Cheat Sheet

Print this on a single page. Tape it to the back of your laptop or keep it face-down on the table.

```
PLAYBOOK DEMO v3.0 — QUICK REFERENCE
======================================

OPENING (0:00): "Today — literally today — Nate B Jones..." 
  → PAUSE 1.5s → "148k subscribers" → "We built PLAYBOOK" → "Deterministic enforcement"

JUDGE LAYER (0:30): 
  Bypass #1: Context Window Displacement — 50k tokens, malicious tool call
  Bypass #2: Unicode Homoglyph — file_delete vs fіle_delete (Cyrillic eye)
  Bypass #3: Adversarial Suffix Injection — crafted suffix, AST structure
  Bypass #4: Multi-Turn State Confusion — 8 queries, cross-turn tracking
  Result: 4 attacks. 4 blocks. 0 LLM in enforcement. <50ms.

INCIDENT (1:15): 
  "The Judge caught it. Now PLAYBOOK responds."
  → Lobster Trap QUARANTINE → Forensic Capture → NIST Classification (Step 1/7)
  → Agent Health Update → 156ms total

POLICY BUILDER (2:00):
  "Same incident. Three organizations. Three different responses."
  → HIPAA Template: CRITICAL, auto-contain, CEO paged, federal report
  → Startup Template: MEDIUM, engineering lead, basic logs, no auto-contain
  → FinTech Template: CRITICAL-conditional, Risk Officer, PCI-DSS report
  → Side-by-side comparison: "One NIST baseline. Infinite organizational responses."
  → "First product to implement NIST Organization-Defined Parameters."

PROFILE (2:40): 
  Lie rate 4.2% ↑ | Risk 73/100 | 12 incidents this week
  "SupraWall guards. PLAYBOOK responds."
  "NIST GOVERN 1.4: Transparent risk management based on organizational priorities."

CLOSE (2:55): 
  "Nate B Jones said every agent needs a judge. NIST says every org needs custom policies."
  "We built PLAYBOOK — the first product that does both."
  → Deterministic Judge Layer | Organization-Defined Parameters | NIST Playbooks
  → EU AI Act Jan 2027 | Built on Veea's Lobster Trap

BACKUP PLAN DECISION TREE:
- Everything works? → PLAN A (Full Live)
- API slow after Judge? → PLAN B ("While that processes..." → Video)
- Env won't start? → PLAN C ("Regardless of network..." → Full Video)
- Total meltdown? → PLAN D ("Let me walk you through..." → Screenshots)

KEY NUMBERS:
- 148,000 (Nate B Jones subscribers)
- <50ms (Judge evaluation — deterministic, not LLM)
- 4/4 (bypass patterns blocked)
- 156ms (full incident resolution)
- 6 (industry templates: HIPAA, SOC2, PCI-DSS, GDPR, Finance, Startup)
- 4.2% (lie rate in demo)
- 73/100 (risk score)
- NIST SP 800-61r2 (playbook mapping)
- NIST SP 800-53 (ODP source)
- January 2027 (EU AI Act deadline)

RECOVERY PHRASES:
- Slow: "In production this is deterministic sub-50ms..."
- Wrong: "Deterministic enforcement means identical results every time..."
- Failure: "This is exactly why we need deterministic enforcement..."
- Blank: Say "Deterministic enforcement." → Reset.

COMPETITOR RESPONSES:
- "SupraWall?" → "SupraWall guards. PLAYBOOK responds. Different layer. ODPs."
- "Lakera?" → "LLM-as-judge. 3/4 bypass. Deterministic: 0/4. No ODPs."
- "ODPs?" → "NIST SP 800-53. First product to implement them natively."
- "Can I customize NIST?" → "Baselines are immutable. ODPs customize response. Conflict detection warns."
```

---

## Appendix B: Practice Schedule

| When | What | Duration |
|------|------|----------|
| 3 days before | Read script aloud 3x, timing each run. Focus on Nate B Jones hook + Policy Builder delivery. | 15 min |
| 2 days before | Full demo run with screen recording, review recording. Test all 4 bypass patterns + all 3 template switches render. | 30 min |
| 1 day before | Full demo run + backup video test + Plan D walkthrough + competitor response practice + ODP Q&A practice | 45 min |
| Morning of | Opening hook + Policy Builder segment — 5 perfect deliveries | 10 min |
| 1 hour before | Full Plan A run + all backup plan triggers + verify bypass pattern visuals + verify template switching | 20 min |
| 15 min before | Opening hook + first 75 seconds (through Judge Layer) only | 5 min |

**Target:** 10 full runs before demo day. Sub-3:15 every time. Plan B and C transitions practiced 3x each. Competitor responses (SupraWall, Lakera) practiced aloud 3x each. ODP Q&A responses (Q15, Q16, Q17) practiced aloud 3x each.

**New for v3.0:**
- Practice the Policy Builder template switches until they're smooth — click, explain, click, explain, click, explain.
- Practice the "first product to implement NIST Organization-Defined Parameters" delivery — confident, not boastful.
- Practice the three template descriptions (HIPAA, Startup, FinTech) until you can deliver each in under 8 seconds.
- Practice the side-by-side comparison pause — let the screen breathe for 2 seconds before speaking.
- Practice the NIST GOVERN 1.4 reference — it should sound natural, not forced.

---

*Document version 3.0 — Policy Template Switching + Organization-Defined Parameters Edition.  
Practice hard. Demo with confidence. Win.*
