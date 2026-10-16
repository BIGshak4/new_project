# SEC-003 — Replaying an evaluating interview answer could repeat model work

- **Severity:** Medium. An authenticated caller could repeat charged evaluation work and replace the payload associated with an accepted retry identity.
- **Status:** Fixed locally; API deployment pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; interview answers handled by independent service instances.

## Problem and impact

A different retry key was refused while a turn was evaluating, but the same key could enter evaluation again through another worker. In a local two-instance fixture, replaying the key invoked the evaluator twice and allowed replacement answer text. An idempotency key must identify the already accepted operation, not permission to repeat it.

## Safe reproduction

Block a scripted evaluator with a local event. Once the first instance has saved the original answer as evaluating, submit the same key and different text through a second instance. Inspect the stored answer and scripted call count, then release the event.

## Exact remediation

`backend/app/services/interview_service.py::answer` now returns the saved evaluating turn for a matching key without replacing its text or calling the model. A different key remains a conflict. Existing optimistic session revision checks still protect simultaneous workers that both read the earlier open state before either persists admission.

## Verification

`backend/tests/test_security_api_abuse.py::test_same_key_in_flight_interview_replay_preserves_answer_and_calls_model_once` verifies one evaluator call, the original stored answer and a replay response still marked evaluating. No real provider or production request was used.

## Remaining work

Deploy the API. Preserve both idempotency checks and optimistic persistence when changing the background evaluation architecture. Retry identities do not authorize another user to access an interview; ownership remains independently enforced.

## References

See the answer/replay regression and `backend/app/repo/sessions.py` for the session revision compare-and-set boundary.
