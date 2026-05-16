#!/usr/bin/env python3
"""Seed ONLY reference data (no demo incidents/agents).

This is NOT mock data — these are the operating rules, baselines,
templates, and playbooks that PLAYBOOK needs to function.
"""

import asyncio
import sys

# Add backend to path
sys.path.insert(0, "K:/Hackthon/Playbook/PlaybookRepo/backend")

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import Base
from app.seed.all import seed_all


async def main():
    print("Seeding PLAYBOOK reference data...")
    print("=" * 50)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        results = await seed_all(db)

    print("\nResults:")
    for table, count in results.items():
        if count > 0:
            print(f"  + {count} {table} seeded")
        else:
            print(f"  = {table} already exist (skipped)")

    print("\nReference data ready.")
    print("You can now register real agents and create real incidents.")


if __name__ == "__main__":
    asyncio.run(main())
