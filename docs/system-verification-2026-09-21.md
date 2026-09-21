# System verification and improvement suggestions — 21 September 2026

Written for Shaked and Harel. A full pass over the system after the overnight build and today's changes
(one follow-up per attempt, the focused next question). What was checked, what was found and fixed, and what
to do next, in priority order.

## 1. What was verified

| Area | Check | Result |
|---|---|---|
| Backend code | `ruff`, 620 offline tests (engine, service, API routes, chaos, sandbox, visual, suggestions) | clean, all pass |
| Backend, real database | 16 live tests against Supabase: every question in both languages, persistence, retry after model failure, double clicks, daily limit, cross-user access, RLS, reseeding, HTTP flow | see §1a |
| Backend, real model | `scripts/e2e_real_flow.py`: wrong majority answer → one follow-up → focused next question (English); buggy Python in Hebrew → code test fails with the failing cases → follow-up → next question; drawn majority circuit → derived function passes the truth table → follow-up → next question | all three flows complete; 17 model calls, $0.15 |
| Backend, judging quality | `scripts/p2_review_set.py`, 13 review answers on Opus 5 after this week's prompt changes (circuit/image blocks, neutralised check results) | 13/13 bands as before, $0.26 |
| Production image | Docker build, container started against the real database, `/health`, `smoke_http.py` | healthy in 15 s, all checks pass |
| Render | `smoke_http.py` against https://jobrun-api.onrender.com with the Netlify origin | all checks pass; `answer_images: assessed` |
| Web app | `tsc --noEmit`, 33 unit tests, `next build` | clean, pass, builds |
| Deploys | push → Render (API) and Netlify (practice site) | both automatic, live within a minute |
| Database access rules | columns the browser may read on `attempt`, `attempt_submission`, `user_skill_profile`; `question` closed | `engine_state` (suggestion, follow-up internals) and `follow_up_turns` are not browser-readable; questions only through the API |
| Database indexes | `attempt(user_id, started_at desc)`, `(user_id, question_id)`, `(question_id, band)`, usage and metrics indexes | present; the new progress queries use them |
| Performance | `scripts/profile_service.py --cpu`: 200 full loops in memory | 39 ms per loop; the extra suggestion/subject queries are a small share |
| Real usage so far | `usage_event`: 35 model calls over two days, $0.60, average 9 s per call; 18 attempts by 3 users | matches the cost model (≈ $0.05 per answer cold) |

### 1a. Live suite

Harel's run of the whole suite on 20 September: **16 passed in 14 m 34 s**. From Shaked's machine the picture is: every test passes when run alone or in small groups (the two "every question" blocks that failed inside full runs passed together in 6 m 36 s on 21 September, and block 1 alone in 4 m 47 s), but in three full runs those same two blocks failed with connection drops mid-statement while the other fourteen tests passed. No assertion about the product ever failed. The likely cause is an interaction between the first test module and the connection pool on Windows over a slow link; it does not affect the deployed API (Linux, same region as the database). Left as an engineering item (§4.13): run the live suite in CI from the Render region.

## 2. Found and fixed today

1. **A strong follow-up erased a partial main answer.** The next-question logic received only the band of the answer just scored, so after a partial main answer and a strong follow-up it "advanced" to a new skill instead of consolidating. Found by the real-model run. Now the main answer's band and every follow-up band decide together. Test added.
2. **Hebrew hint follow-up pasted the whole question again.** The generator model (Sonnet) sometimes returns the original prompt plus the hint. Such a reply is replaced by the short "take another look with this in mind: …" template; flag `hint_restated_prompt`. Test added.
3. **A lost follow-up response could not be resent.** The follow-up send button was disabled whenever an unresolved pending answer existed. It now stays active in resend mode, and a follow-up whose evaluation is running or failed says so.
4. Earlier today, from the independent review of the overnight build: a sandbox escape through `operator.attrgetter` (closed), the code-test child inheriting the API's environment (now a minimal environment), and prompt injection through code-test results (now neutralised). `httpx` moved to runtime dependencies after the Render build failed.

## 3. Observations from the real-model run (not bugs, decisions for the founders)

- **Evidence weight.** In deep mode with no hints, the majority and count-bits answers were still marked `evidence: reduced`, because those questions carry `exposure_risk: high` (classic interview questions). That is by design (`params.py`), but it means a candidate who genuinely knows a classic question earns less credit for it. Decide whether "high exposure" should reduce evidence in the pilot or only in the B2B reports.
- **Follow-up kind.** After a WEAK answer the controller re-asks the same question with a hint (action HINT). The English wording from Sonnet was good ("Let's go back to the three sensors…"); the Hebrew one needed the fix above. Consider asking the generator for a *narrower* question on the missed point instead of a re-ask when the main answer was weak but not empty.
- **Judgement quality held.** The 13 review answers still band correctly after the prompt changes; misconception keys stayed precise; the circuit-only answer was judged PARTIAL with a correct reason ("no written expression or XOR explanation"), which is fair.
- **Cost.** A full deep attempt (main + one follow-up + card + tip + follow-up wording) costs about $0.05 to $0.08 on the current mix. 300 attempts a month per heavy user is $15 to $24.

## 4. Suggestions for improvement, in priority order

### Before inviting more testers

1. **Review and publish the first ten questions.** Everything is still `in_review` and served only because `ALLOW_IN_REVIEW_CONTENT=true`. Checklist in `backend/seeds/questions/README.md`. Then set `ALLOW_IN_REVIEW_CONTENT=false` and `ENV=production` on Render.
2. **Golden set → two decisions.** Run the reviewed founder answers through both judges and decide (a) whether Sonnet 5 can be the evaluator (roughly halves the cost again) and (b) the quick/deep evidence weights and the exposure-risk reduction above. `scripts/p2_review_set.py` is the fixture to extend.
3. **Render Starter plan.** The free instance sleeps after 15 minutes; the first request of a session waits about 40 seconds and the UI shows "could not reach the server". This is the most visible defect a new tester will hit.
4. **Bank coverage.** 14 of the role's 27 skills have a primary question. The focused next question is only as good as the bank: a struggle on a skill with no other question falls back to the grade-based choice. The missing skills are listed in `STATUS.md` §6 (latches/flip-flops, state tables, Moore vs Mealy, number representation, reset strategies, sequential HDL, debugging, testbench basics…).
5. **Monitoring and a daily cost line.** There is no error tracking or alerting on Render. Add a log drain or Sentry for the API, and a daily query on `usage_event` (calls, dollars, average latency, failures) posted somewhere both founders see. The data is already there.

### Product

6. **Hebrew skill names.** Subject names are translated in the app, but the 41 skill labels exist only in English (`seeds/skills/digital_hardware.json`), so the progress page and the next-question reason mix languages in Hebrew. Add `label_he` to the skill seed and serve it.
7. **Code questions should open in Python.** The bank's software questions have no `code_language`, so the editor defaults to plain text and the fence is tagged `text`; the code test still finds Python, but a Python-tagged editor with syntax highlighting is a better experience. Set `code_language` on the seven questions with code tests.
8. **Follow-up that narrows instead of re-asking** (see §3). Also consider letting a strong answer skip straight to the next question with a one-line "nothing to add" instead of no follow-up and no message.
9. **Progress page: a recommended subject.** The plan router already computes "what to practise next across days" with a reason; surface it above the donuts as one sentence and a button.
10. **Visual answers.** Circuits are assessed for one-bit combinational logic; sequential circuits and buses are described but not derived. If the pilot's hardware questions use flip-flops and counters, the truth-table check will not confirm those drawings; the model still reads the netlist. Photos: no per-user quota or cleanup of detached images yet (Harel's note); add both before a broad pilot.
11. **Code tests beyond Python.** Candidates who write C (common in hardware roles) get `passed: null` and model-only review. A C runner needs a compiler in the image and stronger isolation; JavaScript would need Node in the image. Decide by looking at what the first testers actually write.

### Engineering

12. **Run the test suites in CI.** Harel's GitHub Actions deploy the sites; add a job that runs the backend offline suite and the web tests on every push, and the live suite nightly (it takes 15 minutes and needs the database secret as an Actions secret).
13. **Live suite speed.** 15 minutes is mostly round trips to the pooler from Israel. Running it inside the Render region, or against a Supabase branch, would cut it to a few minutes.
14. **Sandbox hardening, second layer.** The AST audit plus restricted builtins are sound against the known escapes, but a runtime read primitive remains (`str.format` attribute access). Running the child under an OS sandbox (seccomp/bubblewrap on Linux, or a separate minimal container) would make the audit a convenience rather than the last line of defence. Worth doing before candidates outside the founders' circle submit code.
15. **Secrets hygiene.** The Anthropic key was pasted into a chat once and rotated; the service-role key now lives in Render and a local `.env`. Put a reminder in the runbook to rotate both when the pilot ends, and set a monthly spend limit on the Anthropic workspace if not already set.
16. **Question versioning.** Reloading content upserts by key and keeps ids; attempts store `question_version`, but the app does not yet show a candidate that a question changed since they answered it. Fine for now; note it before editing published questions.

## 5. Scripts added for this pass

- `backend/scripts/e2e_real_flow.py` — the new flow on the real model without database writes (about $0.15).
- `backend/scripts/p2_review_set.py` — the 13-answer judging check (about $0.26); rerun after any prompt or model change.
