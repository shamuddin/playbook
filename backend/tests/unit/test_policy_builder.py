"""Unit tests for Policy Builder modules: BaselineLoader, ODPResolver, ConflictDetector."""

import json
import pytest

from app.core.constants import IncidentSeverity
from app.policy.baseline_loader import BaselineLoader
from app.policy.odp_resolver import ODPResolver
from app.policy.conflict_detector import ConflictDetector


class TestBaselineLoader:
    """Tests for BaselineLoader."""

    @pytest.mark.asyncio
    async def test_get_by_incident_type(self, seeded_db):
        baseline = await BaselineLoader.get_by_incident_type(seeded_db, "AGT-DEL-001")
        assert baseline is not None
        assert baseline.incident_type == "AGT-DEL-001"
        assert baseline.severity == IncidentSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_get_by_incident_type_not_found(self, seeded_db):
        baseline = await BaselineLoader.get_by_incident_type(seeded_db, "AGT-UNKNOWN-999")
        assert baseline is None

    @pytest.mark.asyncio
    async def test_list_all(self, seeded_db):
        baselines = await BaselineLoader.list_all(seeded_db)
        assert len(baselines) >= 16
        types = {b.incident_type for b in baselines}
        assert "AGT-DEL-001" in types
        assert "AGT-POL-017" in types

    @pytest.mark.asyncio
    async def test_initialize_missing_baselines_idempotent(self, seeded_db):
        count = await BaselineLoader.initialize_missing_baselines(seeded_db)
        # Already seeded by fixture, should return 0
        assert count == 0

    @pytest.mark.asyncio
    async def test_get_odp_defaults(self, seeded_db):
        baseline = await BaselineLoader.get_by_incident_type(seeded_db, "AGT-DEL-001")
        defaults = BaselineLoader.get_odp_defaults(baseline)
        assert defaults["severity_threshold"] == baseline.severity_threshold
        assert defaults["auto_contain_enabled"] == "true"
        assert defaults["response_time_sla"] == str(baseline.response_time_sla_seconds)


class TestODPResolver:
    """Tests for ODPResolver."""

    @pytest.fixture
    def mock_baseline(self):
        class MockBaseline:
            incident_type = "AGT-DEL-001"
            severity_threshold = "critical"
            auto_contain_enabled = True
            escalation_contacts = ["security@example.com"]
            response_time_sla_seconds = 1800
            forensic_level = "deep"
            notify_targets = ["#security-alerts"]
            compliance_report = True
            record_threshold = 1
        return MockBaseline()

    def test_build_effective_policy_defaults(self, mock_baseline):
        effective = ODPResolver.build_effective_policy(mock_baseline, [])
        assert effective["severity_threshold"] == "critical"
        assert effective["auto_contain_enabled"] is True
        assert effective["response_time_sla_seconds"] == 1800
        assert effective["forensic_level"] == "deep"
        assert effective["compliance_report"] is True
        assert effective["record_threshold"] == 1

    def test_build_effective_policy_with_odps(self, mock_baseline):
        class MockODP:
            odp_key = "severity_threshold"
            odp_value = "high"
            is_active = True

        class MockODP2:
            odp_key = "auto_contain_enabled"
            odp_value = "false"
            is_active = True

        class MockODP3:
            odp_key = "response_time_sla_seconds"
            odp_value = "900"
            is_active = True

        class MockODP4:
            odp_key = "escalation_contacts"
            odp_value = '["admin@corp.com"]'
            is_active = True

        odps = [MockODP(), MockODP2(), MockODP3(), MockODP4()]
        effective = ODPResolver.build_effective_policy(mock_baseline, odps)

        assert effective["severity_threshold"] == "high"
        assert effective["auto_contain_enabled"] is False
        assert effective["response_time_sla_seconds"] == 900
        assert effective["escalation_contacts"] == ["admin@corp.com"]

    def test_build_effective_policy_bool_coercion(self, mock_baseline):
        class MockODP:
            odp_key = "compliance_report"
            odp_value = "TRUE"
            is_active = True
        effective = ODPResolver.build_effective_policy(mock_baseline, [MockODP()])
        assert effective["compliance_report"] is True

        class MockODP2:
            odp_key = "compliance_report"
            odp_value = "FALSE"
            is_active = True
        effective = ODPResolver.build_effective_policy(mock_baseline, [MockODP2()])
        assert effective["compliance_report"] is False

    def test_build_effective_policy_int_fallback(self, mock_baseline):
        class MockODP:
            odp_key = "response_time_sla_seconds"
            odp_value = "not_a_number"
            is_active = True
        effective = ODPResolver.build_effective_policy(mock_baseline, [MockODP()])
        # coerce_value for int tries int() which raises ValueError, returns raw string
        assert effective["response_time_sla_seconds"] == "not_a_number"

    def test_build_effective_policy_json_fallback(self, mock_baseline):
        class MockODP:
            odp_key = "notify_targets"
            odp_value = "invalid json"
            is_active = True
        effective = ODPResolver.build_effective_policy(mock_baseline, [MockODP()])
        # coerce_value for list tries json.loads, falls back to single-item list
        assert effective["notify_targets"] == ["invalid json"]

    def test_build_effective_policy_inactive_skipped(self, mock_baseline):
        class MockODP:
            odp_key = "severity_threshold"
            odp_value = "low"
            is_active = False
        effective = ODPResolver.build_effective_policy(mock_baseline, [MockODP()])
        assert effective["severity_threshold"] == "critical"


class TestConflictDetector:
    """Tests for ConflictDetector."""

    @pytest.fixture
    def mock_baseline(self):
        class MockBaseline:
            incident_type = "AGT-DEL-001"
            severity = "critical"
            severity_threshold = "critical"
            auto_contain_enabled = True
            escalation_contacts = ["security@example.com"]
            response_time_sla_seconds = 1800
            forensic_level = "deep"
            notify_targets = ["#security-alerts"]
            compliance_report = True
            record_threshold = 1
        return MockBaseline()

    def test_detect_no_conflicts(self, mock_baseline):
        odps = {
            "severity_threshold": "critical",
            "auto_contain_enabled": "true",
            "response_time_sla": "1800",
            "forensic_level": "deep",
            "compliance_report": "true",
            "record_threshold": "1",
            "escalation_contacts": json.dumps(["security@example.com"]),
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        assert len(conflicts) == 0

    def test_detect_missing_required(self, mock_baseline):
        odps = {"severity_threshold": "critical"}  # Missing 7 keys
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        missing = [c for c in conflicts if c.type == "MISSING_REQUIRED"]
        assert len(missing) >= 6

    def test_detect_severity_downgrade(self, mock_baseline):
        odps = {
            "severity_threshold": "low",
            "auto_contain_enabled": "true",
            "response_time_sla": "1800",
            "forensic_level": "deep",
            "compliance_report": "true",
            "record_threshold": "1",
            "escalation_contacts": json.dumps(["security@example.com"]),
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        downgrade = [c for c in conflicts if c.type == "SEVERITY_DOWNGRADE"]
        assert len(downgrade) == 1
        assert downgrade[0].nist_value == "critical"
        assert downgrade[0].odp_value == "low"

    def test_detect_forensic_level_reduction(self, mock_baseline):
        odps = {
            "severity_threshold": "critical",
            "auto_contain_enabled": "true",
            "response_time_sla": "1800",
            "forensic_level": "none",
            "compliance_report": "true",
            "record_threshold": "1",
            "escalation_contacts": json.dumps(["security@example.com"]),
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        reduction = [c for c in conflicts if c.type == "FORENSIC_LEVEL_REDUCTION"]
        assert len(reduction) == 1

    def test_detect_compliance_disabled(self, mock_baseline):
        odps = {
            "severity_threshold": "critical",
            "auto_contain_enabled": "true",
            "response_time_sla": "1800",
            "forensic_level": "deep",
            "compliance_report": "false",
            "record_threshold": "1",
            "escalation_contacts": json.dumps(["security@example.com"]),
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        disabled = [c for c in conflicts if c.type == "COMPLIANCE_REPORT_DISABLED"]
        assert len(disabled) == 1

    def test_detect_empty_escalation(self, mock_baseline):
        odps = {
            "severity_threshold": "critical",
            "auto_contain_enabled": "true",
            "response_time_sla": "1800",
            "forensic_level": "deep",
            "compliance_report": "true",
            "record_threshold": "1",
            "escalation_contacts": "[]",
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        empty = [c for c in conflicts if "escalation" in c.message.lower() or "contact" in c.message.lower()]
        assert len(empty) == 1

    def test_detect_sla_threshold_violation(self, mock_baseline):
        odps = {
            "severity_threshold": "critical",
            "auto_contain_enabled": "true",
            "response_time_sla": "5000",  # > 2x 1800
            "forensic_level": "deep",
            "compliance_report": "true",
            "record_threshold": "1",
            "escalation_contacts": json.dumps(["security@example.com"]),
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        violation = [c for c in conflicts if c.type == "THRESHOLD_VIOLATION"]
        assert len(violation) == 1

    def test_detect_auto_contain_mismatch(self, mock_baseline):
        odps = {
            "severity_threshold": "critical",
            "auto_contain_enabled": "false",
            "response_time_sla": "1800",
            "forensic_level": "deep",
            "compliance_report": "true",
            "record_threshold": "1",
            "escalation_contacts": json.dumps(["security@example.com"]),
            "notify_targets": json.dumps(["#security-alerts"]),
        }
        conflicts = ConflictDetector.detect(mock_baseline, odps, "AGT-DEL-001")
        mismatch = [c for c in conflicts if c.type == "VALUE_MISMATCH"]
        assert len(mismatch) == 1

    @pytest.mark.asyncio
    async def test_detect_for_baseline(self, seeded_db, mock_baseline):
        # Get real baseline from DB to use its id
        from sqlalchemy import select
        from app.models import NistBaseline, OrganizationODP

        result = await seeded_db.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-DEL-001")
        )
        real_baseline = result.scalar_one()

        # Add a conflict-inducing ODP
        seeded_db.add(OrganizationODP(
            baseline_id=real_baseline.id,
            odp_key="compliance_report",
            odp_value="false",
        ))
        await seeded_db.commit()

        conflicts = await ConflictDetector.detect_for_baseline(seeded_db, real_baseline)
        disabled = [c for c in conflicts if c.type == "COMPLIANCE_REPORT_DISABLED"]
        assert len(disabled) == 1

    @pytest.mark.asyncio
    async def test_persist_conflicts(self, seeded_db, mock_baseline):
        from sqlalchemy import select
        from app.models import NistBaseline, ODPConflict

        result = await seeded_db.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-DEL-001")
        )
        real_baseline = result.scalar_one()

        from app.schemas import ConflictDetail
        conflicts = [
            ConflictDetail(
                type="TEST_CONFLICT",
                severity="high",
                message="Test message",
                nist_value="expected",
                odp_value="actual",
            )
        ]
        count = await ConflictDetector.persist_conflicts(seeded_db, real_baseline, conflicts)
        assert count == 1

        result = await seeded_db.execute(
            select(ODPConflict).where(ODPConflict.baseline_id == real_baseline.id)
        )
        saved = result.scalars().all()
        assert len(saved) == 1
        assert saved[0].conflict_type == "TEST_CONFLICT"
        assert saved[0].conflict_id.startswith("CONF-AGT-DEL-001-TEST_CONFLICT-")
