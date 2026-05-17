---
name: load-test
description: Run load tests and benchmark latency SLOs for detection, judge, and forensics
---

Execute a load-test and latency benchmark suite to validate PLAYBOOK SLOs. If no Locustfile exists, bootstrap a minimal one in `backend/tests/load/`.

1. **Baseline detection**: Run `cd backend && python -m pytest tests/unit/test_detect_engine.py -v --benchmark-only` or create a quick Locust task that submits 100 events/sec for 60 seconds. Verify p95 <= 10 ms.
2. **Judge latency**: Benchmark `JudgeEngine.evaluate()` with 1,000 randomized inputs. Verify p95 <= 50 ms and p99 <= 100 ms.
3. **Forensics packaging**: Generate an evidence package for an incident with 100 timeline events. Verify completion <= 150 ms.
4. **E2E pipeline**: Run `pytest tests/integration/test_full_pipeline.py -v` under normal and concurrent load (10 parallel workers). Verify p95 <= 200 ms.
5. **Pool exhaustion check**: Monitor `database_pool_size` and `database_max_overflow` during the test. Report if asyncpg pool saturates.
6. **Report**: Provide a summary table of measured vs. target latencies. Flag any SLO breach with flame graph or query plan recommendations.
