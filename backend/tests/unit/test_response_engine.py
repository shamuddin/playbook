"""Response Engine unit tests."""

import pytest
from sqlalchemy import select

from app.core.constants import ResponseStatus
from app.models import Incident, ResponseRecord, ResponseStep, TimelineEvent
from app.services.detect.engine import DetectionEngine
from app.services.detect.incident_factory import IncidentFactory
from app.services.detect.normalizer import PB_CES_Event
from app.services.response_engine import ResponseEngine


class TestResponseEngine:
    """Tests for the playbook response engine."""

    @pytest.fixture
    def engine(self):
        return ResponseEngine()

    @pytest.fixture
    async def sample_incident(self, seeded_db):
        """Create a sample incident for response testing."""
        event = PB_CES_Event(
            event_id="test-evt-resp",
            source="test",
            event_type="test",
            tool_call="DROP TABLE users",
        )
        detection = DetectionEngine().evaluate(event)
        if detection.incident_type is None:
            detection.incident_type = "AGT-DEL-001"
            detection.severity = "critical"
            detection.confidence = 1.0
            detection.category = "integrity"

        incident = await IncidentFactory.create_incident(seeded_db, event, detection)
        await seeded_db.commit()
        return incident

    @pytest.mark.asyncio
    async def test_execute_playbook(self, engine, seeded_db, sample_incident):
        result = await engine.execute_playbook(
            seeded_db, sample_incident.incident_id
        )
        assert result.response_id.startswith("RES-")
        assert result.steps_total > 0
        assert result.status in (
            ResponseStatus.COMPLETED,
            ResponseStatus.PARTIAL,
            ResponseStatus.FAILED,
        )
        assert result.total_latency_ms < 5000  # Should be fast

    @pytest.mark.asyncio
    async def test_response_record_created(self, engine, seeded_db, sample_incident):
        await engine.execute_playbook(seeded_db, sample_incident.incident_id)

        result = await seeded_db.execute(
            select(ResponseRecord).where(
                ResponseRecord.incident_id == sample_incident.id
            )
        )
        record = result.scalar_one_or_none()
        assert record is not None
        assert record.response_id.startswith("RES-")
        assert record.steps_total > 0

    @pytest.mark.asyncio
    async def test_response_steps_created(self, engine, seeded_db, sample_incident):
        await engine.execute_playbook(seeded_db, sample_incident.incident_id)

        result = await seeded_db.execute(
            select(ResponseStep).where(
                ResponseStep.response_id.in_(
                    select(ResponseRecord.id).where(
                        ResponseRecord.incident_id == sample_incident.id
                    )
                )
            )
        )
        steps = result.scalars().all()
        assert len(steps) > 0
        for step in steps:
            assert step.step_id.startswith("STEP-")
            assert step.status in ("completed", "failed")

    @pytest.mark.asyncio
    async def test_timeline_events_created(self, engine, seeded_db, sample_incident):
        await engine.execute_playbook(seeded_db, sample_incident.incident_id)

        result = await seeded_db.execute(
            select(TimelineEvent).where(
                TimelineEvent.incident_id == sample_incident.id,
                TimelineEvent.stage == "respond",
            )
        )
        events = result.scalars().all()
        assert len(events) >= 2  # started + completed at minimum

    @pytest.mark.asyncio
    async def test_incident_not_found(self, engine, seeded_db):
        result = await engine.execute_playbook(seeded_db, "INC-NONEXISTENT")
        assert result.status == "failed"
        assert result.error_log is not None

    @pytest.mark.asyncio
    async def test_playbook_not_found(self, engine, seeded_db):
        # Create incident with unknown type
        incident = Incident(
            incident_id="INC-TEST-NO-PB",
            incident_type="AGT-UNKNOWN",
            severity="medium",
            category="test",
            confidence=0.5,
            status="detected",
            response_status="pending",
            forensics_status="pending",
        )
        seeded_db.add(incident)
        await seeded_db.commit()

        result = await engine.execute_playbook(seeded_db, "INC-TEST-NO-PB")
        assert result.status == "failed"
        assert "No playbook found" in result.error_log

    @pytest.mark.asyncio
    async def test_incident_status_updated(self, engine, seeded_db, sample_incident):
        await engine.execute_playbook(seeded_db, sample_incident.incident_id)

        result = await seeded_db.execute(
            select(Incident).where(Incident.id == sample_incident.id)
        )
        incident = result.scalar_one()
        assert incident.response_status is not None
        assert incident.status in ("responding", "resolved")

    @pytest.mark.asyncio
    async def test_playbook_resolution_under_50ms(self, engine, seeded_db, sample_incident):
        import time
        start = time.perf_counter()
        playbook = await engine.resolve_playbook(seeded_db, sample_incident.incident_type)
        elapsed = (time.perf_counter() - start) * 1000
        assert elapsed < 50
        assert playbook is not None


class TestForensicsCrypto:
    """Unit tests for forensics cryptographic helpers."""

    def test_sha256_dict_determinism(self):
        """Same input must produce same hash."""
        from app.services.forensics import _sha256_dict
        data = {"a": 1, "b": "test", "c": [1, 2, 3]}
        h1 = _sha256_dict(data)
        h2 = _sha256_dict(data)
        assert h1 == h2
        assert len(h1) == 64

    def test_sha256_dict_order_independence(self):
        """Dict key order should not affect hash."""
        from app.services.forensics import _sha256_dict
        d1 = {"x": 1, "y": 2}
        d2 = {"y": 2, "x": 1}
        assert _sha256_dict(d1) == _sha256_dict(d2)

    def test_sign_manifest_verifiable(self):
        """HMAC signature should be verifiable."""
        import hmac, hashlib, json
        from app.services.forensics import _sign_manifest
        manifest = {"package_id": "PKG-001", "files": {"a.json": "abc123"}}
        secret = "test-secret-key"
        sig = _sign_manifest(manifest, secret)
        # Verify by recomputing
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
        expected = hmac.new(
            secret.encode("utf-8"),
            canonical.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert sig == expected
        assert len(sig) == 64

    def test_sign_manifest_different_secrets(self):
        """Different secrets must produce different signatures."""
        from app.services.forensics import _sign_manifest
        manifest = {"package_id": "PKG-001", "files": {"a.json": "abc123"}}
        sig1 = _sign_manifest(manifest, "secret-a")
        sig2 = _sign_manifest(manifest, "secret-b")
        assert sig1 != sig2


class TestForensicsService:
    """Unit tests for ForensicsService methods."""

    @pytest.fixture
    def mock_evidence(self):
        """Create a mock evidence package for testing."""
        import hashlib, json
        from unittest.mock import MagicMock
        from datetime import datetime, timezone

        evidence = MagicMock()
        evidence.package_id = "EVIDENCE-TEST-001"
        evidence.is_verified = True
        evidence.created_at = datetime.now(timezone.utc)
        evidence.retention_until = datetime.now(timezone.utc)

        files = {"incident.json": "hash1", "timeline.json": "hash2"}
        # Match _build_manifest canonicalization (no compact separators)
        package_hash = hashlib.sha256(
            json.dumps(files, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        evidence.integrity_hash = package_hash

        evidence.package_data = {
            "manifest": {
                "package_hash": package_hash,
                "files": files,
            },
            "signature": {
                "algorithm": "HMAC-SHA256",
                "signature": "",
            },
            "artifacts": {
                "incident": {"incident_id": "INC-001", "severity": "critical"},
                "timeline": [{"timestamp": "2024-01-01T00:00:00Z", "stage": "detect"}],
                "judge": [{"verdict": "DENY", "severity_score": 9}],
            },
        }
        return evidence

    def test_verify_package_valid(self, mock_evidence):
        """Verify package with correct signature returns overall=True."""
        from app.core.config import get_settings
        from app.services.forensics import ForensicsService, _sign_manifest

        # Compute valid signature using actual secret key
        manifest = mock_evidence.package_data["manifest"]
        sig = _sign_manifest(manifest, get_settings().secret_key)
        mock_evidence.package_data["signature"]["signature"] = sig

        service = ForensicsService()
        report = service.verify_package(mock_evidence)

        assert report["overall"] is True
        assert report["checks"]["manifest_hash_match"] is True
        assert report["checks"]["manifest_recomputed"] is True
        assert report["checks"]["signature_valid"] is True

    def test_verify_package_tampered(self, mock_evidence):
        """Verify package with wrong signature returns overall=False."""
        from app.services.forensics import ForensicsService

        mock_evidence.package_data["signature"]["signature"] = "invalid" * 8

        service = ForensicsService()
        report = service.verify_package(mock_evidence)

        assert report["overall"] is False
        assert report["checks"]["signature_valid"] is False

    def test_export_stix_structure(self, mock_evidence):
        """STIX export must produce valid STIX 2.1 bundle structure."""
        from app.services.forensics import ForensicsService

        service = ForensicsService()
        bundle = service.export_stix(mock_evidence)

        assert bundle["type"] == "bundle"
        assert bundle["spec_version"] == "2.1"
        assert "objects" in bundle
        assert len(bundle["objects"]) > 0

        types = {obj["type"] for obj in bundle["objects"]}
        assert "incident" in types
        assert "report" in types

    def test_export_pdf_html_contains_key_data(self, mock_evidence):
        """HTML export must contain incident key data."""
        from app.services.forensics import ForensicsService

        service = ForensicsService()
        html = service.export_pdf_html(mock_evidence)

        assert "EVIDENCE-TEST-001" in html
        assert "INC-001" in html
        assert "critical" in html
        assert "detect" in html
        assert "<!DOCTYPE html>" in html
