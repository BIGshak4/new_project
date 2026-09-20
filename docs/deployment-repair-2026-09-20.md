# Deployment repair — 20 September 2026

## Root cause

Both Netlify sites previously received manual CLI uploads. Neither had a repository/build connection, so pushing to GitHub did not publish the frontend. Commit authorship was not the cause. The actual primary branch is `master`.

## Changes

- Linked the existing practice and task-board projects to `https://github.com/BIGshak4/new_project.git` over HTTPS, with independent bases `apps/web` and `apps/tasks`.
- Built and published Shaked's latest source, `ca453eafc901f813b1ec8d43a5f4793a77ed3d66`, successfully on both sites.
- Added separate GitHub Actions push workflows and encrypted, site-specific Netlify build-hook secrets. Each workflow builds the relevant application when its files change on `master`; either founder's push works the same way. Documentation-only changes do not rebuild the websites. Backend changes continue through Render.
- Added a public, non-secret Git revision to each app's `/api/health`. Deployment workflows only succeed once their expected SHA is actually live.

The current GitHub account has push access but not repository administration access. Therefore, this uses Netlify's supported build-hook flow with public HTTPS cloning, rather than installing the native Netlify GitHub App. No account-wide Netlify credential is stored in GitHub Actions. Before making the repository private, its owner must authorize the native App and relink both existing projects; then disable the hook workflows to avoid duplicate builds.

The build configuration and recovery instructions are in [netlify-and-supabase.md](netlify-and-supabase.md).

## Verification

- Web application: 33 tests passed; TypeScript checks passed.
- Backend offline suite: 610 tests passed.
- Both applications: Netlify built and published the Git source successfully.
- First push-triggered verification caught a missing server adapter: the cloud build reported ready but the site returned 404. Explicitly enabled `@netlify/plugin-nextjs` in both committed `netlify.toml` files. The final successful release is `ea163856d8a08592243d71b885c48ff193dbd2cd`.
- Both push-triggered Actions completed successfully, and both live `/api/health` endpoints returned HTTP 200 and that exact source revision: [practice run](https://github.com/BIGshak4/new_project/actions/runs/35504734635), [task-board run](https://github.com/BIGshak4/new_project/actions/runs/35504734657).
- Live backend health: real Anthropic provider, database and authentication configured; `answer_images` changed from `stored_only` to `assessed` after the server secret was saved and the service redeployed.
- A temporary PNG uploaded to the private answer-image bucket was fetched successfully by the actual backend `StorageImageFetcher`; unauthenticated fetching was refused. The fixture was deleted. This verifies Storage connectivity, not the correctness of a model's interpretation of a handwritten answer.

## Remaining work being checked

- The server-only Storage key is configured on the existing Render service and in ignored `backend/.env`. The local database URL was copied from the existing server configuration for testing. No model key was copied locally, and local `LLM_PROVIDER` remains `scripted`. Temporary secret export/import files are removed after use.
- Rerun the 16 live database tests using a working database connection. Offline results do not replace this run.
- Confirmed directly in Render: the existing Docker service is **already in Frankfurt**, on the **Free** instance plan. No region move is needed. Free-instance sleep can still delay the first request; upgrading is a separate paid decision and was not performed.
- Updated the Render blueprint so a later sync does not reset the live provider to the old scripted demo setting. Provider selection and server credentials use `sync: false`; real secrets remain in the service settings.
- Harel and Shaked must review the first ten questions and their model feedback before publishing them and disabling in-review content. Deploying the code is not content approval.

No credentials or founder answers belong in this report or in Git. The final operational results will be appended after verification.
