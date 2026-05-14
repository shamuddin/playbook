"""Pydantic models for PLAYBOOK API types."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class JudgeVerdict(BaseModel):
    """Response from the Judge Layer evaluation."""

    verdict: str = Field(..., description="ALLOW, BLOCK, QUARANTINE, or ESCALATE")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: Optional[str] = None
    severity_score: int = Field(default=0, ge=0, le=10)
    latency_ms: float = Field(default=0.0)
    regulatory_tags: list[str] = Field(default_factory=list)


class IncidentReport(BaseModel):
    """Incident report payload."""

    incident_type: str
    severity: str
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    category: str = "unknown"
    event_id: str = ""
    agent_id: Optional[str] = None


class AgentHeartbeat(BaseModel):
    """Agent heartbeat payload."""

    health_score: float = Field(default=100.0, ge=0.0, le=100.0)
    lie_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_score: Optional[int] = None
