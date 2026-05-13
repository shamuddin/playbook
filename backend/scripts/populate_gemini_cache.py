#!/usr/bin/env python3
"""Offline Gemini cache population script.

Uses Application Default Credentials (ADC) via Vertex AI when available.
Falls back to pre-written static enrichment narratives for demo mode.

Usage:
    cd backend && . venv/Scripts/activate
    python scripts/populate_gemini_cache.py

Prerequisites (for live Gemini):
    - Vertex AI API enabled in GCP project
    - gcloud auth application-default login

Environment:
    GEMINI_MODEL_FLASH -- fast model (default: gemini-3.1-flash-lite)
    GEMINI_MODEL_PRO   -- high-quality model (default: gemini-3.1-pro-preview)
    GCP_PROJECT_ID     -- Google Cloud project ID
    GCP_LOCATION       -- Vertex AI region (default: global)
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.database import AsyncSessionLocal
from app.models import GeminiCache
from app.services.gemini_cache import GeminiCacheService

settings = get_settings()
MODEL_FLASH = os.getenv("GEMINI_MODEL_FLASH", "gemini-3.1-flash-lite")
MODEL_PRO = os.getenv("GEMINI_MODEL_PRO", "gemini-3.1-pro-preview")
PROJECT_ID = os.getenv("GCP_PROJECT_ID") or settings.gcp_project_id
LOCATION = os.getenv("GCP_LOCATION") or settings.gcp_location
DEMO_MODE = settings.is_demo_mode

# Pre-written static enrichment narratives (fallback when Gemini unavailable)
STATIC_NARRATIVES = {
    "AGT-DEL-001": "An AI agent attempting to DROP a production database table represents an immediate existential threat to data integrity. This is classified as CRITICAL because a single executed DROP command can destroy millions of customer records without recovery. The agent may have received a malicious instruction via prompt injection or may be hallucinating a destructive action. Deterministic enforcement is required because LLM-based judges can be bypassed by context-window displacement attacks that hide the malicious intent.",
    "AGT-FIN-002": "An AI trading agent committing to a $40M unauthorized FX swap represents a critical financial risk exposure. This incident type bypasses standard authorization workflows and can result in immediate, irreversible monetary loss. The agent may have misinterpreted a benign trading instruction or may be under adversarial control. Deterministic enforcement with Organization-Defined Parameters allows FinTech organizations to set conditional CRITICAL severity only when financial records are affected.",
    "AGT-PER-003": "An AI agent attempting to escalate its own IAM permissions is a high-severity privilege escalation attack. This represents a fundamental security boundary violation where the agent seeks capabilities beyond its authorized scope. If successful, the agent could access sensitive infrastructure, modify audit logs, or disable security controls. Cross-turn state tracking in the deterministic Judge Layer can detect this pattern even when spread across multiple seemingly innocent queries.",
    "AGT-HRM-004": "An AI healthcare agent automatically denying coverage for an emergency craniotomy is a critical harmful output incident with life-or-death consequences. This bypasses physician review and directly impacts patient care. The agent may have misclassified the procedure or may have been influenced by cost-optimization prompts. Deterministic enforcement ensures that healthcare-critical decisions are never made by probabilistic classification alone.",
    "AGT-EXT-005": "An AI agent attempting to export user records to an unauthorized external API is a critical data exfiltration incident. This represents unauthorized data processing under Article 5(1)(a) GDPR and triggers mandatory breach notification requirements. The agent may have been instructed to 'sync data' without understanding authorization boundaries. NIST SP 800-61r2 Step 1 (Detection) maps directly to this incident type, triggering automated containment.",
    "AGT-INJ-006": "An AI agent that ignores previous instructions and executes a DELETE command is exhibiting behavior consistent with prompt injection attack pattern AGT-INJ-006. The attacker may have embedded the malicious instruction in user input, documentation, or retrieved context. The deterministic Judge Layer uses NFKC normalization and AST pattern matching to detect these attacks, unlike LLM-based judges which can be bypassed by Unicode homoglyphs.",
    "AGT-HAL-007": "An AI agent generating conflicting information across multiple turns indicates a hallucination cascade. This occurs when the agent's confidence in incorrect information compounds over time, leading to increasingly divergent responses. In production, this can result in inconsistent customer support, incorrect financial calculations, or dangerous medical advice. The deterministic Judge Layer does not rely on LLM confidence scores; it uses hard rule matching for known patterns.",
    "AGT-CRE-008": "An AI agent exposing credentials or secrets in its output is a critical credential exposure incident. This violates the principle of least privilege and can lead to immediate account compromise. Common triggers include insufficient output filtering, prompt injection that requests 'debug information', or hallucinated authentication flows. The deterministic Judge Layer scans all outputs for credential patterns using deterministic regex matching, not probabilistic LLM classification.",
    "AGT-RAT-009": "An AI agent repeatedly exceeding rate limits may indicate abuse, a runaway loop, or adversarial resource exhaustion. This pattern can degrade service for legitimate users and increase operational costs significantly. The deterministic Judge Layer tracks per-session request velocity and applies rate-limiting decisions without LLM inference, ensuring sub-millisecond response times even under high load.",
    "AGT-DRF-010": "An AI agent whose responses drift from established behavioral baselines may indicate model drift or prompt manipulation. Model drift occurs when the underlying LLM's behavior changes due to temperature variations, context window pressure, or fine-tuning updates. The deterministic Judge Layer does not depend on model behavior; it uses immutable rules that produce identical decisions for identical inputs across all model versions.",
    "AGT-TLM-011": "An AI agent using tools outside their documented parameters is a tool misuse incident. This occurs when the agent invents parameters, calls tools with incorrect types, or chains tools in unauthorized sequences. The deterministic Judge Layer validates every tool call against an allowlist of authorized parameters before execution, preventing parameter injection attacks that LLM-based judges frequently miss.",
    "AGT-GAP-012": "An AI agent action that falls outside all known incident taxonomies is a coverage gap requiring immediate human review. This indicates either a novel attack vector or an emergent agent behavior not captured by existing detection rules. The deterministic Judge Layer fails-closed (ESCALATE) on any unrecognized pattern, ensuring that novel threats are never silently allowed.",
    "AGT-SPY-013": "Systematic unauthorized data access by an AI agent suggests espionage behavior pattern AGT-SPY-013. This is characterized by low-and-slow data harvesting, access to records outside the agent's scope, and attempts to obfuscate access patterns. The deterministic Judge Layer tracks cross-session state and detects anomalous access patterns using deterministic rule matching, not behavioral baselines that can be poisoned.",
    "AGT-BYP-014": "An AI agent action that bypasses guardrails is a critical guardrail bypass incident. This includes context window displacement, Unicode homoglyph substitution, adversarial suffix injection, and multi-turn state confusion. LLM-based judges are vulnerable to all four patterns. The deterministic Judge Layer uses NFKC normalization, AST pattern matching, cross-turn state tracking, and context boundary analysis to detect and block these attacks with 100% accuracy on known patterns.",
    "AGT-PRV-015": "An AI agent processing personal data without authorization is a privacy violation incident under GDPR Article 6 and EU AI Act Article 10. This includes accessing PII fields outside the agent's scope, retaining data longer than authorized, or transmitting data to unauthorized processing systems. The deterministic Judge Layer applies data classification labels at ingestion and enforces access control on every output, regardless of the agent's claimed intent.",
    "AGT-REG-016": "An AI agent action triggering regulatory thresholds is a regulatory incident requiring compliance reporting. This includes incidents that meet EU AI Act Article 73 reporting criteria, HIPAA breach notification thresholds, or PCI-DSS incident response triggers. The deterministic Judge Layer automatically assigns regulatory tags based on incident type and severity, triggering automated compliance report generation for all CRITICAL and HIGH severity incidents.",
}


def _try_gemini_client():
    """Try to configure a live Gemini client via Vertex AI."""
    try:
        from google import genai
        from google.auth import default as google_auth_default
        from google.auth.transport.requests import Request

        credentials, project = google_auth_default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        project_id = PROJECT_ID or project
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=LOCATION,
            credentials=credentials,
        )
        print(f"[gemini] ADC authenticated (project: {project_id}, location: {LOCATION})")
        return client, genai.types.GenerateContentConfig
    except Exception as exc:
        print(f"[gemini] ADC setup failed: {exc}")
        return None, None


async def _generate_live(client, config_cls, incident_type: str, prompt: str) -> str:
    """Generate narrative using live Gemini API."""
    model_name = MODEL_PRO if incident_type in ("AGT-DEL-001", "AGT-FIN-002", "AGT-HRM-004", "AGT-EXT-005") else MODEL_FLASH
    try:
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config_cls(max_output_tokens=256, temperature=0.3),
        )
        narrative = response.text.strip() if response and response.text else ""
        print(f"[gemini] {incident_type} -> {model_name} -> OK ({len(narrative)} chars)")
        return narrative
    except Exception as exc:
        print(f"[gemini] {incident_type} -> ERROR: {exc}")
        return ""


async def populate_cache(db):
    """Populate the Gemini cache with enrichment narratives."""
    client, config_cls = _try_gemini_client()
    use_live = client is not None

    if not use_live:
        if DEMO_MODE:
            print("[populate] Gemini unavailable — using static enrichment narratives (DEMO_MODE)")
        else:
            print("[populate] ERROR: Gemini unavailable in LIVE mode.")
            print("[populate] Enable Vertex AI API: https://console.cloud.google.com/vertex-ai")
            raise RuntimeError("Vertex AI API not enabled — cannot populate cache in live mode")
    else:
        # Quick health check with a simple prompt
        try:
            test_resp = await client.aio.models.generate_content(
                model=MODEL_FLASH,
                contents="Say OK",
                config=config_cls(max_output_tokens=20),
            )
            # Check for valid response (candidates present, not just text)
            if not (test_resp and test_resp.candidates):
                use_live = False
                if DEMO_MODE:
                    print("[populate] Gemini health check failed — using static narratives (DEMO_MODE)")
                else:
                    raise RuntimeError("Gemini health check failed in live mode")
            print(f"[populate] Gemini health check OK ({test_resp.model_version})")
        except Exception:
            if DEMO_MODE:
                use_live = False
                print("[populate] Gemini health check failed — using static narratives (DEMO_MODE)")
            else:
                raise

    cache_service = GeminiCacheService()

    for incident_type, static_narrative in STATIC_NARRATIVES.items():
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

        if use_live:
            prompt = f"Explain in 2-3 sentences why incident type {incident_type} is a critical security concern for AI agents."
            narrative = await _generate_live(client, config_cls, incident_type, prompt)
            if not narrative:
                if DEMO_MODE:
                    narrative = static_narrative
                    print(f"[populate] {incident_type} -> fell back to static narrative")
                else:
                    raise RuntimeError(f"Gemini failed for {incident_type} in live mode")
        else:
            narrative = static_narrative
            print(f"[populate] {incident_type} -> static narrative ({len(narrative)} chars)")

        await cache_service.store(
            db,
            metadata=dummy_metadata,
            verdict="DENY",
            narrative=narrative,
            expires_in_seconds=7 * 24 * 3600,
        )
        await db.commit()

    print("[populate] Cache population complete")


async def main():
    print("=" * 60)
    print("PLAYBOOK Gemini Cache Population Script")
    print("=" * 60)
    print(f"Flash model: {MODEL_FLASH}")
    print(f"Pro model:   {MODEL_PRO}")
    print(f"Project:     {PROJECT_ID or 'auto-detect'}")
    print(f"Location:    {LOCATION}")
    print("-" * 60)

    async with AsyncSessionLocal() as db:
        await populate_cache(db)

    print("-" * 60)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
