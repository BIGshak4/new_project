# Full security review — 2026-11-08

Scope: the whole system as deployed on 2026-11-08 — the FastAPI backend (authentication, authorization, money paths,
input handling, denial of service, code execution), the 44 Supabase migrations (row-level security, grants,
definer functions, storage policies), the Next.js web app and its Netlify configuration (read-only; the web app is
Harel's), the Render blueprint and Dockerfile, the GitHub repository and its history, and the locked dependencies.
Starting Git revision: `3b0d770` (local, rebased on origin `adf343b`). Requested by Shaked ("do a full security
check, i dont want our system to be hacked").

Method: four independent read-only code reviews, one per area, each asked for concrete exploit scenarios and for
what it found solid; automated scans (`npm audit --omit=dev`, `pip-audit` over the exported lock, a pattern sweep of
every commit for key shapes, response-header and health-page checks against the live hosts, the three Next.js
advisories read from GitHub's advisory API); every finding re-verified by hand in the source, the regular-expression
slowdown reproduced with a local benchmark on a copy of the pattern (8,000 blanks: 2.6 s per scan). No production
data was read, no user code run, no live attack sent.

## Result

Seven confirmed findings, [SEC-015](../findings/SEC-015-webhook-without-payment-keys.md) to
[SEC-021](../findings/SEC-021-code-runner-slots-shared.md); the first two are also what an outside attacker would
reach first. Six are fixed in the backend commit that carries this report, with a regression test each in
`backend/tests/test_security_review_2026_11_08.py`. One, the public repository (SEC-018), is an operator action:
Shaked makes the repository private; the tester e-mails it carried were scrubbed from `backend/STATUS.md` in the same
commit (they remain in history until the repository is private or rewritten).

Four hardening items went to Harel's list (`docs/harel-todo-2026-10-18.md` rows 25-26): the Next.js upgrade past
16.4.0 (three advisories; the installed `sharp` 0.35.5 already carries the image-optimizer fix and the app uses
neither `use cache` nor Server Actions, so none is exploitable today), a `script-src` content-security policy with an
explicit HSTS header (login tokens live in browser storage), a column list on the browser's `jr_practice_entries`
UPDATE grant, and the `deleted_at` column of `interview_session` for the browser's reads.

Operator items that no commit can close: make the repository private (SEC-018); confirm "Confirm email" is on in
Supabase Auth and turn on leaked-password protection ([SEC-013](../findings/SEC-013-leaked-password-protection.md),
still open); set `HEALTH_KEY` on Render; move the API off the free plan, which is what turns the two CPU findings
into a whole-service outage.

## What held up

Token verification pins the algorithm, enforces audience, issuer and expiry, and refuses anonymous sessions and the
project's anon/service keys. Every object read or write is scoped to the owner in SQL; foreign objects are 404.
Every debit runs under a per-user advisory lock with the balance read in the same transaction; credits are
idempotent on `(user_id, reference)`; duel stakes are escrowed. Every table has row-level security, policies use
`(select auth.uid())`, the private schema is revoked from the browser roles, 30+ definer functions set
`search_path=''` and verify the caller, storage uploads are path-locked to the owner with count caps. No SQL
injection (SQLAlchemy Core, bound parameters everywhere), no server-side request forgery (only fixed hosts and
validated paths are fetched), no `pickle`/`eval`/`exec` on user data. Learner code never runs on the API host: it
goes to a deny-all micro-VM with Ed25519 single-use tickets, rlimits and a scrubbed environment. No secrets in the
repository or in any commit. The web app has no unsafe HTML rendering, no open redirect, no third-party script,
tokens are never in `NEXT_PUBLIC_*`, and its headers were already right.

## Verification

Backend: the new regression file (12 tests) plus the suites of every touched module green locally; the full offline
suite recorded in `backend/STATUS.md` §5zze. Deployment: once pushed, `/health` must report `env: production` and
the security headers must be on every response; the smoke script covers the 61 routes. Database: no migration in
this review.

## Limitations

Read-only review of the executor service's source; its live sandbox was not re-tested (see SEC-001's 2026-10-31
record). Supabase Auth dashboard settings are not in the repository and were not checked. Dependency conclusions are
dated to the day's advisory databases.
