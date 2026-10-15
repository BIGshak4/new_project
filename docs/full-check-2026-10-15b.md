# Full check, evening of 15 October 2026: verification, profiling, review and fixes

Written for Shaked and Harel. The second full pass of the day, asked for after tasks 8, 9 and 10 of Harel's list
landed on the backend (the questions fit the job type; the plan fits the user's minutes and never piles up; every
reason sentence true to its rule) and Harel's seven interface tasks landed on the web app. Scope of the review: every
change since the morning's check (`e2d7e3b`), backend and web.

## 1. Verification

| Area | Check | Result |
|---|---|---|
| Backend code | `ruff`, offline suite | clean, **945 tests pass** (4.5 min on a busy laptop), 12 added by this pass |
| Backend, real database | the 18 live tests (rolled back), run alone | **18 of 18** before the fixes (23 min) and **18 of 18 again on the final code** (22 min) |
| Real model, in memory | `scripts/e2e_real_flow.py` | passes, 15 model calls, $0.19, 57 s |
| Real model and database | `scripts/e2e_goal_and_visuals.py`, `scripts/e2e_live_trial.py` | both pass on the final code, rolled back (53 s and 93 s) |
| Web app (run only, Harel's) | `npm test`, `tsc` | **104 of 104**, clean |
| Every screen | the harness, both languages, 1280 and 390 px | **56 shots, no overflow**; LCP median 160 ms, CLS worst 0.075; the four sign-in shots still skipped (the harness's selector, Harel's queue item 7) |
| Production | `/health`, `scripts/smoke_http.py` (29 routes) | healthy on the day's build before and after this pass, all routes pass |

## 2. Profiling

| Measure | This morning | This evening |
|---|---|---|
| Full practice loop in memory (`profile_service.py --cpu`) | 26 ms per loop on a quiet laptop | **36 ms per loop with the live suite running alongside**; an A/B on the same machine state put the morning's commit (`e2d7e3b`, in a throwaway worktree) at 37 ms and today's code at 36 ms, so nothing regressed; the profile's shape is unchanged (question summaries built per call by the in-memory store, the suggestion after an answer) |
| Many users (`load_test.py`, local API over HTTP, scripted model with real timing) | 50 users: all flows complete, lag p99 65 ms, max 141 ms | **50 users: 50 of 50 flows complete, no errors**; event-loop lag p50 5.6 ms, p99 25.5 ms, max 44.6 ms; memory 122 to 146 MB; reads p95 ≤ 37 ms (program 22, progress 30, questions 37); whole flow per user 38.9 s median (the model's own time) |
| Round trips | — | the reviewer counted the submit path at 13 statements with the second goal read and 12 without; it is 12 again. The plan rebuild is 3 + one insert per item (11 items at 30 minutes a day, 17 at 600), once a day per user |

## 3. Independent review

Five reviewers, read-only, each with one lens, probing against the in-memory store: correctness, concurrency and
data integrity, security and input handling, performance, and (for Harel) the web app's use of the backend contract.
Every finding below was reproduced by its reviewer's probe before it was accepted; the concurrency probes were re-run
after the fixes and no longer reproduce.

### Found and fixed in this pass (backend)

**Concurrency and data integrity**
1. A program rebuild (under the per-user lock) could overlap an answer's tick (not under it), read the item as
   *started*, and copy that stale status into the new plan after the answer had ticked the old item: the item was
   reborn open with a fully answered attempt linked to it. Fix: the answer's persist transaction runs under the user
   lock, taken before the transaction opens (so neither side ever waits on a row the other holds).
2. The by-skill fallback that ticks an item for an unlinked answer (now the normal path for "opened yesterday,
   answered today") could tick an item another live attempt had open, leaving that attempt's own answer with nothing
   to tick; and it matched *any* of the question's skills, so an answer about skill C could tick a side skill's item
   and leave C's own item open. Fix: the primary skill first, secondary links only when nothing matches it; a
   planned item before a started one; never a started item owned by another attempt.
3. When a rebuild replaced the plan between the answer's read and its write and the item had been dropped, the
   fallback retried the same dead id and ticked nothing. Fix: one fresh look at the new plan.
4. Done items copied by the rebuild were not relinked, leaving the attempt's item reference dangling (no visible
   effect; wrong for anything reading the link). Fix: relinked like started items.
5. The plan-build savepoint treated any integrity error as "another request built the plan first" and handed back the
   old plan. Fix: only the one-active-plan index conflict is treated so; anything else raises.

**Correctness (the router)**
6. In the final reserved days before the interview the candidates were narrowed to rehearsal and re-check items
   *before* the budget filter, so a short-budget user whose day could not hold a 12-minute re-check got an empty
   week. Fix: the budget filter first, then the preference among what fits.
7. The forced "one deep practice per week" item was appended to a day without checking its remaining minutes (42
   over-budget days in 5,390 generated plans) and could land on the day after an interview held today. Fix: placed on
   the day with the most room that can hold it, never after the interview, else skipped.
8. `simulation_minutes(None)` returned the 40-minute estimate, not one of the lobby's lengths (unreachable today).
   Fix: the longest length within the estimate. The interview lengths now have one source (`plan_router.SIMULATION_DURATIONS`,
   imported by the interview service).

**Security and input handling** (no vulnerability; ownership, validation, error shapes and the absence of leaks were
all confirmed by probe)
9. The seed loader coerced `false` or `"0"` in a job type's emphasis into an exclusion. Fix: numbers only.
10. A job type that excludes every role skill loaded silently and sent the user to an interview lobby that refuses.
    Fix: a loader error.

**Wording (task 10's own lens)**
11. "No other question on {skill} is available" was also said when other questions existed but were hidden by the job
    type or outside the difficulty window. Fix: "No other question on {skill} fits right now"; the last-resort sentence
    no longer promises "at this level".

**Performance**
12. The suggestion after an answer re-read the goal: one extra statement on every scored answer. Fix: the job type
    rides on the attempt's context.
13. The plan cache was keyed by the seniority string before normalisation (one entry per unknown value). Fix:
    normalised first.

### Found, accepted for now (written down, not fixed)

- A started item kept across a same-day goal change keeps its minutes, so lowering the budget under an open 20-minute
  item shows those 20 today. This is the one deliberate exception to "never above the day" (the item has a live
  attempt); documented in the rebuild's docstring.
- A week holds at most one item per (mode, skill) pair, so a very large daily budget puts the whole week on day one
  (18 items with today's bank; it bites above about 120 minutes a day). Below 12 minutes a day only quick items fit,
  so such a user is never re-checked. Both are consequences of the bank's size and "never above the day"; a per-day
  cap or more questions would change them.
- The rebuild inserts plan items one at a time (once a day per user); the router recomputes three loop-invariant
  values per candidate (31 ms worst case, 2.6 ms typical).
- A stale `item_id` on program start falls back to the user's own next item with a 200 instead of a 404 (no cross-user
  effect).
- The per-user lock is per process; Render runs one instance. A second instance would need the row lock noted in
  §5zm of `backend/STATUS.md`.

### For Harel (the web reviewer's findings, in his queue in `backend/STATUS.md`)

- The `why` badge has no label for `map` and `same_skill` (queue item 11).
- A question opened from a search result is reported as `source: "library"`, never `"search"` (item 12).
- The plan table's Start on an interview item drops `interview_duration_min`; the Learn page passes it (item 13).
- The "carried" badge and carried-first ordering are still implemented; the backend always sends false (item 10).
- `JobType.excluded_skills` and `SkillProgress.expired` are not in the TypeScript types yet (item 14).
- Checked correct: the skip, the readiness card (the score is never rendered), continue with tomorrow, `source`/`screen`
  on every start, the `?job=` filter, every other type field-for-field.

## 4. Lessons

- The reviewers' interleaving probes (a store wrapper that yields on every call, `asyncio.gather` with a delayed
  rebuild) found a lost update that no ordinary test could. They live under the session scratchpad; the regression
  tests pin the fixed behaviours deterministically.
- A rule stated in a docstring ("never above the day") is worth a generated-plans sweep: 5,390 plans found 42 cases
  that eight hand-written budgets did not.
