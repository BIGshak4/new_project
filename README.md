# JobRun

Interview preparation and a private founders' workspace, built with Next.js, TypeScript and Supabase.

| App | Source | Live pilot |
| --- | --- | --- |
| Practice | `apps/web` | https://jobrun-practice.netlify.app |
| Founder tasks | `apps/tasks` | https://jobrun-tasks.netlify.app |

Both apps require Supabase authentication and an approved email. Task access additionally requires founder permission. Practice includes 304 bilingual question records (299 unique families), written answers, hints, reference solutions, bookmarks and progress. AI evaluation is not connected yet.

The task board supports individual tasks, filters, assignees, due dates, subtasks, comments, private files, archive, version history and conflict-safe saves. Drafts persist in the current browser tab; save to synchronize across devices. The two apps share identity and database but require signing in separately on their different domains.

## Latest question intake — 2026-11-07, batch of ten

The [latest November 7 intake report](docs/question-intake-2026-11-07-batch10.md) records ten screenshots: four new questions (PREP-272–275), six variants of existing questions and two completions of older exercises. The catalog contains 274 PREP records, 304 total records and 299 unique families; the 500 short questions and 2,500 active multiple-choice variants are unchanged. The publication protocol now records the user's authorization to supply clearly labeled, reasonable assumptions when instructions are incomplete. Original sources and historical human-review records are preserved; no new human approval is claimed.

The content-only database update and readback passed for 304 questions and 608 translations. The media inventory has 1,602 assets, including 45 new private assets in this intake. Validation includes 4,194 non-overlapping backend tests, 444 frontend tests, TypeScript, a production build, native SystemVerilog simulation, Verilator/Z3 Sudoku generation, C++ compilation and 48 local bilingual desktop/mobile content views. Code execution has 42 profiles; the new sorting profile passed 14 live signed-broker cases. Netlify and Render both verified content commit `c5d3d1d` with healthy database connectivity; the live catalog reported 304 questions, 500 short-question sources and 2,500 active quiz variants. The public landing page rendered in the browser. The report distinguishes finite models and local fixture views from physical hardware, SPICE/STA, real-device and authenticated production learner testing. The [earlier 30-screenshot intake](docs/question-intake-2026-11-07-batch30.md) remains documented separately.

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
