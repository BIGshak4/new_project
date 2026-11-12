# JobRun

Interview preparation and a private founders' workspace, built with Next.js, TypeScript and Supabase.

| App | Source | Live pilot |
| --- | --- | --- |
| Practice | `apps/web` | [muxijobrun.com](https://muxijobrun.com) |
| Founder tasks | `apps/tasks` | [jobrun-tasks.netlify.app](https://jobrun-tasks.netlify.app) |

Both apps require Supabase authentication and an approved email. Task access additionally requires founder permission. The practice database now contains 340 bilingual question records (335 unique families). Practice includes written answers, hints, reference solutions, bookmarks and progress. The new domain has passed authenticated question loading, saving, isolated Python execution and real OpenAI grading/feedback checks; see the [production record](deploy/selfhost/PRODUCTION.md) for their scope.

The task board supports individual tasks, filters, assignees, due dates, subtasks, comments, private files, archive, version history and conflict-safe saves. Drafts persist in the current browser tab; save to synchronize across devices. The two apps share identity and database but require signing in separately on their different domains.

## Latest question intake — 2026-11-08, batch of twenty

The [November 8 intake report](docs/question-intake-2026-11-08-batch20.md) maps all 20 sources to 20 identities: nine new questions, six technical extensions and five duplicates. The catalog now has 310 PREP records, 340 total records and 335 families; 500 short questions and 2,500 active quiz variants remain unchanged. Forty original bilingual diagrams and 75 private objects were verified. All 20 incoming internal difficulty ratings, on a 1–10 scale, are bound to current content and were read back from the backend; scores remain hidden from learners. The publication protocol now explicitly requires original diagrams whenever supplied or needed and a reviewed internal difficulty for every intake. Verification passed 4,420 unique backend tests, 454 web tests, TypeScript/build, 66,134 native RTL comparisons, 6,665 C checks, 12,003 Java checks, 80 local language/width views and 36 live signed-broker cases across three new profiles. After integrating concurrent security commits, another overlapping 436-test regression passed with the lock-exact certifi dependency. Content commit `0a78195` was verified on both live deployments, with database health and catalog 340/500/2500 read back; the public Hebrew landing page was observed without authentication. [Deployment evidence](interview_preparation/checks/batch1108b20-deployment-verification.json) records the scope and limits.

## Earlier question intake — 2026-11-07, night batch of thirty

The [night intake report](docs/question-intake-2026-11-07-night30.md) maps all 30 screenshots to 29 identities: 14 new questions, five technical extensions and ten existing questions with new sources. The catalog now has 301 PREP records, 331 raw records and 326 families; 500 short questions and 2,500 active quiz variants are unchanged. Forty-four original bilingual diagrams and 94 new private objects are verified. All 317 old live identities, 624 unchanged translations and 337 skill links were preserved. Validation passed 4,351 unique backend tests, 449 web tests, TypeScript/build, 21,810 native SystemVerilog simulation checks, 25 C++ boundary cases and 56 live broker cases across four new profiles. Browser QA covers 116 local language/width views, separate from authenticated production learner testing. Publication is complete: Netlify and Render both verified content revision `1fd0984` with healthy database access. The live catalog reports 331 questions, 500 short-question sources and 2,500 quiz variants; the public landing loaded in the browser. [Deployment evidence](interview_preparation/checks/night1107n30-deployment-verification.json) distinguishes these probes from local renderer QA and authenticated learner testing.

## Earlier question intake — 2026-11-07, batch of twenty

The [latest November 7 intake report](docs/question-intake-2026-11-07-batch20.md) records all twenty screenshots: thirteen new questions (PREP-276–288), two technical extensions and four existing questions with additional sources. Two screenshots belong to PREP-151, making nineteen affected question identities. Repository content now builds to 287 PREP records, 317 total records and 312 unique families. The 500 short questions and 2,500 active multiple-choice variants are unchanged. Missing instructions are completed with explicitly labeled assumptions under the existing publication protocol; original sources and historical human-review records are preserved. The [earlier ten-screenshot report](docs/question-intake-2026-11-07-batch10.md) and [thirty-screenshot report](docs/question-intake-2026-11-07-batch30.md) remain separate.

Completed validation includes 446 frontend tests, TypeScript and production build; 96,555 native RTL checks; 521 C++ assertions; four-thread C11 stress with 100,000 protected increments; eight C decimal-reversal boundary cases; independent model/oracle checks; and two AI peer reviews. Execution now has 45 profiles, 84 positive references and 25 smoke fixtures, preserving all previous profiles and fixture prefixes. Three new profiles passed all 37 live signed-broker cases. The combined runtime suite passed 307 tests; only its 240 catalog tests are disjoint from the 4,039-test backend partition, yielding 4,279 unique backend tests. The media inventory contains 1,668 assets, including 66 new private assets. The guarded database update and readback passed for 317 questions, 634 translations and 337 skill links; all 304 previous identities, 298 unrelated question hashes, 604 unchanged translation hashes and 324 existing skill links were preserved, along with old prefixes/hints in the four expanded translations. All 66 private objects were verified without learner writes. **Publication is complete:** Netlify and Render both reported `ff71aeb` with healthy database access, and the live catalog reported 317 questions, 500 short-question sources and 2,500 active quiz variants. The public landing loaded successfully. [Live deployment evidence](interview_preparation/checks/batch1107b20-deployment-verification.json) keeps these observations distinct from local browser QA and authenticated learner testing. The report distinguishes finite models and direct broker jobs from physical hardware, SPICE/STA, fairness proofs, real-device checks and authenticated production learner testing.

Local browser QA covered nineteen identities in both languages at 1,272px and 382px iframe content widths, revealing all three hints, solutions and material sections with LTR code and no page overflow. Of 104 image DOM observations, 78 were loaded and 26 lazy or not yet loaded; these are not 104 successful fetches. The [browser evidence](interview_preparation/checks/batch1107b20-browser-verification.json) scopes this to production material renderers with local QA controls, separate from authenticated production learner testing.

## Develop

Use Node.js 24. In either app run `npm ci`, copy `.env.example` to `.env.local`, fill the public Supabase configuration, then `npm run dev`. For the second app use `npm run dev -- --port 3001`. Run `npm run build` before deploying.

## Operate and deploy

For the current implementation summary and remaining backend/model work before founder testing, start with [the handoff to Shaked for real-feedback human review](docs/shaked-human-review-handoff.md).

The practice website and API run together on a DigitalOcean VPS at [muxijobrun.com](https://muxijobrun.com) and [api.muxijobrun.com](https://api.muxijobrun.com). Supabase and the isolated code-execution broker remain the existing services. Start with the [current production runbook](deploy/selfhost/PRODUCTION.md); the [publishing guide](deploy/selfhost/AUTODEPLOY.md) describes the dedicated `production` branch and signed images. Signed publication, a supervised rollback drill, normal deployment and real OpenAI grading/feedback have passed. The host update timer is enabled and the publisher is configured to verify the live revision after future pushes. Operator SSH uses key-only authentication and a provider-managed source allowlist.

Founder tasks remain on Netlify. The old practice Netlify site and Render API are retained during the transition, and the Netlify subscription has not been cancelled. The [earlier Netlify and Supabase guide](docs/netlify-and-supabase.md) remains relevant to that retained hosting.

Supabase's canonical schema lives in `supabase/migrations`. The founder additions use `jr_` tables and preserve the existing product/AI schema. Seed generation is in `scripts/seed-example-questions.mjs`; it writes `supabase/seed-example-questions.sql` from the original example question bank. Seeding is an explicit database operation, never part of application startup.

`PRODUCT.md` records product scope; `DESIGN.md` records the shipped interface. Earlier product specifications remain in their existing directories. The legacy Python starter is retained.

## Code execution — 2026-10-31

The live practice site compiles and runs Python, JavaScript, C, C++, Verilog, SystemVerilog and VHDL in isolated microVMs. See [the implementation, coverage and live verification record](docs/isolated-code-execution.md) and [executor operations](apps/executor/README.md) for the execution architecture and historical checks. The [current production record](deploy/selfhost/PRODUCTION.md) separately records the authenticated execution and real OpenAI-feedback checks on the new domain.

For the exhaustive check of all 63 software questions, see [the software execution validation report](docs/software-execution-validation-2026-10-31.md), including reproducible commands and the distinction between execution probes and question-specific correctness tests.
