"""Conflict Detector — detect ODP-NIST baseline conflicts.

Implements 7 conflict detection rules:
1. MISSING_REQUIRED      — required ODP key is missing
2. SEVERITY_DOWNGRADE    — severity threshold below NIST baseline
3. VALUE_MISMATCH        — auto-contain disabled when baseline enables it
4. THRESHOLD_VIOLATION   — SLA exceeds 2x NIST recommendation
5. FORENSIC_LEVEL_REDUCTION — forensic level reduced below baseline
6. COMPLIANCE_REPORT_DISABLED — compliance reporting disabled when required
7. MISSING_REQUIRED      — empty escalation contacts for critical/high
"""

from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NistBaseline, ODPConflict, OrganizationODP
from app.schemas import ConflictDetail, ValidationResult


class ConflictDetector:
    """Detect and manage conflicts between ODPs and NIST baselines."""

    # 8 required ODP keys per incident type
    REQUIRED_KEYS = {
        "severity_threshold",
        "auto_contain_enabled",
        "escalation_contacts",
        "response_time_sla",
        "forensic_level",
        "notify_targets",
        "compliance_report",
        "record_threshold",
    }

    SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    FORENSIC_RANK = {"full": 3, "standard": 2, "none": 1, "deep": 4}

    @staticmethod
    def detect(
        baseline: NistBaseline,
        odps: Dict[str, str],
        incident_type: str,
    ) -> List[ConflictDetail]:
        """Detect all conflicts for a single baseline + ODP map.

        Args:
            baseline: The NIST baseline to compare against.
            odps: Dict of {odp_key: odp_value} for the incident type.
            incident_type: The incident type code (for messages).

        Returns:
            List of ConflictDetail objects.
        """
        conflicts: List[ConflictDetail] = []

        # Rule 1: Missing required ODPs
        for key in ConflictDetector.REQUIRED_KEYS - set(odps.keys()):
            conflicts.append(
                ConflictDetail(
                    type="MISSING_REQUIRED",
                    severity="BLOCKED",
                    message=f"Missing required ODP: {key} for {incident_type}",
                    suggestion=f"Set {key} to baseline default",
                )
            )

        # Rule 2: Severity downgrade
        if "severity_threshold" in odps:
            st = odps["severity_threshold"].lower()
            base_sev = baseline.severity.lower()
            if ConflictDetector.SEVERITY_RANK.get(st, 0) < ConflictDetector.SEVERITY_RANK.get(base_sev, 0):
                conflicts.append(
                    ConflictDetail(
                        type="SEVERITY_DOWNGRADE",
                        severity="BLOCKED",
                        message=f"Severity threshold ({st}) is lower than NIST baseline ({base_sev})",
                        nist_value=base_sev,
                        odp_value=st,
                        suggestion="Match or exceed baseline severity",
                    )
                )

        # Rule 3: Auto-contain disabled when baseline enables it
        if odps.get("auto_contain_enabled", "").lower() == "false" and baseline.auto_contain_enabled:
            conflicts.append(
                ConflictDetail(
                    type="VALUE_MISMATCH",
                    severity="WARNING",
                    message="Auto-contain is disabled but NIST baseline recommends enabled",
                    nist_value="true",
                    odp_value="false",
                    suggestion="Enable auto-contain for compliance",
                )
            )

        # Rule 4: SLA exceeds 2x NIST recommendation
        if "response_time_sla" in odps:
            try:
                sla = int(odps["response_time_sla"])
                if sla > baseline.response_time_sla_seconds * 2:
                    conflicts.append(
                        ConflictDetail(
                            type="THRESHOLD_VIOLATION",
                            severity="WARNING",
                            message=f"Response SLA ({sla}s) exceeds 2x NIST recommendation ({baseline.response_time_sla_seconds}s)",
                            nist_value=str(baseline.response_time_sla_seconds),
                            odp_value=str(sla),
                            suggestion="Reduce SLA to within 2x of baseline",
                        )
                    )
            except (ValueError, TypeError):
                pass

        # Rule 5: Forensic level reduction
        if "forensic_level" in odps:
            fl = odps["forensic_level"].lower()
            base_fl = baseline.forensic_level.lower()
            if fl == "none" and base_fl in ("full", "standard", "deep"):
                conflicts.append(
                    ConflictDetail(
                        type="FORENSIC_LEVEL_REDUCTION",
                        severity="WARNING",
                        message=f"Forensic level reduced to '{fl}' from baseline '{base_fl}'",
                        nist_value=base_fl,
                        odp_value=fl,
                        suggestion="Maintain at least STANDARD forensic level",
                    )
                )

        # Rule 6: Compliance report disabled when baseline requires it
        if odps.get("compliance_report", "").lower() == "false" and baseline.compliance_report:
            conflicts.append(
                ConflictDetail(
                    type="COMPLIANCE_REPORT_DISABLED",
                    severity="WARNING",
                    message="Compliance report generation is disabled but baseline requires it",
                    nist_value="true",
                    odp_value="false",
                    suggestion="Enable compliance report generation",
                )
            )

        # Rule 7: Empty escalation contacts
        if "escalation_contacts" in odps:
            contacts = odps["escalation_contacts"]
            if not contacts or contacts in ("[]", "", "null", "None"):
                conflicts.append(
                    ConflictDetail(
                        type="MISSING_REQUIRED",
                        severity="BLOCKED",
                        message="No escalation contacts defined",
                        suggestion="Add at least one escalation contact",
                    )
                )

        return conflicts

    @staticmethod
    async def detect_for_baseline(
        db: AsyncSession,
        baseline: NistBaseline,
    ) -> List[ConflictDetail]:
        """Load ODPs from DB and detect conflicts for a single baseline."""
        odp_result = await db.execute(
            select(OrganizationODP).where(
                OrganizationODP.baseline_id == baseline.id,
                OrganizationODP.is_active == True,
            )
        )
        odps = {o.odp_key: o.odp_value for o in odp_result.scalars().all()}
        return ConflictDetector.detect(baseline, odps, baseline.incident_type)

    @staticmethod
    async def detect_all(
        db: AsyncSession,
    ) -> List[ValidationResult]:
        """Detect conflicts across all active baselines."""
        baseline_result = await db.execute(
            select(NistBaseline).where(NistBaseline.is_active == True)
        )
        baselines = baseline_result.scalars().all()

        results: List[ValidationResult] = []
        for baseline in baselines:
            conflicts = await ConflictDetector.detect_for_baseline(db, baseline)
            results.append(
                ValidationResult(
                    incident_type=baseline.incident_type,
                    valid=len(conflicts) == 0,
                    conflicts=conflicts,
                )
            )
        return results

    @staticmethod
    async def persist_conflicts(
        db: AsyncSession,
        baseline: NistBaseline,
        conflicts: List[ConflictDetail],
    ) -> int:
        """Persist detected conflicts to the database.

        Returns the number of conflicts created.
        """
        import uuid

        created = 0
        for i, cd in enumerate(conflicts):
            conflict = ODPConflict(
                conflict_id=f"CONF-{baseline.incident_type}-{cd.type}-{i}-{uuid.uuid4().hex[:8]}",
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
            created += 1

        await db.flush()
        return created

    @staticmethod
    async def resolve_conflict(
        db: AsyncSession,
        conflict: ODPConflict,
        resolution: str,
        custom_value: Optional[str] = None,
    ) -> bool:
        """Resolve a conflict by applying the suggested fix or a custom value.

        Args:
            resolution: "accept_suggestion" or "custom_value"
            custom_value: Required when resolution is "custom_value"

        Returns:
            True if an ODP was updated, False otherwise.
        """
        new_value = conflict.actual_value
        updated = False

        if resolution == "accept_suggestion" and conflict.expected_value:
            new_value = conflict.expected_value
        elif resolution == "custom_value" and custom_value is not None:
            new_value = custom_value
        else:
            # Just mark resolved without changing value
            conflict.status = "resolved"
            conflict.resolved_by = "system"
            from app.models import utc_now
            conflict.resolved_at = utc_now()
            return False

        # Find and update the ODP if possible
        if conflict.odp_id:
            odp_result = await db.execute(
                select(OrganizationODP).where(OrganizationODP.id == conflict.odp_id)
            )
            odp = odp_result.scalar_one_or_none()
            if odp:
                odp.odp_value = new_value
                updated = True

        conflict.status = "resolved"
        conflict.resolved_by = "system"
        from datetime import datetime, timezone
        from app.models import utc_now
        conflict.resolved_at = utc_now()
        return updated
