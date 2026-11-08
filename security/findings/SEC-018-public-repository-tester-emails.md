# SEC-018 — The repository is public and carried pilot testers' e-mail addresses

- **Severity:** High for privacy and intellectual property; no credential exposure. The repository publishes the question bank with reference solutions, internal product and pricing notes, the admin allow-list identity, and the first names and personal e-mail addresses of five pilot testers written into `backend/STATUS.md` between 2026-10-28 and 2026-11-07.
- **Status:** Operator action required (make the repository private); the addresses were scrubbed from `backend/STATUS.md` on 2026-11-08 but remain in Git history.
- **Discovered:** 2026-11-08
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** the GitHub repository (visibility PUBLIC at review time); `backend/STATUS.md` lines naming testers; `docs/netlify-and-supabase.md` and two migrations naming the founders' shared address (kept: it is the admin allow-list and cannot change in applied migrations).

## Problem and impact

A pattern sweep of every commit found no key, token, password or connection string. The exposure is personal data (testers' addresses tied to a product) and the solution bank. Verified with the GitHub API (`isPrivate: false`).

## Safe reproduction

`gh repo view --json isPrivate`; `git grep -E '[A-Za-z0-9._%+-]+@gmail\.com' backend/STATUS.md` returns no personal address after the scrub.

## Exact remediation

Code side: eight addresses replaced by "(e-mail withheld)" in `backend/STATUS.md`; the rule for future entries is first name only. Operator side: Shaked switches the repository to private (Settings → General → Danger zone). Optional afterwards: rewrite history to remove the addresses, with Harel's agreement, since every clone must be re-based.

## Verification

Scrub verified by grep. Repository visibility to be verified by the same `gh` command after Shaked's change.

## Remaining work

History still carries the addresses until rewritten. Forks or clones taken while public cannot be recalled.

## References

Israeli Privacy Protection Law notes in `docs/`.
