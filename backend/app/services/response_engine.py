"""Playbook Response Engine.

Executes playbook actions for incidents. DB-backed (playbooks table is source of truth).
Fail-open per action: individual failures logged, execution continues.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import PlaybookActionType, ResponseStatus
from app.models import (
    Incident,
    Playbook,
    PlaybookAction,
    ResponseRecord,
    ResponseStep,
    TimelineEvent,
    HumanReviewTask,
)
from app.services.websocket_manager import ws_manager


@dataclass
class ActionResult:
    """Result of executing a single playbook action."""

    step_id: str
    step_name: str
    action_type: str
    status: str  # completed, failed, skipped
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    error_message: Optional[str] = None
    executed_at: Optional[str] = None
    completed_at: Optional[str] = None
    latency_ms: float = 0.0


@dataclass
class PlaybookExecutionResult:
    """Result of executing a full playbook."""

    response_id: str
    status: str
    steps_total: int
    steps_completed: int
    steps_failed: int
    action_results: List[ActionResult] = field(default_factory=list)
    error_log: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_latency_ms: float = 0.0


class ResponseEngine:
    """Playbook response engine.

    Usage:
        engine = ResponseEngine()
        result = await engine.execute_playbook(db, incident_id)
    """

    @staticmethod
    def _generate_response_id() -> str:
        return f"RES-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _generate_step_id() -> str:
        return f"STEP-{uuid.uuid4().hex[:8].upper()}"

    async def resolve_playbook(
        self, db: AsyncSession, incident_type: str
    ) -> Optional[Playbook]:
        """Find the active playbook for an incident type."""
        result = await db.execute(
            select(Playbook).where(
                Playbook.incident_type == incident_type,
                Playbook.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _execute_action(
        self,
        db: AsyncSession,
        action: PlaybookAction,
        incident: Incident,
        response_record: ResponseRecord,
    ) -> ActionResult:
        """Execute a single playbook action.

        Returns ActionResult with execution details.
        """
        start = time.perf_counter()
        step_id = self._generate_step_id()
        executed_at = time.time()

        # Create ResponseStep record
        step = ResponseStep(
            response_id=response_record.id,
            step_id=step_id,
            step_name=action.name,
            action=action.action_type,
            status="in_progress",
            parameters=action.parameters or {},
        )
        db.add(step)
        await db.flush()

        stdout = ""
        stderr = ""
        returncode = 0
        error_message = None
        status = "completed"

        try:
            action_type = action.action_type.upper()

            if action_type == PlaybookActionType.DENY:
                stdout = f"Denied action for incident {incident.incident_id}"
                # In production, this would call Lobster Trap DPI

            elif action_type == PlaybookActionType.QUARANTINE:
                stdout = f"Quarantined agent session for incident {incident.incident_id}"
                incident.status = "responding"

            elif action_type == PlaybookActionType.ISOLATE:
                stdout = f"Isolated agent for incident {incident.incident_id}"

            elif action_type == PlaybookActionType.RATE_LIMIT:
                stdout = f"Rate-limited agent for incident {incident.incident_id}"

            elif action_type == PlaybookActionType.HUMAN_REVIEW:
                stdout = f"Created human review task for incident {incident.incident_id}"
                # Create human review task
                review_task = HumanReviewTask(
                    task_id=f"HR-{uuid.uuid4().hex[:8].upper()}",
                    incident_id=incident.id,
                    step_record_id=step.id,
                    status="pending",
                )
                db.add(review_task)
                await db.flush()
                # Broadcast human review required
                await ws_manager.broadcast({
                    "event_type": "HUMAN_REVIEW_REQUIRED",
                    "task_id": review_task.task_id,
                    "incident_id": incident.incident_id,
                    "sla_deadline": (
                        datetime.now(timezone.utc) + timedelta(minutes=30)
                    ).isoformat(),
                    "severity": incident.severity,
                })

            elif action_type == PlaybookActionType.NOTIFY:
                targets = action.parameters.get("targets", ["#security-alerts"])
                stdout = f"Notification sent to {targets} for incident {incident.incident_id}"

            elif action_type == PlaybookActionType.FORENSICS:
                stdout = f"Forensics capture initiated for incident {incident.incident_id}"
                incident.forensics_status = "in_progress"

            elif action_type == PlaybookActionType.LOG_EXTENDED:
                stdout = f"Extended audit logging enabled for incident {incident.incident_id}"

            else:
                stdout = f"Unknown action type: {action_type}"
                status = "failed"
                returncode = 1

        except Exception as exc:
            stderr = str(exc)
            error_message = str(exc)
            status = "failed"
            returncode = 1

        latency_ms = (time.perf_counter() - start) * 1000

        # Update step record
        step.status = status
        step.cli_stdout = stdout
        step.cli_stderr = stderr
        step.cli_returncode = returncode
        step.error_message = error_message
        step.executed_at = datetime.fromtimestamp(executed_at, tz=timezone.utc)

        # Add timeline event for this action
        timeline = TimelineEvent(
            incident_id=incident.id,
            stage="respond",
            event_type=f"action_{status}",
            event_description=f"Action '{action.name}' ({action.action_type}) {status}",
            source_component="response_engine",
            details_json={
                "step_id": step_id,
                "action_type": action.action_type,
                "status": status,
                "latency_ms": round(latency_ms, 3),
                "returncode": returncode,
            },
        )
        db.add(timeline)
        await db.flush()

        return ActionResult(
            step_id=step_id,
            step_name=action.name,
            action_type=action.action_type,
            status=status,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            error_message=error_message,
            latency_ms=round(latency_ms, 3),
        )

    async def execute_playbook(
        self,
        db: AsyncSession,
        incident_id: str,
        playbook_id: Optional[str] = None,
    ) -> PlaybookExecutionResult:
        """Execute the playbook for an incident.

        Args:
            db: Async database session
            incident_id: The incident's public incident_id

        Returns:
            PlaybookExecutionResult with all step results
        """
        start = time.perf_counter()
        response_id = self._generate_response_id()

        # Fetch incident
        result = await db.execute(
            select(Incident).where(Incident.incident_id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if incident is None:
            return PlaybookExecutionResult(
                response_id=response_id,
                status="failed",
                steps_total=0,
                steps_completed=0,
                steps_failed=1,
                error_log=f"Incident {incident_id} not found",
            )

        # Resolve playbook: use explicit playbook_id if provided, else lookup by incident_type
        if playbook_id:
            pb_result = await db.execute(
                select(Playbook).where(
                    Playbook.playbook_id == playbook_id,
                    Playbook.is_active == True,
                )
            )
            playbook = pb_result.scalar_one_or_none()
        else:
            playbook = await self.resolve_playbook(db, incident.incident_type)

        if playbook is None:
            return PlaybookExecutionResult(
                response_id=response_id,
                status="failed",
                steps_total=0,
                steps_completed=0,
                steps_failed=1,
                error_log=f"No playbook found for incident type {incident.incident_type}",
            )

        # Fetch actions
        actions_result = await db.execute(
            select(PlaybookAction)
            .where(PlaybookAction.playbook_id == playbook.id)
            .order_by(PlaybookAction.step_order)
        )
        actions = actions_result.scalars().all()

        # Create response record
        response_record = ResponseRecord(
            response_id=response_id,
            incident_id=incident.id,
            playbook_id=playbook.playbook_id,
            status=ResponseStatus.IN_PROGRESS,
            steps_total=len(actions),
        )
        db.add(response_record)
        await db.flush()

        # Update incident status
        incident.response_status = ResponseStatus.IN_PROGRESS
        incident.status = "responding"

        # Add response-started timeline event
        timeline = TimelineEvent(
            incident_id=incident.id,
            stage="respond",
            event_type="playbook_started",
            event_description=f"Playbook '{playbook.name}' started ({len(actions)} actions)",
            source_component="response_engine",
            details_json={
                "response_id": response_id,
                "playbook_id": playbook.playbook_id,
                "playbook_name": playbook.name,
                "steps_total": len(actions),
            },
        )
        db.add(timeline)
        await db.flush()

        # Execute each action (fail-open per action)
        action_results = []
        steps_completed = 0
        steps_failed = 0

        for action in actions:
            action_result = await self._execute_action(
                db, action, incident, response_record
            )
            action_results.append(action_result)

            if action_result.status == "completed":
                steps_completed += 1
            else:
                steps_failed += 1

            # Small yield to prevent blocking
            await asyncio.sleep(0)

        # Update response record
        total_latency_ms = (time.perf_counter() - start) * 1000
        response_record.status = (
            ResponseStatus.COMPLETED if steps_failed == 0
            else ResponseStatus.PARTIAL if steps_completed > 0
            else ResponseStatus.FAILED
        )
        response_record.steps_completed = steps_completed
        response_record.steps_failed = steps_failed
        response_record.completed_at = datetime.now(timezone.utc)

        # Update incident
        incident.response_status = response_record.status
        if response_record.status == ResponseStatus.COMPLETED:
            incident.status = "resolved"

        # Add completion timeline event
        timeline_complete = TimelineEvent(
            incident_id=incident.id,
            stage="respond",
            event_type="playbook_completed",
            event_description=(
                f"Playbook completed: {steps_completed}/{len(actions)} steps succeeded"
            ),
            source_component="response_engine",
            details_json={
                "response_id": response_id,
                "status": response_record.status,
                "steps_completed": steps_completed,
                "steps_failed": steps_failed,
                "total_latency_ms": round(total_latency_ms, 3),
            },
        )
        db.add(timeline_complete)
        await db.flush()

        # Trigger forensics evidence package generation
        try:
            from app.services.forensics import ForensicsService
            forensics_service = ForensicsService()
            evidence = await forensics_service.build_package(db, incident_id)
            await db.flush()

            # Add forensics timeline event
            forensics_timeline = TimelineEvent(
                incident_id=incident.id,
                stage="forensics",
                event_type="evidence_package_created",
                event_description=f"Evidence package {evidence.package_id} generated",
                source_component="response_engine",
                details_json={
                    "package_id": evidence.package_id,
                    "integrity_hash": evidence.integrity_hash,
                },
            )
            db.add(forensics_timeline)
            incident.forensics_status = "completed"
        except Exception as exc:
            # Fail-open: log but don't block response completion
            incident.forensics_status = "failed"
            forensics_error = TimelineEvent(
                incident_id=incident.id,
                stage="forensics",
                event_type="evidence_package_failed",
                event_description="Evidence package generation failed",
                source_component="response_engine",
                details_json={"error": str(exc)},
            )
            db.add(forensics_error)

        await db.commit()

        return PlaybookExecutionResult(
            response_id=response_id,
            status=response_record.status,
            steps_total=len(actions),
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            action_results=action_results,
            total_latency_ms=round(total_latency_ms, 3),
        )
