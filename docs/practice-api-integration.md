# Connecting `apps/web` to the practice API

- Date: 18 September 2026
- For: Harel (frontend), Shaked (backend)
- Backend baseline: `backend/` at commit `b9670dc` or later; contract at `/docs` of the running API

## 1. Run it locally

```powershell
cd backend
uv sync
copy .env.example .env        # fill SUPABASE_URL (already there), ALLOWED_ORIGINS, optionally DATABASE_URL
uv run uvicorn app.main:app --reload
```

- `http://127.0.0.1:8000/docs` is the contract (OpenAPI). Every response model there is exactly what the code returns.
- `LLM_PROVIDER=scripted` (default) gives instant fake evaluations: enough to build every screen. No key.
- Without `DATABASE_URL` the API keeps everything in memory and serves the 30 seed questions; attempts are lost on restart. With it, everything is durable in Supabase.
- `uv run python scripts/smoke_http.py` starts a server and checks it over HTTP; `--url https://…` checks a deployment.

## 2. Authentication

Every `/v1` route needs the Supabase **access token** as a Bearer token, and the e-mail must be in `jr_members`:

```ts
const { data: { session } } = await supabase.auth.getSession();
const res = await fetch(`${API}/v1/me`, { headers: { Authorization: `Bearer ${session.access_token}` } });
```

The backend verifies the signature against the project's JWKS, plus issuer, audience and expiry. The user id always comes from the token; never send a user id in a body.

| Status | `error.code` | Meaning |
|---|---|---|
| 401 | `unauthenticated` | no / expired / invalid token, or the account no longer exists |
| 403 | `forbidden` | signed in, but not on the pilot list (`jr_members`) |
| 404 | `not_found` | unknown question or attempt, or an attempt that is not yours (we do not reveal which) |
| 409 | `conflict`, `already_submitted`, `no_pending_follow_up`, `nothing_to_retry` | see §4 |
| 422 | `validation` | bad input; `error.details` lists the fields |
| 429 | `usage_limit` | daily attempt limit; the message says when to come back |
| 202 | — | the answer is saved and **still being evaluated** (slow model); the body has the same shape with `submission.status = "evaluating"`. Poll `GET` the attempt (the client's `waitForEvaluation`) until `attempt.status` leaves `evaluating` |
| 503 | `evaluation_unavailable` | the evaluation could not be reported; the answer is saved, `GET` the attempt and retry |
| 503 | `temporarily_unavailable` | the database connection dropped mid-request (`Retry-After: 2`); nothing was written, repeat the same call with the same Idempotency-Key |
| 500 | `internal` | our bug; `error.request_id` for the logs |

Every error body is `{"error": {"code": "...", "message": "..."}}`. Every response carries `X-Request-Id`.

## 3. The flow

```
GET  /v1/questions?language=he                → list (safe: no reference, no hints)
GET  /v1/questions/{key}?language=he          → prompt, code, choices, hint_count
POST /v1/practice/attempts                    {question_key, mode: "deep"|"quick", language, self_confidence?}   → 201 AttemptView
POST /v1/practice/attempts/{id}/hints/next    → {hint: {level, text} | null, attempt}
POST /v1/practice/attempts/{id}/reference     → {reference, attempt}          (recorded; answers after it earn no evidence)
POST /v1/practice/attempts/{id}/submissions   {answer: "..." | {text}, latency_ms?, revision_count?}
                                              header Idempotency-Key: <uuid>   → {submission, attempt}
POST /v1/practice/attempts/{id}/follow-ups/{turn}/submissions   {answer}, Idempotency-Key   → {submission, attempt}
POST /v1/practice/attempts/{id}/submissions/{revision}/retry    → {submission, attempt}     (after status "failed")
GET  /v1/practice/attempts/{id}               → AttemptView (everything needed to redraw the page after a refresh)
GET  /v1/me/progress                          → skills (level, status, trend), recent attempts, attempts_today
```

`AttemptView.status` is `in_progress` | `evaluating` | `done` | `failed` (`evaluating` = a revision is being scored right now, possibly on another server); `can_submit`, `can_retry`, `hints_remaining`, `pending_follow_up` tell the UI what to show. `SubmissionView.assessed_by` is `demo` while the server runs the scripted stand-in and `model` (with `model` = the model id) for a real assessment — only `model` results are real feedback or evidence. `SubmissionView` also has `band` (STRONG/PARTIAL/WEAK), `summary`, `key_points_hit/missed`, `check` (the automatic check, when the question has one), `card` (the four-part feedback), `tip`, `follow_up` (the next question, if any), `evidence` (`full` | `reduced` | `none`) and `flags`.

Added 2026-09-20:

- **`next_question`** on `SubmissionView` and `AttemptView`: `{key, title, subject, skill, difficulty, why, reason}` — what to practise next, decided from this evaluation (`why` = `reinforce` after a WEAK answer, `consolidate` after PARTIAL, `advance`/`explore` after STRONG; `reason` is one sentence in the practice language). It is a servable question, so `POST /v1/practice/attempts` with its `key` starts it. `null` when the bank has nothing left to suggest. The suggestion is stored on the attempt, so a refresh shows the same one.
- **`check.type`** is `truth_table` | `numeric` | **`code_tests`** and **`check.mismatches`** lists the first differing rows (`{row, inputs, expected, got}` for truth tables; `{case, inputs, expected, got | error}` for code tests). `code_tests` runs the Python in the answer (a ```python fence, or an untagged fence that parses) against the question's cases in an isolated child interpreter; C, pseudocode or prose give `passed: null` and the model reviews the answer as written.
- **`GET /v1/me/progress`** now returns **`subjects`**: one row per subject with `skills_total/assessed/started`, `levels` (`"1".."5"` → skills at that level), `average_level`, `bands` (STRONG/PARTIAL/WEAK answer counts), `attempts`, `weight` (share of the role plan) and `questions_available`. `recent[]` rows carry `subject`.
- **Visual answers are assessed.** A drawn circuit is turned into a netlist plus derived Boolean functions (`alarm = (A & B) | ...`) that the evaluator reads and the truth-table check tests; flag `circuit_assessed`. Photos are fetched server-side from the private bucket when the server has `SUPABASE_SERVICE_ROLE_KEY` and shown to the model as images (flag `images_assessed`; `images_unavailable` for a photo that could not be read). Without the key: `images_not_assessed`; a photo-only answer with no text or circuit stays `assessed_by: "unassessed"` with flag `visual_review_pending`. `/health.answer_images` is `assessed` or `stored_only`.

## 3b. Mock interviews (added 2026-09-22)

A timed interview run by the session engine (subject router + skill controller). Bank questions only, and by
default only questions a person has reviewed and published (`INTERVIEW_REVIEWED_ONLY=true`): a role skill with no
reviewed question is left out of the interview, and with none left the start returns `409 no_reviewed_questions`.
Nothing is generated. Like a real interview, bands and summaries are hidden until it is over.

| Call | Purpose |
|---|---|
| `POST /v1/interviews` `{duration_min: 20|30|45, language?}` | start; returns the `Interview` with `current_turn` (the first question). `429 usage_limit` after `INTERVIEW_DAILY_LIMIT` (5) a day |
| `GET /v1/interviews` | my interviews, newest first (`InterviewListItem[]`) |
| `GET /v1/interviews/{id}` | the interview as it is now; refresh-safe |
| `POST /v1/interviews/{id}/turns/{index}/answer` `{answer, idempotency_key?, latency_ms?}` + `Idempotency-Key` | answer the current question; `200 {turn, interview}`; `202` when the evaluation runs past 90 s (poll GET until `status` leaves `evaluating`); same key = same result, another key for an answered question = `409 already_submitted` |
| `POST /v1/interviews/{id}/hints/next` | a bank hint for the current question (coach mode; `can_hint` says whether one is available); costs struggle budget |
| `POST /v1/interviews/{id}/end` | stop early; the report covers what was answered |
| `GET /v1/interviews/{id}/report` | scorecards (`fit.role`, `fit.session_overall`, `fit.company` when not Generic), per-skill levels with strengths and gaps, subjects, timeline, recommended next skills, tips, narrative markdown; `409` while the interview runs |

`Interview.status` is `in_progress` | `evaluating` | `completed`; `remaining_min` counts down from the chosen duration
by the time spent on each question; the engine ends the interview when time is up or nothing is left to ask
(`turn_count` ≤ 40). `results_revealed` and `report_ready` turn true on completion, and `turns[]` then carry `band`,
`summary`, key points and `action_after` (what the interviewer decided next). The candidate's skill profile continues
through the interview and is updated after every scored turn.

## 4. Rules the UI must respect

1. **Generate an `Idempotency-Key` (uuid) per submit click and reuse it on retry.** A resend with the same key returns the same result with `replayed: true` and costs nothing. The same key with a different text is a 409 `conflict`. If you send none, the server generates one and returns it in `submission.key`.
2. **Submit waits for the result** (typically 5–30 s with the real model). Show a waiting state; do not re-submit. If it takes longer than ~2 minutes the response is **202** with `status: "evaluating"` and the evaluation continues on the server: poll `GET` (`api.waitForEvaluation(id)`) until the status changes. If the request fails at the network level, `GET` the attempt: the answer is already saved. A `failed` status means the model was unavailable; offer "try again" → `retry`. While a revision is `evaluating`, `retry` and a second submit are refused (409).
3. **After the main answer, only follow-ups.** A second main answer is 409 `already_submitted`; the user starts a new attempt for the same question. Answer the follow-up whose `turn` is in `pending_follow_up`; anything else is 409 `no_pending_follow_up`.
4. **Refresh = `GET` the attempt.** Never re-post. The view contains the hints shown, the reference if revealed, the submission with its card, and the pending follow-up.
5. **The question detail never contains the answer.** Hints come one at a time from `/hints/next`; the reference from `/reference`. The frontend now browses through the safe API too. Migration `20260919093403_restrict_practice_question_reads.sql` closes direct browser reads of `question` and `question_translation`, including column grants, and withholds `attempt.follow_up_turns` because its internal JSON contains expected answers. Deploy the API-based frontend before applying this migration (review finding R6).
6. `jr_practice_entries` keeps working for self-ratings, bookmarks and drafts. `self_confidence` on start is the 1–5 rating the engine uses for calibration.

## 5. Deployment (stage G)

`render.yaml` at the repo root deploys `backend/` as a Docker web service. Secrets are entered in the Render dashboard: `DATABASE_URL` (Session pooler URI), `ALLOWED_ORIGINS` (the Netlify URLs and `http://localhost:3000`), later `ANTHROPIC_API_KEY`. `ENV=staging` until the real model is in; `production` refuses to start with a scripted or manual model. The site then needs `NEXT_PUBLIC_API_BASE_URL=https://jobrun-api.onrender.com` (or whatever Render assigns).

Free-tier note: the service sleeps after 15 minutes idle and takes ~30 s to wake; the first request after a pause will be slow. A paid plan removes that.

## 6. Integrated frontend

`apps/web/src/app/page.tsx` uses the typed client for the library, history and progress. `src/components/practice-session.tsx` implements start, hints, reference, main answer, follow-ups, failed-evaluation retry and saved-state recovery. URLs carry the attempt ID so reloads use GET and never silently start another attempt.

The UI saves the pending submission's original text and idempotency key in session storage before sending. A lost response triggers a saved-state check; a resend keeps the same key and text. Mutations are disabled while a request is running or its outcome cannot be checked. Feedback and attempts always come from the server; local drafts are not a cross-device backup. Optional account draft saving, bookmarks and self-ratings still use the user's RLS-protected `jr_practice_entries`.

The deployed provider is still `scripted`. The UI labels feedback and progress as simulated; a successful integration test is not a validation of AI feedback quality. See [pilot integration handoff](pilot-integration-handoff.md) for the verification record and founder test checklist.
