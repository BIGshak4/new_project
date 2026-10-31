# SEC-001 — Submitted Python could reach API-host capabilities

- **Severity:** Critical. An authenticated user submitting a code-test answer could escape the intended execution boundary and read files accessible to the API process.
- **Status:** Mitigated: the legacy API-host runner remains disabled for submitted code. Real learner execution was restored on 2026-10-31 through a separate authenticated Firecracker microVM executor; no learner source runs on the application API host. See [the execution implementation and verification record](../../docs/isolated-code-execution.md).
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
- `backend/app/engine/practice.py`, interview and duel services: compatible learner answers are checked through `backend/app/services/code_execution.py`, which sends a signed job to a separate executor. The legacy local runner is not used as a fallback.
- `backend/scripts/generate_questions.py`: generated source stays on the non-executing local boundary.
- Explicit `sandbox=False` is retained only for developer-reviewed local seed self-tests. No environment flag enables the legacy runner for HTTP input. `CODE_EXECUTION_ENABLED` controls only the separate isolated service.
- `apps/executor`: verifies an expiring Ed25519 ticket bound to the exact job, then boots a fresh nonpersistent microVM with denied networking, no application credentials or files, a dedicated non-sudo execution user and independent resource/deadline controls. Expected results stay outside the VM; control files and SDK write destinations are protected from candidate modification.
- The backend enforces attempt ownership and uses a backend-only ledger for idempotency, quotas and concurrency before dispatch. Browser input cannot select a testbench, compiler flags, destination, expected result or asserted check outcome.

Submitted source remains saved and available to the evaluator as text. Only verified server execution facts are supplied as check evidence. Compile success, untested execution, timeouts and infrastructure failure remain distinct from passed tests; AI failure does not erase a persisted execution result or create a grade.

## Verification

`backend/tests/test_security_code_execution.py` retains the regression boundary around the legacy runner: local JWT/model/store fixtures replace its helpers with sentinels, so submitted ordinary or indirect-module source cannot enter extraction, audit or local execution through practice/interview routes.

The 2026-10-31 verification record includes 3,135 offline backend tests (11 skipped), 322 frontend tests, 19 broker boundary/auth/adapter tests, 94 Linux compiler CI cases and **95 real microVM operator cases**. After the final quota-query change, 37 targeted quota/security/interoperability tests passed. The live VM cases include timeout, output limits, denied networking, protected controls/write paths and correct/wrong/syntax outcomes across all seven execution languages. Authenticated live API/website checks exercised Python pass/fail/compiler-error, SystemVerilog simulation and standalone C++ execution with stdin at phone width. Persisted execution evidence remained visible in Hebrew and English after a real AI-provider retryable failure; no AI-provider health claim is made. The exact dedicated QA account, membership and execution records were removed and zero remaining rows verified after sign-out; its temporary local credentials were deleted. These are bounded regression and integration checks, not proof against every possible isolation flaw. Full deployment, snapshot and evidence details are in the linked execution record.

## Remaining work

Keep the legacy local execution boundary disabled, maintain the isolated toolchain snapshot, and rerun adversarial and integration checks when changing the runner, its permissions or its image. The live executor and snapshot are recorded in the implementation report. These changes do not assert that historical exploitation did or did not occur.

Review relevant execution/access logs and assess rotation of potentially reachable database, service and provider credentials through a controlled owner handoff. No real secret was read or rotated during this review. Blocking future execution is not evidence that historical credentials were never exposed.

## References

[Python security considerations](https://docs.python.org/3/library/security_warnings.html), [subprocess documentation](https://docs.python.org/3/library/subprocess.html).
