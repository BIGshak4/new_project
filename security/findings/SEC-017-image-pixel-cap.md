# SEC-017 — Pictures were decoded with no pixel cap

- **Severity:** Medium. A pilot member's 5 MB flat PNG declaring 13,000 × 13,000 pixels decodes to about 700 MB and kills the API worker (512 MB on the free plan), repeatably; the decode also ran on the event loop.
- **Status:** Fixed locally, deployed with the backend commit of 2026-11-08; verified by a regression test with a crafted header.
- **Discovered:** 2026-11-08
- **Review:** [2026-11-08 full review](../runs/2026-11-08-full-review.md)
- **Affected revision and components:** since the picture bound of 2026-11-02; `backend/app/services/storage_images.py` (`shrink_image`, `StorageImageFetcher`), `backend/app/services/question_resources.py`.

## Problem and impact

Only bytes were capped (5 MB upload limit, sniffed MIME). Pillow's default refusal starts at twice its 89 Mpx limit; between the two it only warns. `exif_transpose` decoded the whole bitmap before the size was read, synchronously inside an async fetcher.

## Safe reproduction

`tests/test_security_review_2026_11_08.py::TestPixelCap`: a valid PNG whose header declares 13,000 × 13,000 (one grey pixel of data) must be dropped in under half a second.

## Exact remediation

`MAX_IMAGE_PIXELS = 60,000,000` (phone photos are 12-50 Mpx): the header is read before any decode and a larger picture returns `None`; Pillow's own `DecompressionBombError` (above 120 Mpx, raised at `open()`) is mapped to the same `None`. The answer-image fetcher skips such a picture; the question-figure path returns "no assessment" rather than guessing. Both now run the shrink in a thread.

## Verification

Before: the crafted header reached the decoder (Pillow refused it only because it was above 2× its default; one declaring 100 Mpx would have decoded). After: dropped from the header; ordinary pictures still shrink; `tests/test_judge_warm.py` green.

## Remaining work

Storage still accepts the upload (5 MB, own folder); it is only never decoded. A per-member storage allowance is SEC-009's residual.

## References

Pillow `Image.MAX_IMAGE_PIXELS` and `DecompressionBombError`.
