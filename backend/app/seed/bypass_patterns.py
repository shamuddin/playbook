"""Seed data for BypassPattern table."""

BYPASS_PATTERNS_SEED = [
    {
        "pattern_name": "context_window_displacement",
        "canonical_name": "Context Window Displacement",
        "aliases": ["RoleSwap", "system_override", "jailbreak"],
        "description": (
            "Attackers stuff the context window with instructions that displace "
            "the system prompt, causing the model to ignore safety guardrails. "
            "Defense: Judge operates on structured metadata, not raw prompt text."
        ),
        "detection_logic": "Pattern match on displacement keywords in metadata fields",
        "severity": 8,
        "is_active": True,
    },
    {
        "pattern_name": "indirect_tool_chaining",
        "canonical_name": "Indirect Tool Chaining",
        "aliases": ["Separator", "tool_chain", "multi_step_exfil"],
        "description": (
            "Attackers split a malicious operation across multiple tool calls "
            "to evade per-call safety checks. Defense: Composite pattern detection "
            "across session window for known suspicious tool sequences."
        ),
        "detection_logic": "Session window analysis for known chain signatures",
        "severity": 9,
        "is_active": True,
    },
    {
        "pattern_name": "unicode_homoglyph",
        "canonical_name": "Unicode Homoglyph Substitution",
        "aliases": ["homoglyph", "confusable", "lookalike_characters"],
        "description": (
            "Attackers substitute ASCII characters with visually identical Unicode "
            "characters (e.g., Cyrillic 'а' for Latin 'a') to evade string-based filters. "
            "Defense: NFKC normalization + TR39 confusables check before rule matching."
        ),
        "detection_logic": "NFKC normalization + confusable character count threshold",
        "severity": 7,
        "is_active": True,
    },
    {
        "pattern_name": "confidence_hijacking",
        "canonical_name": "Confidence Hijacking",
        "aliases": ["social_engineering", "authority_claim", "trust_manipulation"],
        "description": (
            "Attackers manipulate the model's confidence or claim authority "
            "to bypass safety checks (e.g., 'trust me, this is approved by admin'). "
            "Defense: Binary enforcement for known patterns; confidence is advisory only."
        ),
        "detection_logic": "Pattern match on authority/trust manipulation keywords",
        "severity": 6,
        "is_active": True,
    },
]
