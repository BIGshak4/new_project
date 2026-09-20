# JobRun deployment and access

Updated: 20 September 2026.

## Live applications

| App | URL | Netlify site ID | Repository directory |
| --- | --- | --- | --- |
| Practice | https://jobrun-practice.netlify.app | `a352db9a-5987-437d-aaed-90b5a2622c63` | `apps/web` |
| Founder tasks | https://jobrun-tasks.netlify.app | `3aeea048-c2d1-4803-a5e7-b7723f536283` | `apps/tasks` |

Both are in the existing **JobRun** Netlify team (`jobrunerai`). Free plan retained; no automatic top-up or paid upgrade was enabled. Hosting login protection is off so the application login screens are reachable. Supabase authorization protects all private data. The optional [Powered by Netlify badge](https://docs.netlify.com/manage/projects/powered-by-netlify-badge/) is disabled per project because it overlapped mobile content.

## First sign-in

1. Open either application and choose the first-time account creation option.
2. Use the business email `jobrunerai@gmail.com`, which is already allowlisted with founder access. Choose your own application password; it is not your Google or Netlify password.
3. Confirm the Supabase email and sign in. Each domain requires a separate sign-in, using the same credentials.
4. For separate founder accounts, give the administrator the exact personal email addresses. Add only approved addresses to `jr_members`, with `can_manage_tasks=true` for founders and `false` for learners. Do not place these grants in editable user metadata.

The business membership row alone is permission, not an Auth account. On 19 September, the two requested personal founder accounts were created and allowlisted with task management access; passwords are not stored in the repository. Harel confirmed his email; Shaked's email confirmation was still pending at verification. Both apps use the same Auth accounts but require sign-in on each domain. Supabase email confirmation remains enabled. With Supabase's default mail service, recipient/rate restrictions can prevent sending to people outside the Supabase team. Configure custom SMTP before inviting a broader pilot. See [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp).

Approved redirect URLs are the two production domains plus localhost ports 3000 and 3001. The production default Site URL is the practice site. The minimal managed configuration is `scripts/auth-config/supabase/config.toml`; undeclared remote settings were preserved. Do not push the full local-development `supabase/config.toml` to production blindly.

## Database and files

Existing project: `djpwvqpsqbkvprlncjjg`, Frankfurt, https://supabase.com/dashboard/project/djpwvqpsqbkvprlncjjg.

Additive tables: `jr_members`, `jr_tasks`, `jr_comments`, `jr_task_events`, `jr_practice_entries`. Private trigger functions live in `jobrun_private`. The original question/product/AI schema remains intact. Three dated migrations contain the new infrastructure, founder/learner separation, and private file policies.

The `jobrun-task-files` bucket is private. PDFs, PNG/JPEG and text files up to 10MB are accepted. Founders can upload/read/delete; learners and anonymous users cannot. Downloads use 60-second signed URLs. File names are encoded for storage and decoded for display, including Hebrew names. Uploads happen immediately, independently of saving the task text. The task JSON export does not export files, comments or audit history.

Tasks use optimistic concurrency: updates include the last known version, and the server increments it. An old version cannot overwrite a newer one. Audit rows are server generated. Practice is private to each user, including from other founders. Local drafts use session storage and are not a cross-device backup.

## Question bank and AI

30 original example questions were imported from `example_question/questions.json`, with 60 Hebrew/English translations. They remain `in_review`, visible only to allowlisted participants. Solutions and hints come from the database. Reference links explain concepts; they are not evidence that an employer asked that question. The separate verification bank is not published.

The practice frontend is connected to Shaked's authenticated FastAPI service at https://jobrun-api.onrender.com. Attempts, submissions and engine progress persist in Supabase. Shaked has enabled the real Anthropic provider (Opus evaluator, Sonnet feedback/tips); the live health check confirms it. Image assessment still requires the server-only Storage key; check `/health.answer_images` rather than assuming a successful text assessment covers photos. Self-assessment stays separate. Expanding to 150 reviewed questions is still a content milestone.

Question and translation tables are closed to browser clients by `20260919093403_restrict_practice_question_reads.sql`. Browsing uses the safe API; hint and reference endpoints record exposure. The internal `attempt.follow_up_turns` JSON is also withheld because it includes expected answers. The backend database connection is unaffected. Apply this migration only after deploying the integrated frontend.

## Deploy updates

### Automatic deployment

Both existing Netlify projects now clone `https://github.com/BIGshak4/new_project.git`, branch `master`, directly over HTTPS. This repository is currently public. The practice base directory is `apps/web`, and the task-board base directory is `apps/tasks`; each uses its own committed `netlify.toml`, Next.js adapter, environment variables and Node.js 24.

GitHub Actions requests the appropriate Netlify build on a push to `master`, regardless of who pushes:

- `.github/workflows/deploy-practice.yml`: changes under `apps/web` or its workflow.
- `.github/workflows/deploy-tasks.yml`: changes under `apps/tasks` or its workflow.
- `.github/workflows/netlify-build.yml`: reusable trigger and verification; changes to it deploy both sites.
- Each workflow also supports **Run workflow** on `master` for an intentional redeploy. Backend-only changes are handled by Render's existing Git deployment, not by rebuilding the two frontends. Documentation-only commits do not rebuild the websites.

Each project has a master-branch build hook. The URLs are encrypted GitHub repository secrets (`NETLIFY_PRACTICE_BUILD_HOOK`, `NETLIFY_TASKS_BUILD_HOOK`). They only trigger builds; no account-wide Netlify token, database credential or model key is stored in Actions. The workflow does not run on pull requests or check out untrusted scripts.

**A green deployment workflow means the expected commit is live**, not just that a build was queued. The workflow waits up to 12 minutes for the public `/api/health` to report the pushed SHA in `revision`. `NEXT_PUBLIC_BUILD_REVISION` is populated at build time from Netlify's `COMMIT_REF`; it contains no credentials. If a build fails, Netlify retains the previous successful deployment and the workflow reports a failure. Open the project's Deploys page for the build log.

This uses Netlify's supported build-hook integration rather than the native Netlify GitHub App. The current GitHub account has push access but not repository-admin access, so it cannot install that App on Shaked's repository. HTTPS cloning plus the repository workflow enables automatic deployment without waiting for that installation. **Before making the repository private**, have its owner install/authorize the Netlify GitHub App and relink both existing projects. Disable the two triggering workflows if switching to native push events, to avoid duplicate builds.

### Manual recovery

Prefer **Run workflow** so the site is built from Git. For an emergency local deployment, use Node.js 24 and an authenticated Netlify CLI. These commands build with Netlify's Next.js adapter, then deploy the selected app:

```powershell
# Run in apps/web
npx --yes netlify-cli deploy --prod --site a352db9a-5987-437d-aaed-90b5a2622c63
# Run in apps/tasks
npx --yes netlify-cli deploy --prod --site 3aeea048-c2d1-4803-a5e7-b7723f536283
```

Both projects have `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` configured. The practice project's production build also has `NEXT_PUBLIC_API_BASE_URL=https://jobrun-api.onrender.com`. Rebuild when a public environment value changes. Only publishable client configuration belongs there. Never deploy a service-role key, database password, or model-provider key to a browser bundle.

The earlier manual-only setup is retired. Do not create duplicate hosting projects, change the production branch to `main`, or deploy an old local checkout over a newer Git build. The repository's actual primary branch is `master`.

## Verification and limits

Production builds and TypeScript checks pass. Live Supabase tests exercised password login, both question translations, individual task insert/update, stale-version rejection, comments, server audit history, private practice and file upload/download/delete. Anonymous access, membership self-escalation, learner-to-board access and cross-user practice reads were checked. Browser checks exercised task edits, solution entry/save, hint/reference retrieval and language switching. Desktop and 390px layouts were inspected.

The automated security advisor reports four RLS-enabled question/catalog tables without policies (intentionally closed browser access) and disabled leaked-password detection. Public execution rights on the platform RLS event trigger were revoked. See [Supabase password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection) before broader launch; no plan was upgraded to enable paid controls.

Still pending: custom SMTP for external testers, joint expert feedback validation, expanded reviewed content, and broader user testing. The Render Storage secret and a complete rerun of the live database suite are tracked in the deployment handoff. No custom domain, payment provider, native application or outgoing reminder system is configured. See [the real-model handback](p1-real-model-handback.md) and [the deployment repair report](deployment-repair-2026-09-20.md).

References: [Netlify build hooks](https://docs.netlify.com/build/configure-builds/build-hooks/), [repository linking](https://docs.netlify.com/build/git-workflows/repo-permissions-linking/), [monorepos](https://docs.netlify.com/build/configure-builds/monorepos/).
