# JobRun

Interview preparation and a private founders' workspace, built with Next.js, TypeScript and Supabase.

| App | Source | Live pilot |
| --- | --- | --- |
| Practice | `apps/web` | https://jobrun-practice.netlify.app |
| Founder tasks | `apps/tasks` | https://jobrun-tasks.netlify.app |

Both apps require Supabase authentication and an approved email. Task access additionally requires founder permission. Practice includes 30 bilingual questions under review, written answers, hints, reference solutions, bookmarks and progress. AI evaluation is not connected yet.

The task board supports individual tasks, filters, assignees, due dates, subtasks, comments, private files, archive, version history and conflict-safe saves. Drafts persist in the current browser tab; save to synchronize across devices. The two apps share identity and database but require signing in separately on their different domains.

## Develop

Use Node.js 24. In either app run `npm ci`, copy `.env.example` to `.env.local`, fill the public Supabase configuration, then `npm run dev`. For the second app use `npm run dev -- --port 3001`. Run `npm run build` before deploying.

## Operate and deploy

See [the deployment and access guide](docs/netlify-and-supabase.md). Manual Netlify deployments are live; GitHub auto-deployment still needs repository-owner authorization. No paid upgrade was made.

Supabase's canonical schema lives in `supabase/migrations`. The founder additions use `jr_` tables and preserve the existing product/AI schema. Seed generation is in `scripts/seed-example-questions.mjs`; it writes `supabase/seed-example-questions.sql` from the original example question bank. Seeding is an explicit database operation, never part of application startup.

`PRODUCT.md` records product scope; `DESIGN.md` records the shipped interface. Earlier product specifications remain in their existing directories. The legacy Python starter is retained.
