#!/usr/bin/env python3
"""Offline Gemini cache population script.

Uses Application Default Credentials (ADC) to authenticate with the
Gemini API. Populates the PLAYBOOK cache with enrichment narratives
for all 16 incident types.

Usage:
    cd backend && source venv/Scripts/activate
    python scripts/populate_gemini_cache.py

Prerequisites:
    gcloud auth application-default login
    # OR set GOOGLE_APPLICATION_CREDENTIALS to a service account key

Environment:
    GEMINI_MODEL_FLASH -- fast model for bulk generation (default: gemini-3.1-flash-lite)
    GEMINI_MODEL_PRO   -- high-quality model for critical types (default: gemini-3.1-pro-preview)
    GCP_PROJECT_ID     -- Google Cloud project ID
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database import AsyncSessionLocal
from app.models import GeminiCache
from app.services.gemini_cache import GeminiCacheService

settings = get_settings()

# Model selection
MODEL_FLASH = os.getenv("GEMINI_MODEL_FLASH", "gemini-3.1-flash-lite")
MODEL_PRO = os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview")
PROJECT_ID = os.getenv("GCP_PROJECT_ID", getattr(settings, "gcp_project_id", None))

# Incident type prompts for enrichment
INCIDENT_PROMPTS = {
    "AGT-DEL-001": "Explain in 2 sentences why an AI agent attempting to DROP a production database table is a critical incident requiring immediate containment.",
    "AGT-FIN-002": "Explain in 2 sentences why an AI trading agent committing to an unauthorized $40M FX swap is a critical financial incident.",
    "AGT-PER-003": "Explain in 2 sentences why an AI agent attempting to escalate its own IAM permissions is a high-severity security incident.",
    "AGT-HRM-004": "Explain in 2 sentences why an AI healthcare agent automatically denying coverage for an emergency procedure is a critical harmful output incident.",
    "AGT-EXT-005": "Explain in 2 sentences why an AI agent attempting to export user records to an unauthorized external API is a critical data exfiltration incident.",
    "AGT-INJ-006": "Explain in 2 sentences why an AI agent that ignores previous instructions and executes a DELETE command may be under prompt injection attack.",
    "AGT-HAL-007": "Explain in 2 sentences why an AI agent generating conflicting information across multiple turns indicates a hallucination cascade.",
    "AGT-CRE-008": "Explain in 2 sentences why an AI agent exposing credentials or secrets in its output is a critical credential exposure incident.",
    "AGT-RAT-009": "Explain in 2 sentences why an AI agent repeatedly exceeding rate limits may indicate abuse or a runaway loop.",
    "AGT-DRF-010": "Explain in 2 sentences why an AI agent whose responses drift from established behavioral baselines may indicate model drift.",
    "AGT-TLM-011": "Explain in 2 sentences why an AI agent using tools outside their documented parameters is a tool misuse incident.",
    "AGT-GAP-012": "Explain in 2 sentences why an AI agent action that falls outside all known incident taxonomies is a coverage gap requiring human review.",
    "AGT-SPY-013": "Explain in 2 sentences why systematic unauthorized data access by an AI agent suggests espionage behavior.",
    "AGT-BYP-014": "Explain in 2 sentences why an AI agent action that bypasses guardrails is a critical guardrail bypass incident.",
    "AGT-PRV-015": "Explain in 2 sentences why an AI agent processing personal data without authorization is a privacy violation incident.",
    "AGT-REG-016": "Explain in 2 sentences why an AI agent action triggering regulatory thresholds (EU AI Act, HIPAA) is a regulatory incident.",
}


def _configure_gemini_adc():
    """Configure Gemini SDK with Application Default Credentials."""
    try:
        import google.generativeai as genai
        from google.auth import default as google_auth_default
        from google.auth.transport.requests import Request

        credentials, project = google_auth_default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        # Refresh credentials if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        genai.configure(
            credentials=credentials,
            project=project or PROJECT_ID,
        )
        print(f"[gemini] Authenticated via ADC (project: {project or PROJECT_ID})")
        return genai
    except Exception as exc:
        print(f"[gemini] ADC authentication failed: {exc}")
        print("[gemini] Run: gcloud auth application-default login")
        print("[gemini] Or set GOOGLE_APPLICATION_CREDENTIALS to a service account key")
        return None


async def _generate_narrative(genai, incident_type: str, prompt: str) -> str:
    """Generate an enrichment narrative using Gemini."""
    model_name = MODEL_PRO if incident_type in ("AGT-DEL-001", "AGT-FIN-002", "AGT-HRM-004", "AGT-EXT-005") else MODEL_FLASH

    try:
        model = genai.GenerativeModel(model_name)
        response = await model.generate_content_async(prompt)
        narrative = response.text.strip() if response and response.text else ""
        print(f"[gemini] {incident_type} -> {model_name} -> OK ({len(narrative)} chars)")
        return narrative
    except Exception as exc:
        print(f"[gemini] {incident_type} -> ERROR: {exc}")
        return f"[Gemini enrichment unavailable: {exc}]"


async def populate_cache(db: AsyncSession):
    """Populate the Gemini cache with enrichment narratives for all incident types."""
    genai = _configure_gemini_adc()
    if genai is None:
        print("[populate] Skipping cache population — Gemini not authenticated")
        return

    cache_service = GeminiCacheService()

    for incident_type, prompt in INCIDENT_PROMPTS.items():
        # Check if cache entry already exists
        from sqlalchemy import select
        from app.services.gemini_cache import _make_cache_key

        dummy_metadata = {"incident_type": incident_type, "source": "populate_script"}
        cache_key = _make_cache_key(dummy_metadata, "DENY")

        result = await db.execute(
            select(GeminiCache).where(GeminiCache.cache_key == cache_key)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[populate] {incident_type} -> already cached, skipping")
            continue

        # Generate narrative
        narrative = await _generate_narrative(genai, incident_type, prompt)

        # Store in cache
        await cache_service.store(
            db,
            metadata=dummy_metadata,
            verdict="DENY",
            narrative=narrative,
            expires_in_seconds=7 * 24 * 3600,  # 7 days
        )
        await db.commit()

    print("[populate] Cache population complete")


async def main():
    print("=" * 60)
    print("PLAYBOOK Gemini Cache Population Script")
    print("=" * 60)
    print(f"Flash model: {MODEL_FLASH}")
    print(f"Pro model:   {MODEL_PRO}")
    print(f"Project:     {PROJECT_ID or 'default'}")
    print("-" * 60)

    async with AsyncSessionLocal() as db:
        await populate_cache(db)

    print("-" * 60)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
