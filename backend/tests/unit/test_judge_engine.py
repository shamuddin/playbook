"""Judge Engine unit tests."""

import pytest

from app.core.constants import JudgeVerdict
from app.judge.engine import JudgeEngine, JudgeInput


class TestJudgeEngine:
    """Tests for the deterministic Judge Engine."""

    @pytest.fixture
    def engine(self):
        return JudgeEngine()

    @pytest.fixture
    def low_risk_input(self):
        return JudgeInput(
            action="read_user_profile",
            agent_id="agent-001",
            incident_type="AGT-GAP-012",
            severity="low",
            auth_present=True,
            is_business_hours=True,
            source_ip_reputation="trusted",
        )

    @pytest.fixture
    def high_risk_input(self):
        return JudgeInput(
            action="DROP TABLE users",
            agent_id="agent-001",
            incident_type="AGT-DEL-001",
            severity="critical",
            auth_present=False,
            is_business_hours=False,
            source_ip_reputation="malicious",
            contains_system_commands=True,
            is_repeat_offender=True,
        )

    @pytest.mark.asyncio
    async def test_low_risk_allow(self, engine, low_risk_input, seeded_db):
        result = await engine.evaluate(seeded_db, low_risk_input)
        assert result.verdict == JudgeVerdict.ALLOW
        assert result.severity_score <= 3
        assert result.latency_ms < 50
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_high_risk_deny(self, engine, high_risk_input, seeded_db):
        result = await engine.evaluate(seeded_db, high_risk_input)
        assert result.verdict in (JudgeVerdict.DENY, JudgeVerdict.QUARANTINE)
        assert result.severity_score >= 7
        assert result.latency_ms < 50

    @pytest.mark.asyncio
    async def test_no_auth_quarantine(self, engine, seeded_db):
        """Severity 4-6 + missing auth → QUARANTINE."""
        inp = JudgeInput(
            action="query_database",
            incident_type="AGT-EXT-005",
            severity="medium",
            auth_present=False,
            contains_exfiltration=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.severity_score >= 4
        if result.severity_score <= 6:
            assert result.verdict == JudgeVerdict.QUARANTINE

    @pytest.mark.asyncio
    async def test_dual_auth_reduces_severity(self, engine, seeded_db):
        """Dual auth present should reduce severity score."""
        inp_with = JudgeInput(
            action="transfer_funds",
            incident_type="AGT-FIN-002",
            severity="high",
            auth_present=True,
            dual_auth_present=True,
        )
        inp_without = JudgeInput(
            action="transfer_funds",
            incident_type="AGT-FIN-002",
            severity="high",
            auth_present=True,
            dual_auth_present=False,
        )
        result_with = await engine.evaluate(seeded_db, inp_with)
        result_without = await engine.evaluate(seeded_db, inp_without)
        assert result_with.severity_score < result_without.severity_score

    @pytest.mark.asyncio
    async def test_repeat_offender_escalates(self, engine, seeded_db):
        """Repeat offender gets +2 severity."""
        inp = JudgeInput(
            action="suspicious_action",
            incident_type="AGT-INJ-006",
            severity="medium",
            is_repeat_offender=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.severity_score >= 7  # base 5 + 2 = 7

    @pytest.mark.asyncio
    async def test_bypass_detection_escalates(self, engine, seeded_db):
        """Bypass patterns add +2 to severity."""
        inp = JudgeInput(
            action="test",
            incident_type="AGT-BYP-014",
            severity="medium",
        )
        result = await engine.evaluate(seeded_db, inp, bypass_patterns=["context_window_displacement"])
        # Should be escalated by +2
        assert result.bypass_patterns_detected == ["context_window_displacement"]
        assert result.severity_score >= 7

    @pytest.mark.asyncio
    async def test_odp_resolution(self, engine, seeded_db):
        """ODP resolution should load baseline and return policy."""
        inp = JudgeInput(
            action="test",
            incident_type="AGT-DEL-001",
            severity="critical",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert "odp_resolution" in result.matched_rules
        assert result.resolved_policy_id is not None
        assert isinstance(result.odp_overrides, dict)

    @pytest.mark.asyncio
    async def test_regulatory_tags(self, engine, seeded_db):
        """Regulatory tags should be assigned by incident type."""
        inp = JudgeInput(
            action="test",
            incident_type="AGT-PRV-015",
            severity="high",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert len(result.regulatory_tags) > 0
        assert any("GDPR" in tag for tag in result.regulatory_tags)

    @pytest.mark.asyncio
    async def test_latency_under_50ms(self, engine, seeded_db):
        """Judge evaluation should complete in < 50ms."""
        inp = JudgeInput(
            action="test",
            incident_type="AGT-DEL-001",
            severity="critical",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.latency_ms < 50

    @pytest.mark.asyncio
    async def test_rationale_provided(self, engine, seeded_db):
        """Every decision should include a human-readable rationale."""
        inp = JudgeInput(action="test", incident_type="AGT-GAP-012")
        result = await engine.evaluate(seeded_db, inp)
        assert len(result.rationale) > 0
        assert result.verdict in result.rationale

    @pytest.mark.asyncio
    async def test_severity_clamping(self, engine, seeded_db):
        """Severity score should be clamped to 1-10."""
        # Max modifiers: critical(9) + repeat(2) + no_auth(3) + malicious_ip(4) + credentials(2) + exfil(2) = 22
        inp = JudgeInput(
            action="test",
            incident_type="AGT-DEL-001",
            severity="critical",
            is_repeat_offender=True,
            auth_present=False,
            source_ip_reputation="malicious",
            contains_credentials=True,
            contains_exfiltration=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        assert 1 <= result.severity_score <= 10

    @pytest.mark.asyncio
    async def test_auto_contain_override(self, engine, seeded_db):
        """Auto-contain policy should elevate ALLOW to QUARANTINE for high severity."""
        # This test assumes NIST baseline for AGT-DEL-001 has auto_contain_enabled=True
        inp = JudgeInput(
            action="test",
            incident_type="AGT-DEL-001",
            severity="high",
            auth_present=True,  # Would normally ALLOW
        )
        result = await engine.evaluate(seeded_db, inp)
        # If auto_contain is enabled and severity >= 7, should be QUARANTINE
        if result.severity_score >= 7:
            assert result.verdict != JudgeVerdict.ALLOW


# ============================================================================
# Policy Builder Unit Tests (Phase 8)
# ============================================================================

import pytest

from app.policy.baseline_loader import BaselineLoader
from app.policy.conflict_detector import ConflictDetector
from app.policy.odp_resolver import ODPResolver


class TestODPResolver:
    """Unit tests for ODP resolution and type coercion."""

    def test_coerce_bool_true(self):
        assert ODPResolver.coerce_value("auto_contain_enabled", "true") is True
        assert ODPResolver.coerce_value("auto_contain_enabled", "TRUE") is True

    def test_coerce_bool_false(self):
        assert ODPResolver.coerce_value("auto_contain_enabled", "false") is False
        assert ODPResolver.coerce_value("compliance_report", "FALSE") is False

    def test_coerce_int(self):
        assert ODPResolver.coerce_value("response_time_sla_seconds", "1800") == 1800
        assert ODPResolver.coerce_value("record_threshold", "10") == 10

    def test_coerce_int_invalid_fallback(self):
        assert ODPResolver.coerce_value("response_time_sla_seconds", "abc") == "abc"

    def test_coerce_list_json(self):
        result = ODPResolver.coerce_value("escalation_contacts", '["a@b.com", "c@d.com"]')
        assert result == ["a@b.com", "c@d.com"]

    def test_coerce_list_csv(self):
        result = ODPResolver.coerce_value("notify_targets", "#security, #incident")
        assert result == ["#security", "#incident"]

    def test_coerce_string_fallback(self):
        assert ODPResolver.coerce_value("severity_threshold", "HIGH") == "HIGH"

    def test_build_effective_policy_no_odps(self, baseline_fixture):
        """Baseline values should pass through when no ODPs exist."""
        effective = ODPResolver.build_effective_policy(baseline_fixture, [])
        assert effective["severity_threshold"] == "CRITICAL"
        assert effective["auto_contain_enabled"] is True
        assert effective["response_time_sla_seconds"] == 1800

    def test_build_effective_policy_with_override(self, baseline_fixture, odp_fixture_factory):
        """ODP overrides should replace baseline values."""
        odps = [
            odp_fixture_factory("severity_threshold", "HIGH"),
            odp_fixture_factory("auto_contain_enabled", "false"),
            odp_fixture_factory("response_time_sla", "3600"),
        ]
        effective = ODPResolver.build_effective_policy(baseline_fixture, odps)
        assert effective["severity_threshold"] == "HIGH"
        assert effective["auto_contain_enabled"] is False
        # ODP key "response_time_sla" maps to "response_time_sla_seconds"
        assert effective["response_time_sla_seconds"] == 3600

    def test_get_defaults(self, baseline_fixture):
        defaults = ODPResolver.get_defaults(baseline_fixture)
        assert defaults["severity_threshold"] == "CRITICAL"
        assert defaults["auto_contain_enabled"] == "true"
        assert defaults["response_time_sla"] == "1800"


class TestConflictDetector:
    """Unit tests for the 7 conflict detection rules."""

    def test_missing_required(self, baseline_fixture):
        odps = {}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        missing = [c for c in conflicts if c.type == "MISSING_REQUIRED"]
        assert len(missing) == 8  # All 8 required keys missing

    def test_severity_downgrade(self, baseline_fixture):
        odps = {"severity_threshold": "LOW"}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        sev = [c for c in conflicts if c.type == "SEVERITY_DOWNGRADE"]
        assert len(sev) == 1
        assert sev[0].severity == "BLOCKED"

    def test_no_severity_downgrade_when_equal(self, baseline_fixture):
        odps = {"severity_threshold": "CRITICAL"}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        sev = [c for c in conflicts if c.type == "SEVERITY_DOWNGRADE"]
        assert len(sev) == 0

    def test_auto_contain_mismatch(self, baseline_fixture):
        odps = {"auto_contain_enabled": "false"}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        mismatch = [c for c in conflicts if c.type == "VALUE_MISMATCH"]
        assert len(mismatch) == 1
        assert mismatch[0].severity == "WARNING"

    def test_sla_threshold_violation(self, baseline_fixture):
        """SLA > 2x baseline (1800*2=3600) should trigger warning."""
        odps = {"response_time_sla": "4000"}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        violations = [c for c in conflicts if c.type == "THRESHOLD_VIOLATION"]
        assert len(violations) == 1

    def test_forensic_level_reduction(self, baseline_fixture):
        odps = {"forensic_level": "none"}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        reductions = [c for c in conflicts if c.type == "FORENSIC_LEVEL_REDUCTION"]
        assert len(reductions) == 1

    def test_compliance_report_disabled(self, baseline_fixture):
        odps = {"compliance_report": "false"}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        disabled = [c for c in conflicts if c.type == "COMPLIANCE_REPORT_DISABLED"]
        assert len(disabled) == 1

    def test_empty_escalation_contacts(self, baseline_fixture):
        odps = {"escalation_contacts": ""}
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        empty = [c for c in conflicts if c.type == "MISSING_REQUIRED" and "contact" in c.message.lower()]
        assert len(empty) == 1

    def test_no_conflicts_with_valid_odps(self, baseline_fixture):
        odps = {
            "severity_threshold": "CRITICAL",
            "auto_contain_enabled": "true",
            "escalation_contacts": '["security@example.com"]',
            "response_time_sla": "1800",
            "forensic_level": "deep",
            "notify_targets": '["#alerts"]',
            "compliance_report": "true",
            "record_threshold": "1",
        }
        conflicts = ConflictDetector.detect(baseline_fixture, odps, "AGT-DEL-001")
        assert len(conflicts) == 0


class TestBaselineLoader:
    """Unit tests for baseline loading utilities."""

    @pytest.mark.asyncio
    async def test_get_odp_defaults(self, baseline_fixture):
        defaults = BaselineLoader.get_odp_defaults(baseline_fixture)
        assert defaults["severity_threshold"] == "CRITICAL"
        assert defaults["auto_contain_enabled"] == "true"
        assert defaults["response_time_sla"] == "1800"
        assert defaults["record_threshold"] == "1"


# ============================================================================
# Pytest fixtures for policy builder tests
# ============================================================================

@pytest.fixture
def baseline_fixture():
    """Return a mock NistBaseline for unit tests."""
    from unittest.mock import MagicMock
    baseline = MagicMock(spec="app.models.NistBaseline")
    baseline.severity = "CRITICAL"
    baseline.severity_threshold = "CRITICAL"
    baseline.auto_contain_enabled = True
    baseline.escalation_contacts = ["security@example.com"]
    baseline.response_time_sla_seconds = 1800
    baseline.forensic_level = "deep"
    baseline.notify_targets = ["#security-alerts"]
    baseline.compliance_report = True
    baseline.record_threshold = 1
    baseline.incident_type = "AGT-DEL-001"
    baseline.id = "baseline-uuid-123"
    baseline.is_active = True
    return baseline


@pytest.fixture
def odp_fixture_factory():
    """Factory for creating mock ODPs."""
    from unittest.mock import MagicMock

    def _factory(key: str, value: str):
        odp = MagicMock(spec="app.models.OrganizationODP")
        odp.odp_key = key
        odp.odp_value = value
        odp.is_active = True
        return odp

    return _factory
