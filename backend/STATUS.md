# Backend status

A living summary of what exists in `backend/`, how it was verified, what was decided, and what is next.
Updated at the end of every build step. Newest changes are at the bottom of the changelog.

**Last updated:** 2026-09-18 (step 4b, stages A–F) · **Tests:** 484 offline + 14 live + `scripts/smoke_http.py` · **Latest commit:** see changelog

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
| 4b | HTTP API per the contract in `docs/backend-frontend-integration-readiness.md`: A login + pilot access (`74eea90`), B migration `practice_submissions` applied (`865b83c`), C repository + D service (`8eb0fce`), live sweep (`62fa488`), E routes + F route tests; G (deploy, content load) next | | In progress |
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

## 6. Known gaps and open items

- **Content not loaded yet.** `backend/.env` now has `DATABASE_URL`; `seed_db.py --dry-run` passes against the live database. The real load (30 questions get skills, rubrics, hints, checks) is stage G of 4b.
- **Review before publishing.** All 30 questions stay `in_review` until a person checks technical correctness, rubric weights and Hebrew/English parity (checklist in `seeds/questions/README.md`).
- **Bank coverage: 14 of the role's 27 skills** have a primary question. Missing: latches/flip-flops, state tables, Moore vs Mealy, truth tables, number representation, reset strategies, sequential HDL coding, debugging methodology, project walkthrough, state encoding, testbench basics.
- **Anthropic API key** not created yet; the `AnthropicProvider` is written against SDK 1.6.0 but has not run against the real API.
- **Small schema follow-ups** for a later migration: a per-language template column on `tips_library` (Hebrew tip text lives only in the seed file); the `question.hints` column comment describes the old object format.
- **Placeholders** `app.py`, `requirements.txt`, `src/__init__.py` still in the repo; deletion not yet confirmed.
- Backend notes from the performance review, for step 4: generate UUIDv7 ids for the append-only tables; cap `state.history_window`; write daily-allowance checks as `created_at >= day_start`.

---

## 7. How to run it

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload              # the API: http://127.0.0.1:8000/docs is the contract
uv run pytest -q                                   # 456 tests (13 more run when DATABASE_URL is set)
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
| 2026-09-18 | Verification pass: chaos test, Anthropic provider tests, `smoke_http.py` over real TCP + real JWKS; fixes: error shape on 404/405, 413 body limit, idle locks dropped, demo provider covered; 484 offline tests |
| 2026-09-18 | Step 4b-E/F: the eleven routes, runtime wiring, demo provider, request logging; 46 route tests + live HTTP smoke; 456 offline tests |
| 2026-09-18 | Step 4b-B: migration `20260918170000_practice_submissions` (attempt_submission with unique idempotency key, attempt.exposures/engine_state, user_skill_profile.version) applied, history recorded (`865b83c`). Incident: an ad-hoc dry-run ran the DDL in autocommit because the asyncpg adapter begins lazily; `scripts/dry_run_sql.py` added so dry-runs open the transaction explicitly and verify the rollback |
| 2026-09-18 | Step 4a: submissions as revisions with idempotency keys, evaluation status and retry, exposure events, restart recovery, per-role call deadlines, tip metering, content-hash review preservation and `--dry-run` in the seed loader, local store recovery; 370 tests |
