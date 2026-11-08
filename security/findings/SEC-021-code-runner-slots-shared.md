# SEC-021 — One member could hold everyone's code-runner slots

- **Severity:** Low. Availability only: two unfinished runs by one member refused every other member's code check ("the code runner is busy") for up to two minutes, repeatably.
- **Status:** Fixed locally, deployed with the backend commit of 2026-11-08; verified by regression tests on the in-memory ledger (the SQL ledger carries the same filter).
- **Discovered:** 2026-11-08
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** since the isolated executor of 2026-10-31; `backend/app/repo/executions.py` (`_limits`, `DbExecutionLedger.reserve`).

## Problem and impact

The daily and per-minute counts were per user, the running-slot count was global (`concurrent=2`).

## Safe reproduction

`tests/test_security_review_2026_11_08.py::TestCodeRunnerSlotsPerMember`; `tests/test_isolated_execution.py::test_ledger_idempotency_limits_and_concurrent_reservations` updated to the per-member rule.

## Exact remediation

Both ledgers count running slots for the caller only. The short global advisory lock around a reservation stays (it protects the idempotency check, not capacity).

## Verification

Tests above green.

## Remaining work

Global capacity is now bounded by the broker's own limits; if the executor is ever shared with a larger population, add a global ceiling above the per-member one rather than instead of it.

## References

`security/findings/SEC-001-untrusted-code-execution.md` for the executor's design.
