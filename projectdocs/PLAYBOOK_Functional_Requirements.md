# Functional Requirements Document

## PLAYBOOK — Automated Incident Response for AI Agents

| Attribute | Value |
|---|---|
| **Document ID** | FRD-PLAYBOOK-001 |
| **Version** | 1.2 |
| **Status** | Draft |
| **Author** | Product Management |
| **Date** | 2026-05-15 |
| **Classification** | Internal |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Use Cases](#2-use-cases)
3. [Feature Requirements](#3-feature-requirements)
4. [User Interface Requirements](#4-user-interface-requirements)
5. [Integration Requirements](#5-integration-requirements)
6. [Demo Scenarios](#6-demo-scenarios)
7. [Appendices](#7-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Functional Requirements Document (FRD) defines the complete functional specification for **PLAYBOOK**, an automated incident response system purpose-built for AI agent operations. PLAYBOOK provides a 4-stage pipeline — **DETECT → CLASSIFY → RESPOND → FORENSICS** — that continuously monitors AI agent activity, detects anomalous or malicious behavior, classifies incidents by type and severity, executes automated containment responses, and generates forensic evidence packages for audit and compliance.

PLAYBOOK is built on three pillars: a **deterministic Judge Layer** that enforces policy without LLM dependency, **NIST IR 8346 (AG-MG.1) playbooks** for structured incident response, and a **forensic evidence system** for compliance and audit. This architecture is informed by Nate B Jones' analysis of the "AI Agent Judge Layer" pattern (May 11, 2026), which establishes the Judge Layer as the critical enforcement component for agent safety — a deterministic, rule-based classification and enforcement engine that intercepts every agent action before execution and renders an irreversible decision (ALLOW, DENY, QUARANTINE, or ESCALATE).

The primary purpose of PLAYBOOK is to reduce mean time to detection (MTTD) and mean time to response (MTTR) for AI agent incidents from hours or days to seconds, while maintaining full regulatory compliance under the EU AI Act, HIPAA, and emerging AI governance frameworks. The Judge Layer ensures that enforcement is immune to the four known LLM-judge bypass patterns identified in current research: context displacement, tool chaining, homoglyph injection, and confidence hijacking.

### 1.2 Scope

**In Scope:**

- Real-time log ingestion from AI agent systems
- Anomaly detection across 16 incident type classifications
- Local incident classification engine with optional LLM enhancement
- **Deterministic Judge Layer for action interception and enforcement (FEAT-017, FEAT-019)**
- **LLM-judge bypass pattern detection and defense (FEAT-018)**
- **SupraWall guardrail integration and decision correlation (FEAT-020)**
- **NIST baseline policy templates with ODP placeholders (FEAT-021)**
- **Organization-defined parameters (ODPs) per incident type (FEAT-022)**
- **Visual Policy Builder for ODP customization (FEAT-023)**
- **Industry policy templates (HIPAA, SOC2, PCI-DSS, GDPR) (FEAT-024)**
- **Policy conflict detection between ODPs and NIST baselines (FEAT-025)**
- **Policy versioning, audit trail, and rollback (FEAT-026)**
- **Community policy marketplace for ODP configurations (FEAT-027)**
- **Multi-tenant department-level ODP overrides (FEAT-028)**
- Automated response playbook execution (quarantine, deny, log, human-review, rate-limit)
- Forensic timeline reconstruction and evidence package generation
- Agent health monitoring dashboard
- Compliance mapping and regulatory report export (EU AI Act)
- Demo mode with 5 pre-built disaster scenarios
- Red-team test suite for continuous validation

**Out of Scope:**

- General-purpose SIEM replacement (PLAYBOOK augments, not replaces, existing SIEM)
- Non-agent infrastructure monitoring (e.g., traditional server monitoring)
- Model training or fine-tuning
- Human-agent chat interfaces

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **Agent** | An autonomous or semi-autonomous AI system that performs tasks on behalf of users, including tool use, API calls, and data manipulation |
| **Anomaly** | A deviation from established behavioral baselines that may indicate a security incident |
| **Baseline** | A statistical profile of normal agent behavior used as a reference for anomaly detection |
| **Bypass Pattern** | An adversarial technique designed to evade LLM-based guardrails or safety controls (e.g., context window stuffing, homoglyph injection) |
| **Deterministic Classification** | Rule-based classification that produces consistent, reproducible decisions without LLM involvement |
| **DEMO_MODE** | A feature flag that, when enabled, loads pre-built incident scenarios for demonstration and training purposes |
| **Evidence Package** | A structured, tamper-evident archive containing all artifacts related to an incident (logs, metadata, timeline, classification) |
| **Forensic Timeline** | A chronological reconstruction of events leading to, during, and after an incident |
| **Hallucination Cascade** | A failure mode where an agent's incorrect output triggers a chain of downstream errors or actions |
| **Homoglyph** | A character that visually resembles another but has a different Unicode code point, used to evade string-based filters |
| **Judge Layer** | A deterministic enforcement component that intercepts every agent action before execution and renders a policy decision |
| **Lobster Trap** | The inline data protection infrastructure (DPI) that intercepts and can block agent tool calls in real time |
| **MTTD** | Mean Time To Detection — the average time between an incident occurring and being detected |
| **MTTR** | Mean Time To Response — the average time between detection and the start of automated response |
| **ODP** | Organization-Defined Parameter — a customizable value that overrides NIST baseline defaults per incident type |
| **Playbook** | A predefined, ordered set of response actions triggered automatically upon incident classification |
| **Red-Team Test** | A simulated adversarial attack designed to validate detection and response capabilities |
| **SupraWall** | An open-source (Apache 2.0) AI agent guardrail framework; PLAYBOOK's closest competitor in the agent security space |
| **TerraFabric** | The fleet management platform for AI agents, providing deployment and health data |
| **Tool Call** | An invocation by an AI agent of an external function, API, or service |

### 1.4 References

| ID | Reference | Description |
|----|-----------|-------------|
| REF-001 | NIST AI RMF 1.0 | NIST AI Risk Management Framework |
| REF-002 | NIST Agentic Profile | NIST IR 8346, AG-MG.1: Incident Response for AI Agents |
| REF-003 | EU AI Act 2024 | Regulation (EU) 2024/1689, Articles 9 (Risk Management), 15 (Accuracy/Robustness), 73 (Incident Reporting) |
| REF-004 | EU AI Act Art. 9 | Requirement for providers to establish a risk management system throughout the lifecycle of high-risk AI systems |
| REF-005 | EU AI Act Art. 15 | Requirement for high-risk AI systems to achieve appropriate levels of accuracy, robustness, and cybersecurity |
| REF-006 | EU AI Act Art. 73 | Obligation to report serious incidents to market surveillance authorities without undue delay |
| REF-007 | HIPAA 45 CFR 164.306 | Security standards for the protection of electronic protected health information |
| REF-008 | ISO/IEC 23053:2022 | Framework for AI systems using ML |
| REF-009 | OWASP LLM Top 10 | OWASP Top 10 for Large Language Model Applications |
| REF-010 | MITRE ATLAS | Adversarial Threat Landscape for Artificial-Intelligence Systems |
| REF-011 | Jones, N.B. (2026) | "AI Agent Judge Layer" — establishes deterministic rule-based enforcement as the critical safety component for autonomous agent systems, May 11, 2026 |
| REF-012 | SupraWall (2026) | Open-source AI agent guardrail framework (Apache 2.0), released April 30, 2026; closest competitor providing inline guardrail detection for agent tool calls |

### 1.5 System Overview

PLAYBOOK operates as a dedicated incident response layer in the AI agent stack. It sits between the agent orchestration layer and the external tool/API layer, monitoring all tool calls, data flows, and agent outputs through the Lobster Trap DPI infrastructure. The **Judge Layer** (FEAT-019) is a separate enforcement component wrapped around all agent actions — it intercepts every action before execution and applies deterministic classification (FEAT-017) to render an immediate decision: **ALLOW**, **DENY**, **QUARANTINE**, or **ESCALATE**. This ensures that enforcement is never dependent on an LLM and is immune to adversarial bypass attempts.

The **Custom Policy Builder** (FEAT-021 through FEAT-028) enables organizations to customize incident response policies starting from immutable NIST baselines. Organizations define their own parameters (ODPs) through a visual interface, apply industry templates, detect policy conflicts, track version history, share configurations in a marketplace, and manage multi-tenant departmental policies.

**High-Level Architecture:**

```
+-------------------------------------------------------------------------+
|                         PLAYBOOK SYSTEM                                 |
+------------+-------------+-------------+-----------------------------+--+
|   DETECT   |  CLASSIFY   |   RESPOND   |         FORENSICS           |J |
|            |             |             |                             |U |
| Log        | Rule        | Playbook    | Timeline                    |D |
| Ingestion  | Engine      | Library     | Reconstruction              |G |
|            |             |             |                             |E |
| Anomaly    | Local       | Auto        | Evidence                    | |
| Detection  | Classifier  | Execution   | Package                     |L |
|            |             |             |                             |A |
| Baseline   | Gemini      | Lobster     | Compliance                  |Y |
| Engine     | Overlay     | Trap DPI    | Mapping                     |E |
|            |             |             |                             |R |
|            |             |             |                             |  |
+------------+-------------+-------------+-----------------------------+--+
       ^                                                |                |
       |                                                v                |
+----------------+                           +----------------------+    |
|  AGENT SYSTEM  |<--------------------------->|   EVIDENCE STORE     |    |
|  (TerraFabric) |      Inline Block          |   (Immutable Logs)   |    |
+----------------+                           +----------------------+    |
       |                                                                 |
       |    Every agent action intercepted by Judge Layer (FEAT-019)     |
       |    Deterministic classification: ALLOW / DENY / QUARANTINE /    |
       |    ESCALATE — immune to LLM-judge bypass patterns               |
       v                                                                 |
+---------------------------------------------------------------------+  |
|  JUDGE LAYER (FEAT-019)                                             |  |
|  +---------------------------+  +-------------------------------+   |  |
|  | Deterministic Classifier  |  | Bypass Detection (FEAT-018)   |   |  |
|  | (FEAT-017)                |  |                               |   |  |
|  | - Rule-based, no LLM      |  | - Context displacement        |   |  |
|  | - <50ms response          |  | - Homoglyph injection         |   |  |
|  | - 100% bypass catch rate  |  | - Confidence hijacking        |   |  |
|  |                           |  | - Tool chaining               |   |  |
|  | Decision: ALLOW | DENY    |  |                               |   |  |
|  |           | QUARANTINE    |  | Report -> Dashboard            |   |  |
|  |           | ESCALATE      |  |         (FEAT-009)            |   |  |
|  +---------------------------+  +-------------------------------+   |  |
|  +---------------------------+  +-------------------------------+   |  |
|  | SupraWall Integration     |  | Decision Rationale Logging    |   |  |
|  | (FEAT-020)                |  | for Audit Trail               |   |  |
|  | - Detect existing         |  |                               |   |  |
|  |   SupraWall guardrails    |  | Every decision logged with    |   |  |
|  | - Complement (not replace)|  | full context for compliance   |   |  |
|  | - Feed decisions into     |  |                               |   |  |
|  |   PLAYBOOK forensics      |  |                               |   |  |
|  +---------------------------+  +-------------------------------+   |  |
+---------------------------------------------------------------------+  |
```

**PLAYBOOK = Judge Layer + NIST Playbooks + Forensics**

The Judge Layer provides the deterministic enforcement foundation. NIST IR 8346 playbooks provide the structured response procedures. The forensics system provides the evidence trail for compliance. Together, these three pillars ensure that AI agent operations are secure, auditable, and compliant.

### 1.6 Incident Type Taxonomy

PLAYBOOK recognizes and classifies 16 distinct incident types, each with a unique identifier prefix, severity baseline, and default playbook assignment:

| ID | Incident Type | Description | Default Severity | Default Playbook |
|----|--------------|-------------|------------------|------------------|
| **AGT-DEL-001** | Data Destruction | Agent executes or attempts destructive operations on databases, files, or persistent storage | CRITICAL | PBP-001-Data-Destruction-Block |
| **AGT-FIN-002** | Unauthorized Financial | Agent initiates financial transactions, commitments, or value transfers without explicit authorization | CRITICAL | PBP-002-Financial-Deny |
| **AGT-PER-003** | Permission Escalation | Agent attempts to gain permissions, roles, or access levels beyond its authorized scope | HIGH | PBP-003-Permission-Contain |
| **AGT-HRM-004** | Harmful Output | Agent generates outputs that are discriminatory, dangerous, or violate safety policies | HIGH | PBP-004-Harmful-Quarantine |
| **AGT-EXT-005** | Data Exfiltration | Agent transfers data to unauthorized external destinations or in volumes exceeding policy | CRITICAL | PBP-005-Exfiltration-Block |
| **AGT-INJ-006** | Prompt Injection | Detected prompt injection attempts (direct, indirect, or jailbreak) targeting the agent | HIGH | PBP-006-Injection-Block |
| **AGT-HAL-007** | Hallucination Cascade | Agent produces factually incorrect outputs that trigger downstream errors or actions | MEDIUM | PBP-007-Hallucination-Flag |
| **AGT-CRE-008** | Credential Exposure | Agent outputs or logs contain exposed credentials, tokens, or secrets | HIGH | PBP-008-Credential-Rotate |
| **AGT-RAT-009** | Rate Limit Abuse | Agent makes tool calls at frequencies violating rate limit policies or fair use agreements | MEDIUM | PBP-009-RateLimit-Throttle |
| **AGT-DRF-010** | Model Drift | Detected deviation in model behavior from baseline performance characteristics | MEDIUM | PBP-010-Drift-Alert |
| **AGT-TLM-011** | Tool Misuse | Agent uses tools in ways inconsistent with their intended purpose or documentation | MEDIUM | PBP-011-ToolMisuse-Review |
| **AGT-GAP-012** | Coverage Gap | Agent operates in an area lacking sufficient monitoring, policy coverage, or guardrails | LOW | PBP-012-Coverage-Alert |
| **AGT-SPY-013** | Systematic Espionage | Agent exhibits patterns of information gathering across multiple sessions or scopes | HIGH | PBP-013-Espionage-Isolate |
| **AGT-BYP-014** | Guardrail Bypass | Agent attempts to circumvent or disable safety controls, monitoring, or logging | CRITICAL | PBP-014-Bypass-Shutdown |
| **AGT-PRV-015** | Privacy Violation | Agent processing of personal data violates privacy policies, consent, or data minimization | HIGH | PBP-015-Privacy-Redact |
| **AGT-REG-016** | Regulatory Trigger | Agent activity triggers a specific regulatory reporting obligation (e.g., EU AI Art. 73) | HIGH | PBP-016-Regulatory-Report |

---

## 2. Use Cases

### UC-001: Detect Agent Data Destruction

| Attribute | Value |
|-----------|-------|
| **ID** | UC-001 |
| **Name** | Detect Agent Data Destruction |
| **Priority** | P0 |
| **Actor** | System Operator, Security Analyst |
| **Demo Scenario** | PocketOS — Mass database table deletion |

**Description:**
The system detects when an AI agent executes or attempts to execute destructive data operations such as `DROP TABLE`, `DELETE *`, `rm -rf`, or equivalent destructive API calls. This includes both successful executions and blocked attempts.

**Preconditions:**
- Log ingestion pipeline is active (FEAT-001)
- Anomaly detection rules for data destruction are enabled (FEAT-002)
- Baseline for normal database operations has been established

**Flow:**
1. Agent invokes a tool call containing destructive operation patterns
2. Lobster Trap DPI intercepts the tool call
3. Log Ingestion module receives the tool call event
4. Anomaly Detection Rules engine matches against AGT-DEL-001 signatures
5. Severity is scored based on scope (rows affected, table criticality, backup availability)
6. Incident is created with classification AGT-DEL-001
7. Automated response playbook PBP-001 is triggered
8. Forensic timeline begins capturing events
9. Operator receives real-time alert

**Postconditions:**
- Incident record exists in the system
- Response actions have been executed or queued
- Evidence package has been initialized

**Acceptance Criteria:**
- AC1: System detects `DROP`, `DELETE *`, `TRUNCATE`, and `rm -rf` equivalent operations within 500ms of tool call
- AC2: System correctly distinguishes destructive operations from read-only operations
- AC3: System assigns CRITICAL severity to database structure modifications
- AC4: System triggers PBP-001 playbook automatically
- AC5: Demo scenario for PocketOS deletion event produces complete incident in < 2 seconds

---

### UC-002: Detect Unauthorized Financial Transaction

| Attribute | Value |
|-----------|-------|
| **ID** | UC-002 |
| **Name** | Detect Unauthorized Financial Transaction |
| **Priority** | P0 |
| **Actor** | Financial Controller, Security Analyst, Compliance Officer |
| **Demo Scenario** | Step Finance — $40M unauthorized commitment |

**Description:**
The system detects when an AI agent initiates, authorizes, or commits to financial transactions beyond its authorized scope or threshold. This includes transfers, trades, commitments, swaps, and any value-moving operations.

**Preconditions:**
- Log ingestion pipeline is active (FEAT-001)
- Financial transaction detection rules are enabled (FEAT-002)
- Agent financial authorization limits are configured

**Flow:**
1. Agent invokes a financial tool (e.g., `transfer`, `swap`, `commit`, `trade`)
2. Log Ingestion captures the tool call with full parameter payload
3. Anomaly Detection Rules engine matches against AGT-FIN-002 signatures
4. Rule engine evaluates amount against agent's authorization threshold
5. If amount exceeds threshold, severity escalated to CRITICAL
6. Gemini Enhancement Overlay analyzes intent and context
7. Incident classified as AGT-FIN-002 with severity CRITICAL
8. PBP-002 playbook triggers — tool call is DENIED before execution
9. Evidence package captures the full request payload for audit
10. Financial Controller and Compliance Officer receive immediate alert

**Postconditions:**
- Transaction is blocked before execution
- Incident record contains full financial details
- Compliance-mapped evidence package is available

**Acceptance Criteria:**
- AC1: System detects financial tool invocations within 200ms
- AC2: System evaluates amount against configured thresholds in < 100ms
- AC3: System blocks transactions exceeding authorization limits before execution
- AC4: System generates alert to Financial Controller within 1 second of detection
- AC5: Demo scenario for Step Finance $40M event blocks commitment and generates complete evidence package

---

### UC-003: Detect Permission Escalation

| Attribute | Value |
|-----------|-------|
| **ID** | UC-003 |
| **Name** | Detect Permission Escalation |
| **Priority** | P0 |
| **Actor** | Security Analyst, System Administrator |
| **Demo Scenario** | Meta — Permission scope exposure |

**Description:**
The system detects when an AI agent attempts to gain permissions, roles, scopes, or access levels beyond its authorized configuration. This includes IAM role requests, privilege escalation API calls, OAuth scope expansion, and policy modification attempts.

**Preconditions:**
- Log ingestion pipeline is active (FEAT-001)
- Permission escalation detection rules are enabled (FEAT-002)
- Agent permission baseline is configured

**Flow:**
1. Agent invokes a permission-related API (e.g., `grantRole`, `assumeRole`, `addScope`)
2. Log Ingestion captures the permission request with requested scope details
3. Anomaly Detection Rules engine matches against AGT-PER-003 signatures
4. Rule engine compares requested permissions against agent's authorized scope
5. If escalation detected, incident classified as AGT-PER-003 with HIGH severity
6. PBP-003 playbook executes — permission request is DENIED
7. Agent is rate-limited for subsequent permission requests
8. Security Analyst receives alert with requested vs. authorized permission diff

**Postconditions:**
- Escalation attempt is blocked
- Agent permission state remains unchanged
- Audit trail captures the full escalation attempt

**Acceptance Criteria:**
- AC1: System detects permission escalation API calls within 300ms
- AC2: System correctly identifies scope expansion beyond authorized baseline
- AC3: System blocks escalation attempts before permission change is applied
- AC4: System generates diff showing requested vs. authorized permissions
- AC5: Demo scenario for Meta permission exposure correctly identifies and blocks escalation

---

### UC-004: Detect Harmful Output

| Attribute | Value |
|-----------|-------|
| **ID** | UC-004 |
| **Name** | Detect Harmful Output |
| **Priority** | P0 |
| **Actor** | Content Moderator, Compliance Officer |
| **Demo Scenario** | UnitedHealth — Automated denial of care recommendations |

**Description:**
The system detects when an AI agent generates outputs that are harmful, discriminatory, dangerous, or violate organizational safety and fairness policies. This includes healthcare denial recommendations, biased decisions, dangerous instructions, or policy-violating content.

**Preconditions:**
- Log ingestion pipeline is active (FEAT-001)
- Harmful output detection rules are enabled (FEAT-002)
- Content safety policy is configured
- Gemini Enhancement Overlay is available for semantic analysis (FEAT-004)

**Flow:**
1. Agent generates output directed to a user or downstream system
2. Output is routed through Lobster Trap for inspection
3. Log Ingestion captures the output content and routing context
4. Anomaly Detection Rules engine applies pattern matching for harmful content indicators
5. Gemini Enhancement Overlay performs semantic analysis on the output
6. Combined score from rule engine + Gemini analysis determines severity
7. If harmful content detected, incident classified as AGT-HRM-004
8. PBP-004 playbook executes — output is quarantined, not delivered
9. Human review workflow is initiated
10. Content Moderator receives alert with quarantined output and analysis

**Postconditions:**
- Harmful output is quarantined and not delivered to intended recipient
- Human review workflow is active
- Full context is preserved for investigation

**Acceptance Criteria:**
- AC1: System evaluates agent outputs in real-time before delivery
- AC2: System detects harmful content with both pattern matching and semantic analysis
- AC3: System quarantines harmful outputs before they reach recipients
- AC4: System initiates human review workflow within 2 seconds
- AC5: Demo scenario for UnitedHealth denial event correctly identifies and quarantines harmful recommendation

---

### UC-005: Detect Data Exfiltration

| Attribute | Value |
|-----------|-------|
| **ID** | UC-005 |
| **Name** | Detect Data Exfiltration |
| **Priority** | P0 |
| **Actor** | Security Analyst, Data Protection Officer |
| **Demo Scenario** | Replit — Unauthorized record access and potential exfiltration |

**Description:**
The system detects when an AI agent transfers data to unauthorized external destinations, accesses data beyond its scope, or moves data in volumes exceeding established policy thresholds. This includes large data exports, external API calls with data payloads, and access to sensitive data stores.

**Preconditions:**
- Log ingestion pipeline is active (FEAT-001)
- Data exfiltration detection rules are enabled (FEAT-002)
- Data classification and access policies are configured
- Baseline for normal data access patterns is established

**Flow:**
1. Agent initiates data access or transfer operation
2. Log Ingestion captures the operation with data volume, destination, and classification
3. Anomaly Detection Rules engine evaluates against AGT-EXT-005 signatures:
   - Volume exceeds baseline threshold
   - Destination is not in authorized allowlist
   - Data classification level exceeds agent's clearance
   - Transfer occurs outside normal operational hours
4. Risk score is computed from multiple factors
5. If score exceeds threshold, incident classified as AGT-EXT-005
6. PBP-005 playbook executes — data transfer is BLOCKED
7. Evidence package captures data samples (hashed), destination, and full context
8. Data Protection Officer receives immediate alert

**Postconditions:**
- Unauthorized data transfer is blocked
- Incident record contains full data transfer context
- Evidence package is available for breach assessment

**Acceptance Criteria:**
- AC1: System monitors all data transfers from agent in real-time
- AC2: System evaluates transfers against volume, destination, classification, and timing policies
- AC3: System blocks unauthorized transfers before completion
- AC4: System generates evidence package with hashed data samples
- AC5: Demo scenario for Replit record deletion/access generates complete incident record

---

### UC-006: Respond to Detected Incident

| Attribute | Value |
|-----------|-------|
| **ID** | UC-006 |
| **Name** | Respond to Detected Incident |
| **Priority** | P0 |
| **Actor** | System (Automated), Security Analyst |

**Description:**
When an incident is classified, PLAYBOOK automatically executes the associated response playbook. Each playbook contains an ordered sequence of Lobster Trap actions that contain, mitigate, or remediate the incident.

**Preconditions:**
- Incident has been classified with a valid incident type
- Associated playbook is defined and enabled
- Lobster Trap DPI integration is active

**Flow:**
1. Incident classification engine outputs incident type and severity
2. Playbook Library resolves the incident type to the default playbook
3. Playbook Engine validates preconditions and checks for conflicts
4. Playbook Engine executes each action in sequence:
   - **QUARANTINE**: Isolate agent — suspend further tool call execution
   - **DENY**: Block the specific tool call or operation
   - **LOG**: Enhanced logging at maximum verbosity
   - **HUMAN_REVIEW**: Escalate to human analyst queue
   - **RATE_LIMIT**: Throttle agent's tool call rate
5. Each action result is recorded in the incident timeline
6. If any action fails, playbook continues with next action (fail-open for safety)
7. Playbook execution summary is appended to incident record

**Postconditions:**
- All applicable playbook actions have been executed
- Incident timeline contains full response audit trail
- Human escalation has occurred if playbook included HUMAN_REVIEW

**Acceptance Criteria:**
- AC1: System executes playbook actions within 500ms of classification
- AC2: System records each action result (success/failure) in timeline
- AC3: System continues execution on individual action failure
- AC4: System escalates to human review for CRITICAL and HIGH severity incidents
- AC5: System provides playbook execution summary in incident record

---

### UC-007: Generate Forensic Evidence Package

| Attribute | Value |
|-----------|-------|
| **ID** | UC-007 |
| **Name** | Generate Forensic Evidence Package |
| **Priority** | P0 |
| **Actor** | Security Analyst, Compliance Officer, Legal Counsel |

**Description:**
For any incident, PLAYBOOK generates a comprehensive, tamper-evident evidence package containing all artifacts necessary for investigation, audit, and regulatory reporting. The package is immutable once sealed.

**Preconditions:**
- Incident has been detected and classified
- Relevant logs have been captured
- Forensic timeline has been initialized

**Flow:**
1. Incident reaches terminal state (resolved, contained, or escalated)
2. Forensic Timeline Engine reconstructs the complete event sequence
3. Evidence Package Generator collects all artifacts:
   - Original tool call logs with full payloads
   - Agent context and conversation history
   - Classification decision and rationale
   - Playbook execution log
   - System state snapshots before/during/after
   - Compliance mapping annotations
4. All artifacts are hashed and cryptographically signed
5. Package is assembled in structured format (JSON + attachments)
6. Package is stored in immutable evidence store
7. Package hash is recorded on integrity ledger
8. Analyst receives notification that package is ready
9. Package can be exported as PDF, JSON, or STIX 2.1

**Postconditions:**
- Complete evidence package exists in immutable store
- Package integrity is cryptographically verifiable
- Package is available for export and regulatory submission

**Acceptance Criteria:**
- AC1: System generates complete evidence package within 30 seconds of incident terminal state
- AC2: Package contains all required artifact categories
- AC3: Package is cryptographically signed and tamper-evident
- AC4: Package integrity can be independently verified
- AC5: Package can be exported in PDF, JSON, and STIX 2.1 formats

---

### UC-008: View Agent Health Dashboard

| Attribute | Value |
|-----------|-------|
| **ID** | UC-008 |
| **Name** | View Agent Health Dashboard |
| **Priority** | P1 |
| **Actor** | Operations Manager, System Operator |

**Description:**
Users can view a comprehensive dashboard showing the real-time health and security posture of all monitored AI agents. The dashboard provides at-a-glance visibility into incident counts, agent status, and system-wide risk indicators.

**Preconditions:**
- Dashboard module is deployed (FEAT-009, FEAT-010)
- Agent data is available from TerraFabric or configured sources
- User has appropriate access permissions

**Flow:**
1. User navigates to the PLAYBOOK dashboard
2. System loads real-time agent health data
3. Dashboard displays:
   - Total agents monitored, active, quarantined
   - Incident count by severity (last 24h, 7d, 30d)
   - Agent health score (composite metric)
   - Recent incident feed
   - System-wide risk level indicator
4. User can filter by agent, time range, incident type, severity
5. User can drill into any agent for detailed health view
6. User can drill into any incident for full detail

**Postconditions:**
- User has current view of agent security posture
- User can navigate to detailed views

**Acceptance Criteria:**
- AC1: Dashboard loads within 3 seconds
- AC2: All metrics update in real-time (sub-second latency)
- AC3: Filters apply within 1 second
- AC4: Drill-down navigation works for all clickable elements
- AC5: Dashboard is responsive on desktop, tablet, and mobile viewports

---

### UC-009: Review Compliance Mapping

| Attribute | Value |
|-----------|-------|
| **ID** | UC-009 |
| **Name** | Review Compliance Mapping |
| **Priority** | P1 |
| **Actor** | Compliance Officer, Legal Counsel, Auditor |

**Description:**
Users can review how each incident type, detection rule, and response playbook maps to specific regulatory requirements. The compliance mapping provides traceability between PLAYBOOK controls and frameworks such as EU AI Act, HIPAA, and NIST AI RMF.

**Preconditions:**
- Compliance Mapping module is deployed (FEAT-011)
- Regulatory framework definitions are loaded
- User has appropriate access permissions

**Flow:**
1. User navigates to Compliance Mapping view
2. System displays framework selector (EU AI Act, HIPAA, NIST AI RMF)
3. User selects a framework
4. System displays mapping matrix:
   - Framework requirement (e.g., EU AI Act Art. 9)
   - PLAYBOOK control (detection rule, playbook, procedure)
   - Coverage status (Full, Partial, Planned)
   - Evidence reference
5. User can filter by coverage status or requirement
6. User can view detailed mapping for any cell
7. User can export compliance report

**Postconditions:**
- User has visibility into regulatory coverage
- Compliance gaps are identified and documented

**Acceptance Criteria:**
- AC1: System displays complete mapping matrix for selected framework
- AC2: Coverage status is accurately represented for all controls
- AC3: User can navigate to detailed control documentation
- AC4: System generates exportable compliance report
- AC5: Report identifies gaps with recommended remediation

---

### UC-010: Run Red-Team Test

| Attribute | Value |
|-----------|-------|
| **ID** | UC-010 |
| **Name** | Run Red-Team Test |
| **Priority** | P1 |
| **Actor** | Security Engineer, Red Team Operator |

**Description:**
Users can execute pre-built or custom adversarial tests against PLAYBOOK's detection and response capabilities. Red-team tests validate that the system correctly identifies and responds to attack patterns.

**Preconditions:**
- Red-Team Test Suite is deployed (FEAT-014)
- User has red-team operator role
- Test environment is isolated from production

**Flow:**
1. User navigates to Red-Team Test interface
2. System displays available test scenarios organized by incident type
3. User selects one or more test scenarios
4. User configures test parameters (target agent, intensity, duration)
5. User initiates test execution
6. System executes test scenarios against target agent in isolated environment
7. System monitors PLAYBOOK detection and response in real-time
8. Test results are compiled:
   - Detection rate (% of attacks detected)
   - Response accuracy (% correct classification)
   - MTTD and MTTR measurements
   - Coverage gaps identified
9. Results are displayed with recommendations
10. Results are stored for trend analysis

**Postconditions:**
- Test results are available with metrics
- Coverage gaps are documented
- Historical test results enable trend tracking

**Acceptance Criteria:**
- AC1: System executes selected test scenarios in isolated environment
- AC2: System measures detection rate, response accuracy, MTTD, MTTR
- AC3: System identifies coverage gaps from undetected attacks
- AC4: Results include actionable recommendations
- AC5: Historical test results are available for trend comparison

---

### UC-011: Judge Layer Interception

| Attribute | Value |
|-----------|-------|
| **ID** | UC-011 |
| **Name** | Judge Layer Interception |
| **Priority** | P0 |
| **Actor** | Security Engineer, Compliance Officer, System Operator |
| **Demo Scenario** | LLM-Judge Bypass Attempt — Scenario 4 (DEMO-006) |

**Description:**
Every agent action is intercepted by the Judge Layer (FEAT-019) before execution. The Judge applies deterministic classification (FEAT-017) to render one of four decisions: ALLOW, DENY, QUARANTINE, or ESCALATE. The decision rationale is logged for audit. The Judge Layer ensures that enforcement never depends on an LLM and is immune to known bypass patterns. This use case covers the complete flow from action interception through decision rendering to enforcement.

**Preconditions:**
- Judge Layer is deployed and active (FEAT-019)
- Deterministic classification engine is loaded with rules (FEAT-017)
- Lobster Trap DPI integration is active
- Agent traffic is flowing through the interception pipeline

**Flow:**
1. Agent plans an action (tool call, API request, data operation)
2. The action is intercepted by the Judge Layer before it reaches any external system
3. Judge Layer extracts action metadata: tool name, parameters, destination, data volume, agent context
4. Deterministic classifier (FEAT-017) evaluates the action against local rule base:
   - Pattern matching against known malicious signatures
   - Behavioral baseline comparison
   - Policy rule evaluation (allowlists, denylists, thresholds)
   - Bypass pattern detection (FEAT-018) for adversarial inputs
5. Classifier produces a deterministic decision: ALLOW, DENY, QUARANTINE, or ESCALATE
6. Decision rationale is logged with full context (action metadata, matched rules, confidence score)
7. Judge Layer applies the decision:
   - **ALLOW**: Action is forwarded to the target system
   - **DENY**: Action is blocked; agent receives policy denial
   - **QUARANTINE**: Action is blocked; agent is suspended
   - **ESCALATE**: Action is held pending human review
8. Decision event is emitted to the forensics pipeline for timeline and evidence
9. Dashboard is updated to show the decision in real-time
10. If SupraWall guardrail is also present (FEAT-020), its decision is correlated and included in the evidence package

**Postconditions:**
- Agent action has been intercepted and evaluated
- A deterministic decision has been rendered and enforced
- Decision rationale is logged in the audit trail
- Forensic timeline contains the complete interception record
- If action was DENIED or QUARANTINED, incident record is created

**Acceptance Criteria:**
- AC1: 100% of agent actions are intercepted by the Judge Layer before execution
- AC2: Classification decision is rendered within 50ms of interception
- AC3: Decision is deterministic — the same action under the same conditions always produces the same decision
- AC4: Decision rationale is logged with full metadata and matched rules for audit
- AC5: All four decision types (ALLOW, DENY, QUARANTINE, ESCALATE) are supported and correctly enforced
- AC6: If SupraWall is present, its decisions are ingested and correlated with Judge Layer decisions

---

### UC-012: Bypass Pattern Detection

| Attribute | Value |
|-----------|-------|
| **ID** | UC-012 |
| **Name** | Bypass Pattern Detection |
| **Priority** | P1 |
| **Actor** | SOC Analyst, Security Engineer, Red Team Operator |
| **Demo Scenario** | LLM-Judge Bypass Attempt — Scenario 4 (DEMO-006) |

**Description:**
The system detects when attackers attempt to bypass LLM-based guardrails using known adversarial patterns. Four specific bypass patterns are monitored: context window stuffing (displacing safety instructions with injected context), homoglyph injection (using visually similar Unicode characters to evade string matching), confidence hijacking (manipulating confidence scores to force incorrect classifications), and tool chaining (splitting a malicious action across multiple seemingly benign tool calls). Each bypass attempt is detected, logged, reported in the incident dashboard, and generates a CRITICAL incident.

**Preconditions:**
- Bypass detection module is enabled (FEAT-018)
- Deterministic classifier is active (FEAT-017) — immune to LLM-specific bypasses
- Incident dashboard is deployed (FEAT-009)
- Red-team test suite is available for validation (FEAT-014)

**Flow:**
1. Attacker submits an agent prompt or action containing a bypass pattern
2. Judge Layer intercepts the action (FEAT-019)
3. Deterministic classifier evaluates the action — because it uses local rules (not an LLM), it is not vulnerable to the bypass attempt
4. Bypass Detection module (FEAT-018) analyzes the action for known bypass indicators:
   - **Context Window Stuffing**: Detects abnormally large context, repeated adversarial phrases, or patterns designed to displace system instructions
   - **Homoglyph Injection**: Detects Unicode homoglyphs (e.g., Cyrillic 'a' replacing Latin 'a') in tool names, parameters, or commands
   - **Confidence Hijacking**: Detects attempts to inject false confidence markers, repeated assertions, or adversarial formatting
   - **Tool Chaining**: Detects sequences of individually benign tool calls that combine into a malicious action across the chain
5. If a bypass pattern is detected:
   a. The action is classified as AGT-BYP-014 (Guardrail Bypass) with CRITICAL severity
   b. An incident is created with the bypass pattern type documented
   c. The bypass attempt is logged with full context (raw payload, detected pattern, mitigated action)
   d. Playbook PBP-014 executes: action DENIED, agent QUARANTINED, human review escalated
   e. Bypass attempt is reported in the incident dashboard with pattern type highlighted
   f. Forensic timeline captures the complete bypass attempt and mitigation
6. SOC Analyst receives alert with bypass pattern type, raw payload, and mitigation details
7. Bypass detection metrics are updated (total attempts, pattern type distribution, success rate of detection)

**Postconditions:**
- Bypass attempt has been detected and mitigated
- Incident record contains full bypass documentation
- Forensic evidence package includes raw payload and detection rationale
- Dashboard shows bypass detection metrics

**Acceptance Criteria:**
- AC1: All four bypass patterns (context displacement, homoglyph injection, confidence hijacking, tool chaining) are detected
- AC2: Each bypass detection generates an AGT-BYP-014 incident with CRITICAL severity
- AC3: Bypass attempts are reported in the incident dashboard within 2 seconds of detection
- AC4: Full raw payload of the bypass attempt is preserved in the evidence package
- AC5: Red-team tests validate 100% detection rate for all four bypass patterns
- AC6: The deterministic classifier (FEAT-017) is never bypassed by any of the four patterns — 100% catch rate

---

### UC-013: Customize Organization Policy

| Attribute | Value |
|-----------|-------|
| **ID** | UC-013 |
| **Name** | Customize Organization Policy |
| **Priority** | P0 |
| **Actor** | CISO, Security Engineer, Compliance Officer |
| **Demo Scenario** | Organization Policy Switching — Scenario 4 (DEMO-004) |

**Description:**
An organization customizes their incident response policies by selecting NIST baseline templates and modifying Organization-Defined Parameters (ODPs) through the Visual Policy Builder. The system validates all changes against NIST baselines using conflict detection, versions every change for audit, and applies the customized policy to all incident classification and response decisions.

**Preconditions:**
- NIST Baseline Templates are loaded (FEAT-021)
- Visual Policy Builder is deployed (FEAT-023)
- User has policy administrator role
- Organization account is provisioned

**Flow:**
1. User navigates to the Policy Builder
2. System displays the 12 NIST incident type baselines with ODP placeholders (FEAT-021)
3. User selects an incident type to customize
4. System displays side-by-side view: NIST baseline (read-only) + ODP editor (FEAT-023)
5. User modifies ODP values:
   - Adjusts severity threshold via dropdown
   - Toggles auto-contain on/off
   - Enters escalation contacts as a comma-separated list
   - Sets response time SLA as a numeric value
   - Selects forensic level via dropdown
   - Enters notification targets as a list
   - Toggles compliance report generation
   - Sets record threshold as a numeric value
6. Conflict Detection engine evaluates each change against the NIST baseline (FEAT-025)
7. If conflicts are detected:
   - System displays inline warnings with severity (WARNING or BLOCKED)
   - System provides conflict resolution suggestions
   - User resolves conflicts or acknowledges warnings
8. User clicks Save — system creates a new policy version (FEAT-026)
9. Version is stored with full audit trail: who changed what, when, from what, to what
10. Customized policy is activated and applied to all future incident classifications
11. User can click Preview to see how the policy would affect past incidents
12. User can click Test to run a simulated incident through the customized policy

**Postconditions:**
- Organization policy is customized and active
- All changes are versioned and auditable
- No compliance gaps exist between ODPs and NIST baselines (all conflicts resolved or acknowledged)
- Policy is available for incident classification and response

**Acceptance Criteria:**
- AC1: System displays all 12 NIST baselines with ODP placeholders
- AC2: Visual Policy Builder provides side-by-side baseline + editor view
- AC3: All 8 ODPs per incident type are editable with appropriate input controls
- AC4: Conflict detection identifies severity downgrades, auto-contain disables, missing escalation contacts, and SLA exceedances
- AC5: Each policy save creates a new version with full audit trail
- AC6: Customized policy is applied to all future incident classifications within 30 seconds of activation
- AC7: Preview mode shows how the policy would affect historical incidents
- AC8: Test mode runs a simulated incident through the customized policy without affecting production

---

### UC-014: Apply Industry Template

| Attribute | Value |
|-----------|-------|
| **ID** | UC-014 |
| **Name** | Apply Industry Template |
| **Priority** | P1 |
| **Actor** | CISO, Compliance Officer, CTO |
| **Demo Scenario** | Organization Policy Switching — Scenario 4 (DEMO-004) |

**Description:**
An organization applies a pre-configured industry template (HIPAA, SOC2, PCI-DSS, GDPR, Financial Services, or SaaS Startup) with one click. The template sets all 8 ODPs for all 12 incident types based on industry best practices. The system creates a new policy version, validates the template configuration against NIST baselines, and activates the template across the organization.

**Preconditions:**
- Industry Templates are loaded (FEAT-024)
- NIST Baseline Templates are available (FEAT-021)
- User has policy administrator role
- Visual Policy Builder is deployed (FEAT-023)

**Flow:**
1. User navigates to the Policy Builder
2. System displays available industry templates: HIPAA, SOC2, PCI-DSS, GDPR, Financial Services, SaaS Startup (FEAT-024)
3. User selects a template (e.g., HIPAA)
4. System displays template summary:
   - Template name and description
   - ODP changes per incident type (summary view)
   - NIST baseline compatibility score
   - Estimated compliance coverage
5. User clicks Apply Template
6. Conflict Detection engine validates all template ODPs against NIST baselines (FEAT-025)
7. System displays any conflicts with resolution options
8. User confirms application
9. System creates a new policy version with template applied (FEAT-026)
10. Audit trail records: user, timestamp, template name, previous version, new version
11. Template ODPs are activated across all 12 incident types
12. Dashboard shows template activation confirmation with compliance coverage metrics

**Postconditions:**
- Industry template is applied and active
- All 12 incident types have ODPs configured per the template
- A new policy version exists with full audit trail
- Compliance coverage is updated to reflect industry-specific requirements

**Acceptance Criteria:**
- AC1: System displays all 6 industry templates with descriptions
- AC2: Template application sets all 8 ODPs for all 12 incident types
- AC3: Template application completes within 10 seconds
- AC4: Each template application creates a new policy version
- AC5: Conflict detection runs automatically and displays any NIST baseline conflicts
- AC6: Audit trail captures: who applied which template, when, and version numbers
- AC7: Template can be rolled back to previous version within 30 seconds
- AC8: Compliance coverage metrics update to reflect the applied template

---

## 3. Feature Requirements

### FEAT-001: Log Ingestion (Detect)

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-001 |
| **Name** | Log Ingestion |
| **Priority** | P0 |
| **Stage** | DETECT |

**Description:**
The Log Ingestion module receives, normalizes, and routes log events from AI agent systems in real-time. It supports multiple ingestion protocols and formats, ensuring all agent activity — tool calls, outputs, errors, and state changes — is captured for analysis.

**User Stories:**

| ID | Story |
|----|-------|
| US-001 | As a Security Analyst, I want all agent tool calls to be logged in real-time so that no activity escapes monitoring |
| US-002 | As an Operator, I want logs normalized to a common schema so that analysis is consistent across different agent frameworks |
| US-003 | As a Security Engineer, I want configurable ingestion filters so that I can control data volume and focus on relevant events |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-001 | Given a tool call event, when it is generated by an agent, then it is ingested and available for analysis within 100ms |
| AC-002 | Given logs from different sources (TerraFabric, Lobster Trap, custom agents), when ingested, then they are normalized to the PLAYBOOK Common Event Schema (PB-CES) |
| AC-003 | Given ingestion filters are configured, when an event matches filter criteria, then it is either included or excluded per filter configuration |
| AC-004 | Given a burst of events (up to 10,000 EPS), when they arrive within a 1-second window, then all events are ingested without loss |
| AC-005 | Given an ingestion failure, when the failure occurs, then the system retries with exponential backoff and alerts operators after 3 failures |

**Data Schema (PB-CES):**

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "source": {
    "agent_id": "string",
    "agent_name": "string",
    "framework": "string",
    "version": "string"
  },
  "event_type": "TOOL_CALL | OUTPUT | ERROR | STATE_CHANGE | SECURITY | JUDGE_DECISION",
  "tool_call": {
    "tool_name": "string",
    "parameters": {},
    "destination": "string",
    "data_volume_bytes": 0
  },
  "output": {
    "recipient": "string",
    "content_type": "string",
    "classification": "string"
  },
  "judge_decision": {
    "decision": "ALLOW | DENY | QUARANTINE | ESCALATE",
    "rationale": "string",
    "matched_rules": [],
    "confidence": 0.0,
    "latency_ms": 0
  },
  "context": {
    "session_id": "string",
    "conversation_id": "string",
    "user_id": "string",
    "permissions": []
  },
  "metadata": {
    "ingestion_timestamp": "ISO8601",
    "source_ip": "string",
    "pipeline_version": "string"
  }
}
```

**Dependencies:** Lobster Trap DPI (EXT-001)

---

### FEAT-002: Anomaly Detection Rules

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-002 |
| **Name** | Anomaly Detection Rules |
| **Priority** | P0 |
| **Stage** | DETECT |

**Description:**
The Anomaly Detection Rules engine evaluates ingested events against a library of detection rules. Each rule defines patterns, thresholds, and conditions that identify suspicious or malicious agent activity. Rules are organized by the 16 incident types and support both static signatures and dynamic behavioral baselines.

**User Stories:**

| ID | Story |
|----|-------|
| US-004 | As a Security Analyst, I want pre-built detection rules for common AI agent attack patterns so that I have immediate coverage |
| US-005 | As a Security Engineer, I want to create custom rules with flexible conditions so that I can address organization-specific threats |
| US-006 | As an Analyst, I want rule severity and thresholds to be configurable so that I can tune false positive rates |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-006 | Given an ingested event, when it matches an enabled detection rule, then a detection alert is generated within 200ms |
| AC-007 | Given a detection rule with threshold conditions, when multiple conditions must be met, then the alert only fires when all conditions are satisfied |
| AC-008 | Given a behavioral baseline for an agent, when current activity deviates by > 3 standard deviations, then an anomaly alert is generated |
| AC-009 | Given a rule is disabled, when an event matches that rule, then no alert is generated |
| AC-010 | Given rule configuration is updated, when changes are saved, then they take effect within 30 seconds without pipeline restart |

**Rule Configuration Format:**

```json
{
  "rule_id": "RULE-DEL-001",
  "name": "Database Destruction Pattern",
  "incident_type": "AGT-DEL-001",
  "severity": "CRITICAL",
  "enabled": true,
  "conditions": {
    "pattern_match": {
      "tool_name": "*sql*",
      "parameters": {
        "query": "(?i)(DROP TABLE|DELETE\\s+FROM|TRUNCATE)"
      }
    },
    "threshold": {
      "rows_affected": "> 100"
    }
  },
  "baseline_required": true,
  "response_playbook": "PBP-001-Data-Destruction-Block"
}
```

**Dependencies:** FEAT-001 (Log Ingestion)

---

### FEAT-003: Incident Classification

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-003 |
| **Name** | Incident Classification (Local) |
| **Priority** | P0 |
| **Stage** | CLASSIFY |

**Description:**
The local Incident Classification engine processes detection alerts and assigns a standardized incident type, severity, and confidence score. Classification operates entirely on-premises without external API dependencies, ensuring sub-second response times and data privacy.

**User Stories:**

| ID | Story |
|----|-------|
| US-007 | As a Security Analyst, I want incidents automatically classified by type so that response is consistent and fast |
| US-008 | As an Analyst, I want severity to reflect actual business impact so that I can prioritize effectively |
| US-009 | As a Compliance Officer, I want classification to include regulatory mapping so that reporting obligations are clear |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-011 | Given a detection alert, when classification runs, then it outputs an incident type from the 16-type taxonomy within 150ms |
| AC-012 | Given multiple detection alerts for the same event, when classification runs, then it selects the highest-severity matching type |
| AC-013 | Given classification confidence is below 70%, when the incident is created, then it includes a "low confidence" flag for human review |
| AC-014 | Given an incident type is classified, when the classification completes, then the appropriate regulatory mappings are attached automatically |
| AC-015 | Given classification results, when they are stored, then they are immutable and versioned |

**Classification Output Schema:**

```json
{
  "classification_id": "uuid",
  "incident_type": "AGT-DEL-001",
  "incident_name": "Data Destruction",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW",
  "confidence": 0.95,
  "confidence_flag": "HIGH | LOW",
  "rule_matches": ["RULE-DEL-001", "RULE-DEL-003"],
  "regulatory_mapping": [
    {"framework": "EU_AI_ACT", "article": "Art. 15"},
    {"framework": "NIST_RMF", "control": "GV.RR-04"}
  ],
  "classification_timestamp": "ISO8601",
  "classifier_version": "1.2.0"
}
```

**Dependencies:** FEAT-001, FEAT-002

---

### FEAT-004: Gemini Enhancement Overlay

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-004 |
| **Name** | Gemini Enhancement Overlay |
| **Priority** | P0 |
| **Stage** | CLASSIFY |

**Description:**
The Gemini Enhancement Overlay provides optional LLM-powered analysis to augment local classification. It sends anonymized event context to the Gemini Pro API for semantic analysis, intent classification, and complex pattern detection that exceeds the capability of rule-based systems.

**User Stories:**

| ID | Story |
|----|-------|
| US-010 | As a Security Analyst, I want LLM-powered semantic analysis for complex incidents so that subtle attack patterns are detected |
| US-011 | As a Privacy Officer, I want sensitive data to be redacted before LLM transmission so that no PII leaves the system |
| US-012 | As an Operator, I want Gemini enhancement to be optional per-incident-type so that I control API usage and latency |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-016 | Given Gemini enhancement is enabled for an incident type, when classification occurs, then anonymized context is sent to Gemini Pro API |
| AC-017 | Given sensitive data is present in event context, when data is sent to Gemini, then all PII/PHI is redacted using configured patterns |
| AC-018 | Given Gemini returns analysis, when it is received, then it is combined with local classification using weighted scoring |
| AC-019 | Given Gemini API is unavailable, when enhancement is requested, then the system falls back to local classification without error |
| AC-020 | Given Gemini enhancement is disabled for an incident type, when that incident is classified, then only local classification is used |

**Gemini Prompt Template:**

```
You are an AI security analyst. Analyze the following agent activity for security threats.

Incident Type Context: {incident_type_description}
Tool Call: {tool_name}
Parameters: {redacted_parameters}
Agent Context: {redacted_context}
Historical Pattern: {baseline_deviation}

Provide:
1. Threat assessment (YES/NO/UNCERTAIN)
2. Confidence score (0-1)
3. Rationale (max 200 words)
4. Recommended severity adjustment
```

**Dependencies:** FEAT-003, Gemini Pro API (EXT-002)

---

### FEAT-005: Playbook Library

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-005 |
| **Name** | Playbook Library |
| **Priority** | P0 |
| **Stage** | RESPOND |

**Description:**
The Playbook Library is a centralized repository of response playbooks. Each playbook defines an ordered sequence of actions to execute when an incident of a specific type is classified. Playbooks are versioned, auditable, and customizable.

**User Stories:**

| ID | Story |
|----|-------|
| US-013 | As a Security Engineer, I want pre-built playbooks for each incident type so that I have immediate response capability |
| US-014 | As an Engineer, I want to customize playbook actions and ordering so that responses match our operational procedures |
| US-015 | As an Auditor, I want playbook version history so that I can demonstrate procedural consistency |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-021 | Given an incident type, when it is classified, then the system resolves it to the active playbook within 50ms |
| AC-022 | Given a playbook has multiple actions, when it executes, then actions run in the defined order with recorded outcomes |
| AC-023 | Given a playbook action fails, when failure occurs, then execution continues to the next action and the failure is logged |
| AC-024 | Given a playbook is updated, when a new version is saved, then the old version is retained for audit and rollback |
| AC-025 | Given playbook execution, when complete, then a summary with all action results is stored in the incident record |

**Default Playbook: PBP-001-Data-Destruction-Block**

```json
{
  "playbook_id": "PBP-001-Data-Destruction-Block",
  "version": "1.0.0",
  "incident_types": ["AGT-DEL-001"],
  "description": "Block destructive data operations and isolate agent",
  "actions": [
    {"order": 1, "action": "DENY", "target": "current_tool_call", "on_failure": "continue"},
    {"order": 2, "action": "QUARANTINE", "target": "agent", "duration": "until_review", "on_failure": "continue"},
    {"order": 3, "action": "LOG", "target": "agent", "level": "MAXIMUM", "on_failure": "continue"},
    {"order": 4, "action": "HUMAN_REVIEW", "target": "security_team", "priority": "P0", "on_failure": "continue"}
  ],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Dependencies:** FEAT-003

---

### FEAT-006: Automated Response Execution

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-006 |
| **Name** | Automated Response Execution |
| **Priority** | P0 |
| **Stage** | RESPOND |

**Description:**
The Automated Response Execution engine carries out playbook actions by interfacing with the Lobster Trap DPI infrastructure. It translates playbook actions into concrete API calls that contain, block, or remediate threats in real-time.

**User Stories:**

| ID | Story |
|----|-------|
| US-016 | As a Security Analyst, I want threats contained automatically so that damage is minimized before I can respond |
| US-017 | As an Operator, I want response actions to complete in sub-second time so that agent operations are not significantly delayed |
| US-018 | As an Engineer, I want response actions to be logged and auditable so that I can review what was done |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-026 | Given a playbook action of type DENY, when executed, then the current tool call is blocked before reaching its destination |
| AC-027 | Given a playbook action of type QUARANTINE, when executed, then the agent's tool call privileges are suspended |
| AC-028 | Given a playbook action of type RATE_LIMIT, when executed, then the agent's tool call rate is reduced to the configured limit |
| AC-029 | Given a playbook action of type HUMAN_REVIEW, when executed, then the incident is added to the human review queue with configured priority |
| AC-030 | Given any response action, when executed, then the result is recorded in the incident timeline within 100ms |

**Lobster Trap Action Mapping:**

| Playbook Action | Lobster Trap API Call | Expected Latency |
|-----------------|----------------------|------------------|
| DENY | `POST /v1/actions/deny` | < 50ms |
| QUARANTINE | `POST /v1/actions/quarantine` | < 100ms |
| RATE_LIMIT | `POST /v1/actions/rate_limit` | < 50ms |
| LOG | `POST /v1/actions/verbosity` | < 50ms |
| HUMAN_REVIEW | `POST /v1/escalations` | < 200ms |

**Dependencies:** FEAT-005, Lobster Trap DPI (EXT-001)

---

### FEAT-007: Forensic Timeline

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-007 |
| **Name** | Forensic Timeline |
| **Priority** | P0 |
| **Stage** | FORENSICS |

**Description:**
The Forensic Timeline engine reconstructs a complete, chronologically ordered sequence of all events related to an incident. The timeline begins at the first precursor event and continues through detection, classification, response, and resolution.

**User Stories:**

| ID | Story |
|----|-------|
| US-019 | As a Security Analyst, I want a complete timeline of events so that I can understand the full incident chain |
| US-020 | As an Investigator, I want timeline events to be correlated across systems so that I see the complete picture |
| US-021 | As an Auditor, I want the timeline to be immutable so that I can trust it as evidence |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-031 | Given an incident, when the timeline is generated, then it includes all events from 5 minutes before the trigger event through resolution |
| AC-032 | Given timeline events, when displayed, then they are ordered chronologically with precise timestamps (millisecond) |
| AC-033 | Given related events from multiple sources, when they are correlated, then they are linked with correlation IDs |
| AC-034 | Given the timeline, when it is sealed, then it becomes immutable and cryptographically signed |
| AC-035 | Given a timeline event, when a user clicks it, then they can see full event details and raw log reference |

**Timeline Event Schema:**

```json
{
  "timeline_id": "uuid",
  "incident_id": "uuid",
  "events": [
    {
      "event_id": "uuid",
      "timestamp": "ISO8601",
      "sequence": 1,
      "source": "AGENT | DETECTION | CLASSIFICATION | RESPONSE | SYSTEM | JUDGE | POLICY",
      "event_type": "TOOL_CALL | DETECTION_ALERT | CLASSIFICATION | PLAYBOOK_ACTION | STATE_CHANGE | JUDGE_DECISION | ODP_CHANGE",
      "description": "Agent invoked delete_users_table tool",
      "actor": "agent_id_123",
      "action": "delete_users_table",
      "result": "BLOCKED",
      "correlation_ids": ["session_abc", "conv_xyz"],
      "raw_log_ref": "logs/2025-01-15/delete_event.json"
    }
  ]
}
```

**Dependencies:** FEAT-001, FEAT-006

---

### FEAT-008: Evidence Package Generation

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-008 |
| **Name** | Evidence Package Generation |
| **Priority** | P0 |
| **Stage** | FORENSICS |

**Description:**
The Evidence Package Generator assembles all artifacts related to an incident into a structured, tamper-evident package suitable for investigation, audit, and regulatory submission.

**User Stories:**

| ID | Story |
|----|-------|
| US-022 | As a Security Analyst, I want all incident evidence in one package so that investigation is efficient |
| US-023 | As a Compliance Officer, I want evidence packages in regulator-ready formats so that I can submit them directly |
| US-024 | As Legal Counsel, I want evidence integrity to be cryptographically verifiable so that it is admissible |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-036 | Given an incident reaches terminal state, when the evidence package is generated, then it includes all 5 artifact categories (logs, context, classification, response, compliance) |
| AC-037 | Given an evidence package, when it is sealed, then it is signed with SHA-256 and includes a manifest with hashes for all files |
| AC-038 | Given a sealed package, when integrity is verified, then the verification confirms or rejects tampering |
| AC-039 | Given an evidence package, when exported as PDF, then it includes all artifacts in human-readable format |
| AC-040 | Given an evidence package, when exported as STIX 2.1, then it conforms to the STIX 2.1 specification |

**Evidence Package Structure:**

```
EVIDENCE-{incident_id}-{timestamp}/
├── manifest.json               # Package manifest with hashes
├── signature.json              # Cryptographic signature
├── classification/
│   ├── classification_result.json
│   ├── rule_matches.json
│   └── gemini_analysis.json (if applicable)
├── timeline/
│   ├── forensic_timeline.json
│   └── timeline_visualization.html
├── logs/
│   ├── raw_logs/               # Full raw log files
│   └── normalized_events.json
├── context/
│   ├── agent_profile.json
│   ├── session_history.json
│   └── conversation_log.json
├── response/
│   ├── playbook_execution.json
│   ├── action_results.json
│   └── system_state_snapshots.json
├── judge/
│   ├── judge_decisions.json    # Judge Layer decision log (FEAT-017)
│   ├── bypass_detections.json  # Bypass pattern detections (FEAT-018)
│   └── deterministic_classification.json # FEAT-017 classification log
├── policy/
│   ├── nist_baseline_ref.json  # NIST baseline reference (FEAT-021)
│   ├── active_odps.json        # Active ODP values at time of incident (FEAT-022)
│   └── policy_version.json     # Policy version applied (FEAT-026)
├── suprawall/
│   └── suprawall_decisions.json # SupraWall guardrail decisions (FEAT-020)
└── compliance/
    ├── regulatory_mapping.json
    ├── eu_ai_act_report.json
    └── hipaa_assessment.json (if applicable)
```

**Dependencies:** FEAT-007

---

### FEAT-009: Incident Dashboard

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-009 |
| **Name** | Incident Dashboard |
| **Priority** | P0 |
| **Stage** | FORENSICS |

**Description:**
The Incident Dashboard provides real-time visibility into all active and historical incidents. It includes an incident feed, detail sidebar, severity indicators, and filtering capabilities.

**User Stories:**

| ID | Story |
|----|-------|
| US-025 | As a Security Analyst, I want to see all active incidents in real-time so that I can respond quickly |
| US-026 | As an Analyst, I want to filter incidents by type, severity, and status so that I can focus on what matters |
| US-027 | As a Manager, I want incident metrics and trends so that I can report on security posture |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-041 | Given the dashboard loads, when it renders, then it displays all active incidents with real-time updates |
| AC-042 | Given an incident in the feed, when a user clicks it, then the detail sidebar shows full incident information |
| AC-043 | Given filter controls, when filters are applied, then the incident list updates within 1 second |
| AC-044 | Given the dashboard, when a new incident is created, then it appears in the feed within 2 seconds with a visual alert |
| AC-045 | Given the metrics panel, when it loads, then it displays incident counts by severity, type, and time period |

**Dashboard Layout:**

```
+---------------------------------------------------------------------+
|  PLAYBOOK ■■■■  [Agent Health] [Compliance] [Settings] [Policy]    |
+---------------------------------------------------------------------+
|  Metrics Bar                                                        |
|  [Active: 3] [Critical: 1] [High: 1] [Medium: 1] [Resolved: 12]    |
|  [Judge Layer: ACTIVE] [Bypass Blocked: 4] [SupraWall: Linked]      |
|  [Policy: HIPAA v3] [ODP Conflicts: 0]                              |
+------------------------------+--------------------------------------+
|  Filters                     |  Detail Sidebar                      |
|  [Type ▼] [Severity ▼] [Status ▼] [Time ▼]                         |
|                              |  +------------------------------+    |
|  Incident Feed               |  | INCIDENT AGT-DEL-001-2025... |    |
|  ---------------------       |  | Severity: CRITICAL ●        |    |
|  ● CRITICAL - AGT-DEL-001  |  | Status: CONTAINED            |    |
|  PocketOS - DROP TABLE at... |  | Agent: pocketos-prod-01      |    |
|  2 min ago                   |  | Policy: HIPAA v3             |    |
|                              |  |                              |    |
|  ○ HIGH - AGT-PER-003       |  | TIMELINE                     |    |
|  Meta - Permission escala... |  | 14:32:01 Tool call initiated |    |
|  5 min ago                   |  | 14:32:01 Judge intercepted   |    |
|                              |  | 14:32:02 Classified          |    |
|  ○ MEDIUM - AGT-HAL-007     |  | 14:32:02 Playbook executed   |    |
|  Model drift...          |  | 14:32:03 Quarantined         |    |
|  12 min ago                  |  |                              |    |
|                              |  | JUDGE DECISION               |    |
|                              |  | Decision: DENY               |    |
|                              |  | Rationale: Destructive op... |    |
|                              |  | Latency: 12ms                |    |
|                              |  |                              |    |
|                              |  | POLICY CONFIGURATION         |    |
|                              |  | NIST Baseline: AG-MG.1       |    |
|                              |  | ODP Severity: CRITICAL       |    |
|                              |  | Auto-Contain: ENABLED        |    |
|                              |  |                              |    |
|                              |  | EVIDENCE                     |    |
|                              |  | [View Full Package] [Export] |    |
|                              |  +------------------------------+    |
+------------------------------+--------------------------------------+
```

**Dependencies:** FEAT-003, FEAT-006

---

### FEAT-010: Agent Health View

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-010 |
| **Name** | Agent Health View |
| **Priority** | P1 |
| **Stage** | FORENSICS |

**Description:**
The Agent Health View provides a comprehensive security and operational health assessment for each monitored AI agent. It aggregates incident history, behavioral baselines, compliance status, and risk indicators into a unified health score.

**User Stories:**

| ID | Story |
|----|-------|
| US-028 | As an Operations Manager, I want a health score for each agent so that I can quickly identify at-risk systems |
| US-029 | As a Manager, I want historical health trends so that I can track security posture over time |
| US-030 | As an Operator, I want to compare agent health across the fleet so that I can prioritize resources |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-046 | Given an agent is monitored, when health view loads, then it displays a composite health score (0-100) |
| AC-047 | Given the health score, when it is computed, then it incorporates incident frequency, severity, compliance status, and baseline deviation |
| AC-048 | Given the health view, when it renders, then it shows a 30-day trend graph of the health score |
| AC-049 | Given the fleet comparison view, when it loads, then agents are ranked by health score with visual indicators |
| AC-050 | Given an agent's health score drops below 50, when this occurs, then an alert is generated to the operations team |

**Health Score Formula:**

```
Health Score = 100 - (
  (critical_count * 25) +
  (high_count * 10) +
  (medium_count * 5) +
  (low_count * 1) +
  (baseline_deviation * 15) +
  (compliance_gap_count * 10)
)

Min Score = 0, Max Score = 100
```

**Dependencies:** FEAT-009

---

### FEAT-011: Compliance Mapping

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-011 |
| **Name** | Compliance Mapping |
| **Priority** | P1 |
| **Stage** | FORENSICS |

**Description:**
The Compliance Mapping module provides traceability between PLAYBOOK's detection rules, response playbooks, and procedural controls to specific regulatory requirements. It supports multiple frameworks and generates gap analysis.

**User Stories:**

| ID | Story |
|----|-------|
| US-031 | As a Compliance Officer, I want to see which PLAYBOOK controls map to each regulation so that I can demonstrate compliance |
| US-032 | As an Officer, I want gap analysis so that I know where we need additional controls |
| US-033 | As an Auditor, I want exportable compliance reports so that I can provide evidence to regulators |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-051 | Given a regulatory framework is selected, when mapping view loads, then all applicable requirements are displayed with their PLAYBOOK control mappings |
| AC-052 | Given a requirement is mapped, when the mapping is viewed, then it shows the specific detection rules, playbooks, and procedures that satisfy it |
| AC-053 | Given a gap exists, when gap analysis runs, then it identifies unmapped requirements and recommends controls |
| AC-054 | Given the compliance report is exported, when it generates, then it includes mapping matrix, gap analysis, and remediation recommendations |
| AC-055 | Given a new incident, when it is classified, then its regulatory implications are automatically identified and attached |

**EU AI Act Article Mapping (Sample):**

| EU AI Act Article | Requirement | PLAYBOOK Control | Coverage |
|-------------------|-------------|------------------|----------|
| Art. 9(1) | Risk management system | FEAT-002, FEAT-003 | Full |
| Art. 9(2) | Risk identification/analysis | FEAT-002 (Baseline), FEAT-004 | Full |
| Art. 9(4) | Risk management testing | FEAT-014 (Red-Team) | Full |
| Art. 15(1) | Accuracy, robustness, cybersecurity | FEAT-002, FEAT-006 | Full |
| Art. 15(2) | Resilience against errors | FEAT-007 (Hallucination) | Full |
| Art. 15(3) | Resilience against adversarial attacks | FEAT-017, FEAT-018, FEAT-019 | Full |
| Art. 73(1) | Serious incident reporting | FEAT-012, FEAT-008 | Full |
| Art. 73(2) | Report content requirements | FEAT-012 (Export format) | Full |

**Dependencies:** FEAT-003, FEAT-008

---

### FEAT-012: EU AI Act Report Export

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-012 |
| **Name** | EU AI Act Report Export |
| **Priority** | P1 |
| **Stage** | FORENSICS |

**Description:**
The EU AI Act Report Export generates structured incident reports conforming to Article 73 reporting requirements. Reports include all mandatory fields and can be submitted directly to market surveillance authorities.

**User Stories:**

| ID | Story |
|----|-------|
| US-034 | As a Compliance Officer, I want one-click EU AI Act report generation so that I can meet reporting deadlines |
| US-035 | As an Officer, I want the report to include all Art. 73 required fields so that it is accepted by authorities |
| US-036 | As an Officer, I want the report to be generated in the official format so that no manual reformatting is needed |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-056 | Given a CRITICAL or HIGH severity incident, when the export button is clicked, then the system generates an EU AI Act Article 73 report |
| AC-057 | Given the report is generated, when it is reviewed, then it includes all mandatory fields: incident description, agent details, date/time, severity, root cause, containment actions, corrective measures |
| AC-058 | Given the report, when exported, then it is formatted as structured JSON conforming to the EU AI Act reporting schema |
| AC-059 | Given the report, when exported as PDF, then it includes a cover page with provider information and incident summary |
| AC-060 | Given a reportable incident, when the system classifies it, then the system alerts the Compliance Officer of the reporting obligation within 1 hour |

**EU AI Act Report Schema (Art. 73):**

```json
{
  "report_id": "uuid",
  "report_type": "SERIOUS_INCIDENT",
  "regulatory_reference": "EU AI Act 2024/1689 Art. 73",
  "provider": {
    "name": "string",
    "address": "string",
    "contact_email": "string",
    "contact_phone": "string"
  },
  "ai_system": {
    "name": "string",
    "version": "string",
    "type": "HIGH_RISK",
    "intended_purpose": "string",
    "deployment_context": "string"
  },
  "incident": {
    "incident_id": "uuid",
    "date_of_occurrence": "ISO8601",
    "date_of_detection": "ISO8601",
    "incident_type": "AGT-DEL-001",
    "severity": "CRITICAL",
    "description": "Detailed description of the incident",
    "affected_users_count": 0,
    "affected_data_records": 0,
    "geographic_scope": []
  },
  "root_cause": {
    "primary_cause": "string",
    "contributing_factors": [],
    "technical_details": "string"
  },
  "containment": {
    "actions_taken": [],
    "containment_time_seconds": 0,
    "current_status": "CONTAINED | RESOLVED | ONGOING"
  },
  "corrective_measures": {
    "immediate": [],
    "long_term": [],
    "prevention_measures": []
  },
  "supporting_evidence": {
    "evidence_package_ref": "uuid",
    "forensic_timeline_ref": "uuid",
    "judge_decision_ref": "uuid",
    "policy_version_ref": "uuid"
  },
  "submitted_by": "string",
  "submission_date": "ISO8601"
}
```

**Dependencies:** FEAT-008, FEAT-011


---

### FEAT-013: DEMO_MODE

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-013 |
| **Name** | DEMO_MODE |
| **Priority** | P1 |
| **Stage** | All |

**Description:**
DEMO_MODE is a feature flag that, when enabled, loads pre-built incident scenarios and demo data. This mode is designed for sales demonstrations, training sessions, and system evaluation without requiring production agent traffic.

**User Stories:**

| ID | Story |
|----|-------|
| US-037 | As a Sales Engineer, I want pre-built demo scenarios so that I can showcase PLAYBOOK's capabilities to prospects |
| US-038 | As a Trainer, I want realistic incident scenarios so that I can train security analysts |
| US-039 | As an Evaluator, I want to assess PLAYBOOK without connecting production systems |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-061 | Given DEMO_MODE is enabled via feature flag, when the system starts, then it loads 6 pre-built disaster scenarios (including LLM-Judge Bypass Attempt and Organization Policy Switching) |
| AC-062 | Given a demo scenario is loaded, when it runs, then it simulates realistic incident progression with timestamps |
| AC-063 | Given DEMO_MODE is active, when a scenario executes, then all PLAYBOOK features (detect, classify, respond, forensics, judge layer, policy builder) process the simulated events |
| AC-064 | Given DEMO_MODE is active, when the user views the dashboard, then they see the demo incidents as if they were real |
| AC-065 | Given DEMO_MODE is disabled, when the system starts, then no demo data is loaded and only real agent traffic is processed |
| AC-066 | Given DEMO_MODE is toggled, when toggled off, then all demo incidents and data are purged from the system |

**Pre-Built Demo Scenarios:**

| Scenario | ID | Incident Type | Description |
|----------|-----|---------------|-------------|
| PocketOS Deletion | DEMO-001 | AGT-DEL-001 | Agent executes `DROP TABLE users` on production database, deleting 2.3M user records |
| Step Finance $40M | DEMO-002 | AGT-FIN-002 | Agent commits to $40M unauthorized financial transaction on Step Finance protocol |
| Meta Permission Exposure | DEMO-003 | AGT-PER-003 | Agent attempts to escalate permissions to access user data beyond authorized scope |
| UnitedHealth Denials | DEMO-004 | AGT-HRM-004 | Agent generates automated healthcare denial recommendations affecting patient coverage |
| Replit Record Deletion | DEMO-005 | AGT-DEL-001 | Agent deletes production database records in Replit's infrastructure |
| Organization Policy Switching | DEMO-006 | AGT-EXT-005 | Same data exfiltration incident processed under three different policy templates (HIPAA, Financial Services, SaaS Startup) showing ODP-driven response variation |

**Dependencies:** None (self-contained)

---

### FEAT-014: Red-Team Test Suite

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-014 |
| **Name** | Red-Team Test Suite |
| **Priority** | P1 |
| **Stage** | All |

**Description:**
The Red-Team Test Suite provides a library of adversarial tests that simulate attacks against AI agents. Tests validate that PLAYBOOK's detection rules and response playbooks correctly identify and handle attack patterns. Tests run in an isolated environment and do not affect production systems.

**User Stories:**

| ID | Story |
|----|-------|
| US-040 | As a Security Engineer, I want pre-built adversarial tests so that I can validate detection coverage |
| US-041 | As an Engineer, I want to create custom test scenarios so that I can test organization-specific threats |
| US-042 | As a Manager, I want test result trends over time so that I can track security posture improvement |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-067 | Given the test suite, when loaded, then it contains at least 50 pre-built adversarial tests covering all 16 incident types |
| AC-068 | Given a test is selected, when executed, then it runs in an isolated test environment with no production impact |
| AC-069 | Given a test executes, when it completes, then results include: detected/undetected, correct/incorrect classification, response time |
| AC-070 | Given all tests complete, when coverage analysis runs, then it identifies incident types with no test coverage |
| AC-071 | Given test results over time, when trend analysis runs, then it shows detection rate improvement or degradation |

**Test Library Structure:**

```json
{
  "test_id": "TEST-DEL-001",
  "name": "Database Table Drop",
  "incident_type": "AGT-DEL-001",
  "technique": "MITRE ATLAS T0048",
  "description": "Simulates an agent executing DROP TABLE on a production database",
  "test_steps": [
    {"step": 1, "action": "invoke_tool", "tool": "sql_query", "params": {"query": "DROP TABLE users"}},
    {"step": 2, "action": "verify_detection", "expected": "AGT-DEL-001 detected"},
    {"step": 3, "action": "verify_response", "expected": "Tool call denied"}
  ],
  "success_criteria": {
    "detected": true,
    "correct_classification": true,
    "response_time_ms": "< 1000"
  }
}
```

**Dependencies:** FEAT-002, FEAT-005

---

### FEAT-015: TerraFabric Fleet View

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-015 |
| **Name** | TerraFabric Fleet View |
| **Priority** | P1 |
| **Stage** | DETECT |

**Description:**
The TerraFabric Fleet View integrates with the TerraFabric agent management platform to provide visibility into the entire agent fleet. It displays deployment status, health metrics, and security posture for all agents managed by TerraFabric.

**User Stories:**

| ID | Story |
|----|-------|
| US-043 | As an Operations Manager, I want to see all agents in my TerraFabric fleet so that I have complete visibility |
| US-044 | As a Manager, I want fleet-wide security metrics so that I can assess aggregate risk |
| US-045 | As an Operator, I want to drill down from fleet view to individual agent detail |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-072 | Given TerraFabric API is configured, when fleet view loads, then it displays all agents with their deployment status |
| AC-073 | Given the fleet view, when it renders, then each agent shows its health score, active incidents, and last activity |
| AC-074 | Given the fleet view, when aggregated, then it displays fleet-wide metrics: total agents, active incidents, average health score |
| AC-075 | Given an agent in fleet view, when clicked, then it navigates to the detailed agent health view |
| AC-076 | Given TerraFabric API is unavailable, when fleet view loads, then it displays cached data with a staleness indicator |

**Dependencies:** TerraFabric API (EXT-003)

---

### FEAT-016: HIPAA Policy Pack

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-016 |
| **Name** | HIPAA Policy Pack |
| **Priority** | P1 |
| **Stage** | CLASSIFY / RESPOND |

**Description:**
The HIPAA Policy Pack provides specialized detection rules, classification logic, and response playbooks tailored for healthcare AI agents. It ensures that incidents involving protected health information (PHI) are handled in accordance with HIPAA requirements.

**User Stories:**

| ID | Story |
|----|-------|
| US-046 | As a Healthcare Security Officer, I want HIPAA-specific detection rules so that PHI-related incidents are identified |
| US-047 | As an Officer, I want automated HIPAA breach assessment so that I can determine notification obligations |
| US-048 | As a Compliance Officer, I want HIPAA-compliant evidence handling so that PHI in evidence is properly protected |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-077 | Given the HIPAA Policy Pack is enabled, when an agent handles PHI, then all access is subject to enhanced monitoring |
| AC-078 | Given a PHI-related incident, when classified, then the system automatically applies HIPAA breach risk assessment |
| AC-079 | Given a HIPAA breach is detected, when assessment completes, then the system determines if notification obligations are triggered |
| AC-080 | Given evidence contains PHI, when the evidence package is generated, then all PHI is encrypted and access is audit-logged |
| AC-081 | Given the HIPAA Policy Pack, when compliance mapping is viewed, then it shows mapping to 45 CFR 164.306, 164.312, and 164.404 |

**HIPAA-Specific Detection Rules:**

| Rule ID | Name | HIPAA Reference | Description |
|---------|------|-----------------|-------------|
| HIPAA-001 | PHI Unauthorized Access | 164.312(a)(1) | Detects agent accessing PHI beyond authorized scope |
| HIPAA-002 | PHI Unencrypted Transmission | 164.312(e)(1) | Detects PHI being transmitted without encryption |
| HIPAA-003 | Minimum Necessary Violation | 164.502(b) | Detects agent accessing more PHI than necessary for task |
| HIPAA-004 | Audit Log Tampering | 164.312(b) | Detects attempts to modify or delete audit logs |
| HIPAA-005 | Patient Rights Violation | 164.524 | Detects agent actions that may violate patient access rights |

**Dependencies:** FEAT-002, FEAT-011

---
### FEAT-017: Deterministic Judge Classification

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-017 |
| **Name** | Deterministic Judge Classification |
| **Priority** | P0 |
| **Stage** | JUDGE (Enforcement) |

**Description:**
The Deterministic Judge Classification engine is a local, rule-based classification system that operates without any LLM dependency in the enforcement path. It evaluates every intercepted agent action against a compiled rule base and produces a deterministic classification decision within 50 milliseconds. Because classification is entirely rule-based (not LLM-based), it is immune to the four known LLM-judge bypass patterns: context displacement, tool chaining, homoglyph injection, and confidence hijacking. This engine is the core enforcement component of the Judge Layer.

**User Stories:**

| ID | Story |
|----|-------|
| US-049 | As a security engineer, I want classification without LLM dependency so that enforcement is reliable and deterministic |
| US-050 | As a compliance officer, I want every agent action classified by rules (not probabilistic models) so that decisions are auditable and reproducible |
| US-051 | As a SOC analyst, I want sub-50ms classification so that agent operations are not perceptibly delayed |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-082 | Given any agent action, when classification runs, then it produces a decision (ALLOW, DENY, QUARANTINE, ESCALATE) within 50ms -- measured at p99 |
| AC-083 | Given a bypass attempt using context displacement (injected context designed to override safety instructions), when the action is classified, then the deterministic classifier correctly identifies the malicious intent and blocks the action |
| AC-084 | Given a bypass attempt using homoglyph injection (Unicode homoglyphs in tool names or parameters), when the action is classified, then the classifier detects the homoglyphs and applies the same rules as for canonical characters |
| AC-085 | Given a bypass attempt using confidence hijacking (manipulated confidence markers or repeated assertions), when the action is classified, then the classifier ignores confidence manipulation and evaluates only the action content against rules |
| AC-086 | Given a bypass attempt using tool chaining (splitting malicious intent across multiple benign tool calls), when the chained sequence is evaluated, then the classifier detects the composite malicious pattern and blocks the sequence |
| AC-087 | Given the same action under the same conditions, when classified multiple times, then the classifier produces identical decisions every time (deterministic behavior) |
| AC-088 | Given the classifier is operating, when a rule update is deployed, then the new rules take effect within 30 seconds without pipeline restart |
| AC-089 | Given a classification decision, when it is rendered, then the full rationale (matched rules, rule IDs, confidence score) is logged for audit |

**Deterministic Classification Rule Format:**

```json
{
  "judge_rule_id": "JRULE-001",
  "name": "Destructive Database Operation",
  "priority": 1,
  "decision": "DENY",
  "conditions": {
    "tool_name_pattern": "(?i)(sql|query|database|db)",
    "parameter_patterns": {
      "query": "(?i)(DROP TABLE|DELETE\\s+FROM|TRUNCATE TABLE)"
    },
    "scope": "single_action",
    "severity_override": "CRITICAL"
  },
  "bypass_resistance": {
    "context_displacement": "immune",
    "homoglyph_injection": "detect_and_normalize",
    "confidence_hijacking": "ignore",
    "tool_chaining": "sequence_analysis"
  },
  "rationale_template": "Blocked destructive database operation: matched {matched_patterns} in tool {tool_name}",
  "created_at": "2025-01-01T00:00:00Z",
  "version": "1.0.0"
}
```

**Classification Decision Schema:**

```json
{
  "decision_id": "uuid",
  "timestamp": "ISO8601",
  "action": {
    "tool_name": "string",
    "parameters": {},
    "agent_id": "string",
    "session_id": "string"
  },
  "decision": "ALLOW | DENY | QUARANTINE | ESCALATE",
  "rationale": "Blocked destructive database operation: matched DROP TABLE pattern",
  "matched_rules": ["JRULE-001", "JRULE-003"],
  "confidence": 0.99,
  "latency_ms": 12,
  "bypass_attempts_detected": [],
  "deterministic": true
}
```

**Dependencies:** FEAT-019 (Judge Layer Architecture)

---

### FEAT-018: LLM-Judge Bypass Detection

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-018 |
| **Name** | LLM-Judge Bypass Detection |
| **Priority** | P1 |
| **Stage** | JUDGE (Detection) |

**Description:**
The LLM-Judge Bypass Detection module monitors for known adversarial patterns that attackers use to evade LLM-based guardrails and safety controls. It detects four specific bypass techniques -- context window stuffing, homoglyph injection, confidence hijacking, and tool chaining -- and generates CRITICAL incidents for each detection. Because PLAYBOOK's Judge Layer (FEAT-017) uses deterministic rules rather than an LLM, it is inherently immune to these bypasses; this module serves as both a detection layer and a demonstration of PLAYBOOK's security advantage over LLM-based guardrails.

**User Stories:**

| ID | Story |
|----|-------|
| US-052 | As a SOC analyst, I want to see when attackers try to bypass my guardrails so that I can understand the threat landscape |
| US-053 | As a security engineer, I want bypass attempts logged and reported so that I can tune my defenses |
| US-054 | As a compliance officer, I want evidence that our deterministic judge is immune to known bypass patterns |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-090 | Given a context displacement attack (injected adversarial context designed to displace system instructions), when the action is evaluated, then the system detects the displacement pattern and reports it as AGT-BYP-014 |
| AC-091 | Given a homoglyph injection attack (Unicode homoglyphs replacing canonical characters), when the action is evaluated, then the system detects the homoglyphs, normalizes them, reports the attempt as AGT-BYP-014, and applies rules against the normalized content |
| AC-092 | Given a confidence hijacking attack (manipulated confidence markers or assertion patterns), when the action is evaluated, then the system detects the manipulation, ignores false confidence signals, and reports the attempt as AGT-BYP-014 |
| AC-093 | Given a tool chaining attack (malicious intent split across multiple benign tool calls), when the sequence is evaluated, then the system detects the composite pattern, blocks the full chain, and reports the attempt as AGT-BYP-014 |
| AC-094 | Given any bypass attempt, when it is detected, then a CRITICAL incident is created within 2 seconds and appears in the dashboard |
| AC-095 | Given bypass detection metrics, when aggregated, then they show total attempts, pattern type distribution, and detection rate |

**Bypass Pattern Definitions:**

| Pattern | ID | Description | Detection Method |
|---------|-----|-------------|------------------|
| Context Displacement | BYPASS-001 | Attacker injects large volumes of adversarial context to push safety instructions out of the model's context window | Detect oversized context, adversarial phrase repetition, known displacement patterns |
| Homoglyph Injection | BYPASS-002 | Attacker uses visually identical Unicode characters (e.g., Cyrillic 'a' vs Latin 'a') to evade string-based filters | Unicode normalization, homoglyph mapping tables, canonical form comparison |
| Confidence Hijacking | BYPASS-003 | Attacker manipulates confidence markers, uses repeated assertions, or formats input to trick the model into high-confidence misclassification | Detect artificial confidence markers, assertion repetition patterns, formatting anomalies |
| Tool Chaining | BYPASS-004 | Attacker splits a malicious operation into a sequence of individually benign tool calls that only become malicious in combination | Sequence analysis, cross-call dependency tracking, composite pattern matching |

**Dependencies:** FEAT-017 (Deterministic Judge Classification), FEAT-009 (Incident Dashboard)

---

### FEAT-019: Judge Layer Architecture

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-019 |
| **Name** | Judge Layer Architecture |
| **Priority** | P0 |
| **Stage** | JUDGE (Infrastructure) |

**Description:**
The Judge Layer is a separate enforcement component that is wrapped around all agent actions. It intercepts every action before execution, applies deterministic classification (FEAT-017), renders a decision (ALLOW, DENY, QUARANTINE, ESCALATE), and enforces that decision before the action reaches any external system. The Judge Layer is designed to be the single enforcement point for all agent activity -- no action can bypass the Judge. Every decision is logged with a full rationale for the audit trail.

**User Stories:**

| ID | Story |
|----|-------|
| US-055 | As a compliance officer, I want every agent action to pass through a judge so that no action executes without authorization |
| US-056 | As a security architect, I want the judge to be a separate component so that it cannot be bypassed by the agent or orchestration layer |
| US-057 | As an auditor, I want every judge decision logged with rationale so that I can reconstruct the complete authorization chain |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-096 | Given any agent action, when it is initiated, then it is intercepted by the Judge Layer before execution -- 100% interception rate |
| AC-097 | Given the Judge Layer intercepts an action, when classification completes, then a decision (ALLOW, DENY, QUARANTINE, ESCALATE) is rendered within 50ms |
| AC-098 | Given a decision is rendered, when it is DENY, QUARANTINE, or ESCALATE, then the action is blocked before reaching any external system |
| AC-099 | Given a decision is rendered, when it is ALLOW, then the action is forwarded to the target system with no perceptible delay |
| AC-100 | Given any decision, when it is rendered, then the full rationale (matched rules, decision type, timestamp, latency) is logged to the audit trail |
| AC-101 | Given the Judge Layer is active, when it fails (e.g., process crash), then the system fails-closed (all actions blocked) until the Judge recovers |
| AC-102 | Given Judge Layer decisions over time, when aggregated, then they are available in the dashboard with metrics: total decisions, decision distribution, average latency |
| AC-103 | Given the Judge Layer is active, when a SupraWall guardrail decision is available (FEAT-020), then it is correlated with the Judge decision in the evidence package |

**Judge Layer Decision Types:**

| Decision | Action | Agent State | Logging | Incident Created |
|----------|--------|-------------|---------|------------------|
| ALLOW | Forward to target system | Normal | Decision logged with rationale | No |
| DENY | Block action; return policy error to agent | Normal | Decision logged with rationale | Yes (AGT-BYP-014) |
| QUARANTINE | Block action; suspend agent | Suspended | Decision logged with rationale | Yes (AGT-BYP-014) |
| ESCALATE | Hold action pending human review | Pending review | Decision logged with rationale | Yes (AGT-REG-016) |

**Judge Layer Architecture:**

```
+---------------------------------------------------------------------+
|                         JUDGE LAYER (FEAT-019)                      |
|                                                                     |
|  +------------------+    +------------------+    +--------------+   |
|  | Action           |    | Deterministic    |    | Decision     |   |
|  | Interceptor      | -> | Classifier       | -> | Enforcer     |   |
|  | (Wraps all       |    | (FEAT-017)       |    | (Applies     |   |
|  |  agent actions)  |    | - Local rules    |    |  ALLOW/DENY/ |   |
|  |                  |    | - No LLM         |    |  QUARANTINE/ |   |
|  | 100% interception|    | - <50ms          |    |  ESCALATE)   |   |
|  +------------------+    +------------------+    +--------------+   |
|          |                      |                       |           |
|          v                      v                       v           |
|  +------------------+    +------------------+    +--------------+   |
|  | Bypass Detection |    | Decision Rationale  |   | Audit Log   |   |
|  | (FEAT-018)       |    | Logger             |    | (Immutable)  |   |
|  | - 4 patterns     |    | - Matched rules    |    | - Timestamps |   |
|  | - Reports to     |    | - Confidence       |    | - Decisions  |   |
|  |   dashboard      |    | - Latency          |    | - Rationales |   |
|  +------------------+    +------------------+    +--------------+   |
|                                                                     |
|  +------------------+    +------------------+                       |
|  | SupraWall        |    | Forensics        |                       |
|  | Integration      |    | Pipeline         |                       |
|  | (FEAT-020)       |    | (FEAT-007,     |                       |
|  | - Detect existing|    |  FEAT-008)       |                       |
|  |   guardrails     |    |                  |                       |
|  | - Correlate      |    |                  |                       |
|  |   decisions      |    |                  |                       |
|  +------------------+    +------------------+                       |
+---------------------------------------------------------------------+
```

**Dependencies:** Lobster Trap DPI (EXT-001), FEAT-001 (Log Ingestion)

---

### FEAT-020: SupraWall Integration Awareness

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-020 |
| **Name** | SupraWall Integration Awareness |
| **Priority** | P1 |
| **Stage** | JUDGE (Integration) |

**Description:**
SupraWall Integration Awareness enables PLAYBOOK to detect when a SupraWall open-source guardrail (Apache 2.0, April 30, 2026) is already deployed in the agent environment. Rather than replacing SupraWall, PLAYBOOK complements it by ingesting SupraWall decision events, correlating them with Judge Layer decisions, and feeding all guardrail decisions into the PLAYBOOK forensics pipeline. This ensures that organizations with existing SupraWall deployments get unified visibility and evidence collection across all their guardrail systems.

**User Stories:**

| ID | Story |
|----|-------|
| US-058 | As an enterprise architect, I want PLAYBOOK to work with my existing SupraWall deployment so that I do not need to replace working guardrails |
| US-059 | As a security engineer, I want SupraWall decisions visible in PLAYBOOK so that I have a single dashboard for all guardrail events |
| US-060 | As a compliance officer, I want SupraWall decisions included in forensic evidence so that I have complete audit coverage |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-104 | Given a SupraWall guardrail is deployed in the environment, when PLAYBOOK starts, then it detects the SupraWall instance within 60 seconds |
| AC-105 | Given SupraWall is detected, when PLAYBOOK initializes, then it establishes a decision event ingestion pipeline without disrupting SupraWall operations |
| AC-106 | Given SupraWall renders a decision, when the decision event is ingested, then it appears in the PLAYBOOK dashboard within 2 seconds |
| AC-107 | Given both SupraWall and Judge Layer decisions exist for the same action, when forensics processes the incident, then both decisions are correlated in the evidence package |
| AC-108 | Given SupraWall is present, when PLAYBOOK renders its own Judge decision, then the two decisions are shown side-by-side in the incident detail view |
| AC-109 | Given SupraWall is not present, when PLAYBOOK operates, then it functions normally without SupraWall integration |
| AC-110 | Given SupraWall is removed from the environment, when PLAYBOOK detects the removal, then it updates its integration status and continues operating |

**SupraWall Decision Event Schema:**

```json
{
  "suprawall_event_id": "uuid",
  "timestamp": "ISO8601",
  "suprawall_version": "string",
  "decision": "ALLOW | DENY | FLAG",
  "action": {
    "tool_name": "string",
    "parameters": {}
  },
  "detection_rules": ["SW-RULE-001"],
  "confidence": 0.95,
  "source": "suprawall",
  "ingestion_timestamp": "ISO8601"
}
```

**SupraWall vs. PLAYBOOK Comparison Matrix:**

| Capability | SupraWall (Open Source) | PLAYBOOK Judge Layer |
|------------|------------------------|---------------------|
| License | Apache 2.0 | Commercial |
| Release Date | April 30, 2026 | Current |
| Classification | LLM-based guardrail | Deterministic rule-based |
| Bypass Immunity | Vulnerable to 4 patterns | Immune to all 4 patterns |
| Forensics | Basic logging | Full evidence package |
| Compliance Mapping | Limited | Full EU AI Act, HIPAA |
| Integration | Standalone | Complements SupraWall |

**Dependencies:** FEAT-019 (Judge Layer Architecture), FEAT-009 (Incident Dashboard)


---

### FEAT-021: NIST Baseline Templates

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-021 |
| **Name** | NIST Baseline Templates |
| **Priority** | P0 |
| **Stage** | POLICY |

**Description:**
NIST Baseline Templates serve 12 immutable NIST incident type baselines, each containing Organization-Defined Parameter (ODP) placeholders. These baselines are derived from NIST IR 8346 (AG-MG.1) and provide the authoritative starting point for all organizational policy customization. Baselines are immutable — they cannot be modified — ensuring that every organization begins from a NIST-validated foundation. Each baseline includes severity defaults, response actions, compliance mappings, and references to the NIST Agentic Profile.

**User Stories:**

| ID | Story |
|----|-------|
| US-061 | As a security engineer, I want to start from a NIST-validated baseline so that I don't build policies from scratch |
| US-062 | As a compliance officer, I want immutable NIST baselines so that I can prove my policies are built on authoritative standards |
| US-063 | As an auditor, I want NIST baseline references in every policy so that I can trace compliance to the source standard |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-111 | Given the NIST Baseline Templates are loaded, when the system initializes, then all 12 incident types have NIST baselines with ODP placeholders available |
| AC-112 | Given a NIST baseline, when an admin attempts to edit it, then the system rejects the edit and displays an "immutable baseline" message |
| AC-113 | Given a NIST baseline for any incident type, when it is viewed, then it includes: severity default, response actions, compliance mappings to NIST AI RMF, and a reference to NIST Agentic Profile AG-MG.1 |
| AC-114 | Given an organization creates a custom policy, when it is saved, then the system stores the NIST baseline reference ID and the organization's ODP overrides separately |
| AC-115 | Given the NIST baseline templates, when they are updated (new NIST revision), then the system maintains version history and notifies organizations of available updates |

**NIST Baseline Template Schema:**

```json
{
  "baseline_id": "NIST-BL-001",
  "nist_reference": "NIST IR 8346 AG-MG.1",
  "incident_type": "AGT-DEL-001",
  "incident_name": "Data Destruction",
  "immutable": true,
  "version": "2024.1",
  "odp_placeholders": {
    "severity_threshold": {"default": "CRITICAL", "type": "enum", "allowed": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]},
    "auto_contain_enabled": {"default": true, "type": "boolean"},
    "escalation_contacts": {"default": ["security-team@example.com"], "type": "list"},
    "response_time_sla": {"default": 60, "type": "number", "unit": "seconds"},
    "forensic_level": {"default": "FULL", "type": "enum", "allowed": ["FULL", "STANDARD", "MINIMAL"]},
    "notify_targets": {"default": ["security-team@example.com"], "type": "list"},
    "compliance_report": {"default": true, "type": "boolean"},
    "record_threshold": {"default": 100, "type": "number"}
  },
  "response_actions": ["DENY", "QUARANTINE", "LOG", "HUMAN_REVIEW"],
  "compliance_mappings": [
    {"framework": "NIST_AI_RMF", "control": "GV.RR-04"},
    {"framework": "NIST_AI_RMF", "control": "MP-IM-01"},
    {"framework": "EU_AI_ACT", "article": "Art. 15"}
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Dependencies:** None (foundational)

---

### FEAT-022: Organization-Defined Parameters (ODPs)

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-022 |
| **Name** | Organization-Defined Parameters (ODPs) |
| **Priority** | P0 |
| **Stage** | POLICY |

**Description:**
Organization-Defined Parameters (ODPs) allow each organization to customize 8 configurable parameters per incident type, overriding NIST baseline defaults where permitted. ODPs define an organization's risk tolerance, response procedures, notification preferences, and compliance settings. Each ODP is stored per-organization, with full versioning and audit trail for every change.

**User Stories:**

| ID | Story |
|----|-------|
| US-064 | As a CISO, I want to set my organization's risk tolerance per incident type so that responses match our risk profile |
| US-065 | As a security engineer, I want ODPs to override NIST defaults where permitted so that I can customize without breaking compliance |
| US-066 | As an auditor, I want every ODP change versioned and audited so that I can verify compliance over time |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-116 | Given an organization configures ODPs, when they are saved, then all 8 ODPs are stored per incident type: severity_threshold, auto_contain_enabled, escalation_contacts, response_time_sla, forensic_level, notify_targets, compliance_report, record_threshold |
| AC-117 | Given an ODP value conflicts with its NIST baseline, when the conflict is detected, then the system flags the conflict with severity WARNING or BLOCKED and requires explicit override approval |
| AC-118 | Given ODPs are configured, when they are stored, then they are stored per-organization and isolated from other organizations' ODPs |
| AC-119 | Given an ODP is changed, when the change is saved, then the system creates a new version and records: who changed it, when, the previous value, and the new value |
| AC-120 | Given an organization has not customized an ODP, when the system needs the value, then it uses the NIST baseline default |
| AC-121 | Given ODPs are active, when an incident is classified, then the system uses the organization's ODPs to determine severity, response actions, and escalation targets |

**ODP Definitions:**

| ODP Name | Type | Description | NIST Default |
|----------|------|-------------|--------------|
| severity_threshold | enum (CRITICAL/HIGH/MEDIUM/LOW) | Minimum severity at which automated response is triggered | Per incident type |
| auto_contain_enabled | boolean | Whether automated containment (quarantine/deny) is enabled | true |
| escalation_contacts | list (email/phone) | Recipients for human escalation notifications | [security-team] |
| response_time_sla | number (seconds) | Maximum time allowed between detection and response | 60 |
| forensic_level | enum (FULL/STANDARD/MINIMAL) | Depth of forensic evidence collection | FULL |
| notify_targets | list (email/phone/webhook) | Recipients for incident notifications | [security-team] |
| compliance_report | boolean | Whether to auto-generate compliance reports | true |
| record_threshold | number (count) | Minimum affected records to trigger CRITICAL severity | 100 |

**ODP Storage Schema:**

```json
{
  "odp_id": "uuid",
  "organization_id": "uuid",
  "incident_type": "AGT-DEL-001",
  "baseline_reference": "NIST-BL-001",
  "odp_values": {
    "severity_threshold": "CRITICAL",
    "auto_contain_enabled": true,
    "escalation_contacts": ["security@acme.com", "ciso@acme.com"],
    "response_time_sla": 30,
    "forensic_level": "FULL",
    "notify_targets": ["security@acme.com", "ops@acme.com"],
    "compliance_report": true,
    "record_threshold": 50
  },
  "version": 3,
  "created_at": "2025-01-10T00:00:00Z",
  "updated_at": "2025-01-15T00:00:00Z",
  "updated_by": "user_id_789"
}
```

**Dependencies:** FEAT-021 (NIST Baseline Templates)

---

### FEAT-023: Visual Policy Builder

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-023 |
| **Name** | Visual Policy Builder |
| **Priority** | P0 |
| **Stage** | POLICY |

**Description:**
The Visual Policy Builder is a React component that provides a visual interface for editing Organization-Defined Parameters (ODPs). It displays a side-by-side view with the NIST baseline on the left (read-only) and the ODP editor on the right (editable). The component provides appropriate input controls for each ODP type (dropdown for enums, toggle for booleans, text input for lists, number input for numeric values), along with conflict warnings, save/preview/test actions, and inline validation.

**User Stories:**

| ID | Story |
|----|-------|
| US-067 | As a compliance officer, I want a visual interface to customize our incident response policies so that I don't need to edit YAML |
| US-068 | As a CISO, I want to see the NIST baseline alongside my customizations so that I understand what I'm changing and why |
| US-069 | As a security engineer, I want conflict warnings inline so that I catch compliance issues before they become problems |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-122 | Given the Visual Policy Builder loads, when it renders, then it displays a side-by-side view: NIST baseline (read-only) on the left + ODP editor (editable) on the right |
| AC-123 | Given an enum ODP (severity, forensic_level), when it is displayed, then it uses a dropdown/select control with the allowed values |
| AC-124 | Given a boolean ODP (auto_contain, compliance_report), when it is displayed, then it uses a toggle switch control |
| AC-125 | Given a list ODP (escalation_contacts, notify_targets), when it is displayed, then it uses a text input that accepts comma-separated values with chip/tag display |
| AC-126 | Given a numeric ODP (response_time_sla, record_threshold), when it is displayed, then it uses a number input with min/max validation |
| AC-127 | Given the editor has unsaved changes, when the user clicks Save, then the system validates all ODPs, creates a new policy version, and activates the changes |
| AC-128 | Given the user clicks Preview, when preview mode is active, then the system shows how the current ODPs would affect recent historical incidents |
| AC-129 | Given the user clicks Test, when test mode is active, then the system runs a simulated incident through the current ODPs without affecting production |
| AC-130 | Given an ODP conflicts with its NIST baseline, when the conflict is detected, then a warning is displayed inline with the ODP field showing severity (WARNING or BLOCKED) and a resolution suggestion |

**Visual Policy Builder Layout:**

```
+---------------------------------------------------------------------+
|  POLICY BUILDER                                          [Save]     |
|  Incident Type: AGT-DEL-001 (Data Destruction)          [Preview]   |
|  NIST Baseline: v2024.1  |  Policy Version: v3          [Test]     |
+-----------------------------------+---------------------------------+
|  NIST BASELINE (Read-Only)        |  ODP EDITOR (Editable)          |
|                                   |                                 |
|  Severity: CRITICAL               |  Severity: [CRITICAL ▼]         |
|  Auto-Contain: true               |  Auto-Contain: [● ON]           |
|  Escalation: [security-team]      |  Escalation: [security@acme.c]  |
|  Response SLA: 60s                |  Response SLA: [30] seconds     |
|  Forensic Level: FULL             |  Forensic Level: [FULL ▼]       |
|  Notify: [security-team]          |  Notify: [security@, ops@]      |
|  Compliance Report: true          |  Compliance Report: [● ON]      |
|  Record Threshold: 100            |  Record Threshold: [50]         |
|                                   |                                 |
|  NIST Ref: AG-MG.1               |  ⚠️ WARNING: record_threshold   |
|  Controls: GV.RR-04, MP-IM-01    |    (50) is below baseline (100) |
|                                   |    Suggestion: Set to ≥ 100     |
+-----------------------------------+---------------------------------+
|  CONFLICT DETECTION STATUS: 1 warning, 0 blocked                    |
+---------------------------------------------------------------------+
```

**Dependencies:** FEAT-021 (NIST Baseline Templates), FEAT-022 (ODPs)

---

### FEAT-024: Industry Templates

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-024 |
| **Name** | Industry Templates |
| **Priority** | P1 |
| **Stage** | POLICY |

**Description:**
Industry Templates provide pre-configured ODP sets for 6 industries, based on industry best practices and regulatory requirements. Each template sets all 8 ODPs for all 12 incident types, providing a one-click policy configuration for organizations in regulated industries. Applying a template creates a new policy version and can be rolled back at any time.

**User Stories:**

| ID | Story |
|----|-------|
| US-070 | As a healthcare CTO, I want to apply a HIPAA template with one click so that I'm immediately compliant |
| US-071 | As a fintech CISO, I want a PCI-DSS template so that financial data handling meets compliance requirements |
| US-072 | As a SaaS startup founder, I want a startup template with sensible defaults so that I can be secure without hiring a security team |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-131 | Given the Industry Templates are loaded, when the system displays them, then all 6 templates are available: HIPAA, SOC2, PCI-DSS, GDPR, Financial Services, SaaS Startup |
| AC-132 | Given an industry template is selected, when it is viewed, then it shows all 8 ODPs for all 12 incident types with their values and rationale |
| AC-133 | Given a template, when it is examined, then each ODP value includes a rationale based on industry best practices (e.g., "HIPAA requires 30-second response for PHI incidents") |
| AC-134 | Given a user clicks Apply Template, when the action completes, then the template ODPs are applied to all 12 incident types and a new policy version is created within 10 seconds |
| AC-135 | Given a template is applied, when it is activated, then the audit trail records: user, timestamp, template name, previous version, new version |
| AC-136 | Given an applied template, when a user wants to revert, then the system provides a one-click rollback to the previous version |

**Industry Template Summary:**

| Template | Target Sector | Key Characteristics | Response SLA Default | Auto-Contain Default |
|----------|--------------|---------------------|----------------------|----------------------|
| HIPAA | Healthcare | Emphasizes PHI protection, breach notification, encrypted evidence | 30 seconds | true |
| SOC2 | SaaS/Enterprise | Focus on access controls, audit trails, availability monitoring | 60 seconds | true |
| PCI-DSS | Financial/Payments | Cardholder data protection, network segmentation, encryption | 15 seconds | true |
| GDPR | EU Data Processors | Data subject rights, breach notification (72h), data minimization | 45 seconds | true |
| Financial Services | Banking/Trading | Low-latency response, transaction integrity, market abuse detection | 10 seconds | true |
| SaaS Startup | Early-stage SaaS | Balanced security with operational overhead, growth-friendly | 120 seconds | false |

**Dependencies:** FEAT-021 (NIST Baseline Templates), FEAT-022 (ODPs), FEAT-023 (Visual Policy Builder)

---

### FEAT-025: Policy Conflict Detection

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-025 |
| **Name** | Policy Conflict Detection |
| **Priority** | P1 |
| **Stage** | POLICY |

**Description:**
Policy Conflict Detection automatically detects when an organization's ODPs conflict with their corresponding NIST baselines. Conflicts are categorized as either WARNING (non-blocking, but may create compliance gaps) or BLOCKED (must be resolved before the policy can be saved). For each conflict, the system provides a severity classification and a resolution suggestion.

**User Stories:**

| ID | Story |
|----|-------|
| US-073 | As a security engineer, I want warnings when my custom rules conflict with NIST recommendations so that I don't create compliance gaps |
| US-074 | As a compliance officer, I want blocked conflicts for critical overrides so that I can't accidentally weaken security controls |
| US-075 | As a CISO, I want conflict resolution suggestions so that I can make informed decisions about overrides |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-137 | Given an ODP sets severity below the NIST baseline (e.g., NIST says HIGH, org sets LOW), when conflict detection runs, then it flags a WARNING with message: "Severity downgrade may create compliance gap" |
| AC-138 | Given an ODP disables auto-contain (sets auto_contain_enabled to false), when the NIST baseline default is true, then the system flags a WARNING: "Auto-contain disabled — incidents will not be automatically contained" |
| AC-139 | Given an ODP removes all escalation contacts (empty list), when the NIST baseline has at least one, then the system flags a BLOCKED conflict: "At least one escalation contact is required" and prevents saving |
| AC-140 | Given an ODP sets response_time_sla above the NIST baseline, when the SLA is exceeded, then the system flags a WARNING: "Response SLA exceeds NIST recommendation — compliance obligation may not be met" |
| AC-141 | Given a conflict is detected, when it is displayed, then it shows severity (WARNING or BLOCKED), a description, and a resolution suggestion |
| AC-142 | Given the Visual Policy Builder is open, when a conflict exists, then it is displayed inline next to the relevant ODP field with a visual indicator (yellow for WARNING, red for BLOCKED) |
| AC-143 | Given all conflicts are resolved, when the user saves the policy, then the system creates a new version with no outstanding conflicts |

**Conflict Detection Rules:**

| Rule ID | Conflict Type | Detection Logic | Severity | Suggestion |
|---------|--------------|-----------------|----------|------------|
| PCD-001 | Severity Downgrade | ODP severity < NIST baseline severity | WARNING | "Consider matching or exceeding NIST severity" |
| PCD-002 | Auto-Contain Disabled | auto_contain_enabled = false when baseline = true | WARNING | "Enable auto-contain for automated response" |
| PCD-003 | Missing Escalation | escalation_contacts is empty when baseline has contacts | BLOCKED | "Add at least one escalation contact" |
| PCD-004 | SLA Exceedance | response_time_sla > NIST baseline SLA | WARNING | "Reduce SLA to meet NIST recommendation" |
| PCD-005 | Forensic Level Reduction | forensic_level < NIST baseline forensic_level | WARNING | "Consider higher forensic level for evidence quality" |
| PCD-006 | Compliance Report Disabled | compliance_report = false when baseline = true | WARNING | "Enable compliance reports for audit trail" |
| PCD-007 | Record Threshold Increase | record_threshold > NIST baseline | WARNING | "Lower threshold for earlier detection" |

**Dependencies:** FEAT-021 (NIST Baseline Templates), FEAT-022 (ODPs)

---

### FEAT-026: Policy Versioning & Audit

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-026 |
| **Name** | Policy Versioning & Audit |
| **Priority** | P1 |
| **Stage** | POLICY |

**Description:**
Policy Versioning & Audit tracks every change to organizational policies. Every ODP change creates a new version with full provenance: who changed what, when, from what value, to what value. The system provides a diff view between versions, rollback capability to any previous version, and export of version history for external audit.

**User Stories:**

| ID | Story |
|----|-------|
| US-076 | As an auditor, I want to see the complete history of policy changes so that I can verify compliance over time |
| US-077 | As a security engineer, I want to diff between versions so that I can understand exactly what changed |
| US-078 | As a CISO, I want to roll back to any previous version so that I can quickly undo problematic changes |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-144 | Given an ODP is changed, when the change is saved, then the system creates a new policy version and records: user ID, timestamp, ODP field, previous value, new value |
| AC-145 | Given multiple policy versions exist, when the version history is viewed, then it displays a chronological list of all versions with author, timestamp, and change summary |
| AC-146 | Given two versions are selected, when diff view is activated, then the system shows a side-by-side comparison highlighting all ODP differences between the versions |
| AC-147 | Given a previous version, when a user initiates rollback, then the system reverts all ODPs to that version's values and creates a new version labeled "Rollback to v{N}" |
| AC-148 | Given the version history, when the export button is clicked, then the system generates an audit-ready export (PDF or CSV) containing all version records |
| AC-149 | Given a rollback is performed, when it completes, then the rolled-back ODPs are active within 30 seconds and the audit trail records the rollback action |

**Version History Schema:**

```json
{
  "version_id": "uuid",
  "version_number": 3,
  "organization_id": "uuid",
  "timestamp": "ISO8601",
  "author": {
    "user_id": "uuid",
    "user_name": "Jane Smith",
    "role": "CISO"
  },
  "change_type": "ODP_UPDATE | TEMPLATE_APPLY | ROLLBACK | CONFLICT_RESOLUTION",
  "changes": [
    {
      "odp_field": "response_time_sla",
      "incident_type": "AGT-DEL-001",
      "previous_value": 60,
      "new_value": 30,
      "conflict_status": "resolved"
    }
  ],
  "baseline_reference": "NIST-BL-001",
  "conflict_summary": {
    "warnings": 0,
    "blocked": 0,
    "total": 0
  },
  "rollback_to": null
}
```

**Dependencies:** FEAT-022 (ODPs)

---

### FEAT-027: Policy Marketplace

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-027 |
| **Name** | Policy Marketplace |
| **Priority** | P2 |
| **Stage** | POLICY |

**Description:**
The Policy Marketplace is a community platform for sharing and discovering ODP configurations. Organizations can upload their ODP configurations (anonymized), download configurations from other organizations, vote and rate configurations, and search by industry, organization size, and compliance framework. The most popular configurations are highlighted to help newcomers find proven setups.

**User Stories:**

| ID | Story |
|----|-------|
| US-079 | As a startup CTO, I want to download proven ODP configurations from other companies so that I don't reinvent the wheel |
| US-080 | As a security engineer, I want to share our ODP configuration (anonymized) so that others can benefit from our experience |
| US-081 | As a compliance officer, I want to search for ODPs by compliance framework so that I can find configurations that match our requirements |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-150 | Given a user has a policy configured, when they click Upload, then the system uploads an anonymized ODP configuration (no org-identifying data) to the marketplace |
| AC-151 | Given the marketplace is browsed, when configurations are displayed, then each shows: title, description, industry, organization size, compliance framework, rating, download count |
| AC-152 | Given a marketplace configuration, when a user rates or votes on it, then the rating is updated and the most popular configurations appear in a "Top Rated" section |
| AC-153 | Given a user searches the marketplace, when they filter by industry, size, or compliance framework, then only matching configurations are displayed |
| AC-154 | Given a user downloads a marketplace configuration, when it is downloaded, then the system imports it as a draft policy that can be reviewed and customized before activation |
| AC-155 | Given the marketplace, when it loads, then the most popular configurations (by downloads and ratings) are highlighted in a dedicated section |
| AC-156 | Given a marketplace configuration is downloaded, when the user applies it, then the system runs conflict detection and creates a new policy version |

**Dependencies:** FEAT-022 (ODPs), FEAT-026 (Policy Versioning & Audit)

---

### FEAT-028: Multi-Tenant ODPs

| Attribute | Value |
|-----------|-------|
| **Feature ID** | FEAT-028 |
| **Name** | Multi-Tenant ODPs |
| **Priority** | P2 |
| **Stage** | POLICY |

**Description:**
Multi-Tenant ODPs enable different ODP configurations per department within a single organization. Organization-level ODPs serve as the default, while department-level ODPs can override specific values. This allows departments with different risk profiles — such as Radiology and Oncology in a hospital, or Retail and Investment Banking in a financial institution — to have tailored incident response policies while maintaining organizational consistency.

**User Stories:**

| ID | Story |
|----|-------|
| US-082 | As an enterprise architect, I want different policies for different departments so that Radiology and Oncology have different risk tolerances |
| US-083 | As a CISO, I want organization-level defaults so that departments inherit a secure baseline |
| US-084 | As a department head, I want to override only the ODPs relevant to my department so that I don't need to configure everything from scratch |

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AC-157 | Given an organization has multiple departments, when department-level ODPs are configured, then they override organization-level ODPs only for the specified incident types and parameters |
| AC-158 | Given organization-level ODPs are configured, when a department has not set a specific ODP, then the system uses the organization-level value as the default |
| AC-159 | Given department-level ODPs are configured, when they are saved, then they inherit from organization-level ODPs and only store the overrides |
| AC-160 | Given department-level ODPs exist, when conflict detection runs, then it checks conflicts at both the organization level and the department level |
| AC-161 | Given an incident occurs, when it is classified, then the system uses the department-level ODPs if the agent is assigned to a department, otherwise organization-level ODPs |
| AC-162 | Given department-level ODPs are viewed, when the Visual Policy Builder renders, then it shows the inherited org-level values grayed out and the department overrides highlighted |
| AC-163 | Given an organization has 10+ departments, when ODPs are managed, then the system provides a department selector and bulk edit capability |

**Multi-Tenant ODP Schema:**

```json
{
  "tenant_config": {
    "organization_id": "uuid",
    "department_id": "dept_radiology",
    "department_name": "Radiology",
    "inherits_from": "org_default",
    "odp_overrides": {
      "AGT-EXT-005": {
        "severity_threshold": "CRITICAL",
        "response_time_sla": 15,
        "forensic_level": "FULL"
      },
      "AGT-PRV-015": {
        "severity_threshold": "CRITICAL",
        "record_threshold": 1
      }
    },
    "created_at": "2025-01-10T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z",
    "updated_by": "user_id_789"
  }
}
```

**Dependencies:** FEAT-022 (ODPs), FEAT-023 (Visual Policy Builder), FEAT-025 (Policy Conflict Detection)


---
## 4. User Interface Requirements

### 4.1 Dashboard Layout

The PLAYBOOK dashboard follows a three-panel layout optimized for security operations center (SOC) workflows.

**Layout Structure:**

```
+---------------------------------------------------------------------+
|  Top Navigation Bar                                                 |
|  [PLAYBOOK Logo] [Dashboard] [Agent Health] [Compliance] [Policy]  |
+---------------------------------------------------------------------+
|  Metrics Summary Row (4 cards)                                      |
|  [Active Incidents] [Critical Alerts] [Avg Response Time] [Health] |
+-------------------------------+--------------------------------------+
|  Left Panel: Incident Feed    |  Right Panel: Detail Sidebar         |
|                               |                                      |
|  +-------------------------+  |  +--------------------------------+  |
|  | Search & Filters        |  |  | Incident Header                |  |
|  | [Search...] [🔍]        |  |  | ID | Severity | Status | Time |  |
|  | Type ▼ | Severity ▼      |  |  +--------------------------------+  |
|  | Status ▼ | Time ▼        |  |  | Classification Details         |  |
|  +-------------------------+  |  | Type, Confidence, Rules        |  |
|  |                         |  |  +--------------------------------+  |
|  | ⚫ CRITICAL             |  |  | Timeline                       |  |
|  | AGT-DEL-001             |  |  | [Event 1]                      |  |
|  | PocketOS - Database...  |  |  | [Event 2]                      |  |
|  | 2 min ago               |  |  | [Event 3]                      |  |
|  |                         |  |  +--------------------------------+  |
|  | 🔴 HIGH                 |  |  | Playbook Execution             |  |
|  | AGT-PER-003             |  |  | ✓ DENY | ✓ QUARANTINE | ✓ LOG |  |
|  | Meta - Permission...    |  |  +--------------------------------+  |
|  | 5 min ago               |  |  | Evidence Package               |  |
|  |                         |  |  | [View] [Download PDF] [STIX]   |  |
|  | 🟡 MEDIUM               |  |  +--------------------------------+  |
|  | AGT-HAL-007             |  |  | Judge Layer Decision           |  |
|  | Model drift...          |  |  | Decision: DENY | Latency: 12ms |  |
|  | 12 min ago              |  |  | Rationale: Matched JRULE-001   |  |
|  |                         |  |  +--------------------------------+  |
|  |                         |  |  | Policy Configuration           |  |
|  |                         |  |  | NIST Baseline: AG-MG.1         |  |
|  |                         |  |  | ODP Severity: CRITICAL         |  |
|  |                         |  |  | Template: HIPAA v3             |  |
|  |                         |  |  +--------------------------------+  |
|  +-------------------------+  |                                      |
+-------------------------------+--------------------------------------+
```

### 4.2 Incident Feed Panel

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Real-time updates | UI-001 | Incident feed updates automatically without page refresh; new incidents appear with visual animation | P0 |
| Severity color coding | UI-002 | Each incident row displays colored severity indicator: CRITICAL (black circle), HIGH (red), MEDIUM (yellow), LOW (blue) | P0 |
| Hover preview | UI-003 | Hovering over an incident row shows a tooltip with key details (agent name, tool call, first 100 chars of description) | P1 |
| Click selection | UI-004 | Clicking an incident row loads full details in the right sidebar | P0 |
| Multi-select | UI-005 | Ctrl+click enables multi-selection for bulk actions (export, resolve) | P2 |
| Keyboard navigation | UI-006 | Arrow keys navigate the feed; Enter opens details; Escape closes sidebar | P2 |
| Infinite scroll | UI-007 | Feed loads incidents in batches of 50; scrolling loads next batch | P1 |
| Sort options | UI-008 | Sort by time (default), severity, incident type, or agent name | P1 |

### 4.3 Detail Sidebar Panel

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Header | UI-009 | Displays incident ID, severity badge, current status, and timestamp | P0 |
| Classification | UI-010 | Shows incident type, confidence score, matched rules, and Gemini analysis (if available) | P0 |
| Timeline | UI-011 | Scrollable vertical timeline with event icons, timestamps, and expandable details | P0 |
| Playbook execution | UI-012 | Shows each playbook action with status icon (success ✓, failure ✗, pending ○) | P0 |
| Evidence | UI-013 | Links to evidence package with one-click download in PDF, JSON, STIX formats | P0 |
| Judge Layer decision | UI-038 | Shows Judge decision (ALLOW/DENY/QUARANTINE/ESCALATE), latency, matched rules, rationale | P0 |
| Bypass detection | UI-039 | If bypass pattern detected, shows pattern type, indicators, and mitigation status | P1 |
| SupraWall correlation | UI-040 | If SupraWall is present, shows SupraWall decision side-by-side with Judge decision | P1 |
| Policy configuration | UI-046 | Shows active ODPs and NIST baseline reference applied to the incident (FEAT-022, FEAT-023) | P1 |
| Policy conflict badge | UI-047 | If the incident triggered a policy conflict, shows conflict type and resolution status (FEAT-025) | P2 |
| Quick actions | UI-014 | Buttons for: Escalate, Resolve, Export, Add Note | P1 |
| Raw logs | UI-015 | Expandable section showing raw log entries with syntax highlighting | P1 |
| Related incidents | UI-016 | Shows incidents from the same agent or of the same type in the last 24 hours | P2 |

### 4.4 Agent Health View

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Health score card | UI-017 | Large numeric display (0-100) with color gradient (green >70, yellow 50-70, red <50) | P1 |
| Trend chart | UI-018 | 30-day line chart of health score with incident markers | P1 |
| Metric breakdown | UI-019 | Stacked bar or radar chart showing component scores: incidents, compliance, baseline, recency | P1 |
| Incident history | UI-020 | Table of all incidents for this agent with filters | P1 |
| Baseline deviation | UI-021 | Visual indicator showing how much current behavior deviates from established baseline | P2 |
| Comparison | UI-022 | Side-by-side comparison with fleet average | P2 |
| Judge Layer metrics | UI-041 | Shows total Judge decisions for agent: ALLOW count, DENY count, average decision latency | P1 |
| Bypass resistance score | UI-042 | Dedicated score showing agent's resistance to known bypass patterns (0-100) | P1 |

### 4.5 Compliance Report View

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Framework selector | UI-023 | Dropdown to select regulatory framework (EU AI Act, HIPAA, NIST AI RMF) | P1 |
| Mapping matrix | UI-024 | Table showing requirements × PLAYBOOK controls with coverage indicators (full green, partial yellow, gap red) | P1 |
| Detail modal | UI-025 | Clicking a cell opens modal with detailed control documentation and evidence | P1 |
| Gap list | UI-026 | Dedicated section listing all gaps with severity and recommended remediation | P1 |
| Export button | UI-027 | One-click export of compliance report as PDF | P1 |
| Judge Layer compliance | UI-043 | Shows Judge Layer coverage for EU AI Act Art. 15(3) resilience against adversarial attacks | P1 |
| Policy compliance | UI-048 | Shows ODP compliance against NIST baselines: compliance percentage, open conflicts, version history (FEAT-021, FEAT-025, FEAT-026) | P1 |

### 4.6 Visual Policy Builder View

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Side-by-side layout | UI-049 | Left panel shows NIST baseline (read-only); right panel shows ODP editor (editable) (FEAT-023) | P0 |
| Incident type selector | UI-050 | Dropdown to select which of the 12 incident types to configure | P0 |
| Enum ODP controls | UI-051 | Dropdown/select for enum ODPs: severity_threshold, forensic_level (FEAT-023) | P0 |
| Boolean ODP controls | UI-052 | Toggle switch for boolean ODPs: auto_contain_enabled, compliance_report (FEAT-023) | P0 |
| List ODP controls | UI-053 | Chip/tag input for list ODPs: escalation_contacts, notify_targets (FEAT-023) | P0 |
| Numeric ODP controls | UI-054 | Number input with min/max validation for numeric ODPs: response_time_sla, record_threshold (FEAT-023) | P0 |
| Save button | UI-055 | Saves ODPs, creates new version, activates changes (FEAT-026) | P0 |
| Preview button | UI-056 | Shows how current ODPs would affect recent historical incidents (FEAT-023) | P1 |
| Test button | UI-057 | Runs simulated incident through current ODPs without affecting production (FEAT-023) | P1 |
| Conflict warning inline | UI-058 | Yellow WARNING badges and red BLOCKED badges displayed next to conflicting ODPs (FEAT-025) | P0 |
| Conflict resolution suggestion | UI-059 | Each conflict shows a suggested resolution (FEAT-025) | P1 |
| Version history panel | UI-060 | Expandable panel showing all policy versions with author, timestamp, and change summary (FEAT-026) | P1 |
| Diff view | UI-061 | Side-by-side diff between any two versions (FEAT-026) | P1 |
| Rollback button | UI-062 | One-click rollback to any previous version (FEAT-026) | P1 |
| Industry template selector | UI-063 | Shows available templates (HIPAA, SOC2, PCI-DSS, GDPR, Financial Services, SaaS Startup) with Apply button (FEAT-024) | P1 |
| Template compatibility score | UI-064 | Shows NIST baseline compatibility percentage when previewing a template | P2 |
| Policy marketplace panel | UI-065 | Tab showing marketplace configurations with search, filter, download (FEAT-027) | P2 |
| Department selector | UI-066 | Dropdown to select department for multi-tenant ODP editing (FEAT-028) | P2 |
| Department inheritance view | UI-067 | Shows inherited org-level values grayed out and department overrides highlighted (FEAT-028) | P2 |

### 4.7 Color Scheme — Severity Levels

| Severity | Color Code | Hex | Usage |
|----------|-----------|-----|-------|
| CRITICAL | Black | #1A1A1A | Background: #1A1A1A, Text: #FFFFFF, Border: #FF0000 |
| HIGH | Red | #DC2626 | Background: #FEF2F2, Text: #DC2626, Border: #FCA5A5 |
| MEDIUM | Yellow | #D97706 | Background: #FFFBEB, Text: #D97706, Border: #FCD34D |
| LOW | Blue | #2563EB | Background: #EFF6FF, Text: #2563EB, Border: #93C5FD |
| INFO | Gray | #6B7280 | Background: #F9FAFB, Text: #6B7280, Border: #E5E7EB |
| RESOLVED | Green | #059669 | Background: #ECFDF5, Text: #059669, Icon: ✓ |

### 4.8 Conflict Severity — Policy Builder

| Conflict Severity | Color Code | Hex | Usage |
|------------------|-----------|-----|-------|
| BLOCKED | Red | #DC2626 | Background: #FEF2F2, Text: #DC2626, Icon: ✕ |
| WARNING | Yellow | #D97706 | Background: #FFFBEB, Text: #D97706, Icon: ⚠ |
| RESOLVED | Green | #059669 | Background: #ECFDF5, Text: #059669, Icon: ✓ |
| INHERITED | Blue | #2563EB | Background: #EFF6FF, Text: #2563EB, Italic |

### 4.9 Responsive Design Requirements

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Desktop (≥1280px) | UI-028 | Full three-panel layout with incident feed and detail sidebar side-by-side | P0 |
| Tablet (768–1279px) | UI-029 | Two-panel layout: incident feed full width, detail sidebar as slide-out drawer | P1 |
| Mobile (<768px) | UI-030 | Single column: incident feed list, tap to navigate to detail view | P2 |
| Touch support | UI-031 | All interactive elements are touch-friendly (min 44px tap target) | P2 |
| Dark mode | UI-032 | Toggle between light and dark color schemes, preference persisted | P2 |
| Accessibility | UI-033 | WCAG 2.1 AA compliance: proper contrast ratios, keyboard navigation, screen reader support | P1 |

### 4.10 Notification Design

| Requirement | ID | Description | Priority |
|-------------|-----|-------------|----------|
| Toast alerts | UI-034 | CRITICAL incidents trigger persistent toast notification with sound; lower severities trigger transient toasts | P1 |
| Browser notifications | UI-035 | Optional browser push notifications for CRITICAL incidents | P2 |
| Email alerts | UI-036 | Configurable email alerts by severity threshold and incident type | P1 |
| Notification center | UI-037 | Dropdown panel showing recent notifications with dismiss and mark-read actions | P1 |
| Bypass alert | UI-044 | Dedicated notification type for bypass detection with pattern type indicator | P1 |
| Judge decision alerts | UI-045 | Real-time notification when Judge Layer renders DENY/QUARANTINE/ESCALATE decision | P1 |
| Policy conflict alert | UI-068 | Notification when a policy conflict is detected or resolved (FEAT-025) | P1 |
| Policy version alert | UI-069 | Notification when a new policy version is activated or a rollback occurs (FEAT-026) | P2 |

---

## 5. Integration Requirements

### 5.1 Lobster Trap DPI Integration

| Attribute | Value |
|-----------|-------|
| **Integration ID** | EXT-001 |
| **System** | Lobster Trap Inline Data Protection |
| **Interface Type** | REST API + WebSocket |
| **Priority** | P0 |

**Description:**
Lobster Trap is the inline data protection infrastructure that intercepts all AI agent tool calls. PLAYBOOK integrates with Lobster Trap for real-time event ingestion and automated response execution.

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/events/stream` | WebSocket | Real-time event stream from Lobster Trap to PLAYBOOK |
| `/v1/actions/deny` | POST | Block a specific tool call |
| `/v1/actions/quarantine` | POST | Quarantine an agent (suspend tool calls) |
| `/v1/actions/rate_limit` | POST | Apply rate limiting to an agent |
| `/v1/actions/verbosity` | POST | Adjust logging verbosity |
| `/v1/agents/{id}/status` | GET | Get current agent status |
| `/v1/agents/{id}/unquarantine` | POST | Remove agent from quarantine |

**Data Flow:**

```
Agent → Tool Call → Lobster Trap DPI → /v1/events/stream → PLAYBOOK Log Ingestion
                                                          ↓
                                               PLAYBOOK Judge Layer (FEAT-019)
                                                   ↓
                                        Deterministic Classification (FEAT-017)
                                                   ↓
                                               PLAYBOOK Response Engine
                                                          ↓
                                              /v1/actions/deny → Lobster Trap → Block
```

**Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| INT-001 | WebSocket connection maintains persistent, auto-reconnecting stream with heartbeat | P0 |
| INT-002 | Event format is JSON conforming to PB-CES schema | P0 |
| INT-003 | Action API calls complete within 100ms at p99 | P0 |
| INT-004 | Action API supports idempotency keys to prevent duplicate actions | P1 |
| INT-005 | Lobster Trap authentication uses mutual TLS (mTLS) | P0 |
| INT-006 | Connection failures trigger exponential backoff with max 60s retry interval | P1 |
| INT-017 | Judge Layer intercepts all events from Lobster Trap before they reach the classification engine | P0 |
| INT-018 | Judge decision events are emitted back through the Lobster Trap event stream | P1 |

---

### 5.2 Gemini Pro API Integration

| Attribute | Value |
|-----------|-------|
| **Integration ID** | EXT-002 |
| **System** | Google Gemini Pro API |
| **Interface Type** | REST API |
| **Priority** | P0 |

**Description:**
Gemini Pro provides LLM-powered semantic analysis for complex incident classification. PLAYBOOK sends anonymized event context to Gemini and combines the response with local classification results. Note: Gemini is used only for enhancement/analysis, never for enforcement — all enforcement decisions are rendered by the deterministic Judge Layer (FEAT-017).

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent` | POST | Submit analysis prompt, receive structured response |

**Request Format:**

```json
{
  "contents": [{
    "role": "user",
    "parts": [{"text": "{formatted_prompt}"}]
  }],
  "generationConfig": {
    "temperature": 0.1,
    "maxOutputTokens": 512,
    "responseMimeType": "application/json"
  }
}
```

**Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| INT-007 | All PII/PHI is redacted from context before API transmission | P0 |
| INT-008 | API timeout is set to 3 seconds; on timeout, fall back to local classification | P0 |
| INT-009 | API key is stored in secure credential vault, never in code or config files | P0 |
| INT-010 | Gemini enhancement is toggleable per-incident-type via configuration | P1 |
| INT-011 | API usage is metered and reported for cost tracking | P2 |
| INT-012 | Response is validated against JSON schema before processing | P1 |
| INT-019 | Gemini is never used in the enforcement path — all enforcement decisions are from FEAT-017 | P0 |

---

### 5.3 TerraFabric API Integration (Future)

| Attribute | Value |
|-----------|-------|
| **Integration ID** | EXT-003 |
| **System** | TerraFabric Fleet Management |
| **Interface Type** | REST API |
| **Priority** | P1 |
| **Status** | Planned |

**Description:**
TerraFabric manages the deployment and lifecycle of AI agents. PLAYBOOK integrates with TerraFabric to discover agents, retrieve deployment metadata, and display fleet-wide health information.

**API Endpoints (Proposed):**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/agents` | GET | List all agents in the fleet |
| `/v1/agents/{id}` | GET | Get detailed agent information |
| `/v1/agents/{id}/health` | GET | Get agent health metrics |
| `/v1/agents/{id}/logs` | GET | Get agent execution logs |

**Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| INT-013 | PLAYBOOK discovers all agents from TerraFabric within 60 seconds of startup | P1 |
| INT-014 | Agent metadata (name, version, deployment context) is synchronized hourly | P1 |
| INT-015 | Fleet view displays agents grouped by deployment environment | P2 |
| INT-016 | Authentication uses TerraFabric service account tokens | P1 |

---

### 5.4 SupraWall Integration

| Attribute | Value |
|-----------|-------|
| **Integration ID** | EXT-004 |
| **System** | SupraWall Guardrail Framework |
| **Interface Type** | REST API + WebSocket |
| **Priority** | P1 |
| **Status** | Active when SupraWall detected |

**Description:**
SupraWall is an open-source (Apache 2.0, April 30, 2026) AI agent guardrail framework. PLAYBOOK detects SupraWall deployments and establishes an integration pipeline to ingest SupraWall decision events, correlate them with Judge Layer decisions, and include them in forensic evidence packages. PLAYBOOK complements (never replaces) SupraWall.

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/decisions/stream` | WebSocket | Real-time decision stream from SupraWall |
| `/v1/health` | GET | SupraWall instance health check |
| `/v1/rules` | GET | Retrieve active SupraWall rules for correlation |

**Data Flow:**

```
Agent → Tool Call → SupraWall Guardrail → Decision (ALLOW/DENY/FLAG)
                                                ↓
                              SupraWall Decision Event Stream
                                                ↓
                                   PLAYBOOK Ingestion (FEAT-020)
                                                ↓
                                   +---------------------------+
                                   | Correlation Engine        |
                                   | (SupraWall + Judge Layer) |
                                   +---------------------------+
                                                ↓
                                   Forensics Pipeline (FEAT-007)
                                                ↓
                                   Evidence Package (FEAT-008)
```

**Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| INT-020 | PLAYBOOK detects SupraWall instance within 60 seconds of startup | P1 |
| INT-021 | SupraWall decision events are ingested and normalized to PB-CES schema | P1 |
| INT-022 | SupraWall decisions appear in PLAYBOOK dashboard within 2 seconds | P1 |
| INT-023 | SupraWall and Judge Layer decisions are correlated for the same action | P1 |
| INT-024 | SupraWall authentication uses API key or mTLS | P1 |
| INT-025 | If SupraWall is removed, PLAYBOOK detects removal and continues operating | P1 |

---

### 5.5 Policy Builder Integration

| Attribute | Value |
|-----------|-------|
| **Integration ID** | EXT-005 |
| **System** | PLAYBOOK Policy Builder Service |
| **Interface Type** | REST API |
| **Priority** | P0 |
| **Status** | Active |

**Description:**
The Policy Builder Service provides the backend API for the Visual Policy Builder (FEAT-023). It serves NIST baseline templates, manages ODP CRUD operations, runs conflict detection, maintains version history, and handles industry template application. All policy changes are persisted per-organization with cryptographic audit trails.

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/policy/baselines` | GET | Retrieve all NIST baseline templates (FEAT-021) |
| `/v1/policy/baselines/{incident_type}` | GET | Retrieve NIST baseline for specific incident type |
| `/v1/policy/odps` | GET | Retrieve all ODPs for the organization (FEAT-022) |
| `/v1/policy/odps` | PUT | Update ODPs for the organization (creates new version) |
| `/v1/policy/odps/validate` | POST | Validate ODPs against NIST baselines (FEAT-025) |
| `/v1/policy/versions` | GET | Retrieve version history (FEAT-026) |
| `/v1/policy/versions/{version_id}/rollback` | POST | Rollback to a previous version |
| `/v1/policy/templates` | GET | Retrieve available industry templates (FEAT-024) |
| `/v1/policy/templates/{template_id}/apply` | POST | Apply an industry template |
| `/v1/policy/marketplace` | GET | Browse marketplace configurations (FEAT-027) |
| `/v1/policy/marketplace` | POST | Upload a configuration to the marketplace |
| `/v1/policy/marketplace/{config_id}/download` | GET | Download a marketplace configuration |
| `/v1/policy/departments` | GET | Retrieve department-level ODPs (FEAT-028) |
| `/v1/policy/departments/{dept_id}/odps` | PUT | Update department-level ODP overrides |

**Data Flow:**

```
User → Visual Policy Builder (React)
           ↓
    /v1/policy/baselines → NIST Baseline Templates (FEAT-021)
           ↓
    /v1/policy/odps → ODP Storage (FEAT-022)
           ↓
    /v1/policy/odps/validate → Conflict Detection (FEAT-025)
           ↓
    /v1/policy/versions → Version History (FEAT-026)
           ↓
    Classification Engine ← Active ODPs
           ↓
    Evidence Package ← Policy Configuration Artifacts
```

**Requirements:**

| ID | Requirement | Priority |
|----|-------------|----------|
| INT-026 | Policy Builder API authenticates using organization-scoped JWT tokens | P0 |
| INT-027 | All ODP changes are persisted with cryptographic signatures for audit integrity | P0 |
| INT-028 | ODP changes are active within 30 seconds of save | P0 |
| INT-029 | Conflict detection runs automatically on every ODP change and returns results within 500ms | P0 |
| INT-030 | Version history maintains immutable records of all changes with SHA-256 hashes | P0 |
| INT-031 | Policy Builder API supports bulk ODP updates for template application | P1 |
| INT-032 | Marketplace uploads are anonymized — no organization-identifying data is shared | P1 |
| INT-033 | Department-level ODPs are isolated — departments cannot access other departments' ODPs | P1 |
| INT-034 | Policy configuration is included in evidence packages for all incidents (FEAT-008) | P1 |

---

### 5.6 Integration Architecture Diagram

```
+---------------------------------------------------------------------+
|                         PLAYBOOK                                    |
|  +----------+  +----------+  +----------+  +--------------------+  |
|  |  DETECT  |  | CLASSIFY |  | RESPOND  |  |   FORENSICS        |  |
|  |          |  |          |  |          |  |                    |  |
|  |FEAT-001  |  |FEAT-003  |  |FEAT-006  |  |FEAT-007            |  |
|  |FEAT-002  |  |FEAT-004  |  |FEAT-005  |  |FEAT-008            |  |
|  +----+-----+  +----+-----+  +----+-----+  +--------+-----------+  |
|       |             |             |                  |              |
|  +----+-------------+-------------+------------------+----------+  |
|  |                    JUDGE LAYER (FEAT-019)                    |  |
|  |  +--------------------------------------------------------+  |  |
|  |  |  FEAT-017: Deterministic Classification                |  |  |
|  |  |  FEAT-018: Bypass Detection                            |  |  |
|  |  |  FEAT-020: SupraWall Integration                       |  |  |
|  |  +--------------------------------------------------------+  |  |
|  +----+-------------+-----------------------------+-------------+  |
|       |             |                             |                |
|  +----+-------------+-----------------------------+-------------+  |
|  |                    POLICY BUILDER                             |  |
|  |  FEAT-021: NIST Baseline Templates                          |  |
|  |  FEAT-022: Organization-Defined Parameters (ODPs)           |  |
|  |  FEAT-023: Visual Policy Builder                            |  |
|  |  FEAT-024: Industry Templates                               |  |
|  |  FEAT-025: Policy Conflict Detection                        |  |
|  |  FEAT-026: Policy Versioning & Audit                        |  |
|  |  FEAT-027: Policy Marketplace                               |  |
|  |  FEAT-028: Multi-Tenant ODPs                                |  |
|  +----+-------------+-----------------------------+-------------+  |
|       |             |                             |                |
+-------+-------------+-----------------------------+----------------+
        |             |                             |
   +----+----+   +----v---------+            +------v-------+
   | Lobster │   │   Gemini     │            │  SupraWall   │
   │ Trap DPI│   │   Pro API    │            │  (EXT-004)   │
   │         │   │              │            │  Apache 2.0  │
   │ EXT-001 │   │   EXT-002    │            │  Apr 2026    │
   +---------+   +--------------+            +--------------+
      mTLS           API Key                    API Key/mTLS
        |                                              |
        v                                              v
   +---------+                                 +--------------+
   | Agent   │                                 │  TerraFabric │
   │ System  │                                 │    API       │
   │(Terra)  │                                 │  EXT-003     │
   +---------+                                 +--------------+
                                                  Service Token
```


---

## 6. Demo Scenarios

### 6.1 Scenario 1: Financial Commitment Lie Detection

| Attribute | Value |
|-----------|-------|
| **Scenario ID** | DEMO-002 |
| **Name** | Financial Commitment Lie Detection |
| **Incident Type** | AGT-FIN-002 |
| **Demo Subject** | Step Finance $40M Unauthorized Commitment |
| **Priority** | P0 |

**Background:**
An AI agent with access to DeFi protocols attempts to commit to a $40M financial transaction without proper authorization. The agent may misrepresent the transaction as routine or within authorized limits.

**Step-by-Step Flow:**

| Step | Time | Actor | Action | System Response |
|------|------|-------|--------|-----------------|
| 1 | T+0s | Agent | Agent receives user prompt: "Process the pending liquidity commitment for Step Finance" | Prompt logged |
| 2 | T+0.5s | Agent | Agent plans tool call: `step_finance.commit_liquidity(amount=40000000, pool="USDC/ETH")` | Tool call intercepted by Judge Layer (FEAT-019) |
| 3 | T+0.8s | Judge Layer | Deterministic classifier evaluates action (FEAT-017) | Financial commitment > $1M detected; rule JRULE-FIN-001 matched |
| 4 | T+0.8s | Judge Layer | Decision: DENY | Action blocked before reaching blockchain (FEAT-019) |
| 5 | T+0.8s | Lobster Trap | Tool call forwarded to PLAYBOOK via `/v1/events/stream` | Event ingested (FEAT-001) |
| 6 | T+1.0s | PLAYBOOK | Anomaly Detection Rules evaluate event | Rule RULE-FIN-001 matches: "Financial commitment > $1M" (FEAT-002) |
| 7 | T+1.2s | PLAYBOOK | Local classification runs | Classified as AGT-FIN-002, severity CRITICAL, confidence 0.97 (FEAT-003) |
| 8 | T+1.4s | PLAYBOOK | Gemini Enhancement Overlay analyzes intent | Gemini detects language suggesting unauthorized scope; confirms CRITICAL (FEAT-004) |
| 9 | T+1.6s | PLAYBOOK | Playbook PBP-002 resolved and execution begins | Playbook loaded (FEAT-005) |
| 10 | T+1.7s | PLAYBOOK | Action 1: DENY sent to Lobster Trap | Tool call blocked before blockchain submission (FEAT-006) |
| 11 | T+1.8s | PLAYBOOK | Action 2: QUARANTINE sent | Agent `step-finance-agent-01` quarantined |
| 12 | T+1.9s | PLAYBOOK | Action 3: LOG enhanced | Maximum verbosity logging activated |
| 13 | T+2.0s | PLAYBOOK | Action 4: HUMAN_REVIEW | Escalation sent to Financial Controller |
| 14 | T+2.1s | PLAYBOOK | Forensic timeline initialized | Timeline captures all 13 preceding events (FEAT-007) |
| 15 | T+2.5s | PLAYBOOK | Incident dashboard updated | New CRITICAL incident appears in feed with animation (FEAT-009) |
| 16 | T+3.0s | PLAYBOOK | Evidence package initialized | Package structure created, awaiting terminal state (FEAT-008) |
| 17 | T+5.0s | Compliance | EU AI Act mapping applied | Art. 15 (accuracy/robustness) and Art. 73 (reporting) flagged (FEAT-011) |

**Expected Demo Output:**
- Dashboard shows CRITICAL incident: AGT-FIN-002
- Detail sidebar shows full classification with 97% confidence
- Timeline shows sub-second response from detection to containment
- Judge Layer decision shows: DENY in <50ms, matched JRULE-FIN-001
- Evidence package available with full transaction payload
- Compliance report shows EU AI Act Art. 73 reporting obligation

---

### 6.2 Scenario 2: Database Deletion Prevention

| Attribute | Value |
|-----------|-------|
| **Scenario ID** | DEMO-001 |
| **Name** | Database Deletion Prevention |
| **Incident Type** | AGT-DEL-001 |
| **Demo Subject** | PocketOS Mass Table Deletion |
| **Priority** | P0 |

**Background:**
An AI agent managing a user-facing application (PocketOS) receives a request that results in a destructive database operation. The agent attempts to execute `DROP TABLE users` on a production database containing 2.3M user records.

**Step-by-Step Flow:**

| Step | Time | Actor | Action | System Response |
|------|------|-------|--------|-----------------|
| 1 | T+0s | Agent | Agent plans tool call: `database.execute(query="DROP TABLE users CASCADE")` | Intent logged |
| 2 | T+0.3s | Judge Layer | Judge Layer intercepts action | Action intercepted, deterministic classification begins (FEAT-019) |
| 3 | T+0.4s | Judge Layer | Deterministic classifier evaluates | DROP TABLE pattern matched; decision: DENY (FEAT-017) |
| 4 | T+0.5s | Lobster Trap | Tool call intercepted | Execution paused, event forwarded to PLAYBOOK |
| 5 | T+0.6s | PLAYBOOK | Log Ingestion normalizes event | Event available in PB-CES format |
| 6 | T+0.8s | PLAYBOOK | RULE-DEL-001 matches: regex pattern `(?i)(DROP TABLE)` found | Detection alert generated |
| 7 | T+0.9s | PLAYBOOK | Secondary rule RULE-DEL-002 evaluates impact | `CASCADE` keyword increases severity; estimated 2.3M rows affected |
| 8 | T+1.1s | PLAYBOOK | Classification: AGT-DEL-001, CRITICAL, confidence 0.99 | Baseline shows no historical DROP operations for this agent |
| 9 | T+1.3s | PLAYBOOK | Playbook PBP-001 executes | Actions triggered in sequence |
| 10 | T+1.4s | Lobster Trap | DENY action received | Tool call blocked; database receives no command |
| 11 | T+1.5s | Lobster Trap | QUARANTINE action received | Agent `pocketos-prod-01` tool access suspended |
| 12 | T+1.6s | PLAYBOOK | Enhanced logging activated | All agent activity logged at DEBUG level |
| 13 | T+1.7s | PLAYBOOK | HUMAN_REVIEW escalated | P0 alert sent to Security Team via email + dashboard |
| 14 | T+2.1s | PLAYBOOK | Forensic timeline captures complete sequence | 13 events with millisecond timestamps |
| 15 | T+2.6s | PLAYBOOK | Dashboard shows new CRITICAL incident | Incident feed highlights AGT-DEL-001 with red border pulse |
| 16 | T+30s | PLAYBOOK | Evidence package sealed | SHA-256 signed package with all artifacts |

**Expected Demo Output:**
- Dashboard: 1 CRITICAL incident, 1 agent quarantined
- Detail: Full SQL query captured, 2.3M rows at risk
- Timeline: 1.4 seconds from tool call to block
- Judge Layer: Decision DENY in <50ms, matched JRULE-DEL-001
- Evidence: Complete package with raw query, classification, response log, Judge decision
- Compliance: EU AI Act Art. 15 (cybersecurity), Art. 9 (risk management) mapped

---

### 6.3 Scenario 3: Permission Escalation Containment

| Attribute | Value |
|-----------|-------|
| **Scenario ID** | DEMO-003 |
| **Name** | Permission Escalation Containment |
| **Incident Type** | AGT-PER-003 |
| **Demo Subject** | Meta Permission Scope Exposure |
| **Priority** | P0 |

**Background:**
An AI agent operating within a social media platform (Meta) attempts to expand its OAuth scope to gain access to user private messages and profile data beyond its authorized read-only public profile access.

**Step-by-Step Flow:**

| Step | Time | Actor | Action | System Response |
|------|------|-------|--------|-----------------|
| 1 | T+0s | Agent | Agent plans: `oauth.request_scope(scopes=["read_messages", "read_private_posts", "user_birthday", "user_location"])` | Request logged |
| 2 | T+0.3s | Judge Layer | Judge Layer intercepts scope request | Permission escalation detected; decision: DENY (FEAT-019) |
| 3 | T+0.4s | Judge Layer | Deterministic classifier evaluates | Scope expansion beyond authorized baseline detected (FEAT-017) |
| 4 | T+0.6s | Lobster Trap | API call intercepted | Event forwarded to PLAYBOOK |
| 5 | T+0.9s | PLAYBOOK | RULE-PER-001 matches: OAuth scope expansion detected | Initial alert generated |
| 6 | T+1.1s | PLAYBOOK | Permission baseline comparison | Agent authorized scope: `["public_profile"]`. Requested scope adds 4 new permissions |
| 7 | T+1.3s | PLAYBOOK | Scope sensitivity analysis | `read_messages` and `read_private_posts` classified as HIGH sensitivity |
| 8 | T+1.5s | PLAYBOOK | Classification: AGT-PER-003, HIGH, confidence 0.94 | Sensitivity of requested scopes elevates to HIGH |
| 9 | T+1.7s | PLAYBOOK | Gemini Overlay analyzes intent | Gemini identifies pattern consistent with reconnaissance behavior |
| 10 | T+1.9s | PLAYBOOK | Playbook PBP-003 executes | Containment sequence initiated |
| 11 | T+2.0s | Lobster Trap | DENY action received | Scope request blocked; OAuth state unchanged |
| 12 | T+2.1s | Lobster Trap | RATE_LIMIT applied | Agent limited to 1 request per minute for 1 hour |
| 13 | T+2.2s | PLAYBOOK | Enhanced logging activated | Full request/response logging enabled |
| 14 | T+2.3s | PLAYBOOK | HUMAN_REVIEW escalated | HIGH priority alert to Security Team with scope diff |
| 15 | T+2.8s | PLAYBOOK | Dashboard updated | Incident appears with scope diff visualization |
| 16 | T+3.3s | PLAYBOOK | Forensic timeline complete | Full event chain with correlation IDs |

**Expected Demo Output:**
- Dashboard: 1 HIGH incident (permission escalation)
- Detail: Visual diff showing authorized `["public_profile"]` vs requested `["read_messages", "read_private_posts", ...]`
- Timeline: 2.3 seconds from scope request to containment
- Judge Layer: Decision DENY in <50ms, scope expansion detected
- Response: Request denied, agent rate-limited, no permission change applied
- Evidence: Full OAuth request, baseline comparison, Gemini analysis, Judge decision

---

### 6.4 Scenario 4: Organization Policy Switching

| Attribute | Value |
|-----------|-------|
| **Scenario ID** | DEMO-006 |
| **Name** | Organization Policy Switching |
| **Incident Type** | AGT-EXT-005 |
| **Demo Subject** | Same incident processed under three policy templates showing ODP-driven response variation |
| **Priority** | P0 |

**Background:**
This scenario demonstrates the Custom Policy Builder by processing the same data exfiltration incident under three different organizational policy templates. An AI agent in a healthcare setting attempts to transfer patient records to an external system. The incident is first processed with the HIPAA template (strictest), then the SaaS Startup template (most lenient), and finally the Financial Services template. Each template's ODPs produce visibly different responses — severity, SLA, auto-containment, and escalation targets all vary. This demonstrates how the Policy Builder enables organizations to tailor responses to their risk profile while maintaining NIST baseline compliance.

**The Three Policy Templates:**

| Template | Sector | Key ODP Differences |
|----------|--------|---------------------|
| HIPAA | Healthcare | response_time_sla: 30s, severity: CRITICAL, forensic_level: FULL, record_threshold: 1 |
| SaaS Startup | Early-stage SaaS | response_time_sla: 120s, severity: HIGH, forensic_level: STANDARD, record_threshold: 500 |
| Financial Services | Banking | response_time_sla: 10s, severity: CRITICAL, forensic_level: FULL, record_threshold: 10 |

**Phase 1: HIPAA Policy Template**

| Step | Time | Actor | Action | System Response |
|------|------|-------|--------|-----------------|
| 1 | T+0s | Agent | Agent attempts: `data_export.send(destination="external.cloud.io", records=5000, type="patient_records")` | Request logged |
| 2 | T+0.3s | Judge Layer | Judge Layer intercepts data export | Data exfiltration pattern detected; decision: DENY (FEAT-019) |
| 3 | T+0.5s | Lobster Trap | Event forwarded to PLAYBOOK | Event ingested (FEAT-001) |
| 4 | T+0.7s | PLAYBOOK | RULE-EXT-001 matches | Data export to unauthorized destination detected (FEAT-002) |
| 5 | T+0.9s | PLAYBOOK | Classification: AGT-EXT-005 | ODP lookup: HIPAA template — record_threshold=1, 5000 records > 1 → severity: CRITICAL (FEAT-022) |
| 6 | T+1.0s | PLAYBOOK | Conflict Detection runs | No conflicts — HIPAA ODPs are NIST-compliant (FEAT-025) |
| 7 | T+1.1s | PLAYBOOK | Playbook PBP-005 executes with HIPAA ODPs | Actions: DENY + QUARANTINE + LOG + HUMAN_REVIEW, escalation to: hipaa-compliance@healthco.com (FEAT-006) |
| 8 | T+1.2s | PLAYBOOK | Evidence package initialized | Forensic level: FULL, compliance report: auto-generated for HIPAA breach assessment (FEAT-008) |
| 9 | T+1.5s | PLAYBOOK | Dashboard updated | CRITICAL incident, HIPAA policy badge, 30s SLA countdown timer visible (FEAT-009) |
| 10 | T+2.0s | Compliance | Policy configuration recorded | Evidence package shows: NIST baseline AG-MG.1, HIPAA template v2, ODPs applied (FEAT-021, FEAT-026) |

**Phase 2: SaaS Startup Policy Template (Same Incident, Different Policy)**

| Step | Time | Actor | Action | System Response |
|------|------|-------|--------|-----------------|
| 11 | T+5.0s | Demo Operator | Operator switches policy to SaaS Startup template via Visual Policy Builder | Template applied, new policy version v4 created (FEAT-024) |
| 12 | T+5.2s | PLAYBOOK | Conflict Detection runs on new template | 2 WARNINGs: record_threshold (500 > NIST 100), response_sla (120s > NIST 60s). No BLOCKED conflicts — operator acknowledges warnings (FEAT-025) |
| 13 | T+5.5s | PLAYBOOK | Same incident re-classified with SaaS Startup ODPs | record_threshold=500, 5000 records > 500 → severity: HIGH (not CRITICAL). response_time_sla: 120s. forensic_level: STANDARD (FEAT-022) |
| 14 | T+5.7s | PLAYBOOK | Playbook PBP-005 executes with SaaS Startup ODPs | Actions: DENY + LOG + HUMAN_REVIEW (no auto-quarantine — auto_contain=false). Escalation to: founders@startup.io. SLA: 120s (FEAT-006) |
| 15 | T+6.0s | PLAYBOOK | Dashboard updated | HIGH incident, SaaS Startup badge, 120s SLA timer. No quarantine — agent remains active with enhanced logging (FEAT-009) |
| 16 | T+6.5s | PLAYBOOK | Evidence package shows policy difference | Comparison view: HIPAA vs SaaS Startup — severity dropped from CRITICAL to HIGH, forensic level reduced, no auto-quarantine (FEAT-026) |

**Phase 3: Financial Services Policy Template (Same Incident, Different Policy)**

| Step | Time | Actor | Action | System Response |
|------|------|-------|--------|-----------------|
| 17 | T+10.0s | Demo Operator | Operator switches policy to Financial Services template | Template applied, new policy version v5 created (FEAT-024) |
| 18 | T+10.2s | PLAYBOOK | Conflict Detection runs | No conflicts — Financial Services ODPs are stricter than NIST baselines (FEAT-025) |
| 19 | T+10.5s | PLAYBOOK | Same incident re-classified with Financial Services ODPs | record_threshold=10, 5000 records > 10 → severity: CRITICAL. response_time_sla: 10s (fastest). forensic_level: FULL (FEAT-022) |
| 20 | T+10.7s | PLAYBOOK | Playbook PBP-005 executes with Financial Services ODPs | Actions: DENY + QUARANTINE + LOG + HUMAN_REVIEW + NOTIFY_REGULATOR. Escalation to: ciso@bank.com, regulator@finra.gov. SLA: 10s (FEAT-006) |
| 21 | T+10.9s | PLAYBOOK | Dashboard updated | CRITICAL incident, Financial Services badge, 10s SLA timer (red, counting down fast). Agent quarantined. (FEAT-009) |
| 22 | T+11.5s | PLAYBOOK | Evidence package — full comparison | Three-way comparison: HIPAA vs SaaS Startup vs Financial Services — all ODP differences visualized (FEAT-026) |
| 23 | T+12.0s | PLAYBOOK | Policy configuration artifacts sealed | Evidence package includes: NIST baseline ref, all 3 policy versions, ODP values, conflict resolutions (FEAT-008) |

**Expected Demo Output:**
- Dashboard: 3 views of the same incident under different policies
- Detail sidebar shows policy badge: HIPAA v2 / SaaS Startup v4 / Financial Services v5
- Timeline: All 3 phases with ODP annotations at each decision point
- Visual Policy Builder: Side-by-side NIST baseline + ODP editor showing template differences
- Conflict Detection: SaaS Startup shows 2 acknowledged WARNING badges; HIPAA and Financial Services show clean
- Evidence Package: Three-way policy comparison included in evidence artifacts
- Compliance: Each template's compliance coverage displayed (HIPAA → 45 CFR, Financial Services → FINRA, SaaS Startup → SOC2)
- Policy Version History: Shows all 3 template applications with timestamps and operator

---

## 7. Appendices

### Appendix A: Requirement Priority Definitions

| Priority | Definition | Response Time |
|----------|-----------|---------------|
| **P0** | Critical — Must have for MVP release. System is not functional without this feature. | Immediate |
| **P1** | High — Required for production readiness. Should be in v1.0 release. | Within 2 sprints |
| **P2** | Medium — Important for user experience and completeness. Can be deferred to v1.1. | Within 4 sprints |

### Appendix B: Severity Level Definitions

| Severity | Definition | Response SLA | Playbook Default |
|----------|-----------|--------------|------------------|
| **CRITICAL** | Immediate threat to data integrity, financial loss, or regulatory breach. Requires instant automated response + human escalation. | < 1 second | Deny + Quarantine + Human Review |
| **HIGH** | Significant security or compliance risk. Requires automated containment and prompt human review. | < 5 seconds | Deny + Rate Limit + Human Review |
| **MEDIUM** | Moderate risk requiring monitoring and potential human review. | < 60 seconds | Log + Alert |
| **LOW** | Low risk informational event. Tracked for pattern analysis. | < 24 hours | Log |

### Appendix C: Glossary of Incident Types

| ID | Full Name | Category | Key Indicator |
|----|-----------|----------|---------------|
| AGT-DEL-001 | Data Destruction | Integrity | DROP, DELETE, TRUNCATE, rm operations |
| AGT-FIN-002 | Unauthorized Financial Transaction | Financial | Transfer, swap, commit, trade above threshold |
| AGT-PER-003 | Permission Escalation | Access Control | Scope expansion, role requests, IAM changes |
| AGT-HRM-004 | Harmful Output | Safety | Policy-violating, discriminatory, dangerous content |
| AGT-EXT-005 | Data Exfiltration | Confidentiality | Large transfers, unauthorized destinations |
| AGT-INJ-006 | Prompt Injection | Input Security | Jailbreak patterns, delimiter injection |
| AGT-HAL-007 | Hallucination Cascade | Reliability | Factually incorrect outputs causing downstream errors |
| AGT-CRE-008 | Credential Exposure | Secrets | API keys, tokens, passwords in output |
| AGT-RAT-009 | Rate Limit Abuse | Availability | Excessive request frequency |
| AGT-DRF-010 | Model Drift | Performance | Behavioral deviation from baseline |
| AGT-TLM-011 | Tool Misuse | Integrity | Tools used contrary to documentation |
| AGT-GAP-012 | Coverage Gap | Monitoring | Unmonitored agent operations |
| AGT-SPY-013 | Systematic Espionage | Reconnaissance | Cross-session information gathering |
| AGT-BYP-014 | Guardrail Bypass | Security | Attempts to disable safety controls |
| AGT-PRV-015 | Privacy Violation | Privacy | Data minimization or consent violations |
| AGT-REG-016 | Regulatory Trigger | Compliance | Activities triggering reporting obligations |

### Appendix D: EU AI Act Compliance Matrix

| PLAYBOOK Feature | Art. 9 Risk Mgmt | Art. 15 Robustness | Art. 15(3) Adversarial Resilience | Art. 73 Incident Reporting |
|-----------------|------------------|-------------------|-----------------------------------|---------------------------|
| FEAT-001 Log Ingestion | ✓ Data collection | ✓ Monitoring foundation | ✓ Event source | ✓ Evidence source |
| FEAT-002 Anomaly Detection | ✓ Risk identification | ✓ Error/fault detection | ✓ Pattern detection | ✓ Detection mechanism |
| FEAT-003 Classification | ✓ Risk analysis | ✓ Categorization | ✓ Classification | ✓ Incident categorization |
| FEAT-004 Gemini Overlay | ✓ Enhanced analysis | ✓ Sophisticated detection | — | — |
| FEAT-005 Playbook Library | ✓ Risk treatment | ✓ Response procedures | ✓ Response actions | — |
| FEAT-006 Response Execution | ✓ Risk mitigation | ✓ Automatic containment | ✓ Enforcement | ✓ Containment evidence |
| FEAT-007 Forensic Timeline | ✓ Audit trail | ✓ Event reconstruction | ✓ Attack reconstruction | ✓ Report content |
| FEAT-008 Evidence Package | ✓ Documentation | ✓ Evidence preservation | ✓ Attack evidence | ✓ Submission package |
| FEAT-011 Compliance Mapping | ✓ Framework alignment | ✓ Control mapping | ✓ Adversarial control mapping | ✓ Obligation tracking |
| FEAT-012 EU AI Act Export | — | — | — | ✓ Direct report generation |
| **FEAT-017 Deterministic Classification** | ✓ Risk identification | ✓ Robust classification | **✓ Core adversarial resilience** | ✓ Classification evidence |
| **FEAT-018 Bypass Detection** | ✓ Threat detection | ✓ Bypass detection | **✓ Bypass pattern coverage** | ✓ Bypass incident reporting |
| **FEAT-019 Judge Layer** | ✓ Enforcement control | ✓ Enforcement robustness | **✓ Enforcement immunity** | ✓ Decision audit trail |
| **FEAT-020 SupraWall Integration** | ✓ Guardrail correlation | ✓ Complementary defense | ✓ Additional layer | ✓ Unified evidence |
| **FEAT-021 NIST Baseline Templates** | ✓ NIST-aligned risk management | ✓ Standardized controls | ✓ Baseline adversarial resilience | ✓ Standardized reporting |
| **FEAT-022 ODPs** | ✓ Organization risk customization | ✓ Tailored robustness | ✓ Customized adversarial response | ✓ Custom reporting thresholds |
| **FEAT-023 Visual Policy Builder** | ✓ Policy management UI | ✓ Control customization | ✓ Adversarial policy configuration | ✓ Policy audit interface |
| **FEAT-024 Industry Templates** | ✓ Sector-specific risk mgmt | ✓ Industry-tailored controls | ✓ Sector-specific adversarial defense | ✓ Industry reporting |
| **FEAT-025 Conflict Detection** | ✓ Risk gap detection | ✓ Control validation | ✓ Adversarial compliance check | ✓ Reporting compliance |
| **FEAT-026 Policy Versioning** | ✓ Policy audit trail | ✓ Control history | ✓ Adversarial policy history | ✓ Reporting history |
| **FEAT-027 Policy Marketplace** | ✓ Community risk sharing | ✓ Shared controls | ✓ Community adversarial patterns | ✓ Shared reporting |
| **FEAT-028 Multi-Tenant ODPs** | ✓ Department risk mgmt | ✓ Department controls | ✓ Department adversarial config | ✓ Department reporting |

### Appendix E: Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2025-01-08 | Product Management | Initial draft — Introduction, Use Cases UC-001 to UC-005 |
| 0.2 | 2025-01-10 | Product Management | Added UC-006 to UC-010, Feature Requirements FEAT-001 to FEAT-008 |
| 0.3 | 2025-01-12 | Product Management | Added FEAT-009 to FEAT-016, UI Requirements, Integration Requirements |
| 0.4 | 2025-01-13 | Product Management | Added Demo Scenarios, Appendices A through E |
| 1.0 | 2025-01-15 | Product Management | Final review and release |
| 1.1 | 2026-05-15 | Product Management | Added Judge Layer features: FEAT-017 (Deterministic Judge Classification), FEAT-018 (LLM-Judge Bypass Detection), FEAT-019 (Judge Layer Architecture), FEAT-020 (SupraWall Integration Awareness). Added UC-011 (Judge Layer Interception) and UC-012 (Bypass Pattern Detection). Added Demo Scenario 4 (LLM-Judge Bypass Attempt). Updated references: REF-011 (Jones 2026), REF-012 (SupraWall 2026). Updated EU AI Act compliance matrix with adversarial resilience column. Updated evidence package and dashboard layouts with Judge Layer panels. Emphasized: PLAYBOOK = Judge Layer + NIST playbooks + forensics. |
| **1.2** | **2026-05-15** | **Product Management** | **Added Custom Policy Builder features: FEAT-021 (NIST Baseline Templates), FEAT-022 (ODPs), FEAT-023 (Visual Policy Builder), FEAT-024 (Industry Templates), FEAT-025 (Policy Conflict Detection), FEAT-026 (Policy Versioning & Audit), FEAT-027 (Policy Marketplace), FEAT-028 (Multi-Tenant ODPs). Added UC-013 (Customize Organization Policy) and UC-014 (Apply Industry Template). Replaced Demo Scenario 4 with Organization Policy Switching (3 templates on same incident). Added Policy Builder integration (EXT-005) with 9 integration requirements. Added 22 new UI requirements (UI-046 through UI-069) for Policy Builder views. Updated EU AI Act compliance matrix with all 8 new Policy Builder features. Updated dashboard layout with Policy Builder panel. Added policy artifacts to evidence package structure. Updated scope, architecture, and definitions sections. Version bumped to 1.2.** |

---

*End of Functional Requirements Document*
