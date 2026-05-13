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


@router.get("/gap-analysis", response_model=StandardResponse)
async def get_gap_analysis(
    framework: str = Query(..., description="Framework to analyze gaps for"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Analyze compliance coverage gaps for a framework.

    Returns which incident types lack coverage and recommends controls.
    """
    from app.core.constants import INCIDENT_TYPES

    # Get all mappings for this framework
    result = await db.execute(
        select(ComplianceMapping).where(ComplianceMapping.framework == framework)
    )
    mappings = result.scalars().all()

    covered_types = {m.incident_type for m in mappings}
    all_types = set(INCIDENT_TYPES.keys())
    uncovered_types = sorted(all_types - covered_types)

    # Coverage stats by incident type
    type_coverage = {}
    for itype in all_types:
        type_maps = [m for m in mappings if m.incident_type == itype]
        type_coverage[itype] = {
            "name": INCIDENT_TYPES[itype],
            "mapped_controls": len(type_maps),
            "risk_levels": [m.risk_level for m in type_maps],
        }

    # Overall metrics
    total_controls = len(mappings)
    coverage_pct = round(len(covered_types) / len(all_types) * 100, 1)

    # Risk-weighted gap score
    critical_gaps = sum(
        1 for itype in uncovered_types
        if itype in ("AGT-DEL-001", "AGT-EXT-005", "AGT-CRE-008", "AGT-BYP-014")
    )

    return StandardResponse(
        data={
            "framework": framework,
            "total_incident_types": len(all_types),
            "covered_types": len(covered_types),
            "uncovered_types": len(uncovered_types),
            "coverage_percentage": coverage_pct,
            "critical_gaps": critical_gaps,
            "uncovered": [
                {"incident_type": t, "name": INCIDENT_TYPES[t]}
                for t in uncovered_types
            ],
            "type_coverage": type_coverage,
            "summary": {
                "status": "complete" if coverage_pct == 100 else "gaps_detected",
                "recommendation": (
                    "All incident types are mapped."
                    if coverage_pct == 100
                    else f"Add controls for {len(uncovered_types)} uncovered incident types."
                ),
            },
        },
        message=f"Gap analysis for {framework}: {coverage_pct}% coverage",
    )
