# JobRun Practice

Private bilingual interview practice, deployed at https://jobrun-practice.netlify.app.

Node.js 24, Next.js App Router, React, TypeScript and Supabase. Copy `.env.example` to `.env.local`, run `npm ci`, then `npm run dev`. `npm run build` includes TypeScript validation.

The root page includes authentication, the question library, personal written practice, hints and reference solutions. `GET /api/health` checks only the application runtime; it is not a database or AI health check.

The pilot contains 30 questions marked `in_review`, visible only to allowlisted participants. Self-assessment is explicitly distinguished from AI evaluation.

Practice is connected to the API (`backend/`, deployed at https://jobrun-api.onrender.com, contract at `/docs`). Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` and in the Netlify build environment. The API owns questions, attempts, hints, reference exposure, feedback, follow-ups and skill progress. Supabase Auth supplies the bearer token; only personal bookmarks, drafts and self-ratings use Supabase REST directly. The provider remains scripted until real AI credentials are configured on Render.

`npm test` checks the client contract, error handling, idempotency recovery and stale snapshot protection. `npm run typecheck` validates types. The backend's `tests/test_ts_client_contract.py` also fails if client response types drift from the API. See [API integration](../../docs/practice-api-integration.md) and [pilot handoff](../../docs/pilot-integration-handoff.md).

Deployment, auth, founder access and limitations: [operations guide](../../docs/netlify-and-supabase.md).

`vercel.json` is a retained earlier bootstrap option. The active hosting target is Netlify; it uses this directory's `netlify.toml` and the Next.js adapter.

## Private support reporting

The visible “Report a problem” launcher opens a bilingual, keyboard-accessible report dialog without navigating away from the current answer. Submitting requires a signed-in account. Reports use the idempotent `jr_submit_support_report` RPC; their private attachments use `jr_reserve_support_file`, the `jr-support-files` bucket and guarded `jr_remove_support_file` cleanup. Apply the admin/support database migration before deploying this feature.

Limits: 5 reports per user per day; up to 5 attachments per report, 5 MiB per file and 15 MiB per report. The database also enforces a 100 MiB attachment quota per user. Allowed formats are PNG, JPEG, WebP, PDF and UTF-8 plain text; extension, declared MIME and basic file signatures are checked before upload. No SVG, HTML or office-document uploads. Admins should download untrusted attachments rather than embed them.

Only known page routes and a bounded question ID are included as context. Passwords, access tokens, browser logs, full URLs and answer contents are never collected automatically. Report drafts stay in the current tab's memory, survive closing/reopening the dialog and are cleared when another account signs in. After a partial upload failure, retry uploads only; the report and successful files are retained without duplicates. Reports and status updates are handled in the private admin inbox.
