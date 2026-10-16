# SEC-001 — Submitted Python could reach API-host capabilities

- **Severity:** Critical. An authenticated user submitting a code-test answer could escape the intended execution boundary and read files accessible to the API process.
- **Status:** Fixed locally by disabling host execution of network-submitted Python; API push/deployment pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** `5098ded`; backend deterministic code checks and the legacy Python runner.

## Problem and impact

An AST denylist, restricted built-ins, child interpreter flags, a timeout and resource limits were treated as a sandbox. References reachable through an allowlisted Python module exposed host capabilities beyond that boundary. A child process still shared the host filesystem; filtering its environment did not isolate application files.

The independent reproduction created its own temporary canary and read only that file. Its sanitized result was:

```json
{"audit_rejected":false,"runner_status":"ok","read_own_host_canary":true}
```

This demonstrates a failed host isolation boundary. No real credential, user file, production record, shell command or external network target was accessed. The executable bypass payload is intentionally omitted.

## Safe reproduction

Use a local reviewed fixture and a temporary file created by the test itself. Confirm that the former audit accepted the fixture and the legacy runner could return the canary. For routine retesting, use the regression tests below instead of executing a bypass.

## Exact remediation

- `backend/app/engine/checks.py`: `run_check_async`, default `run_check`, and default `check_code_tests` return an unassessed code-check result before extraction, auditing or execution.
- `backend/app/engine/code_runner.py`: documents the runner as a trusted-fixture harness, not a security sandbox.
- `backend/app/engine/practice.py` and `backend/scripts/generate_questions.py`: keep runtime/generated answers on the non-executing boundary.
- Explicit `sandbox=False` is retained only for developer-reviewed local seed self-tests. No environment flag enables submitted-code execution.

Submitted source remains saved and available to the evaluator as text. A code answer is not falsely reported as passing tests that were never run.

## Verification

`backend/tests/test_security_code_execution.py` covers ordinary and indirect-module source through practice and interview HTTP routes using local JWT/model/store fixtures. All runner helpers are replaced by sentinels; a call to extraction, audit or either executor fails the test. Seven new cases passed in focused testing. Integration/deployment results belong in the run report.

## Remaining work

Deploy the API and verify its revision. Restoring execution requires a separate executor with no application credentials or host filesystem access, restricted networking, independent resource controls and a new adversarial review. These changes do not assert that historical exploitation did or did not occur.

Review relevant execution/access logs and assess rotation of potentially reachable database, service and provider credentials through a controlled owner handoff. No real secret was read or rotated during this review. Blocking future execution is not evidence that historical credentials were never exposed.

## References

[Python security considerations](https://docs.python.org/3/library/security_warnings.html), [subprocess documentation](https://docs.python.org/3/library/subprocess.html).
