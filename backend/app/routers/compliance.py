"""Compliance API router."""

import html
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ComplianceMapping, Incident, NistBaseline
from app.schemas import ComplianceMappingResponse, ComplianceReportResponse, StandardResponse
from app.services.gemini_reasoning import generate_compliance_report

router = APIRouter(prefix="/compliance", tags=["compliance"])

FRAMEWORK_META = {
    "eu_ai_act": {"display_name": "EU AI Act", "version": "2024/1689"},
    "nist_ai_rmf": {"display_name": "NIST AI RMF", "version": "1.0"},
    "hipaa": {"display_name": "HIPAA", "version": "45 CFR 164"},
    "soc2": {"display_name": "SOC 2 Type II", "version": "2017"},
}


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


@router.get("/report/{incident_id}/export")
async def export_compliance_report(
    incident_id: str,
    framework: str = Query("eu_ai_act", description="Framework: eu_ai_act, nist_ai_rmf, hipaa, soc2"),
    format: str = Query("html", description="Export format: html, json"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export compliance report as HTML (print-to-PDF ready) or JSON.

    HTML output uses clean styling optimized for browser print-to-PDF.
    """
    # Re-use existing report generation logic
    result = await db.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    mapping_result = await db.execute(
        select(ComplianceMapping).where(
            ComplianceMapping.incident_type == incident.incident_type,
            ComplianceMapping.framework == framework,
        )
    )
    mappings = mapping_result.scalars().all()

    if format.lower() == "json":
        import json as _json

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
        }
        if framework == "eu_ai_act" and incident.severity in ("critical", "high"):
            report_data["article_73"] = {
                "article": "73",
                "title": "Reporting of serious incidents",
                "date_of_occurrence": incident.created_at.isoformat() if incident.created_at else None,
                "description": f"AI agent incident classified as {incident.incident_type} with severity {incident.severity}",
                "affected_systems": [incident.event_id or "unknown"],
                "mitigation_measures": ["Automated containment executed", "Forensic evidence captured"],
                "cross_border_impact": False,
                "reporting_deadline_hours": 24 if incident.severity == "critical" else 72,
            }
        return Response(
            content=_json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="COMPLIANCE-{incident_id}-{framework}.json"'},
        )

    # HTML export — print-to-PDF ready
    html = _build_compliance_html(incident, framework, mappings)
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="COMPLIANCE-{incident_id}-{framework}.html"'},
    )


def _build_compliance_html(incident, framework: str, mappings) -> str:
    """Build a print-to-PDF ready HTML compliance report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    severity_color = {
        "critical": "#DC2626",
        "high": "#EA580C",
        "medium": "#CA8A04",
        "low": "#16A34A",
    }.get(incident.severity, "#6B7280")

    framework_display = {
        "eu_ai_act": "EU AI Act",
        "nist_ai_rmf": "NIST AI RMF",
        "hipaa": "HIPAA",
        "soc2": "SOC 2",
    }.get(framework, framework.upper())

    rows = ""
    for m in mappings:
        rows += f"""
        <tr>
            <td style="padding:10px;border:1px solid #E5E7EB;font-family:monospace;font-size:12px">{html.escape(str(m.control_id))}</td>
            <td style="padding:10px;border:1px solid #E5E7EB;font-size:13px">{html.escape(str(m.control_name))}</td>
            <td style="padding:10px;border:1px solid #E5E7EB;font-size:13px;text-align:center">
                <span style="display:inline-block;padding:3px 10px;border-radius:9999px;font-size:11px;font-weight:600;color:#fff;background:{severity_color if m.risk_level == 'critical' else '#6B7280'}">{html.escape(str(m.risk_level).upper())}</span>
            </td>
            <td style="padding:10px;border:1px solid #E5E7EB;font-size:13px">{html.escape(str(m.mapping_data)) if m.mapping_data else '—'}</td>
        </tr>
        """

    # Article 73 box for EU AI Act critical/high
    article_73_box = ""
    if framework == "eu_ai_act" and incident.severity in ("critical", "high"):
        deadline = 24 if incident.severity == "critical" else 72
        article_73_box = f"""
        <div style="margin-top:24px;padding:16px;background:#FEF2F2;border:1px solid #FECACA;border-radius:8px">
            <h3 style="margin:0 0 8px 0;font-size:16px;color:#991B1B">EU AI Act Article 73 — Serious Incident Report</h3>
            <p style="margin:0;font-size:13px;color:#7F1D1D">
                This incident meets the threshold for mandatory reporting under Article 73.
                Reporting deadline: <strong>{deadline} hours</strong> from date of occurrence.
            </p>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Compliance Report — {html.escape(str(incident.incident_id))}</title>
    <style>
        @page {{ size: A4; margin: 20mm; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #111827; line-height: 1.5; max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ font-size: 24px; margin-bottom: 4px; }}
        h2 {{ font-size: 18px; margin-top: 32px; margin-bottom: 12px; border-bottom: 2px solid #E5E7EB; padding-bottom: 8px; }}
        .meta {{ color: #6B7280; font-size: 13px; margin-bottom: 24px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; color: #fff; background: {severity_color}; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }}
        th {{ background: #F9FAFB; padding: 10px; border: 1px solid #E5E7EB; text-align: left; font-size: 12px; font-weight: 600; color: #374151; }}
        .footer {{ margin-top: 48px; padding-top: 16px; border-top: 1px solid #E5E7EB; font-size: 11px; color: #9CA3AF; text-align: center; }}
    </style>
</head>
<body>
    <h1>Compliance Report</h1>
    <div class="meta">
        Framework: <strong>{html.escape(str(framework_display))}</strong> &nbsp;|&nbsp;
        Generated: {now} &nbsp;|&nbsp;
        Incident: <code>{html.escape(str(incident.incident_id))}</code>
    </div>

    <div style="display:flex;gap:16px;margin-bottom:24px">
        <div style="flex:1;padding:16px;background:#F9FAFB;border-radius:8px">
            <div style="font-size:11px;color:#6B7280;text-transform:uppercase;font-weight:600">Incident Type</div>
            <div style="font-size:15px;font-weight:600;margin-top:4px">{html.escape(str(incident.incident_type))}</div>
        </div>
        <div style="flex:1;padding:16px;background:#F9FAFB;border-radius:8px">
            <div style="font-size:11px;color:#6B7280;text-transform:uppercase;font-weight:600">Severity</div>
            <div style="margin-top:4px"><span class="badge">{html.escape(str(incident.severity).upper())}</span></div>
        </div>
        <div style="flex:1;padding:16px;background:#F9FAFB;border-radius:8px">
            <div style="font-size:11px;color:#6B7280;text-transform:uppercase;font-weight:600">Status</div>
            <div style="font-size:15px;font-weight:600;margin-top:4px">{html.escape(str(incident.status).upper())}</div>
        </div>
    </div>

    <h2>Mapped Controls ({len(mappings)} total)</h2>
    <table>
        <thead>
            <tr>
                <th>Control ID</th>
                <th>Control Name</th>
                <th style="width:100px">Risk Level</th>
                <th>Mapping Details</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="4" style="padding:16px;text-align:center;color:#9CA3AF">No controls mapped for this incident type and framework.</td></tr>'}
        </tbody>
    </table>

    {article_73_box}

    <div class="footer">
        Generated by PLAYBOOK — Automated Incident Response for AI Agents<br>
        Deterministic Judge Layer + NIST Organization-Defined Parameters
    </div>
</body>
</html>"""


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
    db_frameworks = {row[0] for row in result.all()}

    # Always include well-known frameworks from FRAMEWORK_META, even if no mappings exist yet
    all_frameworks = set(FRAMEWORK_META.keys()) | db_frameworks

    frameworks = [
        {
            "name": fw,
            "display_name": FRAMEWORK_META.get(fw, {}).get("display_name", fw.replace("_", " ").title()),
            "version": FRAMEWORK_META.get(fw, {}).get("version", ""),
        }
        for fw in sorted(all_frameworks)
    ]

    framework_stats = {}
    for fw in frameworks:
        count_result = await db.execute(
            select(ComplianceMapping).where(ComplianceMapping.framework == fw["name"])
        )
        count = len(count_result.scalars().all())
        framework_stats[fw["name"]] = count

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
    critical_gap_types = [
        itype for itype in uncovered_types
        if itype in ("AGT-DEL-001", "AGT-EXT-005", "AGT-CRE-008", "AGT-BYP-014")
    ]
    critical_gaps = [
        {"incident_type": t, "name": INCIDENT_TYPES.get(t, "Unknown"), "missing_controls": 0}
        for t in critical_gap_types
    ]

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


@router.post("/gemini-report", response_model=StandardResponse)
async def generate_ai_compliance_report(
    framework: str = Query(..., description="Framework to generate report for"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Generate an AI-powered narrative compliance report.

    Uses Gemini to produce an executive summary with overview,
    critical gaps, and recommendations based on gap analysis data.
    """
    from app.core.constants import INCIDENT_TYPES

    # Fetch mappings for the framework
    result = await db.execute(
        select(ComplianceMapping).where(ComplianceMapping.framework == framework)
    )
    mappings = result.scalars().all()

    covered_types = {m.incident_type for m in mappings}
    all_types = set(INCIDENT_TYPES.keys())
    uncovered_types = sorted(all_types - covered_types)

    # Build gap list for the AI
    gaps = []
    for m in mappings:
        gaps.append({
            "article": m.control_id,
            "requirement": m.control_name,
            "status": "Compliant" if m.risk_level != "critical" else "Gap",
        })
    for t in uncovered_types:
        gaps.append({
            "article": t,
            "requirement": INCIDENT_TYPES.get(t, "Unknown"),
            "status": "Uncovered",
        })

    # Sort so gaps appear first
    gaps.sort(key=lambda x: 0 if x["status"] == "Gap" else 1 if x["status"] == "Uncovered" else 2)

    report = await generate_compliance_report(framework, gaps[:15])

    return StandardResponse(
        data={
            "framework": framework,
            "model": "gemini-1.5-flash",
            "report": report,
        },
        message=f"AI compliance report generated for {framework}",
    )
