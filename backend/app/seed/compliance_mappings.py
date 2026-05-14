"""Seed data for ComplianceMapping table."""

COMPLIANCE_MAPPINGS_SEED = [
    # EU AI Act mappings
    {"incident_type": "AGT-DEL-001", "framework": "eu_ai_act", "control_id": "Art.9", "control_name": "Risk Management System", "risk_level": "critical", "confidence": 1.0},
    {"incident_type": "AGT-DEL-001", "framework": "eu_ai_act", "control_id": "Art.15", "control_name": "Accuracy, Robustness, Cybersecurity", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-FIN-002", "framework": "eu_ai_act", "control_id": "Art.52", "control_name": "Transparency Obligations", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-EXT-005", "framework": "eu_ai_act", "control_id": "Art.9", "control_name": "Risk Management System", "risk_level": "critical", "confidence": 1.0},
    {"incident_type": "AGT-EXT-005", "framework": "eu_ai_act", "control_id": "Art.73", "control_name": "Reporting of Serious Incidents", "risk_level": "critical", "confidence": 1.0},
    {"incident_type": "AGT-INJ-006", "framework": "eu_ai_act", "control_id": "Art.15", "control_name": "Accuracy, Robustness, Cybersecurity", "risk_level": "high", "confidence": 0.95},
    {"incident_type": "AGT-HAL-007", "framework": "eu_ai_act", "control_id": "Art.10", "control_name": "Data and Data Governance", "risk_level": "medium", "confidence": 0.8},
    {"incident_type": "AGT-CRE-008", "framework": "eu_ai_act", "control_id": "Art.15", "control_name": "Accuracy, Robustness, Cybersecurity", "risk_level": "critical", "confidence": 0.95},
    {"incident_type": "AGT-PRV-015", "framework": "eu_ai_act", "control_id": "Art.5", "control_name": "Prohibited AI Practices", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-REG-016", "framework": "eu_ai_act", "control_id": "Art.73", "control_name": "Reporting of Serious Incidents", "risk_level": "high", "confidence": 0.9},

    # NIST AI RMF mappings
    {"incident_type": "AGT-DEL-001", "framework": "nist_ai_rmf", "control_id": "GOVERN-3", "control_name": "Risk Management Culture", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-DEL-001", "framework": "nist_ai_rmf", "control_id": "MAP-1.6", "control_name": "Impacts of AI on Individuals", "risk_level": "high", "confidence": 0.85},
    {"incident_type": "AGT-FIN-002", "framework": "nist_ai_rmf", "control_id": "GOVERN-2", "control_name": "Accountability Structures", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-EXT-005", "framework": "nist_ai_rmf", "control_id": "GOVERN-1.2", "control_name": "Legal and Regulatory Requirements", "risk_level": "critical", "confidence": 0.95},
    {"incident_type": "AGT-EXT-005", "framework": "nist_ai_rmf", "control_id": "MAP-1.3", "control_name": "AI System Categorization", "risk_level": "high", "confidence": 0.85},
    {"incident_type": "AGT-INJ-006", "framework": "nist_ai_rmf", "control_id": "MEASURE-2.1", "control_name": "Test Sets and Metrics", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-HAL-007", "framework": "nist_ai_rmf", "control_id": "MEASURE-1.1", "control_name": "Appropriate Data Collection", "risk_level": "medium", "confidence": 0.8},
    {"incident_type": "AGT-CRE-008", "framework": "nist_ai_rmf", "control_id": "GOVERN-1.2", "control_name": "Legal and Regulatory Requirements", "risk_level": "critical", "confidence": 0.95},
    {"incident_type": "AGT-BYP-014", "framework": "nist_ai_rmf", "control_id": "MEASURE-2.10", "control_name": "Adversarial Testing", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-PRV-015", "framework": "nist_ai_rmf", "control_id": "GOVERN-5", "control_name": "Policies for Third-Party Risks", "risk_level": "high", "confidence": 0.85},

    # HIPAA mappings
    {"incident_type": "AGT-EXT-005", "framework": "hipaa", "control_id": "164.312", "control_name": "Technical Safeguards", "risk_level": "critical", "confidence": 0.95},
    {"incident_type": "AGT-CRE-008", "framework": "hipaa", "control_id": "164.312(a)(2)(iv)", "control_name": "Encryption and Decryption", "risk_level": "critical", "confidence": 0.95},
    {"incident_type": "AGT-PRV-015", "framework": "hipaa", "control_id": "164.502", "control_name": "Uses and Disclosures", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-PRV-015", "framework": "hipaa", "control_id": "164.530", "control_name": "Administrative Requirements", "risk_level": "medium", "confidence": 0.8},

    # SOC2 mappings
    {"incident_type": "AGT-DEL-001", "framework": "soc2", "control_id": "CC6.1", "control_name": "Logical Access Security", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-FIN-002", "framework": "soc2", "control_id": "CC7.2", "control_name": "System Monitoring", "risk_level": "high", "confidence": 0.85},
    {"incident_type": "AGT-EXT-005", "framework": "soc2", "control_id": "CC7.1", "control_name": "Detect Security Events", "risk_level": "critical", "confidence": 0.95},
    {"incident_type": "AGT-REG-016", "framework": "soc2", "control_id": "CC1.3", "control_name": "Management Communication", "risk_level": "high", "confidence": 0.85},

    # Policy Switching demo mappings
    {"incident_type": "AGT-POL-017", "framework": "nist_ai_rmf", "control_id": "GOVERN-1", "control_name": "Policies and Procedures", "risk_level": "high", "confidence": 0.9},
    {"incident_type": "AGT-POL-017", "framework": "nist_sp_800_53", "control_id": "AC-1", "control_name": "Access Control Policy and Procedures", "risk_level": "high", "confidence": 0.85},
    {"incident_type": "AGT-POL-017", "framework": "soc2", "control_id": "CC5.1", "control_name": "Control Environment", "risk_level": "medium", "confidence": 0.8},
]
