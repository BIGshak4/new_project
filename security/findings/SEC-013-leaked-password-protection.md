# SEC-013 — Breached-password rejection is not enabled

- **Severity:** Medium configuration gap, conditional on users choosing compromised/reused passwords; no credential-stuffing attempt or account compromise was demonstrated.
- **Status:** Operator action required; remains open after the database migrations.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected component:** Supabase Auth project configuration, independent of application source/database grants.

## Problem and evidence

The Supabase security advisor returned warning `auth_leaked_password_protection`, titled **Leaked Password Protection Disabled**. A post-migration advisor check returned the same warning. Minimum length alone does not reject passwords already known from breaches. The warning does not establish that any particular user currently has a compromised password.

## Safe reproduction

Inspect the project's Auth setting/advisor status. Do not inspect password hashes, try guessed passwords against real accounts or publish example credentials from conversations.

## Exact action plan

1. A project owner opens the intended Supabase project's Authentication password/security settings.
2. Check whether the current plan supports leaked-password protection. The official documentation lists Pro and above; no plan upgrade or additional spend is authorized by this report itself.
3. Enable breached-password rejection if available. If unavailable, record a deliberate owner decision and a server-side alternative; a client-only blacklist is insufficient because callers can bypass it.
4. Review minimum length, password-change reauthentication, password-manager guidance and administrator MFA as related controls; do not claim they are implemented by this finding.
5. Using an approved disposable account and safe documented test procedure, verify signup/password-change rejection and normal strong-password success. Recheck the advisor and record the setting/evidence without storing submitted passwords.

## Verification

The post-migration advisor still reports the warning. No source patch enables this hosted Auth setting, and it was not silently changed during the database audit.

## Remaining work

Keep this record open until an owner records the decision, applies any supported setting and verifies it. Do not assume enabling protection invalidates or rotates all existing passwords or ends all sessions; account remediation requires its own scoped plan.

## References

[Supabase password security and plan availability](https://supabase.com/docs/guides/auth/password-security).
