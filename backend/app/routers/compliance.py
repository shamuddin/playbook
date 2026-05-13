"""Compliance API router."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ComplianceMapping, Incident, NistBaseline
from app.schemas import ComplianceMappingResponse, ComplianceReportResponse, StandardResponse

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/report", response_model=ComplianceReportResponse)
async def get_compliance_report(
    incident_id: str,
    framework: str = Query("eu_ai_act"),
    db: AsyncSession = Depends(get_db),
) -> ComplianceReportResponse:
    """Generate compliance report for an incident.

    Supports: eu_ai_act, nist_ai_rmf, hipaa, soc2
    """
    # Find incident
    result = await db.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    # Get compliance mappings for this incident type
    mapping_result = await db.execute(
        select(ComplianceMapping).where(
            ComplianceMapping.incident_type == incident.incident_type,
            ComplianceMapping.framework == framework,
        )
    )
    mappings = mapping_result.scalars().all()

    # Build report data
    report_data = {
        "incident_id": incident_id,
        "incident_type": incident.incident_type,
        "severity": incident.severity,
        "framework": framework,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mappings": [
            {
                "control_id": m.control_id,
                "control_name": m.control_name,
                "risk_level": m.risk_level,
                "confidence": m.confidence,
                "mapping_data": m.mapping_data,
            }
            for m in mappings
        ],
        "summary": {
            "total_controls_mapped": len(mappings),
            "critical_controls": len([m for m in mappings if m.risk_level == "critical"]),
            "high_controls": len([m for m in mappings if m.risk_level == "high"]),
        },
    }

    # EU AI Act Article 73 specific fields for critical/high incidents
    if framework == "eu_ai_act" and incident.severity in ("critical", "high"):
        report_data["article_73"] = {
            "article": "73",
            "title": "Reporting of serious incidents",
            "incident_type": incident.incident_type,
            "severity": incident.severity,
            "date_of_occurrence": incident.created_at.isoformat() if incident.created_at else None,
            "description": f"AI agent incident classified as {incident.incident_type} with severity {incident.severity}",
            "affected_systems": [incident.event_id or "unknown"],
            "mitigation_measures": ["Automated containment executed", "Forensic evidence captured"],
            "cross_border_impact": False,
            "reporting_deadline_hours": 24 if incident.severity == "critical" else 72,
        }

    return ComplianceReportResponse(
        incident_id=incident_id,
        framework=framework,
        report_format="json",
        report_data=report_data,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/mapping", response_model=list[ComplianceMappingResponse])
async def get_compliance_mapping(
    framework: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[ComplianceMappingResponse]:
    """Get compliance mapping matrix.

    Filter by framework and/or incident_type.
    """
    query = select(ComplianceMapping)

    if framework:
        query = query.where(ComplianceMapping.framework == framework)
    if incident_type:
        query = query.where(ComplianceMapping.incident_type == incident_type)

    result = await db.execute(query)
    mappings = result.scalars().all()

    return [
        ComplianceMappingResponse(
            incident_type=m.incident_type,
            framework=m.framework,
            control_id=m.control_id,
            control_name=m.control_name,
            risk_level=m.risk_level,
            confidence=m.confidence,
        )
        for m in mappings
    ]


@router.get("/frameworks", response_model=StandardResponse)
async def list_frameworks(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all compliance frameworks with incident coverage."""
    result = await db.execute(
        select(ComplianceMapping.framework).distinct()
    )
    frameworks = [row[0] for row in result.all()]

    framework_stats = {}
    for fw in frameworks:
        count_result = await db.execute(
            select(ComplianceMapping).where(ComplianceMapping.framework == fw)
        )
        count = len(count_result.scalars().all())
        framework_stats[fw] = count

    return StandardResponse(
        data={
            "frameworks": frameworks,
            "mapping_counts": framework_stats,
        },
        message=f"Found {len(frameworks)} compliance frameworks",
    )
