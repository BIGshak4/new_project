# SEC-019 — The live server ran as "staging", so the production start guard only logged

- **Severity:** Medium. No exploit by itself; it removes the one mechanism that refuses a dangerous setting (pilot gate off, scripted model writing to the real database, empty or wildcard origins) before it serves users.
- **Status:** Fixed locally, deployed with the backend commit of 2026-11-08 (`ENV=production` in the blueprint); verified on `/health.env` after deploy.
- **Discovered:** 2026-11-08
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** `render.yaml` (`ENV: staging` since the first deploy), `backend/app/main.py` lifespan, `backend/app/config.py` (`production_problems`).

## Problem and impact

`production_problems()` is enforced only when `ENV=production`. The blueprint kept `staging` from the days before the real model key, and one check in the list (`ALLOW_IN_REVIEW_CONTENT=true`) contradicted the pilot's deliberate choice of 2026-11-02, so flipping the flag would have refused to start.

## Safe reproduction

`tests/test_security_review_2026_11_08.py::TestProductionGuard`.

## Exact remediation

`ENV=production` in `render.yaml`. The in-review check moved from refusals to a new `production_warnings()` list, logged in every environment together with the open operator items (`HEALTH_KEY` unset, service-role key unset, code-execution signing seed unset). Two refusals added: `*` in `ALLOWED_ORIGINS`, and `REQUIRE_PAYMENT=true` without payment keys. `health_key` and `code_execution_signing_seed` are stripped of pasted whitespace like the other secrets. Render keeps the previous deploy running if a new one refuses to start, so a wrong setting now fails the deploy, not the users.

## Verification

Unit tests above; after deploy `/health` reports `env: production`; the Render start log carries the warnings.

## Remaining work

The warnings are only read by whoever reads the log. `HEALTH_KEY` and the other operator items stay open until set.

## References

`backend/app/config.py` `production_problems` / `production_warnings`.
