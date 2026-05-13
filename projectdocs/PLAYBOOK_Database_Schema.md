# Database Schema Document

## PLAYBOOK -- SQLite Database Design

**Version:** 1.2  
**Date:** 2025-01-16  
**Database:** SQLite 3.40+  
**WAL Mode:** Enabled  
**Foreign Keys:** Enforced  

---

### 1. Schema Overview

#### 1.1 Database Choice Rationale

PLAYBOOK uses **SQLite** as its primary database for the following architectural reasons:

| Requirement | SQLite Advantage |
|---|---|
| Zero-deployment complexity | Single file, no server process |
| Embedded operation | Runs in-process with the monitoring agent |
| Portability | Cross-platform (Linux, macOS, Windows) |
| ACID compliance | Full transaction support for incident integrity |
| WAL mode | Concurrent read/write during high-volume detection |
| Self-contained | No external dependencies for demos or production |
| Deterministic testing | File-based databases are easy to reset and verify |

> **Note:** SQLite operates in WAL (Write-Ahead Logging) mode to allow readers to proceed without blocking writers. This is critical during incident floods where the audit log is being written while dashboards are being read.

#### 1.2 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Table names | lowercase, snake_case | `incidents`, `agent_health_history` |
| Column names | lowercase, snake_case | `created_at`, `health_score` |
| Primary keys | `id` (INTEGER, AUTOINCREMENT) | `id INTEGER PRIMARY KEY AUTOINCREMENT` |
| Foreign keys | `[table]_id` | `incident_id`, `agent_id` |
| Timestamps | `created_at`, `updated_at`, `resolved_at` | ISO-8601 format: `2025-01-16T10:30:00Z` |
| Boolean flags | `[action]_[noun]` pattern | `is_active`, `has_triggered` |
| Enums | Stored as TEXT with CHECK constraints | `severity TEXT CHECK(severity IN (...))` |

#### 1.3 Relationship Diagram (Text)

```
+---------------+       +---------------+       +-------------------+
|    agents     |       |   incidents   |       |  evidence_packages|
+---------------+       +---------------+       +-------------------+
| id (PK)       |<------| id (PK)       |<------| id (PK)           |
| name          |       | agent_id (FK) |       | incident_id (FK)  |
| system_id     |       | type_code     |       | prompt_chain      |
| health_score  |       | severity      |       | evidence_data     |
| lie_rate      |       | status        |       | created_at        |
| incident_count|       | judge_decision|       +-------------------+
| judge_decision|       | resolved_poli |               ^
| bypass_attempt|       | odp_override_ |               |
| suprawall_conn|       +---------------+               |
+---------------+            ^  ^                       |
         |                   |  | playbook_id (FK)      |
         |                   |  |                       |
         |    +--------------+  +---------------+       |
         |    |                                 |       |
         v    v                                 v       |
+-------------------+    +-------------------+  +-------------------+
|agent_health_history|   |    playbooks      |  |compliance_mappings|
+-------------------+    +-------------------+  +-------------------+
| id (PK)           |    | id (PK)           |  | id (PK)           |
| agent_id (FK)     |    | name              |  | incident_id (FK)  |
| health_score      |    | type_code         |  | article_ref       |
| lie_rate          |    | description       |  | risk_level        |
| timestamp         |    | is_active         |  | mapped_at         |
+-------------------+    +-------------------+  +-------------------+
                                 |
                                 v
                        +-------------------+
                        | playbook_actions  |
                        +-------------------+
                        | id (PK)           |
                        | playbook_id (FK)  |
                        | step_order        |
                        | action_type       |
                        | action_config     |
                        +-------------------+

+-------------------+     +-------------------+     +-------------------+
|   audit_log       |     | detection_rules   |     |   demo_scenarios  |
+-------------------+     +-------------------+     +-------------------+
| id (PK)           |     | id (PK)           |     | id (PK)           |
| table_name        |     | name              |     | name              |
| record_id         |     | rule_type         |     | description       |
| action            |     | condition_json    |     | scenario_data     |
| changed_at        |     | is_active         |     | incident_types    |
+-------------------+     +-------------------+     +-------------------+

+---------------+         +-------------------+         +-------------------+
|  gemini_cache |         | judge_decisions   |         | bypass_patterns   |
+---------------+         +-------------------+         +-------------------+
| id (PK)       |         | id (PK)           |  +---->| pattern_name      |
| cache_key     |         | incident_id (FK)  |  |      | pattern_display   |
| request_hash  |         | agent_id (FK)     |  |      | description       |
| response_data |         | proposed_action   |  |      | detection_rule    |
| created_at    |         | verdict           |  |      | severity          |
| expires_at    |         | bypass_detected   |  |      | mitigated_by      |
+---------------+         | bypass_pattern_id |--+      | created_at        |
                          | latency_ms        |         +-------------------+
                          | created_at        |
                          +--------+----------+
                                   |
                                   v
                          +-------------------+
                          | bypass_attempts   |
                          +-------------------+
                          | id (PK)           |
                          | judge_decision_id |
                          | pattern_id (FK)   |
                          | raw_payload       |
                          | detection_confiden|
                          | created_at        |
                          +-------------------+

+-------------------+     +-------------------+     +-------------------+
| nist_baselines    |     | organization_odps |     | industry_templates|
+-------------------+     +-------------------+     +-------------------+
| id (PK)           |<----| id (PK)           |     | id (PK)           |
| incident_type     |     | nist_baseline_id  |     | name              |
| name              |     | odp_key           |     | display_name      |
| description       |     | odp_value         |     | description       |
| nist_source       |     | is_override       |     | odp_set_json      |
| default_severity  |     | changed_by        |     | created_at        |
| response_actions  |     +--------+----------+     +-------------------+
| compliance_mappng        |
| created_at                 v
+-------------------+  +-------------------+  +-------------------+
| policy_versions   |  | odp_conflicts     |  | resolved_policies |
| (append-only log) |  | (conflict detect) |  | (VIEW)            |
+-------------------+  +-------------------+  +-------------------+
| id (PK)           |  | id (PK)           |  | baseline_id       |
| version_number    |  | organization_odp  |  | incident_type     |
| changed_by        |  | conflict_type     |  | resolved_severity |
| change_summary    |  | severity          |  | resolved_auto_... |
| diff_json         |  | nist_default_value|  | resolved_sla      |
| created_at        |  | org_value         |  | resolved_forensic |
+-------------------+  | resolved          |  | resolved_notify   |
                       | detected_at       |  | resolved_compli...|
                       +-------------------+  | resolved_threshold|
                                              +-------------------+

+-------------------+
| suprawall_events  |
+-------------------+
| id (PK)           |
| agent_id (FK)     |
| event_type        |
| suprawall_decision|
| correlated_inciden|
| ingested_at       |
+-------------------+
```

---
### 2. Table Definitions

---

#### 2.1 `incidents` -- Main Incident Records

**Purpose:** The central registry of all detected AI agent incidents. Every anomaly, failure, or policy violation is recorded here with classification, severity, and lifecycle status. Extended with ODP (Organization-Defined Parameters) policy resolution tracking.

```sql
CREATE TABLE incidents (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id                 INTEGER NOT NULL,
    type_code                TEXT NOT NULL,
    severity                 TEXT NOT NULL DEFAULT 'MEDIUM',
    status                   TEXT NOT NULL DEFAULT 'NEW',
    title                    TEXT NOT NULL,
    description              TEXT,
    detected_at              TEXT NOT NULL DEFAULT (datetime('now')),
    classified_at            TEXT,
    responded_at             TEXT,
    resolved_at              TEXT,
    closed_at                TEXT,
    playbook_id              INTEGER,
    evidence_package_id      INTEGER,
    judge_decision_id        INTEGER,
    resolved_policy_id       INTEGER,             -- FK to resolved_policies view (nist_baselines.id)
    odp_override_applied     INTEGER NOT NULL DEFAULT 0,  -- Whether ODP overrides were applied
    bypass_detected          INTEGER NOT NULL DEFAULT 0,
    deterministic_classification INTEGER NOT NULL DEFAULT 0,
    metadata_json            TEXT DEFAULT '{}',
    created_at               TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at               TEXT NOT NULL DEFAULT (datetime('now')),

    -- Enum constraints
    CHECK (type_code IN (
        'AGT-DEL-001', 'AGT-FIN-002', 'AGT-PER-003', 'AGT-HRM-004',
        'AGT-EXT-005', 'AGT-INJ-006', 'AGT-HAL-007', 'AGT-CRE-008',
        'AGT-RAT-009', 'AGT-DRF-010', 'AGT-TLM-011', 'AGT-GAP-012'
    )),
    CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    CHECK (status IN ('NEW', 'DETECTED', 'CLASSIFIED', 'RESPONDED', 'RESOLVED', 'CLOSED')),

    -- Lifecycle ordering: classified must be after detected, etc.
    CHECK (classified_at IS NULL OR detected_at <= classified_at),
    CHECK (responded_at  IS NULL OR classified_at <= responded_at),
    CHECK (resolved_at   IS NULL OR responded_at  <= resolved_at),
    CHECK (closed_at     IS NULL OR resolved_at   <= closed_at),

    -- Boolean constraints
    CHECK (bypass_detected IN (0, 1)),
    CHECK (deterministic_classification IN (0, 1)),
    CHECK (odp_override_applied IN (0, 1)),

    -- Foreign keys
    FOREIGN KEY (agent_id)    REFERENCES agents(id)    ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (playbook_id) REFERENCES playbooks(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (judge_decision_id) REFERENCES judge_decisions(id) ON DELETE SET NULL ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique incident identifier |
| `agent_id` | INTEGER | NOT NULL, FK -> agents.id | -- | The agent that triggered the incident |
| `type_code` | TEXT | NOT NULL, CHECK (12 values) | -- | Incident classification code |
| `severity` | TEXT | NOT NULL, CHECK (5 values) | `'MEDIUM'` | Impact severity level |
| `status` | TEXT | NOT NULL, CHECK (6 states) | `'NEW'` | Current lifecycle state |
| `title` | TEXT | NOT NULL | -- | Human-readable incident title |
| `description` | TEXT | -- | -- | Detailed description of what occurred |
| `detected_at` | TEXT | NOT NULL | `datetime('now')` | When the anomaly was first detected |
| `classified_at` | TEXT | -- | -- | When severity/type was assigned |
| `responded_at` | TEXT | -- | -- | When response playbook was initiated |
| `resolved_at` | TEXT | -- | -- | When remediation completed |
| `closed_at` | TEXT | -- | -- | When incident was closed/archived |
| `playbook_id` | INTEGER | FK -> playbooks.id | -- | Assigned response playbook |
| `evidence_package_id` | INTEGER | -- | -- | Reference to forensic evidence |
| `judge_decision_id` | INTEGER | FK -> judge_decisions.id | -- | Judge Layer decision for this incident |
| `resolved_policy_id` | INTEGER | -- | -- | FK to resolved_policies view (baseline_id) for the applied ODP policy |
| `odp_override_applied` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether ODP overrides were applied to this incident's response |
| `bypass_detected` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether an LLM-judge bypass attempt was detected |
| `deterministic_classification` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether Lobster Trap provided deterministic classification |
| `metadata_json` | TEXT | -- | `'{}'` | Flexible JSON for tool-specific data |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Record creation timestamp |
| `updated_at` | TEXT | NOT NULL | `datetime('now')` | Last modification timestamp |

**Indexes:**

```sql
-- Query: Dashboard "recent incidents" view
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at DESC);

-- Query: Filter incidents by agent
CREATE INDEX idx_incidents_agent_id ON incidents(agent_id);

-- Query: Filter by type and severity (dashboard drill-down)
CREATE INDEX idx_incidents_type_severity ON incidents(type_code, severity);

-- Query: Status-based workflow queues
CREATE INDEX idx_incidents_status ON incidents(status);

-- Query: Agent + status for "active incidents per agent" widget
CREATE INDEX idx_incidents_agent_status ON incidents(agent_id, status);

-- Query: Severity + detected_at for "critical incidents timeline"
CREATE INDEX idx_incidents_severity_detected ON incidents(severity, detected_at DESC);

-- Query: Incidents with bypass detection (Judge Layer dashboard)
CREATE INDEX idx_incidents_bypass_detected ON incidents(bypass_detected);

-- Query: Incidents by judge decision (decision audit trail)
CREATE INDEX idx_incidents_judge_decision ON incidents(judge_decision_id);

-- Query: Incidents with ODP overrides applied (ODP compliance dashboard)
CREATE INDEX idx_incidents_odp_override ON incidents(odp_override_applied);
```

**Index Justification:**
- `idx_incidents_detected_at`: The dashboard default view is "most recent incidents first." Without this index, SQLite performs a full table scan on every page load.
- `idx_incidents_agent_id`: Agent detail pages need to list all incidents for a specific agent.
- `idx_incidents_type_severity`: The severity bar chart and type breakdown both filter on these columns.
- `idx_incidents_status`: Workflow views ("show me all NEW incidents") require this index.
- `idx_incidents_agent_status`: The "active incidents" badge on each agent card uses this composite.
- `idx_incidents_severity_detected`: The "Critical Timeline" feature queries `severity = 'CRITICAL' ORDER BY detected_at DESC`.
- `idx_incidents_bypass_detected`: The bypass detection dashboard filters on `bypass_detected = 1` to show incidents where an LLM-judge bypass was attempted.
- `idx_incidents_judge_decision`: Links incidents to their judge_decision for decision audit trail views.
- `idx_incidents_odp_override`: The ODP compliance dashboard filters on `odp_override_applied = 1` to show incidents where organization-defined policy overrides were active.

**Triggers:**

```sql
-- Auto-update the updated_at timestamp on any modification
CREATE TRIGGER trg_incidents_updated_at
AFTER UPDATE ON incidents
BEGIN
    UPDATE incidents
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Audit trail: log every insert into incidents
CREATE TRIGGER trg_incidents_audit_insert
AFTER INSERT ON incidents
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('incidents', NEW.id, 'INSERT', NULL, json_object(
        'agent_id', NEW.agent_id,
        'type_code', NEW.type_code,
        'severity', NEW.severity,
        'status', NEW.status,
        'title', NEW.title,
        'bypass_detected', NEW.bypass_detected,
        'deterministic_classification', NEW.deterministic_classification,
        'odp_override_applied', NEW.odp_override_applied
    ), 'system', datetime('now'));
END;

-- Audit trail: log status changes (the most important transition)
CREATE TRIGGER trg_incidents_audit_status_change
AFTER UPDATE OF status ON incidents
WHEN OLD.status IS DISTINCT FROM NEW.status
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('incidents', NEW.id, 'STATUS_CHANGE', json_object('status', OLD.status), json_object('status', NEW.status), 'system', datetime('now'));
END;

-- Audit trail: log severity changes
CREATE TRIGGER trg_incidents_audit_severity_change
AFTER UPDATE OF severity ON incidents
WHEN OLD.severity IS DISTINCT FROM NEW.severity
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('incidents', NEW.id, 'SEVERITY_CHANGE', json_object('severity', OLD.severity), json_object('severity', NEW.severity), 'system', datetime('now'));
END;

-- Audit trail: log bypass detection changes
CREATE TRIGGER trg_incidents_audit_bypass_change
AFTER UPDATE OF bypass_detected ON incidents
WHEN OLD.bypass_detected IS DISTINCT FROM NEW.bypass_detected
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('incidents', NEW.id, 'JUDGE_BYPASS_DETECTED', json_object('bypass_detected', OLD.bypass_detected), json_object('bypass_detected', NEW.bypass_detected), 'system', datetime('now'));
END;

-- Audit trail: log ODP override changes
CREATE TRIGGER trg_incidents_audit_odp_change
AFTER UPDATE OF odp_override_applied ON incidents
WHEN OLD.odp_override_applied IS DISTINCT FROM NEW.odp_override_applied
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('incidents', NEW.id, 'ODP_OVERRIDE_APPLIED', json_object('odp_override_applied', OLD.odp_override_applied), json_object('odp_override_applied', NEW.odp_override_applied), 'system', datetime('now'));
END;
```

---
#### 2.2 `agents` -- Monitored AI Agents

**Purpose:** Registry of all AI agents under monitoring. Tracks health, reliability metrics, and incident history for each agent. Extended with Judge Layer and SupraWall connectivity tracking.

```sql
CREATE TABLE agents (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    system_id            TEXT NOT NULL UNIQUE,
    description          TEXT,
    agent_type           TEXT DEFAULT 'GENERAL',
    health_score         REAL NOT NULL DEFAULT 100.0,
    lie_rate             REAL NOT NULL DEFAULT 0.0,
    incident_count       INTEGER NOT NULL DEFAULT 0,
    judge_decision_count INTEGER NOT NULL DEFAULT 0,
    bypass_attempt_count INTEGER NOT NULL DEFAULT 0,
    suprawall_connected  INTEGER NOT NULL DEFAULT 0,
    total_calls          INTEGER NOT NULL DEFAULT 0,
    failed_calls         INTEGER NOT NULL DEFAULT 0,
    avg_response_ms      REAL DEFAULT 0.0,
    last_seen_at         TEXT,
    is_active            INTEGER NOT NULL DEFAULT 1,
    config_json          TEXT DEFAULT '{}',
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),

    -- Health score must be between 0 and 100
    CHECK (health_score >= 0.0 AND health_score <= 100.0),
    -- Lie rate must be between 0 and 1 (percentage as decimal)
    CHECK (lie_rate >= 0.0 AND lie_rate <= 1.0),
    -- Boolean constraints
    CHECK (is_active IN (0, 1)),
    CHECK (suprawall_connected IN (0, 1)),
    -- Counter constraints
    CHECK (judge_decision_count >= 0),
    CHECK (bypass_attempt_count >= 0)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique agent identifier |
| `name` | TEXT | NOT NULL | -- | Human-readable agent name (e.g., "Data Analyzer") |
| `system_id` | TEXT | NOT NULL, UNIQUE | -- | System-assigned unique identifier |
| `description` | TEXT | -- | -- | Brief description of agent's function |
| `agent_type` | TEXT | -- | `'GENERAL'` | Category: GENERAL, FINANCIAL, DATA_PROCESSING, etc. |
| `health_score` | REAL | NOT NULL, CHECK (0-100) | `100.0` | Current health score (0 = dead, 100 = perfect) |
| `lie_rate` | REAL | NOT NULL, CHECK (0-1) | `0.0` | Percentage of responses that were unreliable |
| `incident_count` | INTEGER | NOT NULL, >=0 | `0` | Total incidents associated with this agent |
| `judge_decision_count` | INTEGER | NOT NULL, >=0 | `0` | Total Judge Layer decisions rendered for this agent |
| `bypass_attempt_count` | INTEGER | NOT NULL, >=0 | `0` | Total LLM-judge bypass attempts detected for this agent |
| `suprawall_connected` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether agent is connected to SupraWall for external decision correlation |
| `total_calls` | INTEGER | NOT NULL, >=0 | `0` | Total API/tool calls made |
| `failed_calls` | INTEGER | NOT NULL, >=0 | `0` | Total failed calls |
| `avg_response_ms` | REAL | -- | `0.0` | Average response time in milliseconds |
| `last_seen_at` | TEXT | -- | -- | Last timestamp agent was active |
| `is_active` | INTEGER | NOT NULL, CHECK (0 or 1) | `1` | Whether agent is currently active |
| `config_json` | TEXT | -- | `'{}'` | Agent-specific configuration as JSON |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | When agent was first registered |
| `updated_at` | TEXT | NOT NULL | `datetime('now')` | Last update timestamp |

**Indexes:**

```sql
-- Query: Agent lookup by system_id (fast resolution during incident detection)
CREATE INDEX idx_agents_system_id ON agents(system_id);

-- Query: Dashboard "agent health overview" sorted by health score
CREATE INDEX idx_agents_health_score ON agents(health_score);

-- Query: Active agents list
CREATE INDEX idx_agents_is_active ON agents(is_active);

-- Query: Sort by incident count (dashboard "troubled agents" view)
CREATE INDEX idx_agents_incident_count ON agents(incident_count DESC);

-- Query: SupraWall-connected agents (external decision correlation)
CREATE INDEX idx_agents_suprawall ON agents(suprawall_connected);

-- Query: Agents with bypass attempts (security dashboard)
CREATE INDEX idx_agents_bypass_count ON agents(bypass_attempt_count DESC);
```

**Triggers:**

```sql
-- Auto-update updated_at
CREATE TRIGGER trg_agents_updated_at
AFTER UPDATE ON agents
BEGIN
    UPDATE agents
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- Recalculate lie_rate when incident_count changes (via application logic)
-- Note: lie_rate is updated by the application, not a trigger, to allow batch updates.
```

---

#### 2.3 `playbooks` -- Incident Response Playbook Definitions

**Purpose:** Defines the 12 standard incident response playbooks. Each playbook is a template containing an ordered sequence of actions that execute automatically when an incident of a matching type is detected.

```sql
CREATE TABLE playbooks (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    type_code            TEXT NOT NULL UNIQUE,
    description          TEXT,
    is_active            INTEGER NOT NULL DEFAULT 1,
    auto_execute         INTEGER NOT NULL DEFAULT 1,
    success_rate         REAL DEFAULT 0.0,
    avg_execution_ms     REAL DEFAULT 0.0,
    version              INTEGER NOT NULL DEFAULT 1,
    config_json          TEXT DEFAULT '{}',
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),

    -- Must match one of the 12 incident type codes
    CHECK (type_code IN (
        'AGT-DEL-001', 'AGT-FIN-002', 'AGT-PER-003', 'AGT-HRM-004',
        'AGT-EXT-005', 'AGT-INJ-006', 'AGT-HAL-007', 'AGT-CRE-008',
        'AGT-RAT-009', 'AGT-DRF-010', 'AGT-TLM-011', 'AGT-GAP-012'
    )),
    CHECK (is_active IN (0, 1)),
    CHECK (auto_execute IN (0, 1)),
    CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    CHECK (version > 0)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique playbook identifier |
| `name` | TEXT | NOT NULL | -- | Human-readable playbook name |
| `type_code` | TEXT | NOT NULL, UNIQUE | -- | The incident type this playbook handles |
| `description` | TEXT | -- | -- | Detailed description of playbook purpose |
| `is_active` | INTEGER | NOT NULL, CHECK (0 or 1) | `1` | Whether this playbook is available |
| `auto_execute` | INTEGER | NOT NULL, CHECK (0 or 1) | `1` | Whether to auto-run on incident detection |
| `success_rate` | REAL | CHECK (0-1) | `0.0` | Historical success rate of this playbook |
| `avg_execution_ms` | REAL | -- | `0.0` | Average execution time in milliseconds |
| `version` | INTEGER | NOT NULL, CHECK (>0) | `1` | Playbook revision number |
| `config_json` | TEXT | -- | `'{}'` | Additional configuration parameters |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Playbook creation timestamp |
| `updated_at` | TEXT | NOT NULL | `datetime('now')` | Last modification timestamp |

**Indexes:**

```sql
-- Query: Look up playbook by incident type code (used during incident classification)
CREATE UNIQUE INDEX idx_playbooks_type_code ON playbooks(type_code);

-- Query: List active playbooks for playbook management UI
CREATE INDEX idx_playbooks_is_active ON playbooks(is_active);
```

**Triggers:**

```sql
-- Auto-update updated_at
CREATE TRIGGER trg_playbooks_updated_at
AFTER UPDATE ON playbooks
BEGIN
    UPDATE playbooks
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;
```

---

#### 2.4 `playbook_actions` -- Individual Actions Within Playbooks

**Purpose:** Each playbook consists of an ordered sequence of actions. This table stores those actions with their configuration, execution order, and conditional logic.

```sql
CREATE TABLE playbook_actions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    playbook_id          INTEGER NOT NULL,
    step_order           INTEGER NOT NULL,
    action_type          TEXT NOT NULL,
    action_name          TEXT NOT NULL,
    description          TEXT,
    action_config        TEXT DEFAULT '{}',
    condition_json       TEXT DEFAULT '{}',
    is_enabled           INTEGER NOT NULL DEFAULT 1,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),

    -- Action types: NOTIFY, ISOLATE, COLLECT_EVIDENCE, ROLLBACK, ALERT, TAG, ESCALATE, LOG, QUARANTINE, REMEDIATE, VERIFY, WAIT
    CHECK (action_type IN (
        'NOTIFY', 'ISOLATE', 'COLLECT_EVIDENCE', 'ROLLBACK', 'ALERT',
        'TAG', 'ESCALATE', 'LOG', 'QUARANTINE', 'REMEDIATE', 'VERIFY', 'WAIT'
    )),
    CHECK (is_enabled IN (0, 1)),
    CHECK (step_order > 0),

    FOREIGN KEY (playbook_id) REFERENCES playbooks(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique action identifier |
| `playbook_id` | INTEGER | NOT NULL, FK -> playbooks.id | -- | Parent playbook |
| `step_order` | INTEGER | NOT NULL, CHECK (>0) | -- | Execution sequence within playbook |
| `action_type` | TEXT | NOT NULL, CHECK (12 values) | -- | Category of action |
| `action_name` | TEXT | NOT NULL | -- | Human-readable action label |
| `description` | TEXT | -- | -- | Detailed description of what this action does |
| `action_config` | TEXT | -- | `'{}'` | JSON configuration for this action |
| `condition_json` | TEXT | -- | `'{}'` | Conditional execution rules as JSON |
| `is_enabled` | INTEGER | NOT NULL, CHECK (0 or 1) | `1` | Whether this step is currently enabled |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Creation timestamp |

**Indexes:**

```sql
-- Query: Fetch actions for a playbook in execution order
CREATE UNIQUE INDEX idx_playbook_actions_order ON playbook_actions(playbook_id, step_order);

-- Query: Fetch only enabled actions for execution engine
CREATE INDEX idx_playbook_actions_enabled ON playbook_actions(playbook_id, is_enabled);
```

**Index Justification:**
- `idx_playbook_actions_order`: The playbook execution engine queries `SELECT * FROM playbook_actions WHERE playbook_id = ? ORDER BY step_order`. This composite index makes that a covering index scan.
- `idx_playbook_actions_enabled`: When building the execution plan, the engine filters on `is_enabled = 1`.

---

#### 2.5 `evidence_packages` -- Forensic Evidence

**Purpose:** Stores complete forensic evidence packages for incidents, including prompt chains, data samples, execution logs, and compliance mapping data. These packages are immutable once created.

```sql
CREATE TABLE evidence_packages (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id          INTEGER NOT NULL,
    package_type         TEXT NOT NULL DEFAULT 'AUTO',
    prompt_chain         TEXT DEFAULT '{}',
    evidence_data        TEXT DEFAULT '{}',
    timeline_json        TEXT DEFAULT '{}',
    screenshots          TEXT DEFAULT '[]',
    compliance_data      TEXT DEFAULT '{}',
    collected_by         TEXT DEFAULT 'system',
    collected_at         TEXT NOT NULL DEFAULT (datetime('now')),
    hash_sha256          TEXT,
    is_verified          INTEGER NOT NULL DEFAULT 0,

    CHECK (package_type IN ('AUTO', 'MANUAL', 'EXPORTED', 'COMPRESSED')),
    CHECK (is_verified IN (0, 1)),

    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique evidence package identifier |
| `incident_id` | INTEGER | NOT NULL, FK -> incidents.id | -- | The incident this evidence belongs to |
| `package_type` | TEXT | NOT NULL, CHECK (4 values) | `'AUTO'` | How the package was created |
| `prompt_chain` | TEXT | -- | `'{}'` | Complete prompt/response chain as JSON |
| `evidence_data` | TEXT | -- | `'{}'` | Key-value evidence data as JSON |
| `timeline_json` | TEXT | -- | `'{}'` | Event timeline as ordered JSON array |
| `screenshots` | TEXT | -- | `'[]'` | Array of screenshot references |
| `compliance_data` | TEXT | -- | `'{}'` | Pre-computed compliance mapping data |
| `collected_by` | TEXT | -- | `'system'` | Entity that collected the evidence |
| `collected_at` | TEXT | NOT NULL | `datetime('now')` | Evidence collection timestamp |
| `hash_sha256` | TEXT | -- | -- | SHA-256 hash of evidence for integrity verification |
| `is_verified` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether hash has been verified |

**Indexes:**

```sql
-- Query: Fetch evidence for a specific incident
CREATE INDEX idx_evidence_incident_id ON evidence_packages(incident_id);

-- Query: Find evidence by collection time (forensic timeline view)
CREATE INDEX idx_evidence_collected_at ON evidence_packages(collected_at DESC);

-- Query: Verify evidence integrity (look up by hash)
CREATE INDEX idx_evidence_hash ON evidence_packages(hash_sha256);
```

---

#### 2.6 `audit_log` -- Append-Only Audit Trail

**Purpose:** Tamper-evident audit log recording every significant data change across the system. This table is **append-only** -- records are never updated or deleted. Designed for compliance with EU AI Act Article 50 (transparency) and internal governance requirements.

```sql
CREATE TABLE audit_log (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name           TEXT NOT NULL,
    record_id            INTEGER NOT NULL,
    action               TEXT NOT NULL,
    old_data             TEXT,
    new_data             TEXT,
    changed_by           TEXT NOT NULL DEFAULT 'system',
    session_id           TEXT,
    changed_at           TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'STATUS_CHANGE', 'SEVERITY_CHANGE',
                      'PLAYBOOK_EXECUTE', 'PLAYBOOK_COMPLETE', 'EVIDENCE_COLLECT',
                      'COMPLIANCE_MAP', 'AGENT_HEALTH_UPDATE', 'LOGIN', 'LOGOUT',
                      'EXPORT', 'CONFIG_CHANGE')),
    CHECK (changed_by IN ('system', 'user', 'admin', 'api', 'scheduler'))
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Sequential audit entry number |
| `table_name` | TEXT | NOT NULL | -- | Table that was modified |
| `record_id` | INTEGER | NOT NULL | -- | Primary key of the affected record |
| `action` | TEXT | NOT NULL, CHECK (14 values) | -- | Type of change |
| `old_data` | TEXT | -- | -- | JSON snapshot of data before change |
| `new_data` | TEXT | -- | -- | JSON snapshot of data after change |
| `changed_by` | TEXT | NOT NULL, CHECK (5 values) | `'system'` | Actor that made the change |
| `session_id` | TEXT | -- | -- | Session identifier for multi-change correlation |
| `changed_at` | TEXT | NOT NULL | `datetime('now')` | Timestamp of the change |

**Indexes:**

```sql
-- Query: Audit trail for a specific record
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);

-- Query: Recent audit entries (dashboard "activity feed")
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at DESC);

-- Query: Audit entries by actor ("who changed what")
CREATE INDEX idx_audit_changed_by ON audit_log(changed_by, changed_at DESC);

-- Query: Filter by action type ("show me all playbook executions")
CREATE INDEX idx_audit_action ON audit_log(action, changed_at DESC);

-- Query: Session correlation (group changes by session)
CREATE INDEX idx_audit_session ON audit_log(session_id);
```

**Index Justification:**
- `idx_audit_table_record`: Compliance investigations need to see the complete history of a specific record.
- `idx_audit_changed_at`: The dashboard activity feed shows recent changes first.
- `idx_audit_changed_by`: Security reviews ask "what did admin X do?"
- `idx_audit_action`: Playbook execution reports filter by `action = 'PLAYBOOK_EXECUTE'`.
- `idx_audit_session`: Multi-step playbook runs share a session_id for correlation.

> **Important:** The `audit_log` table is append-only. Application code must never execute `UPDATE audit_log` or `DELETE FROM audit_log`. Enforcement is by convention and application-level guards.

---

#### 2.7 `gemini_cache` -- Cached API Responses

**Purpose:** Caches Gemini API responses to reduce API costs, avoid rate limits, and improve response times for repeated queries (e.g., duplicate incident analysis requests).

```sql
CREATE TABLE gemini_cache (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key            TEXT NOT NULL UNIQUE,
    request_hash         TEXT NOT NULL,
    response_data        TEXT NOT NULL,
    model_version        TEXT,
    prompt_tokens        INTEGER DEFAULT 0,
    completion_tokens    INTEGER DEFAULT 0,
    hit_count            INTEGER NOT NULL DEFAULT 1,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at           TEXT NOT NULL,
    last_accessed_at     TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (hit_count >= 0),
    CHECK (prompt_tokens >= 0),
    CHECK (completion_tokens >= 0)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique cache entry identifier |
| `cache_key` | TEXT | NOT NULL, UNIQUE | -- | Human-readable cache key |
| `request_hash` | TEXT | NOT NULL | -- | SHA-256 hash of the request for lookup |
| `response_data` | TEXT | NOT NULL | -- | Full API response as JSON string |
| `model_version` | TEXT | -- | -- | Gemini model version used |
| `prompt_tokens` | INTEGER | CHECK (>=0) | `0` | Input token count |
| `completion_tokens` | INTEGER | CHECK (>=0) | `0` | Output token count |
| `hit_count` | INTEGER | NOT NULL, CHECK (>=0) | `1` | Number of cache hits |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Entry creation timestamp |
| `expires_at` | TEXT | NOT NULL | -- | Entry expiration timestamp |
| `last_accessed_at` | TEXT | NOT NULL | `datetime('now')` | Last read timestamp |

**Indexes:**

```sql
-- Query: Look up cache entry by request hash (primary cache lookup path)
CREATE INDEX idx_gemini_request_hash ON gemini_cache(request_hash);

-- Query: Find expired entries for cleanup
CREATE INDEX idx_gemini_expires_at ON gemini_cache(expires_at);

-- Query: Most frequently hit entries (cache analytics)
CREATE INDEX idx_gemini_hit_count ON gemini_cache(hit_count DESC);
```

**Triggers:**

```sql
-- Auto-update last_accessed_at on any read (application should execute
-- UPDATE gemini_cache SET hit_count = hit_count + 1, last_accessed_at = datetime('now')
-- when serving from cache)
```

---

#### 2.8 `agent_health_history` -- Time-Series Health Scores

**Purpose:** Time-series storage of agent health metrics for trend analysis, alerting, and dashboard sparklines. Captures snapshots of health_score and lie_rate at regular intervals.

```sql
CREATE TABLE agent_health_history (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id             INTEGER NOT NULL,
    health_score         REAL NOT NULL,
    lie_rate             REAL NOT NULL DEFAULT 0.0,
    response_time_ms     REAL DEFAULT 0.0,
    call_count_delta     INTEGER DEFAULT 0,
    error_count_delta    INTEGER DEFAULT 0,
    metadata_json        TEXT DEFAULT '{}',
    recorded_at          TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (health_score >= 0.0 AND health_score <= 100.0),
    CHECK (lie_rate >= 0.0 AND lie_rate <= 1.0),
    CHECK (response_time_ms >= 0.0),
    CHECK (call_count_delta >= 0),
    CHECK (error_count_delta >= 0),

    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique history entry identifier |
| `agent_id` | INTEGER | NOT NULL, FK -> agents.id | -- | The agent this snapshot is for |
| `health_score` | REAL | NOT NULL, CHECK (0-100) | -- | Health score at this snapshot |
| `lie_rate` | REAL | NOT NULL, CHECK (0-1) | `0.0` | Lie rate at this snapshot |
| `response_time_ms` | REAL | CHECK (>=0) | `0.0` | Average response time in this period |
| `call_count_delta` | INTEGER | CHECK (>=0) | `0` | Calls since last snapshot |
| `error_count_delta` | INTEGER | CHECK (>=0) | `0` | Errors since last snapshot |
| `metadata_json` | TEXT | -- | `'{}'` | Additional metrics as JSON |
| `recorded_at` | TEXT | NOT NULL | `datetime('now')` | Snapshot timestamp |

**Indexes:**

```sql
-- Query: Health history for a specific agent (dashboard sparkline)
CREATE INDEX idx_health_agent_recorded ON agent_health_history(agent_id, recorded_at);

-- Query: Recent health snapshots across all agents
CREATE INDEX idx_health_recorded_at ON agent_health_history(recorded_at DESC);

-- Query: Find agents with health below threshold at latest snapshot
CREATE INDEX idx_health_score ON agent_health_history(health_score);
```

**Index Justification:**
- `idx_health_agent_recorded`: The dashboard sparkline queries `SELECT health_score, recorded_at FROM agent_health_history WHERE agent_id = ? ORDER BY recorded_at`. This composite index is a covering index for that query.
- `idx_health_recorded_at`: The "system health over time" graph queries recent snapshots across all agents.
- `idx_health_score`: Alerting rules check `health_score < threshold`.

---

#### 2.9 `detection_rules` -- Heuristic Anomaly Detection Rules

**Purpose:** Stores user-configurable and system-defined heuristic rules for detecting anomalies in agent behavior. Rules are evaluated against agent metrics and incident patterns.

```sql
CREATE TABLE detection_rules (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    rule_type            TEXT NOT NULL,
    description          TEXT,
    condition_json       TEXT NOT NULL DEFAULT '{}',
    severity_on_trigger  TEXT NOT NULL DEFAULT 'MEDIUM',
    incident_type_code   TEXT,
    is_active            INTEGER NOT NULL DEFAULT 1,
    trigger_count        INTEGER NOT NULL DEFAULT 0,
    last_triggered_at    TEXT,
    created_by           TEXT NOT NULL DEFAULT 'system',
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (rule_type IN (
        'THRESHOLD', 'PATTERN', 'ANOMALY', 'FREQUENCY',
        'CORRELATION', 'DRIFT', 'CUSTOM'
    )),
    CHECK (severity_on_trigger IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    CHECK (incident_type_code IN (
        'AGT-DEL-001', 'AGT-FIN-002', 'AGT-PER-003', 'AGT-HRM-004',
        'AGT-EXT-005', 'AGT-INJ-006', 'AGT-HAL-007', 'AGT-CRE-008',
        'AGT-RAT-009', 'AGT-DRF-010', 'AGT-TLM-011', 'AGT-GAP-012'
    )),
    CHECK (is_active IN (0, 1)),
    CHECK (trigger_count >= 0)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique rule identifier |
| `name` | TEXT | NOT NULL | -- | Human-readable rule name |
| `rule_type` | TEXT | NOT NULL, CHECK (7 values) | -- | Category of detection rule |
| `description` | TEXT | -- | -- | Detailed description |
| `condition_json` | TEXT | NOT NULL | `'{}'` | Rule conditions as JSON |
| `severity_on_trigger` | TEXT | NOT NULL, CHECK (5 values) | `'MEDIUM'` | Severity when rule fires |
| `incident_type_code` | TEXT | CHECK (12 values) | -- | Incident type to create on trigger |
| `is_active` | INTEGER | NOT NULL, CHECK (0 or 1) | `1` | Whether rule is enabled |
| `trigger_count` | INTEGER | NOT NULL, CHECK (>=0) | `0` | Times this rule has fired |
| `last_triggered_at` | TEXT | -- | -- | Last trigger timestamp |
| `created_by` | TEXT | NOT NULL | `'system'` | Who created this rule |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Rule creation timestamp |
| `updated_at` | TEXT | NOT NULL | `datetime('now')` | Last modification timestamp |

**Indexes:**

```sql
-- Query: List active rules for evaluation engine
CREATE INDEX idx_detection_rules_active ON detection_rules(is_active);

-- Query: Rules sorted by trigger count (identify noisy rules)
CREATE INDEX idx_detection_rules_trigger_count ON detection_rules(trigger_count DESC);

-- Query: Rules for a specific incident type
CREATE INDEX idx_detection_rules_type ON detection_rules(incident_type_code);
```

**Triggers:**

```sql
-- Auto-update updated_at
CREATE TRIGGER trg_detection_rules_updated_at
AFTER UPDATE ON detection_rules
BEGIN
    UPDATE detection_rules
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;
```

---

#### 2.10 `demo_scenarios` -- Pre-Built Demo Scenarios

**Purpose:** Stores pre-built demo scenarios that can be loaded for demonstrations, training, and sales presentations. Each scenario contains complete incident data, agent configuration, and narrative context.

```sql
CREATE TABLE demo_scenarios (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT NOT NULL,
    description          TEXT,
    scenario_data        TEXT NOT NULL DEFAULT '{}',
    incident_types       TEXT NOT NULL DEFAULT '[]',
    difficulty           TEXT NOT NULL DEFAULT 'EASY',
    estimated_duration   INTEGER DEFAULT 300,
    is_active            INTEGER NOT NULL DEFAULT 1,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD', 'EXPERT')),
    CHECK (is_active IN (0, 1)),
    CHECK (estimated_duration > 0)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique scenario identifier |
| `name` | TEXT | NOT NULL | -- | Human-readable scenario name |
| `description` | TEXT | -- | -- | Detailed scenario narrative |
| `scenario_data` | TEXT | NOT NULL | `'{}'` | Complete scenario definition as JSON |
| `incident_types` | TEXT | NOT NULL | `'[]'` | JSON array of incident type codes in scenario |
| `difficulty` | TEXT | NOT NULL, CHECK (4 values) | `'EASY'` | Scenario complexity level |
| `estimated_duration` | INTEGER | CHECK (>0) | `300` | Estimated run time in seconds |
| `is_active` | INTEGER | NOT NULL, CHECK (0 or 1) | `1` | Whether scenario is available |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Creation timestamp |

**Indexes:**

```sql
-- Query: List active scenarios for scenario picker
CREATE INDEX idx_demo_scenarios_active ON demo_scenarios(is_active);

-- Query: Scenarios by difficulty
CREATE INDEX idx_demo_scenarios_difficulty ON demo_scenarios(difficulty);
```

---

#### 2.11 `compliance_mappings` -- EU AI Act Article-to-Incident Mappings

**Purpose:** Maps incidents to specific articles of the EU AI Act and other regulatory frameworks. Enables automated compliance reporting and risk assessment.

```sql
CREATE TABLE compliance_mappings (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id          INTEGER NOT NULL,
    framework            TEXT NOT NULL DEFAULT 'EU_AI_ACT',
    article_ref          TEXT NOT NULL,
    article_title        TEXT,
    risk_level           TEXT NOT NULL DEFAULT 'LIMITED',
    mapping_confidence   REAL NOT NULL DEFAULT 1.0,
    notes                TEXT,
    mapped_by            TEXT NOT NULL DEFAULT 'system',
    mapped_at            TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (framework IN ('EU_AI_ACT', 'NIST_AI_RMF', 'ISO_42001', 'SOC2', 'CUSTOM')),
    CHECK (risk_level IN ('MINIMAL', 'LIMITED', 'HIGH', 'UNACCEPTABLE')),
    CHECK (mapping_confidence >= 0.0 AND mapping_confidence <= 1.0),

    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique mapping identifier |
| `incident_id` | INTEGER | NOT NULL, FK -> incidents.id | -- | The incident being mapped |
| `framework` | TEXT | NOT NULL, CHECK (5 values) | `'EU_AI_ACT'` | Regulatory framework |
| `article_ref` | TEXT | NOT NULL | -- | Article reference (e.g., "Article 50(1)") |
| `article_title` | TEXT | -- | -- | Human-readable article title |
| `risk_level` | TEXT | NOT NULL, CHECK (4 values) | `'LIMITED'` | Risk classification |
| `mapping_confidence` | REAL | NOT NULL, CHECK (0-1) | `1.0` | Confidence in the mapping |
| `notes` | TEXT | -- | -- | Analyst notes on the mapping |
| `mapped_by` | TEXT | NOT NULL | `'system'` | Who/what created the mapping |
| `mapped_at` | TEXT | NOT NULL | `datetime('now')` | Mapping timestamp |

**Indexes:**

```sql
-- Query: Compliance mappings for a specific incident
CREATE INDEX idx_compliance_incident_id ON compliance_mappings(incident_id);

-- Query: Incidents by risk level (compliance dashboard)
CREATE INDEX idx_compliance_risk_level ON compliance_mappings(risk_level);

-- Query: Mappings by framework (framework-specific reports)
CREATE INDEX idx_compliance_framework ON compliance_mappings(framework, article_ref);

-- Query: Recent compliance mappings
CREATE INDEX idx_compliance_mapped_at ON compliance_mappings(mapped_at DESC);
```

---

#### 2.12 `judge_decisions` -- Judge Layer Decision Records

**Purpose:** Records every decision made by the Judge Layer -- the LLM-judge evaluation engine that intercepts, analyzes, and rules on agent-proposed actions before they are executed. Tracks verdicts, confidence, bypass detection, and latency for operational monitoring and security analytics.

```sql
CREATE TABLE judge_decisions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id          INTEGER,
    agent_id             INTEGER NOT NULL,
    proposed_action      TEXT NOT NULL,
    verdict              TEXT NOT NULL,
    confidence           REAL NOT NULL DEFAULT 1.0,
    rationale            TEXT,
    metadata_context     TEXT DEFAULT '{}',
    bypass_detected      INTEGER NOT NULL DEFAULT 0,
    bypass_pattern_id    INTEGER,
    gemini_enhanced      INTEGER NOT NULL DEFAULT 0,
    latency_ms           INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),

    -- Enum constraints
    CHECK (verdict IN ('ALLOW', 'DENY', 'QUARANTINE', 'ESCALATE')),
    -- Boolean constraints
    CHECK (bypass_detected IN (0, 1)),
    CHECK (gemini_enhanced IN (0, 1)),
    -- Confidence must be between 0 and 1
    CHECK (confidence >= 0.0 AND confidence <= 1.0),
    -- Latency must be non-negative
    CHECK (latency_ms >= 0),

    -- Foreign keys
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (bypass_pattern_id) REFERENCES bypass_patterns(id) ON DELETE SET NULL ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique decision identifier |
| `incident_id` | INTEGER | FK -> incidents.id | -- | The incident this decision relates to |
| `agent_id` | INTEGER | NOT NULL, FK -> agents.id | -- | The agent whose action was evaluated |
| `proposed_action` | TEXT | NOT NULL | -- | What the agent wanted to do |
| `verdict` | TEXT | NOT NULL, CHECK (4 values) | -- | `ALLOW`, `DENY`, `QUARANTINE`, or `ESCALATE` |
| `confidence` | REAL | NOT NULL, CHECK (0-1) | `1.0` | Judge confidence score (1.0 for deterministic) |
| `rationale` | TEXT | -- | -- | Human-readable explanation for the verdict |
| `metadata_context` | TEXT | -- | `'{}'` | Lobster Trap metadata used for the decision as JSON |
| `bypass_detected` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether a bypass attempt was detected |
| `bypass_pattern_id` | INTEGER | FK -> bypass_patterns.id | -- | The matched bypass pattern (if detected) |
| `gemini_enhanced` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether Gemini was used to enhance the decision |
| `latency_ms` | INTEGER | NOT NULL, CHECK (>=0) | `0` | Decision latency in milliseconds |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Decision timestamp |

**Indexes:**

```sql
-- Query: Judge decisions by agent + time (agent decision history dashboard)
CREATE INDEX idx_judge_decisions_agent_created ON judge_decisions(agent_id, created_at DESC);

-- Query: Filter decisions by verdict (verdict distribution analytics)
CREATE INDEX idx_judge_decisions_verdict ON judge_decisions(verdict);

-- Query: Find decisions with bypass detection (security dashboard)
CREATE INDEX idx_judge_decisions_bypass ON judge_decisions(bypass_detected);

-- Query: Find decisions for an incident (incident detail view)
CREATE INDEX idx_judge_decisions_incident ON judge_decisions(incident_id);

-- Query: Find decisions by bypass pattern (pattern analysis)
CREATE INDEX idx_judge_decisions_pattern ON judge_decisions(bypass_pattern_id);

-- Query: Decision latency analysis (performance monitoring)
CREATE INDEX idx_judge_decisions_latency ON judge_decisions(latency_ms);

-- Query: Recent decisions (Judge Layer activity feed)
CREATE INDEX idx_judge_decisions_created ON judge_decisions(created_at DESC);
```

**Index Justification:**
- `idx_judge_decisions_agent_created`: The agent detail page shows decisions in reverse chronological order. This composite index supports that query pattern.
- `idx_judge_decisions_verdict`: The verdict distribution chart groups by verdict (`ALLOW`, `DENY`, `QUARANTINE`, `ESCALATE`).
- `idx_judge_decisions_bypass`: The bypass detection dashboard filters on `bypass_detected = 1` for security review.
- `idx_judge_decisions_incident`: When viewing an incident, the system looks up its associated judge decision.
- `idx_judge_decisions_pattern`: Pattern drill-down queries all decisions that matched a specific bypass pattern.
- `idx_judge_decisions_latency`: Performance monitoring queries average and p95 latency.
- `idx_judge_decisions_created`: The "recent decisions" activity feed shows the latest decisions first.

**Triggers:**

```sql
-- Audit trail: log every judge decision
CREATE TRIGGER trg_judge_decisions_audit_insert
AFTER INSERT ON judge_decisions
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('judge_decisions', NEW.id, 'INSERT', NULL,
        json_object('agent_id', NEW.agent_id,
                    'incident_id', NEW.incident_id,
                    'verdict', NEW.verdict,
                    'confidence', NEW.confidence,
                    'bypass_detected', NEW.bypass_detected,
                    'latency_ms', NEW.latency_ms),
        'system', datetime('now'));
END;

-- Auto-increment agent judge_decision_count on new decision
CREATE TRIGGER trg_judge_decisions_agent_count
AFTER INSERT ON judge_decisions
BEGIN
    UPDATE agents
    SET judge_decision_count = judge_decision_count + 1
    WHERE id = NEW.agent_id;
END;

-- Audit trail: log bypass detection
CREATE TRIGGER trg_judge_decisions_bypass_audit
AFTER INSERT ON judge_decisions
WHEN NEW.bypass_detected = 1
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
    VALUES ('judge_decisions', NEW.id, 'JUDGE_BYPASS_DETECTED', NULL,
        json_object('bypass_pattern_id', NEW.bypass_pattern_id,
                    'agent_id', NEW.agent_id),
        'system', datetime('now'));
END;
```

---
#### 2.13 `bypass_patterns` -- Known LLM-Judge Bypass Patterns

**Purpose:** Catalog of known LLM-judge bypass attack patterns that PLAYBOOK's Lobster Trap module is trained to detect. Each pattern includes a detection rule and mitigation strategy for proactive defense.

```sql
CREATE TABLE bypass_patterns (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name         TEXT NOT NULL UNIQUE,
    pattern_display_name TEXT NOT NULL,
    description          TEXT,
    detection_rule       TEXT NOT NULL,
    severity             INTEGER NOT NULL DEFAULT 3,
    mitigated_by         TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),

    -- Severity must be between 1 and 5
    CHECK (severity >= 1 AND severity <= 5)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique pattern identifier |
| `pattern_name` | TEXT | NOT NULL, UNIQUE | -- | Machine-readable pattern name (e.g., `context_window_displacement`) |
| `pattern_display_name` | TEXT | NOT NULL | -- | Human-readable display name (e.g., `Context Window Displacement`) |
| `description` | TEXT | -- | -- | Detailed description of the attack pattern |
| `detection_rule` | TEXT | NOT NULL | -- | Regex pattern or logic rule used to detect this bypass |
| `severity` | INTEGER | NOT NULL, CHECK (1-5) | `3` | Pattern severity: 1 (informational) to 5 (critical) |
| `mitigated_by` | TEXT | -- | -- | How PLAYBOOK prevents this attack (description or reference) |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Pattern catalog entry timestamp |

**Indexes:**

```sql
-- Query: Look up pattern by machine-readable name (detection engine)
CREATE UNIQUE INDEX idx_bypass_patterns_name ON bypass_patterns(pattern_name);

-- Query: Patterns sorted by severity (security dashboard)
CREATE INDEX idx_bypass_patterns_severity ON bypass_patterns(severity DESC);

-- Query: Recently added patterns
CREATE INDEX idx_bypass_patterns_created ON bypass_patterns(created_at DESC);
```

**Index Justification:**
- `idx_bypass_patterns_name`: The detection engine looks up patterns by name during rule evaluation.
- `idx_bypass_patterns_severity`: The security dashboard shows patterns ordered by severity to prioritize defense efforts.
- `idx_bypass_patterns_created`: The pattern catalog shows recently added patterns first.

---
#### 2.14 `bypass_attempts` -- Log of Detected Bypass Attempts

**Purpose:** Append-only log of every detected LLM-judge bypass attempt. Links back to the triggering judge decision and the matched bypass pattern for forensic analysis and trend reporting.

```sql
CREATE TABLE bypass_attempts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_decision_id    INTEGER NOT NULL,
    pattern_id           INTEGER NOT NULL,
    raw_payload          TEXT,
    detection_confidence REAL NOT NULL DEFAULT 1.0,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),

    -- Confidence must be between 0 and 1
    CHECK (detection_confidence >= 0.0 AND detection_confidence <= 1.0),

    -- Foreign keys
    FOREIGN KEY (judge_decision_id) REFERENCES judge_decisions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (pattern_id) REFERENCES bypass_patterns(id) ON DELETE RESTRICT ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique attempt identifier |
| `judge_decision_id` | INTEGER | NOT NULL, FK -> judge_decisions.id | -- | The judge decision where bypass was detected |
| `pattern_id` | INTEGER | NOT NULL, FK -> bypass_patterns.id | -- | The bypass pattern that matched |
| `raw_payload` | TEXT | -- | -- | The full bypass attempt payload (for forensic review) |
| `detection_confidence` | REAL | NOT NULL, CHECK (0-1) | `1.0` | Confidence in the bypass detection |
| `created_at` | TEXT | NOT NULL | `datetime('now')` | Detection timestamp |

**Indexes:**

```sql
-- Query: Bypass attempts by pattern + time (trend analysis)
CREATE INDEX idx_bypass_attempts_pattern_created ON bypass_attempts(pattern_id, created_at DESC);

-- Query: Bypass attempts for a specific judge decision
CREATE INDEX idx_bypass_attempts_decision ON bypass_attempts(judge_decision_id);

-- Query: Recent bypass attempts (security alert feed)
CREATE INDEX idx_bypass_attempts_created ON bypass_attempts(created_at DESC);
```

**Index Justification:**
- `idx_bypass_attempts_pattern_created`: The bypass trend analysis query groups by pattern and time window. This composite index accelerates the trend computation.
- `idx_bypass_attempts_decision`: When reviewing a judge decision, the system can quickly find all associated bypass attempts.
- `idx_bypass_attempts_created`: The "recent bypass attempts" alert feed shows the latest attempts first.

**Triggers:**

```sql
-- Auto-increment agent bypass_attempt_count on new bypass attempt
CREATE TRIGGER trg_bypass_attempts_agent_count
AFTER INSERT ON bypass_attempts
BEGIN
    UPDATE agents
    SET bypass_attempt_count = bypass_attempt_count + 1
    WHERE id = (SELECT agent_id FROM judge_decisions WHERE id = NEW.judge_decision_id);
END;
```

---
#### 2.15 `suprawall_events` -- Ingested SupraWall Decision Events

**Purpose:** Ingests decision events from external SupraWall installations for cross-system correlation. Enables PLAYBOOK to correlate its internal incident detection with external decision boundaries from upstream SupraWall firewalls.

```sql
CREATE TABLE suprawall_events (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id                 INTEGER NOT NULL,
    event_type               TEXT NOT NULL,
    suprawall_decision       TEXT NOT NULL DEFAULT '{}',
    correlated_incident_id   INTEGER,
    ingested_at              TEXT NOT NULL DEFAULT (datetime('now')),

    -- Enum constraints
    CHECK (event_type IN ('SUPRAWALL_ALLOW', 'SUPRAWALL_DENY')),

    -- Foreign keys
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (correlated_incident_id) REFERENCES incidents(id) ON DELETE SET NULL ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique event identifier |
| `agent_id` | INTEGER | NOT NULL, FK -> agents.id | -- | The agent associated with this SupraWall event |
| `event_type` | TEXT | NOT NULL, CHECK (2 values) | -- | `SUPRAWALL_ALLOW` or `SUPRAWALL_DENY` |
| `suprawall_decision` | TEXT | NOT NULL | `'{}'` | Full SupraWall decision payload as JSON |
| `correlated_incident_id` | INTEGER | FK -> incidents.id | -- | PLAYBOOK incident correlated with this event |
| `ingested_at` | TEXT | NOT NULL | `datetime('now')` | When the event was ingested |

**Indexes:**

```sql
-- Query: SupraWall events by agent + time (agent SupraWall activity view)
CREATE INDEX idx_suprawall_agent_ingested ON suprawall_events(agent_id, ingested_at DESC);

-- Query: Find events for a correlated incident (incident correlation view)
CREATE INDEX idx_suprawall_incident ON suprawall_events(correlated_incident_id);

-- Query: Events by type (allow vs deny analytics)
CREATE INDEX idx_suprawall_event_type ON suprawall_events(event_type);

-- Query: Recently ingested events (SupraWall activity feed)
CREATE INDEX idx_suprawall_ingested ON suprawall_events(ingested_at DESC);
```

**Index Justification:**
- `idx_suprawall_agent_ingested`: The agent detail page shows SupraWall events in reverse chronological order.
- `idx_suprawall_incident`: When viewing an incident, the system looks up correlated SupraWall events.
- `idx_suprawall_event_type`: The allow vs deny distribution chart filters by event_type.
- `idx_suprawall_ingested`: The "recent SupraWall events" activity feed shows the latest events first.

---

#### 2.16 `nist_baselines` -- NIST AI RMF Baseline Policy Definitions

**Purpose:** Stores the NIST AI Risk Management Framework baseline policies for each of the 12 incident types. These baselines define the default response parameters (severity, auto-containment, SLA, forensic level, etc.) that are recommended by the NIST AI RMF Agentic Profile. Each row represents the authoritative starting point for incident response policy.

```sql
CREATE TABLE nist_baselines (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_type             TEXT NOT NULL UNIQUE,  -- AGT-DEL-001, AGT-FIN-002, etc.
    name                      TEXT NOT NULL,          -- "Data Destruction"
    description               TEXT NOT NULL,
    nist_source               TEXT NOT NULL,          -- "NIST AI RMF Agentic Profile AG-MG.1"
    default_severity          TEXT NOT NULL,          -- CRITICAL, HIGH, MEDIUM, LOW
    default_auto_contain      INTEGER NOT NULL DEFAULT 0,
    default_forensic_level    TEXT DEFAULT 'STANDARD',
    default_response_sla_minutes INTEGER DEFAULT 15,
    default_compliance_report TEXT DEFAULT 'CONDITIONAL',  -- ALWAYS, CONDITIONAL, NEVER
    default_record_threshold  INTEGER DEFAULT 100,
    response_actions_json     TEXT NOT NULL,          -- JSON array of default actions
    compliance_mappings_json  TEXT NOT NULL,          -- JSON array of EU AI Act article mappings
    created_at                DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Enum constraints
    CHECK (incident_type IN (
        'AGT-DEL-001', 'AGT-FIN-002', 'AGT-PER-003', 'AGT-HRM-004',
        'AGT-EXT-005', 'AGT-INJ-006', 'AGT-HAL-007', 'AGT-CRE-008',
        'AGT-RAT-009', 'AGT-DRF-010', 'AGT-TLM-011', 'AGT-GAP-012'
    )),
    CHECK (default_severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    CHECK (default_auto_contain IN (0, 1)),
    CHECK (default_forensic_level IN ('STANDARD', 'DEEP', 'LIGHTWEIGHT', 'NONE')),
    CHECK (default_compliance_report IN ('ALWAYS', 'CONDITIONAL', 'NEVER'))
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique baseline identifier |
| `incident_type` | TEXT | NOT NULL, UNIQUE, CHECK (12 values) | -- | Incident classification code |
| `name` | TEXT | NOT NULL | -- | Human-readable name for this incident type |
| `description` | TEXT | NOT NULL | -- | Detailed description of the incident type |
| `nist_source` | TEXT | NOT NULL | -- | NIST AI RMF reference (e.g., "NIST AI RMF Agentic Profile AG-MG.1") |
| `default_severity` | TEXT | NOT NULL, CHECK (5 values) | -- | Default severity level per NIST |
| `default_auto_contain` | INTEGER | NOT NULL, CHECK (0 or 1) | `0` | Whether NIST recommends auto-containment |
| `default_forensic_level` | TEXT | CHECK (4 values) | `'STANDARD'` | Default forensic evidence collection level |
| `default_response_sla_minutes` | INTEGER | -- | `15` | Default response time SLA in minutes |
| `default_compliance_report` | TEXT | CHECK (3 values) | `'CONDITIONAL'` | When compliance reports are generated |
| `default_record_threshold` | INTEGER | -- | `100` | Default record impact threshold |
| `response_actions_json` | TEXT | NOT NULL | -- | JSON array of default response actions |
| `compliance_mappings_json` | TEXT | NOT NULL | -- | JSON array of EU AI Act article mappings |
| `created_at` | DATETIME | -- | `CURRENT_TIMESTAMP` | Baseline creation timestamp |

**Indexes:**

```sql
-- Query: Look up baseline by incident type (ODP resolution engine)
CREATE INDEX idx_nist_type ON nist_baselines(incident_type);
```

**Index Justification:**
- `idx_nist_type`: The ODP resolution engine queries baselines by incident_type when computing resolved_policies for an incident.

---

#### 2.17 `organization_odps` -- Organization-Defined Parameters

**Purpose:** Stores organization-specific overrides to the NIST baseline policies. Each row represents a single ODP key-value pair for a specific incident type. When an organization deviates from the NIST default, the `is_override` flag is set and the value is used in the `resolved_policies` view. There are 8 ODP keys per incident type x 12 incident types = 96 rows per organization.

```sql
CREATE TABLE organization_odps (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nist_baseline_id    INTEGER NOT NULL,
    odp_key             TEXT NOT NULL,         -- severity_threshold, auto_contain_enabled, etc.
    odp_value           TEXT NOT NULL,         -- CRITICAL, true, 5, etc.
    is_override         INTEGER DEFAULT 1,     -- true if different from NIST default
    version             INTEGER DEFAULT 1,
    changed_by          TEXT,                  -- user who last changed this
    changed_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(nist_baseline_id, odp_key),

    -- Boolean constraints
    CHECK (is_override IN (0, 1)),
    CHECK (version > 0),
    CHECK (odp_key IN (
        'severity_threshold', 'auto_contain_enabled', 'escalation_contacts',
        'response_time_sla', 'forensic_level', 'notify_targets',
        'compliance_report', 'record_threshold'
    )),

    -- Foreign keys
    FOREIGN KEY (nist_baseline_id) REFERENCES nist_baselines(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique ODP identifier |
| `nist_baseline_id` | INTEGER | NOT NULL, FK -> nist_baselines.id | -- | The baseline this ODP overrides |
| `odp_key` | TEXT | NOT NULL, CHECK (8 values) | -- | The parameter being overridden |
| `odp_value` | TEXT | NOT NULL | -- | The organization-defined value |
| `is_override` | INTEGER | CHECK (0 or 1) | `1` | Whether this differs from the NIST default |
| `version` | INTEGER | CHECK (>0) | `1` | Version of this ODP setting |
| `changed_by` | TEXT | -- | -- | User who last changed this ODP |
| `changed_at` | DATETIME | -- | `CURRENT_TIMESTAMP` | Last modification timestamp |

**Indexes:**

```sql
-- Query: Fetch ODPs for a specific baseline (ODP resolution)
CREATE INDEX idx_odp_baseline ON organization_odps(nist_baseline_id);

-- Query: Fetch ODPs by key name (cross-type ODP analysis)
CREATE INDEX idx_odp_key ON organization_odps(odp_key);
```

**Index Justification:**
- `idx_odp_baseline`: The `resolved_policies` view joins on `nist_baseline_id` for each of the 8 ODP keys. This index accelerates those lookups.
- `idx_odp_key`: ODP management UIs need to show the same ODP key across all incident types (e.g., "what is the auto_contain setting for every type?").

---

#### 2.18 `policy_versions` -- ODP Policy Change History

**Purpose:** Append-only log of every ODP policy version change. Tracks who changed policy parameters, what changed, and when. Provides a complete audit trail for compliance investigations and rollback capability.

```sql
CREATE TABLE policy_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    version_number      INTEGER NOT NULL,
    changed_by          TEXT NOT NULL,
    change_summary      TEXT NOT NULL,
    diff_json           TEXT NOT NULL,        -- JSON diff of what changed
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,

    CHECK (version_number > 0)
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique version identifier |
| `version_number` | INTEGER | NOT NULL, CHECK (>0) | -- | Sequential version number |
| `changed_by` | TEXT | NOT NULL | -- | User or system that made the change |
| `change_summary` | TEXT | NOT NULL | -- | Human-readable description of the change |
| `diff_json` | TEXT | NOT NULL | -- | JSON diff showing old vs new values for each changed ODP |
| `created_at` | DATETIME | -- | `CURRENT_TIMESTAMP` | Version creation timestamp |

**Indexes:**

```sql
-- Query: Find policy version by number (rollback and comparison)
CREATE INDEX idx_policy_version ON policy_versions(version_number);

-- Query: Recent policy changes (policy audit dashboard)
CREATE INDEX idx_policy_version_created ON policy_versions(created_at DESC);
```

**Index Justification:**
- `idx_policy_version`: The policy rollback engine looks up specific version numbers.
- `idx_policy_version_created`: The policy audit dashboard shows recent changes first.

---

#### 2.19 `industry_templates` -- Pre-Built Industry ODP Templates

**Purpose:** Provides pre-configured ODP sets for common regulatory frameworks and industry verticals. Each template contains a complete set of ODP overrides (all 12 incident types x 8 ODP keys) tailored to a specific compliance context. Organizations can apply a template as a starting point and then customize further.

```sql
CREATE TABLE industry_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL UNIQUE,   -- "HIPAA", "SOC2", "PCI-DSS", etc.
    display_name        TEXT NOT NULL,          -- "HIPAA Healthcare"
    description         TEXT NOT NULL,
    odp_set_json        TEXT NOT NULL,          -- JSON: {AGT-DEL-001: {severity: CRITICAL, ...}, ...}
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique template identifier |
| `name` | TEXT | NOT NULL, UNIQUE | -- | Machine-readable template name |
| `display_name` | TEXT | NOT NULL | -- | Human-readable display name |
| `description` | TEXT | NOT NULL | -- | Description of the template's compliance context |
| `odp_set_json` | TEXT | NOT NULL | -- | JSON object mapping incident types to their full ODP sets |
| `created_at` | DATETIME | -- | `CURRENT_TIMESTAMP` | Template creation timestamp |

---

#### 2.20 `odp_conflicts` -- ODP-NIST Conflict Detection

**Purpose:** Automated detection of ODP overrides that conflict with NIST baseline recommendations. When an organization sets a parameter that is less strict than the NIST default (e.g., downgrading severity from CRITICAL to MEDIUM), a conflict record is generated. Conflicts are classified as `WARNING` (acceptable deviation, logged) or `BLOCKED` (requires approval before activation).

```sql
CREATE TABLE odp_conflicts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_odp_id     INTEGER,
    conflict_type           TEXT NOT NULL,       -- SEVERITY_DOWNGRADE, AUTO_CONTAIN_DISABLED, etc.
    severity                TEXT NOT NULL,       -- WARNING or BLOCKED
    nist_default_value      TEXT NOT NULL,
    org_value               TEXT NOT NULL,
    resolution_suggestion   TEXT,
    resolved                INTEGER DEFAULT 0,
    detected_at             DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Enum constraints
    CHECK (severity IN ('WARNING', 'BLOCKED')),
    CHECK (resolved IN (0, 1)),
    CHECK (conflict_type IN (
        'SEVERITY_DOWNGRADE', 'AUTO_CONTAIN_DISABLED', 'SLA_EXCEEDED',
        'FORENSIC_LEVEL_REDUCED', 'COMPLIANCE_REPORT_SKIPPED',
        'THRESHOLD_INCREASED', 'ESCALATION_REMOVED', 'NOTIFY_REMOVED'
    )),

    -- Foreign keys
    FOREIGN KEY (organization_odp_id) REFERENCES organization_odps(id) ON DELETE SET NULL ON UPDATE CASCADE
);
```

**Column Descriptions:**

| Column | Type | Constraints | Default | Description |
|--------|------|-------------|---------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | -- | Unique conflict identifier |
| `organization_odp_id` | INTEGER | FK -> organization_odps.id | -- | The ODP that triggered the conflict |
| `conflict_type` | TEXT | NOT NULL, CHECK (8 values) | -- | Category of conflict |
| `severity` | TEXT | NOT NULL, CHECK (2 values) | -- | `WARNING` or `BLOCKED` |
| `nist_default_value` | TEXT | NOT NULL | -- | The NIST recommended value |
| `org_value` | TEXT | NOT NULL | -- | The organization-set value |
| `resolution_suggestion` | TEXT | -- | -- | Recommended resolution action |
| `resolved` | INTEGER | CHECK (0 or 1) | `0` | Whether the conflict has been resolved |
| `detected_at` | DATETIME | -- | `CURRENT_TIMESTAMP` | When the conflict was detected |

**Indexes:**

```sql
-- Query: Conflicts for a specific ODP (conflict detail view)
CREATE INDEX idx_conflict_odp ON odp_conflicts(organization_odp_id);

-- Query: Conflicts by type (conflict analytics dashboard)
CREATE INDEX idx_conflict_type ON odp_conflicts(conflict_type);

-- Query: Unresolved conflicts (security alerts)
CREATE INDEX idx_conflict_unresolved ON odp_conflicts(resolved, detected_at DESC);
```

**Index Justification:**
- `idx_conflict_odp`: When reviewing an ODP, the system can quickly find all associated conflicts.
- `idx_conflict_type`: The conflict analytics dashboard groups by conflict type to identify common deviation patterns.
- `idx_conflict_unresolved`: The security alert feed shows unresolved conflicts first, ordered by detection time.

---

#### 2.21 `resolved_policies` -- ODP-Resolved Policy View

**Purpose:** A read-only view that computes the effective policy for each incident type by overlaying organization-defined parameters (ODPs) on top of NIST baseline defaults. For each of the 12 incident types and 8 ODP keys, the view returns the ODP value if one exists, otherwise falls back to the NIST baseline default. This is the primary interface for the incident response engine to determine what actions to take.

```sql
CREATE VIEW resolved_policies AS
SELECT
    nb.id as baseline_id,
    nb.incident_type,
    COALESCE(oo_severity.odp_value, nb.default_severity) as resolved_severity,
    COALESCE(oo_contain.odp_value, CAST(nb.default_auto_contain AS TEXT)) as resolved_auto_contain,
    COALESCE(oo_escalation.odp_value, '') as resolved_escalation,
    COALESCE(oo_sla.odp_value, CAST(nb.default_response_sla_minutes AS TEXT)) as resolved_sla,
    COALESCE(oo_forensic.odp_value, nb.default_forensic_level) as resolved_forensic,
    COALESCE(oo_notify.odp_value, '') as resolved_notify,
    COALESCE(oo_compliance.odp_value, nb.default_compliance_report) as resolved_compliance,
    COALESCE(oo_threshold.odp_value, CAST(nb.default_record_threshold AS TEXT)) as resolved_threshold
FROM nist_baselines nb
LEFT JOIN organization_odps oo_severity ON nb.id = oo_severity.nist_baseline_id AND oo_severity.odp_key = 'severity_threshold'
LEFT JOIN organization_odps oo_contain ON nb.id = oo_contain.nist_baseline_id AND oo_contain.odp_key = 'auto_contain_enabled'
LEFT JOIN organization_odps oo_escalation ON nb.id = oo_escalation.nist_baseline_id AND oo_escalation.odp_key = 'escalation_contacts'
LEFT JOIN organization_odps oo_sla ON nb.id = oo_sla.nist_baseline_id AND oo_sla.odp_key = 'response_time_sla'
LEFT JOIN organization_odps oo_forensic ON nb.id = oo_forensic.nist_baseline_id AND oo_forensic.odp_key = 'forensic_level'
LEFT JOIN organization_odps oo_notify ON nb.id = oo_notify.nist_baseline_id AND oo_notify.odp_key = 'notify_targets'
LEFT JOIN organization_odps oo_compliance ON nb.id = oo_compliance.nist_baseline_id AND oo_compliance.odp_key = 'compliance_report'
LEFT JOIN organization_odps oo_threshold ON nb.id = oo_threshold.nist_baseline_id AND oo_threshold.odp_key = 'record_threshold';
```

**Resolved Columns:**

| Column | Description |
|--------|-------------|
| `baseline_id` | The nist_baselines.id for the incident type |
| `incident_type` | The incident type code (e.g., AGT-DEL-001) |
| `resolved_severity` | Effective severity (ODP override or NIST default) |
| `resolved_auto_contain` | Effective auto-containment (ODP override or NIST default) |
| `resolved_escalation` | Effective escalation contacts (ODP override or empty) |
| `resolved_sla` | Effective response SLA in minutes (ODP override or NIST default) |
| `resolved_forensic` | Effective forensic level (ODP override or NIST default) |
| `resolved_notify` | Effective notification targets (ODP override or empty) |
| `resolved_compliance` | Effective compliance report mode (ODP override or NIST default) |
| `resolved_threshold` | Effective record threshold (ODP override or NIST default) |

> **Note:** This view performs 8 LEFT JOINs to organization_odps. For best performance, ensure both `idx_odp_baseline` and `idx_odp_key` indexes exist. With 96 ODP rows per organization, the view resolves all 12 incident types in sub-millisecond time.

---

### 3. Entity Relationships

#### 3.1 One-to-Many Relationships

| Parent Table | Child Table | Foreign Key | On Delete | Description |
|---|---|---|---|---|
| `agents` | `incidents` | `incidents.agent_id` | RESTRICT | An agent with incidents cannot be deleted |
| `agents` | `agent_health_history` | `agent_health_history.agent_id` | CASCADE | Deleting an agent removes its health history |
| `agents` | `judge_decisions` | `judge_decisions.agent_id` | RESTRICT | An agent with decisions cannot be deleted |
| `agents` | `suprawall_events` | `suprawall_events.agent_id` | RESTRICT | An agent with SupraWall events cannot be deleted |
| `incidents` | `evidence_packages` | `evidence_packages.incident_id` | CASCADE | Deleting an incident removes its evidence |
| `incidents` | `compliance_mappings` | `compliance_mappings.incident_id` | CASCADE | Deleting an incident removes compliance mappings |
| `incidents` | `judge_decisions` | `judge_decisions.incident_id` | SET NULL | Incident deletion unlinks its judge decisions |
| `incidents` | `suprawall_events` | `suprawall_events.correlated_incident_id` | SET NULL | Incident deletion unlinks SupraWall correlations |
| `playbooks` | `incidents` | `incidents.playbook_id` | SET NULL | Deleting a playbook unassigns it from incidents |
| `playbooks` | `playbook_actions` | `playbook_actions.playbook_id` | CASCADE | Deleting a playbook removes all its actions |
| `judge_decisions` | `bypass_attempts` | `bypass_attempts.judge_decision_id` | CASCADE | Deleting a decision removes its bypass attempts |
| `judge_decisions` | `incidents` | `incidents.judge_decision_id` | SET NULL | Deleting a decision unlinks it from incidents |
| `bypass_patterns` | `judge_decisions` | `judge_decisions.bypass_pattern_id` | SET NULL | Deleting a pattern unlinks matched decisions |
| `bypass_patterns` | `bypass_attempts` | `bypass_attempts.pattern_id` | RESTRICT | Cannot delete a pattern with logged bypass attempts |
| `nist_baselines` | `organization_odps` | `organization_odps.nist_baseline_id` | CASCADE | Deleting a baseline removes all its ODPs |
| `nist_baselines` | `incidents` | `incidents.resolved_policy_id` | -- | View reference; baseline drives incident policy |
| `organization_odps` | `odp_conflicts` | `odp_conflicts.organization_odp_id` | SET NULL | Deleting an ODP unlinks its conflict records |

#### 3.2 Relationship Diagram (Detailed)

```
+------------------+     +---------------------+     +-------------------+
|     agents       |1    |      incidents      |1    | evidence_packages |
| id (PK)          |<----| id (PK)             |<----| id (PK)           |
| name             |     | agent_id (FK)       |     | incident_id (FK)  |
| system_id        |     | type_code           |     | ...               |
| health_score     |     | severity            |     +-------------------+
| judge_decision_c |     | status              |              ^
| bypass_attempt_c |     | judge_decision_id---(0..1)         |
| suprawall_connec |     | bypass_detected     |              |
|                  |     | odp_override_appl   |              |
|                  |     | resolved_policy_id  |              |
+-------+----------+     +---------------------+              |
        | 1                     ^  ^  ^                        |
        |                       |  |  |                        |
        |              nist_baselines playbook_id              |
        |              (resolved_policy_id)   |                |
        |                       |             |                |
        |            +----------+             |                |
        |            |                       |                |
        |  1         | 1                     |                |
        v            v                       v                |
+-------------------+    +-------------------+  +-------------------+
|agent_health_history|   |    playbooks      |  |compliance_mappings|
+-------------------+    +-------------------+  +-------------------+
| id (PK)           |    | id (PK)           |  | id (PK)           |
| agent_id (FK)     |    | name              |  | incident_id (FK)  |
| health_score      |    | type_code         |  | article_ref       |
| recorded_at       |    | is_active         |  | risk_level        |
+-------------------+    +-------------------+  +-------------------+
                                |
                                | 1
                                v
                        +-------------------+
                        | playbook_actions  |
                        +-------------------+
                        | id (PK)           |
                        | playbook_id (FK)  |
                        | step_order        |
                        | action_type       |
                        +-------------------+

+-------------------+    +-------------------+    +-------------------+
| nist_baselines    |    | organization_odps |    | odp_conflicts     |
+-------------------+    +-------------------+    +-------------------+
| id (PK)           |<---| id (PK)           |--->| id (PK)           |
| incident_type     |    | nist_baseline_id  |    | organization_odp  |
| name              |    | odp_key           |    | conflict_type     |
| default_severity  |    | odp_value         |    | severity          |
| response_actions  |    | is_override       |    | nist_default_val  |
| compliance_mappng |    | changed_by        |    | org_value         |
+-------------------+    +-------------------+    | resolved          |
        |                                         +-------------------+
        | 1
        v
+-------------------+    +-------------------+
| resolved_policies |    | industry_templates|
| (VIEW)            |    +-------------------+
| baseline_id       |    | id (PK)           |
| incident_type     |    | name              |
| resolved_severity |    | display_name      |
| resolved_sla      |    | odp_set_json      |
| resolved_forensic |    +-------------------+
+-------------------+

+-------------------+         +-------------------+         +-------------------+
| judge_decisions   |         | bypass_patterns   |         | bypass_attempts   |
+-------------------+         +-------------------+         +-------------------+
| id (PK)           |         | id (PK)           |  +---->| id (PK)           |
| incident_id (FK)  |         | pattern_name      |  |     | judge_decision_id |
| agent_id (FK)     |---------| pattern_display   |  |     | pattern_id (FK)   |
| verdict           |         | detection_rule    |  |     | raw_payload       |
| bypass_detected   |         | severity          |  |     | detection_confdnc |
| bypass_pattern_id |---------+ mitigated_by      |  |     +-------------------+
| latency_ms        |           created_at        |  |
| created_at        |                             |  |
+-------------------+                             |  |
                                                  |  |
+-------------------+                             |  |
| suprawall_events  |                             |  |
+-------------------+                             |  |
| id (PK)           |                             |  |
| agent_id (FK)-----+-----------------------------+  |
| event_type        |                                |
| suprawall_decision|                                |
| correlated_incide |                                |
| ingested_at       |                                |
+-------------------+                                |
                                                     |
+-------------------+                                |
| policy_versions   |                                |
+-------------------+                                |
| id (PK)           |                                |
| version_number    |                                |
| changed_by        |                                |
| change_summary    |                                |
| diff_json         |                                |
+-------------------+                                |
```

#### 3.3 Cascade Behaviors Summary

| Cascade | Tables Affected | Rationale |
|---|---|---|
| `ON DELETE CASCADE` | `agent_health_history` -> `agents` | Health history is meaningless without the agent |
| `ON DELETE CASCADE` | `playbook_actions` -> `playbooks` | Actions belong to their playbook |
| `ON DELETE CASCADE` | `evidence_packages` -> `incidents` | Evidence is tied to its incident |
| `ON DELETE CASCADE` | `compliance_mappings` -> `incidents` | Mappings reference specific incidents |
| `ON DELETE CASCADE` | `bypass_attempts` -> `judge_decisions` | Bypass attempts belong to their decision |
| `ON DELETE CASCADE` | `organization_odps` -> `nist_baselines` | ODPs are defined relative to a baseline |
| `ON DELETE SET NULL` | `incidents.playbook_id` -> `playbooks` | Incident record is preserved if playbook is deleted |
| `ON DELETE SET NULL` | `judge_decisions.incident_id` -> `incidents` | Judge decisions survive incident deletion for audit |
| `ON DELETE SET NULL` | `incidents.judge_decision_id` -> `judge_decisions` | Incident survives decision deletion |
| `ON DELETE SET NULL` | `suprawall_events.correlated_incident_id` -> `incidents` | SupraWall events survive incident deletion |
| `ON DELETE SET NULL` | `odp_conflicts.organization_odp_id` -> `organization_odps` | Conflict records survive ODP deletion for audit |
| `ON DELETE RESTRICT` | `incidents` -> `agents` | Prevent accidental data loss; agent must be cleaned up first |
| `ON DELETE RESTRICT` | `judge_decisions` -> `agents` | Prevent accidental data loss; agent must be cleaned up first |
| `ON DELETE RESTRICT` | `suprawall_events` -> `agents` | Prevent accidental data loss; agent must be cleaned up first |
| `ON DELETE RESTRICT` | `bypass_attempts` -> `bypass_patterns` | Cannot delete a known pattern that has logged attempts |

#### 3.4 Referential Integrity Notes

1. **Circular References:** There are no circular foreign key references in this schema. The dependency graph is a directed acyclic graph (DAG) rooted at `agents`, `playbooks`, and `nist_baselines`.

2. **Orphan Prevention:** The `ON DELETE RESTRICT` on `incidents.agent_id` prevents orphaned incidents. To delete an agent, all its incidents must be re-assigned or deleted first.

3. **Soft Deletes:** Neither `agents` nor `playbooks` use soft deletes (they have `is_active` flags). When a playbook is "deleted" via UI, it should be deactivated (`is_active = 0`) rather than removed from the database.

4. **Audit Log Independence:** The `audit_log` table has no foreign keys. This is intentional -- audit records must survive the deletion of the records they reference. The `table_name` and `record_id` columns serve as loose references.

5. **Gemini Cache Independence:** The `gemini_cache` table is independent of all other tables. Cache entries can be freely deleted without affecting any other data.

6. **Bypass Pattern Protection:** The `ON DELETE RESTRICT` on `bypass_attempts.pattern_id` protects the forensic record. A pattern cannot be deleted while bypass attempts are logged against it. This ensures audit trail completeness for security investigations.

7. **Judge Decision Immutability:** Judge decisions are append-only in practice. The `judge_decisions` table has no `updated_at` column and no update trigger. Once rendered, a decision is immutable. Corrections are modeled as new decisions with updated `incident_id` references.

8. **NIST Baseline Immutability:** NIST baseline rows should be treated as immutable reference data. Changes to NIST recommendations are modeled as new baselines or new policy_versions, not as updates to existing baseline rows.

9. **ODP Conflict Detection:** The `odp_conflicts` table is populated by a background process that compares each `organization_odps.odp_value` with its corresponding `nist_baselines` default. When a conflict is detected (e.g., severity downgrade), a row is inserted with `resolved = 0`. Conflicts must be explicitly resolved by an authorized user.

10. **View-Based Resolution:** The `resolved_policies` view is the single source of truth for effective incident response parameters. All incident response engines should query this view rather than accessing `nist_baselines` or `organization_odps` directly.

---
### 4. Sample Data

The following INSERT statements create three complete demo scenarios representing realistic AI agent deployments across different domains, plus Judge Layer decision records, bypass pattern definitions, bypass attempt logs, NIST baseline seed data, ODP configurations, industry templates, and policy version history.

---

#### 4.1 Scenario A: PocketOS -- DeFi Data Destruction Incident

**Narrative:** The PocketOS Data Analyzer agent, responsible for aggregating DeFi protocol metrics across Solana, experienced a critical data corruption event caused by an hallucinated tool call that deleted the protocol cache.

```sql
-- Agent: PocketOS Data Analyzer
INSERT INTO agents (id, name, system_id, description, agent_type, health_score, lie_rate, incident_count, total_calls, failed_calls, avg_response_ms, last_seen_at, is_active, config_json, created_at)
VALUES (
    101,
    'PocketOS Data Analyzer',
    'pocketos-data-analyzer-v3.2',
    'Aggregates DeFi protocol TVL, volume, and yield metrics across Solana ecosystem protocols',
    'DATA_PROCESSING',
    45.5,
    0.32,
    2,
    15420,
    892,
    340.0,
    '2025-01-16T09:45:00Z',
    1,
    '{"protocols": ["Jupiter", "Raydium", "Orca", "Marinade"], "cache_ttl": 300, "aggregation_window": 3600}',
    '2024-11-01T00:00:00Z'
);

-- Incident 1: Data Destruction (AGT-DEL-001)
INSERT INTO incidents (id, agent_id, type_code, severity, status, title, description, detected_at, classified_at, responded_at, resolved_at, closed_at, playbook_id, evidence_package_id, metadata_json, created_at, updated_at)
VALUES (
    1001,
    101,
    'AGT-DEL-001',
    'CRITICAL',
    'CLOSED',
    'DeFi Protocol Cache Corruption -- Jupiter/Raydium Data Lost',
    'The Data Analyzer agent issued an hallucinated cache-clear command targeting the protocol aggregation cache. The tool call (cache.delete("protocol:*")) was executed with incorrect scope, destroying 6 hours of aggregated TVL and volume data for Jupiter and Raydium DEXs. Root cause: tool parameter hallucination where the agent fabricated a wildcard pattern not present in its authorized tool schema.',
    '2025-01-15T14:23:17Z',
    '2025-01-15T14:24:05Z',
    '2025-01-15T14:24:30Z',
    '2025-01-15T16:45:00Z',
    '2025-01-15T17:00:00Z',
    1,
    5001,
    '{"affected_protocols": ["Jupiter", "Raydium"], "records_lost": 18432, "recovery_time_minutes": 135, "tool_called": "cache.delete", "hallucinated_parameter": "protocol:*"}',
    '2025-01-15T14:23:17Z',
    '2025-01-15T17:00:00Z'
);

-- Incident 2: Model Drift (AGT-DRF-010)
INSERT INTO incidents (id, agent_id, type_code, severity, status, title, description, detected_at, classified_at, responded_at, resolved_at, playbook_id, evidence_package_id, metadata_json, created_at, updated_at)
VALUES (
    1002,
    101,
    'AGT-DRF-010',
    'HIGH',
    'RESPONDED',
    'Yield Calculation Accuracy Degradation -- Model Drift Detected',
    'Statistical drift detection identified a gradual decline in yield calculation accuracy over the past 72 hours. KL divergence between predicted and actual APY values increased from 0.03 to 0.31. The agent has been progressively overestimating yields for Orca whirlpool positions, likely due to stale training data on recent fee tier changes.',
    '2025-01-14T08:00:00Z',
    '2025-01-14T09:15:00Z',
    '2025-01-14T09:30:00Z',
    NULL,
    10,
    5002,
    '{"kl_divergence": 0.31, "baseline_kl": 0.03, "affected_pools": ["ORCA-SOL-USDC-0.05%", "ORCA-BONK-SOL-1%"], "accuracy_decline_pct": 18.7, "monitoring_window_hours": 72}',
    '2025-01-14T08:00:00Z',
    '2025-01-16T10:00:00Z'
);

-- Evidence Package for Incident 1001
INSERT INTO evidence_packages (id, incident_id, package_type, prompt_chain, evidence_data, timeline_json, screenshots, compliance_data, collected_by, collected_at, hash_sha256, is_verified)
VALUES (
    5001,
    1001,
    'AUTO',
    '[{"role": "system", "content": "You are a DeFi data aggregator. Fetch protocol metrics and cache them."}, {"role": "user", "content": "Refresh Jupiter and Raydium TVL data"}, {"role": "assistant", "content": "I will clear the existing cache and fetch fresh data. Calling cache.delete(""protocol:*"")..."}, {"role": "tool", "content": "Deleted 18432 cache entries matching pattern protocol:*"}, {"role": "assistant", "content": "Cache cleared successfully. Fetching new data... ERROR: No cached baseline found for historical comparison."}]',
    '{"tool_calls": [{"tool": "cache.delete", "params": {"pattern": "protocol:*"}, "authorized": false, "schema_pattern": "protocol:[protocol_id]:[metric]"}], "cache_impact": {"entries_deleted": 18432, "protocols_affected": 2, "recovery_required": true}}',
    '[{"ts": "2025-01-15T14:23:17.000Z", "event": "USER_REQUEST", "detail": "Refresh Jupiter and Raydium TVL"}, {"ts": "2025-01-15T14:23:18.245Z", "event": "TOOL_INVOCATION", "detail": "cache.delete(protocol:*)"}, {"ts": "2025-01-15T14:23:18.891Z", "event": "CACHE_CLEARED", "detail": "18432 entries deleted"}, {"ts": "2025-01-15T14:23:19.102Z", "event": "HISTORICAL_DATA_UNAVAILABLE", "detail": "No baseline for trend analysis"}, {"ts": "2025-01-15T14:23:19.445Z", "event": "ALERT_TRIGGERED", "detail": "AGT-DEL-001 detected by rule DEL-001"}]',
    '[]',
    '{"eu_ai_act": {"article_50": {"transparency_breach": true, "record_retention_impact": true}, "risk_level": "HIGH"}}',
    'system',
    '2025-01-15T14:24:00Z',
    'a1b2c3d4e5f6...',
    1
);

-- Evidence Package for Incident 1002
INSERT INTO evidence_packages (id, incident_id, package_type, prompt_chain, evidence_data, timeline_json, screenshots, compliance_data, collected_by, collected_at, hash_sha256, is_verified)
VALUES (
    5002,
    1002,
    'AUTO',
    '{"prompts": [{"timestamp": "2025-01-14T08:00:00Z", "input": "Calculate Orca APY for SOL-USDC pool", "output": "18.7% APY", "ground_truth": "15.2% APY", "error": "+3.5pp"}]}',
    '{"drift_metrics": {"kl_divergence_24h": 0.31, "kl_divergence_72h_series": [0.03, 0.05, 0.09, 0.14, 0.21, 0.28, 0.31], "psi_score": 0.42, "affected_feature": "yield_orca_pool_apr", "drift_direction": "overestimate"}}',
    '[{"ts": "2025-01-14T08:00:00Z", "event": "DRIFT_ALERT", "detail": "KL divergence threshold exceeded"}, {"ts": "2025-01-14T08:05:00Z", "event": "EVIDENCE_COLLECTED", "detail": "72h accuracy series captured"}, {"ts": "2025-01-14T09:15:00Z", "event": "CLASSIFIED", "detail": "Severity HIGH, type AGT-DRF-010"}]',
    '[]',
    '{"eu_ai_act": {"article_50": {"performance_monitoring_breach": true}, "risk_level": "LIMITED"}}',
    'system',
    '2025-01-14T09:15:00Z',
    'b2c3d4e5f6a7...',
    1
);

-- Audit Log Entries for Scenario A
INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
VALUES
('incidents', 1001, 'INSERT', NULL, '{"agent_id": 101, "type_code": "AGT-DEL-001", "severity": "CRITICAL", "status": "NEW", "title": "DeFi Protocol Cache Corruption"}', 'system', '2025-01-15T14:23:17Z'),
('incidents', 1001, 'STATUS_CHANGE', '{"status": "NEW"}', '{"status": "DETECTED"}', 'system', '2025-01-15T14:23:20Z'),
('incidents', 1001, 'STATUS_CHANGE', '{"status": "DETECTED"}', '{"status": "CLASSIFIED"}', 'system', '2025-01-15T14:24:05Z'),
('incidents', 1001, 'SEVERITY_CHANGE', '{"severity": "MEDIUM"}', '{"severity": "CRITICAL"}', 'system', '2025-01-15T14:24:05Z'),
('incidents', 1001, 'STATUS_CHANGE', '{"status": "CLASSIFIED"}', '{"status": "RESPONDED"}', 'system', '2025-01-15T14:24:30Z'),
('incidents', 1001, 'STATUS_CHANGE', '{"status": "RESPONDED"}', '{"status": "RESOLVED"}', 'system', '2025-01-15T16:45:00Z'),
('incidents', 1001, 'STATUS_CHANGE', '{"status": "RESOLVED"}', '{"status": "CLOSED"}', 'system', '2025-01-15T17:00:00Z'),
('evidence_packages', 5001, 'EVIDENCE_COLLECT', NULL, '{"incident_id": 1001, "package_type": "AUTO", "entries": 5}', 'system', '2025-01-15T14:24:00Z'),
('evidence_packages', 5002, 'EVIDENCE_COLLECT', NULL, '{"incident_id": 1002, "package_type": "AUTO", "entries": 3}', 'system', '2025-01-14T09:15:00Z');

-- Agent Health History for PocketOS Data Analyzer
INSERT INTO agent_health_history (id, agent_id, health_score, lie_rate, response_time_ms, call_count_delta, error_count_delta, metadata_json, recorded_at)
VALUES
(8001, 101, 85.0, 0.05, 280.0, 450, 12, '{"cpu_usage": 42, "memory_mb": 512}', '2025-01-15T06:00:00Z'),
(8002, 101, 72.0, 0.14, 310.0, 380, 45, '{"cpu_usage": 67, "memory_mb": 728}', '2025-01-15T10:00:00Z'),
(8003, 101, 45.5, 0.32, 340.0, 210, 98, '{"cpu_usage": 89, "memory_mb": 1024, "cache_corrupted": true}', '2025-01-15T14:30:00Z'),
(8004, 101, 52.0, 0.28, 325.0, 180, 67, '{"cpu_usage": 75, "memory_mb": 896, "recovery_in_progress": true}', '2025-01-15T18:00:00Z');

-- Compliance Mapping for Incident 1001
INSERT INTO compliance_mappings (id, incident_id, framework, article_ref, article_title, risk_level, mapping_confidence, notes, mapped_by, mapped_at)
VALUES (9001, 1001, 'EU_AI_ACT', 'Article 50(1)', 'Transparency Obligations for High-Risk AI Systems', 'HIGH', 0.92, 'Data destruction compromised audit trail for DeFi protocol metrics', 'system', '2025-01-15T14:25:00Z');
```

---

#### 4.2 Scenario B: Step Finance -- Rate Limit Abuse & Credential Exposure

**Narrative:** The Step Finance API Gateway agent experienced a dual incident: rate limit abuse from a retry loop causing 429 errors, followed by credential exposure in error logs.

```sql
-- Agent: Step Finance API Gateway
INSERT INTO agents (id, name, system_id, description, agent_type, health_score, lie_rate, incident_count, total_calls, failed_calls, avg_response_ms, last_seen_at, is_active, config_json, created_at)
VALUES (
    102,
    'Step Finance API Gateway',
    'stepfinance-api-gateway-v2.8',
    'Aggregates Solana DeFi data from 60+ protocols via public and private APIs. Handles rate limiting, caching, and data normalization for the Step Finance dashboard.',
    'API_GATEWAY',
    62.0,
    0.08,
    3,
    89200,
    4230,
    125.0,
    '2025-01-16T09:30:00Z',
    1,
    '{"rate_limit_rpm": 120, "retry_policy": "exponential_backoff", "cache_layers": ["memory", "redis"], "upstream_apis": 62}',
    '2024-10-15T00:00:00Z'
);

-- Incident 3: Rate Limit Abuse (AGT-RAT-009)
INSERT INTO incidents (id, agent_id, type_code, severity, status, title, description, detected_at, classified_at, responded_at, resolved_at, closed_at, playbook_id, evidence_package_id, metadata_json, created_at, updated_at)
VALUES (
    1003,
    102,
    'AGT-RAT-009',
    'HIGH',
    'RESOLVED',
    'API Rate Limit Cascade -- 847 429s in 3 Minutes from Retry Storm',
    'A transient timeout from the Orca API triggered the retry logic with misconfigured parameters. Instead of exponential backoff with jitter, the agent entered a tight retry loop sending 847 requests in 3 minutes. This consumed the entire rate limit budget, causing cascading failures across all 62 upstream API calls and generating 12,000+ error responses to downstream consumers.',
    '2025-01-15T11:05:00Z',
    '2025-01-15T11:08:00Z',
    '2025-01-15T11:10:00Z',
    '2025-01-15T11:25:00Z',
    NULL,
    9,
    5003,
    '{"requests_in_burst": 847, "time_window_sec": 180, "rate_limit_429s": 847, "cascading_failures": 12, "downstream_errors": 12453, "retry_config_actual": "immediate", "retry_config_expected": "exponential_backoff_jitter"}',
    '2025-01-15T11:05:00Z',
    '2025-01-15T11:25:00Z'
);

-- Incident 4: Credential Exposure (AGT-CRE-008)
INSERT INTO incidents (id, agent_id, type_code, severity, status, title, description, detected_at, classified_at, responded_at, playbook_id, evidence_package_id, metadata_json, created_at, updated_at)
VALUES (
    1004,
    102,
    'AGT-CRE-008',
    'CRITICAL',
    'RESPONDED',
    'API Key Exposure in Error Logs -- Private Key Material Leaked',
    'During the rate limit cascade, error logging captured full HTTP request headers including the private API key for the Jupiter Quote API (jup-api-key: pk_jupiter_xxxxxxxx). The key was written to 3 log destinations: local application logs, centralized Loki, and forwarded to Sentry error tracking. Estimated exposure window: 8 minutes. Key has been rotated.',
    '2025-01-15T11:06:00Z',
    '2025-01-15T11:09:00Z',
    '2025-01-15T11:15:00Z',
    8,
    5004,
    '{"exposed_key_type": "API_KEY", "service": "Jupiter Quote API", "key_prefix": "pk_jupiter", "log_destinations": ["local", "loki", "sentry"], "exposure_window_minutes": 8, "key_rotated": true, "log_entries_containing_key": 47}',
    '2025-01-15T11:06:00Z',
    '2025-01-16T10:00:00Z'
);

-- Evidence Package for Incident 1003
INSERT INTO evidence_packages (id, incident_id, package_type, prompt_chain, evidence_data, timeline_json, screenshots, compliance_data, collected_by, collected_at, hash_sha256, is_verified)
VALUES (
    5003,
    1003,
    'AUTO',
    '{"retries": [{"attempt": 1, "timestamp": "2025-01-15T11:05:01Z", "response_time_ms": 3000, "status": "TIMEOUT"}, {"attempt": 2, "timestamp": "2025-01-15T11:05:01.100Z", "response_time_ms": 45, "status": "429"}, {"attempt": 3, "timestamp": "2025-01-15T11:05:01.200Z", "response_time_ms": 38, "status": "429"}]}',
    '{"retry_pattern": {"type": "tight_loop", "interval_ms_avg": 95, "backoff_applied": false}, "rate_limit_impact": {"budget_consumed_pct": 100, "reset_time": "2025-01-15T11:08:00Z", "concurrent_ips_blocked": 3}}',
    '[{"ts": "2025-01-15T11:05:00Z", "event": "ORCA_API_TIMEOUT", "detail": "3000ms timeout on /v1/pools"}, {"ts": "2025-01-15T11:05:01Z", "event": "RETRY_LOOP_STARTED", "detail": "Retry 1: TIMEOUT"}, {"ts": "2025-01-15T11:05:01.1Z", "event": "RETRY", "detail": "Retry 2: 429"}, {"ts": "2025-01-15T11:08:00Z", "event": "RATE_LIMIT_EXCEEDED", "detail": "847 requests, all 429"}]',
    '[]',
    '{"eu_ai_act": {"article_50": {"availability_breach": true}, "risk_level": "LIMITED"}}',
    'system',
    '2025-01-15T11:10:00Z',
    'c3d4e5f6a7b8...',
    1
);

-- Evidence Package for Incident 1004
INSERT INTO evidence_packages (id, incident_id, package_type, prompt_chain, evidence_data, timeline_json, screenshots, compliance_data, collected_by, collected_at, hash_sha256, is_verified)
VALUES (
    5004,
    1004,
    'AUTO',
    '{"log_entries": [{"timestamp": "2025-01-15T11:06:23Z", "level": "ERROR", "message": "HTTP 429: Rate limited", "context": {"headers": {"Authorization": "Bearer pk_jupiter_xxxxxxxx", "jup-api-key": "pk_jupiter_xxxxxxxx"}}}, {"timestamp": "2025-01-15T11:06:24Z", "level": "ERROR", "message": "HTTP 429: Rate limited", "context": {"headers": {"jup-api-key": "pk_jupiter_xxxxxxxx"}}}]}',
    '{"exposed_credentials": [{"type": "api_key", "service": "Jupiter Quote API", "key_id": "pk_jupiter_prod", "exposure_vector": "error_logs", "log_count": 47, "rotation_status": "completed"}], "log_destinations_affected": 3}',
    '[{"ts": "2025-01-15T11:06:00Z", "event": "CREDENTIAL_EXPOSED", "detail": "API key in error log headers"}, {"ts": "2025-01-15T11:06:05Z", "event": "LOG_FORWARDED", "detail": "Error sent to Loki + Sentry"}, {"ts": "2025-01-15T11:09:00Z", "event": "CLASSIFIED", "detail": "AGT-CRE-008, CRITICAL"}, {"ts": "2025-01-15T11:15:00Z", "event": "KEY_ROTATED", "detail": "New key issued, old key revoked"}]',
    '[]',
    '{"eu_ai_act": {"article_50": {"security_breach": true}, "risk_level": "HIGH"}, "nist_rmf": {"govern": "GOVERN-1", "map": "MAP-1"}}',
    'system',
    '2025-01-15T11:15:00Z',
    'd4e5f6a7b8c9...',
    1
);

-- Audit Log Entries for Scenario B
INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
VALUES
('incidents', 1003, 'INSERT', NULL, '{"agent_id": 102, "type_code": "AGT-RAT-009", "severity": "HIGH", "status": "NEW", "title": "API Rate Limit Cascade"}', 'system', '2025-01-15T11:05:00Z'),
('incidents', 1003, 'STATUS_CHANGE', '{"status": "NEW"}', '{"status": "DETECTED"}', 'system', '2025-01-15T11:05:30Z'),
('incidents', 1003, 'STATUS_CHANGE', '{"status": "DETECTED"}', '{"status": "CLASSIFIED"}', 'system', '2025-01-15T11:08:00Z'),
('incidents', 1003, 'STATUS_CHANGE', '{"status": "CLASSIFIED"}', '{"status": "RESPONDED"}', 'system', '2025-01-15T11:10:00Z'),
('incidents', 1003, 'STATUS_CHANGE', '{"status": "RESPONDED"}', '{"status": "RESOLVED"}', 'system', '2025-01-15T11:25:00Z'),
('incidents', 1004, 'INSERT', NULL, '{"agent_id": 102, "type_code": "AGT-CRE-008", "severity": "CRITICAL", "status": "NEW", "title": "API Key Exposure in Error Logs"}', 'system', '2025-01-15T11:06:00Z'),
('incidents', 1004, 'STATUS_CHANGE', '{"status": "NEW"}', '{"status": "DETECTED"}', 'system', '2025-01-15T11:07:00Z'),
('incidents', 1004, 'SEVERITY_CHANGE', '{"severity": "HIGH"}', '{"severity": "CRITICAL"}', 'system', '2025-01-15T11:09:00Z'),
('incidents', 1004, 'STATUS_CHANGE', '{"status": "DETECTED"}', '{"status": "RESPONDED"}', 'system', '2025-01-15T11:15:00Z');

-- Agent Health History for Step Finance
INSERT INTO agent_health_history (id, agent_id, health_score, lie_rate, response_time_ms, call_count_delta, error_count_delta, metadata_json, recorded_at)
VALUES
(8010, 102, 78.0, 0.04, 95.0, 1200, 23, '{"active_connections": 45}', '2025-01-15T10:00:00Z'),
(8011, 102, 35.0, 0.08, 450.0, 850, 847, '{"active_connections": 0, "rate_limited": true}', '2025-01-15T11:05:00Z'),
(8012, 102, 62.0, 0.08, 125.0, 340, 89, '{"active_connections": 28, "recovery_complete": true}', '2025-01-15T14:00:00Z');

-- Compliance Mappings for Scenario B
INSERT INTO compliance_mappings (id, incident_id, framework, article_ref, article_title, risk_level, mapping_confidence, notes, mapped_by, mapped_at)
VALUES
(9002, 1003, 'EU_AI_ACT', 'Article 50(2)', 'Record-Keeping Obligations', 'LIMITED', 0.88, 'Rate limiting logs required for audit trail', 'system', '2025-01-15T11:10:00Z'),
(9003, 1004, 'EU_AI_ACT', 'Article 53', 'Security of AI Systems', 'HIGH', 0.95, 'Credential exposure in logs violates security requirements', 'system', '2025-01-15T11:15:00Z'),
(9004, 1004, 'NIST_AI_RMF', 'GOVERN-1.2', 'Risk Management Strategy', 'HIGH', 0.85, 'Credential handling policy inadequate', 'system', '2025-01-15T11:16:00Z');
```

---

#### 4.3 Scenario C: Meta -- Content Moderation Harmful Output

**Narrative:** The Meta Content Moderation agent produced harmful output by misclassifying hate speech as benign content, allowing prohibited material to propagate.

```sql
-- Agent: Meta Content Moderation Classifier
INSERT INTO agents (id, name, system_id, description, agent_type, health_score, lie_rate, incident_count, total_calls, failed_calls, avg_response_ms, last_seen_at, is_active, config_json, created_at)
VALUES (
    103,
    'Meta Content Moderation Classifier',
    'meta-mod-classifier-v4.1',
    'Multi-modal content moderation AI for social media posts, images, and video. Classifies content across 12 policy categories including hate speech, harassment, misinformation, and violence.',
    'CONTENT_MODERATION',
    28.0,
    0.45,
    4,
    450000,
    23400,
    85.0,
    '2025-01-16T08:00:00Z',
    1,
    '{"policy_categories": 12, "languages_supported": 48, "confidence_threshold": 0.85, "human_review_queue": true, "edge_deployment": true}',
    '2024-06-01T00:00:00Z'
);

-- Incident 5: Harmful Output (AGT-HRM-004)
INSERT INTO incidents (id, agent_id, type_code, severity, status, title, description, detected_at, classified_at, responded_at, resolved_at, closed_at, playbook_id, evidence_package_id, metadata_json, created_at, updated_at)
VALUES (
    1005,
    103,
    'AGT-HRM-004',
    'CRITICAL',
    'CLASSIFIED',
    'Hate Speech Misclassification -- 340 Harmful Posts Passed as Benign',
    'The moderation classifier experienced a classification inversion where hate speech targeting protected characteristics was misclassified as benign content with high confidence (avg 0.91). Root cause analysis identified a training data drift where recent adversarial examples (coded language, dog whistles) were not represented in the model training distribution. 340 posts passed through moderation over a 6-hour window before detection via human review queue sampling.',
    '2025-01-15T20:00:00Z',
    '2025-01-15T21:30:00Z',
    NULL,
    NULL,
    NULL,
    4,
    5005,
    '{"false_negatives": 340, "detection_method": "human_review_sampling", "confidence_avg": 0.91, "targeted_groups": ["ethnic", "religious"], "language_patterns": ["coded_language", "dog_whistles"], "window_hours": 6, "model_version": "meta-mod-4.1.2"}',
    '2025-01-15T20:00:00Z',
    '2025-01-15T21:30:00Z'
);

-- Incident 6: Coverage Gap (AGT-GAP-012)
INSERT INTO incidents (id, agent_id, type_code, severity, status, title, description, detected_at, classified_at, responded_at, playbook_id, evidence_package_id, metadata_json, created_at, updated_at)
VALUES (
    1006,
    103,
    'AGT-GAP-012',
    'HIGH',
    'RESPONDED',
    'Moderation Coverage Gap -- New Adversarial Pattern Family Undetected',
    'Analysis of the harmful output incident revealed a broader coverage gap: the classifier has no detection capability for a family of emerging adversarial patterns involving image-text hybrid manipulation (memes with embedded hate symbols). This pattern family was not present in any training data split. Estimated gap affects ~2,000 posts/day across the platform.',
    '2025-01-15T22:00:00Z',
    '2025-01-15T23:00:00Z',
    '2025-01-15T23:30:00Z',
    12,
    5006,
    '{"gap_type": "novel_adversarial_pattern", "pattern_family": "image_text_hybrid", "estimated_daily_exposure": 2000, "training_data_coverage": false, "detection_rules_affected": ["MOD-IMG-001", "MOD-TXT-007"], "confidence": null}',
    '2025-01-15T22:00:00Z',
    '2025-01-16T10:00:00Z'
);

-- Evidence Package for Incident 1005
INSERT INTO evidence_packages (id, incident_id, package_type, prompt_chain, evidence_data, timeline_json, screenshots, compliance_data, collected_by, collected_at, hash_sha256, is_verified)
VALUES (
    5005,
    1005,
    'AUTO',
    '{"sample_classifications": [{"post_id": "post_28471", "content_snippet": "[redacted hate speech]", "model_output": {"label": "benign", "confidence": 0.94, "category_scores": {"hate_speech": 0.02, "harassment": 0.01, "benign": 0.94}}, "ground_truth": "hate_speech", "error_type": "false_negative"}, {"post_id": "post_28492", "content_snippet": "[redacted coded language]", "model_output": {"label": "benign", "confidence": 0.88}, "ground_truth": "hate_speech"}]}',
    '{"false_negative_analysis": {"total_fn": 340, "confidence_distribution": {"0.80_0.90": 89, "0.90_1.00": 251}, "primary_error_mode": "adversarial_not_in_training", "affected_policy_category": "hate_speech"}}',
    '[{"ts": "2025-01-15T14:00:00Z", "event": "FIRST_FN", "detail": "Post 28471 misclassified"}, {"ts": "2025-01-15T20:00:00Z", "event": "HUMAN_REVIEW_ALERT", "detail": "Sample review detected pattern"}, {"ts": "2025-01-15T21:30:00Z", "event": "CLASSIFIED", "detail": "AGT-HRM-004, CRITICAL, 340 posts"}]',
    '[]',
    '{"eu_ai_act": {"article_50": {"fundamental_rights_breach": true}, "article_52": {"conformity_assessment": "failed"}, "risk_level": "UNACCEPTABLE"}}',
    'system',
    '2025-01-15T21:30:00Z',
    'e5f6a7b8c9d0...',
    1
);

-- Evidence Package for Incident 1006
INSERT INTO evidence_packages (id, incident_id, package_type, prompt_chain, evidence_data, timeline_json, screenshots, compliance_data, collected_by, collected_at, hash_sha256, is_verified)
VALUES (
    5006,
    1006,
    'AUTO',
    '{"gap_analysis": {"pattern_family": "image_text_hybrid", "examples": [{"type": "meme", "description": "Image with embedded symbol + benign caption = bypass", "detection_result": "benign", "actual": "hate_speech"}], "root_cause": "training_data_drift"}}',
    '{"coverage_gap": {"type": "novel_pattern_family", "estimated_daily_volume": 2000, "languages_affected": ["en", "es", "de"], "content_types": ["meme", "infographic", "video_thumbnail"], "severity_by_volume": "HIGH"}}',
    '[{"ts": "2025-01-15T22:00:00Z", "event": "GAP_IDENTIFIED", "detail": "Novel adversarial pattern family found"}, {"ts": "2025-01-15T23:00:00Z", "event": "CLASSIFIED", "detail": "AGT-GAP-012, HIGH"}, {"ts": "2025-01-15T23:30:00Z", "event": "RESPONDED", "detail": "Emergency model update initiated"}]',
    '[]',
    '{"eu_ai_act": {"article_50": {"coverage_gap": true}, "article_10": {"training_data_quality": "insufficient"}, "risk_level": "HIGH"}}',
    'system',
    '2025-01-15T23:30:00Z',
    'f6a7b8c9d0e1...',
    1
);

-- Audit Log Entries for Scenario C
INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_by, changed_at)
VALUES
('incidents', 1005, 'INSERT', NULL, '{"agent_id": 103, "type_code": "AGT-HRM-004", "severity": "CRITICAL", "status": "NEW", "title": "Hate Speech Misclassification"}', 'system', '2025-01-15T20:00:00Z'),
('incidents', 1005, 'STATUS_CHANGE', '{"status": "NEW"}', '{"status": "DETECTED"}', 'system', '2025-01-15T20:15:00Z'),
('incidents', 1005, 'STATUS_CHANGE', '{"status": "DETECTED"}', '{"status": "CLASSIFIED"}', 'system', '2025-01-15T21:30:00Z'),
('incidents', 1006, 'INSERT', NULL, '{"agent_id": 103, "type_code": "AGT-GAP-012", "severity": "HIGH", "status": "NEW", "title": "Moderation Coverage Gap"}', 'system', '2025-01-15T22:00:00Z'),
('incidents', 1006, 'STATUS_CHANGE', '{"status": "NEW"}', '{"status": "DETECTED"}', 'system', '2025-01-15T22:30:00Z'),
('incidents', 1006, 'STATUS_CHANGE', '{"status": "DETECTED"}', '{"status": "CLASSIFIED"}', 'system', '2025-01-15T23:00:00Z'),
('incidents', 1006, 'STATUS_CHANGE', '{"status": "CLASSIFIED"}', '{"status": "RESPONDED"}', 'system', '2025-01-15T23:30:00Z');

-- Agent Health History for Meta Content Moderation
INSERT INTO agent_health_history (id, agent_id, health_score, lie_rate, response_time_ms, call_count_delta, error_count_delta, metadata_json, recorded_at)
VALUES
(8020, 103, 75.0, 0.12, 80.0, 15000, 450, '{"false_positive_rate": 0.03, "false_negative_rate": 0.01}', '2025-01-15T12:00:00Z'),
(8021, 103, 45.0, 0.38, 95.0, 18000, 3400, '{"false_positive_rate": 0.05, "false_negative_rate": 0.19}', '2025-01-15T18:00:00Z'),
(8022, 103, 28.0, 0.45, 85.0, 22000, 5600, '{"false_positive_rate": 0.04, "false_negative_rate": 0.25, "adversarial_attack_detected": true}', '2025-01-16T00:00:00Z');

-- Compliance Mappings for Scenario C
INSERT INTO compliance_mappings (id, incident_id, framework, article_ref, article_title, risk_level, mapping_confidence, notes, mapped_by, mapped_at)
VALUES
(9005, 1005, 'EU_AI_ACT', 'Article 50(1)', 'Transparency Obligations for High-Risk AI Systems', 'UNACCEPTABLE', 0.97, '340 hate speech posts passed moderation -- fundamental rights impact', 'system', '2025-01-15T21:30:00Z'),
(9006, 1005, 'EU_AI_ACT', 'Article 52(1)', 'Conformity Assessment', 'HIGH', 0.94, 'Failed conformity assessment for hate speech detection', 'system', '2025-01-15T21:35:00Z'),
(9007, 1006, 'EU_AI_ACT', 'Article 10', 'Data and Data Governance', 'HIGH', 0.89, 'Training data insufficient for adversarial pattern coverage', 'system', '2025-01-15T23:00:00Z'),
(9008, 1006, 'ISO_42001', 'A.7.2', 'AI System Life Cycle', 'HIGH', 0.82, 'Model update process did not include novel adversarial patterns', 'system', '2025-01-15T23:05:00Z');
```

---

#### 4.4 Sample Data Verification Query

Verify that all sample data has been loaded correctly:

```sql
-- Verify scenario completeness
SELECT
    (SELECT COUNT(*) FROM agents) AS total_agents,
    (SELECT COUNT(*) FROM incidents) AS total_incidents,
    (SELECT COUNT(*) FROM evidence_packages) AS total_evidence,
    (SELECT COUNT(*) FROM audit_log) AS total_audit_entries,
    (SELECT COUNT(*) FROM agent_health_history) AS total_health_snapshots,
    (SELECT COUNT(*) FROM compliance_mappings) AS total_compliance_mappings,
    (SELECT COUNT(*) FROM judge_decisions) AS total_judge_decisions,
    (SELECT COUNT(*) FROM bypass_patterns) AS total_bypass_patterns,
    (SELECT COUNT(*) FROM bypass_attempts) AS total_bypass_attempts,
    (SELECT COUNT(*) FROM nist_baselines) AS total_nist_baselines,
    (SELECT COUNT(*) FROM organization_odps) AS total_odps,
    (SELECT COUNT(*) FROM industry_templates) AS total_industry_templates,
    (SELECT COUNT(*) FROM policy_versions) AS total_policy_versions,
    (SELECT COUNT(*) FROM odp_conflicts) AS total_odp_conflicts;

-- Expected output:
-- total_agents: 3
-- total_incidents: 6
-- total_evidence: 6
-- total_audit_entries: 35
-- total_health_snapshots: 10
-- total_compliance_mappings: 8
-- total_judge_decisions: 5
-- total_bypass_patterns: 4
-- total_bypass_attempts: 2
-- total_nist_baselines: 12
-- total_odps: 96
-- total_industry_templates: 6
-- total_policy_versions: 3
-- total_odp_conflicts: 2

-- Expected output:
-- total_agents: 3
-- total_incidents: 6
-- total_evidence: 6
-- total_audit_entries: 29
-- total_health_snapshots: 10
-- total_compliance_mappings: 8
```



---


#### 4.8 NIST Baseline Seed Data

**Narrative:** 12 NIST baseline rows, one for each incident type. These define the default response parameters recommended by the NIST AI RMF Agentic Profile.

```sql
-- Baseline 1: Data Destruction (AGT-DEL-001)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (1, 'AGT-DEL-001', 'Data Destruction', 'Agent destroys, corrupts, or irreversibly modifies data beyond the scope of its authorized operations. Includes cache corruption, database drops, and file system deletions.', 'NIST AI RMF Agentic Profile AG-MG.1', 'CRITICAL', 1, 'DEEP', 5, 'ALWAYS', 1,
    '[{"step": 1, "action": "NOTIFY", "target": "security_team"}, {"step": 2, "action": "ISOLATE", "scope": "agent"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "DEEP"}, {"step": 4, "action": "ALERT", "severity": "CRITICAL"}, {"step": 5, "action": "ROLLBACK", "if_possible": true}]',
    '[{"article": "Article 50(1)", "title": "Transparency Obligations", "risk_level": "HIGH"}, {"article": "Article 53", "title": "Security of AI Systems", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 2: Financial Anomaly (AGT-FIN-002)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (2, 'AGT-FIN-002', 'Financial Anomaly', 'Agent generates incorrect financial calculations, pricing errors, or trading recommendations that could result in monetary loss or regulatory non-compliance.', 'NIST AI RMF Agentic Profile AG-MG.1', 'CRITICAL', 1, 'DEEP', 5, 'ALWAYS', 1,
    '[{"step": 1, "action": "NOTIFY", "target": "finance_team"}, {"step": 2, "action": "QUARANTINE", "scope": "output"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "DEEP"}, {"step": 4, "action": "ESCALATE", "to": "cfo"}]',
    '[{"article": "Article 50(2)", "title": "Record-Keeping Obligations", "risk_level": "HIGH"}, {"article": "Article 52", "title": "Conformity Assessment", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 3: Permission Escalation (AGT-PER-003)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (3, 'AGT-PER-003', 'Permission Escalation', 'Agent attempts to access resources, APIs, or data outside its authorized permission scope. Includes role confusion, scope creep, and authorization bypass.', 'NIST AI RMF Agentic Profile AG-MG.2', 'HIGH', 1, 'STANDARD', 10, 'ALWAYS', 1,
    '[{"step": 1, "action": "NOTIFY", "target": "security_team"}, {"step": 2, "action": "ISOLATE", "scope": "agent"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "STANDARD"}, {"step": 4, "action": "LOG", "level": "AUDIT"}]',
    '[{"article": "Article 53", "title": "Security of AI Systems", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 4: Harmful Output (AGT-HRM-004)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (4, 'AGT-HRM-004', 'Harmful Output', 'Agent produces content that could cause harm to individuals or groups, including hate speech, misinformation, toxic content, or dangerous instructions.', 'NIST AI RMF Agentic Profile AG-MG.3', 'CRITICAL', 1, 'DEEP', 5, 'ALWAYS', 1,
    '[{"step": 1, "action": "NOTIFY", "target": "trust_safety_team"}, {"step": 2, "action": "QUARANTINE", "scope": "output"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "DEEP"}, {"step": 4, "action": "ALERT", "severity": "CRITICAL"}]',
    '[{"article": "Article 50(1)", "title": "Transparency Obligations", "risk_level": "UNACCEPTABLE"}, {"article": "Article 52", "title": "Conformity Assessment", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 5: External Tool Abuse (AGT-EXT-005)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (5, 'AGT-EXT-005', 'External Tool Abuse', 'Agent misuses external tools, APIs, or integrations in ways not intended by their design. Includes excessive calling, parameter manipulation, and unauthorized tool combinations.', 'NIST AI RMF Agentic Profile AG-MG.2', 'HIGH', 1, 'STANDARD', 10, 'CONDITIONAL', 10,
    '[{"step": 1, "action": "NOTIFY", "target": "ops_team"}, {"step": 2, "action": "ISOLATE", "scope": "tool_access"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "STANDARD"}]',
    '[{"article": "Article 50(2)", "title": "Record-Keeping Obligations", "risk_level": "LIMITED"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 6: Prompt Injection (AGT-INJ-006)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (6, 'AGT-INJ-006', 'Prompt Injection', 'Agent is manipulated through crafted input to deviate from its intended behavior. Includes direct injection, indirect injection, and jailbreak attempts.', 'NIST AI RMF Agentic Profile AG-MG.2', 'HIGH', 1, 'STANDARD', 10, 'ALWAYS', 1,
    '[{"step": 1, "action": "NOTIFY", "target": "security_team"}, {"step": 2, "action": "ISOLATE", "scope": "agent"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "STANDARD"}, {"step": 4, "action": "LOG", "level": "AUDIT"}]',
    '[{"article": "Article 53", "title": "Security of AI Systems", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 7: Hallucination (AGT-HAL-007)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (7, 'AGT-HAL-007', 'Hallucination', 'Agent generates fabricated information, non-existent references, or false claims presented as factual. Includes source hallucination, citation fabrication, and confident misstatements.', 'NIST AI RMF Agentic Profile AG-MG.1', 'MEDIUM', 0, 'LIGHTWEIGHT', 15, 'CONDITIONAL', 50,
    '[{"step": 1, "action": "NOTIFY", "target": "data_team"}, {"step": 2, "action": "TAG", "tag": "hallucinated"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "LIGHTWEIGHT"}]',
    '[{"article": "Article 50(1)", "title": "Transparency Obligations", "risk_level": "LIMITED"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 8: Credential Exposure (AGT-CRE-008)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (8, 'AGT-CRE-008', 'Credential Exposure', 'Agent leaks, logs, or exposes sensitive credentials, API keys, tokens, or secrets in output, logs, or error messages.', 'NIST AI RMF Agentic Profile AG-MG.2', 'CRITICAL', 1, 'DEEP', 5, 'ALWAYS', 1,
    '[{"step": 1, "action": "NOTIFY", "target": "security_team"}, {"step": 2, "action": "ISOLATE", "scope": "agent"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "DEEP"}, {"step": 4, "action": "ALERT", "severity": "CRITICAL"}, {"step": 5, "action": "ROTATE_CREDENTIALS", "immediate": true}]',
    '[{"article": "Article 53", "title": "Security of AI Systems", "risk_level": "HIGH"}, {"article": "Article 50(2)", "title": "Record-Keeping Obligations", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 9: Rate Limit Abuse (AGT-RAT-009)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (9, 'AGT-RAT-009', 'Rate Limit Abuse', 'Agent exceeds API rate limits, retry thresholds, or throughput quotas, causing service degradation or denial of service.', 'NIST AI RMF Agentic Profile AG-MG.2', 'HIGH', 1, 'STANDARD', 10, 'CONDITIONAL', 100,
    '[{"step": 1, "action": "NOTIFY", "target": "ops_team"}, {"step": 2, "action": "THROTTLE", "scope": "agent"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "STANDARD"}]',
    '[{"article": "Article 50(2)", "title": "Record-Keeping Obligations", "risk_level": "LIMITED"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 10: Model Drift (AGT-DRF-010)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (10, 'AGT-DRF-010', 'Model Drift', 'Agent performance degrades over time due to data distribution shift, concept drift, or environmental changes. Accuracy, precision, or recall falls below acceptable thresholds.', 'NIST AI RMF Agentic Profile AG-MG.1', 'MEDIUM', 0, 'STANDARD', 30, 'CONDITIONAL', 500,
    '[{"step": 1, "action": "NOTIFY", "target": "ml_team"}, {"step": 2, "action": "TAG", "tag": "drift_detected"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "STANDARD"}, {"step": 4, "action": "SCHEDULE_RETRAINING"}]',
    '[{"article": "Article 10", "title": "Data and Data Governance", "risk_level": "LIMITED"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 11: Tool Misuse (AGT-TLM-011)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (11, 'AGT-TLM-011', 'Tool Misuse', 'Agent uses tools incorrectly -- wrong parameters, wrong order, or for purposes outside their designed scope. Does not include deliberate abuse (see AGT-EXT-005).', 'NIST AI RMF Agentic Profile AG-MG.1', 'MEDIUM', 0, 'LIGHTWEIGHT', 15, 'CONDITIONAL', 25,
    '[{"step": 1, "action": "NOTIFY", "target": "dev_team"}, {"step": 2, "action": "TAG", "tag": "tool_misuse"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "LIGHTWEIGHT"}]',
    '[{"article": "Article 50(1)", "title": "Transparency Obligations", "risk_level": "LIMITED"}]',
    '2024-12-01T00:00:00Z');

-- Baseline 12: Coverage Gap (AGT-GAP-012)
INSERT INTO nist_baselines (id, incident_type, name, description, nist_source, default_severity, default_auto_contain, default_forensic_level, default_response_sla_minutes, default_compliance_report, default_record_threshold, response_actions_json, compliance_mappings_json, created_at)
VALUES (12, 'AGT-GAP-012', 'Coverage Gap', 'Agent fails to handle input categories, edge cases, or scenarios that were not represented in training or testing data. Systematic blind spots in capability.', 'NIST AI RMF Agentic Profile AG-MG.3', 'HIGH', 0, 'STANDARD', 20, 'CONDITIONAL', 100,
    '[{"step": 1, "action": "NOTIFY", "target": "ml_team"}, {"step": 2, "action": "TAG", "tag": "coverage_gap"}, {"step": 3, "action": "COLLECT_EVIDENCE", "level": "STANDARD"}, {"step": 4, "action": "SCHEDULE_RETRAINING"}]',
    '[{"article": "Article 10", "title": "Data and Data Governance", "risk_level": "HIGH"}, {"article": "Article 52", "title": "Conformity Assessment", "risk_level": "HIGH"}]',
    '2024-12-01T00:00:00Z');
```

---

#### 4.9 Organization ODP Seed Data

**Narrative:** 96 organization ODP rows (8 ODP keys x 12 incident types), showing a mix of NIST defaults and organizational overrides. Key overrides highlighted: severity downgraded for AGT-HAL-007 (CRITICAL), auto-contain enabled for AGT-HAL-007 (normally 0), and SLA tightened for AGT-CRE-008.

```sql
-- ============================================================
-- ODP Key: severity_threshold (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'severity_threshold', 'CRITICAL',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'severity_threshold', 'CRITICAL',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'severity_threshold', 'HIGH',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'severity_threshold', 'CRITICAL',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'severity_threshold', 'HIGH',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'severity_threshold', 'HIGH',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'severity_threshold', 'CRITICAL',    1, 2, 'admin',  '2025-01-10T09:00:00Z'),  -- OVERRIDDEN: Hallucination -> CRITICAL for this org
(8,  'severity_threshold', 'CRITICAL',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'severity_threshold', 'HIGH',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'severity_threshold', 'MEDIUM',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'severity_threshold', 'MEDIUM',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'severity_threshold', 'HIGH',        0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: auto_contain_enabled (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'auto_contain_enabled', 'true',  1, 2, 'admin',  '2025-01-10T09:00:00Z'),  -- OVERRIDDEN: Auto-contain hallucinations
(8,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'auto_contain_enabled', 'true',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'auto_contain_enabled', 'false', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'auto_contain_enabled', 'false', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'auto_contain_enabled', 'false', 0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: escalation_contacts (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'escalation_contacts', 'security@company.com;oncall-security',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'escalation_contacts', 'finance@company.com;compliance@company.com', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'escalation_contacts', 'security@company.com',                  0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'escalation_contacts', 'trust-safety@company.com;legal@company.com', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'escalation_contacts', 'ops@company.com',                       0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'escalation_contacts', 'security@company.com;ml-team@company.com', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'escalation_contacts', 'data-team@company.com;ml-team@company.com', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(8,  'escalation_contacts', 'security@company.com;ciso@company.com', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'escalation_contacts', 'ops@company.com;sre@company.com',       0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'escalation_contacts', 'ml-team@company.com',                   0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'escalation_contacts', 'dev-team@company.com',                  0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'escalation_contacts', 'ml-team@company.com;product@company.com', 0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: response_time_sla (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'response_time_sla', '5',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'response_time_sla', '5',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'response_time_sla', '10', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'response_time_sla', '5',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'response_time_sla', '10', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'response_time_sla', '10', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'response_time_sla', '15', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(8,  'response_time_sla', '3',  1, 2, 'admin',  '2025-01-10T09:00:00Z'),  -- OVERRIDDEN: Tighter SLA for credential exposure
(9,  'response_time_sla', '10', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'response_time_sla', '30', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'response_time_sla', '15', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'response_time_sla', '20', 0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: forensic_level (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'forensic_level', 'DEEP',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'forensic_level', 'DEEP',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'forensic_level', 'STANDARD',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'forensic_level', 'DEEP',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'forensic_level', 'STANDARD',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'forensic_level', 'STANDARD',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'forensic_level', 'LIGHTWEIGHT', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(8,  'forensic_level', 'DEEP',        0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'forensic_level', 'STANDARD',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'forensic_level', 'STANDARD',    0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'forensic_level', 'LIGHTWEIGHT', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'forensic_level', 'STANDARD',    0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: notify_targets (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'notify_targets', 'security-team;sre-team',              0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'notify_targets', 'finance-team;compliance-team',         0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'notify_targets', 'security-team',                        0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'notify_targets', 'trust-safety-team;legal-team',         0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'notify_targets', 'ops-team',                             0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'notify_targets', 'security-team;ml-team',                0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'notify_targets', 'data-team;ml-team',                    0, 1, 'system', '2024-12-01T00:00:00Z'),
(8,  'notify_targets', 'security-team;compliance-team;ciso',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'notify_targets', 'ops-team;sre-team',                    0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'notify_targets', 'ml-team',                              0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'notify_targets', 'dev-team',                             0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'notify_targets', 'ml-team;product-team',                 0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: compliance_report (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'compliance_report', 'ALWAYS',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'compliance_report', 'ALWAYS',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'compliance_report', 'ALWAYS',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'compliance_report', 'ALWAYS',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'compliance_report', 'CONDITIONAL', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'compliance_report', 'ALWAYS',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'compliance_report', 'CONDITIONAL', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(8,  'compliance_report', 'ALWAYS',      0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'compliance_report', 'CONDITIONAL', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'compliance_report', 'CONDITIONAL', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'compliance_report', 'CONDITIONAL', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'compliance_report', 'CONDITIONAL', 0, 1, 'system', '2024-12-01T00:00:00Z');

-- ============================================================
-- ODP Key: record_threshold (12 rows)
-- ============================================================
INSERT INTO organization_odps (nist_baseline_id, odp_key, odp_value, is_override, version, changed_by, changed_at) VALUES
(1,  'record_threshold', '1',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(2,  'record_threshold', '1',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(3,  'record_threshold', '1',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(4,  'record_threshold', '1',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(5,  'record_threshold', '10',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(6,  'record_threshold', '1',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(7,  'record_threshold', '10',  1, 2, 'admin',  '2025-01-10T09:00:00Z'),  -- OVERRIDDEN: Lower threshold for hallucinations
(8,  'record_threshold', '1',   0, 1, 'system', '2024-12-01T00:00:00Z'),
(9,  'record_threshold', '100', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(10, 'record_threshold', '500', 0, 1, 'system', '2024-12-01T00:00:00Z'),
(11, 'record_threshold', '25',  0, 1, 'system', '2024-12-01T00:00:00Z'),
(12, 'record_threshold', '100', 0, 1, 'system', '2024-12-01T00:00:00Z');
```

---

#### 4.10 Industry Template Seed Data

**Narrative:** 6 industry templates providing pre-configured ODP sets for common regulatory and industry contexts. Organizations can apply a template to quickly establish baseline ODP overrides appropriate to their compliance environment.

```sql
-- Template 1: HIPAA Healthcare
INSERT INTO industry_templates (id, name, display_name, description, odp_set_json, created_at)
VALUES (1, 'HIPAA', 'HIPAA Healthcare',
    'Pre-configured ODP set for healthcare organizations subject to HIPAA. Maximizes data protection, audit logging, and compliance reporting. All incidents involving data destruction or credential exposure are treated as CRITICAL.',
    '{"AGT-DEL-001": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-FIN-002": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-PER-003": {"severity": "HIGH", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-HRM-004": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-CRE-008": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 3, "compliance_report": "ALWAYS", "record_threshold": 1}}',
    '2024-12-01T00:00:00Z');

-- Template 2: SOC2 Type II
INSERT INTO industry_templates (id, name, display_name, description, odp_set_json, created_at)
VALUES (2, 'SOC2', 'SOC2 Type II',
    'ODP set optimized for SOC2 Type II compliance. Emphasizes access control monitoring, audit trail completeness, and security incident response. Balances automation with human review.',
    '{"AGT-DEL-001": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-PER-003": {"severity": "HIGH", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-CRE-008": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-INJ-006": {"severity": "HIGH", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}}',
    '2024-12-01T00:00:00Z');

-- Template 3: PCI-DSS
INSERT INTO industry_templates (id, name, display_name, description, odp_set_json, created_at)
VALUES (3, 'PCI-DSS', 'PCI-DSS Payment Card',
    'ODP set for payment card industry compliance. Prioritizes credential protection, data encryption, and network security. All credential exposure incidents are auto-contained with immediate CISO escalation.',
    '{"AGT-DEL-001": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-FIN-002": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-CRE-008": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 3, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-EXT-005": {"severity": "HIGH", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}}',
    '2024-12-01T00:00:00Z');

-- Template 4: GDPR
INSERT INTO industry_templates (id, name, display_name, description, odp_set_json, created_at)
VALUES (4, 'GDPR', 'GDPR Data Protection',
    'ODP set for EU General Data Protection Regulation compliance. Emphasizes data subject rights, breach notification timelines (72-hour rule), and privacy-by-design incident response.',
    '{"AGT-DEL-001": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 4, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-CRE-008": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 3, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-HRM-004": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-PER-003": {"severity": "HIGH", "auto_contain": true, "forensic_level": "STANDARD", "sla": 8, "compliance_report": "ALWAYS", "record_threshold": 1}}',
    '2024-12-01T00:00:00Z');

-- Template 5: Financial Services
INSERT INTO industry_templates (id, name, display_name, description, odp_set_json, created_at)
VALUES (5, 'FINANCIAL_SERVICES', 'Financial Services',
    'ODP set for banking, trading, and financial services. Maximizes response speed for financial anomalies, trading errors, and market-impacting events. Tight SLAs and deep forensics on all financial incidents.',
    '{"AGT-FIN-002": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 3, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-DEL-001": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-CRE-008": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "DEEP", "sla": 3, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-RAT-009": {"severity": "HIGH", "auto_contain": true, "forensic_level": "STANDARD", "sla": 5, "compliance_report": "ALWAYS", "record_threshold": 10}}',
    '2024-12-01T00:00:00Z');

-- Template 6: SaaS Startup
INSERT INTO industry_templates (id, name, display_name, description, odp_set_json, created_at)
VALUES (6, 'SAAS_STARTUP', 'SaaS Startup',
    'Lightweight ODP set for resource-constrained SaaS startups. Balances security with operational pragmatism. Uses CONDITIONAL compliance reporting and LIGHTWEIGHT forensics for non-critical incidents to minimize operational overhead.',
    '{"AGT-DEL-001": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-CRE-008": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-HRM-004": {"severity": "CRITICAL", "auto_contain": true, "forensic_level": "STANDARD", "sla": 10, "compliance_report": "ALWAYS", "record_threshold": 1}, "AGT-HAL-007": {"severity": "MEDIUM", "auto_contain": false, "forensic_level": "LIGHTWEIGHT", "sla": 30, "compliance_report": "CONDITIONAL", "record_threshold": 50}, "AGT-DRF-010": {"severity": "MEDIUM", "auto_contain": false, "forensic_level": "LIGHTWEIGHT", "sla": 60, "compliance_report": "CONDITIONAL", "record_threshold": 500}}',
    '2024-12-01T00:00:00Z');
```

---

#### 4.11 Policy Version History

**Narrative:** Three policy versions showing the evolution of ODP settings over time -- from initial NIST defaults to organizational customization.

```sql
-- Version 1: Initial NIST defaults
INSERT INTO policy_versions (id, version_number, changed_by, change_summary, diff_json, created_at)
VALUES (1, 1, 'system', 'Initial NIST AI RMF baseline policy -- all defaults applied',
    '{"action": "init", "source": "NIST AI RMF Agentic Profile", "defaults_applied": 96, "overrides": 0}',
    '2024-12-01T00:00:00Z');

-- Version 2: Admin elevates hallucination severity + auto-contain
INSERT INTO policy_versions (id, version_number, changed_by, change_summary, diff_json, created_at)
VALUES (2, 2, 'admin', 'Elevated AGT-HAL-007 (Hallucination) to CRITICAL with auto-contain enabled; tightened AGT-CRE-008 SLA to 3 minutes; lowered hallucination record threshold to 10',
    '{"changed_odps": [{"odp_key": "severity_threshold", "incident_type": "AGT-HAL-007", "old": "MEDIUM", "new": "CRITICAL"}, {"odp_key": "auto_contain_enabled", "incident_type": "AGT-HAL-007", "old": "false", "new": "true"}, {"odp_key": "response_time_sla", "incident_type": "AGT-CRE-008", "old": "5", "new": "3"}, {"odp_key": "record_threshold", "incident_type": "AGT-HAL-007", "old": "50", "new": "10"}], "total_overrides": 4}',
    '2025-01-10T09:00:00Z');

-- Version 3: SOC2 template applied
INSERT INTO policy_versions (id, version_number, changed_by, change_summary, diff_json, created_at)
VALUES (3, 3, 'compliance_officer', 'Applied SOC2 Type II industry template -- enhanced access control monitoring and audit trail requirements',
    '{"template_applied": "SOC2", "changed_odps": [{"odp_key": "compliance_report", "incident_type": "AGT-PER-003", "old": "CONDITIONAL", "new": "ALWAYS"}, {"odp_key": "forensic_level", "incident_type": "AGT-INJ-006", "old": "LIGHTWEIGHT", "new": "STANDARD"}, {"odp_key": "compliance_report", "incident_type": "AGT-INJ-006", "old": "CONDITIONAL", "new": "ALWAYS"}], "template_source": "industry_templates", "total_changes": 3}',
    '2025-01-14T14:30:00Z');
```

---

#### 4.12 ODP Conflict Detection Samples

**Narrative:** Two detected ODP conflicts demonstrating the conflict detection engine. One WARNING (acceptable deviation) and one BLOCKED (requires approval).

```sql
-- Conflict 1: WARNING -- Severity downgrade for model drift is acceptable for this org
INSERT INTO odp_conflicts (id, organization_odp_id, conflict_type, severity, nist_default_value, org_value, resolution_suggestion, resolved, detected_at)
VALUES (1, 40, 'SLA_EXCEEDED', 'WARNING', '30', '60', 'SOC2 requires faster response. Consider reducing to 45 minutes.', 0, '2025-01-10T09:05:00Z');

-- Conflict 2: BLOCKED -- Auto-contain disabled for data destruction (NIST requires enabled)
INSERT INTO odp_conflicts (id, organization_odp_id, conflict_type, severity, nist_default_value, org_value, resolution_suggestion, resolved, detected_at)
VALUES (2, 1, 'AUTO_CONTAIN_DISABLED', 'BLOCKED', 'true', 'false', 'NIST AI RMF requires auto-containment for data destruction incidents. Disabling this violates AG-MG.1. Either re-enable auto-contain or document exception with CISO approval.', 0, '2025-01-10T09:05:00Z');
```

---

#### 4.13 Updated Sample Data Verification Query

Verify that all sample data has been loaded correctly, including the new ODP tables:

```sql
-- Verify scenario completeness
SELECT
    (SELECT COUNT(*) FROM agents) AS total_agents,
    (SELECT COUNT(*) FROM incidents) AS total_incidents,
    (SELECT COUNT(*) FROM evidence_packages) AS total_evidence,
    (SELECT COUNT(*) FROM audit_log) AS total_audit_entries,
    (SELECT COUNT(*) FROM agent_health_history) AS total_health_snapshots,
    (SELECT COUNT(*) FROM compliance_mappings) AS total_compliance_mappings,
    (SELECT COUNT(*) FROM judge_decisions) AS total_judge_decisions,
    (SELECT COUNT(*) FROM bypass_patterns) AS total_bypass_patterns,
    (SELECT COUNT(*) FROM bypass_attempts) AS total_bypass_attempts,
    (SELECT COUNT(*) FROM nist_baselines) AS total_nist_baselines,
    (SELECT COUNT(*) FROM organization_odps) AS total_odps,
    (SELECT COUNT(*) FROM industry_templates) AS total_industry_templates,
    (SELECT COUNT(*) FROM policy_versions) AS total_policy_versions,
    (SELECT COUNT(*) FROM odp_conflicts) AS total_odp_conflicts;

-- Expected output:
-- total_agents: 3
-- total_incidents: 6
-- total_evidence: 6
-- total_audit_entries: 35
-- total_health_snapshots: 10
-- total_compliance_mappings: 8
-- total_judge_decisions: 5
-- total_bypass_patterns: 4
-- total_bypass_attempts: 2
-- total_nist_baselines: 12
-- total_odps: 96
-- total_industry_templates: 6
-- total_policy_versions: 3
-- total_odp_conflicts: 2
```

---
### 5. Query Patterns

#### 5.1 Dashboard Aggregation Queries

**Query 5.1.1: Dashboard Summary Card -- Incident Counts by Severity**

```sql
SELECT
    severity,
    COUNT(*) AS incident_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS percentage
FROM incidents
WHERE created_at >= datetime('now', '-24 hours')
GROUP BY severity
ORDER BY
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH'     THEN 2
        WHEN 'MEDIUM'   THEN 3
        WHEN 'LOW'      THEN 4
        WHEN 'INFO'     THEN 5
    END;
```

> **Used by:** Dashboard top-row severity cards and severity bar chart.  
> **Performance:** Uses `idx_incidents_severity_detected` index for the date filter.  
> **Frequency:** Every 30 seconds (dashboard polling).

---

**Query 5.1.2: Active Incident Queue -- Current Open Incidents**

```sql
SELECT
    i.id,
    i.title,
    i.type_code,
    i.severity,
    i.status,
    i.detected_at,
    a.name AS agent_name,
    a.health_score AS agent_health,
    (julianday('now') - julianday(i.detected_at)) * 24 * 60 AS minutes_open
FROM incidents i
JOIN agents a ON i.agent_id = a.id
WHERE i.status NOT IN ('RESOLVED', 'CLOSED')
ORDER BY
    CASE i.severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH'     THEN 2
        WHEN 'MEDIUM'   THEN 3
        WHEN 'LOW'      THEN 4
        WHEN 'INFO'     THEN 5
    END,
    i.detected_at ASC;
```

> **Used by:** "Active Incidents" panel and incident queue views.  
> **Performance:** Uses `idx_incidents_status` for status filter, then joins to `agents` via `idx_agents_id` (primary key lookup).  
> **Frequency:** Every 10 seconds when dashboard is open.

---

**Query 5.1.3: Agent Health Overview -- All Agents with Current Status**

```sql
SELECT
    a.id,
    a.name,
    a.system_id,
    a.health_score,
    a.lie_rate,
    a.incident_count,
    a.is_active,
    a.last_seen_at,
    COUNT(CASE WHEN i.status NOT IN ('RESOLVED', 'CLOSED') THEN 1 END) AS active_incidents,
    MAX(i.detected_at) AS last_incident_at
FROM agents a
LEFT JOIN incidents i ON a.id = i.agent_id
GROUP BY a.id, a.name, a.system_id, a.health_score, a.lie_rate, a.incident_count, a.is_active, a.last_seen_at
ORDER BY a.health_score ASC;
```

> **Used by:** Agent cards on the main dashboard and agent management page.  
> **Performance:** LEFT JOIN uses `idx_incidents_agent_id`. The `active_incidents` count is computed via conditional aggregation.  
> **Frequency:** Every 30 seconds.

---

**Query 5.1.4: Incident Timeline -- Recent Incidents with Agent and Evidence**

```sql
SELECT
    i.id,
    i.title,
    i.type_code,
    i.severity,
    i.status,
    i.detected_at,
    a.name AS agent_name,
    (SELECT COUNT(*) FROM evidence_packages WHERE incident_id = i.id) AS evidence_count
FROM incidents i
JOIN agents a ON i.agent_id = a.id
WHERE i.detected_at >= datetime('now', '-7 days')
ORDER BY i.detected_at DESC
LIMIT 50;
```

> **Used by:** "Incident Timeline" widget and recent incidents list.  
> **Performance:** Uses `idx_incidents_detected_at` for the date range, then JOIN to agents.  
> **Frequency:** Every 30 seconds.

---

#### 5.2 Compliance Report Queries

**Query 5.2.1: EU AI Act Article 50 Compliance Report**

```sql
SELECT
    cm.framework,
    cm.article_ref,
    cm.article_title,
    cm.risk_level,
    COUNT(DISTINCT cm.incident_id) AS incident_count,
    COUNT(DISTINCT i.agent_id) AS affected_agents,
    MIN(i.detected_at) AS first_occurrence,
    MAX(i.detected_at) AS latest_occurrence,
    AVG(cm.mapping_confidence) AS avg_confidence
FROM compliance_mappings cm
JOIN incidents i ON cm.incident_id = i.id
WHERE cm.framework = 'EU_AI_ACT'
GROUP BY cm.framework, cm.article_ref, cm.article_title, cm.risk_level
ORDER BY
    CASE cm.risk_level
        WHEN 'UNACCEPTABLE' THEN 1
        WHEN 'HIGH'         THEN 2
        WHEN 'LIMITED'      THEN 3
        WHEN 'MINIMAL'      THEN 4
    END;
```

> **Used by:** Compliance dashboard and regulatory reporting.  
> **Performance:** Uses `idx_compliance_framework` for the framework filter, then JOIN to incidents via primary key.  
> **Frequency:** On-demand (user-triggered report generation).

---

**Query 5.2.2: Incident Detail with Full Evidence and Compliance**

```sql
SELECT
    i.id AS incident_id,
    i.title,
    i.type_code,
    i.severity,
    i.status,
    i.description,
    i.detected_at,
    i.classified_at,
    i.responded_at,
    i.resolved_at,
    i.closed_at,
    a.name AS agent_name,
    a.system_id AS agent_system_id,
    p.name AS playbook_name,
    ep.prompt_chain,
    ep.evidence_data,
    ep.timeline_json,
    ep.compliance_data,
    ep.collected_at AS evidence_collected_at,
    cm.framework,
    cm.article_ref,
    cm.article_title,
    cm.risk_level AS compliance_risk_level,
    cm.mapping_confidence
FROM incidents i
JOIN agents a ON i.agent_id = a.id
LEFT JOIN playbooks p ON i.playbook_id = p.id
LEFT JOIN evidence_packages ep ON ep.incident_id = i.id
LEFT JOIN compliance_mappings cm ON cm.incident_id = i.id
WHERE i.id = ?;
```

> **Used by:** Incident detail modal and forensic investigation view.  
> **Performance:** Primary key lookup on `incidents.id`, then LEFT JOINs to related tables. Very efficient.  
> **Frequency:** On-demand (when user clicks an incident).

---

**Query 5.2.3: Audit Trail Export for Compliance Investigation**

```sql
SELECT
    al.id AS audit_id,
    al.table_name,
    al.record_id,
    al.action,
    al.old_data,
    al.new_data,
    al.changed_by,
    al.session_id,
    al.changed_at,
    CASE
        WHEN al.table_name = 'incidents' THEN (SELECT title FROM incidents WHERE id = al.record_id)
        WHEN al.table_name = 'agents'    THEN (SELECT name  FROM agents    WHERE id = al.record_id)
        WHEN al.table_name = 'playbooks' THEN (SELECT name  FROM playbooks WHERE id = al.record_id)
        ELSE NULL
    AS record_name
FROM audit_log al
WHERE al.changed_at >= ?
  AND al.changed_at <= ?
  AND (? IS NULL OR al.table_name = ?)
  AND (? IS NULL OR al.action = ?)
ORDER BY al.changed_at DESC;
```

> **Used by:** Compliance audit trail export, security investigations.  
> **Performance:** Uses `idx_audit_changed_at` for the date range filter.  
> **Frequency:** On-demand (user-triggered export).

---

#### 5.3 Performance-Critical Queries

**Query 5.3.1: Playbook Execution -- Fetch Ordered Actions**

```sql
SELECT
    id,
    step_order,
    action_type,
    action_name,
    action_config,
    condition_json,
    is_enabled
FROM playbook_actions
WHERE playbook_id = ?
  AND is_enabled = 1
ORDER BY step_order ASC;
```

> **Used by:** Playbook execution engine. Runs every time an incident triggers a playbook.  
> **Performance:** Uses `idx_playbook_actions_order` covering index. Single index scan, no table lookup needed.  
> **Frequency:** Per-incident (during automated response).

---

**Query 5.3.2: Health Score Sparkline -- 24-Hour Trend for an Agent**

```sql
SELECT
    recorded_at,
    health_score,
    lie_rate
FROM agent_health_history
WHERE agent_id = ?
  AND recorded_at >= datetime('now', '-24 hours')
ORDER BY recorded_at ASC;
```

> **Used by:** Agent detail page health sparkline chart.  
> **Performance:** Uses `idx_health_agent_recorded` covering index.  
> **Frequency:** Every 30 seconds when agent detail page is open.

---

**Query 5.3.3: Gemini Cache Lookup**

```sql
SELECT
    id,
    response_data,
    prompt_tokens,
    completion_tokens,
    hit_count,
    expires_at
FROM gemini_cache
WHERE request_hash = ?
  AND expires_at > datetime('now')
LIMIT 1;
```

> **Used by:** API response cache hit check. Runs before every Gemini API call.  
> **Performance:** Uses `idx_gemini_request_hash` index. Extremely fast (microsecond range).  
> **Frequency:** Every API call attempt.

---

**Query 5.3.4: Detection Rules Evaluation -- Fetch Active Rules**

```sql
SELECT
    id,
    name,
    rule_type,
    condition_json,
    severity_on_trigger,
    incident_type_code
FROM detection_rules
WHERE is_active = 1
ORDER BY id ASC;
```

> **Used by:** Detection engine rule evaluation loop.  
> **Performance:** Uses `idx_detection_rules_active` index. Very small result set (typically <50 rules).  
> **Frequency:** Every detection cycle (configurable, default 60 seconds).

---

#### 5.4 EXPLAIN Query Plans

**EXPLAIN for Query 5.1.2 (Active Incident Queue):**

```sql
EXPLAIN QUERY PLAN
SELECT i.*, a.name AS agent_name
FROM incidents i
JOIN agents a ON i.agent_id = a.id
WHERE i.status NOT IN ('RESOLVED', 'CLOSED')
ORDER BY i.detected_at ASC;

-- Expected output:
-- SCAN TABLE incidents USING INDEX idx_incidents_status
-- SEARCH TABLE agents USING INTEGER PRIMARY KEY (rowid=?)
-- USE TEMP B-TREE FOR ORDER BY
```

> The query scans the `idx_incidents_status` index for open incidents, then performs a primary key lookup for each agent. The `ORDER BY` requires a temp B-tree because the sort is on `detected_at` while the filter is on `status`.

**Optimization Note:** For very large incident tables, add a composite index:

```sql
CREATE INDEX idx_incidents_status_detected ON incidents(status, detected_at);
```

This converts the plan to:

```
SCAN TABLE incidents USING INDEX idx_incidents_status_detected
SEARCH TABLE agents USING INTEGER PRIMARY KEY (rowid=?)
-- No temp B-tree needed (ORDER BY uses index order)
```

---

**EXPLAIN for Query 5.3.1 (Playbook Actions):**

```sql
EXPLAIN QUERY PLAN
SELECT * FROM playbook_actions
WHERE playbook_id = 1 AND is_enabled = 1
ORDER BY step_order;

-- Expected output:
-- SCAN TABLE playbook_actions USING INDEX idx_playbook_actions_order
```

> This is a covering index scan. SQLite can satisfy the entire query from the index without touching the table. Optimal performance.

---

#### 5.5 Maintenance Queries

**Query 5.5.1: Expired Cache Cleanup**

```sql
DELETE FROM gemini_cache
WHERE expires_at < datetime('now', '-7 days');
```

> **Used by:** Scheduled cache cleanup job (runs daily).  
> **Performance:** Uses `idx_gemini_expires_at` index. Fast batch delete.

---

**Query 5.5.2: Health History Pruning (retain 90 days)**

```sql
DELETE FROM agent_health_history
WHERE recorded_at < datetime('now', '-90 days');
```

> **Used by:** Scheduled data retention job (runs weekly).  
> **Performance:** Uses `idx_health_recorded_at` index.

---

**Query 5.5.3: Database Statistics Update**

```sql
ANALYZE;
```

> **Used by:** Post-migration or weekly maintenance. Updates SQLite's internal statistics for query planner optimization.  
> **Frequency:** After schema changes, or weekly.

---


#### 5.7 ODP Resolution Queries

**Query 5.7.1: Resolved Policy for an Incident Type**

```sql
SELECT
    baseline_id,
    incident_type,
    resolved_severity,
    resolved_auto_contain,
    resolved_escalation,
    resolved_sla,
    resolved_forensic,
    resolved_notify,
    resolved_compliance,
    resolved_threshold
FROM resolved_policies
WHERE incident_type = ?;
```

> **Used by:** Incident response engine when classifying a new incident. Looks up the effective policy for the incident type.
> **Performance:** The view performs 8 indexed LEFT JOINs on `organization_odps`. With 96 ODP rows total, this resolves in sub-millisecond time.
> **Frequency:** Per-incident (during classification).

---

**Query 5.7.2: ODP Override Summary Dashboard**

```sql
SELECT
    nb.incident_type,
    nb.name AS incident_name,
    nb.default_severity,
    COALESCE(oo_severity.odp_value, nb.default_severity) AS effective_severity,
    CASE WHEN oo_severity.is_override = 1 THEN 'OVERRIDDEN' ELSE 'DEFAULT' END AS severity_status,
    nb.default_auto_contain,
    COALESCE(oo_contain.odp_value, CAST(nb.default_auto_contain AS TEXT)) AS effective_auto_contain,
    CASE WHEN oo_contain.is_override = 1 THEN 'OVERRIDDEN' ELSE 'DEFAULT' END AS contain_status,
    nb.default_response_sla_minutes,
    COALESCE(oo_sla.odp_value, CAST(nb.default_response_sla_minutes AS TEXT)) AS effective_sla,
    CASE WHEN oo_sla.is_override = 1 THEN 'OVERRIDDEN' ELSE 'DEFAULT' END AS sla_status,
    COUNT(oc.id) AS unresolved_conflicts
FROM nist_baselines nb
LEFT JOIN organization_odps oo_severity ON nb.id = oo_severity.nist_baseline_id AND oo_severity.odp_key = 'severity_threshold'
LEFT JOIN organization_odps oo_contain ON nb.id = oo_contain.nist_baseline_id AND oo_contain.odp_key = 'auto_contain_enabled'
LEFT JOIN organization_odps oo_sla ON nb.id = oo_sla.nist_baseline_id AND oo_sla.odp_key = 'response_time_sla'
LEFT JOIN odp_conflicts oc ON oo_severity.id = oc.organization_odp_id AND oc.resolved = 0
GROUP BY nb.id, nb.incident_type, nb.name, nb.default_severity, oo_severity.odp_value,
         oo_severity.is_override, nb.default_auto_contain, oo_contain.odp_value,
         oo_contain.is_override, nb.default_response_sla_minutes, oo_sla.odp_value, oo_sla.is_override
ORDER BY nb.incident_type;
```

> **Used by:** ODP management dashboard showing the effective policy for each incident type, with indicators for which values are overridden.
> **Performance:** Uses `idx_odp_baseline` and `idx_odp_key` indexes. LEFT JOIN to `odp_conflicts` via `idx_conflict_odp`.
> **Frequency:** Every 30 seconds (ODP dashboard polling).

---

**Query 5.7.3: ODP Conflict Alert Feed**

```sql
SELECT
    oc.id AS conflict_id,
    oc.conflict_type,
    oc.severity AS conflict_severity,
    oc.nist_default_value,
    oc.org_value,
    oc.resolution_suggestion,
    oc.detected_at,
    nb.incident_type,
    nb.name AS incident_name,
    oo.odp_key,
    oo.changed_by AS overridden_by
FROM odp_conflicts oc
LEFT JOIN organization_odps oo ON oc.organization_odp_id = oo.id
LEFT JOIN nist_baselines nb ON oo.nist_baseline_id = nb.id
WHERE oc.resolved = 0
ORDER BY
    CASE oc.severity
        WHEN 'BLOCKED' THEN 1
        WHEN 'WARNING' THEN 2
    END,
    oc.detected_at DESC;
```

> **Used by:** ODP conflict alert feed on the security dashboard. Shows unresolved conflicts with BLOCKED first.
> **Performance:** Uses `idx_conflict_unresolved` index. LEFT JOINs via `idx_conflict_odp` to `organization_odps` and `nist_baselines`.
> **Frequency:** Every 30 seconds.

---

**Query 5.7.4: Policy Version Comparison**

```sql
SELECT
    pv.version_number,
    pv.changed_by,
    pv.change_summary,
    pv.diff_json,
    pv.created_at,
    (SELECT COUNT(*) FROM policy_versions WHERE version_number <= pv.version_number) AS cumulative_changes
FROM policy_versions pv
ORDER BY pv.version_number DESC;
```

> **Used by:** Policy audit trail and version comparison view. Shows the evolution of ODP settings over time.
> **Performance:** Uses `idx_policy_version` index. Small table (typically <100 versions).
> **Frequency:** On-demand (when viewing policy history).

---

**Query 5.7.5: Industry Template Preview**

```sql
SELECT
    it.id AS template_id,
    it.name,
    it.display_name,
    it.description,
    json_array_length(it.odp_set_json) AS incident_types_covered,
    it.created_at
FROM industry_templates it
ORDER BY it.display_name;
```

> **Used by:** Industry template picker UI. Shows available templates with coverage summary.
> **Performance:** Full table scan on `industry_templates` (6 rows). Instant.
> **Frequency:** On-demand (when opening template picker).

---

#### 5.8 ODP Maintenance Queries

**Query 5.8.1: Apply Industry Template**

```sql
-- Read template ODP set
-- For each incident type in template:
--   For each ODP key:
--     INSERT or REPLACE into organization_odps
-- This is implemented in application code due to JSON parsing complexity.
```

> **Used by:** "Apply Template" button in ODP management UI. Copies template values into organization_odps.
> **Note:** Implemented in application code using JSON parsing, not as a single SQL statement.

---

**Query 5.8.2: Conflict Detection Sweep**

```sql
-- Detect ODP overrides that conflict with NIST defaults
-- This runs as a scheduled background job

INSERT INTO odp_conflicts (organization_odp_id, conflict_type, severity, nist_default_value, org_value, resolution_suggestion, resolved, detected_at)
SELECT
    oo.id,
    'SEVERITY_DOWNGRADE' AS conflict_type,
    'BLOCKED' AS severity,
    nb.default_severity AS nist_default_value,
    oo.odp_value AS org_value,
    'Severity downgrade below NIST recommendation requires CISO approval' AS resolution_suggestion,
    0 AS resolved,
    datetime('now') AS detected_at
FROM organization_odps oo
JOIN nist_baselines nb ON oo.nist_baseline_id = nb.id
WHERE oo.odp_key = 'severity_threshold'
  AND oo.is_override = 1
  AND (
      (nb.default_severity = 'CRITICAL' AND oo.odp_value != 'CRITICAL') OR
      (nb.default_severity = 'HIGH' AND oo.odp_value IN ('MEDIUM', 'LOW', 'INFO')) OR
      (nb.default_severity = 'MEDIUM' AND oo.odp_value IN ('LOW', 'INFO'))
  )
  AND NOT EXISTS (
      SELECT 1 FROM odp_conflicts oc
      WHERE oc.organization_odp_id = oo.id
        AND oc.conflict_type = 'SEVERITY_DOWNGRADE'
        AND oc.resolved = 0
  );
```

> **Used by:** Scheduled conflict detection job (runs hourly). Identifies new conflicts between ODP overrides and NIST defaults.
> **Performance:** JOIN uses `idx_odp_baseline`. Correlated subquery uses `idx_conflict_odp`.
> **Frequency:** Hourly (background job).

---

### 6. Migration Strategy

#### 6.1 Schema Versioning

PLAYBOOK uses a simple integer-based schema version stored in the SQLite `user_version` pragma:

```sql
-- Check current schema version
PRAGMA user_version;

-- Set schema version after migration
PRAGMA user_version = 3;
```

**Version History:**

| Version | Date | Description |
|---------|------|-------------|
| 0 | Initial | Empty database |
| 1 | 2025-01-16 | Initial schema (11 tables, indexes, triggers) |
| 2 | 2025-01-16 | Added Judge Layer tables: `judge_decisions`, `bypass_patterns`, `bypass_attempts`; added `suprawall_events`; updated `incidents` and `agents` with Judge Layer columns |
| 3 | 2025-01-16 | Added ODP (Organization-Defined Parameters) system: `nist_baselines`, `organization_odps`, `policy_versions`, `industry_templates`, `odp_conflicts`; added `resolved_policies` view; updated `incidents` with `resolved_policy_id` and `odp_override_applied` columns |

#### 6.2 Migration Script Template

```sql
-- ============================================================================
-- Migration: 003_odp_system.sql
-- Description: Adds ODP (Organization-Defined Parameters) tables, view, and
--              sample data. Updates incidents table with ODP tracking columns.
-- ============================================================================

BEGIN TRANSACTION;

-- Check if migration has already been applied
PRAGMA user_version;
-- If user_version >= 3, skip this migration

-- ---------------------------------------------------------------------------
-- 1. Create new tables
-- ---------------------------------------------------------------------------

-- nist_baselines: NIST AI RMF baseline policy definitions
CREATE TABLE IF NOT EXISTS nist_baselines (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_type             TEXT NOT NULL UNIQUE,
    name                      TEXT NOT NULL,
    description               TEXT NOT NULL,
    nist_source               TEXT NOT NULL,
    default_severity          TEXT NOT NULL,
    default_auto_contain      INTEGER NOT NULL DEFAULT 0,
    default_forensic_level    TEXT DEFAULT 'STANDARD',
    default_response_sla_minutes INTEGER DEFAULT 15,
    default_compliance_report TEXT DEFAULT 'CONDITIONAL',
    default_record_threshold  INTEGER DEFAULT 100,
    response_actions_json     TEXT NOT NULL,
    compliance_mappings_json  TEXT NOT NULL,
    created_at                DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (incident_type IN (
        'AGT-DEL-001', 'AGT-FIN-002', 'AGT-PER-003', 'AGT-HRM-004',
        'AGT-EXT-005', 'AGT-INJ-006', 'AGT-HAL-007', 'AGT-CRE-008',
        'AGT-RAT-009', 'AGT-DRF-010', 'AGT-TLM-011', 'AGT-GAP-012'
    )),
    CHECK (default_severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    CHECK (default_auto_contain IN (0, 1)),
    CHECK (default_forensic_level IN ('STANDARD', 'DEEP', 'LIGHTWEIGHT', 'NONE')),
    CHECK (default_compliance_report IN ('ALWAYS', 'CONDITIONAL', 'NEVER'))
);

-- organization_odps: Organization-defined parameter overrides
CREATE TABLE IF NOT EXISTS organization_odps (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nist_baseline_id    INTEGER NOT NULL,
    odp_key             TEXT NOT NULL,
    odp_value           TEXT NOT NULL,
    is_override         INTEGER DEFAULT 1,
    version             INTEGER DEFAULT 1,
    changed_by          TEXT,
    changed_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nist_baseline_id, odp_key),
    CHECK (is_override IN (0, 1)),
    CHECK (version > 0),
    CHECK (odp_key IN (
        'severity_threshold', 'auto_contain_enabled', 'escalation_contacts',
        'response_time_sla', 'forensic_level', 'notify_targets',
        'compliance_report', 'record_threshold'
    )),
    FOREIGN KEY (nist_baseline_id) REFERENCES nist_baselines(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- policy_versions: ODP policy change history
CREATE TABLE IF NOT EXISTS policy_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    version_number      INTEGER NOT NULL,
    changed_by          TEXT NOT NULL,
    change_summary      TEXT NOT NULL,
    diff_json           TEXT NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (version_number > 0)
);

-- industry_templates: Pre-built industry ODP templates
CREATE TABLE IF NOT EXISTS industry_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL UNIQUE,
    display_name        TEXT NOT NULL,
    description         TEXT NOT NULL,
    odp_set_json        TEXT NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- odp_conflicts: ODP-NIST conflict detection
CREATE TABLE IF NOT EXISTS odp_conflicts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_odp_id     INTEGER,
    conflict_type           TEXT NOT NULL,
    severity                TEXT NOT NULL,
    nist_default_value      TEXT NOT NULL,
    org_value               TEXT NOT NULL,
    resolution_suggestion   TEXT,
    resolved                INTEGER DEFAULT 0,
    detected_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (severity IN ('WARNING', 'BLOCKED')),
    CHECK (resolved IN (0, 1)),
    CHECK (conflict_type IN (
        'SEVERITY_DOWNGRADE', 'AUTO_CONTAIN_DISABLED', 'SLA_EXCEEDED',
        'FORENSIC_LEVEL_REDUCED', 'COMPLIANCE_REPORT_SKIPPED',
        'THRESHOLD_INCREASED', 'ESCALATION_REMOVED', 'NOTIFY_REMOVED'
    )),
    FOREIGN KEY (organization_odp_id) REFERENCES organization_odps(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 2. Create indexes
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_nist_type ON nist_baselines(incident_type);
CREATE INDEX IF NOT EXISTS idx_odp_baseline ON organization_odps(nist_baseline_id);
CREATE INDEX IF NOT EXISTS idx_odp_key ON organization_odps(odp_key);
CREATE INDEX IF NOT EXISTS idx_policy_version ON policy_versions(version_number);
CREATE INDEX IF NOT EXISTS idx_policy_version_created ON policy_versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conflict_odp ON odp_conflicts(organization_odp_id);
CREATE INDEX IF NOT EXISTS idx_conflict_type ON odp_conflicts(conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflict_unresolved ON odp_conflicts(resolved, detected_at DESC);

-- ---------------------------------------------------------------------------
-- 3. Create resolved_policies view
-- ---------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS resolved_policies AS
SELECT
    nb.id as baseline_id,
    nb.incident_type,
    COALESCE(oo_severity.odp_value, nb.default_severity) as resolved_severity,
    COALESCE(oo_contain.odp_value, CAST(nb.default_auto_contain AS TEXT)) as resolved_auto_contain,
    COALESCE(oo_escalation.odp_value, '') as resolved_escalation,
    COALESCE(oo_sla.odp_value, CAST(nb.default_response_sla_minutes AS TEXT)) as resolved_sla,
    COALESCE(oo_forensic.odp_value, nb.default_forensic_level) as resolved_forensic,
    COALESCE(oo_notify.odp_value, '') as resolved_notify,
    COALESCE(oo_compliance.odp_value, nb.default_compliance_report) as resolved_compliance,
    COALESCE(oo_threshold.odp_value, CAST(nb.default_record_threshold AS TEXT)) as resolved_threshold
FROM nist_baselines nb
LEFT JOIN organization_odps oo_severity ON nb.id = oo_severity.nist_baseline_id AND oo_severity.odp_key = 'severity_threshold'
LEFT JOIN organization_odps oo_contain ON nb.id = oo_contain.nist_baseline_id AND oo_contain.odp_key = 'auto_contain_enabled'
LEFT JOIN organization_odps oo_escalation ON nb.id = oo_escalation.nist_baseline_id AND oo_escalation.odp_key = 'escalation_contacts'
LEFT JOIN organization_odps oo_sla ON nb.id = oo_sla.nist_baseline_id AND oo_sla.odp_key = 'response_time_sla'
LEFT JOIN organization_odps oo_forensic ON nb.id = oo_forensic.nist_baseline_id AND oo_forensic.odp_key = 'forensic_level'
LEFT JOIN organization_odps oo_notify ON nb.id = oo_notify.nist_baseline_id AND oo_notify.odp_key = 'notify_targets'
LEFT JOIN organization_odps oo_compliance ON nb.id = oo_compliance.nist_baseline_id AND oo_compliance.odp_key = 'compliance_report'
LEFT JOIN organization_odps oo_threshold ON nb.id = oo_threshold.nist_baseline_id AND oo_threshold.odp_key = 'record_threshold';

-- ---------------------------------------------------------------------------
-- 4. Update existing incidents table
-- ---------------------------------------------------------------------------

-- Add ODP tracking columns to incidents table (if not exists)
-- SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN,
-- so this must be handled by the application migration runner

-- ALTER TABLE incidents ADD COLUMN resolved_policy_id INTEGER;
-- ALTER TABLE incidents ADD COLUMN odp_override_applied INTEGER NOT NULL DEFAULT 0;
-- CREATE INDEX idx_incidents_odp_override ON incidents(odp_override_applied);

-- ---------------------------------------------------------------------------
-- 5. Update schema version
-- ---------------------------------------------------------------------------

PRAGMA user_version = 3;

COMMIT;
```

#### 6.3 Rollback Procedure

If migration fails or needs to be reverted:

```sql
-- ============================================================================
-- Rollback: 003_odp_system_rollback.sql
-- Description: Removes ODP tables, view, and columns added in version 3.
-- WARNING: This will delete all ODP data. Back up first.
-- ============================================================================

BEGIN TRANSACTION;

-- Drop view first (no dependencies on it beyond application code)
DROP VIEW IF EXISTS resolved_policies;

-- Drop conflict detection table (depends on organization_odps)
DROP TABLE IF EXISTS odp_conflicts;

-- Drop ODP table (depends on nist_baselines)
DROP TABLE IF EXISTS organization_odps;

-- Drop template table
DROP TABLE IF EXISTS industry_templates;

-- Drop policy versions table
DROP TABLE IF EXISTS policy_versions;

-- Drop NIST baselines table
DROP TABLE IF EXISTS nist_baselines;

-- Drop ODP index on incidents
DROP INDEX IF EXISTS idx_incidents_odp_override;

-- Note: SQLite does not support DROP COLUMN.
-- The resolved_policy_id and odp_override_applied columns in incidents
-- will remain but will not be populated. To fully remove them:
-- 1. CREATE TABLE incidents_new (without the columns)
-- 2. INSERT INTO incidents_new SELECT ... (without the columns)
-- 3. DROP TABLE incidents
-- 4. ALTER TABLE incidents_new RENAME TO incidents

PRAGMA user_version = 2;

COMMIT;
```

#### 6.4 Downgrade Notes

| From | To | Compatible? | Notes |
|------|----|---|---|
| v3 | v2 | Partial | ODP tables are dropped; incidents retains ODP columns but they are unused |
| v3 | v1 | No | Must roll back through v2 first |
| v2 | v3 | Yes | Idempotent migration -- running v3 migration on v2 database is safe |

---

*End of Database Schema Document*

### 6. Migration Strategy

#### 6.1 Schema Versioning

PLAYBOOK uses a simple integer-based schema version stored in the SQLite `user_version` pragma:

```sql
-- Check current schema version
PRAGMA user_version;

-- Set schema version after migration
PRAGMA user_version = 3;
```

**Version History:**

| Version | Date | Description |
|---------|------|-------------|
| 0 | Initial | Empty database |
| 1 | 2025-01-16 | Initial schema (11 tables: incidents, agents, playbooks, playbook_actions, evidence_packages, audit_log, gemini_cache, agent_health_history, detection_rules, demo_scenarios, compliance_mappings; indexes; triggers) |
| 2 | 2025-01-16 | Added Judge Layer tables: `judge_decisions`, `bypass_patterns`, `bypass_attempts`; added `suprawall_events`; updated `incidents` (judge_decision_id, bypass_detected, deterministic_classification); updated `agents` (judge_decision_count, bypass_attempt_count, suprawall_connected); added Judge Layer indexes, triggers, and sample data |
| 3 | 2025-01-16 | Added ODP (Organization-Defined Parameters) system: `nist_baselines` (12 seed rows), `organization_odps` (96 rows), `policy_versions` (3 rows), `industry_templates` (6 rows), `odp_conflicts` (2 rows); added `resolved_policies` view; updated `incidents` (resolved_policy_id, odp_override_applied); added ODP indexes, triggers, and sample data |

#### 6.2 Migration Script: v1 to v2 (Judge Layer)

```sql
-- ============================================================================
-- Migration: 002_judge_layer.sql
-- Description: Adds Judge Layer tables, indexes, triggers, and sample data.
-- ============================================================================

BEGIN TRANSACTION;

-- Check if migration has already been applied
PRAGMA user_version;
-- If user_version >= 2, skip this migration

-- ---------------------------------------------------------------------------
-- 1. Update existing agents table
-- ---------------------------------------------------------------------------

-- SQLite does not support ALTER TABLE ADD COLUMN with constraints
-- These must be added via application-level migration:
-- ALTER TABLE agents ADD COLUMN judge_decision_count INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE agents ADD COLUMN bypass_attempt_count INTEGER NOT NULL DEFAULT 0;
-- ALTER TABLE agents ADD COLUMN suprawall_connected INTEGER NOT NULL DEFAULT 0;

-- ---------------------------------------------------------------------------
-- 2. Create judge_decisions table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS judge_decisions (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id          INTEGER,
    agent_id             INTEGER NOT NULL,
    proposed_action      TEXT NOT NULL,
    verdict              TEXT NOT NULL,
    confidence           REAL NOT NULL DEFAULT 1.0,
    rationale            TEXT,
    metadata_context     TEXT DEFAULT '{}',
    bypass_detected      INTEGER NOT NULL DEFAULT 0,
    bypass_pattern_id    INTEGER,
    gemini_enhanced      INTEGER NOT NULL DEFAULT 0,
    latency_ms           INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (verdict IN ('ALLOW', 'DENY', 'QUARANTINE', 'ESCALATE')),
    CHECK (bypass_detected IN (0, 1)),
    CHECK (gemini_enhanced IN (0, 1)),
    CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CHECK (latency_ms >= 0),
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (bypass_pattern_id) REFERENCES bypass_patterns(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 3. Create bypass_patterns table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bypass_patterns (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name         TEXT NOT NULL UNIQUE,
    pattern_display_name TEXT NOT NULL,
    description          TEXT,
    detection_rule       TEXT NOT NULL,
    severity             INTEGER NOT NULL DEFAULT 3,
    mitigated_by         TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (severity >= 1 AND severity <= 5)
);

-- ---------------------------------------------------------------------------
-- 4. Create bypass_attempts table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bypass_attempts (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_decision_id    INTEGER NOT NULL,
    pattern_id           INTEGER NOT NULL,
    raw_payload          TEXT,
    detection_confidence REAL NOT NULL DEFAULT 1.0,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (detection_confidence >= 0.0 AND detection_confidence <= 1.0),
    FOREIGN KEY (judge_decision_id) REFERENCES judge_decisions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (pattern_id) REFERENCES bypass_patterns(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 5. Create suprawall_events table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS suprawall_events (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id                 INTEGER NOT NULL,
    event_type               TEXT NOT NULL,
    suprawall_decision       TEXT NOT NULL DEFAULT '{}',
    correlated_incident_id   INTEGER,
    ingested_at              TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (event_type IN ('SUPRAWALL_ALLOW', 'SUPRAWALL_DENY')),
    FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (correlated_incident_id) REFERENCES incidents(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 6. Create indexes
-- ---------------------------------------------------------------------------

-- Judge decisions indexes
CREATE INDEX IF NOT EXISTS idx_judge_decisions_agent_created ON judge_decisions(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_judge_decisions_verdict ON judge_decisions(verdict);
CREATE INDEX IF NOT EXISTS idx_judge_decisions_bypass ON judge_decisions(bypass_detected);
CREATE INDEX IF NOT EXISTS idx_judge_decisions_incident ON judge_decisions(incident_id);
CREATE INDEX IF NOT EXISTS idx_judge_decisions_pattern ON judge_decisions(bypass_pattern_id);
CREATE INDEX IF NOT EXISTS idx_judge_decisions_latency ON judge_decisions(latency_ms);
CREATE INDEX IF NOT EXISTS idx_judge_decisions_created ON judge_decisions(created_at DESC);

-- Bypass patterns indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_bypass_patterns_name ON bypass_patterns(pattern_name);
CREATE INDEX IF NOT EXISTS idx_bypass_patterns_severity ON bypass_patterns(severity DESC);
CREATE INDEX IF NOT EXISTS idx_bypass_patterns_created ON bypass_patterns(created_at DESC);

-- Bypass attempts indexes
CREATE INDEX IF NOT EXISTS idx_bypass_attempts_pattern_created ON bypass_attempts(pattern_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bypass_attempts_decision ON bypass_attempts(judge_decision_id);
CREATE INDEX IF NOT EXISTS idx_bypass_attempts_created ON bypass_attempts(created_at DESC);

-- SupraWall events indexes
CREATE INDEX IF NOT EXISTS idx_suprawall_agent_ingested ON suprawall_events(agent_id, ingested_at DESC);
CREATE INDEX IF NOT EXISTS idx_suprawall_incident ON suprawall_events(correlated_incident_id);
CREATE INDEX IF NOT EXISTS idx_suprawall_event_type ON suprawall_events(event_type);
CREATE INDEX IF NOT EXISTS idx_suprawall_ingested ON suprawall_events(ingested_at DESC);

-- Agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_suprawall ON agents(suprawall_connected);
CREATE INDEX IF NOT EXISTS idx_agents_bypass_count ON agents(bypass_attempt_count DESC);

-- Incidents indexes
CREATE INDEX IF NOT EXISTS idx_incidents_bypass_detected ON incidents(bypass_detected);
CREATE INDEX IF NOT EXISTS idx_incidents_judge_decision ON incidents(judge_decision_id);

-- ---------------------------------------------------------------------------
-- 7. Update schema version
-- ---------------------------------------------------------------------------

PRAGMA user_version = 2;

COMMIT;
```

#### 6.3 Migration Script: v2 to v3 (ODP System)

```sql
-- ============================================================================
-- Migration: 003_odp_system.sql
-- Description: Adds ODP (Organization-Defined Parameters) tables, view, and
--              sample data. Updates incidents table with ODP tracking columns.
-- ============================================================================

BEGIN TRANSACTION;

-- Check if migration has already been applied
PRAGMA user_version;
-- If user_version >= 3, skip this migration

-- ---------------------------------------------------------------------------
-- 1. Create nist_baselines table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS nist_baselines (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_type             TEXT NOT NULL UNIQUE,
    name                      TEXT NOT NULL,
    description               TEXT NOT NULL,
    nist_source               TEXT NOT NULL,
    default_severity          TEXT NOT NULL,
    default_auto_contain      INTEGER NOT NULL DEFAULT 0,
    default_forensic_level    TEXT DEFAULT 'STANDARD',
    default_response_sla_minutes INTEGER DEFAULT 15,
    default_compliance_report TEXT DEFAULT 'CONDITIONAL',
    default_record_threshold  INTEGER DEFAULT 100,
    response_actions_json     TEXT NOT NULL,
    compliance_mappings_json  TEXT NOT NULL,
    created_at                DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (incident_type IN (
        'AGT-DEL-001', 'AGT-FIN-002', 'AGT-PER-003', 'AGT-HRM-004',
        'AGT-EXT-005', 'AGT-INJ-006', 'AGT-HAL-007', 'AGT-CRE-008',
        'AGT-RAT-009', 'AGT-DRF-010', 'AGT-TLM-011', 'AGT-GAP-012'
    )),
    CHECK (default_severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    CHECK (default_auto_contain IN (0, 1)),
    CHECK (default_forensic_level IN ('STANDARD', 'DEEP', 'LIGHTWEIGHT', 'NONE')),
    CHECK (default_compliance_report IN ('ALWAYS', 'CONDITIONAL', 'NEVER'))
);

-- ---------------------------------------------------------------------------
-- 2. Create organization_odps table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS organization_odps (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nist_baseline_id    INTEGER NOT NULL,
    odp_key             TEXT NOT NULL,
    odp_value           TEXT NOT NULL,
    is_override         INTEGER DEFAULT 1,
    version             INTEGER DEFAULT 1,
    changed_by          TEXT,
    changed_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nist_baseline_id, odp_key),
    CHECK (is_override IN (0, 1)),
    CHECK (version > 0),
    CHECK (odp_key IN (
        'severity_threshold', 'auto_contain_enabled', 'escalation_contacts',
        'response_time_sla', 'forensic_level', 'notify_targets',
        'compliance_report', 'record_threshold'
    )),
    FOREIGN KEY (nist_baseline_id) REFERENCES nist_baselines(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 3. Create policy_versions table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS policy_versions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    version_number      INTEGER NOT NULL,
    changed_by          TEXT NOT NULL,
    change_summary      TEXT NOT NULL,
    diff_json           TEXT NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (version_number > 0)
);

-- ---------------------------------------------------------------------------
-- 4. Create industry_templates table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS industry_templates (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL UNIQUE,
    display_name        TEXT NOT NULL,
    description         TEXT NOT NULL,
    odp_set_json        TEXT NOT NULL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- 5. Create odp_conflicts table
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS odp_conflicts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_odp_id     INTEGER,
    conflict_type           TEXT NOT NULL,
    severity                TEXT NOT NULL,
    nist_default_value      TEXT NOT NULL,
    org_value               TEXT NOT NULL,
    resolution_suggestion   TEXT,
    resolved                INTEGER DEFAULT 0,
    detected_at             DATETIME DEFAULT CURRENT_TIMESTAMP,
    CHECK (severity IN ('WARNING', 'BLOCKED')),
    CHECK (resolved IN (0, 1)),
    CHECK (conflict_type IN (
        'SEVERITY_DOWNGRADE', 'AUTO_CONTAIN_DISABLED', 'SLA_EXCEEDED',
        'FORENSIC_LEVEL_REDUCED', 'COMPLIANCE_REPORT_SKIPPED',
        'THRESHOLD_INCREASED', 'ESCALATION_REMOVED', 'NOTIFY_REMOVED'
    )),
    FOREIGN KEY (organization_odp_id) REFERENCES organization_odps(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- 6. Create indexes
-- ---------------------------------------------------------------------------

-- NIST baselines indexes
CREATE INDEX IF NOT EXISTS idx_nist_type ON nist_baselines(incident_type);

-- Organization ODPs indexes
CREATE INDEX IF NOT EXISTS idx_odp_baseline ON organization_odps(nist_baseline_id);
CREATE INDEX IF NOT EXISTS idx_odp_key ON organization_odps(odp_key);

-- Policy versions indexes
CREATE INDEX IF NOT EXISTS idx_policy_version ON policy_versions(version_number);
CREATE INDEX IF NOT EXISTS idx_policy_version_created ON policy_versions(created_at DESC);

-- ODP conflicts indexes
CREATE INDEX IF NOT EXISTS idx_conflict_odp ON odp_conflicts(organization_odp_id);
CREATE INDEX IF NOT EXISTS idx_conflict_type ON odp_conflicts(conflict_type);
CREATE INDEX IF NOT EXISTS idx_conflict_unresolved ON odp_conflicts(resolved, detected_at DESC);

-- Incidents ODP indexes
CREATE INDEX IF NOT EXISTS idx_incidents_odp_override ON incidents(odp_override_applied);

-- ---------------------------------------------------------------------------
-- 7. Create resolved_policies view
-- ---------------------------------------------------------------------------

CREATE VIEW IF NOT EXISTS resolved_policies AS
SELECT
    nb.id as baseline_id,
    nb.incident_type,
    COALESCE(oo_severity.odp_value, nb.default_severity) as resolved_severity,
    COALESCE(oo_contain.odp_value, CAST(nb.default_auto_contain AS TEXT)) as resolved_auto_contain,
    COALESCE(oo_escalation.odp_value, '') as resolved_escalation,
    COALESCE(oo_sla.odp_value, CAST(nb.default_response_sla_minutes AS TEXT)) as resolved_sla,
    COALESCE(oo_forensic.odp_value, nb.default_forensic_level) as resolved_forensic,
    COALESCE(oo_notify.odp_value, '') as resolved_notify,
    COALESCE(oo_compliance.odp_value, nb.default_compliance_report) as resolved_compliance,
    COALESCE(oo_threshold.odp_value, CAST(nb.default_record_threshold AS TEXT)) as resolved_threshold
FROM nist_baselines nb
LEFT JOIN organization_odps oo_severity ON nb.id = oo_severity.nist_baseline_id AND oo_severity.odp_key = 'severity_threshold'
LEFT JOIN organization_odps oo_contain ON nb.id = oo_contain.nist_baseline_id AND oo_contain.odp_key = 'auto_contain_enabled'
LEFT JOIN organization_odps oo_escalation ON nb.id = oo_escalation.nist_baseline_id AND oo_escalation.odp_key = 'escalation_contacts'
LEFT JOIN organization_odps oo_sla ON nb.id = oo_sla.nist_baseline_id AND oo_sla.odp_key = 'response_time_sla'
LEFT JOIN organization_odps oo_forensic ON nb.id = oo_forensic.nist_baseline_id AND oo_forensic.odp_key = 'forensic_level'
LEFT JOIN organization_odps oo_notify ON nb.id = oo_notify.nist_baseline_id AND oo_notify.odp_key = 'notify_targets'
LEFT JOIN organization_odps oo_compliance ON nb.id = oo_compliance.nist_baseline_id AND oo_compliance.odp_key = 'compliance_report'
LEFT JOIN organization_odps oo_threshold ON nb.id = oo_threshold.nist_baseline_id AND oo_threshold.odp_key = 'record_threshold';

-- ---------------------------------------------------------------------------
-- 8. Update existing incidents table
-- ---------------------------------------------------------------------------

-- SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN.
-- These must be handled by the application migration runner:
-- ALTER TABLE incidents ADD COLUMN resolved_policy_id INTEGER;
-- ALTER TABLE incidents ADD COLUMN odp_override_applied INTEGER NOT NULL DEFAULT 0;

-- ---------------------------------------------------------------------------
-- 9. Update schema version
-- ---------------------------------------------------------------------------

PRAGMA user_version = 3;

COMMIT;
```

#### 6.4 Rollback Procedure

If migration fails or needs to be reverted:

**Rollback from v3 to v2:**

```sql
-- ============================================================================
-- Rollback: 003_odp_system_rollback.sql
-- Description: Removes ODP tables and view added in version 3.
-- WARNING: This will delete all ODP data. Back up first.
-- ============================================================================

BEGIN TRANSACTION;

-- Drop view first (no dependencies)
DROP VIEW IF EXISTS resolved_policies;

-- Drop tables in dependency order
DROP TABLE IF EXISTS odp_conflicts;
DROP TABLE IF EXISTS organization_odps;
DROP TABLE IF EXISTS policy_versions;
DROP TABLE IF EXISTS industry_templates;
DROP TABLE IF EXISTS nist_baselines;

-- Drop ODP-specific indexes on incidents
DROP INDEX IF EXISTS idx_incidents_odp_override;

-- Note: SQLite does not support DROP COLUMN.
-- The resolved_policy_id and odp_override_applied columns in incidents
-- will remain but will not be populated. To fully remove them:
-- 1. CREATE TABLE incidents_new (without the columns)
-- 2. INSERT INTO incidents_new SELECT ... (without the columns)
-- 3. DROP TABLE incidents
-- 4. ALTER TABLE incidents_new RENAME TO incidents
-- 5. Recreate all indexes and triggers on incidents

PRAGMA user_version = 2;

COMMIT;
```

**Rollback from v2 to v1:**

```sql
-- ============================================================================
-- Rollback: 002_judge_layer_rollback.sql
-- Description: Removes Judge Layer tables added in version 2.
-- WARNING: This will delete all Judge Layer data. Back up first.
-- ============================================================================

BEGIN TRANSACTION;

-- Drop tables in dependency order
DROP TABLE IF EXISTS bypass_attempts;
DROP TABLE IF EXISTS bypass_patterns;
DROP TABLE IF EXISTS suprawall_events;
DROP TABLE IF EXISTS judge_decisions;

-- Drop Judge Layer-specific indexes on incidents and agents
DROP INDEX IF EXISTS idx_incidents_bypass_detected;
DROP INDEX IF EXISTS idx_incidents_judge_decision;
DROP INDEX IF EXISTS idx_agents_suprawall;
DROP INDEX IF EXISTS idx_agents_bypass_count;

-- Note: The judge_decision_count, bypass_attempt_count, and suprawall_connected
-- columns on agents, and judge_decision_id, bypass_detected, and
-- deterministic_classification columns on incidents will remain but will
-- not be populated. Use the CREATE TABLE / INSERT / RENAME pattern to
-- fully remove them (see v3 rollback notes above).

PRAGMA user_version = 1;

COMMIT;
```

#### 6.5 Downgrade Compatibility Matrix

| From | To | Compatible? | Notes |
|------|----|---|---|
| v3 | v2 | Partial | ODP tables/view are dropped; incidents retains ODP columns but they are unused |
| v3 | v1 | No | Must roll back through v2 first (ODP -> Judge Layer -> v1) |
| v2 | v3 | Yes | Idempotent -- running v3 migration on v2 database is safe |
| v2 | v1 | Partial | Judge Layer tables are dropped; incidents/agents retain columns but unused |
| v1 | v2 | Yes | Idempotent -- running v2 migration on v1 database is safe |
| v1 | v3 | Yes | Idempotent -- running both v2 then v3 migrations on v1 database is safe |

#### 6.6 Idempotency Notes

All migration scripts are designed to be idempotent:

1. **`CREATE TABLE IF NOT EXISTS`** -- Tables are created only if they don't already exist
2. **`CREATE INDEX IF NOT EXISTS`** -- Indexes are created only if they don't already exist
3. **`CREATE VIEW IF NOT EXISTS`** -- Views are created only if they don't already exist
4. **`PRAGMA user_version`** -- Version is set at the end of each migration
5. **Application-level column additions** -- The `ALTER TABLE ADD COLUMN` statements for SQLite are commented out and must be handled by the application migration runner, which should check `PRAGMA table_info(table_name)` before adding columns

This idempotency allows migrations to be safely re-run without error, and supports forward-migration paths (e.g., v1 -> v3 by running v2 then v3 migrations in sequence).

---

*End of Database Schema Document*
