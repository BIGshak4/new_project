# SEC-011 — Concurrent diagnostic health requests multiplied database probes

- **Severity:** Medium. Public diagnostic requests could occupy database connections and repeat probe queries during a cache miss or outage.
- **Status:** Fix deployed to the API; source revision `9a264cf` verified and single-flight/deadline/cache regressions passed locally.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; optional `/health?db_check=true` diagnostic path.

## Problem and impact

A cached database health probe lacked single-flight coordination and an outer deadline. Concurrent callers could all miss the cache and each start three queries. A local mock reproduced **16 connections / 48 queries** for 16 simultaneous callers. The health-path rate-limit exemption also covered the more expensive diagnostic query.

## Safe reproduction

Use the mocked connection pool in `backend/tests/test_security_request_limits.py`. Block/release the mock connection with asyncio events and count connections/queries. No production probe burst is needed.

## Exact remediation

`backend/app/main.py::_database_round_trip` uses a shared per-process lock with a second cache check, a three-second probe timeout, ten-second successful-result caching and two-second failed-result caching. Failed results expose the exception type rather than credentials/connection strings. Diagnostic query requests are now charged to the request budget; basic liveness remains inexpensive and exempt.

## Verification

The same 16-caller fixture now opens **one connection / three queries** and returns the same result to all callers. A deliberately blocked mock with a shortened test deadline returns a timeout result, and an immediate retry uses the negative cache. These are deterministic local tests, not production connection-pool measurements.

## Remaining work

Coordination is per API process, so independent workers may each make one probe. Review public diagnostic detail and monitoring needs when changing topology; this fix addresses probe amplification and does not certify the database under arbitrary load.

## References

[asyncio timeout](https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout), [asyncio lock](https://docs.python.org/3/library/asyncio-sync.html#lock).
