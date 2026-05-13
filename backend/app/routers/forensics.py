"""Forensics API router."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EvidencePackage, Incident
from app.schemas import EvidencePackageResponse, StandardResponse
from app.services.forensics import ForensicsService

router = APIRouter(prefix="/forensics", tags=["forensics"])


@router.get("/{incident_id}", response_model=StandardResponse)
async def get_forensics(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get forensics evidence package for an incident (JSON)."""
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

    return StandardResponse(
        data={
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
        },
        message="Evidence package retrieved",
    )


@router.get("/{incident_id}/export")
async def export_forensics(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export forensics package as ZIP download."""
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

    # Generate ZIP
    service = ForensicsService()
    zip_bytes = service.export_zip(evidence)

    filename = f"EVIDENCE-{incident_id}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
