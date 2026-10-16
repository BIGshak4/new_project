# SEC-007 — Sensitive application pages lacked frame protection

- **Severity:** Medium. A malicious site could frame the UI and attempt clickjacking where the browser makes the user's authenticated context available inside that frame.
- **Status:** Fixed locally; both Netlify deployments and live header verification pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; practice and private task-board delivery configuration.

## Problem and impact

Neither the Next response configuration nor the Netlify static/fallback configuration restricted external frame ancestors. Framing an interactive task board or practice UI can hide real controls beneath misleading content. Authentication/storage partitioning may limit particular browser attack scenarios; no real user's session was used to attempt clickjacking.

## Safe reproduction

Inspect the baseline response configuration. A local synthetic page can attempt to frame a local test deployment; after remediation, a different-origin parent must be blocked while same-origin design-gallery frames remain available. Do not use real authenticated actions for the test.

## Exact remediation

Both `apps/{web,tasks}/next.config.ts` and `apps/{web,tasks}/netlify.toml` now deliver:

```http
Content-Security-Policy: frame-ancestors 'self'; base-uri 'self'; object-src 'none'; form-action 'self'
X-Frame-Options: SAMEORIGIN
```

Permissions policy disables unused camera/location capabilities. Practice retains `microphone=(self)` for explicit dictation; the task board disables microphone. Existing same-origin design previews remain supported.

## Verification

`apps/web/tests/security_headers.test.ts` has four cases validating the actual Next policies and parity with both Netlify configurations. Hostile Markdown rendering is separately covered by `security_rendering.test.ts`; no exploitable Markdown XSS was found.

## Remaining work

Verify headers on actual deployed HTML/static responses and smoke-test same-origin previews and dictation. This bounded policy deliberately does not introduce `script-src`/`default-src`; it is not a complete XSS containment policy. A nonce-based script policy requires its own compatibility review.

## References

[CSP frame ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors), [microphone permissions policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy/microphone).
