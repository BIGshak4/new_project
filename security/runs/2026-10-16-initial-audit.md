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
| Backend complete suite | **964 passed, 30 skipped, 2 warnings** | In-memory store, scripted provider, database/provider credentials explicitly blank; 11.79 seconds |
| Web complete suite | **185 passed, 0 skipped** | Includes 28 new auth/header/rendering security cases |
| Practice production build and typecheck | Passed | Next 16.3.8 |
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

## Safety and verification notes

- A code-runner reproduction read only a temporary canary file created for this review; no real secrets or application files were read.
- A first broad backend test invocation inherited the local database configuration and was stopped when live-fixture connection errors appeared. Those fixtures attempt rollback-only transactions; no successful write was established. This invocation is not counted as a pass or described as fully offline.
- Subsequent full backend tests explicitly clear database/provider credentials, select an in-memory store and scripted model, and assert that the database is not configured before running.
- A separately authorized read-only database-contract connection failed authentication before queries. Working Supabase metadata queries and rollback-only temporary fixtures are recorded separately; skipped pytest checks are not counted as passes.

## Final results and deployment

Production database changes are applied and verified as recorded above. Application changes are tested locally; Git push and live application revision/header checks are recorded below after publication. The API now reports only a validated public Render Git SHA in `/health`, allowing a deployment to be tied to the reviewed source.

### Remaining work and limits

1. Build a genuinely isolated untrusted-code executor before restoring Python execution. An AST denylist, child process, non-root user, timeout, or environment scrub alone is insufficient.
2. Review historical execution/access logs and plan rotation of potentially reachable service/database/provider credentials as appropriate. This audit demonstrates the old boundary was unsafe; it does not establish whether anyone exploited it previously. No credentials were read or rotated during this review.
3. Enable/review leaked-password protection in Supabase Auth, including plan availability and signup UX. This dashboard setting is not changed by SQL migrations.
4. Validate a legitimate raster upload through the real Storage HTTP service and parallel quota boundaries using a dedicated synthetic account. SQL coverage alone must not be described as that test.
5. Per-process rate limits need a trustworthy hosting proxy identity and are not a distributed DDoS solution. Global/edge limits and model-spend monitoring remain operational follow-ups.
6. Production browser authentication flows require an active signed-in session. The available practice tab was authenticated locally; the live task-board tab showed a login form. No password-manager or authentication dialog was automated.

This is a substantial engineering review and remediation, not a penetration-test certification or a guarantee that no vulnerabilities remain.
