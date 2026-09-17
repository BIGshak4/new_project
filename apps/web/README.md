# JobRun Practice

Private bilingual interview practice, deployed at https://jobrun-practice.netlify.app.

Node.js 24, Next.js App Router, React, TypeScript and Supabase. Copy `.env.example` to `.env.local`, run `npm ci`, then `npm run dev`. `npm run build` includes TypeScript validation.

The root page includes authentication, the question library, personal written practice, hints and reference solutions. `GET /api/health` checks only the application runtime; it is not a database or AI health check.

The pilot contains 30 questions marked `in_review`, visible only to allowlisted participants. Self-assessment is explicitly distinguished from AI evaluation. No AI provider is wired to this application yet.

Deployment, auth, founder access and limitations: [operations guide](../../docs/netlify-and-supabase.md).

`vercel.json` is a retained earlier bootstrap option. The active hosting target is Netlify; it uses this directory's `netlify.toml` and the Next.js adapter.
