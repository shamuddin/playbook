"""Forensics API router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EvidencePackage, Incident
from app.schemas import StandardResponse
from app.services.forensics import ForensicsService
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/forensics", tags=["forensics"])


@router.get("/{incident_id}", response_model=StandardResponse)
async def get_forensics(
    incident_id: str,
    format: str = Query("json", description="Output format: json, stix, verify"),
    include_raw_logs: bool = Query(False, description="Include raw system log dumps"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get forensics evidence package for an incident.

    Supported formats:
    - json: Full package data (default)
    - stix: STIX 2.1 bundle
    - verify: Integrity verification report
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

    # Check for existing evidence package
    ev_result = await db.execute(
        select(EvidencePackage).where(EvidencePackage.incident_id == incident.id)
    )
    evidence = ev_result.scalar_one_or_none()

    if evidence is None:
        # Auto-generate on first request
        service = ForensicsService()
        evidence = await service.build_package(db, incident_id)
        await db.commit()

        # Broadcast forensics complete
        await ws_manager.broadcast({
            "event_type": "INCIDENT_FORENSICS_COMPLETE",
            "incident_id": incident_id,
            "package_id": evidence.package_id,
            "integrity_hash": evidence.integrity_hash,
            "timestamp": evidence.created_at.isoformat() if evidence.created_at else None,
        })

    service = ForensicsService()

    if format.lower() == "stix":
        data = service.export_stix(evidence)
        message = "Evidence package exported as STIX 2.1"
    elif format.lower() == "verify":
        data = service.verify_package(evidence)
        message = "Evidence package integrity verification complete"
    else:
        # Default JSON
        data = {
            "package_id": evidence.package_id,
            "incident_id": incident_id,
            "package_type": evidence.package_type,
            "integrity_hash": evidence.integrity_hash,
            "is_verified": evidence.is_verified,
            "generated_at": evidence.created_at.isoformat() if evidence.created_at else None,
            "retention_until": evidence.retention_until.isoformat() if evidence.retention_until else None,
            "artifacts": list(evidence.package_data.get("artifacts", {}).keys()),
            "manifest": evidence.package_data.get("manifest", {}),
            "signature": evidence.package_data.get("signature", {}),
        }
        if include_raw_logs:
            data["raw_logs"] = evidence.package_data.get("artifacts", {}).get("audit", [])
        message = "Evidence package retrieved"

    return StandardResponse(data=data, message=message)


@router.get("/{incident_id}/export")
async def export_forensics(
    incident_id: str,
    format: str = Query("zip", description="Export format: zip, html"),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export forensics package as ZIP or HTML download."""
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

    # Get or generate evidence package
    ev_result = await db.execute(
        select(EvidencePackage).where(EvidencePackage.incident_id == incident.id)
    )
    evidence = ev_result.scalar_one_or_none()

    if evidence is None:
        service = ForensicsService()
        evidence = await service.build_package(db, incident_id)
        await db.commit()

    service = ForensicsService()

    if format.lower() == "html":
        html = service.export_pdf_html(evidence)
        filename = f"EVIDENCE-{incident_id}.html"
        return Response(
            content=html,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Default ZIP
    zip_bytes = service.export_zip(evidence)
    filename = f"EVIDENCE-{incident_id}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{incident_id}/verify", response_model=StandardResponse)
async def verify_forensics(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Verify the cryptographic integrity of an evidence package."""
    result = await db.execute(
        select(Incident).where(Incident.incident_id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    ev_result = await db.execute(
        select(EvidencePackage).where(EvidencePackage.incident_id == incident.id)
    )
    evidence = ev_result.scalar_one_or_none()

    if evidence is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evidence package found for incident {incident_id}",
        )

    service = ForensicsService()
    report = service.verify_package(evidence)

    return StandardResponse(
        data=report,
        message="Integrity verification complete",
    )
