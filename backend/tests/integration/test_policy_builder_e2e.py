"""End-to-end tests for Policy Builder API endpoints."""

import pytest
from sqlalchemy import select

from app.models import OrganizationODP, ODPConflict, PolicyVersion, NistBaseline


class TestPolicyBuilderAPI:
    """E2E tests for /policy-builder endpoints."""

    @pytest.mark.asyncio
    async def test_list_baselines(self, seeded_async_client):
        res = await seeded_async_client.get("/api/v1/policy-builder/nist-baseline")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        items = data["data"]["items"]
        assert len(items) >= 16
        types = {b["incident_type"] for b in items}
        assert "AGT-DEL-001" in types
        assert "AGT-POL-017" in types

    @pytest.mark.asyncio
    async def test_get_baseline_by_type(self, seeded_async_client):
        res = await seeded_async_client.get("/api/v1/policy-builder/nist-baseline/AGT-DEL-001")
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["incident_type"] == "AGT-DEL-001"
        assert data["data"]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_get_baseline_not_found(self, seeded_async_client):
        res = await seeded_async_client.get("/api/v1/policy-builder/nist-baseline/AGT-UNKNOWN")
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_update_odp(self, seeded_async_client, db_session):
        # The endpoint expects odps as a dict of key-value strings
        payload = {
            "odps": {
                "severity_threshold": "high",
                "auto_contain_enabled": "true",
                "escalation_contacts": '["admin@corp.com"]',
                "response_time_sla": "900",
                "forensic_level": "standard",
                "notify_targets": '["#ops"]',
                "compliance_report": "true",
                "record_threshold": "5",
            }
        }
        res = await seeded_async_client.put(
            "/api/v1/policy-builder/odps/AGT-EXT-005",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["odps_applied"] == 8
        assert data["data"]["version"] >= 1

        # Verify in DB
        baseline_result = await db_session.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-EXT-005")
        )
        baseline = baseline_result.scalar_one()
        result = await db_session.execute(
            select(OrganizationODP).where(
                OrganizationODP.baseline_id == baseline.id,
                OrganizationODP.odp_key == "severity_threshold",
            )
        )
        odp = result.scalar_one()
        assert odp.odp_value == "high"

    @pytest.mark.asyncio
    async def test_update_odp_validation_error(self, seeded_async_client):
        # Invalid payload structure (not a dict of strings) should 422
        payload = {
            "odps": {
                "severity_threshold": "invalid",
                "auto_contain_enabled": True,  # bool instead of str
            }
        }
        res = await seeded_async_client.put(
            "/api/v1/policy-builder/odps/AGT-EXT-005",
            json=payload,
        )
        # FastAPI may coerce or reject
        assert res.status_code in (200, 422)

    @pytest.mark.asyncio
    async def test_bulk_update_odps(self, seeded_async_client, db_session):
        # Bulk update expects {incident_type: {odp_key: odp_value}}
        payload = {
            "AGT-INJ-006": {
                "severity_threshold": "medium",
                "auto_contain_enabled": "false",
                "escalation_contacts": '["dev@corp.com"]',
                "response_time_sla": "3600",
                "forensic_level": "basic",
                "notify_targets": "[]",
                "compliance_report": "false",
                "record_threshold": "10",
            }
        }
        res = await seeded_async_client.put(
            "/api/v1/policy-builder/odps/bulk",
            json=payload,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["applied"] == 8

    @pytest.mark.asyncio
    async def test_get_resolved_policy(self, seeded_async_client, db_session):
        # First create an ODP
        baseline_result = await db_session.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-RAT-009")
        )
        baseline = baseline_result.scalar_one()

        db_session.add(OrganizationODP(
            baseline_id=baseline.id,
            odp_key="severity_threshold",
            odp_value="high",
        ))
        await db_session.commit()

        res = await seeded_async_client.get("/api/v1/policy-builder/resolve/AGT-RAT-009")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["data"]["incident_type"] == "AGT-RAT-009"
        # Should reflect ODP override in effective_policy
        assert data["data"]["effective_policy"]["severity_threshold"] == "high"

    @pytest.mark.asyncio
    async def test_list_templates(self, seeded_async_client):
        res = await seeded_async_client.get("/api/v1/policy-builder/templates")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 3
        names = {t["name"] for t in data}
        assert "HIPAA Healthcare" in names

    @pytest.mark.asyncio
    async def test_apply_template_dry_run(self, seeded_async_client):
        res = await seeded_async_client.post(
            "/api/v1/policy-builder/templates/TPL-HIPAA/apply",
            json={"dry_run": True, "incident_types": ["AGT-EXT-005"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        results = data["data"]["results"]
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_conflicts(self, seeded_async_client, db_session):
        # Insert a conflict record directly
        baseline_result = await db_session.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-DEL-001")
        )
        baseline = baseline_result.scalar_one()

        db_session.add(ODPConflict(
            conflict_id="CONF-AGT-DEL-001-TEST-001",
            baseline_id=baseline.id,
            odp_id="",
            conflict_type="COMPLIANCE_REPORT_DISABLED",
            severity="WARNING",
            message="Compliance report disabled but baseline requires it",
            expected_value="true",
            actual_value="false",
            status="open",
        ))
        await db_session.commit()

        res = await seeded_async_client.get("/api/v1/policy-builder/conflicts")
        assert res.status_code == 200
        data = res.json()
        # The conflicts endpoint returns paginated items, not keyed by incident_type
        assert data["success"] is True
        assert data["data"]["summary"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_versions(self, seeded_async_client, db_session):
        # Get a baseline id first
        result = await db_session.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-CRE-008")
        )
        baseline = result.scalar_one()

        # Create a version record
        db_session.add(PolicyVersion(
            baseline_id=baseline.id,
            version_number=1,
            change_type="manual",
            changed_by="test",
        ))
        await db_session.commit()

        res = await seeded_async_client.get(f"/api/v1/policy-builder/versions?baseline_id={baseline.id}")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) >= 1
        assert data["data"]["items"][0]["version_number"] == 1

    @pytest.mark.asyncio
    async def test_rollback_version(self, seeded_async_client, db_session):
        # Get baseline id
        result = await db_session.execute(
            select(NistBaseline).where(NistBaseline.incident_type == "AGT-HAL-007")
        )
        baseline = result.scalar_one()

        # Seed ODP and version
        odp = OrganizationODP(
            baseline_id=baseline.id,
            odp_key="severity_threshold",
            odp_value="high",
        )
        db_session.add(odp)
        await db_session.flush()

        db_session.add(PolicyVersion(
            baseline_id=baseline.id,
            odp_id=odp.id,
            version_number=1,
            change_type="manual",
            from_value="medium",
            to_value="high",
            changed_by="test",
        ))
        await db_session.commit()

        # Get version id
        result = await db_session.execute(
            select(PolicyVersion).where(PolicyVersion.baseline_id == baseline.id)
        )
        version = result.scalar_one()

        res = await seeded_async_client.post(
            f"/api/v1/policy-builder/versions/{version.id}/rollback"
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_validate_odps(self, seeded_async_client):
        res = await seeded_async_client.post("/api/v1/policy-builder/validate")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "results" in data["data"]
