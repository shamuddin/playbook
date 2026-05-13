"""Forensics Service — evidence package generation and timeline reconstruction.

Assembles tamper-evident evidence packages with SHA-256 manifest
and HMAC-SHA256 digital signature.
"""

import hashlib
import hmac
import io
import json
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import (
    AuditLog,
    BypassAttempt,
    EvidencePackage,
    Incident,
    IncidentMetadata,
    JudgeDecision,
    ResponseRecord,
    ResponseStep,
    TimelineEvent,
)

settings = get_settings()


def _generate_package_id(incident_id: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")[:-3]
    return f"EVIDENCE-{incident_id}-{ts}"


def _sha256_dict(data: Dict[str, Any]) -> str:
    """Compute SHA-256 hash of a JSON-serializable dict."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sign_manifest(manifest: Dict[str, Any], secret: str) -> str:
    """Create HMAC-SHA256 signature of the manifest."""
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class ForensicsService:
    """Forensics evidence package builder.

    Usage:
        service = ForensicsService()
        package = await service.build_package(db, incident_id)
    """

    async def _fetch_incident_data(
        self, db: AsyncSession, incident_id: str
    ) -> Dict[str, Any]:
        """Fetch all incident-related data from the database."""
        # Get incident
        result = await db.execute(
            select(Incident).where(Incident.incident_id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident is None:
            raise ValueError(f"Incident {incident_id} not found")

        # Get metadata
        meta_result = await db.execute(
            select(IncidentMetadata).where(IncidentMetadata.incident_id == incident.id)
        )
        metadata = meta_result.scalar_one_or_none()

        # Get timeline events
        timeline_result = await db.execute(
            select(TimelineEvent)
            .where(TimelineEvent.incident_id == incident.id)
            .order_by(TimelineEvent.timestamp.asc())
        )
        timeline_events = timeline_result.scalars().all()

        # Get judge decisions
        judge_result = await db.execute(
            select(JudgeDecision).where(JudgeDecision.incident_id == incident.id)
        )
        judge_decisions = judge_result.scalars().all()

        # Get response record
        resp_result = await db.execute(
            select(ResponseRecord).where(ResponseRecord.incident_id == incident.id)
        )
        response_record = resp_result.scalar_one_or_none()

        # Get response steps if response exists
        response_steps = []
        if response_record:
            steps_result = await db.execute(
                select(ResponseStep).where(
                    ResponseStep.response_id == response_record.id
                ).order_by(ResponseStep.step_order if hasattr(ResponseStep, "step_order") else ResponseStep.id)
            )
            response_steps = steps_result.scalars().all()

        # Get bypass attempts
        bypass_result = await db.execute(
            select(BypassAttempt).where(BypassAttempt.incident_id == incident.id)
        )
        bypass_attempts = bypass_result.scalars().all()

        # Get audit logs for this incident
        audit_result = await db.execute(
            select(AuditLog).where(
                (AuditLog.target_type == "incident")
                & (AuditLog.target_id == incident.id)
            ).order_by(AuditLog.created_at.asc())
        )
        audit_logs = audit_result.scalars().all()

        return {
            "incident": incident,
            "metadata": metadata,
            "timeline_events": timeline_events,
            "judge_decisions": judge_decisions,
            "response_record": response_record,
            "response_steps": response_steps,
            "bypass_attempts": bypass_attempts,
            "audit_logs": audit_logs,
        }

    def _build_manifest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build SHA-256 manifest from all evidence artifacts."""
        manifest = {
            "package_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files": {},
        }

        incident = data["incident"]
        manifest["files"]["incident.json"] = _sha256_dict({
            "incident_id": incident.incident_id,
            "event_id": incident.event_id,
            "status": incident.status,
            "severity": incident.severity,
            "category": incident.category,
            "incident_type": incident.incident_type,
            "confidence": incident.confidence,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
        })

        if data["metadata"]:
            manifest["files"]["metadata.json"] = _sha256_dict(
                data["metadata"].full_metadata_json or {}
            )

        timeline_data = [
            {
                "timestamp": evt.timestamp.isoformat() if evt.timestamp else None,
                "stage": evt.stage,
                "event_type": evt.event_type,
                "event_description": evt.event_description,
                "source_component": evt.source_component,
                "details": evt.details_json,
            }
            for evt in data["timeline_events"]
        ]
        manifest["files"]["timeline.json"] = _sha256_dict({"events": timeline_data})

        judge_data = [
            {
                "decision_id": d.decision_id,
                "verdict": d.verdict,
                "severity_score": d.severity_score,
                "confidence": d.confidence,
                "matched_rules": d.matched_rules,
                "bypass_patterns": d.bypass_patterns_detected,
                "rationale": d.rationale,
                "latency_ms": d.latency_ms,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in data["judge_decisions"]
        ]
        manifest["files"]["judge_decisions.json"] = _sha256_dict({"decisions": judge_data})

        if data["response_record"]:
            resp = data["response_record"]
            manifest["files"]["response.json"] = _sha256_dict({
                "response_id": resp.response_id,
                "playbook_id": resp.playbook_id,
                "status": resp.status,
                "steps_total": resp.steps_total,
                "steps_completed": resp.steps_completed,
                "steps_failed": resp.steps_failed,
                "started_at": resp.started_at.isoformat() if resp.started_at else None,
                "completed_at": resp.completed_at.isoformat() if resp.completed_at else None,
            })

            steps_data = [
                {
                    "step_id": s.step_id,
                    "step_name": s.step_name,
                    "action": s.action,
                    "status": s.status,
                    "returncode": s.cli_returncode,
                    "stdout": s.cli_stdout,
                    "stderr": s.cli_stderr,
                }
                for s in data["response_steps"]
            ]
            manifest["files"]["response_steps.json"] = _sha256_dict({"steps": steps_data})

        bypass_data = [
            {
                "pattern_id": b.pattern_id,
                "detection_confidence": b.detection_confidence,
                "payload_sample": b.payload_sample,
                "blocked_at": b.blocked_at.isoformat() if b.blocked_at else None,
            }
            for b in data["bypass_attempts"]
        ]
        if bypass_data:
            manifest["files"]["bypass_attempts.json"] = _sha256_dict({"attempts": bypass_data})

        audit_data = [
            {
                "action": a.action,
                "actor_type": a.actor_type,
                "actor_id": a.actor_id,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "details": a.details,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in data["audit_logs"]
        ]
        if audit_data:
            manifest["files"]["audit_log.json"] = _sha256_dict({"entries": audit_data})

        # Overall package hash
        manifest["package_hash"] = hashlib.sha256(
            json.dumps(manifest["files"], sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        return manifest

    def _build_package_data(self, data: Dict[str, Any], manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Build the full evidence package payload."""
        incident = data["incident"]

        package = {
            "package_id": manifest.get("package_id", "unknown"),
            "incident_id": incident.incident_id,
            "generated_at": manifest["generated_at"],
            "manifest": manifest,
            "artifacts": {},
        }

        # Incident artifact
        package["artifacts"]["incident"] = {
            "incident_id": incident.incident_id,
            "event_id": incident.event_id,
            "status": incident.status,
            "severity": incident.severity,
            "category": incident.category,
            "incident_type": incident.incident_type,
            "confidence": incident.confidence,
            "created_at": incident.created_at.isoformat() if incident.created_at else None,
            "updated_at": incident.updated_at.isoformat() if incident.updated_at else None,
        }

        # Metadata artifact
        if data["metadata"]:
            package["artifacts"]["metadata"] = data["metadata"].full_metadata_json or {}

        # Timeline artifact
        package["artifacts"]["timeline"] = [
            {
                "timestamp": evt.timestamp.isoformat() if evt.timestamp else None,
                "stage": evt.stage,
                "event_type": evt.event_type,
                "event_description": evt.event_description,
                "source_component": evt.source_component,
                "details": evt.details_json,
            }
            for evt in data["timeline_events"]
        ]

        # Judge decisions artifact
        package["artifacts"]["judge"] = [
            {
                "decision_id": d.decision_id,
                "verdict": d.verdict,
                "severity_score": d.severity_score,
                "confidence": d.confidence,
                "matched_rules": d.matched_rules,
                "bypass_patterns": d.bypass_patterns_detected,
                "rationale": d.rationale,
                "latency_ms": d.latency_ms,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in data["judge_decisions"]
        ]

        # Response artifact
        if data["response_record"]:
            resp = data["response_record"]
            package["artifacts"]["response"] = {
                "response_id": resp.response_id,
                "playbook_id": resp.playbook_id,
                "status": resp.status,
                "steps_total": resp.steps_total,
                "steps_completed": resp.steps_completed,
                "steps_failed": resp.steps_failed,
                "started_at": resp.started_at.isoformat() if resp.started_at else None,
                "completed_at": resp.completed_at.isoformat() if resp.completed_at else None,
                "steps": [
                    {
                        "step_id": s.step_id,
                        "step_name": s.step_name,
                        "action": s.action,
                        "status": s.status,
                        "returncode": s.cli_returncode,
                        "stdout": s.cli_stdout,
                        "stderr": s.cli_stderr,
                        "error_message": s.error_message,
                    }
                    for s in data["response_steps"]
                ],
            }

        # Bypass attempts artifact
        if data["bypass_attempts"]:
            package["artifacts"]["bypass"] = [
                {
                    "pattern_id": b.pattern_id,
                    "detection_confidence": b.detection_confidence,
                    "payload_sample": b.payload_sample,
                    "blocked_at": b.blocked_at.isoformat() if b.blocked_at else None,
                }
                for b in data["bypass_attempts"]
            ]

        # Audit log artifact
        if data["audit_logs"]:
            package["artifacts"]["audit"] = [
                {
                    "action": a.action,
                    "actor_type": a.actor_type,
                    "actor_id": a.actor_id,
                    "target_type": a.target_type,
                    "target_id": a.target_id,
                    "details": a.details,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in data["audit_logs"]
            ]

        return package

    async def build_package(
        self, db: AsyncSession, incident_id: str
    ) -> EvidencePackage:
        """Build and store an evidence package for an incident.

        Returns the created EvidencePackage record.
        """
        data = await self._fetch_incident_data(db, incident_id)
        manifest = self._build_manifest(data)
        package_data = self._build_package_data(data, manifest)

        package_id = _generate_package_id(incident_id)
        manifest["package_id"] = package_id
        package_data["package_id"] = package_id

        # Compute integrity hash and signature
        package_hash = manifest["package_hash"]
        signature = _sign_manifest(manifest, settings.secret_key)

        # Create evidence package record
        evidence = EvidencePackage(
            package_id=package_id,
            incident_id=data["incident"].id,
            response_id=data["response_record"].id if data["response_record"] else None,
            package_type="full",
            package_data=package_data,
            integrity_hash=package_hash,
            is_verified=True,
            retention_until=datetime.now(timezone.utc) + timedelta(days=2555),
        )
        db.add(evidence)
        await db.flush()

        # Add signature to package data
        package_data["signature"] = {
            "algorithm": "HMAC-SHA256",
            "signature": signature,
            "key_hint": settings.secret_key[:8] + "..." if len(settings.secret_key) > 8 else "",
        }
        evidence.package_data = package_data
        await db.flush()

        return evidence

    def export_zip(self, evidence: EvidencePackage) -> bytes:
        """Export an evidence package as a ZIP archive.

        Returns the raw ZIP bytes.
        """
        package_data = evidence.package_data or {}
        artifacts = package_data.get("artifacts", {})
        manifest = package_data.get("manifest", {})
        signature = package_data.get("signature", {})

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Manifest
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, default=str))

            # Signature
            zf.writestr("signature.json", json.dumps(signature, indent=2, default=str))

            # Artifacts
            for name, content in artifacts.items():
                filename = f"artifacts/{name}.json"
                zf.writestr(filename, json.dumps(content, indent=2, default=str))

        buf.seek(0)
        return buf.read()
