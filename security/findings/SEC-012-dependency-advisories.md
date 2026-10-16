# SEC-012 — Locked frontend/Python dependencies matched published advisories

- **Severity:** Critical maximum advisory rating in the installed set; this is an advisory bundle, not a claim that every advisory was reachable in JobRun.
- **Status:** Dependencies upgraded locally, post-update advisory scans clear and local integration checks passed; deployments pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; both npm lockfiles and the backend uv lockfile.

## Problem and evidence

Both npm audits identified three affected packages: Next.js 16.3.5, sharp 0.35.4 and source-map-js 1.2.1. The Next aggregate included a critical `next/og` ImageResponse advisory and additional cache/image/development-route advisories. Presence in a lockfile does not establish use of each affected feature; no `next/og` exploit or production SSRF was attempted.

The Python OSV scan identified PyJWT 2.14.0 with **two distinct advisories**, each also represented by a PYSEC alias. The recursive pre-verification payload issue can escape as a request-level exception; maintainer evidence does not establish process termination or auth bypass. The separate OKP/DPoP key-identity issue was not shown reachable in JobRun, which accepts ES256/RS256 and optional HS256.

## Safe reproduction

Audit installed/locked versions against registry advisories. For PyJWT's parser regression, use a local synthetic nested token and assert the documented decoding exception; no network call or real login token is needed.

## Exact remediation

| Package | Before | Selected patch |
|---|---:|---:|
| Next.js, both apps | 16.3.5 | 16.3.8 |
| sharp, both npm lockfiles | 0.35.4 | 0.35.5 |
| source-map-js, both npm lockfiles | 1.2.1 | 1.2.2 |
| PyJWT | 2.14.0 | 2.15.1 |

Changed `apps/{web,tasks}/package.json` and `package-lock.json`, plus `backend/pyproject.toml`/`uv.lock`. The PyJWT minimum is 2.15.1; 2.15.0 is the first advisory fix, while 2.15.1 also fixes its padding compatibility regression. Unrelated Python package versions were preserved.

## Verification

Post-update `npm audit` reported **zero vulnerabilities for each app**. A fresh OSV scan of 47 installed Python registry packages reported no advisories. The local PyJWT fixture returned `DecodeError` rather than an uncaught recursion exception, with zero network/production calls. Frozen uv export and Python dependency consistency checks passed. Root integration builds/tests and deployed revisions are recorded in the run report, not inferred from a successful install.

## Remaining work

Deploy all three applications and keep lockfiles in dependency-review automation. Clear scans are a dated advisory snapshot, not proof of absence of unknown vulnerabilities or application bugs.

## References

- Next: [ImageResponse](https://github.com/advisories/GHSA-vcvr-r3jv-pc5j), [image optimization SSRF](https://github.com/advisories/GHSA-cjq9-62q9-8jv4), [Draft Mode cache](https://github.com/advisories/GHSA-3w37-wq28-93x7), [SSG/ISR cache poisoning](https://github.com/advisories/GHSA-4jqv-mc3x-m676), [development MCP disclosure](https://github.com/advisories/GHSA-39w2-rjm5-chcv), [metadata image routes](https://github.com/advisories/GHSA-f87g-xv8r-7p7x), [SSG/ISR substitution](https://github.com/advisories/GHSA-mcj8-r9mp-w47p).
- [sharp/librsvg](https://github.com/advisories/GHSA-wq5f-xc86-pv6w), [source-map-js](https://github.com/advisories/GHSA-68fv-2mgg-jv7q).
- PyJWT: [recursive payload](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-42vr-xj54-vc7v), [OKP identity](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-x33g-cr3x-6449), [changelog](https://pyjwt.readthedocs.io/en/stable/changelog.html).
