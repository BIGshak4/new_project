# JobRun

Interview preparation and a private founders' workspace, built with Next.js, TypeScript and Supabase.

| App | Source | Live pilot |
| --- | --- | --- |
| Practice | `apps/web` | https://jobrun-practice.netlify.app |
| Founder tasks | `apps/tasks` | https://jobrun-tasks.netlify.app |

Both apps require Supabase authentication and an approved email. Task access additionally requires founder permission. Practice includes 300 bilingual question records (295 unique families), written answers, hints, reference solutions, bookmarks and progress. AI evaluation is not connected yet.

The task board supports individual tasks, filters, assignees, due dates, subtasks, comments, private files, archive, version history and conflict-safe saves. Drafts persist in the current browser tab; save to synchronize across devices. The two apps share identity and database but require signing in separately on their different domains.

## Latest question intake — 2026-11-07

The [November 7 intake report](docs/question-intake-2026-11-07-batch30.md) records all 30 screenshots: 15 new questions (PREP-257–271), six extensions and eight provenance-only additions, covering 29 distinct questions. The catalog now contains 270 PREP records, 300 total records and 295 unique families; the 500 short questions and 2,500 active multiple-choice variants are unchanged. The existing publication protocols and historical human-review registry are unchanged.

The content-only database update and all 99 currently referenced new private asset readbacks passed. Of 104 distinct uploads, five superseded PREP-206 objects remain private historical artifacts. Validation includes 4,156 non-overlapping backend tests, 443 frontend tests, TypeScript, a production build, SystemVerilog simulation, 27 live executor cases and 116 local bilingual desktop/mobile content views. Code execution now has 41 profiles. Netlify and Render both served verified content commit `feb50f9`, and the live catalog reported300 questions/500 quiz sources/2500 variants; the intake report distinguishes these checks from physical hardware, SPICE/STA, real-device and production learner-session testing.

## Develop

Use Node.js 24. In either app run `npm ci`, copy `.env.example` to `.env.local`, fill the public Supabase configuration, then `npm run dev`. For the second app use `npm run dev -- --port 3001`. Run `npm run build` before deploying.

## Operate and deploy

For the current implementation summary and remaining backend/model work before founder testing, start with [the handoff to Shaked for real-feedback human review](docs/shaked-human-review-handoff.md).

See [the deployment and access guide](docs/netlify-and-supabase.md). Manual Netlify deployments are live; GitHub auto-deployment still needs repository-owner authorization. No paid upgrade was made.

Supabase's canonical schema lives in `supabase/migrations`. The founder additions use `jr_` tables and preserve the existing product/AI schema. Seed generation is in `scripts/seed-example-questions.mjs`; it writes `supabase/seed-example-questions.sql` from the original example question bank. Seeding is an explicit database operation, never part of application startup.

`PRODUCT.md` records product scope; `DESIGN.md` records the shipped interface. Earlier product specifications remain in their existing directories. The legacy Python starter is retained.

## Code execution — 2026-10-31

The live practice site now compiles and runs Python, JavaScript, C, C++, Verilog, SystemVerilog and VHDL in isolated microVMs. See [the implementation, coverage and live verification record](docs/isolated-code-execution.md) and [executor operations](apps/executor/README.md). That record includes the current AI-feedback limitation and supersedes the earlier execution-readiness notes above.

For the exhaustive check of all 63 software questions, see [the software execution validation report](docs/software-execution-validation-2026-10-31.md), including reproducible commands and the distinction between execution probes and question-specific correctness tests.
