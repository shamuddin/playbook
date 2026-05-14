"""Deterministic Judge Evaluation Engine.

The core of PLAYBOOK's enforcement layer. Zero LLM calls.
Operates on structured metadata to render ALLOW/DENY/QUARANTINE/ESCALATE verdicts.
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import INCIDENT_TYPES, JudgeVerdict
from app.models import NistBaseline, OrganizationODP


@dataclass
class JudgeInput:
    """Structured input for the Judge Layer.

    All fields are typed (bools, ints, enums) — never raw natural language.
    This makes the judge immune to context-window displacement attacks.
    """

    action: str = ""
    agent_id: str = "unknown"
    session_id: str = ""
    incident_type: str = "AGT-GAP-012"
    severity: str = "medium"  # low, medium, high, critical
    confidence: float = 0.0

    # Auth context
    auth_present: bool = False
    dual_auth_present: bool = False
    is_repeat_offender: bool = False

    # Content signals (booleans from metadata)
    contains_pii: bool = False
    contains_credentials: bool = False
    contains_injection_patterns: bool = False
    contains_system_commands: bool = False
    contains_exfiltration: bool = False

    # Environment
    is_business_hours: bool = True
    source_ip_reputation: str = "unknown"  # trusted, unknown, suspicious, malicious

    # Policy context
    organization_id: str = "default"
    department: str = "default"

    # Raw metadata for enrichment (not used in decision)
    metadata: Dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class JudgeResult:
    """Output of the Judge evaluation."""

    verdict: str = JudgeVerdict.ALLOW
    severity_score: int = 1  # 1–10
    confidence: float = 1.0
    matched_rules: List[str] = field(default_factory=list)
    bypass_patterns_detected: List[str] = field(default_factory=list)
    rationale: str = ""
    latency_ms: float = 0.0
    resolved_policy_id: Optional[str] = None
    odp_overrides: Dict[str, Any] = field(default_factory=dict)
    regulatory_tags: List[str] = field(default_factory=list)


class JudgeEngine:
    """Deterministic judge evaluation engine.

    Usage:
        engine = JudgeEngine()
        result = await engine.evaluate(db, judge_input)
    """

    # Base severity scores (1-10 scale)
    _SEVERITY_BASE = {
        "low": 3,
        "medium": 5,
        "high": 7,
        "critical": 9,
    }

    # Source IP reputation modifiers
    _IP_REPUTATION_MODIFIERS = {
        "trusted": -1,
        "unknown": 0,
        "suspicious": 2,
        "malicious": 4,
    }

    # Regulatory tag mappings by incident type
    _REGULATORY_TAGS = {
        "AGT-DEL-001": ["EU_AI_ACT_ART_9", "NIST_AI_RMF_GOVERN_3"],
        "AGT-FIN-002": ["PCI_DSS_10_2", "SOX_302"],
        "AGT-PER-003": ["NIST_AI_RMF_GOVERN_2", "ISO_27001_A_9_2"],
        "AGT-HRM-004": ["EU_AI_ACT_ART_52", "NIST_AI_RMF_MAP_1_2"],
        "AGT-EXT-005": ["GDPR_ART_32", "HIPAA_164_312"],
        "AGT-INJ-006": ["OWASP_LLM_01", "NIST_AI_RMF_MEASURE_2_1"],
        "AGT-HAL-007": ["EU_AI_ACT_ART_10", "NIST_AI_RMF_MEASURE_1_1"],
        "AGT-CRE-008": ["NIST_AI_RMF_GOVERN_1_2", "ISO_27001_A_9_4"],
        "AGT-RAT-009": ["NIST_AI_RMF_MEASURE_2_9", "PCI_DSS_6_6"],
        "AGT-DRF-010": ["EU_AI_ACT_ART_14", "NIST_AI_RMF_MEASURE_3_2"],
        "AGT-TLM-011": ["OWASP_LLM_06", "NIST_AI_RMF_GOVERN_3_1"],
        "AGT-GAP-012": ["NIST_AI_RMF_GOVERN_4", "ISO_27001_A_12_6"],
        "AGT-SPY-013": ["GDPR_ART_32", "NIST_AI_RMF_MAP_1_3"],
        "AGT-BYP-014": ["OWASP_LLM_02", "NIST_AI_RMF_MEASURE_2_10"],
        "AGT-PRV-015": ["GDPR_ART_5", "HIPAA_164_502", "CCPA_1798_100"],
        "AGT-REG-016": ["SOX_404", "GDPR_ART_33", "NIST_AI_RMF_GOVERN_5"],
        "AGT-POL-017": ["NIST_AI_RMF_GOVERN_1", "ISO_27001_A_5", "NIST_SP_800_53_AC_1"],
    }

    async def _resolve_odp(
        self, db: AsyncSession, incident_type: str
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """Resolve effective policy for an incident type.

        Returns (baseline_id, effective_policy_dict).
        """
        # Load NIST baseline
        baseline_result = await db.execute(
            select(NistBaseline).where(
                NistBaseline.incident_type == incident_type,
                NistBaseline.is_active == True,
            )
        )
        baseline = baseline_result.scalar_one_or_none()

        if baseline is None:
            return None, {}

        # Build effective policy from baseline
        effective = {
            "severity_threshold": baseline.severity_threshold,
            "auto_contain_enabled": baseline.auto_contain_enabled,
            "escalation_contacts": baseline.escalation_contacts,
            "response_time_sla_seconds": baseline.response_time_sla_seconds,
            "forensic_level": baseline.forensic_level,
            "notify_targets": baseline.notify_targets,
            "compliance_report": baseline.compliance_report,
            "record_threshold": baseline.record_threshold,
        }

        # Load ODP overrides
        odp_result = await db.execute(
            select(OrganizationODP).where(
                OrganizationODP.baseline_id == baseline.id,
                OrganizationODP.is_active == True,
            )
        )
        odps = odp_result.scalars().all()

        odp_overrides = {}
        for odp in odps:
            effective[odp.odp_key] = odp.odp_value
            odp_overrides[odp.odp_key] = odp.odp_value

        return baseline.id, effective

    def _calculate_severity_score(self, input_data: JudgeInput) -> int:
        """Calculate severity score (1–10) with modifiers."""
        base = self._SEVERITY_BASE.get(input_data.severity.lower(), 5)

        modifiers = 0
        if input_data.is_repeat_offender:
            modifiers += 2
        if input_data.dual_auth_present:
            modifiers -= 2
        if not input_data.auth_present:
            modifiers += 3
        if input_data.is_business_hours:
            modifiers -= 1

        # Content signal modifiers
        if input_data.contains_credentials:
            modifiers += 2
        if input_data.contains_exfiltration:
            modifiers += 2
        if input_data.contains_injection_patterns:
            modifiers += 1
        if input_data.contains_system_commands:
            modifiers += 1

        # IP reputation modifier
        modifiers += self._IP_REPUTATION_MODIFIERS.get(
            input_data.source_ip_reputation, 0
        )

        # Clamp to 1–10
        return max(1, min(10, base + modifiers))

    def _render_decision(self, severity_score: int, auth_present: bool) -> str:
        """Render final verdict from severity score and auth context.

        Decision matrix:
        - Severity 1–3 → ALLOW
        - Severity 4–6 + valid auth → ALLOW with logging
        - Severity 4–6 + missing auth → QUARANTINE
        - Severity 7–8 → QUARANTINE or ESCALATE
        - Severity 9–10 → DENY or ESCALATE
        """
        if severity_score <= 3:
            return JudgeVerdict.ALLOW
        elif severity_score <= 6:
            return JudgeVerdict.ALLOW if auth_present else JudgeVerdict.QUARANTINE
        elif severity_score <= 8:
            return JudgeVerdict.QUARANTINE
        else:
            return JudgeVerdict.DENY

    async def evaluate(
        self,
        db: AsyncSession,
        input_data: JudgeInput,
        bypass_patterns: Optional[List[str]] = None,
    ) -> JudgeResult:
        """Evaluate a proposed action and render a deterministic verdict.

        Args:
            db: Async database session
            input_data: Structured judge input
            bypass_patterns: Optional list of already-detected bypass patterns

        Returns:
            JudgeResult with verdict, severity score, rationale, etc.

        Fail-closed: any exception returns ESCALATE.
        """
        start = time.perf_counter()
        try:
            return await self._evaluate_inner(db, input_data, bypass_patterns)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            return JudgeResult(
                verdict=JudgeVerdict.ESCALATE,
                severity_score=10,
                confidence=1.0,
                matched_rules=["fail_closed"],
                bypass_patterns_detected=bypass_patterns or [],
                rationale=f"Exception during judge evaluation: {exc}",
                latency_ms=round(latency_ms, 3),
            )

    async def _evaluate_inner(
        self,
        db: AsyncSession,
        input_data: JudgeInput,
        bypass_patterns: Optional[List[str]] = None,
    ) -> JudgeResult:
        """Core evaluation logic (wrapped by evaluate for fail-closed)."""
        start = time.perf_counter()
        matched_rules = []
        rationale_parts = []

        # Step 1: ODP Resolution
        baseline_id, effective_policy = await self._resolve_odp(
            db, input_data.incident_type
        )

        if effective_policy:
            matched_rules.append("odp_resolution")
            rationale_parts.append(
                f"Resolved policy for {input_data.incident_type} "
                f"(auto_contain={effective_policy.get('auto_contain_enabled', False)})"
            )

        # Step 2: Severity scoring
        severity_score = self._calculate_severity_score(input_data)
        matched_rules.append(f"severity_score:{severity_score}")
        rationale_parts.append(f"Severity score: {severity_score}/10")

        # Step 3: Bypass pattern impact
        bypass_detected = bypass_patterns or []
        if bypass_detected:
            matched_rules.extend([f"bypass:{p}" for p in bypass_detected])
            rationale_parts.append(f"Bypass patterns detected: {', '.join(bypass_detected)}")
            # Bypass attempts escalate severity
            severity_score = min(10, severity_score + 2)
            rationale_parts.append(f"Severity escalated to {severity_score} due to bypass attempt")

        # Step 4: Render decision
        verdict = self._render_decision(severity_score, input_data.auth_present)

        # Step 5: Override with ESCALATE if auto_contain is enabled and severity is high
        if effective_policy.get("auto_contain_enabled") and severity_score >= 7:
            if verdict == JudgeVerdict.ALLOW:
                verdict = JudgeVerdict.QUARANTINE
                rationale_parts.append("Auto-contain policy elevated verdict to QUARANTINE")

        # Step 6: Regulatory tags
        regulatory_tags = self._REGULATORY_TAGS.get(input_data.incident_type, [])

        latency_ms = (time.perf_counter() - start) * 1000

        rationale = "; ".join(rationale_parts)
        rationale += f"; Verdict: {verdict}"
        if not rationale_parts:
            rationale = f"Default verdict {verdict} for severity {severity_score}"

        return JudgeResult(
            verdict=verdict,
            severity_score=severity_score,
            confidence=1.0,  # Deterministic — always 1.0
            matched_rules=matched_rules,
            bypass_patterns_detected=bypass_detected,
            rationale=rationale,
            latency_ms=round(latency_ms, 3),
            resolved_policy_id=baseline_id,
            odp_overrides=effective_policy,
            regulatory_tags=regulatory_tags,
        )
