# AGENTS Cross-Verification Report v2.0

> **Date:** 2026-05-12  
> **Baseline:** `AGENTS.md` v1.2, `Development_Plan.md` v1.1  
> **Documents Audited:** All 13 files under `projectdocs/` (38,403 lines total)  
> **Previous Report:** `AGENTS_CROSS_VERIFICATION_REPORT.md` (v1.0, 24 issues)

---

## Executive Summary

The project documents have undergone a **major update** since the initial cross-verification. Four new files were added, and all existing `.md` files were refreshed. This report identifies **31 new or changed items** across 5 severity categories, with a focus on the **Policy Builder** (new architectural pillar), **expanded database schema** (20 tables + 1 view), **DEMO-006 replacement**, and **honest competitive positioning**.

### Severity Breakdown

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 3 | Schema gaps, auth conflicts, P0 architectural drift |
| **Major** | 8 | New features, changed numbers, missing env vars |
| **Minor** | 12 | Naming inconsistencies, outdated references |
| **Info** | 6 | New files, expanded scopes, documentation additions |
| **Resolved** | 2 | Previously identified issues now fixed |

---

## Critical Issues (3)

### C1 — Database Schema Incident Type Gap
**Status:** UNRESOLVED  
**Severity:** Critical

- **Functional Requirements** (v1.2) defines **16 incident types** (AGT-DEL-001 through AGT-REG-016)
- **Database Schema** (v1.2) implements only **12 type codes** (AGT-DEL-001 through AGT-GAP-012)
- **Missing:** AGT-SPY-013, AGT-BYP-014, AGT-PRV-015, AGT-REG-016

**Impact:** 4 incident types have no database representation, no NIST baseline, and no default playbook mapping.  
**Resolution:** Add the 4 missing types to `incidents.category` CHECK constraint, `nist_baselines`, `playbooks`, and `detection_rules` tables in Alembic migration #2.

---

### C2 — Authentication Conflict Persists
**Status:** PARTIALLY RESOLVED  
**Severity:** Critical

- **Technical Specification** (Section 5.2) still lists **ALL endpoints as `Auth: None`**
- **API Documentation** (v1.6.0) requires Bearer JWT on all endpoints except `/health`
- **AGENTS.md** v1.2 notes this as a "documentation error" in the Technical Spec

**Impact:** Risk of implementing without auth if a developer follows the Technical Spec literally.  
**Resolution:** Already noted in AGENTS.md. Technical Spec needs explicit update.

---

### C3 — DEMO_MODE Incident Count Conflict
**Status:** RESOLVED in AGENTS.md v1.2  
**Severity:** Critical (was)

- **Demo Script** (v3.0): 6 demo scenarios
- **NFR** (V-030, V-049): "Dashboard loads with 20 incidents"
- **Old AGENTS.md** v1.1: "pre-seeds 6 incidents"

**Resolution in v1.2:** Clarified as "6 demo scenarios (20 synthetic incidents total)." The 6 scenarios comprise 20 individual incident records.

---

## Major Issues (8)

### M1 — Policy Builder: Entirely New P0 Feature
**Status:** ADDRESSED in AGENTS.md v1.2 + Development Plan v1.1  
**Severity:** Major

A full **Custom Policy Builder** was introduced in `CUSTOM_POLICY_BUILDER_Design.md` and `PLAYBOOK_Functional_Requirements.md` v1.2:
- 8 new features (FEAT-021 through FEAT-028)
- 14 new API endpoints
- 5 new database tables + 1 view
- 6 industry templates
- ODP Resolution Engine feeding into Judge Layer

**Impact:** Was not in AGENTS.md v1.1 or Development Plan v1.0 at all.  
**Resolution:** Added to both files. Policy Builder is now Phase 8 in Development Plan.

---

### M2 — Database Schema Expanded from 10 → 20 Tables + 1 View
**Status:** ADDRESSED in AGENTS.md v1.2  
**Severity:** Major

The old schema (10 tables) is replaced by a production-grade 20-table + 1-view design in `PLAYBOOK_Database_Schema.md` v1.2. Key additions:
- Judge Layer tables: `judge_decisions`, `bypass_patterns`, `bypass_attempts`, `suprawall_events`
- Policy Builder tables: `nist_baselines`, `organization_odps`, `policy_versions`, `industry_templates`, `odp_conflicts`
- Supporting tables: `agents`, `playbook_actions`, `audit_log`, `gemini_cache`, `agent_health_history`, `detection_rules`, `demo_scenarios`, `compliance_mappings`
- View: `resolved_policies`

**Impact:** Alembic migration #1 (original 10 tables) is now migration #1 + #2.  
**Resolution:** Updated AGENTS.md with full table inventory.

---

### M3 — DEMO-006 Replaced: Bypass Attempt → Policy Switching
**Status:** ADDRESSED in Development Plan v1.1  
**Severity:** Major

The v3.0 Demo Script replaces DEMO-006:
- **Old:** LLM-Judge Bypass Attempt (AGT-BYP-014)
- **New:** Organization Policy Switching (AGT-EXT-005 under HIPAA → SaaS Startup → FinTech)

**Impact:** Old demo scenario fixtures, slide deck storyboard, and backup video are now obsolete.  
**Resolution:** Updated Development Plan Phase 6 with new scenario table and demo script alignment.

---

### M4 — Judge Layer Latency Target Tightened
**Status:** ADDRESSED in AGENTS.md v1.2  
**Severity:** Major

- **Old:** Classification ≤ 50ms (p95)
- **New:** Core target ≤ 40ms; p95 SLA ≤ 50ms; p99 ≤ 100ms

**Source:** `PLAYBOOK_Non_Functional_Requirements.md` v2.0, `PLAYBOOK_AI_Agent_Documentation.md` v2.1.0  
**Resolution:** Updated latency targets in AGENTS.md.

---

### M5 — New Environment Variables for Policy Builder
**Status:** ADDRESSED in AGENTS.md v1.2  
**Severity:** Major

3 new env vars required:
- `POLICY_BUILDER_ENABLED` (default `true`)
- `NIST_BASELINE_PATH` (default `./data/nist_baselines.json`)
- `ODP_DEFAULTS_PATH` (default `./data/odp_defaults.json`)

**Resolution:** Added to Key Configuration table.

---

### M6 — Railway Sleep Timeout Changed
**Status:** ADDRESSED in AGENTS.md v1.2  
**Severity:** Major

- **Old AGENTS.md v1.1:** 15 min (from NFR)
- **Deployment Guide:** 30 min
- **Updated AGENTS.md v1.2:** 30 min (with UptimeRobot note)

**Resolution:** Updated to match Deployment Guide explicitly.

---

### M7 — Bypass Pattern Naming Multiplied
**Status:** DOCUMENTED in AGENTS.md v1.2  
**Severity:** Major

The 4 canonical bypass patterns now have **multiple names** across documents:

| Canonical | NFR Alias | API Doc Alias | Demo Script Variant |
|-----------|-----------|---------------|---------------------|
| Context Window Displacement | RoleSwap | context_window | Context Window Displacement |
| Indirect Tool Chaining | Separator | delimiter, encoding | Multi-Turn State Confusion |
| Unicode Homoglyph | Base64 | encoding | Unicode Homoglyph |
| Confidence Hijacking | SocialEngineering | social_engineering | Adversarial Suffix Injection |

**Impact:** Test vectors, demo labels, and API enums use different vocabularies.  
**Resolution:** Added alias mapping in AGENTS.md. Canonical 4 names are primary.

---

### M8 — New Compliance Frameworks Mapped
**Status:** ADDRESSED in AGENTS.md v1.2  
**Severity:** Major

`PLAYBOOK_EU_AI_Act_NIST_Compliance_Mapping.md` v1.1 adds:
- **NIST AI 600-1 GenAI Profile:** Map 1.1, Measure 2.1, Manage 3.1
- **SOC 2 Type II:** CC6.1, CC7.2, CC7.3
- **NIST SP 800-53:** ODP source citation
- **NIST SP 800-61r2:** Incident response playbook mapping

**Resolution:** Added all new frameworks to Compliance section.

---

## Minor Issues (12)

### m1 — Token Expiry: 60m vs 24h
**API Doc:** `ACCESS_TOKEN_EXPIRE_MINUTES=60`  
**NFR:** 24 hours  
**AGENTS.md v1.2:** 24h production, 60m dev  
**Status:** Documented as configurable.

---

### m2 — Rate Limits: 60 vs 100 vs 120
**API Doc default:** 60 req/min  
**NFR:** 100 req/min per IP  
**Technical Spec config:** 120/min  
**AGENTS.md v1.2:** 100 for production  
**Status:** Documented as configurable via env.

---

### m3 — NIST Baseline Coverage Gap
**NIST baselines** cover 12 of 16 incident types.  
**Missing baselines:** AGT-INJ-006, AGT-RAT-009, AGT-DRF-010, AGT-GAP-012 (or the 4 additional types depending on which 12 are implemented).  
**Status:** Noted in AGENTS.md and Development Plan.

---

### m4 — File Count Budget Pressure
Policy Builder UI adds ~8 React components.  
**Current budget:** ≤ 40 React components.  
**Status:** AGENTS.md v1.2 notes to merge or defer P2 features (marketplace, multi-tenant).

---

### m5 — WebSocket Auth Method
**API Doc:** JWT passed as **query parameter** (`?token={jwt}`)  
**Older docs:** JWT in `Authorization` header  
**Status:** AGENTS.md should note both methods; query param for WS, header for REST.

---

### m6 — Evidence Package Structure Expanded
New directories in evidence packages:
- `judge_layer_decision_log/`
- `bypass_attempt_log/`
- `deterministic_enforcement_proof/`
- `policy/` (nist_baseline_ref.json, active_odps.json, policy_version.json)
- `suprawall/`

**Status:** Noted in Functional Requirements; AGENTS.md updated.

---

### m7 — New WebSocket Events
3 new WS events added:
- `judge.decision`
- `judge.bypass_detected`
- `judge.suprawall_event`

**Status:** Added to API Doc summary; Development Plan updated.

---

### m8 — Judge Pre-Screen Not in Original Pipeline
The Detect Agent now includes a lightweight **Judge Pre-Screen** for bypass patterns.  
**Status:** AGENTS.md pipeline diagram updated.

---

### m9 — Red-Team Detection Rate: 94%
**NFR v2.0:** "94% detection rate on test set"  
**Bypass tests:** 400/400 = 100% on known patterns  
**Status:** 94% refers to the broader red-team test suite (≥50 adversarial tests); 400/400 remains the canonical bypass test.

---

### m10 — MTTD/MTTR/MTTC Targets Added
**NFR v2.0:** MTTD < 500ms, MTTR < 1s, MTTC < 2s  
**Status:** Added to AGENTS.md latency section.

---

### m11 — New Alerting Thresholds (NFR-MON-006)
13 new monitoring thresholds added, including:
- Judge Layer p95 > 50ms → WARNING
- Bypass detection rate < 100% → CRITICAL (P0 alert)
- Memory > 95% → emergency shutdown

**Status:** NFR document is authoritative; AGENTS.md references it.

---

### m12 — Research Synthesis Revises Market Claims
`RESEARCH_SYNTHESIS_HONEST.md` corrects:
- $15B SOAR market → **$1.72B** (Grand View Research 2024)
- "No SOAR for AI agents" → **FALSE** (Swimlane, ServiceNow, Pragatix, Wiz exist)
- Revised score: 91/100 (honest) → 95/100 (with effort)

**Status:** AGENTS.md updated with honest competitive positioning.

---

## Info Items (6)

### i1 — New File: `CUSTOM_POLICY_BUILDER_Design.md`
285 lines. Defines the Policy Builder architecture, 8 features, competitive moat analysis. Added to AGENTS.md document inventory.

---

### i2 — New File: `PLAYBOOK_Database_Schema.md`
3,924 lines. Replaces the old `.docx` file. Production-grade SQLite schema with 20 tables, audit triggers, immutability guarantees. Added to AGENTS.md document inventory.

---

### i3 — New File: `RESEARCH_SYNTHESIS_HONEST.md`
95 lines. Honest market sizing, competitor identification, revised claims. Added to AGENTS.md document inventory.

---

### i4 — New File: `VIDEO_ANALYSIS_Nate_B_Jones.md`
166 lines. Validates Judge Layer architecture, discovers SupraWall (April 2026 competitor). Added to AGENTS.md document inventory.

---

### i5 — Functional Requirements Expanded to FEAT-028
From FEAT-020 to FEAT-028 with Policy Builder features. P0 now includes Policy Builder (FEAT-021–023).

---

### i6 — AI Agent Documentation at v2.1.0
Major expansion with Judge Layer code, 5-prompt deterministic framework, AgentMessageBus, prompt versioning, Judge Risk Profiles, and performance benchmarks (15,000 logs/sec).

---

## Previously Resolved Issues (from v1.0 Report)

| ID | Original Issue | Status in v1.2 |
|----|---------------|----------------|
| C4 | SQLCipher config missing | ✅ `SQLCIPHER_KEY` added to env table |
| C6 | Data retention mismatch | ✅ 90 days incidents, 7 years evidence |

---

## Action Items

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 1 | Add 4 missing incident types to database schema (Alembic migration #2) | Backend | Critical |
| 2 | Update Technical Spec Section 5.2 auth table to `Bearer: Required` | Documentation | Critical |
| 3 | Create 6 industry template JSON files | Backend | Major |
| 4 | Create 12 NIST baseline JSON files (with 4 placeholder gaps) | Backend | Major |
| 5 | Scaffold Policy Builder React components (≤8 files) | Frontend | Major |
| 6 | Update demo scenario fixtures for DEMO-006 (Policy Switching) | Backend | Major |
| 7 | Create `test_policy_builder.py` with baseline/ODP/conflict tests | QA | Major |
| 8 | Verify all 400 bypass test vectors use canonical pattern names | QA | Minor |
| 9 | Add `judge_pre_screen` to Detect Agent | Backend | Minor |
| 10 | Update slide deck storyboard for Policy Builder segment (40s) | Demo/Pitch | Minor |

---

*Report generated: 2026-05-12*  
*Baseline: AGENTS.md v1.2, Development_Plan.md v1.1*
