# SEC-005 — Login forms retained a reusable password after authentication

- **Severity:** Medium, requiring access to the same browser session. This concerns application form state, not extraction of Supabase password hashes.
- **Status:** Fixed locally; both frontend deployments pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; practice and task-board `Auth` components.

## Problem and impact

The authentication component stayed mounted while its signed-in workspace was visible. Its controlled password state was not cleared after login. Signing out could therefore return to the same populated password field, exposing a reusable secret on a shared device. This was established from the component state lifetime and submission paths; no real account password was inspected.

## Safe reproduction

In a local mocked-auth browser fixture with password-manager autofill disabled, enter synthetic credentials, return a successful login, then emit sign-out. The returned form's password value must be empty. Browser password-manager behavior must be distinguished from application retention.

## Exact remediation

`apps/web/src/components/auth.tsx` and `apps/tasks/src/components/auth.tsx` capture credentials only for the authentication request, immediately clear the controlled password, and clear it on auth events and explicit sign-out. Failed authentication requires re-entry rather than restoring the submitted secret.

## Verification

`apps/web/tests/security_auth.test.ts` parses each actual production form and verifies password clearing occurs before the awaited authentication request. These two checks are source-integration guards, not browser interaction tests. The complete auth component changes passed TypeScript checks and the frontend regression suite; deployment/browser verification remains separate.

## Remaining work

Deploy both sites. With a local mock or authorized test account, verify login → logout leaves the application field empty; repeat failed login and signup-confirmation flows. Saved passwords supplied by a browser password manager are outside this fix and must not be described as disabled.

## References

[React controlled inputs](https://react.dev/reference/react-dom/components/input#controlling-an-input-with-a-state-variable).
