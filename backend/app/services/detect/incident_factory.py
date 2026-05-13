"""Incident Record Factory.

Creates Incident, IncidentMetadata, and TimelineEvent records from detection results.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.constants import INCIDENT_TYPES
from app.models import Incident, IncidentMetadata, Playbook, TimelineEvent
from app.services.detect.engine import DetectionResult
from app.services.detect.normalizer import PB_CES_Event


class IncidentFactory:
    """Factory for creating incident records from detection results."""

    @staticmethod
    def _generate_incident_id() -> str:
        """Generate a human-readable incident ID."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        short_uuid = uuid.uuid4().hex[:8].upper()
        return f"INC-{ts}-{short_uuid}"

    @staticmethod
    async def _find_playbook(
        db: AsyncSession, incident_type: str
    ) -> Playbook | None:
        """Find the playbook associated with an incident type."""
        result = await db.execute(
            select(Playbook).where(
                Playbook.incident_type == incident_type,
                Playbook.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def create_incident(
        cls,
        db: AsyncSession,
        event: PB_CES_Event,
        detection: DetectionResult,
    ) -> Incident:
        """Create a full incident record from a detection result.

        This creates:
        1. An Incident record
        2. An IncidentMetadata record with raw event data
        3. An initial TimelineEvent (stage="detect")

        Args:
            db: Async database session
            event: The normalized event that triggered detection
            detection: The detection result from the engine

        Returns:
            The created Incident model instance (already flushed to DB).
        """
        # Find associated playbook
        playbook = await cls._find_playbook(db, detection.incident_type or "AGT-GAP-012")
        playbook_id = playbook.playbook_id if playbook else None

        # Determine status
        status = "detected"

        # Create incident
        incident = Incident(
            incident_id=cls._generate_incident_id(),
            event_id=event.event_id,
            status=status,
            severity=detection.severity,
            category=detection.category,
            incident_type=detection.incident_type or "AGT-GAP-012",
            confidence=detection.confidence,
            local_rule_id=detection.matched_rules[0] if detection.matched_rules else None,
            deterministic_classification=detection.deterministic,
            playbook_id=playbook_id,
            response_status="pending",
            forensics_status="pending",
            bypass_detected=detection.category == "bypass",
        )
        db.add(incident)
        await db.flush()  # Get the ID assigned

        # Create metadata
        metadata = IncidentMetadata(
            incident_id=incident.id,
            intent_category=detection.category,
            risk_score=int(detection.anomaly_score),
            contains_injection_patterns=detection.incident_type == "AGT-INJ-006",
            contains_pii=detection.incident_type == "AGT-PRV-015",
            contains_credentials=detection.incident_type == "AGT-CRE-008",
            contains_exfiltration=detection.incident_type == "AGT-EXT-005",
            contains_system_commands=detection.incident_type in (
                "AGT-DEL-001",
                "AGT-PER-003",
                "AGT-EXT-005",
            ),
            full_metadata_json={
                "event": {
                    "event_id": event.event_id,
                    "source": event.source,
                    "event_type": event.event_type,
                    "agent_id": event.agent_id,
                    "session_id": event.session_id,
                    "timestamp": event.timestamp.isoformat(),
                },
                "detection": {
                    "incident_type": detection.incident_type,
                    "incident_type_name": detection.incident_type_name,
                    "severity": detection.severity,
                    "confidence": detection.confidence,
                    "anomaly_score": detection.anomaly_score,
                    "matched_rules": detection.matched_rules,
                    "matched_patterns": detection.matched_patterns,
                    "latency_ms": detection.latency_ms,
                    "deterministic": detection.deterministic,
                    "category": detection.category,
                },
                "event_raw": event.raw_data,
            },
        )
        db.add(metadata)

        # Create initial timeline event
        timeline_event = TimelineEvent(
            incident_id=incident.id,
            stage="detect",
            event_type="detection",
            event_description=(
                f"Detected {detection.incident_type_name} "
                f"({detection.incident_type}) with confidence {detection.confidence}"
            ),
            source_component="detection_engine",
            details_json={
                "latency_ms": detection.latency_ms,
                "matched_rules": detection.matched_rules,
                "anomaly_score": detection.anomaly_score,
            },
        )
        db.add(timeline_event)

        await db.flush()
        return incident

    @classmethod
    async def add_classification_timeline_event(
        cls,
        db: AsyncSession,
        incident: Incident,
        detection: DetectionResult,
        classified_by: str = "system",
    ) -> TimelineEvent:
        """Add a classification timeline event to an existing incident.

        Used when re-classifying an incident (e.g., via POST /classify).
        """
        timeline_event = TimelineEvent(
            incident_id=incident.id,
            stage="classify",
            event_type="classification",
            event_description=(
                f"Classified as {detection.incident_type_name} "
                f"({detection.incident_type}) with confidence {detection.confidence}"
            ),
            source_component="classification_engine",
            details_json={
                "classified_by": classified_by,
                "latency_ms": detection.latency_ms,
                "matched_rules": detection.matched_rules,
                "anomaly_score": detection.anomaly_score,
                "previous_severity": incident.severity,
                "new_severity": detection.severity,
            },
        )
        db.add(timeline_event)
        await db.flush()
        return timeline_event
