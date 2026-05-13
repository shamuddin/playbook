"""Unit tests for the PB-CES normalizer."""

import pytest
from datetime import datetime, timezone

from app.services.detect.normalizer import (
    NormalizationError,
    PB_CES_Event,
    normalize_event,
    normalize_lobstertrap,
    normalize_terrabric,
)


class TestNormalizer:
    """Tests for event normalization."""

    def test_normalize_lobstertrap_event(self):
        raw = {
            "event_id": "lt-abc123",
            "agent_id": "agent-001",
            "session_id": "sess-xyz",
            "action": "tool_call",
            "tool": "database.query",
            "input": "SELECT * FROM users",
            "output": "200 OK",
            "decision": "ALLOW",
            "timestamp": "2024-01-15T10:30:00Z",
            "risk_score": 0.2,
        }
        event = normalize_lobstertrap(raw)

        assert event.event_id == "lt-abc123"
        assert event.source == "lobstertrap"
        assert event.event_type == "tool_call"
        assert event.agent_id == "agent-001"
        assert event.session_id == "sess-xyz"
        assert "database.query" in event.tool_call
        assert event.output == "200 OK"
        assert event.judge_decision == "ALLOW"
        assert event.metadata["risk_score"] == 0.2
        assert isinstance(event.timestamp, datetime)

    def test_normalize_terrabric_event(self):
        raw = {
            "id": "tf-001",
            "agent": {"id": "agent-002", "name": "DataBot"},
            "event": "anomaly_detected",
            "details": {"tool": "api.call", "args": {"url": "http://api.example.com"}},
            "severity": "high",
            "timestamp": 1705317000,
        }
        event = normalize_terrabric(raw)

        assert event.event_id == "tf-001"
        assert event.source == "terrabric"
        assert event.event_type == "anomaly_detected"
        assert event.agent_id == "agent-002"
        assert event.metadata["severity"] == "high"
        assert isinstance(event.timestamp, datetime)

    def test_normalize_generic_event(self):
        raw = {
            "event_id": "gen-001",
            "source": "custom-agent",
            "event_type": "custom_event",
            "agent_id": "agent-003",
            "tool_call": "custom_tool.run",
            "output": "success",
            "decision": "DENY",
        }
        event = normalize_event(raw)

        assert event.event_id == "gen-001"
        assert event.source == "custom-agent"
        assert event.event_type == "custom_event"
        assert event.agent_id == "agent-003"
        assert event.tool_call == "custom_tool.run"
        assert event.output == "success"
        assert event.judge_decision == "DENY"

    def test_auto_detect_lobstertrap(self):
        raw = {
            "source": "lobstertrap",
            "tool": "file.read",
            "input": "/etc/passwd",
            "decision": "DENY",
        }
        event = normalize_event(raw)
        assert event.source == "lobstertrap"

    def test_auto_detect_terrabric(self):
        raw = {
            "agent": {"id": "a1"},
            "event": "health_check",
            "details": {"status": "ok"},
        }
        event = normalize_event(raw)
        assert event.source == "terrabric"

    def test_missing_required_field_with_hint(self):
        """Generic normalization should handle missing fields gracefully."""
        raw = {"source": "test", "message": "hello"}
        event = normalize_event(raw, source_hint="generic")
        assert event.event_id.startswith("EVT-")
        assert event.event_type == "unknown"
        assert event.agent_id == "unknown"

    def test_non_dict_raises_error(self):
        with pytest.raises(NormalizationError):
            normalize_event("not a dict")

    def test_timestamp_parsing_iso(self):
        raw = {
            "event_id": "ts-001",
            "timestamp": "2024-06-15T14:30:00+00:00",
        }
        event = normalize_event(raw, source_hint="generic")
        assert event.timestamp.year == 2024
        assert event.timestamp.month == 6

    def test_timestamp_parsing_unix(self):
        raw = {
            "event_id": "ts-002",
            "timestamp": 1705317000,
        }
        event = normalize_event(raw, source_hint="generic")
        assert event.timestamp.year == 2024

    def test_timestamp_parsing_string(self):
        raw = {
            "event_id": "ts-003",
            "timestamp": "2024-01-15 10:30:00",
        }
        event = normalize_event(raw, source_hint="generic")
        assert event.timestamp.year == 2024

    def test_event_generates_id_if_missing(self):
        raw = {"source": "test", "type": "test_event"}
        event = normalize_event(raw)
        assert event.event_id.startswith("EVT-")
        assert len(event.event_id) > 4

    def test_raw_data_preserved(self):
        raw = {"event_id": "raw-001", "custom_field": "custom_value"}
        event = normalize_event(raw, source_hint="generic")
        assert event.raw_data["custom_field"] == "custom_value"

    def test_lobstertrap_defaults(self):
        """Lobster Trap event with minimal fields should still normalize."""
        raw = {"tool": "test.tool"}
        event = normalize_lobstertrap(raw)
        assert event.source == "lobstertrap"
        assert event.event_id.startswith("EVT-")
        assert event.agent_id == "unknown"
