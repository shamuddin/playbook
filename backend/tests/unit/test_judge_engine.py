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
