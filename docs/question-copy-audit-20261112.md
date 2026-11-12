# Question copy audit — 12 November 2026

The checkout was synchronized with `git pull --rebase` before the audit, against baseline `6559796`. The work covers the current website banks in Hebrew and English, including answers, hints, supplementary learner material, multiple-choice options and explanations.

| Bank | Reviewed inventory | Records with copy corrections |
| --- | ---: | ---: |
| Interview questions | 340 (30 examples and 310 preparation questions) | 141 |
| Fundamentals | 500 cards | 149 |
| Multiple choice | 2,500 active variants and 40 retained draft records | 690 |

Interview coverage combines full-field typography/language screening with contextual review of flagged passages and the example-bank texts. Fundamentals received a paired reading of all 4,000 localized title/prompt/answer/takeaway fields. Multiple-choice review covered every distinct generated wording template, all preserved literal records, and screening of all 30,480 localized fields. This is an agent editorial audit, not a new human technical approval.

Corrections include missing spaces, repeated words, Hebrew agreement, English singular/plural forms, ambiguous wording and ordinary English table headings inside Hebrew answers. Literal bracket examples remain intentional inputs. Technical names, formulas, half-open intervals, source code and signal names retain their meanings; identifiers such as `Shuffle100`, `Random5`, `have0` and `borrow0` have explicit regression coverage.

All IDs, topics, answer indexes, numerical models, source code, grading controls and difficulty scores remain unchanged. Difficulty fingerprints were rebound only after comparing the changed question revisions. One stale resource-hint alias now matches its existing primary hint, spelling “modulo 3” as “modulo three.” Five previously attached solution-review records cease to match their exact reviewed content and are therefore invalidated; the original attestation registry is unchanged. Frozen historical tests reconstruct prior text through exact before/after hashes rather than replacing their old expected hashes.

The real `StudyText`, `BidiText` and technical-material renderers passed 414 browser checks. The audit covers 54,640 source string fields, deduplicated to 34,251 distinct language/rendering cases, at desktop and simulated mobile widths. Each viewport checks both content languages, text preservation, paragraph direction and LTR isolation. Independent glyph-position checks cover nested brackets, half-open intervals, literal malformed-bracket exercises and formatting boundaries. Screenshots were inspected. This is an isolated renderer test, not a physical-phone or authenticated production-session test. A compact [renderer report](../reports/question-renderer-audit-20261112.json) records the coverage.

Validation includes the frontend test suite (452 passes), type checking and production build; 28 targeted typography/difficulty/copy-sync checks; independent Fundamentals and multiple-choice arithmetic/model checks; source-generator reproduction; and frozen historical-content checks. Detailed bank evidence is in [the Fundamentals audit](../reports/fundamentals-copy-audit-20261112.json) and [the quiz audit](../reports/quiz-copy-audit-20261112.json).

The live update uses a full backup of all 340 question rows, 680 translations and their skill links, outside Git. A copy-only plan contains 141 changed questions with no preimage conflicts or disallowed changes. All 19 guarded transactions passed rollback dry runs and were then committed, starting with one canary. A complete readback matched every updated question column, both translation rows and all skill links against the reviewed plan; only trigger-maintained timestamps and serving counters were excluded. The SQL updates only copy and revision metadata, preserves learner history and difficulty, and rejects concurrent content changes.
