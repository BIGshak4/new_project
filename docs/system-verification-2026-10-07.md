# System verification and Shaked handoff on 7 October 2026

Historical verification snapshot. For Harel's current 24-item product queue and the seven accepted fixes, see the [15 October handoff](harel-product-tasks-handoff-2026-10-15.md). Counts and open issues below describe 7 October.

The checkout is updated to `e5e70e1f138ab75615d357f0f106ab576f531571`. The offline suites pass **960 tests** (895 backend and 65 web), both frontends build, the deployed API passes its 14 HTTP smoke checks, and 80 local concurrent-user flows complete. Live database integration remains unverified in this run because the local database credential is rejected. Several new backend capabilities still need their frontend screens.

## Git and local changes

`git pull --rebase origin master` advanced `master` from `9abeba0` to `e5e70e1` by fast-forward, with no conflicts or local commits to replay. The three existing untracked Supabase files were preserved: `.gitignore`, `config.toml`, and `migrations/20260916224150_initial_schema.sql` under `supabase/`.

One import-order lint error in `backend/tests/test_loyalty.py` was corrected; this changes whitespace between imports only. This report is the other new local change. No push, deployment, migration, question import, or production load test was performed.

## Shaked's summary and the next work

The comprehensive handoff is [backend/STATUS.md](../backend/STATUS.md). Its opening **Harel's front-end queue** is the actionable screen backlog, and its later changelog sections explain the backend work. Some historical sections and the headline test count are older than the current implementation; use this run's results for current verification.

The pulled work includes:

- Fairer answer grading: a correct method does not require worked examples to be complete; correct solutions with thin reasoning can receive STRONG with lighter evidence and a reasoning follow-up. Follow-ups probe understanding or edge cases, and the backend supports skipping them.
- Daily plans that fit available minutes, role-weighted priorities, evidence freshness, work ahead after today is finished, and replanning after goal changes while preserving completed work.
- Role-specific readiness, skill gaps, coverage and recommended practice. The screen should show the readiness word rather than a numerical readiness score when coverage is sufficient.
- Start-attempt source, screen and device tracking, plus read-only journey reporting scripts.
- A separate bank of 242 bilingual generated drafts. [The draft review document](question-bank-drafts.md) flags three reference/check disagreements. The drafts have not been imported into the active bank.

Recommended implementation order, following Shaked's queue:

1. Add follow-up skipping, including pending/answered/skipped states and race handling; add the readiness card and its recommended-question actions. Include `source` and `screen` on attempt starts throughout the app.
2. Update progress presentation for expired evidence and remove the assessed-of-N overview count. Add the action to continue with tomorrow's plan.
3. Add the browser-side circuit truth table, bounded to six inputs and combinational circuits. Leave dictation conditional on the Hebrew technical-vocabulary trial.
4. Review and repair the flagged drafts before importing reviewed batches; this is separate from the screen integration.

`backend/tests/test_ts_client_contract.py` explicitly exempts `ProgramView.ahead`, `FollowUpView.skipped`, `SkillProgress.expired`, the skip route and the readiness route while the client is pending. Passing contract tests therefore does **not** establish that these features are connected. Remove each exemption as its integration is completed.

## Verification results

| Area | Result | Scope |
|---|---|---|
| Backend offline tests | **895 passed**, 16.03 s | Three live-DB modules explicitly excluded; `DATABASE_URL` empty for this run |
| Web unit tests | **65 passed** | Existing `apps/web` test suite |
| Backend lint | Passed after the import-order fix | `ruff check app scripts tests` |
| Web type check and production build | Passed | `npm.cmd run typecheck`, `npm.cmd run build` |
| Tasks type check and production build | Passed | Same commands in `apps/tasks`; no unit-test script in that app |
| Seed validation | Passed | Six subjects, 35 skills, 67 seed questions: 30 in review and 37 trial; no database import |
| Deployed API HTTP smoke | **14 checks passed**, 29 v1 routes found | Health, docs/schema, CORS, unauthenticated and forged-token rejection, request ID, 404/405/413 behavior and JWKS verification |
| Local load with simulated model | **10/10 and 50/50 flows completed** | No endpoint errors; evaluator latency 0.5 s, prose latency 0.3 s |
| Local load with simulated model rate limits | **20/20 flows completed** | 30% configured evaluator failure probability; 32 injected 429s across 108 evaluator calls |
| Supabase metadata review | Seven inspected tables have RLS enabled and no anonymous SELECT grant | Read-only policy/grant metadata, not a behavioral RLS test |
| Deployed frontend health | Both HTTP endpoints returned `ok` | Practice revision `9abeba0`; tasks revision `ea163856`; each app's tracked directory matches HEAD despite different repository revision labels |
| Signed-out browser checks | Passed | Both login pages render; XOR outputs match all four input pairs; empty task-board login is blocked; no captured warning/error console entries on either page |

The local load test uses an in-memory store and simulated AI. It is a concurrency and failure-handling check, **not** a benchmark of production database or Anthropic capacity. At 50 users, observed memory grew from 97.9 to 115.1 MB and event-loop lag p99 was 44.7 ms. In the rate-limit run, three practice answers required an explicit retry; three interview answers were retained but unscored after model failure, allowing the turn to be answered again. Completion of the flow does not imply every injected failure produced a grade automatically.

The deployed backend reported `provider=anthropic`, `store=database`, `env=staging`. The smoke test does not submit a real learner answer or assess the model's feedback quality.

## Outstanding verification

- **Live database integration:** 21 tests were collected across `test_live_db.py`, `test_live_service.py`, and `test_live_interview.py`. An initial live-interview setup attempt failed with `InvalidPasswordError` for the configured database user. The remaining live suite was not run against the rejected credential. Restore a valid local `DATABASE_URL`, then run these three modules; do not reset production credentials just to satisfy this checkout.
- **Authenticated browser journeys:** this browser session was signed out. Real-account onboarding, answer submission, refresh recovery and private task-board permissions were not exercised through the deployed UI in this run. Their automated coverage and database metadata checks are not substitutes for that end-to-end pass.
- **Real AI answer quality:** no fresh paid-model evaluation sweep was run. Review a small representative Hebrew/English sample after connecting the new screens.
- Two offline warnings concerned an AnyIO deprecation and an intentionally short HMAC key used by an authentication test. The smoke script also uses a short key to construct its forged-token negative case.

## Reproduction and evidence

Run from `backend/`, with a blank `DATABASE_URL` for the offline suite:

```text
.venv/Scripts/python.exe -m pytest -q --ignore=tests/test_live_db.py --ignore=tests/test_live_service.py --ignore=tests/test_live_interview.py --tb=short
.venv/Scripts/python.exe -m ruff check app scripts tests
.venv/Scripts/python.exe scripts/seed_db.py --check
.venv/Scripts/python.exe scripts/smoke_http.py --url https://jobrun-api.onrender.com --origin https://jobrun-practice.netlify.app
.venv/Scripts/python.exe scripts/load_test.py --users 10 50 --eval-latency 0.5 --prose-latency 0.3
.venv/Scripts/python.exe scripts/load_test.py --users 20 --eval-latency 0.5 --prose-latency 0.3 --rate-limit 0.3
```

Run `npm.cmd test`, `npm.cmd run typecheck`, and `npm.cmd run build` from `apps/web/`; run the latter two from `apps/tasks/`.

Local logs, JUnit XML and load-test JSON are in the ignored directory `backend/workdir/system-verification-2026-10-07/`. The definitive backend result is `backend-offline-final.log` / `backend-offline-final.xml`; the earlier run includes the database setup failure. Load results are `load-normal.json` and `load-rate-limit.json`.
