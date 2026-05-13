"""PB-CES (Playbook Common Event Schema) normalizer.

Converts raw agent events from any source into a canonical format.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


class NormalizationError(ValueError):
    """Raised when an event cannot be normalized."""

    pass


@dataclass
class PB_CES_Event:
    """Canonical event schema for PLAYBOOK ingestion.

    All fields have sensible defaults so partial events can still be processed.
    """

    event_id: str
    source: str  # "lobstertrap", "terrabric", "suprawall", "generic"
    event_type: str
    agent_id: str = "unknown"
    session_id: str = ""
    tool_call: str = ""
    output: str = ""
    judge_decision: str = ""  # ALLOW, DENY, QUARANTINE, ESCALATE, or empty
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)


def _generate_event_id() -> str:
    """Generate a unique event ID."""
    return f"EVT-{uuid.uuid4().hex[:12].upper()}"


def _ensure_timestamp(ts: Any) -> datetime:
    """Coerce various timestamp formats to datetime."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(ts, str):
        # Try ISO format first
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            pass
        # Try common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)


def normalize_lobstertrap(raw: Dict[str, Any]) -> PB_CES_Event:
    """Normalize a Lobster Trap DPI event.

    Expected Lobster Trap format:
    {
        "event_id": "lt-abc123",
        "agent_id": "agent-001",
        "session_id": "sess-xyz",
        "action": "tool_call",
        "tool": "database.query",
        "input": "SELECT * FROM users",
        "output": "...",
        "decision": "ALLOW",
        "timestamp": "2024-01-15T10:30:00Z",
        "risk_score": 0.2,
        ...
    }
    """
    if not isinstance(raw, dict):
        raise NormalizationError("Lobster Trap event must be a dict")

    return PB_CES_Event(
        event_id=raw.get("event_id") or _generate_event_id(),
        source="lobstertrap",
        event_type=raw.get("action", "unknown"),
        agent_id=raw.get("agent_id", "unknown"),
        session_id=raw.get("session_id", ""),
        tool_call=raw.get("tool", "") + " " + raw.get("input", ""),
        output=raw.get("output", ""),
        judge_decision=raw.get("decision", ""),
        context=raw.get("context", ""),
        metadata={
            "risk_score": raw.get("risk_score", 0.0),
            "source_format": "lobstertrap",
            **{k: v for k, v in raw.items() if k not in {
                "event_id", "agent_id", "session_id", "action", "tool",
                "input", "output", "decision", "context", "timestamp"
            }},
        },
        timestamp=_ensure_timestamp(raw.get("timestamp")),
        raw_data=raw,
    )


def normalize_terrabric(raw: Dict[str, Any]) -> PB_CES_Event:
    """Normalize a TerraFabric fleet management event.

    Expected TerraFabric format:
    {
        "id": "tf-001",
        "agent": {"id": "agent-001", "name": "DataBot"},
        "event": "anomaly_detected",
        "details": {"tool": "api.call", "args": {...}},
        "severity": "high",
        "timestamp": 1705317000,
        ...
    }
    """
    if not isinstance(raw, dict):
        raise NormalizationError("TerraFabric event must be a dict")

    agent_info = raw.get("agent", {})
    details = raw.get("details", {})

    return PB_CES_Event(
        event_id=raw.get("id") or _generate_event_id(),
        source="terrabric",
        event_type=raw.get("event", "unknown"),
        agent_id=agent_info.get("id", "unknown") if isinstance(agent_info, dict) else str(agent_info),
        session_id=raw.get("session_id", ""),
        tool_call=details.get("tool", "") + " " + str(details.get("args", "")),
        output=details.get("result", ""),
        judge_decision=raw.get("guardrail_decision", ""),
        context=raw.get("context", ""),
        metadata={
            "severity": raw.get("severity", "medium"),
            "source_format": "terrabric",
            **{k: v for k, v in raw.items() if k not in {
                "id", "agent", "event", "details", "severity", "timestamp", "session_id", "context"
            }},
        },
        timestamp=_ensure_timestamp(raw.get("timestamp")),
        raw_data=raw,
    )


def normalize_generic(raw: Dict[str, Any]) -> PB_CES_Event:
    """Normalize a generic/unstructured event.

    Attempts to extract known fields via common key names.
    """
    if not isinstance(raw, dict):
        raise NormalizationError("Event must be a dict")

    # Common key mappings
    event_id = (
        raw.get("event_id")
        or raw.get("id")
        or raw.get("eventId")
        or _generate_event_id()
    )
    agent_id = (
        raw.get("agent_id")
        or raw.get("agentId")
        or raw.get("agent")
        or "unknown"
    )
    if isinstance(agent_id, dict):
        agent_id = agent_id.get("id", "unknown")

    tool_call = ""
    for key in ("tool_call", "toolCall", "tool", "function", "action"):
        val = raw.get(key, "")
        if val:
            tool_call = str(val)
            if key == "tool" and "input" in raw:
                tool_call += " " + str(raw["input"])
            break

    output = ""
    for key in ("output", "result", "response", "stdout"):
        val = raw.get(key, "")
        if val:
            output = str(val)
            break

    judge_decision = ""
    for key in ("judge_decision", "decision", "verdict", "guardrail_decision"):
        val = raw.get(key, "")
        if val:
            judge_decision = str(val)
            break

    return PB_CES_Event(
        event_id=event_id,
        source=raw.get("source", "generic"),
        event_type=raw.get("event_type", raw.get("type", "unknown")),
        agent_id=agent_id,
        session_id=raw.get("session_id", raw.get("sessionId", "")),
        tool_call=tool_call,
        output=output,
        judge_decision=judge_decision,
        context=raw.get("context", ""),
        metadata={"source_format": "generic", **{
            k: v for k, v in raw.items()
            if k not in {"event_id", "id", "agent_id", "agent", "tool_call", "tool",
                         "output", "result", "decision", "timestamp", "source", "event_type", "type"}
        }},
        timestamp=_ensure_timestamp(raw.get("timestamp")),
        raw_data=raw,
    )


def normalize_event(raw: Dict[str, Any], source_hint: str = "") -> PB_CES_Event:
    """Normalize a raw event into PB-CES format.

    Args:
        raw: The raw event dictionary.
        source_hint: Optional hint for the source type ("lobstertrap", "terrabric", etc.).
                     If not provided, auto-detects from fields.

    Returns:
        A normalized PB_CES_Event.

    Raises:
        NormalizationError: If the event cannot be normalized.
    """
    if not isinstance(raw, dict):
        raise NormalizationError(f"Event must be a dict, got {type(raw).__name__}")

    # Auto-detect source if not hinted
    detected_source = source_hint.lower() if source_hint else ""
    if not detected_source:
        if "lobstertrap" in str(raw.get("source", "")).lower():
            detected_source = "lobstertrap"
        elif "terrabric" in str(raw.get("source", "")).lower():
            detected_source = "terrabric"
        elif raw.get("decision") is not None and raw.get("tool") is not None:
            detected_source = "lobstertrap"
        elif raw.get("agent") is not None and raw.get("event") is not None:
            detected_source = "terrabric"
        else:
            detected_source = "generic"

    if detected_source == "lobstertrap":
        return normalize_lobstertrap(raw)
    elif detected_source == "terrabric":
        return normalize_terrabric(raw)
    else:
        return normalize_generic(raw)
