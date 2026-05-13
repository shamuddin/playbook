"""NIST Baseline Loader — load and initialize NIST baseline policies.

Provides lookup by incident type, bulk loading, and default initialization
from seed data when baselines are missing from the database.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NistBaseline
from app.seed.nist_baselines import NIST_BASELINES_SEED


class BaselineLoader:
    """Load and manage NIST baseline policies."""

    @staticmethod
    async def get_by_incident_type(
        db: AsyncSession,
        incident_type: str,
    ) -> Optional[NistBaseline]:
        """Fetch a single active baseline by incident type code."""
        result = await db.execute(
            select(NistBaseline).where(
                NistBaseline.incident_type == incident_type,
                NistBaseline.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        baseline_id: str,
    ) -> Optional[NistBaseline]:
        """Fetch a baseline by its UUID primary key."""
        result = await db.execute(
            select(NistBaseline).where(
                NistBaseline.id == baseline_id,
                NistBaseline.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(
        db: AsyncSession,
        incident_type: Optional[str] = None,
    ) -> List[NistBaseline]:
        """List all active baselines, optionally filtered by incident type."""
        query = select(NistBaseline).where(NistBaseline.is_active == True)
        if incident_type:
            query = query.where(NistBaseline.incident_type == incident_type)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def initialize_missing_baselines(db: AsyncSession) -> int:
        """Seed any missing NIST baselines from canonical seed data.

        Returns the number of baselines created.
        """
        created = 0
        for seed in NIST_BASELINES_SEED:
            existing = await BaselineLoader.get_by_incident_type(
                db, seed["incident_type"]
            )
            if existing is not None:
                continue

            baseline = NistBaseline(**seed)
            db.add(baseline)
            created += 1

        if created:
            await db.commit()
        return created

    @staticmethod
    def get_odp_defaults(baseline: NistBaseline) -> dict:
        """Return the 8 canonical ODP default values for a baseline."""
        return {
            "severity_threshold": baseline.severity_threshold,
            "auto_contain_enabled": str(baseline.auto_contain_enabled).lower(),
            "escalation_contacts": baseline.escalation_contacts,
            "response_time_sla": str(baseline.response_time_sla_seconds),
            "forensic_level": baseline.forensic_level,
            "notify_targets": baseline.notify_targets,
            "compliance_report": str(baseline.compliance_report).lower(),
            "record_threshold": str(baseline.record_threshold),
        }
