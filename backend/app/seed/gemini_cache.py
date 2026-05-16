"""Pre-populated Gemini Cache explanations for demo fallback.

20 realistic explanations covering common verdict × incident-type combinations.
Ensures the demo works without a live Gemini API key.
"""

import datetime
import hashlib
import json

from app.services.gemini_reasoning import generate_cache_key


def _build_seed_entry(
    verdict: str,
    incident_type: str,
    severity_score: int,
    bypass_patterns: list,
    explanation: str,
) -> dict:
    """Build a GeminiCache seed entry with deterministic key and far-future expiry."""
    cache_key = generate_cache_key(verdict, incident_type, severity_score, bypass_patterns)
    request_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    return {
        "cache_key": cache_key,
        "request_hash": request_hash,
        "response_data": {"explanation": explanation},
        "expires_at": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365),
        "hit_count": 0,
    }


GEMINI_CACHE_SEED = [
    # ALLOW — low severity, no bypass
    _build_seed_entry(
        "ALLOW", "prompt_injection", 2, [],
        "The Judge Layer allowed this prompt_injection incident (severity 2/10) because "
        "the input contained only benign stylistic patterns with no executable payload. "
        "Bypass patterns (none) did not exceed thresholds and standard monitoring continues."
    ),
    _build_seed_entry(
        "ALLOW", "insecure_output", 1, [],
        "The Judge Layer allowed this insecure_output incident (severity 1/10) because "
        "the generated content passed all output-filter checks and contained no sensitive tokens. "
        "No bypass patterns were detected and the session proceeds normally."
    ),
    _build_seed_entry(
        "ALLOW", "toxic_content", 3, [],
        "The Judge Layer allowed this toxic_content incident (severity 3/10) because "
        "sentiment scoring stayed within acceptable bounds and no slur or threat signatures matched. "
        "Standard logging continues without intervention."
    ),
    _build_seed_entry(
        "ALLOW", "data_exfiltration", 2, [],
        "The Judge Layer allowed this data_exfiltration incident (severity 2/10) because "
        "the outbound data flow was within policy limits and no credential patterns were present. "
        "Monitoring remains active."
    ),
    _build_seed_entry(
        "ALLOW", "model_manipulation", 2, [],
        "The Judge Layer allowed this model_manipulation incident (severity 2/10) because "
        "the prompt structure matched known benign instructional patterns rather than adversarial embeddings. "
        "No containment action is necessary."
    ),

    # DENY — clear violations
    _build_seed_entry(
        "DENY", "prompt_injection", 8, ["RoleSwap"],
        "The Judge Layer denied this prompt_injection incident (severity 8/10) due to "
        "a high-confidence RoleSwap bypass pattern embedded in the system preamble. "
        "Detected bypass patterns (RoleSwap) reinforced the deterministic block and no further action is required."
    ),
    _build_seed_entry(
        "DENY", "jailbreak_attempt", 9, ["SocialEngineering"],
        "The Judge Layer denied this jailbreak_attempt incident (severity 9/10) because "
        "the input contained a SocialEngineering bypass sequence designed to override safety instructions. "
        "The deterministic rule set matched immediately and the request was blocked."
    ),
    _build_seed_entry(
        "DENY", "privilege_escalation", 8, ["Separator"],
        "The Judge Layer denied this privilege_escalation incident (severity 8/10) due to "
        "a Separator-based tool-chaining pattern that attempted to elevate permissions without dual-auth. "
        "The bypass was intercepted and the action was blocked."
    ),
    _build_seed_entry(
        "DENY", "data_exfiltration", 7, ["Base64/encoding"],
        "The Judge Layer denied this data_exfiltration incident (severity 7/10) because "
        "the payload contained Base64/encoding obfuscation wrapping potential PII. "
        "Policy mandates automatic denial for encoded exfiltration channels."
    ),
    _build_seed_entry(
        "DENY", "system_prompt_leak", 6, [],
        "The Judge Layer denied this system_prompt_leak incident (severity 6/10) due to "
        "explicit prompt-injection tokens targeting configuration disclosure. "
        "No bypass patterns were detected, but the deterministic rule for prompt-leak probes triggered denial."
    ),

    # QUARANTINE — elevated but uncertain
    _build_seed_entry(
        "QUARANTINE", "prompt_injection", 5, ["Unicode homoglyph"],
        "The Judge Layer quarantined this prompt_injection incident (severity 5/10) because "
        "risk signals were elevated by Unicode homoglyph substitution that evaded basic filters, "
        "but definitive malicious intent was not established. Containment pending human review is in effect."
    ),
    _build_seed_entry(
        "QUARANTINE", "model_manipulation", 6, ["Context window displacement"],
        "The Judge Layer quarantined this model_manipulation incident (severity 6/10) because "
        "a Context window displacement pattern was detected, suggesting a long-horizon adversarial setup. "
        "The session is isolated until an analyst confirms benign intent."
    ),
    _build_seed_entry(
        "QUARANTINE", "toxic_content", 5, [],
        "The Judge Layer quarantined this toxic_content incident (severity 5/10) because "
        "edge-case sentiment scores hovered near the policy boundary without a clear deterministic match. "
        "The output is held for moderator review rather than released."
    ),
    _build_seed_entry(
        "QUARANTINE", "insecure_output", 4, ["Confidence hijacking"],
        "The Judge Layer quarantined this insecure_output incident (severity 4/10) because "
        "Confidence hijacking markers were found in the model's justification chain, "
        "raising doubt about the truthfulness of the generated response. Analyst verification is required."
    ),
    _build_seed_entry(
        "QUARANTINE", "jailbreak_attempt", 6, [],
        "The Judge Layer quarantined this jailbreak_attempt incident (severity 6/10) because "
        "the input contained multiple low-confidence bypass indicators that, taken together, exceeded the quarantine threshold. "
        "No single pattern was definitive, so containment is the safest posture."
    ),

    # ESCALATE — high uncertainty or critical severity
    _build_seed_entry(
        "ESCALATE", "privilege_escalation", 10, ["Indirect tool chaining", "Separator"],
        "The Judge Layer escalated this privilege_escalation incident (severity 10/10) due to "
        "critical severity combined with multiple bypass patterns: Indirect tool chaining and Separator. "
        "The deterministic rule engine lacks an unambiguous playbook for chained privilege elevation, requiring senior analyst intervention."
    ),
    _build_seed_entry(
        "ESCALATE", "data_exfiltration", 9, ["Base64/encoding", "Unicode homoglyph"],
        "The Judge Layer escalated this data_exfiltration incident (severity 9/10) because "
        "the request exhibited both Base64/encoding and Unicode homoglyph obfuscation, indicating sophisticated adversarial tradecraft. "
        "Policy mandates escalation for multi-vector bypass attempts."
    ),
    _build_seed_entry(
        "ESCALATE", "system_prompt_leak", 8, ["RoleSwap", "Confidence hijacking"],
        "The Judge Layer escalated this system_prompt_leak incident (severity 8/10) due to "
        "high uncertainty: RoleSwap and Confidence hijacking patterns were both detected, suggesting a coordinated extraction attempt. "
        "Senior analysts must evaluate whether prompt hardening has been compromised."
    ),
    _build_seed_entry(
        "ESCALATE", "jailbreak_attempt", 7, [],
        "The Judge Layer escalated this jailbreak_attempt incident (severity 7/10) because "
        "the deterministic rule set flagged novel manipulation primitives not yet mapped to a specific bypass taxonomy. "
        "Human expertise is required to update detection logic and render a final verdict."
    ),
    _build_seed_entry(
        "ESCALATE", "prompt_injection", 8, ["Context window displacement", "SocialEngineering"],
        "The Judge Layer escalated this prompt_injection incident (severity 8/10) due to "
        "a hybrid attack combining Context window displacement and SocialEngineering, creating ambiguity about the true user intent. "
        "The ODP resolver returned conflicting parameters, so escalation is the deterministic default."
    ),
]
