"""Judge Layer API router."""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.judge import BypassDetector, DecisionRenderer, JudgeEngine, JudgeInput
from app.models import BypassAttempt, BypassPattern, JudgeDecision
from app.schemas import (
    BypassAttemptResponse,
    BypassPatternResponse,
    JudgeEvaluateRequest,
    JudgeEvaluateResponse,
    JudgeStats,
    StandardResponse,
)

router = APIRouter(prefix="/judge", tags=["judge"])


@router.post("/evaluate", response_model=JudgeEvaluateResponse)
async def evaluate_action(
    request: JudgeEvaluateRequest,
    db: AsyncSession = Depends(get_db),
) -> JudgeEvaluateResponse:
    """Evaluate a proposed action through the deterministic Judge Layer.

    Pipeline: bypass detection → ODP resolution → severity scoring → verdict.
    Zero LLM calls. Fails-closed (ESCALATE on exception).
    """
    # Step 1: Bypass detection
    bypass_detector = BypassDetector()
    bypass_result = bypass_detector.evaluate(
        text=request.action,
        tool_calls=[request.action],
    )

    # Step 2: Build structured judge input
    metadata = request.metadata or {}
    judge_input = JudgeInput(
        action=request.action,
        agent_id=request.agent_id,
        session_id=request.session_id,
        incident_type=metadata.get("incident_type", "AGT-GAP-012"),
        severity=metadata.get("severity", "medium"),
        confidence=metadata.get("confidence", 0.5),
        auth_present=metadata.get("auth_present", False),
        dual_auth_present=metadata.get("dual_auth_present", False),
        is_repeat_offender=metadata.get("is_repeat_offender", False),
        contains_pii=metadata.get("contains_pii", False),
        contains_credentials=metadata.get("contains_credentials", False),
        contains_injection_patterns=metadata.get("contains_injection_patterns", False),
        contains_system_commands=metadata.get("contains_system_commands", False),
        contains_exfiltration=metadata.get("contains_exfiltration", False),
        is_business_hours=metadata.get("is_business_hours", True),
        source_ip_reputation=metadata.get("source_ip_reputation", "unknown"),
    )

    # Step 3: Judge evaluation
    engine = JudgeEngine()
    judge_result = await engine.evaluate(
        db, judge_input, bypass_patterns=bypass_result.patterns_detected
    )

    # Step 4: Render decision + audit log
    renderer = DecisionRenderer()
    incident_id = metadata.get("incident_id")
    await renderer.render(db, incident_id, judge_result, agent_id=request.agent_id)
    await db.commit()

    # Step 5: Auto-create bypass incident and record attempts
    if bypass_result.patterns_detected:
        from app.services.detect.incident_factory import IncidentFactory
        from app.services.detect.normalizer import PB_CES_Event

        # Create AGT-BYP-014 incident for the bypass attempt
        bypass_event = PB_CES_Event(
            event_id=f"bypass-{request.agent_id}-{int(time.time())}",
            source="judge_layer",
            event_type="bypass_detected",
            tool_call=request.action,
            agent_id=request.agent_id,
            session_id=request.session_id,
        )
        from app.services.detect.engine import DetectionResult
        bypass_detection = DetectionResult(
            incident_type="AGT-BYP-014",
            incident_type_name="Guardrail Bypass",
            severity="critical",
            confidence=bypass_result.confidence,
            anomaly_score=bypass_result.confidence * 100,
            matched_rules=[f"bypass:{p}" for p in bypass_result.patterns_detected],
            matched_patterns=bypass_result.patterns_detected,
            deterministic=True,
            category="bypass",
        )
        bypass_incident = await IncidentFactory.create_incident(
            db, bypass_event, bypass_detection
        )
        await db.flush()

        # Update the original incident if there is one
        if incident_id:
            bypass_incident.event_id = incident_id

        # Record bypass attempts
        for pattern_name in bypass_result.patterns_detected:
            pattern_result = await db.execute(
                select(BypassPattern).where(BypassPattern.pattern_name == pattern_name)
            )
            pattern = pattern_result.scalar_one_or_none()
            pattern_id = pattern.id if pattern else None

            attempt = BypassAttempt(
                incident_id=bypass_incident.id,
                pattern_id=pattern_id,
                detection_confidence=bypass_result.confidence,
                payload_sample=request.action[:500],
            )
            db.add(attempt)
        await db.commit()

    return JudgeEvaluateResponse(
        verdict=judge_result.verdict,
        severity_score=judge_result.severity_score,
        confidence=judge_result.confidence,
        matched_rules=judge_result.matched_rules,
        bypass_patterns_detected=judge_result.bypass_patterns_detected,
        rationale=judge_result.rationale,
        latency_ms=judge_result.latency_ms,
        resolved_policy_id=judge_result.resolved_policy_id,
    )


@router.get("/decisions/{agent_id}", response_model=StandardResponse)
async def get_decisions(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Get decision history for an agent."""
    # Count total
    count_result = await db.execute(
        select(func.count(JudgeDecision.id)).where(JudgeDecision.agent_id == agent_id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    result = await db.execute(
        select(JudgeDecision)
        .where(JudgeDecision.agent_id == agent_id)
        .order_by(JudgeDecision.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    decisions = result.scalars().all()

    return StandardResponse(
        data=[
            {
                "decision_id": d.decision_id,
                "incident_id": d.incident_id,
                "verdict": d.verdict,
                "severity_score": d.severity_score,
                "confidence": d.confidence,
                "matched_rules": d.matched_rules,
                "bypass_patterns": d.bypass_patterns_detected,
                "rationale": d.rationale,
                "latency_ms": d.latency_ms,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in decisions
        ],
        message=f"Found {total} decisions for agent {agent_id}",
    )


@router.get("/stats", response_model=JudgeStats)
async def get_judge_stats(
    db: AsyncSession = Depends(get_db),
) -> JudgeStats:
    """Get Judge Layer aggregate statistics."""
    # Total decisions
    count_result = await db.execute(select(func.count(JudgeDecision.id)))
    total_decisions = count_result.scalar() or 0

    # Verdict distribution
    verdict_result = await db.execute(
        select(JudgeDecision.verdict, func.count(JudgeDecision.id))
        .group_by(JudgeDecision.verdict)
    )
    verdict_distribution = {row[0]: row[1] for row in verdict_result.all()}
    # Ensure all verdicts are present
    for v in ["ALLOW", "DENY", "QUARANTINE", "ESCALATE"]:
        verdict_distribution.setdefault(v, 0)

    # Average latency
    avg_result = await db.execute(
        select(func.avg(JudgeDecision.latency_ms))
    )
    avg_latency = avg_result.scalar() or 0.0

    # P95 latency (approximate using subquery)
    p95_result = await db.execute(
        select(JudgeDecision.latency_ms)
        .order_by(JudgeDecision.latency_ms)
        .offset(int(total_decisions * 0.95))
        .limit(1)
    )
    p95_latency = p95_result.scalar() or 0.0

    # Bypass attempts blocked
    bypass_result = await db.execute(select(func.count(BypassAttempt.id)))
    bypass_attempts_blocked = bypass_result.scalar() or 0

    return JudgeStats(
        total_decisions=total_decisions,
        verdict_distribution=verdict_distribution,
        avg_latency_ms=round(avg_latency, 3),
        p95_latency_ms=round(p95_latency, 3),
        bypass_attempts_blocked=bypass_attempts_blocked,
    )


@router.get("/bypass-attempts", response_model=list[BypassAttemptResponse])
async def list_bypass_attempts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[BypassAttemptResponse]:
    """List detected bypass attempts."""
    result = await db.execute(
        select(BypassAttempt)
        .order_by(BypassAttempt.blocked_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    attempts = result.scalars().all()

    return [
        BypassAttemptResponse(
            id=a.id,
            incident_id=a.incident_id,
            pattern_id=a.pattern_id,
            detection_confidence=a.detection_confidence,
            blocked_at=a.blocked_at,
        )
        for a in attempts
    ]


@router.get("/bypass-patterns", response_model=list[BypassPatternResponse])
async def list_bypass_patterns(
    db: AsyncSession = Depends(get_db),
) -> list[BypassPatternResponse]:
    """List known bypass pattern definitions."""
    result = await db.execute(
        select(BypassPattern).where(BypassPattern.is_active == True)
    )
    patterns = result.scalars().all()

    return [
        BypassPatternResponse(
            id=p.id,
            pattern_name=p.pattern_name,
            canonical_name=p.canonical_name,
            aliases=p.aliases or [],
            description=p.description,
            severity=p.severity,
            is_active=p.is_active,
        )
        for p in patterns
    ]
