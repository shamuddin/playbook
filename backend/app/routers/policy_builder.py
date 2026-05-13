"""Policy Builder API router.

Endpoints for managing NIST baselines, ODPs, industry templates,
policy versions, and conflict detection.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import INCIDENT_TYPES
from app.database import get_db
from app.models import (
    IndustryTemplate,
    NistBaseline,
    ODPConflict,
    OrganizationODP,
    PolicyVersion,
)
from app.policy import BaselineLoader, ConflictDetector, ODPResolver
from app.schemas import (
    ConflictDetail,
    ConflictResolveBody,
    ConflictResolveResponse,
    IndustryTemplateResponse,
    NistBaselineResponse,
    ODPConflictResponse,
    ODPResponse,
    ODPEntryResponse,
    ODPsForTypeResponse,
    ODPsUpdateBody,
    ODPsUpdateResponse,
    ODPUpdateRequest,
    PolicyVersionResponse,
    ResolvedPolicyResponse,
    RollbackBody,
    RollbackResponse,
    StandardResponse,
    TemplateApplyBody,
    TemplateApplyResponse,
    TemplateApplyResult,
    ValidateResponse,
    ValidationResult,
)

router = APIRouter(prefix="/policy-builder", tags=["policy-builder"])


# ============================================================================
# NIST Baselines
# ============================================================================

@router.get("/nist-baseline", response_model=StandardResponse)
async def list_nist_baselines(
    incident_type: Optional[str] = Query(None),
    sort_by: str = Query("incident_type"),
    sort_order: str = Query("asc"),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all NIST baseline policies."""
    query = select(NistBaseline).where(NistBaseline.is_active == True)

    if incident_type:
        query = query.where(NistBaseline.incident_type == incident_type)

    sort_field = getattr(NistBaseline, sort_by, NistBaseline.incident_type)
    if sort_order.lower() == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())

    result = await db.execute(query)
    baselines = result.scalars().all()

    # Compute summary
    total = len(baselines)
    critical_count = sum(1 for b in baselines if b.severity == "critical")

    return StandardResponse(
        data={
            "items": [
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
            "summary": {
                "total": total,
                "critical_count": critical_count,
            },
        },
        message=f"Found {total} NIST baselines",
    )


@router.get("/nist-baseline/{incident_type}", response_model=StandardResponse)
async def get_nist_baseline(
    incident_type: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get a single NIST baseline policy with ODP placeholders."""
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

    # ODP placeholders
    odp_placeholders = [
        {"key": "severity_threshold", "label": "Severity Threshold", "type": "dropdown", "default": baseline.severity_threshold},
        {"key": "auto_contain_enabled", "label": "Auto Contain", "type": "toggle", "default": str(baseline.auto_contain_enabled).lower()},
        {"key": "escalation_contacts", "label": "Escalation Contacts", "type": "chips", "default": baseline.escalation_contacts},
        {"key": "response_time_sla", "label": "Response SLA (seconds)", "type": "number", "default": str(baseline.response_time_sla_seconds)},
        {"key": "forensic_level", "label": "Forensic Level", "type": "dropdown", "default": baseline.forensic_level},
        {"key": "notify_targets", "label": "Notify Targets", "type": "chips", "default": baseline.notify_targets},
        {"key": "compliance_report", "label": "Compliance Report", "type": "toggle", "default": str(baseline.compliance_report).lower()},
        {"key": "record_threshold", "label": "Record Threshold", "type": "number", "default": str(baseline.record_threshold)},
    ]

    return StandardResponse(
        data={
            "id": baseline.id,
            "baseline_id": baseline.baseline_id,
            "incident_type": baseline.incident_type,
            "version": baseline.version,
            "severity": baseline.severity,
            "severity_threshold": baseline.severity_threshold,
            "auto_contain_enabled": baseline.auto_contain_enabled,
            "escalation_contacts": baseline.escalation_contacts,
            "response_time_sla_seconds": baseline.response_time_sla_seconds,
            "forensic_level": baseline.forensic_level,
            "notify_targets": baseline.notify_targets,
            "compliance_report": baseline.compliance_report,
            "record_threshold": baseline.record_threshold,
            "description": baseline.description,
            "odp_placeholders": odp_placeholders,
            "defaults": {
                "severity_threshold": baseline.severity_threshold,
                "auto_contain_enabled": baseline.auto_contain_enabled,
                "escalation_contacts": baseline.escalation_contacts,
                "response_time_sla_seconds": baseline.response_time_sla_seconds,
                "forensic_level": baseline.forensic_level,
                "notify_targets": baseline.notify_targets,
                "compliance_report": baseline.compliance_report,
                "record_threshold": baseline.record_threshold,
            },
        },
        message="NIST baseline retrieved",
    )


# ============================================================================
# ODPs
# ============================================================================

@router.get("/odps", response_model=StandardResponse)
async def list_odps(
    baseline_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List all organizational ODPs."""
    query = select(OrganizationODP).where(OrganizationODP.is_active == True)
    if baseline_id:
        query = query.where(OrganizationODP.baseline_id == baseline_id)

    result = await db.execute(query)
    odps = result.scalars().all()

    return StandardResponse(
        data={
            "items": [
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
            "summary": {
                "total": len(odps),
            },
        },
        message=f"Found {len(odps)} ODPs",
    )


@router.get("/odps/{incident_type}", response_model=StandardResponse)
async def get_odps_for_type(
    incident_type: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get structured ODPs for a specific incident type."""
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

    # Build structured ODP map with defaults from baseline
    defaults = {
        "severity_threshold": baseline.severity_threshold,
        "auto_contain_enabled": str(baseline.auto_contain_enabled).lower(),
        "escalation_contacts": str(baseline.escalation_contacts),
        "response_time_sla": str(baseline.response_time_sla_seconds),
        "forensic_level": baseline.forensic_level,
        "notify_targets": str(baseline.notify_targets),
        "compliance_report": str(baseline.compliance_report).lower(),
        "record_threshold": str(baseline.record_threshold),
    }

    odp_map: Dict[str, ODPEntryResponse] = {}
    for odp in odps:
        nist_default = defaults.get(odp.odp_key)
        odp_map[odp.odp_key] = ODPEntryResponse(
            value=odp.odp_value,
            is_override=odp.odp_value != nist_default if nist_default else True,
            nist_default=nist_default,
            value_type=odp.value_type,
        )

    # Count conflicts
    conflict_result = await db.execute(
        select(ODPConflict).where(
            ODPConflict.baseline_id == baseline.id,
            ODPConflict.status == "open",
        )
    )
    conflicts = conflict_result.scalars().all()

    last_updated = max((o.updated_at for o in odps), default=None)

    return StandardResponse(
        data={
            "incident_type": incident_type,
            "incident_name": INCIDENT_TYPES.get(incident_type, "Unknown"),
            "odp_count": len(odps),
            "version": baseline.version,
            "odps": {k: v.model_dump() for k, v in odp_map.items()},
            "conflicts_detected": len(conflicts),
            "last_updated": last_updated.isoformat() if last_updated else None,
            "updated_by": "system",
        },
        message=f"Found {len(odps)} ODPs for {incident_type}",
    )


@router.put("/odps/bulk")
async def bulk_update_odps(
    updates: Dict[str, Dict[str, str]],
    skip_validation: bool = False,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Bulk update ODPs across multiple incident types.

    updates: {incident_type: {odp_key: odp_value, ...}, ...}
    """
    total_applied = 0
    total_conflicts = 0

    for incident_type, odps in updates.items():
        baseline_result = await db.execute(
            select(NistBaseline).where(NistBaseline.incident_type == incident_type)
        )
        baseline = baseline_result.scalar_one_or_none()
        if not baseline:
            continue

        for key, value in odps.items():
            result = await db.execute(
                select(OrganizationODP).where(
                    OrganizationODP.baseline_id == baseline.id,
                    OrganizationODP.odp_key == key,
                )
            )
            odp = result.scalar_one_or_none()
            if odp is None:
                odp = OrganizationODP(
                    baseline_id=baseline.id,
                    odp_key=key,
                    odp_value=value,
                    value_type="string",
                )
                db.add(odp)
            else:
                version = PolicyVersion(
                    version_number=await _get_next_version(db),
                    baseline_id=baseline.id,
                    odp_id=odp.id,
                    changed_by="system",
                    change_type="bulk_update",
                    from_value=odp.odp_value,
                    to_value=value,
                    change_reason=f"Bulk update: {key}",
                )
                db.add(version)
                odp.odp_value = value
            total_applied += 1

        if not skip_validation:
            total_conflicts += await _validate_baseline(db, baseline)

    await db.commit()

    return StandardResponse(
        message=f"Bulk update complete. {total_applied} ODPs updated, {total_conflicts} conflicts detected.",
        data={"applied": total_applied, "conflicts": total_conflicts},
    )


# ============================================================================
# Validation
# ============================================================================

@router.put("/odps/{incident_type}")
async def update_odp(
    incident_type: str,
    request: ODPsUpdateBody,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Update multiple ODPs for an incident type."""
    baseline_result = await db.execute(
        select(NistBaseline).where(NistBaseline.incident_type == incident_type)
    )
    baseline = baseline_result.scalar_one_or_none()

    if baseline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline for {incident_type} not found",
        )

    applied = 0
    for key, value in request.odps.items():
        result = await db.execute(
            select(OrganizationODP).where(
                OrganizationODP.baseline_id == baseline.id,
                OrganizationODP.odp_key == key,
            )
        )
        odp = result.scalar_one_or_none()

        if odp is None:
            odp = OrganizationODP(
                baseline_id=baseline.id,
                odp_key=key,
                odp_value=value,
                value_type="string",
            )
            db.add(odp)
        else:
            version = PolicyVersion(
                version_number=await _get_next_version(db),
                baseline_id=baseline.id,
                odp_id=odp.id,
                changed_by="system",
                change_type="odp_update",
                from_value=odp.odp_value,
                to_value=value,
                change_reason=f"Updated {key}",
            )
            db.add(version)
            odp.odp_value = value

        applied += 1

    await db.commit()

    # Run validation if not skipped
    conflicts = 0
    if not request.skip_validation:
        conflicts = await _validate_baseline(db, baseline)

    # Build resolved policy
    odp_result = await db.execute(
        select(OrganizationODP).where(OrganizationODP.baseline_id == baseline.id)
    )
    all_odps = odp_result.scalars().all()
    effective = _build_effective_policy(baseline, all_odps)

    latest_version = await db.execute(
        select(PolicyVersion).where(PolicyVersion.baseline_id == baseline.id)
        .order_by(PolicyVersion.version_number.desc())
    )
    latest = latest_version.scalar_one_or_none()

    return StandardResponse(
        data={
            "incident_type": incident_type,
            "odps_applied": applied,
            "conflicts_detected": conflicts,
            "version": latest.version_number if latest else 1,
            "resolved_policy": effective,
        },
        message=f"Updated {applied} ODPs for {incident_type}",
    )


@router.post("/validate")
async def validate_odps(
    body: Optional[Dict[str, Dict[str, str]]] = None,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Validate ODPs against NIST baselines and detect conflicts.

    If body is provided, validates the proposed ODPs (dry-run).
    Otherwise validates all existing ODPs in the database.
    """
    baselines_result = await db.execute(select(NistBaseline))
    baselines = baselines_result.scalars().all()

    results: List[ValidationResult] = []
    total_conflicts = 0

    for baseline in baselines:
        odp_result = await db.execute(
            select(OrganizationODP).where(OrganizationODP.baseline_id == baseline.id)
        )
        odps = {o.odp_key: o.odp_value for o in odp_result.scalars().all()}

        # If body provided, overlay proposed values
        proposed = body.get(baseline.incident_type, {}) if body else {}
        merged = {**odps, **proposed}

        conflicts: List[ConflictDetail] = []

        # Check for missing required ODPs
        required = {
            "severity_threshold", "auto_contain_enabled", "escalation_contacts",
            "response_time_sla", "forensic_level", "notify_targets",
            "compliance_report", "record_threshold",
        }
        for key in required - set(merged.keys()):
            conflicts.append(ConflictDetail(
                type="MISSING_REQUIRED",
                severity="BLOCKED",
                message=f"Missing required ODP: {key}",
                suggestion=f"Set {key} to baseline default",
            ))

        # Check for severity downgrade
        if "severity_threshold" in merged:
            st = merged["severity_threshold"].lower()
            base_sev = baseline.severity.lower()
            severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            if severity_rank.get(st, 0) < severity_rank.get(base_sev, 0):
                conflicts.append(ConflictDetail(
                    type="SEVERITY_DOWNGRADE",
                    severity="BLOCKED",
                    message=f"Severity threshold ({st}) is lower than NIST baseline ({base_sev})",
                    nist_value=base_sev,
                    odp_value=st,
                    suggestion="Match or exceed baseline severity",
                ))

        # Check for auto-contain disabled
        if merged.get("auto_contain_enabled", "").lower() == "false" and baseline.auto_contain_enabled:
            conflicts.append(ConflictDetail(
                type="VALUE_MISMATCH",
                severity="WARNING",
                message="Auto-contain is disabled but NIST baseline recommends enabled",
                nist_value="true",
                odp_value="false",
                suggestion="Enable auto-contain for compliance",
            ))

        # Check for SLA too long
        if "response_time_sla" in merged:
            try:
                sla = int(merged["response_time_sla"])
                if sla > baseline.response_time_sla_seconds * 2:
                    conflicts.append(ConflictDetail(
                        type="THRESHOLD_VIOLATION",
                        severity="WARNING",
                        message=f"Response SLA ({sla}s) exceeds 2x NIST recommendation ({baseline.response_time_sla_seconds}s)",
                        nist_value=str(baseline.response_time_sla_seconds),
                        odp_value=str(sla),
                        suggestion="Reduce SLA to within 2x of baseline",
                    ))
            except ValueError:
                pass

        # Check for forensic level reduction
        if "forensic_level" in merged:
            fl = merged["forensic_level"].lower()
            base_fl = baseline.forensic_level.lower()
            if fl == "none" and base_fl in ("full", "standard"):
                conflicts.append(ConflictDetail(
                    type="FORENSIC_LEVEL_REDUCTION",
                    severity="WARNING",
                    message=f"Forensic level reduced to '{fl}' from baseline '{base_fl}'",
                    nist_value=base_fl,
                    odp_value=fl,
                    suggestion="Maintain at least STANDARD forensic level",
                ))

        # Check for compliance report disabled
        if merged.get("compliance_report", "").lower() == "false" and baseline.compliance_report:
            conflicts.append(ConflictDetail(
                type="COMPLIANCE_REPORT_DISABLED",
                severity="WARNING",
                message="Compliance report generation is disabled but baseline requires it",
                nist_value="true",
                odp_value="false",
                suggestion="Enable compliance report generation",
            ))

        # Check for empty escalation contacts
        if "escalation_contacts" in merged:
            contacts = merged["escalation_contacts"]
            if not contacts or contacts in ("[]", "", "null"):
                conflicts.append(ConflictDetail(
                    type="MISSING_REQUIRED",
                    severity="BLOCKED",
                    message="No escalation contacts defined for CRITICAL incidents",
                    suggestion="Add at least one escalation contact",
                ))

        # Persist conflicts if validating existing (not dry-run)
        if body is None:
            for i, cd in enumerate(conflicts):
                conflict = ODPConflict(
                    conflict_id=f"CONF-{baseline.incident_type}-{cd.type}-{i}",
                    baseline_id=baseline.id,
                    odp_id="",
                    conflict_type=cd.type,
                    severity=cd.severity,
                    message=cd.message,
                    expected_value=cd.nist_value,
                    actual_value=cd.odp_value,
                    status="open",
                )
                db.add(conflict)

        total_conflicts += len(conflicts)
        results.append(ValidationResult(
            incident_type=baseline.incident_type,
            valid=len(conflicts) == 0,
            conflicts=conflicts,
        ))

    if body is None:
        await db.commit()

    return StandardResponse(
        data={
            "valid": total_conflicts == 0,
            "total_validated": len(baselines),
            "total_conflicts": total_conflicts,
            "results": [r.model_dump() for r in results],
        },
        message=f"Validation complete. {total_conflicts} conflicts detected.",
    )


# ============================================================================
# Resolved Policy
# ============================================================================

@router.get("/resolve/{incident_type}", response_model=StandardResponse)
async def get_resolved_policy(
    incident_type: str,
    include_conflicts: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
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

    effective = _build_effective_policy(baseline, odps)

    response_data: Dict[str, Any] = {
        "incident_type": incident_type,
        "incident_name": INCIDENT_TYPES.get(incident_type, "Unknown"),
        "baseline": {
            "id": baseline.id,
            "baseline_id": baseline.baseline_id,
            "incident_type": baseline.incident_type,
            "version": baseline.version,
            "severity": baseline.severity,
            "severity_threshold": baseline.severity_threshold,
            "auto_contain_enabled": baseline.auto_contain_enabled,
            "escalation_contacts": baseline.escalation_contacts,
            "response_time_sla_seconds": baseline.response_time_sla_seconds,
            "forensic_level": baseline.forensic_level,
            "notify_targets": baseline.notify_targets,
            "compliance_report": baseline.compliance_report,
            "record_threshold": baseline.record_threshold,
        },
        "effective_policy": effective,
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }

    if include_conflicts:
        conflict_result = await db.execute(
            select(ODPConflict).where(
                ODPConflict.baseline_id == baseline.id,
                ODPConflict.status == "open",
            )
        )
        conflicts = conflict_result.scalars().all()
        response_data["conflicts"] = [
            {
                "conflict_id": c.conflict_id,
                "conflict_type": c.conflict_type,
                "severity": c.severity,
                "message": c.message,
                "expected_value": c.expected_value,
                "actual_value": c.actual_value,
            }
            for c in conflicts
        ]

    return StandardResponse(data=response_data, message="Resolved policy retrieved")


# ============================================================================
# Templates
# ============================================================================

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
    body: TemplateApplyBody = TemplateApplyBody(),
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

    odp_set = template.odp_set or {}
    target_types = body.incident_types or list(odp_set.keys())

    results: List[TemplateApplyResult] = []
    total_applied = 0
    total_conflicts = 0

    for incident_type in target_types:
        if incident_type not in odp_set:
            continue

        baseline_result = await db.execute(
            select(NistBaseline).where(NistBaseline.incident_type == incident_type)
        )
        baseline = baseline_result.scalar_one_or_none()
        if not baseline:
            continue

        settings = odp_set[incident_type]
        applied_count = 0
        skipped_count = 0

        for key, value in settings.items():
            odp_result = await db.execute(
                select(OrganizationODP).where(
                    OrganizationODP.baseline_id == baseline.id,
                    OrganizationODP.odp_key == key,
                )
            )
            odp = odp_result.scalar_one_or_none()

            if odp is None:
                if not body.dry_run:
                    odp = OrganizationODP(
                        baseline_id=baseline.id,
                        odp_key=key,
                        odp_value=str(value),
                        value_type="string",
                    )
                    db.add(odp)
                applied_count += 1
            elif body.overwrite_existing:
                if not body.dry_run:
                    version = PolicyVersion(
                        version_number=await _get_next_version(db),
                        baseline_id=baseline.id,
                        odp_id=odp.id,
                        changed_by="system",
                        change_type="template_apply",
                        from_value=odp.odp_value,
                        to_value=str(value),
                        change_reason=f"Applied template {template_id}",
                    )
                    db.add(version)
                    odp.odp_value = str(value)
                applied_count += 1
            else:
                skipped_count += 1

        total_applied += applied_count

        # Validate conflicts
        conflicts = 0
        if not body.dry_run:
            conflicts = await _validate_baseline(db, baseline)
        total_conflicts += conflicts

        latest_version = await db.execute(
            select(PolicyVersion).where(PolicyVersion.baseline_id == baseline.id)
            .order_by(PolicyVersion.version_number.desc())
        )
        latest = latest_version.scalar_one_or_none()

        results.append(TemplateApplyResult(
            incident_type=incident_type,
            odps_applied=applied_count,
            odps_skipped=skipped_count,
            conflicts_detected=conflicts,
            version=latest.version_number if latest else 1,
        ))

    if not body.dry_run:
        await db.commit()

    return StandardResponse(
        data={
            "template_id": template_id,
            "dry_run": body.dry_run,
            "results": [r.model_dump() for r in results],
            "total_applied": total_applied,
            "total_conflicts": total_conflicts,
        },
        message=f"Template {template_id} applied. {total_applied} ODPs updated."
        if not body.dry_run else f"Dry run: {total_applied} ODPs would be updated.",
    )


# ============================================================================
# Versions
# ============================================================================

@router.get("/versions", response_model=StandardResponse)
async def list_versions(
    baseline_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List policy version history."""
    query = select(PolicyVersion)
    if baseline_id:
        query = query.where(PolicyVersion.baseline_id == baseline_id)

    # Count total
    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(PolicyVersion.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    versions = result.scalars().all()

    # Get current version summary
    current_version = 1
    if versions:
        current_version = max(v.version_number for v in versions)

    return StandardResponse(
        data={
            "items": [
                {
                    "id": v.id,
                    "version_number": v.version_number,
                    "baseline_id": v.baseline_id,
                    "changed_by": v.changed_by,
                    "change_type": v.change_type,
                    "from_value": v.from_value,
                    "to_value": v.to_value,
                    "change_reason": v.change_reason,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ],
            "summary": {
                "total_versions": total,
                "current_version": current_version,
            },
            "page": page,
            "page_size": page_size,
        },
        message=f"Found {len(versions)} versions",
    )


@router.post("/versions/{version_id}/rollback")
async def rollback_version(
    version_id: str,
    body: RollbackBody = RollbackBody(),
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

    if not body.dry_run:
        # Find the ODP and revert it
        if version.odp_id:
            odp_result = await db.execute(
                select(OrganizationODP).where(OrganizationODP.id == version.odp_id)
            )
            odp = odp_result.scalar_one_or_none()

            if odp and version.from_value is not None:
                previous_value = odp.odp_value
                odp.odp_value = version.from_value

                # Create rollback version record
                new_version = PolicyVersion(
                    version_number=await _get_next_version(db),
                    baseline_id=version.baseline_id,
                    odp_id=version.odp_id,
                    changed_by="system",
                    change_type="rollback",
                    from_value=previous_value,
                    to_value=version.from_value,
                    change_reason=body.description or f"Rollback to version {version.version_number}",
                )
                db.add(new_version)
                await db.commit()

    return StandardResponse(
        data={
            "rolled_back_from": version.version_number,
            "rolled_back_to": version.version_number,
            "new_version": version.version_number + 1 if not body.dry_run else version.version_number,
            "description": body.description,
            "dry_run": body.dry_run,
            "changes": [
                {
                    "odp_id": version.odp_id,
                    "from": version.to_value,
                    "to": version.from_value,
                }
            ],
        },
        message=f"Rolled back to version {version.version_number}",
    )


# ============================================================================
# Conflicts
# ============================================================================

@router.get("/conflicts", response_model=StandardResponse)
async def list_conflicts(
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """List ODP-NIST conflicts."""
    query = select(ODPConflict)

    if status:
        query = query.where(ODPConflict.status == status)
    if severity:
        query = query.where(ODPConflict.severity == severity)
    if incident_type:
        # Find baseline for incident type
        baseline_result = await db.execute(
            select(NistBaseline).where(NistBaseline.incident_type == incident_type)
        )
        baseline = baseline_result.scalar_one_or_none()
        if baseline:
            query = query.where(ODPConflict.baseline_id == baseline.id)

    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.order_by(ODPConflict.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    conflicts = result.scalars().all()

    return StandardResponse(
        data={
            "items": [
                {
                    "id": c.id,
                    "conflict_id": c.conflict_id,
                    "conflict_type": c.conflict_type,
                    "severity": c.severity,
                    "message": c.message,
                    "expected_value": c.expected_value,
                    "actual_value": c.actual_value,
                    "status": c.status,
                    "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                    "resolved_by": c.resolved_by,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in conflicts
            ],
            "summary": {
                "total": total,
                "open": sum(1 for c in conflicts if c.status == "open"),
                "resolved": sum(1 for c in conflicts if c.status == "resolved"),
            },
            "page": page,
            "page_size": page_size,
        },
        message=f"Found {len(conflicts)} conflicts",
    )


@router.post("/conflicts/{conflict_id}/resolve")
async def resolve_conflict(
    conflict_id: str,
    body: ConflictResolveBody = ConflictResolveBody(),
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

    previous_value = conflict.actual_value
    new_value = previous_value

    # Apply the resolution
    if body.resolution == "accept_suggestion" and conflict.expected_value:
        new_value = conflict.expected_value
        # Update the ODP if found
        if conflict.odp_id:
            odp_result = await db.execute(
                select(OrganizationODP).where(OrganizationODP.id == conflict.odp_id)
            )
            odp = odp_result.scalar_one_or_none()
            if odp:
                odp.odp_value = new_value
    elif body.resolution == "custom_value" and body.custom_value is not None:
        new_value = body.custom_value
        if conflict.odp_id:
            odp_result = await db.execute(
                select(OrganizationODP).where(OrganizationODP.id == conflict.odp_id)
            )
            odp = odp_result.scalar_one_or_none()
            if odp:
                odp.odp_value = new_value

    conflict.status = "resolved"
    conflict.resolved_by = "system"
    conflict.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    return StandardResponse(
        data={
            "conflict_id": conflict_id,
            "status": "resolved",
            "resolution": body.resolution,
            "previous_value": previous_value,
            "new_value": new_value,
            "note": body.note,
            "resolved_by": "system",
        },
        message=f"Conflict {conflict_id} resolved",
    )


# ============================================================================
# Helpers
# ============================================================================

def _build_effective_policy(baseline: NistBaseline, odps: List[OrganizationODP]) -> Dict[str, Any]:
    """Build effective policy by overlaying ODPs onto baseline."""
    effective: Dict[str, Any] = {
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

    return effective


async def _validate_baseline(db: AsyncSession, baseline: NistBaseline) -> int:
    """Run conflict detection for a single baseline. Returns conflict count."""
    odp_result = await db.execute(
        select(OrganizationODP).where(OrganizationODP.baseline_id == baseline.id)
    )
    odps = {o.odp_key: o.odp_value for o in odp_result.scalars().all()}

    conflicts_created = 0

    # Missing required
    required = {
        "severity_threshold", "auto_contain_enabled", "escalation_contacts",
        "response_time_sla", "forensic_level", "notify_targets",
        "compliance_report", "record_threshold",
    }
    for key in required - set(odps.keys()):
        conflict = ODPConflict(
            conflict_id=f"CONF-{baseline.incident_type}-MISSING-{key}",
            baseline_id=baseline.id,
            odp_id="",
            conflict_type="MISSING_REQUIRED",
            severity="BLOCKED",
            message=f"Missing required ODP: {key}",
            expected_value="defined",
            actual_value="undefined",
            status="open",
        )
        db.add(conflict)
        conflicts_created += 1

    # Severity downgrade
    if "severity_threshold" in odps:
        st = odps["severity_threshold"].lower()
        base_sev = baseline.severity.lower()
        severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        if severity_rank.get(st, 0) < severity_rank.get(base_sev, 0):
            conflict = ODPConflict(
                conflict_id=f"CONF-{baseline.incident_type}-SEVERITY",
                baseline_id=baseline.id,
                odp_id="",
                conflict_type="SEVERITY_DOWNGRADE",
                severity="BLOCKED",
                message=f"Severity threshold ({st}) is lower than NIST baseline ({base_sev})",
                expected_value=base_sev,
                actual_value=st,
                status="open",
            )
            db.add(conflict)
            conflicts_created += 1

    # Auto-contain disabled
    if odps.get("auto_contain_enabled", "").lower() == "false" and baseline.auto_contain_enabled:
        conflict = ODPConflict(
            conflict_id=f"CONF-{baseline.incident_type}-AUTOCONTAIN",
            baseline_id=baseline.id,
            odp_id="",
            conflict_type="VALUE_MISMATCH",
            severity="WARNING",
            message="Auto-contain is disabled but NIST baseline recommends enabled",
            expected_value="true",
            actual_value="false",
            status="open",
        )
        db.add(conflict)
        conflicts_created += 1

    # Empty escalation contacts
    if "escalation_contacts" in odps:
        contacts = odps["escalation_contacts"]
        if not contacts or contacts in ("[]", "", "null"):
            conflict = ODPConflict(
                conflict_id=f"CONF-{baseline.incident_type}-ESCALATION",
                baseline_id=baseline.id,
                odp_id="",
                conflict_type="MISSING_REQUIRED",
                severity="BLOCKED",
                message="No escalation contacts defined",
                expected_value="at least one contact",
                actual_value="none",
                status="open",
            )
            db.add(conflict)
            conflicts_created += 1

    await db.flush()
    return conflicts_created


async def _get_next_version(db: AsyncSession) -> int:
    """Get the next version number."""
    from sqlalchemy import func
    result = await db.execute(select(func.max(PolicyVersion.version_number)))
    latest = result.scalar()
    return (latest or 0) + 1
