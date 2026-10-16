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

Every record separates observed evidence, the exact change, verification and residual work. Final integrated test counts and deployment revisions are recorded once in the run report to avoid adding overlapping focused-suite counts.

## Rules for every review

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
