from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class IncidentStatus(str, Enum):
    NEW = "new"
    DETECTED = "detected"
    CLASSIFIED = "classified"
    INVESTIGATING = "investigating"
    RESPONDING = "responding"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"
    CLOSED = "closed"


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class JudgeVerdict(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"
    ESCALATE = "ESCALATE"


class PlaybookActionType(str, Enum):
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"
    RATE_LIMIT = "RATE_LIMIT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    NOTIFY = "NOTIFY"
    FORENSICS = "FORENSICS"
    ISOLATE = "ISOLATE"
    LOG_EXTENDED = "LOG_EXTENDED"


class BypassPattern(str, Enum):
    CONTEXT_WINDOW_DISPLACEMENT = "context_window_displacement"
    INDIRECT_TOOL_CHAINING = "indirect_tool_chaining"
    UNICODE_HOMOGLYPH = "unicode_homoglyph"
    CONFIDENCE_HIJACKING = "confidence_hijacking"


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    CLASSIFY = "classify"
    RESPOND = "respond"
    JUDGE = "judge"
    EXPORT = "export"
    PURGE = "purge"
    LOGIN = "login"
    LOGOUT = "logout"


class ActorType(str, Enum):
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"
    API = "api"


class ODPConflictSeverity(str, Enum):
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


class ODPConflictType(str, Enum):
    SEVERITY_DOWNGRADE = "SEVERITY_DOWNGRADE"
    MISSING_REQUIRED = "MISSING_REQUIRED"
    VALUE_MISMATCH = "VALUE_MISMATCH"
    THRESHOLD_VIOLATION = "THRESHOLD_VIOLATION"


class Framework(str, Enum):
    EU_AI_ACT = "eu_ai_act"
    NIST_AI_RMF = "nist_ai_rmf"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO_23053 = "iso_23053"


class EvidenceType(str, Enum):
    LOGS = "logs"
    CONTEXT = "context"
    CLASSIFICATION = "classification"
    RESPONSE = "response"
    COMPLIANCE = "compliance"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class ResponseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"


# 16 Incident Types
INCIDENT_TYPES = {
    "AGT-DEL-001": "Data Destruction",
    "AGT-FIN-002": "Unauthorized Financial",
    "AGT-PER-003": "Permission Escalation",
    "AGT-HRM-004": "Harmful Output",
    "AGT-EXT-005": "Data Exfiltration",
    "AGT-INJ-006": "Prompt Injection",
    "AGT-HAL-007": "Hallucination Cascade",
    "AGT-CRE-008": "Credential Exposure",
    "AGT-RAT-009": "Rate Limit Abuse",
    "AGT-DRF-010": "Model Drift",
    "AGT-TLM-011": "Tool Misuse",
    "AGT-GAP-012": "Coverage Gap",
    "AGT-SPY-013": "Systematic Espionage",
    "AGT-BYP-014": "Guardrail Bypass",
    "AGT-PRV-015": "Privacy Violation",
    "AGT-REG-016": "Regulatory Trigger",
    "AGT-POL-017": "Organization Policy Switching",
}

# 8 ODP Keys
ODP_KEYS = [
    "severity_threshold",
    "auto_contain_enabled",
    "escalation_contacts",
    "response_time_sla",
    "forensic_level",
    "notify_targets",
    "compliance_report",
    "record_threshold",
]

# 6 Industry Templates
INDUSTRY_TEMPLATES = [
    "HIPAA",
    "SOC2",
    "PCI-DSS",
    "GDPR",
    "Financial Services",
    "SaaS Startup",
]

# Latency targets (ms)
LATENCY_TARGETS = {
    "detection": 10,
    "judge_core": 40,
    "judge_p95": 50,
    "judge_p99": 100,
    "response": 150,
    "e2e_p95": 200,
    "e2e_hard_ceiling": 500,
}

# Rate limits
RATE_LIMIT_DEFAULT = 100  # requests per minute
RATE_LIMIT_BURST = 10

# Data retention (days)
RETENTION_DAYS = {
    "incidents": 90,
    "audit_logs": 90,
    "full_prompts": 30,
    "evidence_packages": 2555,
    "benign_events": 30,
}

# File size limits
MAX_PROMPT_LENGTH = 10000
MAX_DB_SIZE_MB = 500
MAX_LOG_SIZE_MB = 10
MAX_LOG_FILES = 7
