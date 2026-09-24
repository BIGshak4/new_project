# System verification after the overnight build — 24 September 2026

Written for Shaked and Harel. Shaked asked for eight things before he left on the evening of 23 September and a full
verification of the whole site from scratch at the end. This is what was built, what was checked, what was found and
fixed, and what waits for a human decision in the morning. `backend/STATUS.md` §5k has the feature-by-feature notes.

## 1. What was verified

| Area | Check | Result |
|---|---|---|
| Backend code | `ruff`, 709 offline tests (engine, service, routes, chaos, sandbox, visual, suggestions, interview, and 25 new tests for job types, the goal, company sightings, the progress parts and drawings in interviews) | clean, all pass |
| Backend, real database | 17 live tests against Supabase (rolled back): every question in both languages, persistence, retry after model failure, double clicks, daily limit, cross-user access, RLS, reseeding, HTTP flow, a whole interview | **17 passed, 18 m 28 s** (§1a) |
| Backend, real model, production rules | `scripts/e2e_live_trial.py` (rolled back): weak majority answer → WEAK in 15 s → one follow-up (PARTIAL, 9 s) → focused next question; 20-minute interview, 3 trial questions scored in 8–9 s each, report with narrative in 30 s | passes, $0.40 |
| Backend, real model, tonight's features | `scripts/e2e_goal_and_visuals.py` (rolled back): goal saved on the real profile row and read back in Hebrew; 28 of 30 questions relevant to "verification", ordered by relevance; sightings writer answers 503 while its table is missing and readers stay empty; progress overview / graph points / a 10-item plan over 7 days at 20 min a day; an interview turn answered with a **drawn circuit** scored by Opus in 9 s with `circuit_assessed`, the drawing stored on the turn and shown in the report | passes, $0.15 |
| Render | `scripts/smoke_http.py --url https://jobrun-api.onrender.com`: health, docs, all **23** v1 routes present, CORS allowed/refused, 401/404/405/413 shapes, forged token, JWKS | all checks pass; `answer_images: assessed` |
| Web app | `tsc --noEmit`, 38 unit tests (5 new for the graph and plan helpers), `next build` | clean, pass, builds |
| Deploys | push → Render (API) and Netlify (practice site) through the GitHub workflow | both automatic; the workflow runs for all three commits succeeded in under a minute |
| Production image | `docker build` of the same Dockerfile | **not run locally** (Docker Desktop's daemon is off on this machine); Render built it from the same file and the smoke test ran against that build |
| Independent review | a second agent reviewed the whole diff for defects (it ran the offline suites itself) | 6 findings, all fixed the same night (§2) |
| Database changes | `scripts/dry_run_sql.py` on both new migrations, rolled back, with a Hebrew-slug probe on the constraint | dry runs OK; **both applied on the morning of 24 September with Shaked's approval**; company tags verified on the real database afterwards |

### 1a. Live suite

**17 passed in 18 m 28 s** from Shaked's machine on the night of 23–24 September, in one full run (the run that the previous session started was cut off with it and was simply repeated). The two "every question" blocks that used to drop the connection on Windows passed inside the full run this time. The suite ran while the real-model scripts were using the same database, with no interference.

## 2. Found and fixed tonight

1. **The plan until the interview was empty in production.** The Plan Router's coverage check read the question status from the seed file (in review) instead of the database (trial), so with 30 trial questions it saw nothing to schedule. Found by the real-data script, not by the offline tests (the in-memory store cannot disagree with the seed file). Fixed like the interview pool: the database state is copied onto the question. A test now builds the plan from summaries that say "trial" over a seed that says "in review". The production plan now has 10 items over 7 days.
2. **Hebrew company names would have been refused by the database.** `slugify` kept Hebrew letters but the table's check constraint allowed only `a-z0-9`; the first "ראיתי את זה באינטל" would have been a 500 once the table existed. Both sides now accept the same alphabet (Latin, digits, Hebrew letters); a test extracts the regex from the migration file and checks it against the Python slugs, including a 200-character name and one ending in a dash. Probed on the real database in the dry run.
3. **The goal endpoint echoed the request instead of the row.** A request without seniority kept the stored value but answered `null`. It now returns the row as stored; omitting seniority keeps the profile's value (the column also belongs to Harel's app).
4. **"Today" in the goal card was the UTC date**, so after midnight in Israel the picker allowed yesterday and the day count disagreed with the server by one. Local calendar day now.
5. **The plan's tick was decided by the last 10 attempts, scored or not.** An opened-and-abandoned question ticked today's row, and the tick could vanish after the eleventh attempt. Now: scored answers of the day, from a 60-row history.
6. **The library said "ordered by relevance" while the unfiltered list was still showing** (filter request in flight, or refused because a saved job type no longer exists). The note waits for the filtered list; a refused filter is dropped.
7. Smaller: the graph's day buckets are explicit UTC whatever the connection's time zone; the scripts print UTF-8 on a Windows console (two script runs died on an arrow character before that).

## 3. Waiting for Shaked (the morning list)

Items 1 and 2 were done on the morning of 24 September after Shaked's approval (migrations `20260924045708` and `20260924045651`, `INTERVIEW_PHOTOS` on).

1. **Apply migration `supabase/migrations/20260924045708_question_sightings.sql`** (the "I saw it at company X" table). Until then the button says "company tags are opening soon" and company search returns nothing. Dry run: `uv run python scripts/dry_run_sql.py ../supabase/migrations/20260924045708_question_sightings.sql`, then apply through the MCP as usual and rename the file to the version it assigns.
2. **Apply migration `20260924045651_interview_answer_images.sql`** (photos in interview answers: the upload rule and its trigger also accept an in-progress interview of the same learner). Dry run needs `--replaces "policy learners upload answer images"`. Then set `INTERVIEW_PHOTOS = true` in `apps/web/src/components/interview-session.tsx` and push. Until then the interview offers the circuit drawing only, which works end to end today.
3. **Rotate the Netlify build hook** that was pasted in chat and update the GitHub secret `NETLIFY_PRACTICE_BUILD_HOOK`.
4. **Opus 5.5** exists (`claude-opus-5-5`, $4 in / $20 out per million tokens). Decide whether to run the 13-answer P2 set on it before changing the evaluator. Nothing was changed tonight.
5. **Look at the site once**: sign in fresh (or clear the "later" flag) to see the goal card, pick a job type, open the progress page, answer one question and watch the feedback → follow-up → next question flow. Say what feels off; the visual refresh is a taste call.

## 4. Observations, not bugs

- **The level word is honest and therefore slow to move.** It is the rounded average of assessed plan skills; one strong answer on one skill still reads "Getting started" because most skills are unassessed. The counts and the message carry the encouragement until the meter moves. If that feels too flat, the rank could count "started" skills too; it is one line in `_level_rank`.
- **Job types are a lens, not a wall.** A job type multiplies the role's skill weights (0.2–2.5) and the plan is renormalised, so an embedded candidate still sees some digital-design questions, lower in the list. "Software" and "student/general" lean on the same hardware bank for now; the bank has no pure software questions beyond the seven code questions.
- **Relevance ties.** Most questions have one primary skill and one secondary, so many share the same relevance score within a job type; the tie is broken by difficulty then key. That is fine for now; with a larger bank a per-question job tag would be better than a formula.
- **The plan regenerates on every load**, so it only ticks today's items; yesterday's are not remembered. The `learning_plan`/`plan_item` tables exist for a persisted plan when that matters.
- **Interview drawings on non-Boolean questions.** The circuit is described to the evaluator whatever the question; the deterministic check only understands one-bit combinational logic. On a timing or FSM question the drawing helps the judge but produces no check result (the run above shows `check=None` for the masked-equality question).
- **Cost of tonight's verification:** about $0.60 of model calls, all inside rolled-back transactions.

## 5. Scripts added or changed

- `backend/scripts/e2e_goal_and_visuals.py` — tonight's features on the real model and database, rolled back (about $0.15).
- `backend/scripts/dry_run_sql.py --replaces` — for migrations that drop and recreate a policy.
- `backend/scripts/smoke_http.py` — knows the 23 routes.
