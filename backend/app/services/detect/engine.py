"""Anomaly Detection Engine.

Deterministic rule-based pattern matcher. Zero LLM calls.
Loads DetectionRule records from DB and matches them against normalized events.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.constants import INCIDENT_TYPES, IncidentSeverity
from app.services.detect.normalizer import PB_CES_Event


@dataclass
class DetectionResult:
    """Result of running the detection engine on an event."""

    incident_type: Optional[str] = None  # e.g., "AGT-DEL-001"
    incident_type_name: Optional[str] = None  # e.g., "Data Destruction"
    severity: str = "medium"
    confidence: float = 0.0  # 0.0 - 1.0
    anomaly_score: float = 0.0  # 0.0 - 100.0
    matched_rules: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    deterministic: bool = True
    category: str = "unknown"


# --- Static rule definitions (fallback when DB is empty or for bootstrapping) ---

_STATIC_RULES: List[Dict[str, any]] = [
    {
        "rule_id": "RULE-DEL-001",
        "name": "Data Destruction Pattern",
        "incident_type": "AGT-DEL-001",
        "severity": "critical",
        "patterns": [
            r"DROP\s+TABLE",
            r"DELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1",
            r"TRUNCATE\s+TABLE",
            r"rm\s+-rf",
            r"shred\s+-",
            r"del\s+/[fqs]",
        ],
        "threshold": 0.6,
    },
    {
        "rule_id": "RULE-FIN-002",
        "name": "Unauthorized Financial Action",
        "incident_type": "AGT-FIN-002",
        "severity": "critical",
        "patterns": [
            r"transfer\s*\$?\d+[\d,]*\.?\d*",
            r"wire\s*transfer",
            r"swift\s*payment",
            r"bank\s*account\s*\d+",
            r"credit\s*card\s*\d{4}[\s-]?\d{4}",
            r"bitcoin\s*address",
            r"wallet\s*0x[a-fA-F0-9]{40}",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-PER-003",
        "name": "Permission Escalation",
        "incident_type": "AGT-PER-003",
        "severity": "high",
        "patterns": [
            r"sudo\s+",
            r"chmod\s+777",
            r"chown\s+root",
            r"setuid",
            r"privilege\s*escalation",
            r"escalate\s*privileges",
            r"grant\s+all\s+privileges",
            r"ROLE\s+ADMIN",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-HRM-004",
        "name": "Harmful Output Generation",
        "incident_type": "AGT-HRM-004",
        "severity": "high",
        "patterns": [
            r"bomb\s*making",
            r"weapon\s*instructions",
            r"poison\s*recipe",
            r"self.?harm",
            r"suicide\s*method",
            r"hate\s*speech",
            r"child\s*exploitation",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-EXT-005",
        "name": "Data Exfiltration",
        "incident_type": "AGT-EXT-005",
        "severity": "critical",
        "patterns": [
            r"scp\s+.*@",
            r"rsync\s+.*:\s*/",
            r"curl\s+.*https?://.*\s+-d",
            r"wget\s+.*\s+-O\s+\-",
            r"base64\s+.*\|\s*curl",
            r"dns\s*exfiltration",
            r"pastebin",
            r"gist\.github\.com",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-INJ-006",
        "name": "Prompt Injection",
        "incident_type": "AGT-INJ-006",
        "severity": "high",
        "patterns": [
            r"ignore\s+previous\s+instructions",
            r"disregard\s+all\s+prior",
            r"DAN\s*mode",
            r"jailbreak",
            r"system\s*override",
            r"you\s+are\s+now\s+\w+",
            r"new\s*persona",
            r"developer\s*mode",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-HAL-007",
        "name": "Hallucination Cascade",
        "incident_type": "AGT-HAL-007",
        "severity": "medium",
        "patterns": [
            r"I\s+apologize,?\s+but\s+I\s+cannot",
            r"I\s+don\'t\s+have\s+access\s+to",
            r"conflicting\s+information",
            r"cascade\s*failure",
            r"recursive\s*error",
            r"inconsistent\s*output",
        ],
        "threshold": 0.6,
    },
    {
        "rule_id": "RULE-CRE-008",
        "name": "Credential Exposure",
        "incident_type": "AGT-CRE-008",
        "severity": "critical",
        "patterns": [
            r"password\s*[:=]\s*\S+",
            r"api[_-]?key\s*[:=]\s*\S+",
            r"secret\s*[:=]\s*\S+",
            r"token\s*[:=]\s*\S+",
            r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----",
            r"AKIA[0-9A-Z]{16}",  # AWS Access Key
            r"gh[pousr]_[A-Za-z0-9_]{36}",  # GitHub token
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-RAT-009",
        "name": "Rate Limit Abuse",
        "incident_type": "AGT-RAT-009",
        "severity": "medium",
        "patterns": [
            r"rate\s*limit\s*exceeded",
            r"429\s+Too\s+Many\s+Requests",
            r"throttle",
            r"burst\s*limit",
            r"quota\s*exceeded",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-DRF-010",
        "name": "Model Drift",
        "incident_type": "AGT-DRF-010",
        "severity": "medium",
        "patterns": [
            r"model\s*drift",
            r"distribution\s*shift",
            r"KL\s*divergence\s*>",
            r"accuracy\s*degradation",
            r"prediction\s*variance",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-TLM-011",
        "name": "Tool Misuse",
        "incident_type": "AGT-TLM-011",
        "severity": "high",
        "patterns": [
            r"tool\s*misuse",
            r"unauthorized\s*tool",
            r"function\s+not\s+allowed",
            r"schema\s*violation",
            r"parameter\s*injection",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-GAP-012",
        "name": "Coverage Gap",
        "incident_type": "AGT-GAP-012",
        "severity": "low",
        "patterns": [
            r"uncategorized\s*event",
            r"unknown\s*action",
            r"no\s*policy\s*match",
            r"unhandled\s*exception",
        ],
        "threshold": 0.7,
    },
    {
        "rule_id": "RULE-SPY-013",
        "name": "Systematic Espionage",
        "incident_type": "AGT-SPY-013",
        "severity": "critical",
        "patterns": [
            r"reconnaissance",
            r"port\s*scan",
            r"nmap\s+-",
            r"masscan",
            r"enumerate\s*users",
            r"directory\s*listing",
            r"\.git\s+exposed",
            r"\.env\s+exposed",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-BYP-014",
        "name": "Guardrail Bypass",
        "incident_type": "AGT-BYP-014",
        "severity": "high",
        "patterns": [
            r"bypass\s*guardrail",
            r"context\s*window\s*displacement",
            r"indirect\s*tool\s*chaining",
            r"homoglyph",
            r"confidence\s*hijacking",
            r"unicode\s*spoof",
            r"token\s*smuggling",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-PRV-015",
        "name": "Privacy Violation",
        "incident_type": "AGT-PRV-015",
        "severity": "high",
        "patterns": [
            r"PII\s*detected",
            r"SSN\s*\d{3}-\d{2}-\d{4}",
            r"email\s*:\s*\S+@\S+",
            r"phone\s*:\s*\d{3}-\d{3}-\d{4}",
            r"GDPR\s*violation",
            r"HIPAA\s*breach",
            r"unauthorized\s*data\s*access",
        ],
        "threshold": 0.5,
    },
    {
        "rule_id": "RULE-REG-016",
        "name": "Regulatory Trigger",
        "incident_type": "AGT-REG-016",
        "severity": "high",
        "patterns": [
            r"regulatory\s*violation",
            r"compliance\s*breach",
            r"audit\s*failure",
            r"SOX\s*violation",
            r"PCI\s*DSS\s*failure",
        ],
        "threshold": 0.5,
    },
]


# Compile regex patterns once at module load
for rule in _STATIC_RULES:
    rule["_compiled"] = [re.compile(p, re.IGNORECASE) for p in rule["patterns"]]


class DetectionEngine:
    """Deterministic anomaly detection engine.

    Matches events against a library of detection rules and returns
    classification results with confidence scores.

    Usage:
        engine = DetectionEngine()
        result = engine.evaluate(event)
    """

    def __init__(self, rules: Optional[List[Dict]] = None):
        """Initialize with optional custom rules.

        Args:
            rules: Optional list of rule dicts. If None, uses static bootstrap rules.
        """
        self._rules = rules if rules is not None else list(_STATIC_RULES)
        # Ensure compiled patterns
        for rule in self._rules:
            if "_compiled" not in rule:
                rule["_compiled"] = [
                    re.compile(p, re.IGNORECASE) for p in rule.get("patterns", [])
                ]

    async def load_rules_from_db(self, db) -> int:
        """Load active detection rules from the database.

        Replaces static rules with DB rules. Returns number of rules loaded.

        Args:
            db: Async SQLAlchemy session.
        """
        from sqlalchemy import select
        from app.models import DetectionRule

        result = await db.execute(
            select(DetectionRule).where(DetectionRule.is_active == True)
        )
        db_rules = result.scalars().all()

        if not db_rules:
            return 0

        new_rules = []
        for rule in db_rules:
            # Split stored pipe-delimited pattern into individual patterns
            patterns = [p.strip() for p in rule.pattern.split("|") if p.strip()]
            new_rules.append({
                "rule_id": rule.rule_id,
                "name": rule.name,
                "incident_type": rule.incident_type,
                "severity": rule.severity,
                "patterns": patterns,
                "threshold": rule.threshold or 0.5,
                "is_active": rule.is_active,
                "_compiled": [re.compile(p, re.IGNORECASE) for p in patterns],
            })

        self._rules = new_rules
        return len(new_rules)

    def evaluate(self, event: PB_CES_Event) -> DetectionResult:
        """Evaluate a single event against all rules.

        Returns the best matching incident type with confidence score.
        Latency is measured and included in the result.
        """
        start = time.perf_counter()

        # Text to match against
        haystack = f"{event.tool_call} {event.output} {event.judge_decision} {event.context}"
        haystack_lower = haystack.lower()

        best_match: Optional[Dict] = None
        best_score = 0.0
        best_matched_patterns: List[str] = []

        for rule in self._rules:
            if not rule.get("is_active", True):
                continue

            matched = []
            match_count = 0
            for pattern in rule.get("_compiled", []):
                if pattern.search(haystack):
                    match_count += 1
                    matched.append(pattern.pattern)

            total_patterns = len(rule.get("patterns", []))
            if total_patterns == 0:
                continue

            score = 1.0 if match_count > 0 else 0.0
            threshold = rule.get("threshold", 0.5)

            if score >= threshold and score > best_score:
                best_score = score
                best_match = rule
                best_matched_patterns = matched

        latency_ms = (time.perf_counter() - start) * 1000

        if best_match is None:
            return DetectionResult(
                latency_ms=latency_ms,
                deterministic=True,
                category="unknown",
            )

        incident_type = best_match["incident_type"]
        incident_type_name = INCIDENT_TYPES.get(incident_type, "Unknown")
        severity = best_match.get("severity", "medium")
        confidence = round(best_score, 3)
        anomaly_score = min(confidence * 100, 100.0)

        # Map incident type prefix to category
        category_map = {
            "AGT-DEL": "integrity",
            "AGT-FIN": "financial",
            "AGT-PER": "access",
            "AGT-HRM": "safety",
            "AGT-EXT": "exfiltration",
            "AGT-INJ": "injection",
            "AGT-HAL": "reliability",
            "AGT-CRE": "secrets",
            "AGT-RAT": "availability",
            "AGT-DRF": "model",
            "AGT-TLM": "misuse",
            "AGT-GAP": "coverage",
            "AGT-SPY": "reconnaissance",
            "AGT-BYP": "bypass",
            "AGT-PRV": "privacy",
            "AGT-REG": "compliance",
        }
        prefix = incident_type.rsplit("-", 1)[0] if "-" in incident_type else incident_type
        category = category_map.get(prefix, "unknown")

        return DetectionResult(
            incident_type=incident_type,
            incident_type_name=incident_type_name,
            severity=severity,
            confidence=confidence,
            anomaly_score=round(anomaly_score, 2),
            matched_rules=[best_match["rule_id"]],
            matched_patterns=best_matched_patterns,
            latency_ms=round(latency_ms, 3),
            deterministic=True,
            category=category,
        )

    def evaluate_batch(self, events: List[PB_CES_Event]) -> List[DetectionResult]:
        """Evaluate multiple events efficiently."""
        return [self.evaluate(evt) for evt in events]
