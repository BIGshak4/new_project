# JobRun: handoff to Shaked for the first real-feedback review

**Date:** 19 September 2026  
**For:** Shaked Buzi and Harel Artman  
**Code baseline:** `d055fa5` on `master`  
**Immediate goal:** both founders can sign in, solve real hardware/software questions, receive real model feedback, inspect the reference, and review the accuracy of the feedback and the saved learning evidence.

The frontend-to-backend integration is already working. The next milestone is a controlled human review of real feedback, not another integration rewrite. This document consolidates the current implementation and the remaining work. Suggested solutions are not the only valid approach; Shaked owns backend implementation decisions, with API or product changes coordinated with Harel.

Use this as the current handoff. Earlier integration/readiness documents contain historical proposals, including a mode selector, confidence questionnaire, visible demo grades and automatic follow-ups that are no longer part of the regular practice UI.

## 1. Current system and verified status

| Component | Current location and responsibility |
| --- | --- |
| Practice website | [jobrun-practice.netlify.app](https://jobrun-practice.netlify.app/) — `apps/web`, Next.js and TypeScript |
| Founder task board | [jobrun-tasks.netlify.app](https://jobrun-tasks.netlify.app/) — `apps/tasks`, separate private founder workspace |
| Practice API | [jobrun-api.onrender.com](https://jobrun-api.onrender.com/) — FastAPI in `backend`, deployed with Docker on Render |
| Database and identity | Existing Supabase project `djpwvqpsqbkvprlncjjg`; Auth, Postgres and private task attachments |
| Model integration | Anthropic adapter exists in the backend; the deployed runtime still uses the scripted demonstration provider |

During preparation of this document, `/health` returned `status=ok`, `env=staging`, `llm_provider=scripted`, `store=database`, and configured authentication and pooler database access. This establishes the reported runtime configuration, not a successful paid model call. No key, paid plan or database change was made for this handoff.

The local seed validator passes and reports **30 questions, all `in_review`**, 35 skills, six subjects, ten tips and 30 glossary terms. The deployed 30-question bilingual bank was verified during the integration work. The original target of at least 150 questions remains a later content milestone; 150 questions have not been implemented or reviewed.

```text
Practice browser on Netlify
  ├─ Supabase Auth → user access token
  ├─ Supabase → private bookmarks, notes and optional saved drafts
  └─ authenticated HTTPS → FastAPI on Render
                            ├─ Supabase Postgres → questions, attempts, evaluations, profiles
                            └─ model provider → scripted now; real API next

Founder task board on Netlify → Supabase Auth + founder-only tables/files
```

The two websites share the identity service and database, but their different domains have separate sign-in sessions. Practice access and permission to manage founder tasks are separate.

## 2. What has been completed

### A. Infrastructure and integration

- Both websites are deployed. The practice frontend calls the authenticated FastAPI API rather than reading the full question bank directly from the browser.
- Sign-in uses Supabase; the backend verifies tokens, checks pilot membership and enforces ownership of attempts. The pilot allowlist is `jr_members`; learners must not receive `can_manage_tasks=true`.
- Attempts, submitted answers, exposure history, evaluation results and skill updates have persistent server storage. Refresh uses the attempt ID in the URL to retrieve the same attempt.
- Starting practice is explicit and counts toward the daily limit. A page refresh does not start another attempt.
- The client saves the exact pending answer and its idempotency key before sending. Ambiguous network failures are reconciled against the server; retrying the same submission reuses that key.
- The UI supports saved-but-evaluating results, polling after HTTP 202, and retrying a failed evaluation. It does not blindly repeat paid submission requests.
- The separate task board supports assignees, dates, filters, subtasks, comments, private files, archive/history and conflict-safe saves. It does not require the model API.

Shaked's existing backend hardening already addresses immutable answer revisions, duplicate scoring, persistence through evaluation failure, exposure snapshots, tip usage accounting, review-preserving content imports, and profile update conflicts. These are regression requirements to preserve, not a request to implement those features again.

### B. Practice experience

- Hebrew and English UI, with a compact `EN` / `עב` switch in the toolbar. Technical code remains left-to-right.
- The question appears first, followed by one clear action to write a solution. The old mode/confidence setup form has been removed.
- **Every new UI attempt explicitly requests `mode: "quick"`.** One answer is submitted; automatic follow-up questions are not displayed. Backend deep mode and old follow-up records remain available for future work and export.
- Hints are revealed one at a time, with a visible count. The reference solution requires a separate explicit action.
- After submission, the UI clearly distinguishes **the candidate's submitted answer** from **the reference solution**. A prominent comparison button reveals the reference below the saved answer.
- While the provider is scripted, the screen says the answer is saved but has not received a real assessment. Fake feedback, grades and skill-progress scores are hidden.
- A dedicated **Practice assistant** area exists. It is the destination for real submission feedback once enabled. Interactive chat has not been implemented.
- History, bookmarks, personal notes and JSON export for review remain available.

### C. Technical answer editor

- Separate explanation field and CodeMirror editor with line numbers, syntax highlighting, indentation, undo and language selection.
- Supports C, C++, Python, JavaScript, Verilog, SystemVerilog, VHDL and plain text for formulas, truth tables and pseudocode.
- C/C++ now have local completions for keywords, common library names, current-document words, and `for` / `if` / `while` snippets. Python and JavaScript retain their language completions. Ctrl+Space opens suggestions; Enter accepts; snippet fields support Tab navigation.
- These editing aids run locally. They do not call a model, compile code, simulate HDL, or prove the answer correct. There is no schematic/drawing editor yet.
- Explanation and code are serialized into the existing answer text using a fenced code block. Draft restoration preserves both. No editor-related database migration was needed.

### D. Loading and answer exposure

- Catalog, progress, personal notes and health load independently. A slow background request no longer holds back an already available question list.
- A per-user, per-language, 12-hour session cache contains only allowed question-summary fields. It never contains hidden hints, references or evaluation rubrics.
- The old “Question requirements” disclosure was removed because some authored requirements contained answer details. The public detail response keeps an empty compatibility field; the full requirements remain available to the server evaluator.
- The deployed exposure migration closes direct browser reads of `question`, `question_translation` and the internal `attempt.follow_up_turns` column. Do not reopen these grants to simplify frontend work.
- The Render blueprint still uses a free service. Independent loading does not remove a cold start: Render documents idle suspension after 15 minutes and roughly a minute to wake. Measure cold and warm requests separately; choose an always-on instance if immediate first-load response becomes a required acceptance criterion. No hosting upgrade is required merely to start a scheduled internal feedback review. [Render documentation](https://render.com/docs/free)

## 3. The API contract to preserve

The live [OpenAPI page](https://jobrun-api.onrender.com/docs), [response schemas](../backend/app/schemas/api.py) and [typed frontend client](../apps/web/src/lib/practice-api.ts) are the implementation references.

| Operation | Current route |
| --- | --- |
| List / read questions | `GET /v1/questions?language=he` / `GET /v1/questions/{key}?language=he` |
| Start / restore attempt | `POST /v1/practice/attempts` / `GET /v1/practice/attempts/{id}` |
| Next hint / reference | `POST /v1/practice/attempts/{id}/hints/next` / `POST /v1/practice/attempts/{id}/reference` |
| Submit answer | `POST /v1/practice/attempts/{id}/submissions` with `Idempotency-Key` |
| Retry failed evaluation | `POST /v1/practice/attempts/{id}/submissions/{revision}/retry` |
| Saved history / skills | `GET /v1/me/progress` |

All `/v1` calls require the user's bearer token. The normal frontend submission is:

```json
{
  "answer": {
    "text": "My reasoning...\n\n```c\nfor (size_t i = 0; i < n; ++i) {\n    total += a[i];\n}\n```"
  }
}
```

The current combined limit is **20,000 characters**, including code fences. The editor's language choice is represented in the fence, not a separate API field. If structured answer fields are added later, keep existing saved answers and clients compatible.

`SubmissionView` exposes the accepted answer's immutable `hints_seen` and `reference_seen`. Current assistance multipliers for 0/1/2/3 hints are 1.0/0.8/0.6/0.4, with a `quick` base evidence weight of 0.3 before familiarity and exposure factors. These are confidence/evidence weights, not percentage grades. Revealing the reference **before** submission yields no independent mastery evidence; revealing it **after** submission must not rewrite that answer's recorded assistance.

Review this calibration intentionally. If the new single-answer experience deserves a different weight, change the explicit policy and tests in [params.py](../backend/app/engine/params.py). Do not switch the frontend back to deep mode merely to increase its weight: that also changes the flow and can generate follow-ups.

## 4. Remaining work for Shaked, in execution order

### P0. Separate demonstration history from real assessment

**Why this comes first:** the scripted pipeline has already written demonstration evaluations and profile updates. Hiding those values in the UI does not remove them. Today, the frontend decides whether to show assessment using the server's current `/health.llm_provider`; it does not know each historical submission's provider. Simply switching the server to Anthropic could expose old demonstration results as if they were real.

Choose and document a bounded transition:

- Preferred durable approach: expose persisted evaluation provenance in the API, identify scripted/real results per submission, filter demo evidence from real progress, and coordinate the frontend display change. Model/version fields already exist in evaluation metrics and usage records; inspect them before adding another table.
- A smaller internal-test alternative is an isolated clean dataset or test cohort. If Harel and Shaked want to use their existing personal accounts, agree on a scoped archive/reset of **practice assessment** data first. Preserve task-board records, accounts and any answers they want to keep. Do not perform a blanket database reset.

**Done when:** a prior scripted attempt cannot be presented or counted as a real assessment, and each founder's first real test starts from an understood baseline.

### P1. Connect and verify the real provider

The existing runtime supports Anthropic, so that is the shortest integration path. Another provider is valid but requires an adapter plus changes to the frontend's current `health.llm_provider === "anthropic"` check.

1. Prepare company-controlled API access, a dedicated key and an agreed small review budget. Follow the provider's [API setup](https://platform.claude.com/docs/en/get-started).
2. Choose a model available to that account. The repository currently defaults to `claude-opus-5`; this is a configured baseline, not proof that the company's account and this SDK request have been tested successfully. Check the [model catalog](https://platform.claude.com/docs/en/models/overview) when selecting it.
3. Test the actual adapter request, including `messages.parse`, structured schemas, effort settings, token limits, streaming used internally for text responses, and the optional fallback beta. A successful generic “hello” call is insufficient. If an optional feature is unsupported, disable or adapt it rather than silently replacing real feedback with a scripted result.
4. Configure the Render service, redeploy, then perform a real authenticated submission. Verify model output, stored feedback, usage and returned model ID.

| Setting | Action |
| --- | --- |
| `LLM_PROVIDER` | Change `scripted` to `anthropic` only after the demo-data plan is ready. The variable is **not** `AI_PROVIDER`. |
| `ANTHROPIC_API_KEY` | Set as a Render secret; never in frontend variables, Markdown or Git. |
| `ANTHROPIC_MODEL` | Set the exact tested model ID. |
| `ANTHROPIC_ENABLE_FALLBACKS` | Explicitly verify the chosen setting against the actual provider request. |
| `ENV` | Keep `staging` for this controlled internal review. |
| `DATABASE_URL`, `SUPABASE_URL` | Preserve the existing working database/auth configuration. |
| `REQUIRE_PILOT_MEMBERSHIP` | Keep `true`. |
| `ALLOWED_ORIGINS` | Keep the actual practice origin and required development origins; do not replace them with a wildcard. |
| `ALLOW_IN_REVIEW_CONTENT` | `true` is acceptable only for the clearly identified internal review cohort; production checks reject it. |
| `DAILY_ATTEMPT_LIMIT` | Keep a small agreed limit. This is an attempt-count limit, not a hard monetary spending cap. |

The frontend already has `NEXT_PUBLIC_API_BASE_URL` configured. A working real provider should make existing submission feedback appear in the assistant area; no new evaluation endpoint is required just to display that feedback. A health response naming Anthropic is not itself evidence that a model call succeeded.

**Done when:** one correct and one incorrect answer produce substantive, persisted real feedback in each language, with measured latency and usage, and without automatic follow-ups.

### P2. Verify feedback against the actual editor payload and languages

- Feed the evaluator the question, trusted rubric and reference, the complete explanation/code, and the accepted assistance snapshot. Preserve code whitespace and distinguish candidate text from system instructions.
- Exercise prose-only, code-only, Hebrew explanation plus C/HDL, formulas, truth tables, valid alternative approaches, irrelevant text and deliberately incorrect answers. Do not reward answer length or plausible wording as correctness.
- Check deterministic-check parsing against fenced editor text. Boolean/numeric checks exist, but this is not a general compiler or HDL simulator. An unparseable check must remain “not checked,” not an invented pass/fail. Existing check detail strings can be English; inspect the real Hebrew feedback path and localize user-visible messages where needed.
- Verify that technical correctness and reasoning/communication are assessed separately. An FSM design error is a technical skill gap; unclear explanation is a different dimension.
- Confirm Hebrew/English feedback follows the **attempt's language**. Switching the UI language currently does not rewrite an existing attempt's hints or feedback. Starting a new English attempt should produce English feedback.
- Review feedback-card fallbacks and partial failures. A missing explanation, unavailable provider or fallback template must not look like a completed expert-quality assessment.

**Done when:** a small agreed answer set produces defensible classifications and useful explanations, and any known uncertainty is visible to the reviewers.

### P3. Prepare the first human-reviewed content batch

Start with a manageable **10–15 question review set** drawn from the 30-question bank. Include combinational logic, sequential logic/FSMs, timing, relevant C/debugging, and any other topic both founders can review competently. This suggested size is for the first review session, not a reduction of the product's eventual bank target.

For each question, Harel and Shaked should verify the prompt, constraints, accepted approaches, reference, three progressively useful hints where applicable, skill mapping, rubric, difficulty and Hebrew/English parity. Put candidate-facing requirements in the public prompt; keep grading expectations private. Check that hint 1 does not immediately reveal the full solution.

Questions must be technically solvable as presented, including any needed diagrams/assets, units, bit widths and reset assumptions. Keep source/reuse metadata with content. Mark content as reviewed/published only after the actual review; re-importing files must preserve or invalidate review state according to the existing content-hash policy.

Use [seed_db.py](../backend/scripts/seed_db.py) deliberately: `--check` validates files, `--dry-run` tests database loading and rolls back, and running without either flag writes content. Database-backed serving reads questions from the database; editing a seed file alone does not update the live question.

### P4. Check failures, cost and deployment before the joint session

- Re-run the relevant backend regressions after provider/configuration changes. The prior fixes are not evidence that a real model has been tested.
- Verify a lost response, duplicate submission, evaluator failure, failed-revision retry and delayed HTTP 202 recovery. Scores must not be applied twice. A server process restart can interrupt model work; confirm the existing recovery/retry path rather than assuming the in-process background task survives it.
- Verify both personal accounts have confirmed email, pilot membership and independent histories. Recheck Shaked's sign-in; an older handoff recorded his confirmation as pending, and that status was not freshly verified here.
- Measure cost and latency for the **whole answer flow**: evaluator, feedback and optional tip polishing. The quick flow avoids automatic generated follow-ups, but can still make several model calls. Metering exists; reconcile it with actual provider usage, including retries, and preserve “unknown cost” for an unrecognized price entry.
- Define a small review-session budget and a stop mechanism. Attempt quotas alone do not bound retries, token usage or concurrent provider calls. Verify the available spending/concurrency controls before broadening access.
- Record the backend commit/model/prompt versions and the frontend deployment. Git push currently triggers Render auto-deploy; the Netlify sites still use manual deployment. A frontend change must be deployed separately to `apps/web`'s existing site.

No new database, vector store, Redis service, mobile app, paid monitoring platform or task-board rewrite is a prerequisite for this milestone.

## 5. Human review session: the acceptance checklist

This is the gate for beginning meaningful founder testing, not certification for a public launch. Run with deliberately prepared examples and retain the results, not only screenshots of successful requests.

| Test | Expected result |
| --- | --- |
| Two personal accounts | Each sees its own attempts/progress; both retain authorized founder-board access. |
| Correct answer | Feedback explains why it satisfies the requirements and does not invent errors. |
| Partial answer | Feedback identifies the missing requirement or reasoning and gives a useful next step. |
| Incorrect / irrelevant answer | Feedback identifies the technical issue; fluent or long nonsense is not praised as correct. |
| Different valid solution | Accepted when it meets the constraints, even if it differs from the reference. |
| Hebrew and English | Meaning and feedback quality agree; code and technical notation stay readable. |
| Explanation plus code / HDL / formula | Actual editor text is evaluated intact; no claim of execution unless a real check was run. |
| Zero, one, two and three hints | Exact count is stored; assistance affects evidence using the chosen policy, separately from correctness. |
| Reference before submission | Saved as assisted practice, without independent mastery evidence. |
| Reference after submission | Comparison opens; the earlier answer's assistance snapshot remains unchanged. |
| Refresh / reopen / duplicate click | Same answer and feedback return without another revision, score update or unnecessary model call. |
| Provider failure or timeout | The accepted answer survives, the state is understandable, and the supported retry works. |
| Demo-to-real transition | No old scripted score is mislabeled or included in real progress. |
| Progress after several answers | Changes are traceable to genuine assessed attempts and plausible to a human reviewer. |

Suggested initial quality gate: no unresolved critical errors in this small set, including false confident feedback on clearly wrong answers, lost answers, duplicate scoring, cross-user exposure or demo results presented as real. Track less severe wording/usability issues separately. Agree on quantitative quality thresholds after seeing the first batch; do not declare validated accuracy based only on this smoke test.

### Review record for each attempt

Export the attempt using **Export for review** and attach it to a task-board issue when useful. Record:

```text
Reviewer / date:
Frontend deployment / backend commit:
Provider / returned model ID / prompt and engine version:
Question key / question version / attempt ID / practice language:
Submitted explanation and code:
Hints seen before submission / reference seen before submission:
Expected assessment and technical rationale:
Actual band, summary, feedback and suggested next step:
Warm/cold load time / feedback latency / usage or estimated cost:
Verdict: acceptable | minor issue | major issue | critical
Issue category: content | translation | input parsing | evaluator |
                feedback wording | scoring | UI | persistence | latency
Evidence / owner / next action:
```

The current JSON export includes the attempt view; it does not yet expose every diagnostic/version field above. Shaked should provide missing provenance through a safe review export or a controlled server-side lookup. Do not paste credentials or access tokens into the board.

## 6. What can wait until after this milestone

| Item | Boundary for now |
| --- | --- |
| Conversational AI coaching | The dedicated area exists, but chat needs a separate authenticated interaction contract, storage and assistance tracking. It is not necessary to start reviewing post-submission feedback. |
| Chat that gives extra help | When added, record that assistance and enforce explicit solution reveal; chat must not bypass hint/exposure accounting. |
| Voice/video, competitions, matchmaking, employer workflows | Outside the first human-feedback review. |
| Automated prompt/model improvement | Begin with a versioned human-reviewed evaluation set. Later compare candidates against it before promoting changes. |
| Branded email, broad onboarding, public production launch | Separate release work. Confirm email delivery, access policy, content publication and production settings before external invitations. |
| Full 150-question bank and additional fields | Expand after the first content/feedback review process works. |

## 7. Verification evidence and useful entry points

Previously completed at the code baseline: **17 frontend tests**, TypeScript and the Netlify production build passed; the last backend run reported **531 passed, 16 environment-dependent tests skipped**. Browser checks covered desktop/mobile, answer persistence, hints, explicit reference exposure, C/C++ completion and unchanged Python completion. Temporary test accounts were removed. These are prior run results, not a claim that all tests were rerun for this documentation-only change, nor evidence of real-model accuracy.

Fresh checks for this handoff: repository synchronization, source/configuration inspection, live `/health`, and `seed_db.py --check`. No paid model calls were made.

Useful commands, from the indicated directories:

```powershell
# apps/web
npm ci
npm test
npm run typecheck
npm run build

# backend, after configuring a suitable local environment
uv sync
uv run pytest -q
uv run python scripts/seed_db.py --check
uv run python scripts/smoke_http.py --url https://jobrun-api.onrender.com
```

Live database tests require an appropriate configured test environment; inspect their rollback harness before running them. Report skipped tests explicitly. Health/HTTP smoke tests do not perform the full authenticated real-feedback review above.

| Work area | Start here |
| --- | --- |
| Frontend attempt flow / assistant area | [practice-session.tsx](../apps/web/src/components/practice-session.tsx) |
| Answer serialization / editor | [technical-answer.ts](../apps/web/src/lib/technical-answer.ts), [answer-editor.tsx](../apps/web/src/components/answer-editor.tsx) |
| C/C++ completions | [c-code-completions.ts](../apps/web/src/lib/c-code-completions.ts) |
| API client / UI provider detection | [practice-api.ts](../apps/web/src/lib/practice-api.ts), [page.tsx](../apps/web/src/app/page.tsx) |
| Provider configuration | [config.py](../backend/app/config.py), [runtime.py](../backend/app/runtime.py), [providers.py](../backend/app/engine/providers.py), [render.yaml](../render.yaml) |
| Acceptance, evaluation and evidence | [practice.py](../backend/app/engine/practice.py), [practice_service.py](../backend/app/services/practice_service.py), [params.py](../backend/app/engine/params.py) |
| Feedback and language prompts | [feedback.py](../backend/app/engine/feedback.py), [prompts](../backend/app/engine/prompts) |
| Safe questions / content import | [questions.py](../backend/app/repo/questions.py), [seed_db.py](../backend/scripts/seed_db.py) |
| Existing implementation details | [guided practice handoff](guided-practice-and-assistant-handoff.md), [loading and help notes](practice-ui-loading-and-help.md) |

Before any future schema deployment, reconcile the previously documented local/live migration timestamp differences. Do not blindly apply every local migration; inspect the live history and dry-run the intended change. Nothing in this handoff requires a schema reset.

## 8. What Shaked should hand back

- [ ] The chosen demo-data separation method, with any frontend/API changes clearly identified.
- [ ] Deployed backend commit, provider/model/configuration, and confirmation of successful real calls in both languages.
- [ ] The question keys and prepared answers for the first joint review session.
- [ ] Results for failure/retry, assistance snapshots and usage checks, plus any known limitations.
- [ ] A practical review budget and observed feedback latency.
- [ ] Confirmation that both founders can sign in and begin the checklist in section 5.

With these items ready, Harel and Shaked can test the actual learning experience together and turn disagreements into concrete content, prompt, scoring or UI fixes.
