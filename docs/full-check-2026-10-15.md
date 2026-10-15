# Full check: verification, profiling, review and fixes — 15 October 2026

Written for Shaked and Harel. Shaked asked for a complete pass: every suite against the real system, a profiling
pass, an independent code review of everything that changed since the last full check (1 October), and fixes for
what it found. This is the result. The backend changed a lot in those two weeks (the work-ahead program, the new
follow-ups, the skip, grader v2 and the lean-strong rule, evidence freshness in weeks, readiness for the job type,
the entry source); the review concentrated on that code.

## 1. Verification

| Area | Check | Result |
|---|---|---|
| Backend code | `ruff`, offline suite | clean, **907 tests pass** (29 s), 11 added by this pass |
| Backend, real database | the 17 live tests (rolled back), run alone | **17 of 17** before the fixes (20 min) and **17 of 17 again on the final code** (30 min, the laptop busy with the other runs) |
| Real model, in memory | `scripts/e2e_real_flow.py` | passes, 15 model calls, $0.18 |
| Real model and database | `scripts/e2e_goal_and_visuals.py`, `scripts/e2e_live_trial.py` | both pass, rolled back (99 s for the trial) |
| Web app (run only, Harel's) | `npm test`, `tsc` | **65 of 65**, clean |
| Every screen | the harness, both languages, 1280 and 390 px | **56 shots, no overflow**; the four sign-in shots were not produced because the harness looks for a `.landing` element the redesigned landing page no longer has (a harness entry for Harel, not a page fault) |
| Production | `/health`, `scripts/smoke_http.py` (29 routes) | healthy on the day's build, all routes pass |

## 2. Profiling

| Measure | 1 October | Today |
|---|---|---|
| Full practice loop in memory (`profile_service.py --cpu`) | 48 ms per loop | **26 ms per loop** (322 loops in 8.4 s); the top of the profile is pydantic validation of question summaries, now cached (see fixes) |
| Many users (`load_test.py`, local API over HTTP, scripted model with real timing) | 10 and 50 users, all flows complete, lag p99 29 ms | **10 and 50 users: every flow completed, no errors**; event-loop lag p50 6 ms, p99 65 ms, max 141 ms; memory 121 to 145 MB; whole flow per user 40 s median at 50 users (the model's own time) |
| Grade latency on the real model (`latency_bench.py`, from this laptop to Frankfurt) | 7.9 s median grade known | **9.5 s median, 11.1 s max** grade known over 5 answers; the evaluator itself 4.3 to 8.2 s; the rest is 21 to 26 database statements at this machine's round trip (the server's own round trip is 2 to 4 ms) |
| The API's pool under many readers (`db_concurrency.py --phase pool`, from this laptop) | fine at 50 | 10 users: wait p50 0.4 s; 50 users: wait p50 7.5 s, p95 17 s, no errors. The 5+5 pool is the limit when every progress read holds a connection for 1.3 s at this machine's latency; from Render the same read set holds it for a few tens of milliseconds, which is why the HTTP load test at 50 users stayed under 250 ms per read |

The performance reviewer's reading, confirmed by the profile: the engine is cheap (the router is 4 to 6 ms per
rebuild, a whole practice loop 26 ms); what a user feels is round trips to the database, and the new code had
multiplied them in two places. Both are fixed below.

## 3. Independent review

Four reviewers read the diff since 1 October, each with one lens, read-only, with probes against the in-memory
store; a fifth pass verified their findings against the code. Sound, confirmed by probe: ownership on every attempt
and interview route (a second user gets 404 everywhere), the follow-up skip under send-and-skip in either order, the
prose writer's reload under the lock, the prompt-injection protections, the input bounds on answers, drawings and
keys, every hot query indexed, the caches bounded.

### Found and fixed in this pass

**Concurrency and data integrity (the saved program):**
1. Nothing serialised one user's program writes. Two first-of-day reads both rebuilt the plan and the second hit the
   one-active-plan index (a 500 on a GET); a double click on Start opened two attempts on one item, and a later answer
   could tick an unrelated item; a goal saved during a rebuild left the old job type's plan in place all day; a
   rebuild racing an answer stranded the item as "started" in the new plan. Fix: a per-user lock around the rebuild,
   the plan start and the goal save; a started item is **resumed** on a second click instead of reopened; the item is
   linked and marked in the attempt's own transaction; the tick lands only on the active plan and, if the plan was
   replaced meanwhile, follows the attempt to its relinked copy; the plan build runs in a savepoint and a loser takes
   the winner's plan instead of failing; the plan's stamp never trails the goal's, so a clock that runs ahead triggers
   one rebuild, not one per read (equal stamps count as newer, for coarse clocks).
2. Carried items were placed before the minutes of work done ahead were counted, so a day could exceed its budget.
   Fix: work done or opened ahead is counted first.
3. An opened item with a live attempt could be dropped by the de-duplication (its answer then ticked nothing). Fix:
   an opened item is never dropped.

**Security and input handling:**
4. The 256 KB body guard checked only the Content-Length header; a chunked body of any size was buffered and parsed
   before authentication. Fix: the limit is enforced on the bytes that arrive, as an outer ASGI layer, and answers 413.
5. `latency_ms` and `revision_count` had no upper bound and overflowed the 32-bit metrics columns after the model had
   already been paid for, failing the save (500) and losing the grade. Fix: bounded in the request models and clamped
   in the engine.
6. Company sightings accepted any text from any pilot user and published it to every user. Fix: a company name is
   letters, digits, spaces and `. & ' -` only; at most five new company names per user per day (429 after that).
7. The request id from the client was reflected and logged unvalidated (log forgery), the path was logged decoded,
   and under plain `uvicorn` the access log was never emitted. Fix: the id must match `[A-Za-z0-9_-]{1,64}` or is
   replaced; the path is logged without line breaks; the root logger is configured at startup.
8. No per-caller request budget: a tight loop on the plan-rebuilding reads could saturate the pool. Fix: 600
   requests a minute per caller (token, else address), `/health` exempt, 429 above that.

**Performance (round trips):**
9. A plan start opened four transactions and loaded the profile and goal three times. Fix: the program's reads are
   reused and the link happens inside the attempt's transaction: two transactions.
10. The readiness view ran the whole progress computation and then opened a second transaction. Fix: one
    read-only transaction and the per-skill rows shared with progress.
11. A follow-up answer scheduled a background words task that wrote nothing (two transactions). Fix: a revision is
    marked as awaiting words only when there is something to write.
12. The 67 question summaries were rebuilt on every list call (3 ms of validation each time). Fix: cached per
    language within the servable cache's minute.

**Caught by the live run, of this pass's own making:** the first version of the "tick only the active plan" query
was malformed (a correlated subquery returned more than one row) and failed five program tests on the real database
while the in-memory store, which has no SQL, passed them all. The query was rewritten and the live suite rerun on the
final code. The lesson stands: a repository change is verified against the real database before it is committed.

### Found, accepted for now (written down, not fixed)

- `/health` tells an anonymous caller the environment, the model ids and the pooler mode. Shaked reads it; gating it
  behind a key is a later step.
- The report response returns the all-users count of open reports on the question (a minor cross-user signal).
- The plan rebuild inserts items one at a time inside a GET (up to about 20 statements, once per user per day).
- Progress recomputes XP from a year of rows on each call (2 ms today; an aggregate when users accumulate rows).
- The follow-up writer's second call, when a guard fires, holds back the feedback card and tip with it (they are
  saved together); counting the guard flags in production tells how often that is.
- A refusal from the model that arrives with partial text is reported as a failed grading, not a refusal.

## 4. For Harel

- The harness entry for the sign-in screen needs the new landing page's selector.
- Nothing in the contract moved in this pass; the queue in `backend/STATUS.md` stands.
