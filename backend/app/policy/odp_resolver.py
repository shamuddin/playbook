"""ODP Resolver — merge organizational ODPs with NIST baselines.

Builds the effective policy by overlaying organizational overrides onto
NIST defaults, with proper type coercion for booleans, integers, and lists.
"""

import json
from typing import Any, Dict, List, Optional

from app.models import NistBaseline, OrganizationODP


class ODPResolver:
    """Resolve effective policy from baseline + ODP overrides."""

    # Type coercion map for known ODP keys
    _TYPE_MAP = {
        "auto_contain_enabled": bool,
        "compliance_report": bool,
        "response_time_sla_seconds": int,
        "record_threshold": int,
        "response_time_sla": int,
    }

    @staticmethod
    def build_effective_policy(
        baseline: NistBaseline,
        odps: List[OrganizationODP],
    ) -> Dict[str, Any]:
        """Build effective policy by overlaying ODPs onto baseline defaults.

        Returns a dict with properly typed values:
        - bool for toggles (auto_contain_enabled, compliance_report)
        - int for numeric thresholds (response_time_sla_seconds, record_threshold)
        - list for contact/target arrays (escalation_contacts, notify_targets)
        - str for everything else
        """
        effective: Dict[str, Any] = {
            "severity_threshold": baseline.severity_threshold,
            "auto_contain_enabled": baseline.auto_contain_enabled,
            "escalation_contacts": baseline.escalation_contacts,
            "response_time_sla_seconds": baseline.response_time_sla_seconds,
            "forensic_level": baseline.forensic_level,
            "notify_targets": baseline.notify_targets,
            "compliance_report": baseline.compliance_report,
            "record_threshold": baseline.record_threshold,
        }

        # Map ODP keys to effective policy keys
        key_map = {
            "response_time_sla": "response_time_sla_seconds",
        }

        for odp in odps:
            if not odp.is_active:
                continue
            target_key = key_map.get(odp.odp_key, odp.odp_key)
            effective[target_key] = ODPResolver.coerce_value(
                odp.odp_key, odp.odp_value
            )

        return effective

    @staticmethod
    def coerce_value(key: str, raw_value: str) -> Any:
        """Coerce an ODP string value to its proper Python type.

        Handles:
        - bool: "true"/"false" (case-insensitive)
        - int: numeric strings for SLA and thresholds
        - list: JSON array strings for contacts/targets
        - str: fallback for everything else
        """
        target_type = ODPResolver._TYPE_MAP.get(key)

        if target_type is bool:
            return raw_value.strip().lower() == "true"

        if target_type is int:
            try:
                return int(raw_value.strip())
            except (ValueError, TypeError):
                return raw_value

        # Try JSON list parsing for contact arrays
        if key in ("escalation_contacts", "notify_targets"):
            try:
                parsed = json.loads(raw_value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            # Fallback: comma-separated string
            return [v.strip() for v in raw_value.split(",") if v.strip()]

        return raw_value

    @staticmethod
    def build_odp_map(
        baseline: NistBaseline,
        odps: List[OrganizationODP],
    ) -> Dict[str, dict]:
        """Build a structured ODP map with override tracking.

        Returns a dict of {odp_key: {"value", "is_override", "nist_default", "value_type"}}.
        """
        defaults = ODPResolver.get_defaults(baseline)
        odp_map: Dict[str, dict] = {}

        for odp in odps:
            if not odp.is_active:
                continue
            nist_default = defaults.get(odp.odp_key)
            odp_map[odp.odp_key] = {
                "value": odp.odp_value,
                "is_override": odp.odp_value != nist_default if nist_default is not None else True,
                "nist_default": nist_default,
                "value_type": odp.value_type,
            }

        return odp_map

    @staticmethod
    def get_defaults(baseline: NistBaseline) -> Dict[str, str]:
        """Return canonical default values as strings for comparison."""
        return {
            "severity_threshold": baseline.severity_threshold,
            "auto_contain_enabled": str(baseline.auto_contain_enabled).lower(),
            "escalation_contacts": (
                json.dumps(baseline.escalation_contacts)
                if isinstance(baseline.escalation_contacts, list)
                else str(baseline.escalation_contacts)
            ),
            "response_time_sla": str(baseline.response_time_sla_seconds),
            "response_time_sla_seconds": str(baseline.response_time_sla_seconds),
            "forensic_level": baseline.forensic_level,
            "notify_targets": (
                json.dumps(baseline.notify_targets)
                if isinstance(baseline.notify_targets, list)
                else str(baseline.notify_targets)
            ),
            "compliance_report": str(baseline.compliance_report).lower(),
            "record_threshold": str(baseline.record_threshold),
        }
