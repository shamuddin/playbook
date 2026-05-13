"""Decision Renderer — renders final verdicts and logs to audit trail.

Immutable decision logging. Fails-closed (ESCALATE on any exception).
"""

import time
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import JudgeVerdict
from app.models import JudgeDecision, TimelineEvent
from app.judge.engine import JudgeResult


class DecisionRenderer:
    """Renders final verdicts and creates immutable audit records.

    Usage:
        renderer = DecisionRenderer()
        result = await renderer.render(db, incident_id, judge_result)
    """

    @staticmethod
    def _generate_decision_id() -> str:
        return f"JDG-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    async def render(
        db: AsyncSession,
        incident_id: Optional[str],
        judge_result: JudgeResult,
        agent_id: Optional[str] = None,
    ) -> JudgeResult:
        """Render a decision, log it to the database, and create a timeline event.

        Args:
            db: Async database session
            incident_id: The incident ID (can be None for pre-screen evaluations)
            judge_result: The result from JudgeEngine.evaluate()
            agent_id: Optional agent ID

        Returns:
            The same JudgeResult (for chaining)

        Raises:
            Exception: Re-raised after logging ESCALATE fallback.
        """
        try:
            # Create immutable judge decision record
            decision = JudgeDecision(
                decision_id=DecisionRenderer._generate_decision_id(),
                incident_id=incident_id or "pre-screen",
                agent_id=agent_id,
                verdict=judge_result.verdict,
                severity_score=judge_result.severity_score,
                confidence=judge_result.confidence,
                matched_rules=judge_result.matched_rules,
                bypass_patterns_detected=judge_result.bypass_patterns_detected,
                rationale=judge_result.rationale,
                latency_ms=judge_result.latency_ms,
                resolved_policy_id=judge_result.resolved_policy_id,
                odp_overrides=judge_result.odp_overrides,
            )
            db.add(decision)
            await db.flush()

            # Create timeline event if we have an incident_id
            if incident_id:
                timeline = TimelineEvent(
                    incident_id=incident_id,
                    stage="judge",
                    event_type="verdict_rendered",
                    event_description=(
                        f"Judge rendered {judge_result.verdict} "
                        f"(severity={judge_result.severity_score}, "
                        f"latency={judge_result.latency_ms}ms)"
                    ),
                    source_component="judge_layer",
                    details_json={
                        "decision_id": decision.decision_id,
                        "verdict": judge_result.verdict,
                        "severity_score": judge_result.severity_score,
                        "matched_rules": judge_result.matched_rules,
                        "bypass_patterns": judge_result.bypass_patterns_detected,
                        "latency_ms": judge_result.latency_ms,
                        "regulatory_tags": judge_result.regulatory_tags,
                    },
                )
                db.add(timeline)
                await db.flush()

            return judge_result

        except Exception as exc:
            # Fail-closed: on any exception, escalate
            # Still try to log the escalation
            try:
                fallback_decision = JudgeDecision(
                    decision_id=DecisionRenderer._generate_decision_id(),
                    incident_id=incident_id or "pre-screen",
                    agent_id=agent_id,
                    verdict=JudgeVerdict.ESCALATE,
                    severity_score=10,
                    confidence=1.0,
                    matched_rules=["fail_closed"],
                    bypass_patterns_detected=[],
                    rationale=f"Exception during rendering: {exc}",
                    latency_ms=0.0,
                )
                db.add(fallback_decision)
                await db.flush()
            except Exception:
                pass  # If even logging fails, just raise

            # Return escalated result instead of crashing
            return JudgeResult(
                verdict=JudgeVerdict.ESCALATE,
                severity_score=10,
                confidence=1.0,
                matched_rules=["fail_closed"],
                rationale=f"Exception during decision rendering: {exc}",
                latency_ms=0.0,
            )
