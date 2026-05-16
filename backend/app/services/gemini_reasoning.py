"""Gemini-powered decision explainer.

Generates natural-language explanations for Judge Layer decisions.
Uses pre-populated cache as fallback when API is unavailable.
"""

import hashlib
import json
import os
from typing import List

import google.generativeai as genai

from app.core.config import get_settings


def _build_prompt(verdict: str, incident_type: str, severity_score: int, bypass_patterns: List[str]) -> str:
    """Build the Gemini prompt for explaining a judge decision."""
    bypass_str = ", ".join(bypass_patterns) if bypass_patterns else "none"
    return (
        f"Explain why an AI agent security system rendered a {verdict} verdict "
        f"for a {incident_type} incident with severity {severity_score}/10. "
        f"Bypass patterns detected: {bypass_str}. "
        f"Explain in 2-3 sentences suitable for a security analyst."
    )


def _fallback_explanation(verdict: str, incident_type: str, severity_score: int, bypass_patterns: List[str]) -> str:
    """Return a deterministic fallback explanation when Gemini is unavailable."""
    bypass_str = ", ".join(bypass_patterns) if bypass_patterns else "none"
    explanations = {
        "ALLOW": (
            f"The Judge Layer allowed this {incident_type} incident (severity {severity_score}/10) because "
            f"no critical risk indicators were triggered and bypass patterns ({bypass_str}) did not exceed thresholds. "
            f"Standard monitoring continues."
        ),
        "DENY": (
            f"The Judge Layer denied this {incident_type} incident (severity {severity_score}/10) due to "
            f"clear policy violations. Detected bypass patterns ({bypass_str}) reinforced the deterministic block. "
            f"No further action is required."
        ),
        "QUARANTINE": (
            f"The Judge Layer quarantined this {incident_type} incident (severity {severity_score}/10) because "
            f"risk signals were elevated but not definitively malicious. Bypass patterns ({bypass_str}) triggered "
            f"containment pending human review."
        ),
        "ESCALATE": (
            f"The Judge Layer escalated this {incident_type} incident (severity {severity_score}/10) due to "
            f"high uncertainty or critical severity. Bypass patterns ({bypass_str}) and policy gaps require "
            f"senior analyst intervention."
        ),
    }
    return explanations.get(verdict, explanations["ESCALATE"])


def generate_cache_key(verdict: str, incident_type: str, severity_score: int, bypass_patterns: List[str]) -> str:
    """Generate a deterministic generic cache key for a decision profile."""
    payload = json.dumps(
        {
            "verdict": verdict,
            "incident_type": incident_type,
            "severity_score": severity_score,
            "bypass_patterns": sorted(bypass_patterns),
        },
        sort_keys=True,
    )
    hash_val = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"judge_explain:generic:{hash_val}"


def explain_judge_decision(
    decision_id: str,
    verdict: str,
    severity_score: int,
    bypass_patterns: List[str],
    incident_type: str,
) -> str:
    """Generate a natural-language explanation for a Judge decision.

    Prefers live Gemini API when GEMINI_API_KEY is configured.
    Falls back to deterministic fallback text on any API error.
    """
    settings = get_settings()
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")

    if not api_key:
        return _fallback_explanation(verdict, incident_type, severity_score, bypass_patterns)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = _build_prompt(verdict, incident_type, severity_score, bypass_patterns)
        response = model.generate_content(prompt)
        text = response.text.strip() if response and hasattr(response, "text") and response.text else ""
        if text:
            return text
    except Exception:
        # Graceful fallback on any API error
        pass

    return _fallback_explanation(verdict, incident_type, severity_score, bypass_patterns)
