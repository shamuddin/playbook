"""Performance benchmark for the Judge Layer.

Run from the backend directory with the virtual environment activated:
    python benchmarks/test_latency.py

Reports mean, median, p95, p99, min, and max latency in milliseconds.
"""

import asyncio
import statistics
import time
from typing import List

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.judge.engine import JudgeEngine, JudgeInput
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.seed import seed_all


async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_all(session)
        return session


async def teardown_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def benchmark(
    db,
    iterations: int = 1000,
) -> dict:
    engine = JudgeEngine()

    test_inputs = [
        JudgeInput(
            action="DROP TABLE customers",
            agent_id="agent-prod-01",
            incident_type="AGT-DEL-001",
            severity="critical",
            auth_present=False,
            is_business_hours=False,
            source_ip_reputation="malicious",
            contains_system_commands=True,
            is_repeat_offender=True,
        ),
        JudgeInput(
            action="export 50000 rows",
            agent_id="agent-prod-01",
            incident_type="AGT-EXT-005",
            severity="high",
            auth_present=False,
            contains_exfiltration=True,
            source_ip_reputation="suspicious",
        ),
        JudgeInput(
            action="read_user_profile",
            agent_id="agent-001",
            incident_type="AGT-GAP-012",
            severity="low",
            auth_present=True,
            is_business_hours=True,
            source_ip_reputation="trusted",
        ),
        JudgeInput(
            action="transfer $5000",
            agent_id="agent-finance-01",
            incident_type="AGT-FIN-002",
            severity="high",
            auth_present=True,
            dual_auth_present=True,
            source_ip_reputation="trusted",
            is_business_hours=True,
        ),
    ]

    latencies: List[float] = []

    for i in range(iterations):
        inp = test_inputs[i % len(test_inputs)]
        start = time.perf_counter()
        await engine.evaluate(db, inp)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

    latencies.sort()
    n = len(latencies)
    p95_idx = int(n * 0.95) - 1
    p99_idx = int(n * 0.99) - 1

    return {
        "iterations": n,
        "mean_ms": round(statistics.mean(latencies), 3),
        "median_ms": round(statistics.median(latencies), 3),
        "p95_ms": round(latencies[max(0, p95_idx)], 3),
        "p99_ms": round(latencies[max(0, p99_idx)], 3),
        "min_ms": round(min(latencies), 3),
        "max_ms": round(max(latencies), 3),
        "stdev_ms": round(statistics.stdev(latencies), 3) if n > 1 else 0.0,
    }


async def main():
    print("=" * 60)
    print("PLAYBOOK Judge Layer Latency Benchmark")
    print("=" * 60)

    db = await setup_db()
    try:
        await db.close()  # close the seed session
        db = AsyncSessionLocal()
    except Exception:
        pass
    try:
        # Warm-up run to prime caches
        print("Warming up...")
        await benchmark(db, iterations=100)

        # Official benchmark
        print("Running benchmark (1000 iterations)...")
        results = await benchmark(db, iterations=1000)

        print()
        print(f"Iterations:    {results['iterations']}")
        print(f"Mean:          {results['mean_ms']} ms")
        print(f"Median:        {results['median_ms']} ms")
        print(f"P95:           {results['p95_ms']} ms")
        print(f"P99:           {results['p99_ms']} ms")
        print(f"Min:           {results['min_ms']} ms")
        print(f"Max:           {results['max_ms']} ms")
        print(f"StdDev:        {results['stdev_ms']} ms")
        print()

        target_p95 = 50.0
        if results["p95_ms"] <= target_p95:
            print(f"[PASS] P95 latency target met ({results['p95_ms']} ms <= {target_p95} ms)")
        else:
            print(f"[WARN] P95 latency target missed ({results['p95_ms']} ms > {target_p95} ms)")

    finally:
        await db.close()
        await teardown_db()


if __name__ == "__main__":
    asyncio.run(main())
