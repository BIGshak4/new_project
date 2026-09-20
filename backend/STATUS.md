# Backend status

A living summary of what exists in `backend/`, how it was verified, what was decided, and what is next.
Updated at the end of every build step. Newest changes are at the bottom of the changelog.

> **Deployment operations update (20 September):** Both Netlify frontends now deploy automatically from Git, with successful push-to-live verification. The existing Render service is already in Frankfurt and uses the real Anthropic provider. The server-only Storage credential is now configured and `/health.answer_images` reports `assessed`. See [the deployment repair report](../docs/deployment-repair-2026-09-20.md) for current checks and remaining human-review steps; older scripted-provider / missing-photo-key notes below are historical.

**Last updated:** 2026-09-21 (overnight build §5i deployed) · **Tests:** 610 offline + 16 live + `scripts/smoke_http.py` against Render · **Latest commit:** see changelog

---

## 1. What the backend is

The "brain" of the platform, as specified in `src/AI_Engine_Spec.md`. It evaluates a candidate's answer, decides what to ask next, keeps the candidate's skill profile, and plans their week. The model (Claude) only scores answers and words questions; every decision is plain Python that can be tested and replayed.

Harel's Next.js apps (`apps/web`, `apps/tasks`) are the face of the product. The backend does not have a UI; in step 5 his app will call it.

---

## 2. Build steps so far

| Step | What | Commit | Status |
|---|---|---|---|
| 1 | Database schema in Supabase: 30 tables, row-level security, indexes, structural seed | `d7744f9` | Done, live |
| 2 | The engine, seeds, terminal practice tool, seed loader, FastAPI shell | `40dd1c8` | Done |
| 3 | Harel's 30 questions enriched for the engine (skills, rubrics, hints, errors, checks) | `18bfaa2` | Done, files only |
| 4a | Engine hardening for real-world use, from Harel's review (`docs/backend-review-for-shaked.md`, R1–R5) | | Done |
| 4b | HTTP API per the contract in `docs/backend-frontend-integration-readiness.md`: A login + pilot access (`74eea90`), B migration `practice_submissions` applied (`865b83c`), C repository + D service (`8eb0fce`), live sweep (`62fa488`), E routes + F route tests (`685827c`), verification pass (`b9670dc`), G: content loaded, Docker image verified, **deployed at https://jobrun-api.onrender.com** (staging, scripted model, pooler DB) | | Done |
| 5 | `apps/web` wired to the API by Harel (quick mode, code editor, 202 polling, refresh recovery; browser reads of questions closed by his migration). P0 done: provenance per revision, demo data wiped. Next: P1 real model (needs the key) → P2 feedback check → joint review (`docs/shaked-human-review-handoff.md` §5) | | P2 done: 13/13 review answers judged correctly; numeric-check bug fixed. Next: joint review session |
| 5 | Connect `apps/web` to the API (with Harel) | | |

---

## 3. What exists, file by file

### Engine (`app/engine/`)

| Module | Role | Spec |
|---|---|---|
| `params.py` | Every threshold and weight in one place; assumptions marked | all |
| `checks.py` | Deterministic checks: truth table (safe Boolean parser, bounded input), numeric with named values | Data_Models §13.4 |
| `scores.py` | Bands, k/c updates, evidence weights, levels, priors, observed skills, calibration | §2, §3.1 |
| `plan.py` | Role set + company set + user focus → session skill plan | Data_Models §6.3 |
| `skill_controller.py` | Layer 1: escalate / hold / hint / step back / resolve (full transition table) | §3 |
| `subject_router.py` | Layer 2: subject status, next subject and skill, entry difficulty, rebalancing, fatigue and ending overrides, bridges, hard clock stop | §4 |
| `session.py` | One simulation turn end to end, no I/O | §4.9 |
| `practice.py` | One deep or quick practice question end to end: hints, reveal, submit, follow-ups, feedback, tip. Answers are accepted as immutable revisions with idempotency keys, evaluated with their own status, scored exactly once, and restorable after a restart | §1.1, §6.6 |
| `plan_router.py` | Across days: next activity with a plain-language reason, weekly plan, retention checks, diagnostic | §4.11 |
| `scorecards.py` | Role/company/overall fit with core-gap caps, profile roll-up, target fit | Data_Models §7 |
| `bank.py` | Bank-first question selection, coverage per skill | §1.2 |
| `catalog.py` | Loads and validates every seed file together | Data_Models §12 |
| `providers.py` | `ScriptedProvider` (tests), `ManualProvider` (request/reply files, no key), `AnthropicProvider` (Opus 5); `call()` puts a per-role deadline on every model call | Build guide §7 |
| `evaluator.py`, `generator.py`, `tips.py`, `feedback.py`, `reporter.py` | The model-facing roles, each with a fallback if the call fails | §2.3, §5, §6, §7 |
| `i18n.py` + `prompts/` | Versioned prompt per role; Hebrew and English language blocks; glossary injection | Data_Models §17 |

### Content (`seeds/`)

| What | Count | Notes |
|---|---|---|
| Subjects | 6 | Match the database seed |
| Skills with 5-level rubrics | 35 | `seeds/skills/digital_hardware.json` |
| Roles | 1 | Digital Hardware Engineer, `student` and `junior`, weights sum to 1.0 |
| Companies | 1 | Generic |
| Questions | 30 | Harel's bank, enriched; all `in_review` |
| Tips | 10 | Rule-triggered, bilingual |
| Glossary terms | 30 | Which terms stay in English inside Hebrew |

### Tools (`scripts/`)

- `cli_practice.py`: the whole coaching loop in the terminal. Works without an API key.
- `seed_db.py`: validates the seeds (`--check`), upserts them into Supabase, `--dry-run` reports and rolls back.
- `dry_run_sql.py`: runs a migration file in an explicitly opened, always-rolled-back transaction and proves nothing it creates is left behind. Required before asking for approval to apply a migration.
- `build_example_bank.py`: merges Harel's `example_question/questions.json` with `seeds/questions/enrichment/*.json`.

### App shell (`app/`)

`main.py` with `/health` and `/catalog/summary`; `config.py` (settings from `.env`); `db.py` (async Supabase connection, tables reflected from the live schema).

---

## 4. How it was verified

- **370 tests**, about 4 seconds, no network. They are built from the worked examples in the specs: the §6.3 merge table, every row of the §3.3 transition table, the §4.5 entry-difficulty cases, the fit caps, the roll-up weights.
- **Persona bots** run whole sessions (always strong, always weak, weak in two subjects, strong then collapses) and check the promises: no hint followed by an escalation, weak core subjects get extra turns, strong subjects close early, the fatigue override fires.
- **40 randomized sessions** assert invariants: terminates, difficulty in range, never re-enters a resolved skill, never targets an observed skill, budgets never negative, at most one turn past the clock.
- **Fuzzing** of the Boolean parser (20,000 random inputs, deep nesting, 60,000-term chains): rejected cleanly, never crashes.
- **A real practice session** was run in the terminal with the manual provider: wrong XOR answer → check fails → WEAK → feedback card and tip → level-1 hint → strong recovery → HOLD (not escalate) → probe on the one missed point → profile saved.
- **Seed loader** checked column by column against the SQL schema; every deterministic check self-tests against known-good and known-bad answers.
- Two independent review agents were started; both were cut off by session limits, so their open leads were verified by hand (and were real: stale subject status at rebalance time, no hard clock stop, parser recursion).
- **Live verification against Supabase** (`tests/test_live_db.py`, `tests/test_live_service.py`, run only with `DATABASE_URL`): the whole service on the real database inside one rolled-back transaction (`tests/livetools.py: RollbackStore`). All 30 questions complete the loop in English and Hebrew; refresh and restart replay without a model call; outage then retry; three simultaneous submits score once; the daily limit counts real rows; a stranger gets `not_found`; as a signed-in user through RLS the card is readable but `evaluation`, `evidence_weight`, `engine_state`, `knowledge_score` are denied and another user sees nothing; re-seeding keeps Harel's question ids and a published question's review; listing 30 questions takes ~1 s. Bugs it found: scores scaled ×100 twice (numeric overflow), JSON `null` written for absent cards (constraint violation), 20 tables with policies but no client grant, `reuse_status` overwritten on re-import of a published question, N+1 question loading (11 s).
- **Chaos test** (`tests/test_chaos.py`): random users, attempts, actions (hint / reveal / submit / same key / follow-up / retry / refresh / restart) run concurrently against a model that fails at random; invariants: one revision per key, scores once per done revision, metrics rows = done revisions × skills, a restarted service sees the same attempt, no evidence after a reveal. A 20-seed run covered 1,026 attempts, 98 failures, 43 retries, 162 reveal-then-answer cases.
- **Anthropic provider with a fake SDK client** (`tests/test_anthropic_provider.py`): what is sent (model, cached system blocks, effort per role, structured output, fallbacks) and how every SDK outcome maps (parsed, refusal, cut-off, 429/5xx retryable, 4xx not, connection error). The path that runs once the key exists has now run.
- **`scripts/smoke_http.py`**: starts a real `uvicorn` process (or targets `--url` of a deployed instance) and checks health, docs, all eleven routes in OpenAPI, CORS preflight allowed/refused, 401/404/405/413 error shapes, forged token → 401, and that the project's real JWKS is reachable and loads into the verifier.
- **Real-world behaviour tests** (`tests/test_practice_hardening.py`, 42 tests): double clicks and four simultaneous submits score once; the same key with a different answer is a conflict; the evaluator being down or stalling keeps the answer and a retry scores once; a hint or reveal after submitting does not change the evidence of the answer already given; a refresh or server restart shows the same card, tip and follow-up without re-scoring; a restart mid-evaluation leaves a retryable submission; every model role is metered, unknown model prices are "unknown", never free; re-importing an unchanged question keeps its review status; forged protocol tags in an answer are neutralised; the local store recovers from a corrupt file.

---

## 5. Decisions made along the way

| Decision | Why |
|---|---|
| Supabase Auth instead of Clerk | RLS policies can use `auth.uid()`; one fewer account |
| Clients only read their own rows; the backend (service role) is the only writer | An evaluation must come from the engine, never from the browser |
| `question` has no user-facing read policy | RLS is per row; it would expose reference solutions and hints. Harel added a founders-only read policy for his review app, which is fine |
| Decision logic is code, the model only evaluates and words | Reproducible, cheap, testable (core spec principle) |
| One provider interface with a manual mode | The whole loop runs before an API key exists |
| Harel's `questions.json` is the source of question text; enrichment lives beside it | No double source of truth; reviewers see only what was added |
| Hints stored as plain string arrays | The format Harel's app already renders |
| `EXPLORING` subjects keep the core-gap bonus (§4.3) | The formula as written contradicts the §4.10 worked session; the prose rule wins |
| A first assessment does not schedule a retention check | §4.11 says "when a level rises"; there was no earlier level |
| Generated follow-ups carry no exposure penalty | They are new to everyone |

Assumptions where the spec was silent are marked `ASSUMPTION` in `params.py` and `scores.py` (student prior 32, latency normalization, level when no STRONG answer exists).

---

## 5a. Step 4a: what "hardened" means here

Harel's review (`docs/backend-review-for-shaked.md`) asked for five things before an API is built on the engine. All five are in, with a test for each:

| Finding | What changed |
|---|---|
| R1 exactly-once scoring | Every answer is a `Submission` revision with an idempotency key. A replay returns the stored outcome (`replayed=True`); a different answer under the same key is a `conflict`; a second main answer after an evaluated one is `already_submitted`. Concurrent duplicates are serialised by a lock. |
| R2 answers survive failure | Acceptance and evaluation are separate. `EvaluationStatus` is pending / evaluating / done / failed. A failed evaluation keeps the answer; `retry_evaluation()` scores it once with the original exposure. |
| R3 evidence bound to exposure | Every hint and reveal is an `ExposureEvent`. Each submission snapshots `hints_seen` / `reference_seen` at acceptance, so peeking after submitting changes nothing, and a retry keeps its evidence. `hint_at(level)` re-reads an exposed hint without advancing. |
| R4 tips metered | `tips.compose()` returns `ComposedTip` with model, usage and latency; it is recorded like every other model call. `cost_usd()` returns `None` for an unknown model (never 0). |
| R5 re-import keeps review | `seed_db.py` hashes the content of each question; an unchanged question keeps `status`, `reviewed_by`, `reviewed_at` and translation parity. A changed one is reset to `in_review` and reported. `--dry-run` shows the report and rolls back. |

Further real-world bugs found while probing, and fixed: a hanging model call now hits a per-role deadline and becomes a retryable error (`providers.call`); a server restart rebuilds the attempt from `attempt_row()` via `PracticeAttempt.restore()` (card, tip, follow-up and check are stored on the revision, nothing is re-scored, the struggle budget is not reset, a submission caught mid-evaluation becomes retryable); the API answer shape `{"text": ...}` replays like a plain string; a `PracticeError` carries a stable code for the API; absent behaviour signals are False, unknown signals never match a tip; a corrupt local store file is set aside and recovered from.

Deferred to 4b, because they belong in the persistence layer: a database uniqueness constraint on `(attempt_id, idempotency_key)`, optimistic versioning of the skill profile, and usage limits. (All three are now in: stage B migration, `app/repo/profiles.py`, `PracticeService.start`.)

## 5b. Step 4b so far: the API layer underneath the routes

| Stage | What exists |
|---|---|
| A | `app/auth.py` verifies Supabase tokens (JWKS ES256, issuer, audience, expiry); `app/repo/users.py` pilot access from `jr_members`; `app/api/errors.py` one error shape; `GET /v1/me` |
| B | Migrations `practice_submissions` (revisions with unique idempotency key, `attempt.exposures/engine_state`, `user_skill_profile.version`), `skill_profile_engine_state`, `client_read_grants` |
| C | `app/repo/`: `questions.py` (database is the runtime source; safe summaries; four-query batch load; short caches), `attempts.py`, `profiles.py` (optimistic versioning), `events.py`, `cache.py` |
| E | `app/api/v1/questions.py`, `practice.py`, `me.py`: the eleven contract routes; `app/runtime.py` builds catalog, provider, store and service once at startup; `app/services/demo_provider.py` (`LLM_PROVIDER=scripted`) gives instant fake evaluations so the web app can be built without a key; request log line per request (id, route, user, status, ms; never bodies or tokens); unexpected errors are a 500 with a request id, never a traceback |
| F | `tests/test_api_routes.py` (46): the flow over HTTP, idempotency (header, body, generated key, conflict), reveal-then-answer, outage → retry by revision, every bad input is 422, wrong follow-up turn, daily limit 429, every `/v1` route in the OpenAPI document has a no-token and non-member test (the test fails if a route is added without one), another user's attempt is 404 on every route. Live: the real app with `DbStore` through the rollback harness (found: a token for a deleted account was a 500, now 401) |
| D | `app/services/store.py` (`DbStore`, `Tx` boundary), `memory_store.py` (same rules in memory), `practice_service.py` (start / get / hint / reveal / submit / follow-up / retry / progress; answer saved before the model call; one transaction per result; profile conflict keeps the answer) |

Rule learned the hard way: **every migration goes through `scripts/dry_run_sql.py` first**, and every writer goes through `db.sql_values()` so Python `None` is SQL NULL, never JSON `null`.

---

## 5c. Independent code review (2026-09-19) and profiling

A fresh reviewer read the API, service, repository, auth and engine-practice layers with the deployment in mind (Render, several workers, remote database). Thirteen findings, all fixed the same night, each with a regression test:

| # | Finding | Fix |
|---|---|---|
| 1 | Two workers could both accept "revision N" with different keys; the second upsert silently overwrote the first, so the unique idempotency key never fired | New revisions are a plain `INSERT … ON CONFLICT DO NOTHING` (no row → reload, replay or 409 `conflict`); existing revisions an `UPDATE … WHERE status <> 'done'` (no row → `AlreadyEvaluated` → the winner's result is returned, the loser's usage still recorded) |
| 2 | `restore()` marked any pending revision as failed at once, so a refresh during a live evaluation showed "failed / retry" and a retry could double-score | `evaluating_since` stamp; a revision counts as interrupted only after `EVALUATION_BUDGET_SECONDS` (10 min); until then the view says `evaluating`, retry/submit are refused |
| 3 | On a profile version race the evaluation was thrown away (a retry re-ran every model call and left a dangling follow-up) | The scores are re-applied on top of the fresh profile with the pure scoring functions (`_rescore`); no second model call. Only a second race falls back to "failed", with the follow-up turn undone |
| 4 | `StaleProfile` in `start` / `next_hint` was a 500 | Redone once with a fresh load, then 409 `conflict` |
| 5 | Route timeout (300 s) was shorter than the worst-case chain of model deadlines and could cancel mid-persist | Submit answers **202 `evaluating`** after 120 s and the evaluation continues shielded in the background; clients poll `GET` (`waitForEvaluation` in the TS client). Per-role deadlines lowered (evaluator 90 s, generator 60, feedback 60, tip 30) |
| 6 | Pilot access resolved with ~7 round trips on every request | Cached per user for 120 s |
| 7 | Every save re-upserted every revision; metrics and usage inserted row by row | Only changed revisions are written; multi-row inserts |
| 8 | Lock table cleanup skipped when an action raised | `finally` |
| 9 | Lost duplicate-key race could 500 | 409 `conflict` / replay |
| 10 | Schema reflection ran on the first user request per worker | At startup, under a lock |
| 11 | `first_assessed_at` never set on the update path | `coalesce(first_assessed_at, now())` |
| 12 | Member e-mail compared case-sensitively; production allowed the pilot gate off; unverified e-mails accepted | `lower()` on both sides; `REQUIRE_PILOT_MEMBERSHIP=false` is a production problem; `email_verified: false` is refused |
| 13 | An unknown key id refetched the JWKS on every request | Unknown kids remembered for 5 minutes |

**Profiling** (`scripts/profile_service.py`): in memory, a full loop (start → hint → submit → follow-ups → refresh → progress) is ~66 ms, 60% of it Pydantic validating skill states — negligible next to the database. Against Supabase from the dev machine (~130 ms per round trip; Render sits in the same region as the database, so roughly a tenth of that): before the fixes a submit made 26–28 statements (3.7–5.3 s), a refresh 6 (0.8 s), the first listing 5 (1.4 s); after them a submit is 18 statements (2.3 s on that link, and 4 of the 18 are the test harness's own savepoints), the rest unchanged. The in-memory store deep-copied everything on every transaction and got slower with every attempt; it now copies containers only.

## 5d. First production run and full verification (2026-09-19)

With the founders' session token, the whole chain ran on Render: login → 30 Hebrew questions → start → hint → wrong answer (truth-table check failed, WEAK, reduced evidence, feedback card, tip, follow-up) → same click replayed for free → two follow-ups STRONG → refresh identical → progress (`boolean_algebra` level 2 assessed, `truth_tables` insufficient evidence). First call 23 s (free-tier wake-up), the rest 0.2–0.4 s. That attempt is real data under the JobRun account.

Full bench afterwards: ruff; 513 offline tests; chaos sweep 40 seeds × 4 users × 80 steps (1,982 attempts, 197 failures, 75 retries, 70 superseded revisions, all invariants held); TypeScript typecheck + contract test; Docker image built from the latest code, healthy in 15 s, smoke green; Render smoke green; seed loader dry-run: all 30 questions unchanged, review state kept; live suite against Supabase.

Bugs found and fixed by this pass:
- **A superseded answer could be scored.** Main answer fails → user sends a new one → it fails → retry fixes the new one → a second retry picked up the *old* revision and scored it too (two scored main answers, two dangling follow-ups). Older revisions of a turn are now flagged `superseded` and never retried; chaos invariant: at most one scored revision per turn.
- TypeScript client said `insufficient` where the engine says `insufficient_evidence`; the contract test now checks enum values.
- Deployment config: a wrong `DATABASE_URL` failed with a misleading "password authentication failed"; startup now names the mistake (plain `postgres` user on the pooler, placeholder left in, characters needing percent-encoding), and pasted values are stripped of whitespace (a trailing newline made Postgres look for a database called `postgres
`).
- Live test harness: one transaction held open for ~10 minutes gets dropped by the pooler; each live test now uses its own connection and transaction, and the 30-question sweep runs in three chunks. Tests measure deltas, since the founders' account now has real attempts. The pooler also resets connections sporadically under sustained load from a home connection, so the API now answers a dropped database connection with **503 `temporarily_unavailable` + `Retry-After`** (the transaction rolled back atomically; nothing is lost) and retries the read-only load once.

## 5e. Harel's integration and P0 (2026-09-19)

Harel wired the practice page to the API (six commits, documented in `docs/shaked-human-review-handoff.md`, `pilot-integration-handoff.md`, `guided-practice-and-assistant-handoff.md`): every attempt is **`quick` mode** (one answer, no automatic follow-ups shown), a CodeMirror editor whose output arrives as explanation + fenced code (the deterministic checks parse Verilog/C/text inside fences — verified), 202 polling, refresh recovery by attempt id, Hebrew demo output, and a migration (`restrict_practice_question_reads`) that removes all browser access to `question`/`question_translation` and `attempt.follow_up_turns` — his R6 closed. Merged code: 531 tests + 16 live green. Migration file versions were aligned with the live history (the MCP tool assigns its own timestamps: keep file names equal to `supabase_migrations.schema_migrations`).

**P0 (demo vs real):** `attempt_submission.evaluator_model` (migration `submission_provenance`, applied); `SubmissionView.assessed_by` = `demo` | `model` plus the model id, so scripted results can never pass as real; startup warns when a non-Anthropic provider writes to the real database; the demo assessment rows were wiped with approval (8 attempts, 6 submissions, 9 metrics, 23 usage, 3 tips, 5 profiles; accounts, notes and the task board kept). All three founders' accounts (`jobrunerai@`, Harel's, Shaked's) are on `jr_members`, confirmed.

**Hardened before P1:** a 400 naming the fallbacks beta disables fallbacks and retries; a 400 rejecting the structured-output schema falls back to JSON-in-text; submit response budget 90 s (Render's proxy limit is 100 s). Open calibration question from Harel: `quick` base evidence weight is 0.3 (`params.py`) — now that quick is the whole flow, revisit after the first real session.

## 5f. P1: the real model (2026-09-19)

First real Claude calls, locally then through the service into production under Shaked's account (quick mode, as the site sends it):

| | Hebrew, wrong answer (sensor majority) | English, mostly-right answer (mod-6 counter) |
|---|---|---|
| band / check | WEAK, truth-table check failed 6/8 | PARTIAL (caught that 6/7 recovery sat inside the enable branch and that the requested trace was missing) |
| misconception | `xor_confused_with_majority` found | none |
| wall time | 43 s | 41 s |
| cost | ≈ $0.076 per answer: evaluate $0.038 + card $0.034 + tip $0.004 | |

Prompt caching works (second evaluation of the same question: 3,978 tokens read from cache, $0.010 instead of $0.034). Structured output and the fallbacks beta were accepted by the account, so neither downgrade path fired. Feedback card at low effort: same quality in ~10 s instead of ~16 s → `ROLE_EFFORT["feedback"] = "low"`, max 2,000 tokens. Tip polish sometimes echoed the `<tip>` delimiter → stripped. Render runs `LLM_PROVIDER=anthropic` (`ENV=staging`); `/health` confirms. The key was rotated once during the session (a revoked key shows as `401 API key is invalid` and the card falls back to the template, as designed).

## 5g. Cost: the Opus/Sonnet mix (2026-09-20)

Model per role is configuration (`ANTHROPIC_MODEL` for the judge, `ANTHROPIC_ROLE_MODELS` for the prose roles; `/health.models` shows the split). Default: **evaluator on Claude Opus 5; feedback card, tip and generator on Claude Sonnet 5.** A second cache point on the shared instructions block means the ~3k-token role prompt is cached across questions, not only per question.

Same two answers as P1: **$0.106 vs $0.152** with Opus everywhere (−30%), 36 s / 22 s instead of 43 s / 41 s, both caches cold. Per answer: ≈ $0.05 cold, ≈ $0.025 warm (evaluator $0.039 cold / $0.010 warm, card $0.012, tip $0.002). For a heavy learner (300 answers/month) that is $8–15 on this mix versus $20+ on Opus alone; Sonnet as judge too would roughly halve it again — to be decided on the golden set, not by feel.

## 5h. P2: the review answer set (2026-09-20)

`scripts/p2_review_set.py` ran 13 answers (prose only, code only, Hebrew + C, formulas, a different valid approach, prompt injection, irrelevant text, confidently wrong, one-liner) through Opus 5 with Sonnet 5 cards, without database writes: **13/13 bands as a careful human would judge**, misconception keys precise, injection scored as content and named, alternative approach credited. $0.26. Report: `docs/p2-feedback-review.md`.

Bug found and fixed: the numeric check took the *first* number after the name, so `Tmin = 0.12 + 1.10 + 0.18 = 1.40 ns` was checked as failed ("got 0.12") — and a failed check overrides the score. The locator now takes the last quantity with a compatible unit in the clause; the clause ends at the next assignment. Nine regression cases; the seed self-tests caught the first attempt.

## 5i. Overnight build (2026-09-20 → 21): next question, subject charts, code tests, visual assessment

Shaked asked for five things before sleeping; all five are built, tested offline and wired into Harel's app.

1. **Next suggested question after every evaluation** — `app/engine/next_question.py`. WEAK → *reinforce* (same skill, easier or equal, unseen); PARTIAL → *consolidate* (same skill, same level); STRONG → *advance/explore* (the skill the role plan weights most among those below their required level). Deterministic, explained in one sentence in the practice language, only ever a servable question. Stored in the attempt's `engine_state.next_question` so a refresh shows the same; exposed as `next_question` on `SubmissionView` and `AttemptView`.
2. **Subject-level progress for charts** — `ProgressView.subjects`: per subject the plan's skills (total / started / assessed), level histogram, STRONG/PARTIAL/WEAK answer counts (one grouped query joining attempt → question → skill), plan weight, questions available. Harel's `apps/web` progress page now opens with one donut per subject (`subject-charts.tsx`, inline SVG, no library; helpers in `lib/charts.ts` with unit tests).
3. **Code checking** — new deterministic check `code_tests` (`app/engine/code_runner.py`): the Python in the answer runs against the question's cases in a child interpreter (`python -I -S`), after an AST audit (allow-listed imports, no open/exec/eval/`__import__`/introspection), with restricted built-ins, a wall-clock timeout, and memory/CPU limits where the platform allows. C, pseudocode or prose → `passed: null` (the model still reviews). Specs + self-tests authored for 7 software questions (count set bits, power of two, register field, lower bound, merge, pair sum, balanced brackets); the loader runs the self-tests in-process through the same harness. **The database still has the old rows: `seed_db.py` must be re-run (approval) for the checks to reach production.** The check runs in a thread so it never blocks the event loop. The database constraint on check types needs the migration `20260920064052_code_tests_check_type.sql` before the rows can be loaded (found by the live suite; §6).
4. **Visual assessment** — a drawn circuit becomes a netlist (`app/engine/circuit_text.py`) plus derived Boolean functions for one-bit combinational logic; the evaluator gets it in `<candidate_circuit>` and the truth-table check tests the derived function (a drawn majority gate passes the same check as a typed one). Photos are fetched server-side from the private bucket with the service-role key (`app/services/storage_images.py`, bytes sniffed again) and sent to Claude as image blocks (`LLMRequest.images`). Harel's early return ("visual → unassessed") is gone; only a photo-only answer that the server cannot read stays `unassessed`. **Needs `SUPABASE_SERVICE_ROLE_KEY` on Render and in `.env`** — until then photos are stored, not judged (`/health.answer_images`).
5. **An attractive evaluation** — `apps/web/src/components/evaluation-panel.tsx` replaces the old feedback block: band ring, summary, chips (check, circuit/photos assessed, evidence, judged-by), the automatic check with a table of differing rows / failing test cases, the four-part card as tiles, what went well / what to work on, the coaching tip, and a "suggested next question" card with the reason and a start button. Styles appended to `globals.css`.

Independent review of the new modules (one reviewer agent, findings verified by execution) found and I fixed: a sandbox escape through `operator.attrgetter`/`methodcaller` (run-time attribute lookup past the AST audit; `operator` and `string` removed from the allow-list, `typing.get_type_hints` and `from … import *` refused), the child interpreter inheriting the API's environment (now a minimal env, temp cwd), and prompt injection through a code test's `got`/`error` text into the `<check_result>` block (now neutralised like the answer). Remaining known limits: `str.format` gives a read-only attribute route; no memory cap on Windows dev machines (Linux/Render has rlimits).

Verification: `ruff` clean; **610 offline tests** (was 557; new: `test_next_question.py`, `test_code_tests.py`, `test_visual_assessment.py`, Harel's `test_visual_answers.py` updated to the new behaviour); TS client contract test passes with the new fields; `apps/web`: `tsc --noEmit` clean, 33 unit tests; live suite and `next build` results in §8.

## 6. Known gaps and open items

- **Content is loaded** (2026-09-18): 41 skill rows, role, company, 10 tips, 30 glossary terms; the 30 questions have 50 skill links, 60 translations, 3 hints each, 3 deterministic checks. All still `in_review`; the pilot serves them with `ALLOW_IN_REVIEW_CONTENT=true` until the first ones are published.
- **Deployed**: https://jobrun-api.onrender.com (Render free tier, Frankfurt, `ENV=staging`, `LLM_PROVIDER=scripted`, `ALLOW_IN_REVIEW_CONTENT=true`). `scripts/smoke_http.py --url https://jobrun-api.onrender.com` passes, including CORS from `https://jobrun-practice.netlify.app`. Free tier sleeps after 15 idle minutes (~40 s wake).
- `backend/Dockerfile` and `render.yaml`: the image builds (345 MB, non-root, healthy in 10 s) and passes `smoke_http.py` in a container. **The database string must be the Session pooler (IPv4)**: the direct `db.<ref>.supabase.co` host is IPv6-only and unreachable from containers and Render (found by running the container; `/health` now reports `database_host` and production refuses `direct`). The Render service itself must be created under a JobRun account and given `DATABASE_URL` and `ALLOWED_ORIGINS`. Then `scripts/smoke_http.py --url <render url>`.
- **Done 2026-09-21 with Shaked's approval:** migration `20260920064052_code_tests_check_type` applied (the constraint had allowed only `truth_table | numeric | sim`, which the live suite caught), content reloaded (7 questions updated, ids and review state kept), live suite rerun (result in §8).
- **`SUPABASE_SERVICE_ROLE_KEY` not set anywhere yet:** photos attached to answers are stored but not judged until it is added to Render (and `backend/.env` for local runs). Server-only secret.
- **Review before publishing.** All 30 questions stay `in_review` until a person checks technical correctness, rubric weights and Hebrew/English parity (checklist in `seeds/questions/README.md`).
- **Bank coverage: 14 of the role's 27 skills** have a primary question. Missing: latches/flip-flops, state tables, Moore vs Mealy, truth tables, number representation, reset strategies, sequential HDL coding, debugging methodology, project walkthrough, state encoding, testbench basics.
- **Small schema follow-ups** for a later migration: a per-language template column on `tips_library` (Hebrew tip text lives only in the seed file); the `question.hints` column comment describes the old object format.
- **Placeholders** `app.py`, `requirements.txt`, `src/__init__.py` still in the repo; deletion not yet confirmed.
- Backend notes from the performance review, for step 4: generate UUIDv7 ids for the append-only tables; cap `state.history_window`; write daily-allowance checks as `created_at >= day_start`.

---

## 7. How to run it

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload              # the API: http://127.0.0.1:8000/docs is the contract
uv run pytest -q                                   # 598 tests (16 more run when DATABASE_URL is set)
uv run python scripts/seed_db.py --check           # validate content
uv run python scripts/cli_practice.py --debug      # practice in the terminal, manual provider
uv run python scripts/cli_practice.py --language he
```

For the web app: `.env` with `SUPABASE_URL` (login verification), `ALLOWED_ORIGINS=http://localhost:3000`, `LLM_PROVIDER=scripted` (instant fake feedback, no key). Without `DATABASE_URL` everything runs in memory with the seed questions. Send the Supabase access token as `Authorization: Bearer <token>`; the e-mail must be in `jr_members`.

With the manual provider, each model call appears as `workdir/manual_llm/NNN_<role>.request.md`; write the reply as `NNN_<role>.response.json` and the loop continues.

---

## 8. Changelog

| Date | Change |
|---|---|
| 2026-09-17 | Step 1: schema designed from `Data_Models.md`, reviewed by 25 agents, dry-run in a rolled-back transaction, applied to Supabase; 44 review findings, 40 fixed; performance items applied |
| 2026-09-17 | Step 2: engine, seeds, practice CLI, seed loader written; 272 tests |
| 2026-09-17 | Harel pushed `apps/web`, `apps/tasks`, three `jr_*` migrations and the 30 questions into the database |
| 2026-09-18 | Step 2 hardening: stale subject status at rebalance, hard clock stop, parser bounds, prose-tolerant expression extraction; 324 tests; committed and pushed |
| 2026-09-18 | Step 3: enrichment files, build script, named-value numeric check, shared code in prompts, hints as string arrays, two tips; golden set folded into Harel's keys; 328 tests |
| 2026-09-18 | Harel's review and integration checklist landed in `docs/` (`be08576`) |
| 2026-09-18 | seed_db: None → SQL NULL for jsonb columns, found by the first live dry-run (`afc48a9`) |
| 2026-09-18 | Step 4b-A: settings, Supabase token verification (JWKS/ES256), pilot access via `jr_members`, error shape, `/v1/me`; 392 tests (`74eea90`) |
| 2026-09-18 | Step 4b-C/D: repository layer, store boundary, practice service; migration `skill_profile_engine_state`; 409 tests (`8eb0fce`) |
| 2026-09-18 | Live verification sweep: RollbackStore harness, 13 live tests; fixes: JSON null in every writer (`db.sql_values`), batch question loading + caches, `reuse_status` preserved on re-import, migration `client_read_grants` (20 tables had policies but no grant) |
| 2026-09-21 | Render build of the overnight push failed (`ModuleNotFoundError: httpx` — it was only a dev dependency; the SDK now depends on `httpx2`), so the old build kept serving and the earlier "redeployed" note was wrong. Fixed in `97d9eaf` (runtime dependency, verified with `uv sync --no-dev` and inside the Docker image) |
| 2026-09-21 | Migration `20260920064052_code_tests_check_type` applied and content reloaded with approval (7 questions updated). Live suite from Shaked's machine: 11/16 passed in the full run (HTTP flow, RLS, double clicks, outage retry, seeding, Hebrew); the loop blocks passed alone (4 min 47 s) but the full run and a rerun hit repeated pooler connection drops (`connection was closed in the middle of operation`, WinError 121) with no feature assertion failing anywhere — network on the night, to be rerun from a stable connection or inside the Docker image |
| 2026-09-21 | Overnight build (§5i): next suggested question, subject progress + donut charts, `code_tests` check with sandboxed runner (7 questions), circuit netlist + photo assessment, evaluation panel in `apps/web`; 598 tests |
| 2026-09-20 | P2 review set 13/13; numeric locator fixed (derivations were marked wrong) |
| 2026-09-20 | Per-role models (Opus judge, Sonnet prose), second cache point; −30% per answer |
| 2026-09-19 | P1: real model verified locally and in production (both languages); feedback effort low; tip delimiter stripped |
| 2026-09-19 | Harel's integration merged and verified; P0: provenance column + demo wipe; Anthropic path hardened (fallbacks/schema downgrades), budget 90 s (`07a2813`) |
| 2026-09-19 | First production run with a real session; full verification bench; superseded-revision bug fixed; DATABASE_URL mistakes named at startup; live harness restructured (per-test connections) |
| 2026-09-19 | Render deployment live and smoke-tested; TS client + contract test (`24e6263`); independent code review, 13 findings fixed; profiling script, submit path cut, memory store O(1) snapshots |
| 2026-09-18 | Docker image built and smoke-tested in a container (WSL 2 installed); finding: direct Supabase host is IPv6-only, pooler required; detection added |
| 2026-09-18 | Stage G: content loaded into Supabase (approved), `Dockerfile`, `.dockerignore`, `render.yaml`, `docs/practice-api-integration.md` for Harel |
| 2026-09-18 | Verification pass: chaos test, Anthropic provider tests, `smoke_http.py` over real TCP + real JWKS; fixes: error shape on 404/405, 413 body limit, idle locks dropped, demo provider covered; 484 offline tests |
| 2026-09-18 | Step 4b-E/F: the eleven routes, runtime wiring, demo provider, request logging; 46 route tests + live HTTP smoke; 456 offline tests |
| 2026-09-18 | Step 4b-B: migration `20260918170000_practice_submissions` (attempt_submission with unique idempotency key, attempt.exposures/engine_state, user_skill_profile.version) applied, history recorded (`865b83c`). Incident: an ad-hoc dry-run ran the DDL in autocommit because the asyncpg adapter begins lazily; `scripts/dry_run_sql.py` added so dry-runs open the transaction explicitly and verify the rollback |
| 2026-09-18 | Step 4a: submissions as revisions with idempotency keys, evaluation status and retry, exposure events, restart recovery, per-role call deadlines, tip metering, content-hash review preservation and `--dry-run` in the seed loader, local store recovery; 370 tests |
