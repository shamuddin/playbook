---
name: llm-observability
description: Audit Gemini overlay for missing metrics, retry logic, and cache health
---

Audit the Gemini reasoning and caching layer for production observability gaps. Validate deterministic fallback coverage and cache efficiency.

1. **Latency audit**: Read `backend/app/services/gemini_reasoning.py` and confirm every API call is wrapped with `time.perf_counter()` logging. If not, flag missing instrumentation.
2. **Cache health query**: Query the `gemini_cache` table: `SELECT COUNT(*) as total, SUM(hit_count) as hits FROM gemini_cache;`. Calculate hit rate = hits / (hits + misses). Report if < 70%.
3. **Fallback validation**: Simulate a Gemini API failure (unset `GEMINI_API_KEY` or block DNS) and verify the deterministic fallback dictionary returns a valid rationale for ALLOW, DENY, QUARANTINE, and ESCALATE.
4. **Retry/circuit breaker audit**: Check `gemini_reasoning.py` for retry logic and circuit breaker. If absent, flag as production risk.
5. **Cost estimation**: Review `config.py` for `gemini_max_tokens` and `gemini_temperature`. Estimate tokens-per-request and monthly cost at 10,000 incident enrichments/day.
6. **Metrics recommendation**: Propose 3 structured logging fields or Prometheus metrics to add (e.g., `gemini_latency_ms`, `gemini_fallback_rate`, `gemini_cache_hit_rate`).
