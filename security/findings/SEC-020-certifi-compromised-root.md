# SEC-020 — The backend's certificate bundle trusted a compromised certificate authority

- **Severity:** Medium (advisory severity Critical). Every outbound TLS connection of the API (OpenAI, Anthropic, Supabase Storage, the code-execution broker) trusted emSign roots whose intermediate keys were compromised; an attacker on the network path with a mis-issued certificate could have intercepted them.
- **Status:** Fixed locally (lock updated), deployed with the backend commit of 2026-11-08.
- **Discovered:** 2026-11-08 (`pip-audit` over the exported lock: PYSEC-2026-4320 / GHSA-6q48-6c7w-9gw2)
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** `backend/uv.lock` `certifi 2026.7.22`.

## Problem and impact

Installed-advisory finding, not a demonstrated exploit.

## Safe reproduction

`uv export --no-hashes --no-dev --format requirements-txt | uvx pip-audit -r -`.

## Exact remediation

`uv lock --upgrade-package certifi` → `2026.10.23`; the image is rebuilt on deploy.

## Verification

`pip-audit` clean after the bump; no other Python advisory; `npm audit --omit=dev` on the web app reports only the Next.js advisories handed to Harel (row 25).

## Remaining work

Re-run both scans at every dependency change and monthly.

## References

GHSA-6q48-6c7w-9gw2.
