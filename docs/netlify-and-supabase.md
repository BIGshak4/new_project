# JobRun deployment and access

Updated: 17 September 2026.

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

The seeded membership row is permission, not an Auth account: no founder password was created on your behalf. Supabase email confirmation remains enabled. The live login/session flow was tested with a temporary confirmed QA identity; delivery of a real founder's confirmation email still needs that person's inbox verification. With Supabase's default mail service, recipient/rate restrictions can prevent sending to people outside the Supabase team. Configure custom SMTP before inviting a broader pilot. See [Supabase SMTP](https://supabase.com/docs/guides/auth/auth-smtp).

Approved redirect URLs are the two production domains plus localhost ports 3000 and 3001. The production default Site URL is the practice site. The minimal managed configuration is `scripts/auth-config/supabase/config.toml`; undeclared remote settings were preserved. Do not push the full local-development `supabase/config.toml` to production blindly.

## Database and files

Existing project: `djpwvqpsqbkvprlncjjg`, Frankfurt, https://supabase.com/dashboard/project/djpwvqpsqbkvprlncjjg.

Additive tables: `jr_members`, `jr_tasks`, `jr_comments`, `jr_task_events`, `jr_practice_entries`. Private trigger functions live in `jobrun_private`. The original question/product/AI schema remains intact. Three dated migrations contain the new infrastructure, founder/learner separation, and private file policies.

The `jobrun-task-files` bucket is private. PDFs, PNG/JPEG and text files up to 10MB are accepted. Founders can upload/read/delete; learners and anonymous users cannot. Downloads use 60-second signed URLs. File names are encoded for storage and decoded for display, including Hebrew names. Uploads happen immediately, independently of saving the task text. The task JSON export does not export files, comments or audit history.

Tasks use optimistic concurrency: updates include the last known version, and the server increments it. An old version cannot overwrite a newer one. Audit rows are server generated. Practice is private to each user, including from other founders. Local drafts use session storage and are not a cross-device backup.

## Question bank and AI

30 original example questions were imported from `example_question/questions.json`, with 60 Hebrew/English translations. They remain `in_review`, visible only to allowlisted participants. Solutions and hints come from the database. Reference links explain concepts; they are not evidence that an employer asked that question. The separate verification bank is not published.

There is no AI evaluation endpoint or provider key in these apps. Shaked's proof of concept can later be connected through an authenticated server endpoint and a reviewed evaluation contract. The current progress screen reports completed practice and self-assessment, not hiring readiness. Expanding to 150 reviewed questions is still a content milestone.

## Deploy updates

Use Node.js 24 and an authenticated Netlify CLI. The following commands build with Netlify's Next.js adapter, then deploy the selected app:

```powershell
# Run in apps/web
npx --yes netlify-cli deploy --prod --site a352db9a-5987-437d-aaed-90b5a2622c63
# Run in apps/tasks
npx --yes netlify-cli deploy --prod --site 3aeea048-c2d1-4803-a5e7-b7723f536283
```

Both projects have `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` configured. Only publishable client configuration belongs there. Never deploy a service-role key, database password, or model-provider key to a browser bundle.

The sites are manually deployed; a Git push currently does not update them. For automatic deployment, the owner of `BIGshak4/new_project` must authorize the Netlify GitHub app. Connect each existing Netlify project to that same repository and production branch `master`, using its app directory as the base/package directory and its `netlify.toml`. Do not create duplicate hosting projects. Review the detected Next.js build settings before the first connected build.

## Verification and limits

Production builds and TypeScript checks pass. Live Supabase tests exercised password login, both question translations, individual task insert/update, stale-version rejection, comments, server audit history, private practice and file upload/download/delete. Anonymous access, membership self-escalation, learner-to-board access and cross-user practice reads were checked. Browser checks exercised task edits, solution entry/save, hint/reference retrieval and language switching. Desktop and 390px layouts were inspected.

The automated security advisor's remaining existing items are two RLS-enabled catalog tables without policies (closed access) and disabled leaked-password detection. Public execution rights on the platform RLS event trigger were revoked. See [Supabase password protection](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection) before broader launch; no plan was upgraded to enable paid controls.

Still pending: founder inbox confirmation, individual founder email grants, custom SMTP for external testers, GitHub auto-deployment, validated AI integration, expanded expert-reviewed content, and broader user testing. No custom domain, payment provider, native application or outgoing reminder system is configured.
