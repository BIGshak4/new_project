# Practice pilot integration handoff

Date: 19 September 2026. Owners: Harel and Shaked.

## What is connected

- Practice site: https://jobrun-practice.netlify.app
- API: https://jobrun-api.onrender.com (FastAPI on Render, database-backed storage).
- Supabase supplies authentication, persistent attempts/evaluations, skill profiles and private personal notes.
- Founder board: https://jobrun-tasks.netlify.app. Its implementation is unchanged; both personal founders have board membership.

The existing bilingual visual design now supports quick/deep practice, confidence before an attempt, ordered hints, reference exposure, written submissions, feedback cards, checks, follow-ups, retrying failed evaluations, history, progress and JSON export for expert review. The attempt ID stays in the URL, and browser refresh reads its persisted state. Starting a new attempt is explicit and counts toward the server's daily quota.

The frontend never evaluates an answer itself. Model feedback and skill metrics are marked **simulated** while `/health` reports the scripted provider. No AI provider key was added. The default scripted feedback can be English even in a Hebrew attempt; it is a flow-testing fixture, not the final multilingual tutor.

## Data and exposure boundaries

Question browsing now goes through the safe API. The browser cannot read hidden solutions, rubrics, all hints, or generated follow-up answer outlines directly from the database. Applied migration `20260919093403_restrict_practice_question_reads.sql` removes browser table/column access to `question` and `question_translation` and removes the `attempt.follow_up_turns` column grant. Backend access remains intact. This file matches the live migration timestamp. Two earlier migrations (`skill_profile_engine_state` and `client_read_grants`) already have different local/live timestamps; reconcile their history before a future CLI database push rather than applying them twice.

Bookmarks, optional saved drafts and self-ratings remain in `jr_practice_entries`, protected by row ownership and optimistic versions. A late library refresh cannot overwrite a newer bookmark response. These personal notes do not change the engine's skill assessment.

Before sending, the UI stores the answer and its idempotency key in session storage. It checks the server after ambiguous failures and reuses that key if resending is necessary. Refresh never creates another attempt. Local drafts require the same tab/browser session; use account draft saving or submit for cross-device persistence.

## Verification

- Backend offline suite: **516 passed, 16 skipped**. Skipped tests need a direct database connection and were not represented as passing.
- Frontend suite: **9 passed**, covering authenticated requests, absent-session handling, 202 evaluation state, request errors, no automatic duplicate POST, follow-up routing, pending-answer reconciliation and stale bookmark snapshots.
- Next.js production build and TypeScript checks passed.
- Live HTTP checks used disposable accounts: real sign-in, 30 questions in each language, safe question payload, persisted feedback, idempotent replay, progress/history, production CORS, anonymous rejection and cross-user attempt denial.
- Browser checks exercised Hebrew practice, draft recovery after refresh, one-at-a-time hints, feedback, a follow-up answer, reference reveal and language switching. Desktop and 390px layouts were inspected.
- After the migration, both QA accounts received 403 for direct solution, hint and internal follow-up reads. Safe API browsing still returned 30 questions; personal notes updated successfully; other users' notes and founder-board data were invisible to learner accounts. Database grants were checked directly too.

These checks validate integration and persistence. They do **not** establish the educational accuracy of scripted feedback or the quality of a real model. Temporary QA identities and their practice records are removed after verification; founder attempts are not used as test fixtures.

## Founder test session

1. Confirm your personal email, then sign in to the practice site. Harel's confirmation was verified; Shaked's was pending. Use the separate founder board URL for tasks.
2. Start one quick and one deep attempt. Check the Hebrew/English prompt, requirements, confidence selector and code layout.
3. Type an answer, refresh, and verify recovery. Submit it once; confirm the saved answer, feedback and history. Reopen that same attempt instead of starting another one.
4. On another question, request a hint before answering. On a third, reveal the reference before answering. Confirm exposure is retained after reload and the evidence label changes appropriately.
5. Answer a follow-up. Switch language, revisit history, save a bookmark and verify it remains after reload.
6. Check that the two personal accounts have separate practice histories. Both should have founder-board access.
7. Export an attempt for review. Record the question key, attempt ID, expected behavior, actual behavior and a screenshot for any issue. Do not include passwords or tokens.

## Enabling real feedback later

Shaked should configure the chosen provider on Render. The current implementation supports `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` and `LLM_PROVIDER=anthropic`; verify the model configured at that time is available to the business account. Keep provider and database credentials server-side. Configure a provider spending cap and keep the backend usage limits active.

Before switching, decide how to separate or reset **scripted practice metrics** so they cannot be mistaken for real learning evidence. Do not delete founder data indiscriminately. Re-run the same flow with the real model, exercise timeout/retry behavior, and have a hardware expert review correct, partially correct, incorrect and ambiguous answers in both languages. Only then use the feedback quality to judge pilot readiness. `ENV=production` intentionally refuses scripted/manual providers.

Custom SMTP is still needed before a broader external pilot. Supabase's advisor also reports disabled leaked-password protection; see [password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection). RLS-enabled question/catalog tables without browser policies are intentionally closed, not missing public access.

## Deployment and rollback

Deploy `apps/web` with its existing Netlify project and `NEXT_PUBLIC_API_BASE_URL` configured for the production build. Stop a local development server before Netlify's Windows adapter moves build output. Deploy the API-based frontend first, then apply the database migration. No paid plan change is needed for this integration.

The old frontend depends on direct question-table reads, so rolling back only the frontend after this migration will break browsing. Prefer fixing/redeploying the integrated frontend. Any deliberate rollback of the exposure restriction needs a reviewed database change as well. Git push currently does not automatically redeploy the Netlify sites.
