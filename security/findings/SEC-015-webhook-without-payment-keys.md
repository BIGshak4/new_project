# SEC-015 — The payment webhook accepted events signed with a built-in test secret

- **Severity:** High. Any unauthenticated caller could set their own plan to Premium (50 questions a day instead of 30) or alter another user's billing row (cancelled, past due, foreign customer id) on the live server; a full paywall bypass the day `REQUIRE_PAYMENT` is switched on before real keys exist.
- **Status:** Fixed locally, deployed with the backend commit of 2026-11-08; verified by regression tests.
- **Discovered:** 2026-11-08
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** every revision since the billing work of 2026-10-20 up to `3b0d770`; `backend/app/services/billing.py` (`FakeStripe`), `backend/app/runtime.py`, `POST /v1/billing/webhook`.

## Problem and impact

Without Stripe keys the runtime builds `FakeStripe`, whose `secret` was the class constant `"whsec_test"`, and the webhook route verified signatures against it. The live server has no payment keys (payment is optional and the provider is still to be chosen), so the route accepted any event whose HMAC a caller computed with the public constant. The handler trusts `metadata.user_id` from the event. Observed in code and in the HTTP test that exercised exactly this path; not sent against production.

## Safe reproduction

`tests/test_security_review_2026_11_08.py::TestWebhookWithoutKeys` and the HTTP case in `tests/test_billing.py` (`test_billing_routes_and_the_webhook`): an event signed with the former constant is a 404 on a server without keys.

## Exact remediation

`FakeStripe(secret=None)`: no signing secret unless one is injected; `verify` raises `not_found` ("payment is not set up on this server") without one, so the route does not exist for the outside world until real keys arrive; `sign` refuses without a secret. Tests construct `FakeStripe(secret="whsec_test")` explicitly. `Settings.production_problems` now also refuses `REQUIRE_PAYMENT=true` without `STRIPE_SECRET_KEY`.

## Verification

Before: the HTTP test accepted a signed event on the key-less server (200). After: 404 with and without a forged signature; with an injected secret the signed path is 200 and the unsigned 422. `tests/test_billing.py` 14 passed.

## Remaining work

When the Israeli gateway is chosen the webhook moves to its signature scheme; the same rule applies: no secret, no route.

## References

Stripe webhook signature scheme (`t=…,v1=…`, HMAC-SHA256 over `t.payload`).
