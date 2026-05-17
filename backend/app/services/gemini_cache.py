"""Gemini Cache — read-only cache overlay.

Cache key: SHA-256 of normalized metadata + judge verdict.
Cache hit enriches narrative only; NEVER overrides decision.
Zero LLM API calls in the enforcement path.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import GeminiCache


def _make_cache_key(metadata: Dict[str, Any], verdict: str) -> str:
    """Generate a deterministic cache key from metadata + verdict."""
    normalized = json.dumps(metadata, sort_keys=True, default=str) + f"|{verdict}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class CacheLookupResult:
    hit: bool
    enriched_narrative: Optional[str] = None
    cache_metadata: Optional[Dict[str, Any]] = None


class GeminiCacheService:
    """Read-only cache lookup service.

    Usage:
        cache = GeminiCacheService()
        result = await cache.lookup(db, metadata, verdict)
        if result.hit:
            # Enrich incident narrative with cached insight
            pass
    """

    async def lookup(
        self,
        db: AsyncSession,
        metadata: Dict[str, Any],
        verdict: str,
    ) -> CacheLookupResult:
        """Look up a cached enrichment for this metadata + verdict combination.

        Returns CacheLookupResult. On hit, enriched_narrative contains
        pre-computed analysis text. On miss, returns hit=False.

        Never blocks enforcement — this is called asynchronously after
        the deterministic decision has already been rendered.
        """
        cache_key = _make_cache_key(metadata, verdict)

        from datetime import datetime, timezone

        result = await db.execute(
            select(GeminiCache).where(
                GeminiCache.cache_key == cache_key,
                GeminiCache.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        cached = result.scalar_one_or_none()

        if cached is None:
            return CacheLookupResult(hit=False)

        # Update hit count
        cached.hit_count += 1
        await db.flush()

        response_data = cached.response_data or {}
        return CacheLookupResult(
            hit=True,
            enriched_narrative=response_data.get("narrative"),
            cache_metadata={
                "hit_count": cached.hit_count,
                "created_at": cached.created_at.isoformat() if cached.created_at else None,
            },
        )

    async def store(
        self,
        db: AsyncSession,
        metadata: Dict[str, Any],
        verdict: str,
        narrative: str,
        expires_in_seconds: int = 86400,
    ) -> str:
        """Store an enrichment in the cache.

        Called by background tasks or async enrichment pipeline.
        Never called from the enforcement hot path.
        """
        import datetime

        cache_key = _make_cache_key(metadata, verdict)
        request_hash = hashlib.sha256(
            json.dumps(metadata, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        # Check if entry exists
        result = await db.execute(
            select(GeminiCache).where(GeminiCache.cache_key == cache_key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.response_data = {"narrative": narrative}
            existing.expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                seconds=expires_in_seconds
            )
            existing.hit_count = 0
        else:
            cache_entry = GeminiCache(
                cache_key=cache_key,
                request_hash=request_hash,
                response_data={"narrative": narrative},
                expires_at=datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(seconds=expires_in_seconds),
            )
            db.add(cache_entry)

        await db.flush()
        return cache_key
