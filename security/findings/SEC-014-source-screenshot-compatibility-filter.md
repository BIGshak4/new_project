# SEC-014 — New archive filenames bypassed the browser compatibility filter

- **Severity:** Low, defense-in-depth regression. The current API already excludes archive sources; no production disclosure was demonstrated.
- **Status:** Fixed locally; deployment verification pending.
- **Discovered:** 2026-10-18
- **Review:** [Question-batch review](../runs/2026-10-18-question-batch-media.md).
- **Affected revision and components:** Browser compatibility filter at `fb7a7f2`, exercised against the expanded question archive. The server provenance filter remains authoritative.

## Problem and impact

`visibleQuestionMedia` relied on a static source-filename list. A newly archived, dated source image was not in that list. A synthetic API-shaped response containing that image therefore retained it, even though archive source images must not be learner-facing media. Such responses are relevant to compatibility with older/cached resource payloads. This is an observed client filtering gap, not evidence that the current server issued a source-image URL.

## Safe reproduction

The existing full-bank media test failed for a dated PREP-022 intake image. The test uses synthetic nonworking resource URLs and now omits internal `source_path`, matching the public response shape. No real user account, signed URL, or live download was used.

## Exact remediation

- `apps/web/src/lib/question-media.ts` keeps the legacy denylist, compares it case-insensitively, and recognizes reserved bare PREP IDs and dated intake image filenames.
- Archive `sources/` provenance, when present in compatibility responses, is normalized across slash styles and withheld regardless of prompt/solution role.
- Authored descriptive diagrams and implementation files remain available.
- `apps/web/tests/question-media.test.ts` checks every current source image and authored asset, plus future IDs, dated variants, case differences and nested/Windows paths. The source count is derived from the bank.

No database authorization or storage policy was relaxed. The private question-media bucket was verified private during this publication.

## Verification

The prior filter failed the expanded full-bank regression. After remediation, all five focused media tests and all 195 web tests passed. TypeScript checking passed. Deployment status and revision are recorded in the run report after publishing.

## Remaining work

Client filename rules cannot infer provenance for arbitrarily named files. Keep server-side manifest provenance filtering authoritative, use the documented archive naming convention, and rerun the full-bank test whenever source or media formats change. Authenticated live-account compatibility rendering was not exercised.

## References

- [Server-side resource provenance tests](../../backend/tests/test_question_resources_language.py)
- [Browser compatibility regression tests](../../apps/web/tests/question-media.test.ts)
