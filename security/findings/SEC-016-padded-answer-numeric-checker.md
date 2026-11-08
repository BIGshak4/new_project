# SEC-016 — A padded answer pinned a CPU in the numeric answer checker

- **Severity:** High on the free single-CPU host (a few requests stall the whole API); Medium elsewhere. Prerequisite: a pilot member and a question with a numeric check and named outputs (at least one human-reviewed question has that).
- **Status:** Fixed locally, deployed with the backend commit of 2026-11-08; verified by a timed regression test.
- **Discovered:** 2026-11-08
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** `backend/app/engine/checks.py` (`_CLAUSE_END`, `locate_named_value`), on the submit path before any model call.

## Problem and impact

`_CLAUSE_END`'s alternation `\s+(connective)\s+` backtracks quadratically over a long run of blanks, and the scan restarts at every match of every configured output name. Measured on a copy of the pattern: 8,000 spaces cost 2.6 s per scan; an answer at the 20,000-character cap with twenty name mentions costs over a minute of CPU. The check runs in a worker thread, so the event loop survives, but the thread pool and the single CPU do not. No model cost is incurred, so the per-day cap does not limit it.

## Safe reproduction

`tests/test_security_review_2026_11_08.py::TestPaddedAnswerAgainstTheNumericChecker`: a 19,000-blank answer must locate its value in under half a second.

## Exact remediation

`_collapse_whitespace` runs first: every run of two or more whitespace characters becomes one space, or one newline when the run had one (newlines still end a clause). Linear, and the located values are unchanged (`tests/test_checks.py` green).

## Verification

Before: 2.6 s per scan at 8,000 blanks. After: under 1 ms; both new tests pass; `tests/test_checks.py` unchanged and green.

## Remaining work

Other regular expressions over learner text were read and found linear; a future pattern with nested quantifiers over `\s` or `\w` runs should be benchmarked the same way.

## References

Catastrophic backtracking in backtracking regex engines (OWASP ReDoS).
