import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ============================================================================
# CORE PIPELINE TABLES (11)
# ============================================================================

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    incident_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    event_id: Mapped[str] = mapped_column(String(36), nullable=True)
    score_id: Mapped[str] = mapped_column(String(36), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(20), nullable=False, default="AGT-GAP-012")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    local_rule_id: Mapped[str] = mapped_column(String(50), nullable=True)
    gemini_cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    playbook_id: Mapped[str] = mapped_column(String(50), nullable=True)
    response_status: Mapped[str] = mapped_column(String(20), default="pending")
    forensics_status: Mapped[str] = mapped_column(String(20), default="pending")

    # Judge Layer
    judge_decision_id: Mapped[str] = mapped_column(String(36), nullable=True)
    bypass_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    deterministic_classification: Mapped[bool] = mapped_column(Boolean, default=True)

    # Policy Builder
    resolved_policy_id: Mapped[str] = mapped_column(String(36), nullable=True)
    odp_override_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    # Relationships
    metadata_rel: Mapped["IncidentMetadata"] = relationship(
        back_populates="incident", uselist=False
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="incident"
    )
    response_record: Mapped["ResponseRecord"] = relationship(
        back_populates="incident", uselist=False
    )
    forensics_package: Mapped["EvidencePackage"] = relationship(
        back_populates="incident", uselist=False
    )
    human_reviews: Mapped[list["HumanReviewTask"]] = relationship(
        back_populates="incident"
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    system_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    health_score: Mapped[int] = mapped_column(Integer, default=100)
    lie_rate: Mapped[float] = mapped_column(Float, default=0.0)
    incident_count: Mapped[int] = mapped_column(Integer, default=0)
    bypass_attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    judge_decision_count: Mapped[int] = mapped_column(Integer, default=0)
    suprawall_connected: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )


class Playbook(Base):
    __tablename__ = "playbooks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    playbook_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    incident_type: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    auto_execute: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    actions: Mapped[list["PlaybookAction"]] = relationship(back_populates="playbook")


class PlaybookAction(Base):
    __tablename__ = "playbook_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    playbook_id: Mapped[str] = mapped_column(
        ForeignKey("playbooks.id"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target: Mapped[str] = mapped_column(String(100), nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)

    playbook: Mapped["Playbook"] = relationship(back_populates="actions")


class EvidencePackage(Base):
    __tablename__ = "evidence_packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    package_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )
    response_id: Mapped[str] = mapped_column(String(36), nullable=True)

    package_type: Mapped[str] = mapped_column(String(50), default="full")
    package_data: Mapped[dict] = mapped_column(JSON, default=dict)
    export_path: Mapped[str] = mapped_column(String(500), nullable=True)
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    retention_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    incident: Mapped["Incident"] = relationship(back_populates="forensics_package")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(50), default="system")
    actor_id: Mapped[str] = mapped_column(String(100), nullable=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class GeminiCache(Base):
    __tablename__ = "gemini_cache"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    cache_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AgentHealthHistory(Base):
    __tablename__ = "agent_health_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=False)
    health_score: Mapped[int] = mapped_column(Integer, nullable=False)
    lie_rate: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    rule_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(20), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )


class DemoScenario(Base):
    __tablename__ = "demo_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    scenario_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    scenario_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ComplianceMapping(Base):
    __tablename__ = "compliance_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    incident_type: Mapped[str] = mapped_column(String(20), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    control_id: Mapped[str] = mapped_column(String(100), nullable=False)
    control_name: Mapped[str] = mapped_column(String(200), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    mapping_data: Mapped[dict] = mapped_column(JSON, default=dict)


# ============================================================================
# JUDGE LAYER TABLES (4)
# ============================================================================

class JudgeDecision(Base):
    __tablename__ = "judge_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    decision_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    agent_id: Mapped[str] = mapped_column(String(36), nullable=True)

    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    severity_score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    matched_rules: Mapped[list] = mapped_column(JSON, default=list)
    bypass_patterns_detected: Mapped[list] = mapped_column(JSON, default=list)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)

    # ODP
    resolved_policy_id: Mapped[str] = mapped_column(String(36), nullable=True)
    odp_overrides: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    # NOTE: No updated_at — judge decisions are immutable


class BypassPattern(Base):
    __tablename__ = "bypass_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    pattern_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(100), nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detection_logic: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BypassAttempt(Base):
    __tablename__ = "bypass_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    incident_id: Mapped[str] = mapped_column(String(36), nullable=False)
    pattern_id: Mapped[str] = mapped_column(
        ForeignKey("bypass_patterns.id"), nullable=False
    )
    detection_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    payload_sample: Mapped[str] = mapped_column(Text, nullable=True)
    blocked_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    pattern: Mapped["BypassPattern"] = relationship()


class SuprawallEvent(Base):
    __tablename__ = "suprawall_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(100), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=True)
    client_ip: Mapped[str] = mapped_column(String(45), nullable=True)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=True)
    matched_rules: Mapped[list] = mapped_column(JSON, default=list)
    risk_score: Mapped[float] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    framework: Mapped[str] = mapped_column(String(100), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


# ============================================================================
# POLICY BUILDER TABLES (5)
# ============================================================================

class NistBaseline(Base):
    __tablename__ = "nist_baselines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    baseline_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    incident_type: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    severity: Mapped[str] = mapped_column(String(20), nullable=False)

    # 8 ODP defaults
    severity_threshold: Mapped[str] = mapped_column(String(20), nullable=False)
    auto_contain_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    escalation_contacts: Mapped[list] = mapped_column(JSON, default=list)
    response_time_sla_seconds: Mapped[int] = mapped_column(Integer, default=1800)
    forensic_level: Mapped[str] = mapped_column(String(20), default="standard")
    notify_targets: Mapped[list] = mapped_column(JSON, default=list)
    compliance_report: Mapped[bool] = mapped_column(Boolean, default=False)
    record_threshold: Mapped[int] = mapped_column(Integer, default=1)

    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # NOTE: Baselines are immutable — no updated_at


class OrganizationODP(Base):
    __tablename__ = "organization_odps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    baseline_id: Mapped[str] = mapped_column(
        ForeignKey("nist_baselines.id"), nullable=False
    )
    odp_key: Mapped[str] = mapped_column(String(100), nullable=False)
    odp_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(20), default="string")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        # Unique constraint: one ODP key per baseline
        {"sqlite_autoincrement": True},
    )


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    baseline_id: Mapped[str] = mapped_column(String(36), nullable=False)
    odp_id: Mapped[str] = mapped_column(String(36), nullable=True)
    changed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_value: Mapped[str] = mapped_column(Text, nullable=True)
    to_value: Mapped[str] = mapped_column(Text, nullable=True)
    change_reason: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class IndustryTemplate(Base):
    __tablename__ = "industry_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    template_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    odp_set: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ODPConflict(Base):
    __tablename__ = "odp_conflicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    conflict_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    baseline_id: Mapped[str] = mapped_column(String(36), nullable=False)
    odp_id: Mapped[str] = mapped_column(String(36), nullable=False)

    conflict_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="WARNING")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    expected_value: Mapped[str] = mapped_column(Text, nullable=True)
    actual_value: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="open")
    resolved_by: Mapped[str] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


# ============================================================================
# SUPPORTING TABLES
# ============================================================================

class IncidentMetadata(Base):
    __tablename__ = "incident_metadata"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )

    intent_category: Mapped[str] = mapped_column(String(100), nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=True)
    contains_injection_patterns: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_credentials: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_exfiltration: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_system_commands: Mapped[bool] = mapped_column(Boolean, default=False)
    full_metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    incident: Mapped["Incident"] = relationship(back_populates="metadata_rel")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    stage: Mapped[str] = mapped_column(String(20), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_description: Mapped[str] = mapped_column(Text, nullable=False)
    source_component: Mapped[str] = mapped_column(String(100), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)

    incident: Mapped["Incident"] = relationship(back_populates="timeline_events")


class ResponseRecord(Base):
    __tablename__ = "response_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    response_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )
    playbook_id: Mapped[str] = mapped_column(String(50), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    steps_total: Mapped[int] = mapped_column(Integer, default=0)
    steps_completed: Mapped[int] = mapped_column(Integer, default=0)
    steps_failed: Mapped[int] = mapped_column(Integer, default=0)
    steps_pending_review: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[str] = mapped_column(Text, nullable=True)

    incident: Mapped["Incident"] = relationship(back_populates="response_record")
    steps: Mapped[list["ResponseStep"]] = relationship(back_populates="response_record")


class ResponseStep(Base):
    __tablename__ = "response_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    response_id: Mapped[str] = mapped_column(
        ForeignKey("response_records.id"), nullable=False
    )
    step_id: Mapped[str] = mapped_column(String(50), nullable=False)
    step_name: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")

    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    policy_file: Mapped[str] = mapped_column(String(500), nullable=True)
    cli_command: Mapped[str] = mapped_column(Text, nullable=True)
    cli_stdout: Mapped[str] = mapped_column(Text, nullable=True)
    cli_stderr: Mapped[str] = mapped_column(Text, nullable=True)
    cli_returncode: Mapped[int] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)

    response_record: Mapped["ResponseRecord"] = relationship(back_populates="steps")
    human_reviews: Mapped[list["HumanReviewTask"]] = relationship(
        back_populates="response_step"
    )


class HumanReviewTask(Base):
    __tablename__ = "human_review_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    task_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), nullable=False
    )
    step_record_id: Mapped[str] = mapped_column(
        ForeignKey("response_steps.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    sla_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)
    override_action: Mapped[str] = mapped_column(String(50), nullable=True)

    incident: Mapped["Incident"] = relationship(back_populates="human_reviews")
    response_step: Mapped["ResponseStep"] = relationship(
        back_populates="human_reviews"
    )


# ============================================================================
# RESOLVED POLICIES VIEW
# ============================================================================

from sqlalchemy import select, text

# This VIEW computes the effective policy per incident type by merging
# NIST baselines with organizational ODPs.
# It is created via raw SQL in the Alembic migration.
ResolvedPolicyView = select(
    NistBaseline.id.label("baseline_id"),
    NistBaseline.incident_type,
    NistBaseline.severity.label("baseline_severity"),
    NistBaseline.auto_contain_enabled.label("baseline_auto_contain"),
    NistBaseline.escalation_contacts.label("baseline_escalation_contacts"),
    NistBaseline.response_time_sla_seconds.label("baseline_sla"),
    NistBaseline.forensic_level.label("baseline_forensic_level"),
    NistBaseline.notify_targets.label("baseline_notify_targets"),
    NistBaseline.compliance_report.label("baseline_compliance_report"),
    NistBaseline.record_threshold.label("baseline_record_threshold"),
    OrganizationODP.odp_key,
    OrganizationODP.odp_value,
    OrganizationODP.value_type,
).select_from(
    NistBaseline
).where(
    NistBaseline.is_active == True
).outerjoin(
    OrganizationODP,
    (NistBaseline.id == OrganizationODP.baseline_id) & (OrganizationODP.is_active == True)
)


# Raw SQL for creating the view in migrations
RESOLVED_POLICIES_VIEW_SQL = """
CREATE VIEW IF NOT EXISTS resolved_policies AS
SELECT
    nb.id AS baseline_id,
    nb.incident_type,
    nb.severity AS baseline_severity,
    nb.auto_contain_enabled AS baseline_auto_contain,
    nb.escalation_contacts AS baseline_escalation_contacts,
    nb.response_time_sla_seconds AS baseline_sla,
    nb.forensic_level AS baseline_forensic_level,
    nb.notify_targets AS baseline_notify_targets,
    nb.compliance_report AS baseline_compliance_report,
    nb.record_threshold AS baseline_record_threshold,
    ood.odp_key,
    ood.odp_value,
    ood.value_type
FROM nist_baselines nb
LEFT JOIN organization_odps ood ON nb.id = ood.baseline_id AND ood.is_active = 1
WHERE nb.is_active = 1;
"""

# ============================================================================
# AUDIT TRIGGERS (via SQLAlchemy events)
# ============================================================================

@event.listens_for(Incident, "after_insert")
def audit_incident_insert(mapper, connection, target):
    """Log incident creation to audit_log."""
    connection.execute(
        AuditLog.__table__.insert().values(
            action="create",
            actor_type="system",
            target_type="incident",
            target_id=target.id,
            details={"incident_id": target.incident_id, "severity": target.severity},
        )
    )


@event.listens_for(Incident, "after_update")
def audit_incident_update(mapper, connection, target):
    """Log incident status/severity changes to audit_log."""
    from sqlalchemy import inspect

    state = inspect(target)
    changes = {}
    for attr in state.attrs:
        hist = state.get_history(attr.key, True)
        if hist.has_changes():
            changes[attr.key] = {
                "old": hist.deleted[0] if hist.deleted else None,
                "new": hist.added[0] if hist.added else None,
            }

    if changes:
        connection.execute(
            AuditLog.__table__.insert().values(
                action="update",
                actor_type="system",
                target_type="incident",
                target_id=target.id,
                details=changes,
            )
        )
