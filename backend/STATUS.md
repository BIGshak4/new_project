# Backend status

A living summary of what exists in `backend/`, how it was verified, what was decided, and what is next.
Updated at the end of every build step. Newest changes are at the bottom of the changelog.

**Last updated:** 2026-09-18 (after step 3) · **Tests:** 328 passing · **Latest commit:** `18bfaa2`

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
| 4 | API and WebSocket so the web app can call the engine | | Next |
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
| `practice.py` | One deep or quick practice question end to end: hints, reveal, submit, follow-ups, feedback, tip | §1.1, §6.6 |
| `plan_router.py` | Across days: next activity with a plain-language reason, weekly plan, retention checks, diagnostic | §4.11 |
| `scorecards.py` | Role/company/overall fit with core-gap caps, profile roll-up, target fit | Data_Models §7 |
| `bank.py` | Bank-first question selection, coverage per skill | §1.2 |
| `catalog.py` | Loads and validates every seed file together | Data_Models §12 |
| `providers.py` | `ScriptedProvider` (tests), `ManualProvider` (request/reply files, no key), `AnthropicProvider` (Opus 5) | Build guide §7 |
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
- `seed_db.py`: validates the seeds (`--check`) and upserts them into Supabase.
- `build_example_bank.py`: merges Harel's `example_question/questions.json` with `seeds/questions/enrichment/*.json`.

### App shell (`app/`)

`main.py` with `/health` and `/catalog/summary`; `config.py` (settings from `.env`); `db.py` (async Supabase connection, tables reflected from the live schema).

---

## 4. How it was verified

- **328 tests**, about 3 seconds, no network. They are built from the worked examples in the specs: the §6.3 merge table, every row of the §3.3 transition table, the §4.5 entry-difficulty cases, the fit caps, the roll-up weights.
- **Persona bots** run whole sessions (always strong, always weak, weak in two subjects, strong then collapses) and check the promises: no hint followed by an escalation, weak core subjects get extra turns, strong subjects close early, the fatigue override fires.
- **40 randomized sessions** assert invariants: terminates, difficulty in range, never re-enters a resolved skill, never targets an observed skill, budgets never negative, at most one turn past the clock.
- **Fuzzing** of the Boolean parser (20,000 random inputs, deep nesting, 60,000-term chains): rejected cleanly, never crashes.
- **A real practice session** was run in the terminal with the manual provider: wrong XOR answer → check fails → WEAK → feedback card and tip → level-1 hint → strong recovery → HOLD (not escalate) → probe on the one missed point → profile saved.
- **Seed loader** checked column by column against the SQL schema; every deterministic check self-tests against known-good and known-bad answers.
- Two independent review agents were started; both were cut off by session limits, so their open leads were verified by hand (and were real: stale subject status at rebalance time, no hard clock stop, parser recursion).

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

## 6. Known gaps and open items

- **Database password** needed in `backend/.env` before `seed_db.py` can load the skills, role, tips, glossary and enriched questions. Everything is validated, nothing is loaded.
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
uv run pytest -q                                   # 328 tests
uv run python scripts/seed_db.py --check           # validate content
uv run python scripts/cli_practice.py --debug      # practice in the terminal, manual provider
uv run python scripts/cli_practice.py --language he
```

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
