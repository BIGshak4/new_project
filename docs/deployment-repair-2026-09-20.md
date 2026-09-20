# Deployment repair — 20 September 2026

## Root cause

Both Netlify sites previously received manual CLI uploads. Neither had a repository/build connection, so pushing to GitHub did not publish the frontend. Commit authorship was not the cause. The actual primary branch is `master`.

## Changes

- Linked the existing practice and task-board projects to `https://github.com/BIGshak4/new_project.git` over HTTPS, with independent bases `apps/web` and `apps/tasks`.
- Pulled/rebased Shaked's latest source, `ca453eafc901f813b1ec8d43a5f4793a77ed3d66`. The final verified frontend release includes all of those changes plus the deployment repairs below.
- Added separate GitHub Actions push workflows and encrypted, site-specific Netlify build-hook secrets. Each workflow builds the relevant application when its files change on `master`; either founder's push works the same way. Documentation-only changes do not rebuild the websites. Backend changes continue through Render.
- Added a public, non-secret Git revision to each app's `/api/health`. Deployment workflows only succeed once their expected SHA is actually live.

The current GitHub account has push access but not repository administration access. Therefore, this uses Netlify's supported build-hook flow with public HTTPS cloning, rather than installing the native Netlify GitHub App. No account-wide Netlify credential is stored in GitHub Actions. Before making the repository private, its owner must authorize the native App and relink both existing projects; then disable the hook workflows to avoid duplicate builds.

The build configuration and recovery instructions are in [netlify-and-supabase.md](netlify-and-supabase.md).

## Verification

- Web application: 33 tests passed; TypeScript checks passed.
- Backend offline suite: 610 tests passed.
- Live database suite: **16 passed in 874.37 seconds (14m34s)**, running both `tests/test_live_db.py` and `tests/test_live_service.py` together against the existing Supabase session pooler from the local Windows environment. No connection-drop failures occurred in this run; Docker was not necessary. The suite uses scripted model responses and rolled-back transactions: no paid model calls and no persistent test submissions or content-publication changes.
- This is **659 passing tests** across the web, offline backend and live database suites. The live suite covers all 30 questions in both languages, persistence, retry after model failure, double-click handling, daily limits, cross-user access, RLS, reseeding, loading speed and the HTTP service flow.
- The deployed backend also passed `scripts/smoke_http.py --url https://jobrun-api.onrender.com --origin https://jobrun-practice.netlify.app`, including authentication rejection, CORS, route contracts, oversized-request rejection and signing-key retrieval.
- Both applications: Netlify built and published the Git source successfully.
- First push-triggered verification caught a missing server adapter: the cloud build reported ready but the site returned 404. Explicitly enabled `@netlify/plugin-nextjs` in both committed `netlify.toml` files. The final successful release is `ea163856d8a08592243d71b885c48ff193dbd2cd`.
- Both push-triggered Actions completed successfully, and both live `/api/health` endpoints returned HTTP 200 and that exact source revision: [practice run](https://github.com/BIGshak4/new_project/actions/runs/35504734635), [task-board run](https://github.com/BIGshak4/new_project/actions/runs/35504734657).
- Live backend health: real Anthropic provider, database and authentication configured; `answer_images` changed from `stored_only` to `assessed` after the server secret was saved and the service redeployed.
- Render automatically deployed `471e6ebaf5613541019bb35100006434de5b636b` successfully after the configuration repair; the provider and image capability remained enabled. The practice browser displayed the authenticated 30-question bank, and the task-board browser displayed its normal sign-in page.
- A temporary PNG uploaded to the private answer-image bucket was fetched successfully by the actual backend `StorageImageFetcher`; unauthenticated fetching was refused. The fixture was deleted. This verifies Storage connectivity, not the correctness of a model's interpretation of a handwritten answer.

## Operational state and remaining human decisions

- The server-only Storage key is configured on the existing Render service and in ignored `backend/.env`. The local database URL was copied from the existing server configuration for testing. No model key was copied locally, and local `LLM_PROVIDER` remains `scripted`. Temporary secret export/import files are removed after use.
- The previously requested complete live-database rerun is now done. To repeat it locally with visible per-test progress: `cd backend`, then `.venv/Scripts/python.exe -m pytest tests/test_live_db.py tests/test_live_service.py -v --tb=short`. Use the ignored local database configuration; never copy credentials into a command, issue or commit.
- Confirmed directly in Render: the existing Docker service is **already in Frankfurt**, on the **Free** instance plan. No region move is needed. Free-instance sleep can still delay the first request; upgrading is a separate paid decision and was not performed.
- Updated the Render blueprint so a later sync does not reset the live provider to the old scripted demo setting. Provider selection and server credentials use `sync: false`; real secrets remain in the service settings.
- Harel and Shaked must review the first ten questions and their model feedback before publishing them and disabling in-review content. Deploying the code is not content approval.

No credentials or founder answers are included in this report or Git. Temporary environment export/import files and the synthetic image were removed. Existing untracked local Supabase setup files were left untouched.

For the human pilot, review representative correct, partial and wrong answers in both languages, plus handwritten photos and circuit diagrams. Confirm that feedback uses the visual evidence correctly before approving content or inviting more testers. Publishing the first ten questions and disabling in-review content remains a deliberate content-review step.
