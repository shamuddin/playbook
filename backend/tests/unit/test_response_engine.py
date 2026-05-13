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
