# SEC-002 — Concurrent starts could exceed daily allowances

- **Severity:** Medium. An authenticated user could obtain additional practice attempts/interviews and subsequent model work beyond the configured daily allowance.
- **Status:** Fix deployed to the API; source revision `9a264cf` verified and local regression suite passed. No production attack/load test was performed.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; practice/interview admission across independent service instances.

## Problem and impact

Counting today's starts and inserting a new resource were not serialized across API workers. Concurrent requests could all observe one remaining slot. A local fixture with a daily limit of one and four independent service instances accepted four starts, for both resource types.

## Safe reproduction

Use the in-memory store, scripted provider and synthetic user ID. Force a scheduling yield after the allowance count, then run four starts concurrently. No real user, production load or paid model call is required.

## Exact remediation

- `backend/app/services/store.py`: adds transaction-scoped PostgreSQL advisory locking keyed by user and allowance scope.
- `backend/app/services/practice_service.py`: acquires the lock before COUNT and INSERT, including profile-race retries.
- `backend/app/services/interview_service.py`: rechecks the allowance under the lock in the insertion transaction; the earlier check is only an inexpensive refusal.
- `backend/app/services/memory_store.py`: supplies equivalent lock lifecycle behavior for local fixtures.

The lock spans admission, not model evaluation. Hash collisions can serialize unrelated callers but cannot grant additional allowance.

## Verification

`backend/tests/test_security_api_abuse.py::test_daily_allowance_is_atomic_across_service_instances` now accepts one start and rejects three with `usage_limit`, independently for practice and interviews. No provider requests occur. The database review confirmed PostgreSQL 17.6, READ COMMITTED behavior and availability of the advisory-lock functions; no concurrent production starts were attempted.

## Remaining work

Retain these regressions when changing transaction isolation, stores, worker topology or billing rules. A controlled PostgreSQL concurrency fixture is a useful additional check; local service-instance tests are not a production load test.

## References

[PostgreSQL advisory locks](https://www.postgresql.org/docs/17/explicit-locking.html#ADVISORY-LOCKS), [READ COMMITTED](https://www.postgresql.org/docs/17/transaction-iso.html#XACT-READ-COMMITTED).
