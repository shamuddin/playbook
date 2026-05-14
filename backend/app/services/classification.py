"""Classification Bridge — transforms DetectionResult into JudgeInput.

Zero LLM calls. Purely deterministic metadata transformation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.core.constants import INCIDENT_TYPES
from app.services.detect.engine import DetectionResult


@dataclass
class ClassifiedIncident:
    """Output of the classification bridge."""

    incident_type: str
    incident_type_name: str
    severity: str
    confidence: float
    category: str
    playbook_id: str
    local_rule_id: str
    regulatory_tags: List[str] = field(default_factory=list)
    human_review_required: bool = False
    judge_input: Dict[str, Any] = field(default_factory=dict)


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


class ClassificationBridge:
    """Bridges detection results to structured judge inputs.

    Usage:
        bridge = ClassificationBridge()
        classified = bridge.classify(detection_result, metadata)
    """

    def classify(
        self,
        detection: DetectionResult,
        metadata: Dict[str, Any] = None,
    ) -> ClassifiedIncident:
        """Transform a DetectionResult into a ClassifiedIncident.

        Args:
            detection: Result from DetectionEngine.evaluate()
            metadata: Optional incident metadata dict

        Returns:
            ClassifiedIncident with all classification fields
        """
        metadata = metadata or {}
        incident_type = detection.incident_type or "AGT-GAP-012"
        incident_type_name = detection.incident_type_name or INCIDENT_TYPES.get(
            incident_type, "Unknown"
        )
        severity = detection.severity or "medium"
        confidence = detection.confidence
        category = detection.category or "unknown"
        local_rule_id = detection.matched_rules[0] if detection.matched_rules else ""

        # Auto-assign playbook
        playbook_id = f"PB-{incident_type}"

        # Determine if human review is required
        human_review_required = confidence < 0.70

        # Regulatory tags
        regulatory_tags = _REGULATORY_TAGS.get(incident_type, [])

        # Build judge input from metadata (23 fields)
        judge_input = {
            "incident_type": incident_type,
            "incident_type_name": incident_type_name,
            "severity": severity,
            "confidence": confidence,
            "category": category,
            "action": metadata.get("action", "unknown"),
            "agent_id": metadata.get("agent_id", "unknown"),
            "session_id": metadata.get("session_id", ""),
            "auth_present": metadata.get("auth_present", False),
            "dual_auth_present": metadata.get("dual_auth_present", False),
            "is_repeat_offender": metadata.get("is_repeat_offender", False),
            "contains_pii": metadata.get("contains_pii", False),
            "contains_credentials": metadata.get("contains_credentials", False),
            "contains_injection_patterns": metadata.get(
                "contains_injection_patterns", False
            ),
            "contains_system_commands": metadata.get("contains_system_commands", False),
            "contains_exfiltration": metadata.get("contains_exfiltration", False),
            "contains_harmful_content": metadata.get("contains_harmful_content", False),
            "contains_privacy_violation": metadata.get("contains_privacy_violation", False),
            "is_business_hours": metadata.get("is_business_hours", True),
            "source_ip_reputation": metadata.get("source_ip_reputation", "unknown"),
            "organization_id": metadata.get("organization_id", "default"),
            "department": metadata.get("department", "default"),
            "data_classification": metadata.get("data_classification", "internal"),
            "network_zone": metadata.get("network_zone", "internal"),
            "compliance_frameworks": metadata.get("compliance_frameworks", []),
        }

        return ClassifiedIncident(
            incident_type=incident_type,
            incident_type_name=incident_type_name,
            severity=severity,
            confidence=confidence,
            category=category,
            playbook_id=playbook_id,
            local_rule_id=local_rule_id,
            regulatory_tags=regulatory_tags,
            human_review_required=human_review_required,
            judge_input=judge_input,
        )
