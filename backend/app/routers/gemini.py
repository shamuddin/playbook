"""Gemini Decision Explainer router."""

import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import GeminiCache, Incident, JudgeDecision
from app.schemas import StandardResponse
from app.services.gemini_reasoning import explain_judge_decision, generate_cache_key

router = APIRouter(tags=["gemini"])


@router.post("/judge/{decision_id}/explain", response_model=StandardResponse)
async def explain_decision(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
) -> StandardResponse:
    """Generate a Gemini-powered explanation for a Judge decision.

    Returns cached explanation if available, otherwise calls Gemini API
    and stores the result in the gemini_cache table.
    """
    # Look up the decision
    result = await db.execute(
        select(JudgeDecision).where(JudgeDecision.decision_id == decision_id)
    )
    decision = result.scalar_one_or_none()
    if decision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Judge decision {decision_id} not found",
        )

    # Resolve incident type from the linked incident
    incident_result = await db.execute(
        select(Incident).where(Incident.id == decision.incident_id)
    )
    incident = incident_result.scalar_one_or_none()
    incident_type = incident.incident_type if incident else "unknown"
    bypass_patterns = decision.bypass_patterns_detected or []

    # 1. Check decision-specific cache
    specific_key = f"judge_explain:{decision_id}"
    cache_result = await db.execute(
        select(GeminiCache).where(GeminiCache.cache_key == specific_key)
    )
    cached = cache_result.scalar_one_or_none()
    if cached:
        cached.hit_count += 1
        await db.commit()
        explanation = cached.response_data.get("explanation", "")
        return StandardResponse(
            data={
                "explanation": explanation,
                "model": "gemini-1.5-flash",
                "cached": True,
            }
        )

    # 2. Check generic cache (pre-seeded for demo)
    generic_key = generate_cache_key(decision.verdict, incident_type, decision.severity_score, bypass_patterns)
    generic_result = await db.execute(
        select(GeminiCache).where(GeminiCache.cache_key == generic_key)
    )
    generic_cached = generic_result.scalar_one_or_none()
    if generic_cached:
        generic_cached.hit_count += 1
        await db.commit()
        explanation = generic_cached.response_data.get("explanation", "")
        # Also store in decision-specific cache for future lookups
        await _store_explanation(db, specific_key, explanation)
        return StandardResponse(
            data={
                "explanation": explanation,
                "model": "gemini-1.5-flash",
                "cached": True,
            }
        )

    # 3. Generate explanation via Gemini API or fallback
    explanation = await explain_judge_decision(
        decision_id=decision.decision_id,
        verdict=decision.verdict,
        severity_score=decision.severity_score,
        bypass_patterns=bypass_patterns,
        incident_type=incident_type,
    )

    # 4. Store in decision-specific cache
    await _store_explanation(db, specific_key, explanation)

    return StandardResponse(
        data={
            "explanation": explanation,
            "model": "gemini-1.5-flash",
            "cached": False,
        }
    )


async def _store_explanation(db: AsyncSession, cache_key: str, explanation: str) -> None:
    """Store an explanation in the gemini_cache table."""
    import hashlib

    request_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(days=30)

    cache_entry = GeminiCache(
        cache_key=cache_key,
        request_hash=request_hash,
        response_data={"explanation": explanation},
        expires_at=expires_at,
        hit_count=1,
    )
    db.add(cache_entry)
    await db.commit()
