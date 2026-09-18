# Backend review for Shaked

- Date: 18 September 2026
- Reviewed code: `57ed764` on `master`
- Companion document: [Backend/frontend integration readiness](backend-frontend-integration-readiness.md)

## Purpose and decision ownership

This records the findings discussed with Harel after reviewing the backend and its connection to the existing practice UI. It is a review of the current POC, not a claim that it is already a production service.

**The proposed fixes are suggestions, not the only correct implementations. Shaked owns the backend design and should decide how to address each finding.** Preserve the intended behavior and verify the acceptance criteria; feel free to use a different state model, persistence strategy, or API design. Discuss product-policy changes with Harel.

No engine code, database records, permissions, or deployed applications were changed during this review. The reproduction scripts used simulated model responses, not paid API requests. The seed-loader risk was established by reading the update logic; it was not tested by modifying the live database.

## What is already strong

- The model evaluates and phrases content, while ordinary Python controls progression and routing.
- Deterministic checks can constrain model evaluations, particularly valuable for digital hardware questions.
- Hint usage, answer exposure, familiarity, and evidence quality influence scoring.
- Provider interfaces and offline tests make the engine easier to inspect and change.
- Enrichment keeps the original bilingual question keys and frontend assets rather than creating an unrelated bank.

The existing suite passed **328 tests** during the preceding review. Those tests primarily verify engine behavior with controlled inputs. They do not establish real-model grading quality, deployed API behavior, or database persistence correctness. The additional reproductions below exposed cases that the existing passing tests did not cover. They were review probes, not committed regression tests.

## Priority overview

| ID | Finding | Evidence | Suggested timing |
| --- | --- | --- | --- |
| R1 | Repeated submission updates skill state repeatedly | Reproduced offline | Before exposing submission through the API |
| R2 | Main-answer persistence and failed follow-up recovery are incomplete | Code trace and offline reproduction | Before end-to-end persistence |
| R3 | Reveal after evaluation failure can receive positive evidence on resubmission | Reproduced offline | Before progress scores are trusted |
| R4 | AI-polished tips are missing from usage accounting | Reproduced offline | Before paid pilot usage and quotas |
| R5 | Re-import can overwrite question publication/review metadata | Static inspection | Before re-running seeds against reviewed content |
| R6 | Current frontend hint retrieval also exposes the solution | Static inspection | Before using the UI for measured assessment |

## R1. Make submission and scoring idempotent

**Location:** [`PracticeAttempt.submit`](../backend/app/engine/practice.py), starting at line 147 in the reviewed commit.

`submit()` sets `self.submitted = True` but does not reject or deduplicate another submission. A second call performs another evaluation and updates the same skill states again.

Reproduction used `example-mod-six-counter`, quick mode, one `PracticeAttempt`, shared skill states, and two identical scripted evaluations (`correctness=0.9`, `depth=0.8`). Submitting the same answer twice produced:

| Observation | After first submission | After repeated submission |
| --- | --- | --- |
| Primary-skill turn count | 1 | 2 |
| Internal knowledge score | 41.03 | 48.56 |

These are internal engine scores, not calibrated percentages of job readiness. The issue is the duplicate update, not the particular numbers. This is an engine-level reproduction; there is no deployed submission API yet.

**Suggested solution:** Give every accepted answer revision a persistent identifier and an idempotency key scoped to its user and attempt. Replaying the same submission should return its existing result or pending status. Use a database uniqueness constraint and a transaction/version check to protect scoring across concurrent requests and multiple server processes. An in-memory guard alone would not provide that protection.

Separate a deliberate new learning attempt from a transport retry. If the same key arrives with a different answer, reject it as a conflict rather than silently reusing the old result. Avoid holding a database transaction open during the model call; claim the work first and atomically finalize the result later. Exactly-once score application is the goal; a process failure may still make an external model call's billing outcome uncertain.

**Acceptance criteria:** Sequential retries and simultaneous duplicate requests produce one accepted answer revision, one application of its metrics, and one skill-state update. A deliberate new attempt remains possible under the agreed familiarity policy.

## R2. Preserve answers and recover failed evaluations

**Locations:** [`attempt_row()` and `submit_follow_up()`](../backend/app/engine/practice.py), [`cli_practice.py`](../backend/scripts/cli_practice.py), and [`LocalStore.record_attempt()`](../backend/app/services/local_store.py).

Two related gaps exist:

1. `attempt_row()` does not include the main submitted answer. The CLI persists that row without adding the answer elsewhere in the stored attempt. A submitted test string was absent from the serialized record. The existing `public.attempt` table already has an `answer` JSONB column; the caller/engine contract needs to populate it. The method describes only the fields owned by the engine, so this can be fixed at the caller boundary rather than necessarily inside that method.
2. If follow-up evaluation fails, `submit_follow_up()` clears `_pending_follow_up` before the answer is added to `follow_up_turns`. The outcome says `saved_without_evaluation`, but the answer is absent from the attempt record. A second submission raises `there is no follow-up question to answer`.

Reproduction for the second case: submit `alarm = A ^ B ^ C` for `example-sensor-majority`, let the scripted evaluation generate a follow-up, and make its evaluator raise a non-retryable `LLMError`. Check the saved turn and retry that same follow-up.

**Suggested solution:** Persist the original answer and its question/turn identity before invoking the model. Track evaluation state separately from answer submission. For example, use pending, evaluating, succeeded, and failed states, with a bounded retry path that reuses the saved answer. Keep enough durable attempt state to reconstruct the pending follow-up after a server restart. Store the user-visible feedback as well if the UI must recover it without generating a potentially different response.

Shaked should decide whether follow-up submissions live in separate rows or versioned JSON. Either approach must preserve the answer, its prompt/version, status, and ownership. This does not require inventing a second main-answer column.

**Acceptance criteria:** Main and follow-up answers survive evaluation failure and reload. Retrying evaluates the same saved answer without a second score update. The UI can distinguish “answer saved; feedback unavailable” from “answer was not saved.”

## R3. Bind exposure evidence to the actual answer revision

**Locations:** [`reveal_reference()`, `submit()`, and evidence weighting](../backend/app/engine/practice.py).

Reproduction:

1. Submit an answer and simulate an evaluator error.
2. Reveal the reference solution.
3. Submit the revealed solution as a new answer on the same attempt.

Because `submitted` was already set, revealing the reference does not set `revealed_before_submit`. The retry received an evidence weight of **0.3** in the quick-mode test instead of zero for a newly submitted answer copied after exposure.

**Suggested solution:** Record exposure events and answer revisions on the server. Evaluate evidence using the exposure state when that specific answer was accepted. Retrying the evaluation of an immutable answer submitted before exposure is different from accepting a revised answer after exposure.

Shaked and Harel should choose whether answer edits after submission create a new revision, a fresh learning attempt, or are disallowed within that attempt. Do not solve this by simply zeroing every evaluation that finishes after a reveal: that could unfairly penalize a valid answer submitted before the reveal.

**Acceptance criteria:** Failure followed by reveal and a new answer cannot gain independent-skill credit. Retrying the unchanged, pre-exposure answer follows the agreed policy. Concurrent reveal/submission requests have an unambiguous server-side order.

## R4. Account for the tip-generation call

**Locations:** [`PracticeAttempt._tip()`](../backend/app/engine/practice.py) and [`tips.compose()`](../backend/app/engine/tips.py).

With `polish_tips=True`, `tips.compose()` calls the provider and returns only text. Its usage metadata does not reach `PracticeOutcome.usage`, even though `_tip()` receives that collection.

A metered fake provider assigned 100 input and 100 output tokens to each response. A wrong majority-gate answer triggered four roles: evaluator, generator, feedback, and tip. Only three usage events were returned: **800 simulated tokens consumed versus 600 recorded**. This is a test measurement, not a real provider bill.

**Suggested solution:** Either return a structured tip result containing text, model, usage, and latency, or centralize metering in a provider wrapper used by all model calls. The latter can also record retries and malformed/refused responses when the provider supplies usage data. Keep internal billing detail separate from safe client error messages.

Also check the existing price lookup when selecting a model: an unrecognized model ID currently receives a zero-price fallback. Treat unavailable pricing as unknown, rather than free, and reconcile estimates against provider billing.

**Acceptance criteria:** Every successful model response with usage data has a corresponding usage event, including tips. Template-only tips create no model event. Tests cover fallback behavior and prevent duplicate accounting during request replay.

## R5. Define ownership of publication and review metadata

**Location:** [`seed_db.py`](../backend/scripts/seed_db.py), generic `upsert()` and the question row construction around lines 152–170.

The generic upsert updates all supplied non-key columns. The question payload includes `status`, `reviewed_by`, `reviewed_at`, and `review_notes`. Current seed questions are `in_review`; loading an older seed after human approval in the database can overwrite that approval and publication state.

**Suggested alternatives for Shaked to choose from:**

- Make database review metadata authoritative and preserve it on a content-identical re-import; changed content should require a new review.
- Make versioned seed files authoritative, but require explicit reviewed metadata and a deliberate publish operation.
- Import content into a new draft revision and promote it only after review.

Preserving a `published` flag while silently changing the approved answer or rubric would also be incorrect. Treat review approval as belonging to a specific content revision. A dry-run diff would make imports easier to review.

**Acceptance criteria:** Re-importing unchanged seeds does not erase approval. Changing reviewed content follows an explicit re-review/version policy. Verify this against a disposable database or rolled-back transaction, not production data.

## R6. Change how the frontend accesses hints and solutions

**Location:** [`apps/web/src/app/page.tsx`](../apps/web/src/app/page.tsx), `reveal()` around line 549; question-read policies in the `jr_*` migrations.

The current UI selects both `hints` and `reference_solution` even when the user requests only a hint. It also joins the available hints into one displayed string. Hiding the solution visually does not prevent it from reaching the browser.

This was sufficient for the original learning prototype. For evidence-based assessment, it bypasses the engine's incremental hint and exposure accounting. The current access is for allowlisted pilot members, not exclusively founders; the corresponding statement in `backend/STATUS.md` should be corrected during integration.

**Suggested solution:** Add authenticated, attempt-scoped operations for the next hint and reference reveal. Return only the requested content and persist exposure in the same operation. Remove ordinary learner access to answer-bearing fields through the old direct database path, including translations and any answer-bearing metadata. Merely changing the frontend query is insufficient if learners can still query the full row themselves. Keep any reviewer access explicit and separate.

**Acceptance criteria:** A normal learner cannot retrieve a reference solution through the question-list/detail or direct database APIs before a reveal. A next-hint request returns only the intended hint; replay does not advance twice. Hebrew and English share the same attempt exposure state.

## Other points to retain in the implementation plan

- The backend currently exposes health and catalog-summary routes only. Missing practice routes, authentication middleware, durable practice state, and frontend wiring are planned work, not regressions in an already implemented API.
- All 30 enriched questions are still `in_review`, and primary questions cover 14 of the role's 27 skills. Avoid presenting missing evidence as low ability. Human review and expanded coverage remain product work; 150 reviewed questions is a separate milestone.
- Secondary skills currently receive weighted evidence from the same overall evaluation. Consider whether this is precise enough for skill-specific feedback; this is a calibration/product decision, not a reproduced crash.
- Real-provider evaluation quality, latency, and cost still need a bounded trial. Evaluate correct alternative solutions, partial answers, misconceptions, Hebrew/English parity, irrelevant answers, and instructions embedded in candidate text. Escaping a delimiter alone is not proof of prompt-injection resistance.
- Thresholds and priors marked as assumptions should be calibrated against expert-reviewed examples. Keep model, prompt, question, and engine versions so disagreements can be investigated.

## Suggested resolution order

1. Agree on submission, revision, exposure, and retry semantics together (R1–R3).
2. Implement and test durable persistence and authenticated practice endpoints.
3. Close the direct solution-access path while wiring the frontend (R6).
4. Complete usage accounting before the paid model trial (R4).
5. Set the content import/review policy before loading or reloading the enriched bank (R5).
6. Run the complete browser-to-database flow and review real feedback with an interviewer.

Shaked can reorder independent work or choose different implementations. The behavioral checks above are intended to make those decisions reviewable, not to impose an architecture.
