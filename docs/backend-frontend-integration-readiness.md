# Backend/frontend integration readiness

- Date: 18 September 2026
- Repository baseline: `57ed764`
- For: Shaked and Harel
- Related review: [Backend findings and suggested fixes](backend-review-for-shaked.md)

## Goal and ownership

Deliver one durable flow: **sign in → open a question → submit an answer → receive AI feedback → save progress → reload and recover the same result**.

This is a proposed implementation checklist, not a completed integration. Shaked owns backend implementation choices; Harel and Shaked should agree on product behavior and the API contract. The hosting, endpoint names, and persistence suggestions below are not the only valid approach.

Frontend work can start against an agreed mock contract before hosting and billing are ready. The launch checks at the end must pass before inviting a broader pilot to rely on AI scores.

## 1. Current state

| Component | Repository state | Integration work remaining |
| --- | --- | --- |
| Practice UI, `apps/web` | Next.js app; Supabase login; question browsing; answer/self-rating saves; direct hint/solution reads | Call the new practice API; render feedback and evaluation states |
| Task board, `apps/tasks` | Separate founder app using `jr_*` tables and private files | Keep working independently; no AI-engine migration needed |
| Python engine, `backend` | Evaluation, deterministic checks, routing, practice, plans, provider abstraction, offline tests | Address review findings and wrap the engine in authenticated, durable API operations |
| FastAPI | `/health` and `/catalog/summary` | Practice, recovery, feedback/history, and progress endpoints |
| Supabase | Shared Auth/database plus canonical product tables and `jr_*` prototype tables | Verify live schema, map users/data, load reviewed enrichment, revise access boundaries |
| AI provider | Anthropic adapter and manual/scripted providers | Company API access, billing, secret configuration, real-provider trial |
| Hosting | Two Netlify frontend projects, documented as manually deployed | Choose and deploy the Python service; configure frontend API access |

The backend status document says enriched seed content has not been loaded. This checklist does not claim a fresh inspection of deployed secrets or live schema. Verify that state before implementing changes. See [deployment/access notes](netlify-and-supabase.md), [backend status](../backend/STATUS.md), and [backend settings](../backend/app/config.py).

## 2. Accounts, services, and what actually needs payment

| Service | Needed for the first connected flow? | Action |
| --- | --- | --- |
| Existing Supabase project | Yes | Reuse it; obtain the backend connection securely and verify Auth/permissions |
| Existing Netlify projects | Yes for the current deployed frontends | Reuse both projects; configure the practice API URL when implemented |
| Model-provider API | Yes for real automated feedback; no for mock development | Create company-controlled API access and enable billing/credits as required |
| Python backend host | Yes for a public connected pilot | Select a host and a plan that supports the chosen latency and availability requirements |
| Custom SMTP | Before inviting users beyond the default Auth mail service's limitations | Configure a provider such as Resend and verify a sender domain |
| Custom website domain | Optional for first integration | Existing hosting domains can be used initially |
| Redis, vector database, dedicated queue service | Not prerequisites for the first flow | Add only if the chosen architecture needs them; durable work tracking can start in Postgres |

No new Vercel account, separate task-board database, or multiple model subscriptions are required just to connect this implementation. This document authorizes no purchases and provisions no resources.

### Model API: recommended first step

Start the controlled evaluation with **Anthropic**, because that adapter already exists. The configured baseline is `claude-opus-5`; keep it configurable and verify that the exact model and structured-output options work in the company's account. This is a compatibility-first recommendation, not a conclusion that it is the best-value model. Compare a less expensive supported model only after establishing an expert-reviewed quality baseline. Official references: [current model catalog](https://platform.claude.com/docs/en/models/overview) and [API quickstart](https://platform.claude.com/docs/en/get-started).

1. Use a company-controlled Claude Console workspace/account and invite the founders through supported access controls.
2. Enable API billing or credits as required by that account. Claude app subscriptions and API usage are billed separately; buying a chat subscription is not the API setup step. See [Anthropic's billing explanation](https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-do-i-have-to-pay-separately-to-use-the-claude-api-and-console).
3. Create a dedicated project key. Put it in a secret manager or the backend host's secret configuration; use an ignored local `.env` for development. Do not paste it into Markdown, Git, task comments, or browser configuration. See [API authentication](https://platform.claude.com/docs/en/manage-claude/authentication).
4. Agree on a small trial budget. Configure available provider spending controls and application-side per-user/concurrency limits. Verify whether a dashboard setting is a hard stop or only an alert.
5. Run a small explicit real-API smoke test covering evaluator structured output, feedback, generated follow-up, tip, Hebrew, and English. Exercise the configured fallback option rather than assuming it works.
6. Record actual latency, tokens, returned model ID, failures, and estimated cost. Fix the tip-metering gap before using these figures for quotas or pricing.

Using another provider is valid, but requires its own adapter and compatibility tests. No provider API credentials are needed to begin contract and UI development with scripted responses.

## 3. Decide where the Python backend runs

Suggested initial topology:

```text
Browser: apps/web on Netlify
  ├─ Supabase Auth: sign-in and access-token refresh
  └─ HTTPS + access token → hosted FastAPI service
                             ├─ Supabase Postgres: durable attempts/progress
                             └─ Model API: evaluate and generate feedback

Browser: apps/tasks on Netlify → existing Supabase task-board services
```

For a straightforward managed Python service, **Render is one reasonable option**. It has a documented FastAPI deployment path. Shaked may choose another Python-capable host; there is no need to move the existing frontends merely to host the backend. Review current plan limits, cold starts, region, and request timeouts before purchasing. [Render's FastAPI deployment guide](https://render.com/docs/deploy-fastapi).

- Use `backend` as the service root and `app.main:app` as the ASGI entry point.
- Use a compatible Python runtime, initially 3.12, and install from `pyproject.toml`/`uv.lock`. Avoid the unrelated root-level placeholder `requirements.txt`.
- If the deployment image provides `uv`, a proposed build command is `uv sync --frozen --no-dev`; a proposed Linux start command is `uv run --frozen --no-dev uvicorn app.main:app --host 0.0.0.0 --port "$PORT"`. Confirm those commands in the chosen image; they have not been deployed as part of this review.
- Configure HTTPS, explicit frontend origins, request limits, logs, and readiness checks. The existing `/health` only reports configuration; `database_configured=true` is not proof of database connectivity. A health probe must not make a paid model call.
- Prefer a service region close to the existing Frankfurt database where practical. Verify the selected connection method and network reachability.
- Give the host access to the repository through an authorized owner/admin. Repository access was previously a deployment blocker; verify it rather than assuming a Git push auto-deploys either app.

A direct browser-to-FastAPI call is a reasonable first choice. A Next.js server proxy is an alternative, but introduces another timeout boundary. Full WebSockets are not required for the first text flow. Ordinary HTTP plus status polling can recover long evaluations and page reloads. If using background processing, work must be durable across process restarts; an in-memory fire-and-forget task alone is insufficient.

## 4. Configuration inventory

**Already recognized by backend settings:**

| Variable | Purpose | Visibility |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy/asyncpg connection to the selected Supabase database | Backend secret only |
| `LLM_PROVIDER` | `manual` locally or `anthropic` for real API calls | Backend configuration |
| `ANTHROPIC_API_KEY` | Model API authentication | Backend secret only |
| `ANTHROPIC_MODEL` | Tested model ID; currently defaults to `claude-opus-5` | Backend configuration |
| `ANTHROPIC_ENABLE_FALLBACKS` | Existing provider option; verify with real calls | Backend configuration |
| `ALLOW_IN_REVIEW_CONTENT` | Development content allowance; keep false for ordinary production serving | Backend configuration |
| `DEFAULT_LANGUAGE` | Default content language | Backend configuration |

The frontend already uses `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`. These are public client configuration, not privileged server credentials.

**Proposed additions, not implemented settings:** a frontend API base URL (for example `NEXT_PUBLIC_API_BASE_URL`), backend Supabase issuer/audience verification configuration, an allowed-origin list, request/model timeouts, per-user usage limits, and environment identifiers. Agree on exact names and add validated settings plus `.env.example` entries while implementing. A JWKS URL is appropriate when the project's signing-key configuration supports it; do not assume every project uses the same key type.

A Supabase database password, model API key, or secret/service-role key must never use a `NEXT_PUBLIC_` variable. A database connection string and a Supabase API key are different credentials; the current SQLAlchemy path needs the former. Select direct/session/transaction pooling intentionally and test asyncpg compatibility and connection limits. [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).

## 5. Authenticate users and preserve the access boundaries

- Verify the Supabase access token on the backend, including its signature, issuer, audience, and expiry using a supported verification method appropriate to the project's signing keys. Decoding a token without verifying it is not authentication. [Supabase JWT guide](https://supabase.com/docs/guides/auth/jwts).
- Derive the user identity from that verified token. Do not accept client-supplied user IDs as authority to read/write attempts.
- Enforce pilot membership and attempt ownership server-side. Founder task-management permission must remain distinct from learner access.
- Check how `auth.users` maps to `public.user_profile`; ensure registration/first use creates required profile records once and does not assign founder rights. Existing prototype users must be supported.
- Privileged database connections can bypass RLS. Apply explicit ownership checks even if the browser's Supabase reads are protected by RLS. Restrict runtime database permissions where practical.
- Restrict CORS to approved frontend origins if using direct calls. Authentication remains required even for requests that do not come from browsers.
- Make question-list/detail responses safe by construction: no reference solutions, hidden expected answers, correct-choice indices, or complete future-hint arrays. Close the old direct learner access path described in review R6.
- Test expired tokens, unapproved accounts, cross-user attempt IDs, anonymous requests, and attempted learner access to the task board.

## 6. Agree on a minimal API contract

The following routes are **proposals; none is claimed to exist today**. Shaked can rename or combine them while preserving the behavior.

| Proposed operation | Required behavior |
| --- | --- |
| `GET /v1/questions` and `GET /v1/questions/{id}` | Safe catalog/prompt, language selection, stable IDs, publication/access filtering |
| `POST /v1/practice/attempts` | Start an owned attempt from a question/version, language, and mode; return a stable attempt ID |
| `GET /v1/practice/attempts/{id}` | Recover saved answer, evaluation status, user-visible feedback, exposed hints, and pending follow-up |
| `POST /v1/practice/attempts/{id}/hints/next` | Reveal and record one hint; deduplicate replay |
| `POST /v1/practice/attempts/{id}/reference` | Record exposure and return the reference under the agreed policy |
| `POST /v1/practice/attempts/{id}/submissions` | Accept an immutable answer revision with an idempotency key; return a result or pending status |
| `POST /v1/practice/attempts/{id}/follow-ups/{turn_id}/submissions` | Accept a reply to a specific follow-up; reject stale or unrelated turn IDs |
| `GET /v1/me/progress` | Return durable professional-skill progress with evidence status, separate from self-ratings and engagement |

Agree on request/response schemas before wiring the UI. Include answer text/code shape, timestamps, language, question and prompt versions, feedback fields, and safe error codes. Suggested errors include unauthenticated, forbidden, conflict/stale revision, validation error, usage limit, and temporarily unavailable evaluation. Publish the agreed contract in FastAPI/OpenAPI and keep frontend types aligned.

For asynchronous evaluation, define pending/failed/retryable states and how the client polls. Reopening the page must retrieve the existing submission rather than trigger a new model request. A failed evaluation must never be presented as a zero-score answer.

## 7. Persistence, migrations, and content

- Decide which canonical tables own attempts, evaluation metrics, skill state/profile, usage events, and feedback. Existing candidates include `attempt`, `evaluation_metrics`, `user_skill_assessment`, `user_skill_profile`, and `usage_event`; inspect their schemas rather than treating engine dictionaries as insert-ready rows.
- Map stable question/skill keys to database UUIDs. Preserve question versions and the original answer. Determine where durable feedback, pending follow-up state, and submission idempotency fit; add focused migrations only where existing columns are insufficient.
- Keep `jr_practice_entries` self-ratings, bookmarks, and learning completion distinct from engine-generated assessments. Decide whether to retain it for those features or migrate them deliberately. Do not reinterpret historical self-ratings as AI evidence or overwrite multiple attempts with one mutable record.
- Persist answer acceptance before calling the model. Finalize evaluation, metrics, and skill-state updates atomically after success, with protection against concurrent attempts updating the same skill. Test recovery if the model succeeds but saving fails.
- Make database state, not process memory or CLI JSON, authoritative for hosted requests. Bound retained history and define what survives deletion/retry/restart.
- Verify migration history and live schema before changes. The locally untracked Supabase configuration and empty initial-schema placeholder were not included in this documentation commit; do not apply or publish them blindly.
- Address seed-import review ownership (R5), run `uv run python scripts/seed_db.py --check`, then load content using a controlled process. Confirm the existing 30 question IDs remain stable for frontend records.
- Decide whether runtime content comes from the database or versioned seed files. Existing engine catalog loading reads seeds; publishing a database row alone will not automatically change a seed-backed runtime catalog. Define the refresh/reload strategy.
- Review technical correctness, rubrics, hints, deterministic checks, and Hebrew/English parity before publication. For initial wiring, a small reviewed subset is enough; do not bulk-publish all 30 simply to satisfy filtering.
- Resolve the documented bilingual tip persistence gap if the hosted engine will read tips from the database. Keep missing skill coverage visible as “not assessed.”

## 8. Frontend changes and pilot email

- Replace the relevant direct question-help and assessment operations with the new authenticated API; preserve bookmarks/drafts according to the agreed data ownership.
- Add submitting, evaluating, saved-but-evaluation-failed, completed, and retry states. Disable duplicate clicks for usability while retaining server-side deduplication.
- Render feedback, deterministic-check outcomes, follow-up questions, and evidence-aware progress in both languages. Keep soft-skill feedback distinct from technical correctness.
- Restore the attempt after refresh and token renewal. Test language switching without resetting exposure history. Preserve unsent drafts on recoverable errors.
- Continue regression-checking the separate task board; it should not depend on the AI provider being available.

Before wider invitations, configure custom SMTP for Supabase Auth: the default mail service is restricted and is not a general production delivery solution. Resend is one possible SMTP provider, not a required vendor. Set up an owned, verified sender domain, then test confirmation and password-reset messages and redirect URLs for both apps. You do not need to buy a custom *website* domain just to wire the API, but a branded email sender needs an appropriate verified domain. [Supabase SMTP guidance](https://supabase.com/docs/guides/auth/auth-smtp).

## 9. Evaluation, costs, and observability

- Fix R1–R4 and add regression cases before trusting recorded progress and usage.
- Create a small expert-reviewed answer set with strong, partial, wrong, alternative-valid, and adversarial answers in Hebrew and English. Record expected score ranges and acceptable feedback; examine disagreements with an interviewer.
- Establish latency and failure targets suitable for the actual pilot; measure the complete multi-call attempt, not just one evaluator request.
- Add bounded retries/backoff, per-user limits, concurrency controls, and a graceful exhausted-budget response. Do not use the reviewer CLI's manual provider in a public deployment.
- Log request/attempt IDs, statuses, model/prompt/engine versions, latency, and usage. Keep credentials and raw candidate answers out of ordinary logs; use access-controlled stored attempts for expert review under an agreed retention policy.
- Meter every model call, distinguish estimates from provider billing, and review actual cost per completed attempt before selecting user quotas. More capable models and extra feedback/follow-up calls affect the economics.

These are launch-readiness checks, not a requirement to buy an observability platform or build a large queue system first.

## 10. Suggested sequence and acceptance gates

| Stage | Proposed owner | Completion evidence |
| --- | --- | --- |
| Contract and policies | Shaked + Harel | Answer revisions, exposure rules, routes, errors, persistence ownership agreed |
| Engine hardening and persistence | Shaked | R1–R5 addressed with regression tests; stored attempts survive failure/restart |
| Mock integration | Frontend implementer + Shaked | Browser flow works with scripted provider and real authenticated persistence |
| API account and hosting | Founders + Shaked | Backend deployed; secrets configured; paid model smoke test within agreed budget |
| Real feedback and content review | Both founders + interviewer | Reviewed question subset and real feedback meet agreed criteria |
| Pilot release | Both founders | End-to-end checks below pass, email works, rollback path documented |

Run these checks before calling the first connected release ready:

- [ ] Two personal accounts can sign in and see only their own attempts/progress.
- [ ] A reviewed question works in Hebrew and English.
- [ ] A correct, partial, and incorrect answer produce appropriate feedback reviewed by a person.
- [ ] Double-clicks, parallel requests, and network retries do not apply the same score twice.
- [ ] Main and follow-up answers survive provider outage and server restart.
- [ ] Reveal-before-new-answer behavior matches the exposure policy; hint reads do not leak solutions.
- [ ] Refresh restores the same answer, feedback, and pending follow-up without another paid call.
- [ ] Cross-user requests and direct solution-fetch bypasses are denied.
- [ ] Usage includes all applicable model calls and limits fail gracefully.
- [ ] Content imports preserve the chosen review/version policy and stable identifiers.
- [ ] Task-board access and files still work, including when the AI backend is unavailable.
- [ ] A failed backend release can be rolled back without losing accepted answers.

For the first release, defer voice/video, competitive matchmaking, full interview simulation UI, employer assessment workflows, and automated prompt promotion. Weekly-plan UI and streaming can follow once the core question-to-feedback flow is reliable.

## Decisions Shaked should return before implementation is split

1. Selected host and direct API versus frontend proxy.
2. API contract and synchronous versus durable asynchronous evaluation.
3. Answer/retry/exposure semantics and the chosen fixes for review findings.
4. Exact database mappings, required migrations, and runtime content source.
5. Model choice, bounded trial budget, and secret owners.
6. Reviewed initial question subset and the criteria for expanding the pilot.

Official service documentation above was checked on 18 September 2026. Recheck model access, prices, and hosting limits when purchasing; repository configuration is not evidence of a deployed, working integration.
