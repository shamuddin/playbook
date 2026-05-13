"""Bypass Pattern Detector.

Detects 4 known LLM-judge bypass patterns:
1. Context Window Displacement
2. Indirect Tool Chaining
3. Unicode Homoglyph Substitution
4. Confidence Hijacking

Defense by design:
- Operates on structured metadata, never raw natural language
- NFKC normalization before string matching
- Binary enforcement (confidence is advisory)
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


# Unicode confusable characters commonly used in homoglyph attacks
# Maps lookalike characters to their canonical ASCII equivalents
_CONFUSABLE_MAP: Dict[str, str] = {
    "а": "a",  # Cyrillic а (U+0430) → Latin a (U+0061)
    "е": "e",  # Cyrillic е (U+0435) → Latin e (U+0065)
    "о": "o",  # Cyrillic о (U+043E) → Latin o (U+006F)
    "р": "p",  # Cyrillic р (U+0440) → Latin p (U+0070)
    "с": "c",  # Cyrillic с (U+0441) → Latin c (U+0063)
    "х": "x",  # Cyrillic х (U+0445) → Latin x (U+0078)
    "і": "i",  # Cyrillic і (U+0456) → Latin i (U+0069)
    "ј": "j",  # Cyrillic ј (U+0458) → Latin j (U+006A)
    "ԁ": "d",  # Cyrillic ԁ (U+0501) → Latin d (U+0064)
    "ѕ": "s",  # Cyrillic ѕ (U+0455) → Latin s (U+0073)
    "һ": "h",  # Cyrillic һ (U+04BB) → Latin h (U+0068)
    "ո": "n",  # Armenian ո (U+0578) → Latin n (U+006E)
    "օ": "o",  # Armenian օ (U+0585) → Latin o (U+006F)
    "ᴛ": "T",  # Small caps ᴛ (U+1D1B) → Latin T (U+0054)
    "ᴄ": "C",  # Small caps ᴄ (U+1D04) → Latin C (U+0043)
}

# Known tool chaining signatures
_TOOL_CHAIN_SIGNATURES = [
    # Pattern: tool_a → result → tool_b where the pair is suspicious
    (r"read_file|file_read|read", r"send_email|email_send|post|upload"),
    (r"query_database|db_query|sql", r"curl|wget|fetch|request"),
    (r"list_users|enumerate|scan", r"curl|wget|fetch|scp|rsync"),
    (r"get_password|retrieve_secret|fetch_token|retrieve_token", r"curl|wget|post|send|upload"),
    (r"search_web|web_search|browser", r"write_file|file_write|save"),
]

# Context window displacement indicators
_CONTEXT_DISPLACEMENT_INDICATORS = [
    r"ignore\s+(all\s+)?previous\s+(instructions|commands|rules)",
    r"disregard\s+(all\s+)?(prior|previous|above|the\s+above)",
    r"forget\s+(everything|all|your)\s+(instructions|training|rules)",
    r"you\s+are\s+now\s+(a\s+)?\w+",
    r"new\s+role\s*:\s*",
    r"system\s*:\s*you\s+are",
    r"developer\s+mode\s*:\s*enabled",
    r"DAN\s*mode",
    r"jailbreak",
    r"\[system\s+override\]",
]

# Confidence hijacking patterns
_CONFIDENCE_HIJACKING_PATTERNS = [
    r"i\s+am\s+(certain|100%\s+confident)\s+this\s+is\s+safe",
    r"trust\s+me\s*,?\s+(completely,\s+)?this\s+is\s+(authorized|fully\s+authorized)",
    r"approved\s+by\s+(admin|root|superuser)",
    r"override\s+(all\s+)?safety\s+(check|guard|limit|checks)",
    r"confidence\s*:\s*(99|100)%",
    r"this\s+request\s+is\s+(benign|harmless|safe|completely\s+harmless)",
]


@dataclass
class BypassResult:
    """Result of bypass pattern detection."""

    patterns_detected: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0–1.0, advisory only
    normalized_payload: str = ""
    details: Dict[str, any] = field(default_factory=dict)

    @property
    def is_bypass_detected(self) -> bool:
        return len(self.patterns_detected) > 0


class BypassDetector:
    """Detects known LLM-judge bypass patterns.

    All detection is deterministic and operates on normalized structured data.
    """

    def __init__(self):
        self._context_patterns = [re.compile(p, re.IGNORECASE) for p in _CONTEXT_DISPLACEMENT_INDICATORS]
        self._confidence_patterns = [re.compile(p, re.IGNORECASE) for p in _CONFIDENCE_HIJACKING_PATTERNS]

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Apply NFKC normalization and map confusable characters."""
        # First apply NFKC normalization
        normalized = unicodedata.normalize("NFKC", text)
        # Then map known confusables
        result = []
        for char in normalized:
            result.append(_CONFUSABLE_MAP.get(char, char))
        return "".join(result)

    def detect_context_window_displacement(self, text: str) -> tuple[bool, float, str]:
        """Detect context window displacement / role swap attempts.

        Defense: We only scan for pattern signatures in metadata fields.
        The actual judge engine never processes raw prompt text.
        """
        normalized = self.normalize_unicode(text)
        matches = []
        for pattern in self._context_patterns:
            if pattern.search(normalized):
                matches.append(pattern.pattern)

        detected = len(matches) > 0
        confidence = min(len(matches) * 0.25, 1.0) if detected else 0.0
        return detected, confidence, "|".join(matches) if matches else ""

    def detect_indirect_tool_chaining(
        self,
        tool_calls: List[str],
        session_window: Optional[List[str]] = None,
    ) -> tuple[bool, float, str]:
        """Detect indirect tool chaining / separator attacks.

        Looks for suspicious sequences of tool calls within a session window.
        """
        all_calls = list(tool_calls)
        if session_window:
            all_calls.extend(session_window)

        if len(all_calls) < 2:
            return False, 0.0, ""

        # Check for known suspicious chain signatures
        matches = []
        for i in range(len(all_calls) - 1):
            call_a = all_calls[i].lower()
            call_b = all_calls[i + 1].lower()

            for sig_a, sig_b in _TOOL_CHAIN_SIGNATURES:
                if re.search(sig_a, call_a) and re.search(sig_b, call_b):
                    matches.append(f"{call_a[:30]}→{call_b[:30]}")

        detected = len(matches) > 0
        confidence = min(len(matches) * 0.3, 1.0) if detected else 0.0
        return detected, confidence, "|".join(matches) if matches else ""

    def detect_unicode_homoglyph(self, text: str) -> tuple[bool, float, str]:
        """Detect Unicode homoglyph substitution.

        Applies NFKC normalization and checks if text changes significantly.
        Also counts known confusable characters.
        """
        normalized = self.normalize_unicode(text)

        # Count confusable characters in original
        confusable_count = sum(1 for c in text if c in _CONFUSABLE_MAP)
        total_chars = len(text)

        if total_chars == 0:
            return False, 0.0, ""

        # Detection: either significant confusable ratio OR normalization changed the text
        confusable_ratio = confusable_count / total_chars
        text_changed = text != unicodedata.normalize("NFKC", text)
        text_changed_further = unicodedata.normalize("NFKC", text) != normalized

        detected = confusable_count > 0 and (confusable_ratio > 0.05 or text_changed_further)
        confidence = min(confusable_ratio * 5, 1.0) if detected else 0.0
        details = f"confusables={confusable_count},ratio={confusable_ratio:.3f}"
        return detected, confidence, details

    def detect_confidence_hijacking(self, text: str) -> tuple[bool, float, str]:
        """Detect confidence hijacking / social engineering attempts.

        Binary enforcement: these patterns are flagged but the rule engine
        makes the actual decision. Confidence is advisory only.
        """
        normalized = self.normalize_unicode(text)
        matches = []
        for pattern in self._confidence_patterns:
            if pattern.search(normalized):
                matches.append(pattern.pattern)

        detected = len(matches) > 0
        confidence = min(len(matches) * 0.3, 1.0) if detected else 0.0
        return detected, confidence, "|".join(matches) if matches else ""

    def evaluate(
        self,
        text: str = "",
        tool_calls: Optional[List[str]] = None,
        session_window: Optional[List[str]] = None,
    ) -> BypassResult:
        """Run all bypass detection patterns.

        Returns a BypassResult with all detected patterns.
        """
        patterns_detected = []
        details = {}

        # Context window displacement
        cd_detected, cd_conf, cd_detail = self.detect_context_window_displacement(text)
        if cd_detected:
            patterns_detected.append("context_window_displacement")
            details["context_displacement"] = {"confidence": cd_conf, "matches": cd_detail}

        # Indirect tool chaining
        tc_detected, tc_conf, tc_detail = self.detect_indirect_tool_chaining(
            tool_calls or [], session_window
        )
        if tc_detected:
            patterns_detected.append("indirect_tool_chaining")
            details["tool_chaining"] = {"confidence": tc_conf, "matches": tc_detail}

        # Unicode homoglyph
        uh_detected, uh_conf, uh_detail = self.detect_unicode_homoglyph(text)
        if uh_detected:
            patterns_detected.append("unicode_homoglyph")
            details["homoglyph"] = {"confidence": uh_conf, "matches": uh_detail}

        # Confidence hijacking
        ch_detected, ch_conf, ch_detail = self.detect_confidence_hijacking(text)
        if ch_detected:
            patterns_detected.append("confidence_hijacking")
            details["confidence_hijacking"] = {"confidence": ch_conf, "matches": ch_detail}

        # Overall confidence is max of individual confidences
        all_confidences = [d.get("confidence", 0) for d in details.values()]
        overall_confidence = max(all_confidences) if all_confidences else 0.0

        return BypassResult(
            patterns_detected=patterns_detected,
            confidence=round(overall_confidence, 3),
            normalized_payload=self.normalize_unicode(text),
            details=details,
        )
