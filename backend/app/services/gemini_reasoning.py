"""Gemini-powered decision explainer.

Generates natural-language explanations for Judge Layer decisions.
Uses Vertex AI ADC when available, API key as fallback, and
pre-populated cache as last resort.
"""

import asyncio
import hashlib
import json
import os
import re
from typing import List

from app.core.config import get_settings

# Lazy imports — only load the SDK we actually need
genai = None
genai_client = None


def _lazy_import_genai():
    """Lazy-load google.generativeai (API-key path)."""
    global genai
    if genai is None:
        import google.generativeai as _genai
        genai = _genai
    return genai


def _lazy_import_genai_client():
    """Lazy-load google.genai Client (Vertex AI ADC path)."""
    global genai_client
    if genai_client is None:
        from google import genai as _genai
        genai_client = _genai
    return genai_client


def _generate_with_gemini_sync(prompt: str) -> str:
    """Call Gemini via API key or Vertex AI ADC. Returns empty string on failure."""
    settings = get_settings()
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")

    # Path 1: API key via google.generativeai
    if api_key:
        try:
            g = _lazy_import_genai()
            g.configure(api_key=api_key)
            model = g.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip() if response and hasattr(response, "text") and response.text else ""
            if text:
                return text
        except Exception:
            pass

    # Path 2: Vertex AI ADC via google-genai
    project = settings.gcp_project_id or os.getenv("GCP_PROJECT_ID")
    location = settings.gcp_location or os.getenv("GCP_LOCATION", "us-central1")
    if location == "global":
        location = "us-central1"
    if project:
        try:
            client_mod = _lazy_import_genai_client()
            client = client_mod.Client(vertexai=True, project=project, location=location)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            text = response.text.strip() if response and hasattr(response, "text") and response.text else ""
            if text:
                return text
        except Exception:
            pass

    return ""


async def generate_with_gemini(prompt: str) -> str:
    """Async wrapper that runs the sync Gemini call in a thread pool."""
    return await asyncio.to_thread(_generate_with_gemini_sync, prompt)


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


def _build_incident_analysis_prompt(
    incident_type: str,
    severity: str,
    confidence: float,
    category: str,
    tool_call: str,
    judge_verdict: str,
    bypass_detected: bool,
) -> str:
    """Build a Gemini prompt for comprehensive incident security analysis."""
    return (
        f"You are a senior AI security analyst. Analyze the following incident and provide a concise security assessment:\n\n"
        f"Incident Type: {incident_type}\n"
        f"Severity: {severity}\n"
        f"Confidence: {confidence:.0%}\n"
        f"Category: {category}\n"
        f"Payload/Tool Call: {tool_call}\n"
        f"Judge Verdict: {judge_verdict}\n"
        f"Bypass Detected: {'Yes' if bypass_detected else 'No'}\n\n"
        f"Provide 3 short sections:\n"
        f"1. THREAT_ANALYSIS: What was the attacker trying to achieve? (1-2 sentences)\n"
        f"2. IMPACT_ASSESSMENT: What would have happened if this was not blocked? (1-2 sentences)\n"
        f"3. REMEDIATION: Specific actions the security team should take now. (1-2 sentences)\n"
        f"Keep each section under 40 words. Be specific and actionable."
    )


def _fallback_incident_analysis(
    incident_type: str,
    severity: str,
    confidence: float,
    category: str,
    tool_call: str,
    judge_verdict: str,
    bypass_detected: bool,
) -> dict:
    """Return deterministic fallback analysis when Gemini is unavailable."""
    bypass_note = "A bypass attempt was detected, indicating sophisticated adversarial intent." if bypass_detected else "No bypass patterns were detected."
    return {
        "threat_analysis": f"A {severity.lower()} severity {category} incident was detected with {confidence:.0%} confidence. {bypass_note}",
        "impact_assessment": f"If unblocked, this {incident_type} incident could compromise data integrity or system availability, potentially resulting in regulatory violations.",
        "remediation": f"Review the blocked payload, verify agent permissions, and audit similar tool calls. Consider updating detection rules for this {category} category.",
    }


async def analyze_incident(
    incident_type: str,
    severity: str,
    confidence: float,
    category: str,
    tool_call: str,
    judge_verdict: str,
    bypass_detected: bool,
) -> dict:
    """Generate a comprehensive AI security analysis for an incident.

    Uses live Gemini via API key or Vertex AI ADC. Falls back to deterministic text.
    Returns a dict with threat_analysis, impact_assessment, and remediation.
    """
    prompt = _build_incident_analysis_prompt(
        incident_type, severity, confidence, category, tool_call, judge_verdict, bypass_detected
    )
    text = await generate_with_gemini(prompt)

    if text:
        result = {"threat_analysis": "", "impact_assessment": "", "remediation": ""}
        current_key = None
        for line in text.split("\n"):
            line = line.strip()
            if "THREAT_ANALYSIS" in line.upper() and (":" in line or line.startswith("1.")):
                current_key = "threat_analysis"
                m = re.search(r":\s*(.+)", line)
                if m:
                    result[current_key] += (" " if result[current_key] else "") + m.group(1)
                continue
            elif "IMPACT_ASSESSMENT" in line.upper() and (":" in line or line.startswith("2.")):
                current_key = "impact_assessment"
                m = re.search(r":\s*(.+)", line)
                if m:
                    result[current_key] += (" " if result[current_key] else "") + m.group(1)
                continue
            elif "REMEDIATION" in line.upper() and (":" in line or line.startswith("3.")):
                current_key = "remediation"
                m = re.search(r":\s*(.+)", line)
                if m:
                    result[current_key] += (" " if result[current_key] else "") + m.group(1)
                continue
            elif current_key and line:
                result[current_key] += (" " if result[current_key] else "") + line

        if all(result.values()):
            return result

    return _fallback_incident_analysis(
        incident_type, severity, confidence, category, tool_call, judge_verdict, bypass_detected
    )


def _build_compliance_report_prompt(framework: str, gaps: list) -> str:
    """Build a Gemini prompt for generating a narrative compliance report."""
    gap_summary = "\n".join(
        f"- {g['article']}: {g['requirement']} (Status: {g['status']})"
        for g in gaps[:10]
    )
    return (
        f"You are a compliance officer writing an executive summary for a {framework} gap analysis.\n\n"
        f"Findings:\n{gap_summary}\n\n"
        f"Write a 3-paragraph executive summary:\n"
        f"1. OVERVIEW: Current compliance posture in 2 sentences.\n"
        f"2. CRITICAL_GAPS: The most important gaps requiring immediate attention.\n"
        f"3. RECOMMENDATIONS: Specific next steps to achieve full compliance.\n"
        f"Use professional regulatory language. Keep each paragraph to 2-3 sentences."
    )


async def generate_compliance_report(framework: str, gaps: list) -> dict:
    """Generate an AI-powered narrative compliance report.

    Uses live Gemini via API key or Vertex AI ADC. Falls back to deterministic text.
    Returns a dict with overview, critical_gaps, and recommendations.
    """
    prompt = _build_compliance_report_prompt(framework, gaps)
    text = await generate_with_gemini(prompt)

    if text:
        result = {"overview": "", "critical_gaps": "", "recommendations": ""}
        current_key = None
        for line in text.split("\n"):
            line = line.strip()
            if "OVERVIEW" in line.upper() and (":" in line or line.startswith("1.")):
                current_key = "overview"
                m = re.search(r":\s*(.+)", line)
                if m:
                    result[current_key] += (" " if result[current_key] else "") + m.group(1)
                continue
            elif "CRITICAL_GAPS" in line.upper() and (":" in line or line.startswith("2.")):
                current_key = "critical_gaps"
                m = re.search(r":\s*(.+)", line)
                if m:
                    result[current_key] += (" " if result[current_key] else "") + m.group(1)
                continue
            elif "RECOMMENDATIONS" in line.upper() and (":" in line or line.startswith("3.")):
                current_key = "recommendations"
                m = re.search(r":\s*(.+)", line)
                if m:
                    result[current_key] += (" " if result[current_key] else "") + m.group(1)
                continue
            elif current_key and line:
                result[current_key] += (" " if result[current_key] else "") + line

        if all(result.values()):
            return result

    return {
        "overview": f"Gap analysis for {framework} has been completed. Review the detailed mapping table for control coverage and deficiency identification.",
        "critical_gaps": "Focus on incident reporting and risk management controls, as these are typically the most scrutinized during regulatory audits.",
        "recommendations": "Prioritize implementing automated evidence collection and establish a regular review cadence for policy updates.",
    }


async def explain_judge_decision(
    decision_id: str,
    verdict: str,
    severity_score: int,
    bypass_patterns: List[str],
    incident_type: str,
) -> str:
    """Generate a natural-language explanation for a Judge decision.

    Prefers live Gemini via API key or Vertex AI ADC.
    Falls back to deterministic fallback text on any error.
    """
    prompt = _build_prompt(verdict, incident_type, severity_score, bypass_patterns)
    text = await generate_with_gemini(prompt)
    if text:
        return text
    return _fallback_explanation(verdict, incident_type, severity_score, bypass_patterns)
