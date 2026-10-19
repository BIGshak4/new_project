# Full check, night of 18–19 October 2026: verification, profiling, review and fixes

Written for Shaked and Harel. Shaked asked for "a full verification, code review and profiling" over everything
since the evening check of the 15th (`4cb6c70`): 33 commits — Harel's security pass and interface tasks (truth table,
dictation, landing, testimonials scaffold, the circuit workspace, localised solutions, the bracket fix), and on the
backend no XP for unrelated answers, the soft skills and the improvement gradient as backend-only data, and the
checks of his pushes.

## 1. Verification

| Area | Check | Result |
|---|---|---|
| Backend code | `ruff`, offline suite | clean, **992 tests pass, 9 skipped** before the fixes and **1,003 pass, 9 skipped** on the final code (11 regression tests added; the skips are Harel's opt-in database checks) |
| Backend, real database | the three live files (rolled back), run alone | **21 of 21** (24 min) |
| Real model, in memory | `scripts/e2e_real_flow.py` | passes, 15 model calls, $0.18, 60 s |
| Real model and database | `scripts/e2e_goal_and_visuals.py`, `scripts/e2e_live_trial.py` | both pass, rolled back (46 s and 82 s) |
| Web app (run only, Harel's) | `npm test`, `tsc` | **234 of 234**, clean |
| Every screen | the harness, both languages, 1280 and 390 px | **56 shots, no overflow**; LCP median 176 ms at 1280, 144 ms at 390; the four sign-in shots still skipped (his item 7) |
| Production | `/health`, `scripts/smoke_http.py` (29 routes) | healthy on `091b7d4` before the fixes and on `f9f450b` after them, all routes pass both times; the health body is still the full one until `HEALTH_KEY` is set on Render |

## 2. Profiling

| Measure | 15 October (morning, quiet) | This night |
|---|---|---|
| Full practice loop in memory (`profile_service.py --cpu`) | 26 ms per loop | **38 ms per loop** while the reviewers' probes and the database scripts shared the machine; an A/B on the same machine state put the last check's commit (`4cb6c70`, in a throwaway worktree) at 38 ms too, so nothing regressed; the quiet-machine figure remains the 15th's 26 ms |
| Many users (`load_test.py`, local API over HTTP, scripted model with real timing) | 50 users: all flows complete, lag p99 25 ms | **10 users: 10 of 10 flows, lag p50 2.7 ms / p99 23 ms; 50 users: 50 of 50 flows, lag p50 3.9 ms / p99 27 ms / max 46 ms**; memory 124 to 149 MB; program p95 32 ms, progress p95 31 ms; whole flow 38 s median (the model's own time) |
| Round trips | — | the performance reviewer counted: submit 13 statements / 3 transactions and progress 12 / 1, unchanged by the week; practice start +1 (the advisory lock), interview start +2; the soft-skill reading 5 statements |

## 3. Independent review

Five reviewers, read-only, one lens each, probing against the in-memory store: correctness, concurrency and data
integrity, security and input handling, performance, and the web app's use of the contract. (The first attempt at
three of them was cut off by the session's rate limit and rerun after the reset.)

### Backend

Every finding below was reproduced by its reviewer's probe (or confirmed by reading where a probe was not
possible) before it was accepted; each fix carries a regression test in `tests/test_night_fixes_2026_10_19.py`.

**Fixed in this pass**

*Request limits and caches (Harel's security pass, hardened)*
1. The bucket eviction was pure LRU over live buckets, so a caller rotating identities could flush every other
   caller's count and restart their windows (confirmed: 10,000 rotated tokens cleared a caller sitting at its limit).
   Fix: expired buckets first, then the least recently seen one-request bucket (what a churner's identities are),
   and only then a live one.
2. The per-token bucket was keyed on the raw `Authorization` bytes, so one valid token spelled three ways
   (`Bearer x`, `bearer x`, `Bearer x `) was three budgets, and a duplicated header was read differently from the
   authenticator. Fix: the first header, trimmed, scheme lower-cased.
3. A cache invalidation that landed while a load was in flight was lost: the stale value was stored for a full TTL
   (a member added during an access lookup stayed out for 120 s). Fix: a generation counter; a load that started
   before an invalidation serves its value but does not keep it.
4. A refused request is now logged with the peer address — the one line that tells whether Render's proxy hands
   the API real client addresses or a single shared one (in which case every user shares one 1,800/min bucket).

*The judge's outputs as data*
5. `overall_improvement` divided by zero for a user whose only gradient-bearing hard skill is outside the current
   plan (a job type changed since): one such user aborted the whole founders' report. Fix: skills with zero weight
   do not count.
6. The 49-day level window and 180-day gradient window admitted anything younger than N + 1 days; now strict, like
   the hard skills' expiry. The assessment also carries the count the gradient rests on (`gradient_answers`),
   so the report no longer prints a verdict next to a count that does not support it.
7. Superseded answer revisions (a retry after a failed evaluation) were read by the XP and soft-skill readers; now
   excluded in both stores.
8. In the interview, relatedness was judged on the check-adjusted scores (a truth-table pass raises the floor) and
   after the metrics row had copied the flags; now on the judge's own output, before the row is built, as in
   practice. And the "did not address the question" verdict was visible mid-interview while the band was hidden;
   now it is revealed with the results.
9. `related_to_question(flags=None)` crashed; defensive now.

*Routes*
10. An in-flight interview answer replayed with the same key returned 200 with an `evaluating` turn; the route now
    answers 202 for that state, as it does on its own timeout, so the client polls.
11. `/health` told any anonymous caller the environment, the model ids and the pooler mode. With `HEALTH_KEY` set on
    Render, that detail needs the `X-Health-Key` header; anonymous callers get status, build and provider (the web
    app reads the provider to decide demo mode). Unset, the body is unchanged — Shaked sets the key when he wants.

**Found, accepted for now (written down, not fixed)**
- The address budget is shared by everyone behind one NAT by design: one abusive client on a campus network locks
  out that network's other users for a minute. Acceptable for the pilot; a per-user budget after authentication is
  the real fix at scale.
- Harel's storage trigger takes the parent row lock before it checks ownership, so a user who learns another's
  attempt id can take that lock for the duration of a failing upload. A nuisance at most; the cheap hardening
  (check ownership with a plain SELECT first) is a migration, hence Shaked's approval.
- The question cache has no single flight at the servable list's 60-second expiry (pre-existing).
- `soft_skills_report.py --json` holds user ids; a bare file name now lands in `backend/workdir/`, which git
  ignores.
- The empty-answer branch of the evaluator is unreachable from text input (both services refuse empty text first);
  if reached it reads as unrelated.

**Checked and found sound by probe:** the advisory lock is taken before the count on both start paths and never
held across a model call; the lock order `_user_lock → transaction → lock_usage` is the only one used, so no cycle;
the in-memory lock is released on exceptions and on the StaleProfile retry; the interview lock map empties after
every answer and after a not-found lookup; the same-key replay never shows half-written state and makes no second
model call; the `off_topic` flag survives every save path and a restart; the evidence readers filter by user, sort
on aware timestamps and exclude running interviews; the revealed reference is reachable only by the attempt's
owner, only after reveal, only for that question; no remaining path executes submitted or model-written code; the
flags list never echoes caller strings; the soft-skill reading is reachable from no HTTP route; the migrations
revoke nothing the browser app uses; no new logging of bodies, tokens or emails.

### Performance (no fix needed)

- Submit and progress paths carry the same statement counts as before the week's changes (13 / 3 transactions and
  12 / 1).
- The advisory lock adds one statement per practice start and two per interview start (Harel kept the early
  unlocked count as a fast refusal; a COUNT per start, acceptable). The lock is never held across a model call.
- The soft-skill reading: 5 statements and about 30 ms for 500 answers and 50 interview turns; linear beyond that.
- The rate limiter costs 16–25 µs per request with 10,000 buckets present; the health probe is single-flight.
- Noted, pre-existing: the question cache has no single flight at the servable list's 60-second expiry; a caller
  rotating 10,000 identities evicts a legitimate heavy caller's bucket. Neither matters at pilot load.

### For Harel (web)

Done since his to-do file: the brackets (his own `bidi-segments.ts`), the `map` / `same_skill` labels. Not done:
the "no XP" sentence, `source: "search"`, the interview length from the plan table, the "carried" badge, the typed
fields, the harness entry. New: the interview report shows the fit as a percentage and the subject donuts "N of M
assessed" (Shaked's words-not-numbers rule, pre-existing); a missing test for Hebrew hyphen prefixes in the new
splitter; a solution that would spin forever on an English-only question (none exists today); the password cleared
on the initial auth event. Auth, headers, dictation, the truth table and the revealed-reference gating all check
out. Details in `docs/harel-todo-2026-10-18.md`.

## 4. Lessons

- A hardening change deserves the same adversarial probe as a feature: two of Harel's security fixes (the LRU
  buckets, the raw-header key) opened small new holes that a ten-line probe found.
- The soft-skill reading met its first real users within hours of being written and the review found the exact
  case (a changed job type) that would have crashed the founders' report on the fifth pilot user. Backend-only data
  still needs the full check.
- Three reviewers were cut off by the session's rate limit mid-probe; rerunning them with a tool-call budget made
  them finish faster and no less thoroughly.
