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
- First push-triggered workflow verification: pending the commit containing these workflows.
- Live backend health: real Anthropic provider, database and authentication configured. Image assessment was `stored_only` before server secret setup.

## Remaining work being checked

- Configure the server-only Supabase Storage key on the existing Render backend and in the ignored local backend environment, then verify image fetching.
- Rerun the 16 live database tests using a working database connection. Offline results do not replace this run.
- Confirm current Render region and instance plan before proposing any migration or paid upgrade. No paid upgrade is included in this change.
- Harel and Shaked must review the first ten questions and their model feedback before publishing them and disabling in-review content. Deploying the code is not content approval.

No credentials or founder answers belong in this report or in Git. The final operational results will be appended after verification.
