from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Base Response
# ============================================================================

class StandardResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: Dict[str, Any]
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Notifications
# ============================================================================

class NotificationTestRequest(BaseModel):
    channel: str = "slack"
    message: str = "Test notification from PLAYBOOK"
    severity: Optional[str] = "high"
    incident_id: Optional[str] = None


class NotificationTestResponse(BaseModel):
    channel: str
    success: bool
    detail: str


# ============================================================================
# Health
# ============================================================================

class HealthCheck(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "0.1.0"
    components: Dict[str, str] = Field(default_factory=dict)


# ============================================================================
# Incidents
# ============================================================================

class IncidentBase(BaseModel):
    incident_type: str
    severity: str
    confidence: float = Field(ge=0.0, le=1.0)
    category: str


class IncidentCreate(IncidentBase):
    event_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EventIngestRequest(BaseModel):
    """Request to ingest a raw agent event."""

    source: str = "generic"  # lobstertrap, terrabric, suprawall, generic
    event_data: Dict[str, Any] = Field(default_factory=dict)


class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    event_id: Optional[str] = None
    status: str
    playbook_id: Optional[str] = None
    response_status: str
    forensics_status: str
    judge_verdict: Optional[str] = None
    bypass_detected: bool = False
    created_at: datetime
    updated_at: datetime


class IncidentListResponse(BaseModel):
    data: List[IncidentResponse]
    total: int
    page: int
    page_size: int


class IncidentFilter(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 50


# ============================================================================
# Judge Layer
# ============================================================================

class JudgeEvaluateRequest(BaseModel):
    action: str
    agent_id: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JudgeEvaluateResponse(BaseModel):
    verdict: str
    severity_score: int = Field(ge=1, le=10)
    confidence: float
    matched_rules: List[str] = Field(default_factory=list)
    bypass_patterns_detected: List[str] = Field(default_factory=list)
    rationale: str
    latency_ms: float
    resolved_policy_id: Optional[str] = None


class JudgeStats(BaseModel):
    total_decisions: int
    verdict_distribution: Dict[str, int]
    avg_latency_ms: float
    p95_latency_ms: float
    bypass_attempts_blocked: int


class BypassPatternResponse(BaseModel):
    id: str
    pattern_name: str
    canonical_name: str
    aliases: List[str]
    description: str
    severity: int
    is_active: bool


class BypassAttemptResponse(BaseModel):
    id: str
    incident_id: str
    pattern_id: str
    detection_confidence: float
    blocked_at: datetime


# ============================================================================
# Playbooks
# ============================================================================

class PlaybookActionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_order: int
    name: str
    action_type: str
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int


class PlaybookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    playbook_id: str
    name: str
    version: str
    incident_type: str
    description: Optional[str] = None
    auto_execute: bool
    is_active: bool
    actions: List[PlaybookActionSchema] = Field(default_factory=list)


# ============================================================================
# Policy Builder
# ============================================================================

class NistBaselineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    baseline_id: str
    incident_type: str
    version: str
    severity: str
    severity_threshold: str
    auto_contain_enabled: bool
    escalation_contacts: List[str]
    response_time_sla_seconds: int
    forensic_level: str
    notify_targets: List[str]
    compliance_report: bool
    record_threshold: int
    description: Optional[str] = None


class ODPUpdateRequest(BaseModel):
    odp_key: str
    odp_value: str
    value_type: str = "string"


class ODPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    baseline_id: str
    odp_key: str
    odp_value: str
    value_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResolvedPolicyResponse(BaseModel):
    incident_type: str
    baseline: NistBaselineResponse
    odps: List[ODPResponse] = Field(default_factory=list)
    effective_policy: Dict[str, Any] = Field(default_factory=dict)


class IndustryTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    name: str
    description: Optional[str] = None
    odp_set: Dict[str, Any] = Field(default_factory=dict)


class ODPConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conflict_id: str
    conflict_type: str
    severity: str
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    status: str
    created_at: datetime


class PolicyVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version_number: int
    baseline_id: str
    changed_by: Optional[str] = None
    change_type: str
    from_value: Optional[str] = None
    to_value: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: datetime


class ODPEntryResponse(BaseModel):
    """Structured ODP entry with override tracking."""
    value: str
    is_override: bool = False
    nist_default: Optional[str] = None
    value_type: str = "string"


class ODPsForTypeResponse(BaseModel):
    """Full ODP response for an incident type per API spec."""
    incident_type: str
    incident_name: Optional[str] = None
    odp_count: int = 0
    version: str = "1.0"
    odps: Dict[str, ODPEntryResponse] = Field(default_factory=dict)
    conflicts_detected: int = 0
    last_updated: Optional[datetime] = None
    updated_by: Optional[str] = None


class ODPsUpdateBody(BaseModel):
    """Request body for updating multiple ODPs at once."""
    odps: Dict[str, str] = Field(default_factory=dict)
    skip_validation: bool = False


class ODPsUpdateResponse(BaseModel):
    """Response from multi-ODP update."""
    incident_type: str
    odps_applied: int
    conflicts_detected: int
    version: int
    resolved_policy: Dict[str, Any] = Field(default_factory=dict)


class ConflictDetail(BaseModel):
    """Single conflict detail within validation results."""
    type: str
    severity: str
    message: str
    nist_value: Optional[str] = None
    odp_value: Optional[str] = None
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Per-incident-type validation result."""
    incident_type: str
    valid: bool
    conflicts: List[ConflictDetail] = Field(default_factory=list)


class ValidateResponse(BaseModel):
    """Full validation response."""
    valid: bool
    total_validated: int
    total_conflicts: int
    results: List[ValidationResult] = Field(default_factory=list)


class TemplateApplyBody(BaseModel):
    """Request body for applying a template."""
    incident_types: Optional[List[str]] = None
    overwrite_existing: bool = True
    dry_run: bool = False


class TemplateApplyResult(BaseModel):
    """Per-incident-type template application result."""
    incident_type: str
    odps_applied: int
    odps_skipped: int
    conflicts_detected: int
    version: int


class TemplateApplyResponse(BaseModel):
    """Full template apply response."""
    template_id: str
    dry_run: bool
    results: List[TemplateApplyResult] = Field(default_factory=list)
    total_applied: int
    total_conflicts: int


class RollbackBody(BaseModel):
    """Request body for rollback."""
    description: Optional[str] = None
    dry_run: bool = False


class RollbackResponse(BaseModel):
    """Full rollback response."""
    rolled_back_from: int
    rolled_back_to: int
    new_version: int
    description: Optional[str] = None
    changes: List[Dict[str, Any]] = Field(default_factory=list)


class ConflictResolveBody(BaseModel):
    """Request body for resolving a conflict."""
    resolution: str = "accept_suggestion"
    custom_value: Optional[str] = None
    note: Optional[str] = None


class ConflictResolveResponse(BaseModel):
    """Full conflict resolution response."""
    conflict_id: str
    status: str
    resolution: str
    previous_value: Optional[str] = None
    new_value: Optional[str] = None
    note: Optional[str] = None
    resolved_by: Optional[str] = None


# ============================================================================
# Forensics
# ============================================================================

class EvidencePackageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    package_id: str
    incident_id: str
    package_type: str
    export_path: Optional[str] = None
    integrity_hash: Optional[str] = None
    is_verified: bool
    created_at: datetime


class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    stage: str
    event_type: str
    event_description: str
    source_component: str
    details_json: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Compliance
# ============================================================================

class ComplianceReportRequest(BaseModel):
    incident_id: str
    framework: Optional[str] = None


class ComplianceReportResponse(BaseModel):
    incident_id: str
    framework: str
    report_format: str
    report_data: Dict[str, Any]
    generated_at: datetime


class ComplianceMappingResponse(BaseModel):
    incident_type: str
    framework: str
    control_id: str
    control_name: str
    risk_level: str
    confidence: float


# ============================================================================
# Demo
# ============================================================================

class DemoSeedRequest(BaseModel):
    scenario: str = "default"
    agent_count: int = 5
    incident_count: int = 25
    clear_existing: bool = True
    include_judge_decisions: bool = True
    include_bypass_attempts: bool = True


class DemoSeedResponse(BaseModel):
    success: bool = True
    message: str = "Demo data seeded successfully"
    scenario: str = "default"
    seeded: Dict[str, int] = Field(default_factory=dict)
    clear_existing: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DemoTriggerRequest(BaseModel):
    scenario: str
    target_agent_id: Optional[str] = None
    severity: Optional[str] = None
    auto_classify: bool = True
    auto_respond: bool = True
    delay_seconds: int = 0


# ============================================================================
# WebSocket
# ============================================================================

class WebSocketMessage(BaseModel):
    action: str
    data: Optional[Dict[str, Any]] = None


class WebSocketEvent(BaseModel):
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
