# JobRun Practice

Private bilingual interview practice, deployed at https://jobrun-practice.netlify.app.

Node.js 24, Next.js App Router, React, TypeScript and Supabase. Copy `.env.example` to `.env.local`, run `npm ci`, then `npm run dev`. `npm run build` includes TypeScript validation.

The root page includes authentication, the question library, personal written practice, hints and reference solutions. `GET /api/health` checks only the application runtime; it is not a database or AI health check.

The pilot contains 30 questions marked `in_review`, visible only to allowlisted participants. Self-assessment is explicitly distinguished from AI evaluation.

Practice is connected to the API (`backend/`, deployed at https://jobrun-api.onrender.com, contract at `/docs`). Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` and in the Netlify build environment. The API owns questions, attempts, hints, reference exposure, feedback, follow-ups and skill progress. Supabase Auth supplies the bearer token; only personal bookmarks, drafts and self-ratings use Supabase REST directly. The provider remains scripted until real AI credentials are configured on Render.

`npm test` checks the client contract, error handling, idempotency recovery and stale snapshot protection. `npm run typecheck` validates types. The backend's `tests/test_ts_client_contract.py` also fails if client response types drift from the API. See [API integration](../../docs/practice-api-integration.md) and [pilot handoff](../../docs/pilot-integration-handoff.md).

Deployment, auth, founder access and limitations: [operations guide](../../docs/netlify-and-supabase.md).

`vercel.json` is a retained earlier bootstrap option. The active hosting target is Netlify; it uses this directory's `netlify.toml` and the Next.js adapter.
