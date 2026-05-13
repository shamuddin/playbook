"""Idempotent seeding of all reference data.

Called on startup when DEMO_MODE or SEED_ON_STARTUP is enabled.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DetectionRule, NistBaseline, Playbook, PlaybookAction
from app.seed.detection_rules import DETECTION_RULES_SEED
from app.seed.nist_baselines import NIST_BASELINES_SEED
from app.seed.playbooks import PLAYBOOKS_SEED

logger = logging.getLogger(__name__)


async def _seed_detection_rules(db: AsyncSession) -> int:
    """Seed detection rules if none exist."""
    result = await db.execute(select(DetectionRule).limit(1))
    if result.scalar_one_or_none() is not None:
        logger.info("DetectionRule records already exist, skipping seed")
        return 0

    count = 0
    for rule_data in DETECTION_RULES_SEED:
        rule = DetectionRule(
            rule_id=rule_data["rule_id"],
            name=rule_data["name"],
            rule_type=rule_data["rule_type"],
            severity=rule_data["severity"],
            incident_type=rule_data["incident_type"],
            pattern=rule_data["pattern"],
            threshold=rule_data["threshold"],
            is_active=rule_data["is_active"],
        )
        db.add(rule)
        count += 1

    await db.flush()
    logger.info(f"Seeded {count} detection rules")
    return count


async def _seed_playbooks(db: AsyncSession) -> int:
    """Seed playbooks and their actions if none exist."""
    result = await db.execute(select(Playbook).limit(1))
    if result.scalar_one_or_none() is not None:
        logger.info("Playbook records already exist, skipping seed")
        return 0

    count = 0
    for pb_data in PLAYBOOKS_SEED:
        playbook = Playbook(
            playbook_id=pb_data["playbook_id"],
            name=pb_data["name"],
            incident_type=pb_data["incident_type"],
            description=pb_data["description"],
            version=pb_data["version"],
            auto_execute=pb_data["auto_execute"],
            is_active=pb_data["is_active"],
        )
        db.add(playbook)
        await db.flush()  # Need ID for actions

        for action_data in pb_data["actions"]:
            action = PlaybookAction(
                playbook_id=playbook.id,
                step_order=action_data["step_order"],
                name=action_data["name"],
                action_type=action_data["action_type"],
                timeout_seconds=action_data["timeout_seconds"],
            )
            db.add(action)

        count += 1

    await db.flush()
    logger.info(f"Seeded {count} playbooks with actions")
    return count


async def _seed_nist_baselines(db: AsyncSession) -> int:
    """Seed NIST baselines if none exist."""
    result = await db.execute(select(NistBaseline).limit(1))
    if result.scalar_one_or_none() is not None:
        logger.info("NistBaseline records already exist, skipping seed")
        return 0

    count = 0
    for base_data in NIST_BASELINES_SEED:
        baseline = NistBaseline(
            baseline_id=base_data["baseline_id"],
            incident_type=base_data["incident_type"],
            version=base_data["version"],
            severity=base_data["severity"],
            severity_threshold=base_data["severity_threshold"],
            auto_contain_enabled=base_data["auto_contain_enabled"],
            escalation_contacts=base_data["escalation_contacts"],
            response_time_sla_seconds=base_data["response_time_sla_seconds"],
            forensic_level=base_data["forensic_level"],
            notify_targets=base_data["notify_targets"],
            compliance_report=base_data["compliance_report"],
            record_threshold=base_data["record_threshold"],
            description=base_data["description"],
            is_active=base_data["is_active"],
        )
        db.add(baseline)
        count += 1

    await db.flush()
    logger.info(f"Seeded {count} NIST baselines")
    return count


async def seed_all(db: AsyncSession) -> dict[str, int]:
    """Idempotently seed all reference data.

    Returns a dict of {table_name: count_seeded}.
    """
    results = {
        "detection_rules": await _seed_detection_rules(db),
        "playbooks": await _seed_playbooks(db),
        "nist_baselines": await _seed_nist_baselines(db),
    }
    await db.commit()
    return results
