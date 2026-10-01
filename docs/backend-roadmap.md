# The backend: how it works, and what comes next

Written for Shaked and Harel, 1 October 2026. Part A is a map of the backend as it runs today, in plain words with
the file names you need to find things. Part B is the roadmap: what is left to do, in order, with who does it.
`backend/STATUS.md` stays the running log; this document is the picture.

---

## Part A. How it works

### A1. The shape in one paragraph

A student opens the web app (Next.js, on Netlify). The app signs them in with Supabase Auth and calls our API
(FastAPI, on Render) with their token. The API checks the token, checks that the e-mail is on the pilot list, and
runs the **practice service**: it loads a question from the bank, saves the student's answer, asks the **engine** to
grade it, saves the grade, and later writes the words of the feedback in the background. The engine talks to Claude
(Opus 5.5 to judge, Sonnet 5 to write prose) through one provider module. Everything the student did is stored in
Postgres (Supabase), and only the API writes there; the browser reads its own rows through row-level security.
Progress, XP, the daily program and the mock interview are all computed from those stored rows.

```
 browser (Next.js, RTL)  ──token──▶  FastAPI (Render)  ──SQL──▶  Postgres (Supabase)
        │                                │   │
        │  Supabase Auth (sign in)       │   └──▶ Claude (judge, prose)  via app/engine/providers.py
        └───────────────────────────────▶│
                                         └──▶ Supabase Storage (drawn circuits, photos)
```

### A2. One answer, step by step (the most important path)

1. **`POST /v1/practice/attempts`** (`app/api/v1/practice.py`): the student opens a question. The service
   (`app/services/practice_service.py`) loads the question and the student's skill profile, creates an attempt row,
   and returns the question text, hints count and the attempt id.
2. **`POST /v1/practice/attempts/{id}/submissions`**: the answer arrives with an `Idempotency-Key` header, so a
   double click or a retry after a dropped connection can never grade twice (`app/repo/attempts.py`,
   `DuplicateSubmissionKey`).
3. **Accept and save** the answer as a submission revision (status `evaluating`). If the question has a
   deterministic check (a truth table, a number with a unit, Python test cases), it runs now in
   `app/engine/checks.py` (code runs in a sandboxed runner, `app/engine/code_runner.py`, with a timeout).
4. **Grade first** (`app/engine/practice.py`, `PracticeAttempt._score_and_decide`): the evaluator prompt goes to the
   judge with the question, the rubric, the known misconception keys and the check result. The reply is a
   structured `Evaluation` (correctness, depth, clarity, structure, misconceptions found, key points hit and
   missed, behaviour signals). `app/engine/scores.py` turns it into a **band** (STRONG / PARTIAL / WEAK), applies the
   check result and the core-misconception rule, and `app/engine/skill_controller.py` updates the student's skill
   levels and loyalty. The **grade is saved and returned at once**, about 8 seconds after the answer.
5. **The words come after** (`write_prose` / `apply_prose`): the feedback card, the coaching tip and the follow-up
   question's wording are written by Sonnet in a background task and stored with a conditional update
   (`attempts.save_prose`), so they are written exactly once and never re-score anything. The web app polls the
   attempt until `feedback_pending` is false. If the server dies between the two saves, the next read after 30 s
   writes the words; `retry` does it at once.
6. **Follow-up and next question**: one follow-up per attempt, chosen by `app/engine/skill_controller.py` from what
   the answer showed (escalate, step back, scaffold). After it, `app/engine/next_question.py` picks the next bank
   question for the student's weakest relevant skill, and the plan item (if the attempt came from the program) is
   ticked (`app/repo/plans.py`).
7. **XP** (`app/engine/xp.py`) is never stored: it is computed on read from the stored bands, difficulties, hints and
   references. STRONG 20 / PARTIAL 10 / WEAK 4, scaled by difficulty and reduced by hints, ×0.25 with the reference
   shown, ×0.5 for a follow-up, ×1.5 for a finished interview. That is why XP can never change how an answer is
   graded.

### A3. The other flows

- **Today's program** (`GET /v1/me/program`, `POST /v1/me/program/start`): `app/engine/plan_router.py` builds a plan
  from today until the interview from the goal (job type, date, minutes a day), the role's skill weights re-weighted
  by the job type (`seeds/job_types.json`), the student's levels and loyalty, and the bank's coverage. Stored in
  `learning_plan` / `plan_item`, rebuilt daily, items carried forward up to three days, ticked by scored answers
  and finished interviews.
- **Progress** (`GET /v1/me/progress`): the level in words, the three-part overview, the per-skill levels with
  loyalty (10 − days/3 since the last evidence; 6 or lower means "provisional, refresh first"), the timeline per
  day, and the plan. One transaction, about 12 statements.
- **Mock interview** (`/v1/interviews`, `app/services/interview_service.py`, `app/engine/session.py`): a
  session with a plan of skills, one question at a time against the clock, the subject router moving between
  subjects by the answers, grades hidden until the end, then a report (`app/engine/reporter.py`, `scorecards.py`)
  with role fit, skill by skill, what to practise next and a narrative. Drawn circuits and photos are stored in
  Supabase Storage and judged (`visual_evidence.py`, `circuit_text.py`).
- **Company sightings and question reports** (`/v1/questions/{key}/sightings`, `/reports`): "I saw it at company
  X" and "this question is not clear", stored per question, shown as aggregates or read by the review tooling only.
- **Goal, job types, companies**: `/v1/me/goal`, `/v1/job-types`, `/v1/companies`.

### A4. The pieces, by folder

| Folder | What lives there | The file to open first |
|---|---|---|
| `app/api/v1/` | the HTTP routes, request and response models, auth dependencies | `practice.py` |
| `app/services/` | the use cases: practice, interview, the store boundary (`store.py`: a protocol with a database store and an in-memory store for tests and the harness) | `practice_service.py` |
| `app/repo/` | SQL per table: attempts, profiles, plans, sessions, questions, users, sightings, reports, events | `attempts.py` |
| `app/engine/` | the evaluation engine: prompts, evaluator, scores, skill controller, next question, plan router, XP, checks, code runner, reporter | `practice.py` |
| `app/engine/prompts/` | the exact words sent to the model, versioned | |
| `app/schemas/` | the data shapes (Pydantic): bank questions, engine state, API views | `bank.py` |
| `app/auth.py`, `app/config.py`, `app/db.py` | Supabase token verification (JWKS, ES256), settings from `.env`, the connection pool | `config.py` |
| `seeds/` | the content: skills and their proficiency rubrics, the role, job types, companies, tips, glossary, the 30 questions (`questions/example_bank.json`) and the drafts (`question_drafts/`, never loaded by accident) | `questions/README.md` |
| `scripts/` | the operator's tools, listed in A6 | |
| `tests/` | 797 offline tests (in-memory store, scripted model) and 17 live tests against the real database, rolled back | `conftest.py` |
| `supabase/migrations/` (repo root) | every schema change, timestamped; applied through the Supabase connector after a dry run and Shaked's approval | |

### A5. The data, in one picture

- **Content** (written by the loader, read by everyone): `skill`, `role`, `company`, `question` with
  `question_translation`, `question_skill`, `tips_library`, `glossary`, `job_type`. Questions have a status
  (`draft → in_review → trial → published`); the API serves `published` and `trial`, and `in_review` only when a
  development flag says so.
- **People**: `user_profile` (goal, background, seniority) joined to Supabase Auth; `jr_members` is the pilot list.
- **Doing**: `attempt` → `attempt_submission` (revisions, grade first, prose after) → `follow_up`; `skill_profile`
  (level, loyalty, engine state, history); `learning_plan` / `plan_item`; `interview_session` / `session_turn`;
  `question_sighting`; `question_report` (migration ready, apply pending); events and usage rows for cost.
- **Rules**: every table has row-level security; the browser can read its own rows and nothing of the engine's
  internals; only the backend's service role writes. The database refuses to publish a question without a reviewer
  and a reuse status.

### A6. The operator's tools (all under `backend/scripts/`)

| Tool | What it does | When |
|---|---|---|
| `seed_db.py --check` / `seed_db.py` | validate the content against the catalog rules, then load it (upsert by key; keeps reviewer decisions) | after content edits, with approval |
| `question_status.py --set trial <keys> --apply` | move questions between review states | when a question is ready for pilot users |
| `build_example_bank.py` | merge Harel's question text with the enrichment files into the loadable bank | after editing either |
| `generate_questions.py --per-skill N --verify` | draft new questions in the seed format, validated and judged, into `seeds/question_drafts/` | when the bank needs to grow |
| `question_reports.py` | the inbox of "not clear" reports, `--resolve` to close them | weekly review |
| `dry_run_sql.py <migration>` then the Supabase connector (`apply_sql.py --yes` as fallback) | every schema change | with Shaked's approval |
| `smoke_http.py --url https://jobrun-api.onrender.com` | 25 routes against production | after every deploy |
| `e2e_live_trial.py`, `e2e_goal_and_visuals.py`, `e2e_mock_interview.py` | the real model and the real database, rolled back | after engine or service changes |
| `latency_bench.py`, `load_test.py --users 10 50`, `db_concurrency.py`, `profile_service.py --cpu` | speed and capacity | after performance changes |
| `p2_review_set.py` | 13 known answers through the judge; the gate for changing the judge model | before a model change |
| `cli_practice.py` | practise in the terminal, manual or real model | debugging the engine |
| `screenshot_server.py` | the API behind the web screenshot harness | run by `npm run screenshots` |

### A7. Where it runs, and the settings that matter

- **Render** (`render.yaml`, Dockerfile): the API, auto-deploys on every push to `master`. Environment: `DATABASE_URL`
  (the Transaction pooler, port 6543), `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (the judge; overrides the code's
  default), `ALLOWED_ORIGINS`, `ALLOW_IN_REVIEW_CONTENT`, `SUPABASE_SERVICE_ROLE_KEY` (for photos), pool sizes.
  `/health?db_check=true` tells you the model names, the pooler and the round trip.
- **Supabase**: Postgres, Auth, Storage. Project `djpwvqpsqbkvprlncjjg`. The Session pooler refuses the tenth
  connection; the Transaction pooler took 40 in the load test.
- **Netlify**: the web app, built by a GitHub workflow on every push, triggered through a build hook stored as a
  GitHub secret.
- **Anthropic**: the Evaluation tier today, about 55 to 75 fully answered questions a minute before output tokens
  bind.

### A8. The guarantees we test for

- A grade is written once and never re-scored by a retry, a crash or a replaced answer (golden record test).
- Another user can never read or touch an attempt; row-level security lets a user read their result and never the
  engine's internals.
- The daily limit counts real rows; simultaneous double clicks score once.
- The judge model changes only on the 13-answer review set; the engine's files were byte-identical across the last
  three nights of front-end work.
- 10, 50 and 100 users at once complete every flow with event-loop lag under 30 ms.

---

## Part B. The roadmap: what comes next, in order

Each item says who, and what "done" looks like. Items 1 to 4 are yours and take about fifteen minutes together.

| # | What | Who | Done when |
|---|---|---|---|
| 1 | Apply the `question_report` table: `cd backend && uv run python scripts/apply_sql.py ../supabase/migrations/20261001180000_question_report.sql --yes` (or sign in to the Supabase connector with `/mcp` and I apply it) | Shaked | the command prints `table question_report: exists`; the "question unclear" flag saves instead of saying "opens soon" |
| 2 | Render → Environment → `ANTHROPIC_MODEL` = `claude-opus-5-5` | Shaked | `/health` shows `"evaluator": "claude-opus-5-5"` |
| 3 | Rotate the database password (Supabase → Settings → Database), paste the new Transaction-pooler string into Render's `DATABASE_URL` and `backend/.env` | Shaked | `/health?db_check=true` is ok; `uv run pytest -q tests/test_live_db.py` passes locally |
| 4 | Rotate the Netlify build hook and update the GitHub secret `NETLIFY_PRACTICE_BUILD_HOOK` | Shaked | the next push shows a green "Deploy practice site" run |
| 5 | After 1: smoke test and live suite from this machine; add the report route to `smoke_http.py` | Claude | 26 routes pass; 17 live tests pass |
| 6 | The question drafts: finish the run, spot-check, validate with the loader, commit `seeds/question_drafts/` and the coverage report. **Not loaded**, per Shaked | Claude | the file and `docs/question-bank-<date>.md` are in the repo |
| 7 | Hide an attempt or an interview from the screen, data kept: table `user_hidden_item` (dry run → approval → apply), route, the hide action with undo and a "show hidden" switch | Claude, approval from Shaked | hidden rows vanish from "My practice" and "Previous interviews"; XP, levels and the plan unchanged |
| 8 | Skip to the next question in today's program: `POST /v1/me/program/skip`, the item marked skipped, the next opens, un-skip the same day; no XP, no penalty | Claude | the button works on the day's sheet and the probe; tests cover skip, un-skip and the empty day |
| 9 | A review page for drafts (approve, edit, reject, by skill) with reviewer access through `can_manage_tasks`; approved questions move into `seeds/questions` and load with the usual approval | Claude, Harel reviews | Harel can approve a question without opening JSON |
| 10 | Publishing: review the 30 questions (`seeds/questions/README.md` checklist), set `published` with a reviewer and a reuse status; the coach's suggestions and the interview then use them without the development flag | Harel / an engineer | `ALLOW_IN_REVIEW_CONTENT` can be turned off on Render |
| 11 | The content pass: Hebrew skill names in the seed, check messages and tip second lines in both languages, plan reasons in the page's language | Claude, content check by Harel | no English strings on the Hebrew screens except code |
| 12 | Anthropic tier when a group larger than a few testers is planned (Start tier ≈ ×4–5 capacity) | Shaked | decided |
| 13 | Housekeeping: delete `app.py`, `requirements.txt`, `src/__init__.py` placeholders once confirmed; UUIDv7 ids for append-only tables; cap `state.history_window`; daily-allowance checks as `created_at >= day_start` | Claude, confirmation from Shaked | tests pass, nothing else changes |
| 14 | Night runs: Windows set not to sleep while plugged in, so live suites and real-model scripts survive | Shaked | a live suite finishes without a mid-query drop |

### What is deliberately not on the list

- Changing how the engine evaluates. Thresholds, prompts and the skill controller change only with a decision and
  the review set.
- A second role beyond the digital hardware engineer. The software track lives inside this role's "relevant
  programming" subject for now; a separate software role is a content project, not a code change.
- Moving off Render or Supabase. Both carry the pilot comfortably; capacity is the model, not the servers.
