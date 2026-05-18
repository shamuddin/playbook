"""Seed data for Playbook and PlaybookAction tables.

One playbook per incident type with appropriate response actions.
"""

from app.core.constants import INCIDENT_TYPES, PlaybookActionType, IncidentSeverity


# Action templates by severity
SEVERITY_ACTIONS = {
    IncidentSeverity.CRITICAL: [
        {"step_order": 1, "name": "Log Extended", "action_type": PlaybookActionType.LOG_EXTENDED, "timeout_seconds": 10, "parameters": {}},
        {"step_order": 2, "name": "Isolate Agent", "action_type": PlaybookActionType.ISOLATE, "timeout_seconds": 30, "parameters": {}},
        {"step_order": 3, "name": "Notify Security Team", "action_type": PlaybookActionType.NOTIFY, "timeout_seconds": 15, "parameters": {"channels": ["email"]}},
        {"step_order": 4, "name": "Capture Forensics", "action_type": PlaybookActionType.FORENSICS, "timeout_seconds": 60, "parameters": {}},
        {"step_order": 5, "name": "Human Review", "action_type": PlaybookActionType.HUMAN_REVIEW, "timeout_seconds": 1800, "parameters": {}},
    ],
    IncidentSeverity.HIGH: [
        {"step_order": 1, "name": "Log Extended", "action_type": PlaybookActionType.LOG_EXTENDED, "timeout_seconds": 10, "parameters": {}},
        {"step_order": 2, "name": "Quarantine Agent", "action_type": PlaybookActionType.QUARANTINE, "timeout_seconds": 30, "parameters": {}},
        {"step_order": 3, "name": "Notify Team", "action_type": PlaybookActionType.NOTIFY, "timeout_seconds": 15, "parameters": {"channels": ["email"]}},
        {"step_order": 4, "name": "Capture Forensics", "action_type": PlaybookActionType.FORENSICS, "timeout_seconds": 60, "parameters": {}},
    ],
    IncidentSeverity.MEDIUM: [
        {"step_order": 1, "name": "Log Event", "action_type": PlaybookActionType.LOG_EXTENDED, "timeout_seconds": 10, "parameters": {}},
        {"step_order": 2, "name": "Rate Limit", "action_type": PlaybookActionType.RATE_LIMIT, "timeout_seconds": 15, "parameters": {}},
        {"step_order": 3, "name": "Notify", "action_type": PlaybookActionType.NOTIFY, "timeout_seconds": 15, "parameters": {"channels": ["email"]}},
    ],
    IncidentSeverity.LOW: [
        {"step_order": 1, "name": "Log Event", "action_type": PlaybookActionType.LOG_EXTENDED, "timeout_seconds": 10, "parameters": {}},
    ],
}


def _build_playbooks() -> list[dict]:
    """Generate playbook seed data for all 16 incident types."""
    playbooks = []

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
        "AGT-POL-017": IncidentSeverity.CRITICAL,
    }

    for code, name in INCIDENT_TYPES.items():
        severity = severity_map.get(code, IncidentSeverity.MEDIUM)
        playbook_id = f"PB-{code}"

        playbooks.append({
            "playbook_id": playbook_id,
            "name": f"Respond to {name}",
            "incident_type": code,
            "description": f"Automated response playbook for {name} incidents ({code}).",
            "version": "1.0",
            "auto_execute": severity in (IncidentSeverity.CRITICAL, IncidentSeverity.HIGH),
            "is_active": True,
            "actions": SEVERITY_ACTIONS.get(severity, SEVERITY_ACTIONS[IncidentSeverity.MEDIUM]),
        })

    return playbooks


PLAYBOOKS_SEED = _build_playbooks()
