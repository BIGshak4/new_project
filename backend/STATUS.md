# Backend status

A living summary of what exists in `backend/`, how it was verified, what was decided, and what is next.
Updated at the end of every build step. Newest changes are at the bottom of the changelog.

> **Deployment operations update (20 September):** Both Netlify frontends now deploy automatically from Git, with successful push-to-live verification. The existing Render service is already in Frankfurt and uses the real Anthropic provider. The server-only Storage credential is now configured and `/health.answer_images` reports `assessed`. See [the deployment repair report](../docs/deployment-repair-2026-09-20.md) for current checks and remaining human-review steps; older scripted-provider / missing-photo-key notes below are historical.

**Last updated:** 2026-09-24 (loyalty and the saved program §5l) · **Tests:** 742 offline + 17 live + `scripts/smoke_http.py` against Render (25 routes) · **Latest commit:** see changelog

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

## 5j. Faster answers, reviewed-only suggestions, and the mock interview (2026-09-21 → 22)

Shaked's three overnight requests, in the order he gave them.

1. **Faster responses.** After the evaluation, the follow-up wording, the feedback card and the tip used to run one after another; they now run concurrently, so the candidate waits for the slowest of the three instead of their sum. Measured on the real model with `scripts/e2e_real_flow.py`: the English main answer went from 19 s to 13 s, the Hebrew code answer from 42 s to 28 s; follow-ups 5–11 s. What remains is the evaluator itself (Opus, effort already `low`) plus the slowest prose call.
2. **Only reviewed questions are ever suggested.** `QuestionSummary.reviewed` (published after human review); `SUGGEST_REVIEWED_ONLY=true` (default) filters the next-question candidates, and with nothing published the coach stays silent rather than suggest an unreviewed question. **Effect today: no suggestion appears until the first questions are published.** Tests run the seed bank with the switch off.
3. **The mock interview**, built in four stages, each verified before the next:
   - *Stage 1, store + service* (`app/repo/sessions.py`, `app/services/interview_service.py`): the session engine (subject router + skill controller, written in step 2) driven over the store. Plan from role + company; skills without a reviewed bank question are dropped, none left → `409 no_reviewed_questions`; nothing is generated. The answer is saved before the model call, scored exactly once (idempotent replay), the next bank question is chosen (never the same question twice; a skill whose questions ran out is resolved and skipped), and the candidate's skill profile continues through the interview (session states start from the profile's k/c and history and are written back after every turn). Results hidden until the end. Hints from the bank cost struggle budget. End early keeps what was answered. Report: scorecards, per-skill assessments, recommended skills, tips, model narrative (cached). Live state in `interview_session.state`, turns in `session_turn`, plan in `session_skill_plan`, metrics/usage rows session-scoped; **no migration needed**. A bug found by the trace: the engine state was not re-saved after a turn (fixed; test clock added).
   - *Stage 2, API + client*: `/v1/interviews` (start, list, get, answer with 90 s budget then 202, hint, end, report with a 75 s budget then the plain report), settings `INTERVIEW_REVIEWED_ONLY=true`, `INTERVIEW_DAILY_LIMIT=5`; TypeScript types and calls; contract and route-protection tests; docs §3b.
   - *Stage 3, real model*: `scripts/e2e_mock_interview.py`, 20-minute interview on Opus/Sonnet with canned answers: 10 questions across 4 subjects, 4–6 s per evaluation, report with narrative in 31 s, $0.19; fit 80 capped by a core gap the weak answers created — as designed.
   - *Stage 4, the screen* (`apps/web/src/components/interview-session.tsx`, "Mock interview" in the sidebar): lobby (duration 20/30/45, rules, past interviews), the room (countdown, one question, answer editor, hint, end early, answered list without bands), the report (fit cards, skill table, next skills, tips, narrative, questions with bands revealed). Refresh-safe; drafts and idempotency keys kept in the browser per question.

   - *Review and fixes*: an independent review (verified by execution) found and I fixed: a crash mid-evaluation left the question stuck forever (now any failure marks the turn failed, and an evaluation older than 5 minutes counts as failed); two servers or tabs could both score the same turn (optimistic revision on the session row, conditional UPDATE); a new interview inherited the report evidence of earlier ones (session skills now start from the profile's scores only, the profile takes each turn's evidence through a merge); the countdown ignored the open question; the screen stopped polling after one tick; a failed evaluation wiped the typed answer; a narrative failure was cached forever.

Verification: 663 offline tests (was 631; 19 interview tests, protection tests for 7 new routes), the live interview test against the real schema (17th live test), tsc clean, 33 web tests, `next build` passes, real-model dry runs for both flows, Render smoke test with 18 routes.

**"On trial" questions (2026-09-22, Shaked's "go").** A third question state between in review and published: `trial`. Migration `20260922061417_question_trial_status` (enum value, applied with approval). Trial questions are served in production, count as usable for the coach's next-question suggestion and for the mock interview, are exempt from the parity gate while on trial (that is what is being checked), and are badged "on trial" in the library and in the interview room (`QuestionSummary.trial`, `InterviewTurn.trial`). `scripts/question_status.py --list | --set trial|published|in_review <keys> [--reviewed-by NAME] --apply` moves questions without SQL; without `--apply` it is a dry run. A content reload keeps trial like published (content changed → back to in review with a REVIEW RESET line). Three tests over a catalog with five trial questions.

**Open in the morning:** the practice site on Netlify has not published any build since `336382b` (20 Sep evening). The GitHub workflow requests the build and then times out waiting for the new revision, so Netlify's own build is failing or not running (build minutes on the free plan are one suspect). Its log is only visible in the Netlify dashboard: https://app.netlify.com/projects/jobrun-practice/deploys. Until it is fixed, the interview screen, the follow-up resend fix and the reviewed-only client field are not on the live site; a manual `npx netlify-cli deploy --prod` from a logged-in machine publishes immediately.

## 5k. Overnight build (2026-09-23 → 24): the goal, job types, company tags, the three-part progress page, drawings in interviews

Shaked's eight requests before he left, built in three stages (backend `90b921b`, frontend `0b91e44`, verification below).

1. **Circuits and photos in the mock interview.** An interview answer is `{text, visual}` like a practice answer. A drawn circuit is described to the evaluator (netlist + derived functions) and its derived functions run through the question's deterministic check; the drawing is kept on the turn (`session_turn.question_generation_meta.answer_visual`) and shown in the report with a "your circuit was assessed" chip. Photos go through the same `visual_evidence.gather` as practice; **the storage bucket only accepts `<user>/<attempt>/…` paths today**, so interview photos need migration `20260924045651_interview_answer_images.sql` (upload rule and trigger also accept an in-progress `interview_session` of the same learner; applied 2026-09-24 with Shaked's approval; `INTERVIEW_PHOTOS = true`).
2. **The practice screen.** The side column holds only the answer. Under it, full width: what was good / what was missing (the evaluator's key points plus a failed check's detail), a tip for next time (the tip and the card's next step), then the follow-up question, then the suggested next question once the follow-up is answered. The old assistant panel is gone; the four-part card, the check table and the chips live under "more about this assessment".
3. **The progress page is three things** (`progress-board.tsx`): an overview card with the level in words (Getting started / Awareness / Foundational / Proficient / Advanced / Expert, a six-step meter, no percentages), the counts (answered, strong, partial, to strengthen, skills assessed of the plan) and one encouraging sentence; the road-so-far graph (stacked answers per day + the average level line, inline SVG, `lib/timeline.ts`); the plan until the interview (the Plan Router's week within the user's minutes, grouped by day, today's covered items ticked). Server side: `ProgressView.overview / timeline / plan / goal` (`PracticeService._overview/_timeline/_weekly_plan`, `attempts.daily_bands`). The donuts and the skill list are no longer shown (the data is still served).
4. **Job types.** `seeds/job_types.json`: digital design, verification, FPGA, embedded/firmware, software, student/general. A job type does not add skills: it multiplies the role's skill weights (verification 1.8× testbenches, embedded 1.6× bit manipulation…), and the plan, the next-question suggestion and the interview plan all take the multiplied weights (`_plan(seniority, job_type)` in both services; `RoleSkillRow.model_copy` before `merge_skill_sets`). A question belongs to every job type that does not play down its primary skill; `GET /v1/questions?job=` filters and sorts by relevance (Σ link weight × emphasis). `GET /v1/job-types`.
5. **"I saw it at company X."** `POST /v1/questions/{key}/sightings` with a company name; slugged, one row per (question, user, company); `QuestionSummary.companies` carries `{slug, name, count}` (never who); `GET /v1/questions?company=` and `GET /v1/companies` search by company. Table `question_sighting` = migration `20260924045708_question_sightings.sql` (applied 2026-09-24 with Shaked's approval). While the table is absent, readers return empty and the writer answers `503 temporarily_unavailable`, which the button shows as "company tags are opening soon"; the API must be restarted after the table appears (Render redeploys on push), because the schema is reflected once at startup.
6. **The goal, asked first.** Job type, interview date, minutes a day, seniority, stored on `user_profile` without a migration (`background.job_type`, `target_interview_date`, `available_minutes_per_day`, `seniority_self_assessed`); `GET/POST /v1/me/goal`. The goal card opens the library for a new user ("Later" skips it, per browser), is editable from the progress page, sets the default job filter, and shapes the plan, the question order and the interview.
7. **More alive.** Warm accent colour, soft shadows, cards that rise in, pill buttons, gradient headings, a background wash; `prefers-reduced-motion` respected.
8. **Full verification from scratch:** `docs/system-verification-2026-09-24.md`: 709 offline tests, live suite 17/17 in 18 m 28 s, two real-model scripts under production rules (rolled back), Render smoke with 23 routes after each deploy, web typecheck/tests/build, independent review (6 findings fixed, including an empty production plan and Hebrew company slugs).

Decisions: emphasis multipliers stay within 0.2–2.5 and the plan is renormalised, so a job type shifts attention without silencing a skill; the level word is the rounded average of assessed plan skills, "Getting started" until something is assessed; the plan's "done" tick is decided from today's attempts only (the plan is regenerated on every load, so past days are not tracked); with nothing reviewed the plan is empty rather than an error (production has 30 trial questions, so it is full there).

**Morning list:** (a) done 2026-09-24 with Shaked's approval: migrations `20260924045708_question_sightings` and `20260924045651_interview_answer_images` applied, `INTERVIEW_PHOTOS` on, company tags verified on the real database; (b) rotate the Netlify build hook pasted in chat and update the GitHub secret `NETLIFY_PRACTICE_BUILD_HOOK`; (c) decide on the Opus 5.5 comparison; (d) open the site once through the goal card and the progress page and say what feels off.

## 5l. Loyalty and the saved program (2026-09-24, morning, Shaked's "go")

**Loyalty (1..10) per skill.** How fresh the evidence behind a level is, not how good the level is: 10 on the day of the last scored answer on the skill, one less for every full three days since, never below 1; any scored answer (strong or weak) brings it back to 10. Computed on read from `user_skill_profile.last_assessed_at` (`scores.loyalty`), so no migration and no nightly job. Loyalty 6 or lower (12+ days) makes the level **provisional**: it is not counted as assessed in the overview and the Plan Router schedules a refresh (a retention check, reason "It has been N days since X was last checked") before new material. `SkillProgress.loyalty / needs_refresh`, `ProgressOverview.skills_to_refresh`, one line on the overview card.

**The saved program.** The plan is no longer recomputed and forgotten on every load. `learning_plan` + `plan_item` (existing tables from step 1) hold one active plan per user (`app/repo/plans.py`). Rules: the program is rebuilt **every day** from the fresh profile (so a level that went stale or rose overnight changes the plan); open items of earlier days that are at most 3 days past their day are **carried forward** and lead the new day (marked "carried"); older ones are dropped, the router re-adds the skill if it still matters; within one day the saved plan is reused, so a started item stays started; a new goal deactivates the plan. **Ticking:** a scored main answer completes the item it was started from, else the earliest open item due by today on one of the question's skills (`plan_item.completed_attempt_id`); a finished mock interview completes the earliest open simulation item (`completed_session_id`, `InterviewService(on_finished=...)`). **"My program"** replaces "One question for today" in the library (`program-panel.tsx`): the next due item with its reason and minutes; Start chooses a bank question for the item's skill at the user's level (unseen and reviewed first, `bank.select_question`) and opens a practice attempt linked to the item (`attempt.plan_item_id`); a simulation item points to the interview lobby with the closest duration; an item the bank cannot serve is skipped with a message. `GET /v1/me/program`, `POST /v1/me/program/start`. The progress page's plan table reads the same saved plan (status, carried, started, skipped). Reasons are stored in the language the plan was built in.

Verification: 742 offline tests (17 loyalty, 10 program), `scripts/e2e_goal_and_visuals.py` on the real database (plan rows written, item started and linked, the answer ticks it, rolled back), typecheck / 38 web tests / build, Render smoke with 25 routes.

## 5m. XP and the path (overnight 2026-09-24 → 25, Shaked's approved plan)

**XP: a motivation layer, computed on read.** `app/engine/xp.py` is pure arithmetic over results the engine already stored; it imports nothing from the app (a test parses its imports) and nothing in `evaluator.py`, `scores.py`, `practice.py`, `skill_controller.py`, `subject_router.py`, `session.py` or `plan_router.py` changed. One scored answer earns band STRONG 20 / PARTIAL 10 / WEAK 4, × `1 + (difficulty − 1)/9` (difficulty 10 doubles), × `max(0.4, 1 − 0.2 × hints seen before the answer)`, × 0.25 if the reference was revealed before the answer, × 0.5 for a follow-up answer, × 1.5 for an interview turn; rounded, never below 1 for a scored answer; unscored, failed and still-evaluating answers earn 0. The answer's XP is split over the question's skill links by weight (whole numbers that add up, largest remainders first). What it reads: `attempt_submission` rows with `status = done` and a band (`band`, `turn`, `hints_seen`, `reference_seen`, `accepted_at`) joined to `attempt` and `question.difficulty`, plus `question_skill` for the split; `session_turn` rows whose `question_generation_meta` has `status = done` and a `band` (`difficulty`, `hint_level`, `answer_submitted_at`, the question's links or the turn's skill at weight 1). Store readers `scored_submissions` / `scored_interview_turns` exist on `DbTx` and on the in-memory store, a 365-day window. No table, no migration, no write: the same rows always give the same XP.

**Where it shows.** `ProgressOverview.xp_total / xp_today / streak_days`; `SkillProgress.xp` and `level_progress`; `SubmissionView.xp_earned` (a "+15 XP" pill after an answer, also on follow-ups); `InterviewTurnView.xp_earned` once the results are revealed. **Streak** = consecutive UTC days with at least one scored answer, counted back from today, or from yesterday when today has none yet (a gap of one full day ends it). **`level_progress`** is derived from the engine's existing `scores.questioned_level(state)` pair: the level is `round_half_up(level_score)` clamped to 1..5, so level L spans scores [L − 0.5, L + 0.5); the fill is `clamp(level_score − (L − 0.5), 0, 1)`; a level capped below its score (level-3 hint, core misconception) shows a full bar, level 5 is always full, an unassessed skill 0. The level itself is untouched.

**Proof the engine is untouched:** `tests/test_xp.py::TestOnTheService::test_the_engine_is_identical_with_and_without_xp` runs the same answer through two services, one with the XP module monkeypatched to return zeros, and compares band, attempt status, every skill's level/status/loyalty, the overview rank and the stored `engine_state` of every profile row: identical. 30 XP tests in all (arithmetic, split, streak edge cases, level fill, service view, interview turn, the import check).

**The restyle (`apps/web`).** The approved mockup's language across the whole app: Nunito paired with Heebo (Nunito has no Hebrew glyphs; the font stack falls through per glyph), warm off-white ground `#F6F5EF`, white cards with 2 px `#E6E3D8` borders and 22–28 px radii, leaf green `#2F9E44` for nodes and bars with a pressed 3D shadow (`0 5px 0 #217A33`, moves down on `:active`), streak orange, refresh blue `#1C64B8`, interview yellow `#FFF4D6 / #A16207`, chunky uppercase buttons, segmented bars. Button fill is `#22823A` rather than the mockup's `#2F9E44` so white text reads at 4.9:1 (the brighter green stays on icon-only nodes and bars). The 2026-09-23 gradient headings, background washes, radial blobs and rise-in animations are gone; `prefers-reduced-motion` still switches every animation off. Navigation is a top bar (Learn, Library, Mock interview, Progress; streak flame + days and XP + level word on the right; language switch and sign-out) that becomes a fixed bottom tab bar with icons under 760 px. **Learn** is the default view: the saved program (`GET /v1/me/program`) drawn as a winding path of nodes (done = green tick; the next item = large with Start, its reason and minutes; future = grey lock; a simulation item = yellow microphone; carried items marked; the zig-zag is a logical margin, so RTL mirrors it by itself, and it folds into one column on a phone), a unit band with the goal, and a side column with Today (done/total meter), Skill strength (five-block bars, the level word, XP, blue "Needs a refresh") and the streak card. Start goes through the unchanged `POST /v1/me/program/start` flow. The goal card opens on Learn for a new user. The library keeps All / Saved / My practice as a segmented control; every `?view=` link still resolves (`library`, `bookmarks`, `history`, `progress`, `interview`). `lib/path.ts` (node states, zig-zag, RTL offset, strength tones, today's count) has 10 tests; 48 web tests in all. No data flow changed: drafts, idempotency keys, polling, follow-ups and program ticking are as they were.

**Also:** `tests/test_program.py::test_an_item_older_than_three_days_is_dropped` failed twice on the morning of 2026-09-25 (on master too, before any change) and passed on every later run; its assertion matched carried items by reason text, and two items on one skill share a reason, so it now matches by (mode, skills). The `carried` flag itself compares a UTC `created_at` date with the local `week_start`, which can disagree for three hours after local midnight; a small follow-up.

Verification 2026-09-25: `ruff` clean; 772 offline tests; web typecheck, 48 tests, production build; Netlify workflow and Render redeploy confirmed (`/openapi.json` on Render lists the XP fields).

**Follow-up (2026-09-25, morning):** the program's `carried` flag now compares one clock (an item created before the plan's `generated_at` is carried), which removes the UTC-vs-local-date disagreement after midnight behind the flaky test. XP is asserted on the real database by `scripts/e2e_goal_and_visuals.py` (+24 XP for a strong answer at difficulty 3, streak 1).

## 5n. Speed and many users (overnight 2026-09-25 → 26, Shaked's approved plan)

Full numbers and the decisions: `docs/performance-2026-09-26.md`.

1. **Measured first.** `scripts/latency_bench.py` times every stage of an answer on the real model and the real
   database (rolled back): load, accept + save, check, evaluator, card, tip, follow-up wording, next question,
   outcome save, words save, `progress()`, `program()`, statements per call. Before: **the candidate waited
   16.8 s median (max 37 s)** for the grade, because `submit` also waited for the card, the tip and the follow-up
   wording (Sonnet, 7–28 s) after the evaluator (Opus, ~5 s).
2. **Grade first.** `PracticeAttempt._evaluate` now scores and decides (`_score_and_decide`: band, evidence, scores,
   controller decision, tip choice, the follow-up turn opened without words) and marks the revision
   `feedback_pending`; `write_prose` / `apply_prose` add the card, the polished tip and the follow-up wording.
   `PracticeService.submit` answers after the grade is saved; the prose calls start the moment the answer is scored
   (while the grade is saved) and a background task stores them with `attempts.save_prose`, a conditional update
   (only a `done` revision still flagged `feedback_pending`: never written twice). Crash between the two saves: the
   next read after 30 s writes the words, `retry` at once; neither re-scores. A failed save is retried with the words
   already written. A follow-up without words refuses answers (`409 follow_up_not_ready`). Views:
   `SubmissionView.feedback_pending`, `AttemptView.feedback_pending`, `FollowUpView.question_pending`. Web: the grade
   shows at once, polling continues while words are pending, the follow-up box waits for its question, progress is
   no longer reloaded after hints. `FEEDBACK_IN_BACKGROUND` (default true) switches it. Interview turns have no prose
   per turn, so nothing to move there. **After: grade 8.1 s median (max 10.3 s)** from this machine; from Render
   (4 ms database round trips instead of 71 ms) about 5 s.
3. **Nothing about evaluation changed**, proven by `tests/test_grade_first.py`: a four-attempt scenario's full stored
   result (bands, evaluations, evidence, XP, next question, every `engine_state`, level history, metrics, usage,
   tips, card, tip and follow-up wording) equals a record written by the code before the split (`tests/golden/`),
   inline and in the background. `evaluator.py`, `scores.py`, `skill_controller.py`, `params.py`, the prompts,
   `feedback.py`, `generator.py`, `tips.py` and `providers.py` are byte-identical to `a9d8643`.
4. **Fewer round trips.** Cached servable question list and question-skill links; one transaction for
   `progress()`; next-question reads inside the outcome transaction; no second seniority read. Warm submit 29 → 22
   statements, progress 20 → 12, library 6 → 3.
5. **Many users** (`scripts/load_test.py`, local API over HTTP, scripted model with real timing, test tokens):
   10 / 50 / 100 users, every flow completed, no errors, event-loop lag p99 ≤ 29 ms, 117 → 160 MB. Same harness,
   50 users, old way: submit p50 14.1 s vs 7.8 s. Fixed: signing-key lookups took a default-pool thread per request
   and code tests (up to 5 s each) shared that pool: 20 slow code answers stalled everyone's requests ~5 s on a
   6-thread host; keys are now reused from memory and code tests have their own 4-thread pool (others stay at
   10–40 ms). Made-up token `kid`s can no longer force a JWKS download per request. 429s from the evaluator (30 %):
   answers kept, retries score them, nothing lost.
6. **Database** (`scripts/db_concurrency.py`, rolled back): the Session pooler refuses the project's ~10th
   simultaneous connection (`EMAXCONNSESSION`); the Transaction pooler (port 6543) accepted 40 and ran every flow.
   Production round trip 4 ms (`/health?db_check=true`). Pool settings are now `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` /
   `DB_POOL_TIMEOUT`; `/health.database_pooler` says which pooler is in use.
7. **Model capacity**: the account is on the Evaluation tier (1,000 RPM, 500k ITPM, 80k OTPM per model, read from
   response headers): about 55–75 fully answered questions per minute, Sonnet's output tokens binding first.
8. **Evaluator comparison** (P2, 13 answers): Sonnet 5 agreed with Opus 5 on 13/13 bands, 4.0 s vs 5.0 s median,
   62 % cheaper, but missed or over-flagged misconception keys in 2 of 13. Opus stays (decision for Shaked).

**Decisions for Shaked:** (a) set Render's `DATABASE_URL` to port 6543 (Transaction pooler); (b) the Anthropic tier
(Start tier = ×4–5 capacity, $500/month cap); (c) Opus stays the judge unless you decide otherwise; (d) rotate the
database password as a precaution (part of the connection string was printed to the agent's console once).

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
| 2026-09-26 | Overnight (§5n): latency bench (grade 16.8 s → 8.1 s median, 37 → 10 s max); grade first (words in a background task, conditional save, crash-safe, proven identical by a golden record); fewer round trips; load test 10/50/100 users over HTTP, all flows complete; signing keys reused from memory and code tests in their own pool (a slow code answer no longer stalls other users); JWKS refresh throttled; database concurrency check (Session pooler refuses the 10th connection, Transaction pooler recommended); model capacity from the account's headers (Evaluation tier); P2 Opus vs Sonnet as judge; `docs/performance-2026-09-26.md` |
| 2026-09-25 | Overnight (§5m): XP computed on read (`app/engine/xp.py`: band × difficulty × hints × reference, follow-up ½, interview ×1.5, per-skill split, streak, `level_progress` from the engine's level score; engine untouched, proven by test); the Duolingo-style restyle of the web app (top bar + bottom tabs, Learn home with the program as a path, skill-strength bars, streak, XP pills); 772 offline tests, 48 web tests |
| 2026-09-24 | Loyalty per skill (1..10, -1 per 3 days without evidence, back to 10 on any scored answer; 6 or lower = provisional, refresh scheduled first); the saved program on `learning_plan`/`plan_item` (rebuilt daily, carried forward up to 3 days, ticked by attempts and interviews); "My program" replaces "One question for today"; 742 offline tests (§5l) |
| 2026-09-24 | Overnight (§5k): the goal (job type, interview date, minutes a day) on `user_profile`; six job types that re-weight the role's skills for the plan, the next question and the interview; questions listed by job relevance and by company; "I saw it at company X" (migration `20260924045708`, applied); progress = overview in words + road-so-far graph + plan until the interview; practice feedback → follow-up → next question under the answer; drawn circuits in interview answers (photos: migration `20260924045651`, applied); visual refresh; 706 offline tests; `scripts/e2e_goal_and_visuals.py`; verification report `docs/system-verification-2026-09-24.md` |
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
| 2026-09-22 | Overnight (§5j): prose model calls concurrent (19→13 s, 42→28 s); suggestions only from reviewed questions (silent until the first publish); **mock interview** end to end — session store/service (no migration), `/v1/interviews` routes, TypeScript client, the interview screen with lobby/room/report; real-model dry run 10 questions/$0.19; 656 offline tests |
| 2026-09-21 | Full verification pass (`docs/system-verification-2026-09-21.md`): 620 offline tests, real-model end-to-end flow (`scripts/e2e_real_flow.py`), P2 set 13/13 again, Docker image against the real DB, Render smoke, web build; three fixes (whole-attempt bands for the next question, hint follow-ups that restate the prompt, follow-up resend). Live suite: 16/16 for Harel; on Shaked's Windows machine the two question blocks fail only inside full runs (connection drops), pass alone — engineering item, not a product fault |
| 2026-09-21 | Shaked's flow: **one** follow-up per attempt (`MAX_FOLLOW_UPS = 1`), then the next question from the bank, chosen from what was hard: a recognised bank misconception picks the skill it undermines and its explanation is shown as "what was hard here" (`NextQuestionView.focus`); questions examining the skill as a secondary skill count; the weakest band across main answer and follow-up decides. `next_question.py`, `follow-ups.tsx`, `NextUpCard` under the follow-ups |
| 2026-09-21 | Follow-up questions back in the web app: new attempts start in `deep` mode (full evidence weight; up to two engine follow-ups), `follow-ups.tsx` shows answered follow-ups with their band and the open one with its own answer box; the "next question" card waits until the attempt is complete. Shaked asked for follow-ups on seeing the live site |
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
