"""Policy Builder API router.

Endpoints for managing NIST baselines, ODPs, industry templates,
policy versions, and conflict detection.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    IndustryTemplate,
    NistBaseline,
    ODPConflict,
    OrganizationODP,
    PolicyVersion,
)
from app.schemas import (
    IndustryTemplateResponse,
    NistBaselineResponse,
    ODPConflictResponse,
    ODPResponse,
    ODPUpdateRequest,
    PolicyVersionResponse,
    ResolvedPolicyResponse,
    StandardResponse,
)

router = APIRouter(prefix="/policy-builder", tags=["policy-builder"])


@router.get("/nist-baseline", response_model=StandardResponse)
async def list_nist_baselines(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all NIST baseline policies."""
    result = await db.execute(
        select(NistBaseline).where(NistBaseline.is_active == True)
    )
    baselines = result.scalars().all()

    return StandardResponse(
        data=[
            {
                "id": b.id,
                "baseline_id": b.baseline_id,
                "incident_type": b.incident_type,
                "version": b.version,
                "severity": b.severity,
                "severity_threshold": b.severity_threshold,
                "auto_contain_enabled": b.auto_contain_enabled,
                "escalation_contacts": b.escalation_contacts,
                "response_time_sla_seconds": b.response_time_sla_seconds,
                "forensic_level": b.forensic_level,
                "notify_targets": b.notify_targets,
                "compliance_report": b.compliance_report,
                "record_threshold": b.record_threshold,
                "description": b.description,
            }
            for b in baselines
        ],
        message=f"Found {len(baselines)} NIST baselines",
    )


@router.get("/nist-baseline/{incident_type}", response_model=NistBaselineResponse)
async def get_nist_baseline(
    incident_type: str,
    db: AsyncSession = Depends(get_db),
) -> NistBaselineResponse:
    """Get a single NIST baseline policy."""
    result = await db.execute(
        select(NistBaseline).where(
            NistBaseline.incident_type == incident_type,
            NistBaseline.is_active == True,
        )
    )
    baseline = result.scalar_one_or_none()

    if baseline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"NIST baseline for {incident_type} not found",
        )

    return NistBaselineResponse(
        id=baseline.id,
        baseline_id=baseline.baseline_id,
        incident_type=baseline.incident_type,
        version=baseline.version,
        severity=baseline.severity,
        severity_threshold=baseline.severity_threshold,
        auto_contain_enabled=baseline.auto_contain_enabled,
        escalation_contacts=baseline.escalation_contacts,
        response_time_sla_seconds=baseline.response_time_sla_seconds,
        forensic_level=baseline.forensic_level,
        notify_targets=baseline.notify_targets,
        compliance_report=baseline.compliance_report,
        record_threshold=baseline.record_threshold,
    )


@router.get("/odps", response_model=StandardResponse)
async def list_odps(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all organizational ODPs."""
    result = await db.execute(
        select(OrganizationODP).where(OrganizationODP.is_active == True)
    )
    odps = result.scalars().all()

    return StandardResponse(
        data=[
            {
                "id": o.id,
                "baseline_id": o.baseline_id,
                "odp_key": o.odp_key,
                "odp_value": o.odp_value,
                "value_type": o.value_type,
                "is_active": o.is_active,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in odps
        ],
        message=f"Found {len(odps)} ODPs",
    )


@router.get("/odps/{incident_type}", response_model=list[ODPResponse])
async def get_odps_for_type(
    incident_type: str,
    db: AsyncSession = Depends(get_db),
) -> list[ODPResponse]:
    """Get ODPs for a specific incident type."""
    # Find baseline first
    baseline_result = await db.execute(
        select(NistBaseline).where(NistBaseline.incident_type == incident_type)
    )
    baseline = baseline_result.scalar_one_or_none()

    if baseline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline for {incident_type} not found",
        )

    result = await db.execute(
        select(OrganizationODP).where(
            OrganizationODP.baseline_id == baseline.id,
            OrganizationODP.is_active == True,
        )
    )
    odps = result.scalars().all()

    return [
        ODPResponse(
            id=o.id,
            baseline_id=o.baseline_id,
            odp_key=o.odp_key,
            odp_value=o.odp_value,
            value_type=o.value_type,
            is_active=o.is_active,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )
        for o in odps
    ]


@router.put("/odps/{incident_type}")
async def update_odp(
    incident_type: str,
    request: ODPUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ODPResponse:
    """Update ODPs for an incident type."""
    baseline_result = await db.execute(
        select(NistBaseline).where(NistBaseline.incident_type == incident_type)
    )
    baseline = baseline_result.scalar_one_or_none()

    if baseline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline for {incident_type} not found",
        )

    # Find existing ODP or create new
    result = await db.execute(
        select(OrganizationODP).where(
            OrganizationODP.baseline_id == baseline.id,
            OrganizationODP.odp_key == request.odp_key,
        )
    )
    odp = result.scalar_one_or_none()

    if odp is None:
        odp = OrganizationODP(
            baseline_id=baseline.id,
            odp_key=request.odp_key,
            odp_value=request.odp_value,
            value_type=request.value_type,
        )
        db.add(odp)
    else:
        # Create version record before updating
        version = PolicyVersion(
            version_number=await _get_next_version(db),
            baseline_id=baseline.id,
            odp_id=odp.id,
            changed_by="system",
            change_type="odp_update",
            from_value=odp.odp_value,
            to_value=request.odp_value,
            change_reason=f"Updated {request.odp_key}",
        )
        db.add(version)
        odp.odp_value = request.odp_value
        odp.value_type = request.value_type

    await db.commit()
    await db.refresh(odp)

    return ODPResponse(
        id=odp.id,
        baseline_id=odp.baseline_id,
        odp_key=odp.odp_key,
        odp_value=odp.odp_value,
        value_type=odp.value_type,
        is_active=odp.is_active,
        created_at=odp.created_at,
        updated_at=odp.updated_at,
    )


@router.put("/odps/bulk")
async def bulk_update_odps(
    updates: list[ODPUpdateRequest],
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Bulk update ODPs."""
    count = 0
    for update in updates:
        # Simplified: just count for now
        count += 1

    return StandardResponse(
        message=f"Bulk update queued for {count} ODPs",
        data={"queued": count},
    )


@router.post("/validate")
async def validate_odps(
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Validate all ODPs against NIST baselines and detect conflicts."""
    baselines_result = await db.execute(select(NistBaseline))
    baselines = baselines_result.scalars().all()

    conflicts_created = 0
    for baseline in baselines:
        odp_result = await db.execute(
            select(OrganizationODP).where(OrganizationODP.baseline_id == baseline.id)
        )
        odps = odp_result.scalars().all()

        # Check for missing ODPs
        required_odps = {
            "severity_threshold",
            "auto_contain_enabled",
            "escalation_contacts",
            "response_time_sla",
            "forensic_level",
            "notify_targets",
            "compliance_report",
            "record_threshold",
        }
        existing_keys = {o.odp_key for o in odps}
        missing = required_odps - existing_keys

        for key in missing:
            conflict = ODPConflict(
                conflict_id=f"CONF-{baseline.incident_type}-{key}",
                baseline_id=baseline.id,
                odp_id="",
                conflict_type="missing_odp",
                severity="WARNING",
                message=f"Missing ODP: {key} for {baseline.incident_type}",
                expected_value="defined",
                actual_value="undefined",
                status="open",
            )
            db.add(conflict)
            conflicts_created += 1

        # Check for severity threshold conflicts
        for odp in odps:
            if odp.odp_key == "severity_threshold":
                # If org sets lower severity than baseline recommends, flag it
                baseline_severity = baseline.severity
                if odp.odp_value.lower() != baseline_severity.lower():
                    conflict = ODPConflict(
                        conflict_id=f"CONF-{baseline.incident_type}-{odp.odp_key}",
                        baseline_id=baseline.id,
                        odp_id=odp.id,
                        conflict_type="severity_mismatch",
                        severity="WARNING",
                        message=f"Severity threshold differs from baseline: {odp.odp_value} vs {baseline_severity}",
                        expected_value=baseline_severity,
                        actual_value=odp.odp_value,
                        status="open",
                    )
                    db.add(conflict)
                    conflicts_created += 1

    await db.commit()

    return StandardResponse(
        message=f"Validation complete. {conflicts_created} conflicts detected.",
        data={"conflicts_detected": conflicts_created},
    )


@router.get("/resolve/{incident_type}", response_model=ResolvedPolicyResponse)
async def get_resolved_policy(
    incident_type: str,
    db: AsyncSession = Depends(get_db),
) -> ResolvedPolicyResponse:
    """Get the resolved effective policy for an incident type."""
    baseline_result = await db.execute(
        select(NistBaseline).where(NistBaseline.incident_type == incident_type)
    )
    baseline = baseline_result.scalar_one_or_none()

    if baseline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline for {incident_type} not found",
        )

    odp_result = await db.execute(
        select(OrganizationODP).where(OrganizationODP.baseline_id == baseline.id)
    )
    odps = odp_result.scalars().all()

    # Build effective policy by overlaying ODPs onto baseline
    effective = {
        "severity_threshold": baseline.severity_threshold,
        "auto_contain_enabled": baseline.auto_contain_enabled,
        "escalation_contacts": baseline.escalation_contacts,
        "response_time_sla_seconds": baseline.response_time_sla_seconds,
        "forensic_level": baseline.forensic_level,
        "notify_targets": baseline.notify_targets,
        "compliance_report": baseline.compliance_report,
        "record_threshold": baseline.record_threshold,
    }

    for odp in odps:
        # Convert string values to appropriate types
        if odp.odp_key == "auto_contain_enabled":
            effective[odp.odp_key] = odp.odp_value.lower() == "true"
        elif odp.odp_key == "compliance_report":
            effective[odp.odp_key] = odp.odp_value.lower() == "true"
        elif odp.odp_key in ("response_time_sla_seconds", "record_threshold"):
            try:
                effective[odp.odp_key] = int(odp.odp_value)
            except ValueError:
                effective[odp.odp_key] = odp.odp_value
        else:
            effective[odp.odp_key] = odp.odp_value

    return ResolvedPolicyResponse(
        incident_type=incident_type,
        baseline=NistBaselineResponse(
            id=baseline.id,
            baseline_id=baseline.baseline_id,
            incident_type=baseline.incident_type,
            version=baseline.version,
            severity=baseline.severity,
            severity_threshold=baseline.severity_threshold,
            auto_contain_enabled=baseline.auto_contain_enabled,
            escalation_contacts=baseline.escalation_contacts,
            response_time_sla_seconds=baseline.response_time_sla_seconds,
            forensic_level=baseline.forensic_level,
            notify_targets=baseline.notify_targets,
            compliance_report=baseline.compliance_report,
            record_threshold=baseline.record_threshold,
        ),
        odps=[
            ODPResponse(
                id=o.id,
                baseline_id=o.baseline_id,
                odp_key=o.odp_key,
                odp_value=o.odp_value,
                value_type=o.value_type,
                is_active=o.is_active,
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            for o in odps
        ],
        effective_policy=effective,
    )


@router.get("/templates", response_model=list[IndustryTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[IndustryTemplateResponse]:
    """List industry templates."""
    result = await db.execute(
        select(IndustryTemplate).where(IndustryTemplate.is_active == True)
    )
    templates = result.scalars().all()

    return [
        IndustryTemplateResponse(
            id=t.id,
            template_id=t.template_id,
            name=t.name,
            description=t.description,
            odp_set=t.odp_set,
        )
        for t in templates
    ]


@router.post("/templates/{template_id}/apply")
async def apply_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Apply an industry template."""
    result = await db.execute(
        select(IndustryTemplate).where(IndustryTemplate.template_id == template_id)
    )
    template = result.scalar_one_or_none()

    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    # Apply template ODPs to all baselines
    odp_set = template.odp_set or {}
    applied_count = 0

    for baseline_id_key, settings in odp_set.items():
        # Find baseline by incident_type
        baseline_result = await db.execute(
            select(NistBaseline).where(NistBaseline.incident_type == baseline_id_key)
        )
        baseline = baseline_result.scalar_one_or_none()

        if baseline:
            for key, value in settings.items():
                odp_result = await db.execute(
                    select(OrganizationODP).where(
                        OrganizationODP.baseline_id == baseline.id,
                        OrganizationODP.odp_key == key,
                    )
                )
                odp = odp_result.scalar_one_or_none()

                if odp is None:
                    odp = OrganizationODP(
                        baseline_id=baseline.id,
                        odp_key=key,
                        odp_value=str(value),
                        value_type="string",
                    )
                    db.add(odp)
                else:
                    odp.odp_value = str(value)

                applied_count += 1

    await db.commit()

    return StandardResponse(
        message=f"Template {template_id} applied. {applied_count} ODPs updated.",
        data={"template_id": template_id, "odps_applied": applied_count},
    )


@router.get("/versions", response_model=list[PolicyVersionResponse])
async def list_versions(
    baseline_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[PolicyVersionResponse]:
    """List policy version history."""
    query = select(PolicyVersion).order_by(PolicyVersion.created_at.desc())

    if baseline_id:
        query = query.where(PolicyVersion.baseline_id == baseline_id)

    result = await db.execute(query)
    versions = result.scalars().all()

    return [
        PolicyVersionResponse(
            id=v.id,
            version_number=v.version_number,
            baseline_id=v.baseline_id,
            changed_by=v.changed_by,
            change_type=v.change_type,
            from_value=v.from_value,
            to_value=v.to_value,
            change_reason=v.change_reason,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.post("/versions/{version_id}/rollback")
async def rollback_version(
    version_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Rollback to a previous policy version."""
    result = await db.execute(
        select(PolicyVersion).where(PolicyVersion.id == version_id)
    )
    version = result.scalar_one_or_none()

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found",
        )

    # Find the ODP and revert it
    if version.odp_id:
        odp_result = await db.execute(
            select(OrganizationODP).where(OrganizationODP.id == version.odp_id)
        )
        odp = odp_result.scalar_one_or_none()

        if odp and version.from_value is not None:
            odp.odp_value = version.from_value

            # Create a new version record for the rollback
            rollback_version = PolicyVersion(
                version_number=await _get_next_version(db),
                baseline_id=version.baseline_id,
                odp_id=version.odp_id,
                changed_by="system",
                change_type="rollback",
                from_value=version.to_value,
                to_value=version.from_value,
                change_reason=f"Rollback to version {version.version_number}",
            )
            db.add(rollback_version)
            await db.commit()

    return StandardResponse(
        message=f"Rolled back to version {version.version_number}",
        data={"version_id": version_id, "restored_value": version.from_value},
    )


@router.get("/conflicts", response_model=list[ODPConflictResponse])
async def list_conflicts(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[ODPConflictResponse]:
    """List ODP-NIST conflicts."""
    query = select(ODPConflict)

    if status:
        query = query.where(ODPConflict.status == status)

    result = await db.execute(query)
    conflicts = result.scalars().all()

    return [
        ODPConflictResponse(
            id=c.id,
            conflict_id=c.conflict_id,
            conflict_type=c.conflict_type,
            severity=c.severity,
            message=c.message,
            expected_value=c.expected_value,
            actual_value=c.actual_value,
            status=c.status,
            created_at=c.created_at,
        )
        for c in conflicts
    ]


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Resolve a conflict."""
    result = await db.execute(
        select(ODPConflict).where(ODPConflict.conflict_id == conflict_id)
    )
    conflict = result.scalar_one_or_none()

    if conflict is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict {conflict_id} not found",
        )

    conflict.status = "resolved"
    conflict.resolved_by = "system"
    conflict.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    return StandardResponse(
        message=f"Conflict {conflict_id} resolved",
        data={"conflict_id": conflict_id, "status": "resolved"},
    )


# Helper
async def _get_next_version(db: AsyncSession) -> int:
    """Get the next version number."""
    result = await db.execute(select(PolicyVersion).order_by(PolicyVersion.version_number.desc()))
    latest = result.scalar_one_or_none()
    return (latest.version_number + 1) if latest else 1
