# Initial security review — 2026-10-16

## Scope and starting point

- Starting source revision: `5098ded` on `master`.
- Components: FastAPI API and execution engine, practice web app, private task-board app, public-schema privileges/RLS, private Storage buckets, runtime configuration, dependency lockfiles, and deployment headers.
- User authorized finding and fixing issues, recording this review, and pushing changes to Git. An existing signed-in browser tab was offered for ordinary validation.
- Production inspection is limited to configuration/catalog metadata and ordinary health/header checks. Reproductions use synthetic local data or rollback-only temporary PostgreSQL fixtures. No exploit payload is submitted to production.

## Results

The [finding register](../README.md) contains the individual evidence, severity, fixes, tests, and limitations. It separates demonstrated application issues from dependency advisories, excessive privileges, and dashboard configuration.

- **Host execution boundary:** a harmless submitted Python candidate escaped the AST restrictions and read an audit-created host canary. HTTP practice/interview checks and default synchronous dispatch now fail closed before source extraction or execution. Written answers and AI review remain available; Python execution is deliberately unavailable until a separately isolated executor exists. No environment switch re-enables host execution. Unreviewed generated references also cannot execute through the generator command.
- **Usage and model cost:** transaction-scoped PostgreSQL advisory locks serialize daily allowance checks with insertion across workers; equivalent in-memory locks protect local mode. Replaying an in-flight interview submission preserves its accepted text and does not call the model again.
- **Availability:** missing-question caches and interview locks are bounded or released. Request throttling adds an independent address budget, bounds all fresh request buckets, and does not trust raw forwarded headers. Concurrent database health probes share one bounded query rather than opening a connection for each caller.
- **Authentication UI:** passwords are cleared before asynchronous authentication and on identity events. Stale auth/member responses cannot restore a previous identity's access; task-board state is keyed to its user. Server-side authorization and RLS remain the security boundary.
- **Browser protection:** both Next configuration and Netlify configuration now restrict framing, base URLs, objects, form destinations, camera/geolocation, and inappropriate microphone access. This is a bounded policy, not a complete script-source CSP or an assertion that all XSS is impossible.
- **Database:** excessive client maintenance privileges were removed from 28 public tables. All 38 tables retain RLS, and before/after comparisons show existing row policies and column grants unchanged. This was excessive privilege hardening; an externally reachable arbitrary-SQL path was not demonstrated.
- **Image storage:** a parent-row-locked trigger enforces canonical private image paths, an open owned parent, and aggregate limits of 24 images per practice attempt / 200 per interview. Existing 5 MiB object and raster MIME restrictions remain. Actual Storage HTTP upload and true multi-connection stress tests were not performed.
- **Dependencies:** both apps moved from Next 16.3.5 to 16.3.8, Sharp to 0.35.5 and source-map-js to 1.2.2. PyJWT moved from 2.14.0 to 2.15.1 with its minimum declared version raised. Installed advisories do not automatically establish that every vulnerable feature is reachable in JobRun.

### Database changes applied to production

Applied using Supabase's migration API to the configured JobRun project; the local filenames match the versions actually recorded remotely:

1. `supabase/migrations/20261016171103_restrict_client_table_maintenance_privileges.sql`
2. `supabase/migrations/20261016171110_bound_answer_image_storage_quota.sql`

Both applications returned success. All 8 metadata contracts passed through the working Supabase connection. All 19 synthetic Storage quota assertions passed in a rolled-back temporary fixture. The deployed function body matches the reviewed SQL, the trigger is enabled, client EXECUTE is denied, and search_path is empty. No user records or files were read, changed, or deleted.

The final advisor check reported one warning for disabled leaked-password protection and six INFO entries for intentionally inaccessible backend-only RLS tables. There were no new advisor findings. The warning requires an operator decision/action in Supabase Auth; see [its documentation](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection).

## Final QA

| Check | Result | Scope |
| --- | --- | --- |
| Backend complete suite | **967 passed, 30 skipped, 2 warnings** | In-memory store, scripted provider, database/provider credentials explicitly blank; includes actual Uvicorn proxy-chain regressions |
| Web complete suite | **185 passed, 0 skipped** | Includes 28 new auth/header/rendering security cases |
| Practice production build and typecheck | Passed | Next 16.3.8 |
| Practice hermetic tests/build/typecheck | Passed; **185 tests passed** | Sibling task-app dependencies physically unavailable throughout; restored afterward |
| Task-board production build and typecheck | Passed | Next 16.3.8 |
| npm audit, each app | **0 reported vulnerabilities** | Installed lockfiles at review time |
| OSV scan | **47 Python registry packages, 0 reported vulnerabilities after update** | Exact locked versions; not a source-code audit substitute |
| Frozen Python production requirements export and pip check | Passed | Compatible with Docker's uv 0.5 tooling |
| Production metadata contracts | **8 passed** | Read-only catalog checks via Supabase |
| Storage quota SQL assertions | **19 passed, rolled back** | Synthetic temporary fixtures; not Storage HTTP or load testing |
| Whitespace / changed Python lint checks | Passed | Changed files |

The two backend warnings are a Starlette/AnyIO deprecation and an intentionally short rejected HMAC key in an authentication test. Neither uses a production secret. The 30 skipped cases require optional integration/test facilities; they are not counted as passes. Nine of those are the new explicit opt-in database checks; their working-MCP equivalents above were performed separately.

The first integrated run found two strict historical-golden failures after automatic code execution was blocked. Only nine fixture values changed: four copies of the code check's result/explanation and one metric now record an unavailable check, not a pass. Grades, XP, evaluations, profiles, progress, and other feedback are unchanged; assertions were not weakened. The complete suite was then rerun successfully.

A limited credential-pattern scan covered 783 tracked/unignored paths and found only a documented placeholder URL in an auth configuration test. No exposed real secret was confirmed by this scan. It does not certify all Git history or all provider dashboards.

### Reviewed boundaries without a new demonstrated exploit

- Local JWT regressions and ownership tests reject bad tokens and foreign-user practice/interview resource access without mutating another user's state or calling the model. Caller-controlled body user IDs do not replace the verified identity.
- Database metadata checks cover client access to private engine/content fields and membership/promotion boundaries, not just the presence of RLS flags.
- Markdown rendering disables raw HTML; reviewed rendering cases escape unsafe markup/links. Reviewed circuits use React attributes rather than evaluating submitted JavaScript. No new XSS or server-side arbitrary-URL fetch was demonstrated in these surfaces.
- A malformed JWT `kid` candidate was rejected after reproduction showed the installed parser already rejects list/dict/integer/null/unknown values. It is deliberately absent from the finding register.

Payments, legal compliance, external provider-internal controls, and a complete history/forensics review are outside this engineering run. A surface reviewed without a finding must not be described as proven secure.

## Safety and verification notes

- A code-runner reproduction read only a temporary canary file created for this review; no real secrets or application files were read.
- A first broad backend test invocation inherited the local database configuration and was stopped when live-fixture connection errors appeared. Those fixtures attempt rollback-only transactions; no successful write was established. This invocation is not counted as a pass or described as fully offline.
- Subsequent full backend tests explicitly clear database/provider credentials, select an in-memory store and scripted model, and assert that the database is not configured before running.
- A separately authorized read-only database-contract connection failed authentication before queries. Working Supabase metadata queries and rollback-only temporary fixtures are recorded separately; skipped pytest checks are not counted as passes.

## Final results and deployment

Production database changes are applied and verified as recorded above. All application fixes were pushed to `origin/master` and published. The final ordinary HTTP verification completed at **17:32 UTC on 16 October 2026**:

| Component | Published source | Evidence |
| --- | --- | --- |
| Practice site | `9a264cfe74bbb85dbd11042b094b12856f947649` | `/api/health` 200 and exact SHA; homepage and health route contain the new CSP, SAMEORIGIN and microphone-self policy |
| Founder task board | `afe9d14c99ebdb3d86a9042938d83ec6e8773044` | `/api/health` 200 and exact SHA; homepage and health route contain the new CSP, SAMEORIGIN and disabled microphone policy |
| Render API | `9a264cfe74bbb85dbd11042b094b12856f947649` | `/health` 200 and exact public `source_revision`; unauthenticated `/v1/me` returns 401 |
| Supabase | Migration versions `20261016171103`, `20261016171110` | Successful migration API results, exact live SQL/trigger/ACL verification, 8 metadata contracts and 19 rolled-back assertions |

The task board correctly remains on the first security commit: the second commit changed no task-board source. Both successful GitHub publication checks are available for [practice](https://github.com/BIGshak4/new_project/actions/runs/38940214655) and [tasks](https://github.com/BIGshak4/new_project/actions/runs/38938576507). Read-only Netlify metadata independently confirmed the corrected practice deployment ready at 17:31:31 UTC.

All six final HTTP checks passed. No exploit or model submission was sent to production. The API's new revision field exposes only a validated public Render Git SHA; it lets this record distinguish tested source from an old live process. The later verification/documentation-only commit does not change these deployed application artifacts.

### Remaining work and limits

1. Build a genuinely isolated untrusted-code executor before restoring Python execution. An AST denylist, child process, non-root user, timeout, or environment scrub alone is insufficient.
2. Review historical execution/access logs and plan rotation of potentially reachable service/database/provider credentials as appropriate. This audit demonstrates the old boundary was unsafe; it does not establish whether anyone exploited it previously. No credentials were read or rotated during this review.
3. Enable/review leaked-password protection in Supabase Auth, including plan availability and signup UX. This dashboard setting is not changed by SQL migrations.
4. Validate a legitimate raster upload through the real Storage HTTP service and parallel quota boundaries using a dedicated synthetic account. SQL coverage alone must not be described as that test.
5. Per-process rate limits need a trustworthy hosting proxy identity and are not a distributed DDoS solution. Global/edge limits and model-spend monitoring remain operational follow-ups.
6. Production browser authentication flows require an active signed-in session. The available practice tab was authenticated locally; the live task-board tab showed a login form. Computer Use then stopped automatically because it could not confidently identify the active browser URL. No further UI input was attempted. No password-manager or authentication dialog was automated; production button-click validation remains incomplete.

### Deployment correction discovered during verification

The first practice deployment of `afe9d14` failed at 17:19 UTC. Its new cross-app header test statically imported the task app's typed Next configuration. Local builds had both dependency directories, masking the fact that Netlify installs only practice dependencies; TypeScript could not resolve `next` from the sibling app. The GitHub workflow continued waiting for a published revision after Netlify had already failed, so its running state was not proof of an active successful build.

Read-only Netlify API/build-log access identified the exact failure. The test now reads fixed, trusted repository config paths and erases their type-only imports before executing the actual configs. All header/parity assertions remain. No production typecheck was skipped and no tests were excluded. A fresh full test/build/typecheck passed while task dependencies were physically unavailable, then those dependencies were restored. The failed deployment was not retried blindly; the corrected source is published by a new Git push.

A final deployment-stack review also found Uvicorn's wildcard forwarding trust. The Docker command now trusts only loopback/private proxy ranges. Three real-Uvicorn middleware regressions verify that a caller-supplied prefix cannot reset the address budget in the modeled chain; hosting-specific proxy grouping remains an operational tuning consideration.

## Manual validation handoff

Use an authorized test account and the real sites, rather than assuming an already-open local tab represents production.

1. Open [practice](https://jobrun-practice.netlify.app/) in a fresh tab and sign in yourself. Click Today, Catalog and Progress (Hebrew: `היום`, `מאגר`, `התקדמות`); confirm navigation and your own data load. Do not change another user's account to test isolation.
2. Sign out and inspect the login form. The application should not preserve the submitted password. A browser password manager may independently fill it; use a profile without saved credentials to distinguish that behavior. Test failed login/signup confirmation only with a designated test account.
3. Open a normal Python/code question from Catalog, enter an ordinary answer and submit once as part of legitimate test practice. Its automatic Python check must be unassessed/unavailable; its text may still receive AI feedback. Truth-table/numeric questions retain their existing bounded checks. Do not submit the old host-read bypass to production.
4. Before submitting an open practice answer, attach one small JPEG/PNG/WebP through the answer-image control; confirm upload and preview, then normal submission. Repeat an ordinary authorized interview attachment if that feature is in use. This HTTP path remains unverified by this run, even though the trigger's SQL assertions passed. Do not upload hundreds of files to test the quota on production.
5. Open [tasks](https://jobrun-tasks.netlify.app/), sign in yourself and confirm the intended member's board loads. Auth-switch/recovery scenarios need deliberate test identities; do not infer cross-user isolation from one successful login.

The open password-protection setting, credential/log review and isolated-executor work are owner/backend follow-ups. They are not marked complete by the frontend smoke checks above.

This is a substantial engineering review and remediation, not a penetration-test certification or a guarantee that no vulnerabilities remain.
