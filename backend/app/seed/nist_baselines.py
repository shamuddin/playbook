"""Seed data for NistBaseline table.

Default NIST baselines for all 16 incident types with standard ODP values.
"""

from app.core.constants import INCIDENT_TYPES, IncidentSeverity


def _build_baselines() -> list[dict]:
    """Generate NIST baseline seed data."""
    baselines = []

    severity_map = {
        "AGT-DEL-001": IncidentSeverity.CRITICAL,
        "AGT-FIN-002": IncidentSeverity.CRITICAL,
        "AGT-PER-003": IncidentSeverity.HIGH,
        "AGT-HRM-004": IncidentSeverity.HIGH,
        "AGT-EXT-005": IncidentSeverity.CRITICAL,
        "AGT-INJ-006": IncidentSeverity.HIGH,
        "AGT-HAL-007": IncidentSeverity.MEDIUM,
        "AGT-CRE-008": IncidentSeverity.CRITICAL,
        "AGT-RAT-009": IncidentSeverity.MEDIUM,
        "AGT-DRF-010": IncidentSeverity.MEDIUM,
        "AGT-TLM-011": IncidentSeverity.HIGH,
        "AGT-GAP-012": IncidentSeverity.LOW,
        "AGT-SPY-013": IncidentSeverity.CRITICAL,
        "AGT-BYP-014": IncidentSeverity.HIGH,
        "AGT-PRV-015": IncidentSeverity.HIGH,
        "AGT-REG-016": IncidentSeverity.HIGH,
    }

    auto_contain_map = {
        IncidentSeverity.CRITICAL: True,
        IncidentSeverity.HIGH: True,
        IncidentSeverity.MEDIUM: False,
        IncidentSeverity.LOW: False,
    }

    for code, name in INCIDENT_TYPES.items():
        severity = severity_map.get(code, IncidentSeverity.MEDIUM)
        baselines.append({
            "baseline_id": f"NIST-{code}",
            "incident_type": code,
            "version": "1.0",
            "severity": severity,
            "severity_threshold": severity,
            "auto_contain_enabled": auto_contain_map.get(severity, False),
            "escalation_contacts": ["security@example.com"],
            "response_time_sla_seconds": 1800 if severity == IncidentSeverity.CRITICAL else 3600,
            "forensic_level": "deep" if severity == IncidentSeverity.CRITICAL else "standard",
            "notify_targets": ["#security-alerts", "#incident-response"],
            "compliance_report": severity in (IncidentSeverity.CRITICAL, IncidentSeverity.HIGH),
            "record_threshold": 1,
            "description": f"NIST baseline for {name} ({code}).",
            "is_active": True,
        })

    return baselines


NIST_BASELINES_SEED = _build_baselines()
