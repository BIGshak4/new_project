# Security reviews and remediation

This directory records JobRun security reviews, confirmed findings, fixes, verification, and remaining work. It is an engineering record, not a claim that the application is free of vulnerabilities.

## Layout

- `runs/`: one dated Markdown report for each review, with scope, source revision, methods, results, and limitations.
- `findings/`: one Markdown record for each confirmed finding. Keep the same ID when retesting or reopening it.
- `finding-template.md`: the required structure for future findings.

Start with [the initial review](runs/2026-10-16-initial-audit.md).

## Finding register — 2026-10-16

The register contains 13 engineering records, including an installed-advisory bundle and an open hosted-setting action. It is not a count of 13 demonstrated production exploits. The source fixes are deployed, with exact revisions and HTTP verification recorded in the run report. SQL-only and automated coverage is distinguished from pending authenticated browser/Storage checks; the hosted password-protection setting remains open.

| ID | Finding | Severity | Current verification/status |
|---|---|---|---|
| [SEC-001](findings/SEC-001-untrusted-code-execution.md) | Submitted Python reached host capabilities | Critical | Mitigated in live API; isolated executor still required |
| [SEC-002](findings/SEC-002-concurrent-daily-quota.md) | Concurrent daily-allowance admission | Medium | API deployed; admission regressions pass |
| [SEC-003](findings/SEC-003-in-flight-interview-replay.md) | In-flight interview replay repeated model work | Medium | API deployed; replay preserves one answer/model call |
| [SEC-004](findings/SEC-004-caller-controlled-memory-growth.md) | Unknown IDs accumulated caches/locks | Medium | API deployed; bounded lifecycle/LRU regressions pass |
| [SEC-005](findings/SEC-005-retained-password-state.md) | Password retained by mounted login component | Medium | Both apps deployed; authenticated browser check pending |
| [SEC-006](findings/SEC-006-authentication-identity-races.md) | Auth/access response identity races | Low | Both apps deployed; lifecycle regressions pass; browser switch check pending |
| [SEC-007](findings/SEC-007-cross-origin-framing.md) | Missing cross-origin frame protection | Medium | Both live sites verified by HTTP headers |
| [SEC-008](findings/SEC-008-browser-role-maintenance-privileges.md) | Unneeded browser-role administration grants | Medium | Database deployed; 28 affected tables reduced to zero; metadata verified |
| [SEC-009](findings/SEC-009-answer-image-storage-allowance.md) | Missing aggregate answer-image upload allowance | Medium | Database deployed; 19 rollback assertions pass; Storage HTTP check pending |
| [SEC-010](findings/SEC-010-request-budget-bypass.md) | Rotating unverified headers reset limiter accounting | Medium | API deployed; budgets, memory and proxy trust tested |
| [SEC-011](findings/SEC-011-health-probe-stampede.md) | Concurrent health probes multiplied database work | Medium | API deployed; single-flight/deadline/cache tested |
| [SEC-012](findings/SEC-012-dependency-advisories.md) | Vulnerable locked npm/Python dependencies | Critical maximum advisory | All three apps deployed; dated npm/OSV scans clear |
| [SEC-013](findings/SEC-013-leaked-password-protection.md) | Hosted breached-password rejection disabled | Medium configuration gap | Open; project-owner action required |

## Finding register — 2026-11-08 full review

[The full review](runs/2026-11-08-full-review.md): backend, database rules, code execution, web app, deployment, repository and dependencies. Seven records; six fixed in one backend commit with regression tests, one an operator action.

| ID | Finding | Severity | Current verification/status |
|---|---|---|---|
| [SEC-015](findings/SEC-015-webhook-without-payment-keys.md) | Payment webhook accepted events signed with a built-in test secret | High | Fixed; 404 without payment keys; tests pass |
| [SEC-016](findings/SEC-016-padded-answer-numeric-checker.md) | Padded answer pinned a CPU in the numeric checker | High on the free host | Fixed; whitespace runs collapsed; timed test |
| [SEC-017](findings/SEC-017-image-pixel-cap.md) | Pictures decoded with no pixel cap | Medium | Fixed; header read first, 60 Mpx cap, decode off the loop |
| [SEC-018](findings/SEC-018-public-repository-tester-emails.md) | Repository public with tester e-mails and the solution bank | High (privacy) | Addresses scrubbed; operator action: make the repository private |
| [SEC-019](findings/SEC-019-production-guard-inactive.md) | Live server ran as staging; start guard only logged | Medium | Fixed; `ENV=production`, warnings separated from refusals |
| [SEC-020](findings/SEC-020-certifi-compromised-root.md) | Certificate bundle trusted a compromised authority | Medium (advisory Critical) | Fixed; certifi 2026.10.23 |
| [SEC-021](findings/SEC-021-code-runner-slots-shared.md) | One member could hold everyone's code-runner slots | Low | Fixed; slots counted per member |

Every record separates observed evidence, the exact change, verification and residual work. Final integrated test counts and deployment revisions are recorded once in the run report to avoid adding overlapping focused-suite counts.

## Rules for every review

Subsequent focused review: [2026-10-18 question-batch media compatibility](runs/2026-10-18-question-batch-media.md), with [SEC-014](findings/SEC-014-source-screenshot-compatibility-filter.md). This is a browser defense-in-depth finding; the server source-provenance boundary was already effective. Deployment status is tracked in that run report.

The [2026-10-21 thirteen-source intake](runs/2026-10-21-question-intake-media.md) extends SEC-014 to dated source ordinals and the current 86-image source inventory. It is a focused regression review, not a new full audit.

1. Record the tested revision, environment, and authorized scope before testing.
2. Reproduce suspected issues with synthetic accounts, files, and data. Do not probe other users' records, send real campaigns, incur AI charges, or stress production.
3. Distinguish a demonstrated exploit, an installed dependency advisory, excessive permissions, and a hardening recommendation. Do not inflate the finding count.
4. Add a regression test that fails for the original behavior where practical. Review the fix and run the relevant existing tests.
5. Record code, migration, deployment, and verification separately. A local patch is not a deployed fix; a skipped test is not a pass.
6. Verify changed database privileges/policies after application. Use metadata-only checks and rollback-only synthetic fixtures where possible.
7. Commit code and sanitized documentation together. Never commit credentials, tokens, signed URLs, real answers, personal data, or raw production dumps.
8. Retest relevant findings after changes to authorization, data storage, code execution, dependencies, providers, or deployment.

## Status vocabulary

- **Confirmed / open:** demonstrated issue without an effective mitigation.
- **Fixed locally:** patch and relevant tests exist; deployment is pending.
- **Mitigated:** the unsafe capability is blocked, with residual functionality or architectural work explicitly recorded.
- **Deployed / verified:** the relevant production component or database has been updated and the stated checks passed.
- **Operator action required:** an account/dashboard action cannot be completed by code changes alone.
- **Not reproduced / reviewed:** reviewed surface without a confirmed vulnerability; not a security certification.

Raw tool output stays in the ignored `backend/workdir/security-audit-2026-10-16/` directory. Only sanitized results belong here. Keep an English run report for every future review, even if it finds no new issue.
