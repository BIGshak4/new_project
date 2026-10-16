# SEC-010 — Rotating unverified tokens bypassed request limits and grew limiter state

- **Severity:** Medium. An unauthenticated caller could reset request accounting with arbitrary Authorization values and retain fresh per-token buckets, increasing API processing/memory use.
- **Status:** Fix deployed, including restricted proxy trust; API source revision `9a264cf` verified. Actual Uvicorn proxy-chain regressions passed locally; no production spoof/load test was performed.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; `backend/app/main.py::StreamLimits`.

## Problem and impact

The middleware selected a bucket from any offered Authorization header before verification. Rotating junk tokens avoided a single token allowance. Its cleanup threshold removed only expired buckets, so many fresh headers could exceed the intended memory bound. A local mock peer sent eight distinct junk headers and was admitted eight times; 100 fresh bucket keys remained in memory despite a test capacity of four.

## Safe reproduction

Call the ASGI middleware around an inexpensive local responder with a fixed synthetic peer address. Vary the offered Authorization/X-Forwarded-For strings and inspect response statuses and container size. Do not generate production traffic.

## Exact remediation

`backend/app/main.py` adds an independent resolved-peer address allowance, retains the offered-token allowance, and enforces a hard LRU bucket capacity. Defaults are 600 requests/minute per offered token/address layer, 1,800/minute per resolved network peer and 10,000 total buckets per process. Raw caller-supplied forwarding headers are not interpreted by this middleware.

Only inexpensive query-free GET/HEAD `/health` is exempt; database-probe health requests consume the budget.

`backend/Dockerfile` also removes Uvicorn's universal `--forwarded-allow-ips='*'` trust. The default trusts loopback and RFC1918 private proxy ranges only. A forged left-hand forwarding prefix must not become the resolved rate-limit identity merely because another proxy appended its own address. This is a confirmed local deployment-stack weakness; production header spoofing was not attempted.

## Verification

`backend/tests/test_security_request_limits.py` demonstrates that a fixture network allowance of five accepts the first five rotating-token requests and rejects the next three, regardless of supplied forwarding text. Fresh churn respects a capacity of four. Additional cases verify cheap-health exemptions versus probe requests.

Three additional cases wrap the limiter in Uvicorn's actual `ProxyHeadersMiddleware`: the old wildcard admitted all six rotated-prefix requests, while the restricted chain admitted three and rejected three at the configured limit. An untrusted public peer cannot forge identity/scheme, and a trusted private peer can preserve the valid client/HTTPS scheme. These regressions test the deployed middleware composition rather than assuming the ASGI client was already trustworthy.

## Remaining work

Review infrastructure proxy trust so the ASGI resolved address represents the intended caller boundary. Budgets are per process and may be shared by users behind a NAT; they are not a distributed limiter, WAF or DDoS guarantee. Tune with actual usage and preserve hard memory bounds.

## References

[Uvicorn proxy/header settings](https://www.uvicorn.org/settings/#http), [ASGI HTTP connection scope](https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope), [Render proxy-trust guidance](https://render.com/articles/fastapi-production-best-practices#how-do-you-configure-proxy-trust-security-and-routing).
