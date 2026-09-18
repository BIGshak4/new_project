# JobRun Practice

Private bilingual interview practice, deployed at https://jobrun-practice.netlify.app.

Node.js 24, Next.js App Router, React, TypeScript and Supabase. Copy `.env.example` to `.env.local`, run `npm ci`, then `npm run dev`. `npm run build` includes TypeScript validation.

The root page includes authentication, the question library, personal written practice, hints and reference solutions. `GET /api/health` checks only the application runtime; it is not a database or AI health check.

The pilot contains 30 questions marked `in_review`, visible only to allowlisted participants. Self-assessment is explicitly distinguished from AI evaluation.

AI evaluation comes from the practice API (`backend/`, deployed at https://jobrun-api.onrender.com, contract at `/docs`). `src/lib/practice-api.ts` is a typed client for it; set `NEXT_PUBLIC_API_BASE_URL` in `.env.local`. How to wire the practice page to it: [docs/practice-api-integration.md](../../docs/practice-api-integration.md). The backend's `tests/test_ts_client_contract.py` fails if the client's types drift from the API.

Deployment, auth, founder access and limitations: [operations guide](../../docs/netlify-and-supabase.md).

`vercel.json` is a retained earlier bootstrap option. The active hosting target is Netlify; it uses this directory's `netlify.toml` and the Next.js adapter.
