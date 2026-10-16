# SEC-004 — Unknown identifiers accumulated permanent process state

- **Severity:** Medium. Authenticated identifier churn could retain unnecessary locks/cache entries and consume API memory.
- **Status:** Fix deployed to the API; source revision `9a264cf` verified and bounded-lifecycle regressions passed.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; interview lock map and repository TTL caches.

## Problem and impact

Interview locks remained allocated for unknown IDs after requests had failed. Separately, expiry made cache values stale but did not remove old keys unless those same keys were reused. Local fixtures retained 100 locks for 100 nonexistent interview IDs and 100 entries for 100 expired negative-cache lookups.

## Safe reproduction

Use synthetic UUIDs and a local in-memory service/cache. Advance a fake monotonic clock between misses. Inspect container sizes rather than stressing a running deployment.

## Exact remediation

- `backend/app/services/interview_service.py`: a context manager removes a lock when no owner or waiter needs it, including failed lookups; completion no longer removes an actively used lock prematurely.
- `backend/app/repo/cache.py`: removes expired entries and enforces an LRU capacity even when misses remain fresh. Default capacity is 1,024; the access cache uses 4,096.

The lock map still holds active operations/waiters. This change removes indefinite idle retention rather than claiming a fixed bound on all concurrent work.

## Verification

`backend/tests/test_security_api_abuse.py` verifies unknown interview locks return to zero, expired misses retain at most one fixture entry, and fresh misses respect a configured hard capacity while retaining frequently used results. All tests use local synthetic data.

## Remaining work

Monitor memory and preserve capacity/lifecycle tests when adding caches or changing asyncio/Python versions. Rate limits and infrastructure concurrency controls remain separate protections.

## References

[asyncio locks](https://docs.python.org/3/library/asyncio-sync.html#lock), [OrderedDict](https://docs.python.org/3/library/collections.html#collections.OrderedDict).
