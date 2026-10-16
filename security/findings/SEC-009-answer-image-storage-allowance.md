# SEC-009 — Direct answer-image uploads lacked an aggregate parent allowance

- **Severity:** Medium. An authenticated user could bypass the four-image UI limit and accumulate objects under an owned answer resource, increasing storage consumption and cost.
- **Status:** Database guard deployed and metadata/rollback-fixture verified on 2026-10-16; real Storage HTTP validation pending.
- **Discovered:** 2026-10-16
- **Review:** [Initial audit](../runs/2026-10-16-initial-audit.md)
- **Affected baseline:** Live `practice-answer-images` Storage persistence before the new guard.

## Problem and impact

Client selection limits and per-file size/MIME limits do not impose an aggregate upload allowance. A caller can bypass the UI and use the Storage API directly. Ownership/private-bucket protections existed; this finding concerns additional storage consumption under otherwise owned resources, not reading another user's files.

## Safe reproduction

Use rollback-only temporary parent/object tables and the production trigger function with schema references redirected into the temporary fixture. Never upload hundreds of real files or modify existing user records to test a quota.

## Exact remediation

`supabase/migrations/20261016171110_bound_answer_image_storage_quota.sql` installs `jobrun_private.limit_answer_images()` before Storage object insertion/locator changes:

- Validates canonical owner/parent/UUID raster locators and matching, open parent ownership.
- Locks the parent row, then counts its objects: maximum **24 per practice attempt** and **200 per interview**, allowing multiple turns/replacement headroom.
- Checks insertion, rename and moves into the bucket; permits unchanged-locator metadata finalization.
- Uses an empty search path and qualified objects; browser roles cannot execute the private function directly. Existing Storage RLS remains the caller-authorization boundary. The persistence trigger does not assume the internal Storage writer has an Auth subject.

## Verification

Production migration application succeeded; the enabled trigger and deployed function body matched the reviewed source. **19 synthetic SQL assertions** passed before and after application and rolled back. Cases include exact capacities, independent parents, forged owners, missing/closed parents, invalid locators/extensions, rename/bucket-move bypasses and metadata finalization. `backend/tests/test_security_storage_quota.py` contains the reusable fixture.

## Remaining work

Validate ordinary browser/Storage HTTP upload and replacement flows using an authorized disposable account. Live parallel uploads were not stress-tested. This is a per-parent guard, not a lifetime user/global storage budget or orphan-cleanup system; retention and deletion need continued monitoring. No existing image was deleted by this migration.

## References

[Supabase Storage access control](https://supabase.com/docs/guides/storage/security/access-control), [PostgreSQL row locks](https://www.postgresql.org/docs/17/explicit-locking.html#LOCKING-ROWS).
