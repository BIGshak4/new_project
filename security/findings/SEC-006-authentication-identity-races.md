# SEC-006 — Delayed auth/access responses were not bound to the current identity

- **Severity:** Low. A shared-browser/account-switch race could restore stale local identity/access context; no backend or RLS bypass was demonstrated.
- **Status:** Fixed locally; both frontend deployments pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; both authentication gates and task-board state lifetime.

## Problem and impact

An initial `getUser()` response could arrive after a newer auth event and overwrite it. Membership was a single boolean independent of user ID; old permission requests could also overwrite newer checks. The task board was not keyed by identity. These conditions could render stale workspace context during sign-out/account transitions. Server token verification and database row policies remain the authorization boundaries.

## Safe reproduction

Use deferred local promises to deliver an old user or membership grant after sign-out, another login, a newer denial or component cleanup. No real accounts or protected records are needed.

## Exact remediation

- `apps/{web,tasks}/src/lib/auth-access.ts`: auth observation suppresses superseded initial reads; access checks bind results to both user ID and request generation and support cleanup invalidation.
- `apps/{web,tasks}/src/components/auth.tsx`: uses identity-scoped access state. A previous user's grant fails closed during rendering before an effect can run.
- `apps/tasks/src/app/page.tsx`: keys the board by `user.id`, preventing reuse of its local workspace state for a different identity.

The small helper is present in each independently deployed app and both implementations are tested.

## Verification

`apps/web/tests/security_auth.test.ts` includes 18 runtime lifecycle/access cases across both implementations: stale initial success/failure, sign-out, account changes, concurrent checks, cleanup, failed query/retry and obsolete callers. These test the actual production helpers, not a separately implemented policy. No real browser account-switch test is claimed.

## Remaining work

Deploy both apps and run authorized account-switch/logout smoke tests. Preserve server/RLS checks; this client fix does not replace them or promise immediate revocation of every previously issued token.

## References

[Supabase auth state events](https://supabase.com/docs/reference/javascript/auth-onauthstatechange), [React state reset with keys](https://react.dev/learn/preserving-and-resetting-state#resetting-state-with-a-key).
