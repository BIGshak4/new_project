# Preparation collection integration and review

## Scope and preservation

Pulled/rebased `master` from `f245273` to `2c4a578` without conflicts. Before the pull, the complete untracked preparation archive was copied to an external ZIP with a SHA-256 manifest (307 files). The original archive is unchanged and is now included in version control, excluding generated Python caches.

The live database now contains **67 questions: the existing 30 plus all 37 prepared questions**. Import uses stable `prep-` keys and preserves IDs. A full content snapshot was saved outside the repository before import. A read-back comparison confirmed every column of all 30 existing question rows is unchanged. No learner records, attempts, answers, uploaded drawings, or progress were deleted.

All **120 referenced assets (92 PNG images and 28 code files)** were uploaded to the private `question-bank-media` bucket and fetched back to verify their SHA-256 hashes. The manifest includes every original and alternative PNG in the archive. Generator scripts, Markdown authoring records, and other source files are preserved in Git; the site exposes question/solution material, not personal hint-delivery or chat history.

## User experience

- Same library and practice flow, with discipline/topic/company filters and searchable original PREP identifiers.
- Source company claims are visibly marked **not independently verified**, separate from candidate sightings and their counts.
- Hebrew and English questions and references; three progressive hints per language. Existing Hebrew hints are preserved, with English translations in a separate editorial file. PREP-002 had no reference answer: its proposed bilingual answer is an explicit editorial addition awaiting human review.
- Original question figures are available before answering. Solution diagrams, implementation-file links, technical explanations, and the full technical JSON export require an owned attempt with recorded reference exposure.
- Images use expiring, signed URLs. The bucket has no anonymous read policy. A refresh control renews expired links.
- Long answers support Markdown, code fences and tables. Technical fields that exist only in Hebrew remain labelled honestly; they have not all been professionally translated.

## Assessment boundaries

The archive contains no calibrated difficulty values. The UI says **Unrated**, rather than inventing a difficulty. Internally the existing engine requires an integer, so 5 is a compatibility value only. Each new question has `assets.assessment_ready=false` and `difficulty_status=unrated`.

These questions support manual practice and provisional qualitative feedback. They earn **no XP, no mastery evidence, no skill-state update, no automatic plan completion**, and are excluded from adaptive selection and mock interviews. The provisional rubric weights correctness/reasoning/verification at 55/30/15; this is not a validated rubric for every question. Human review must replace/calibrate it where appropriate.

Curated source question images reach the evaluator separately from the candidate's images. If a required source image cannot be read and hash-verified, the answer remains saved and evaluation can be retried; the evaluator must not guess the unseen diagram.

## Import and maintenance

1. Author/edit `interview_preparation/questions.json` and its original assets.
2. Keep translations and explicit editorial additions in `backend/seeds/preparation_editorial.json`.
3. Run `python scripts/build_preparation_bank.py` from `backend` (or any directory).
4. Run `python scripts/seed_db.py --check`.
5. Run `python scripts/import_preparation_bank.py` for a rolled-back dry run; add `--apply` only for the approved import.
6. Commit source, compiled seed, manifest, and frontend/backend changes; pull/rebase before pushing. Both hosting services must deploy the matching revision.

The focused importer updates only prepared questions. It uploads and verifies immutable content-addressed assets before committing content changes. Re-importing identical content preserves IDs and review state. Changed prepared content, including diagrams, changes its hash and resets review as the existing seed policy requires.

To approve a question for adaptive assessment, review correctness and image/text parity, validate both languages and hints, set a calibrated difficulty and rubric, then change `assessment_ready` and `difficulty_status` in the compiled source workflow. Do not merely change its database status to `published`; study-only safeguards are separate. Replace the builder's explicit provisional defaults with per-question review metadata when beginning publication.

## Review of Shaked's recent work

Strong foundations: durable idempotent submissions, retry/recovery, ownership checks, grade-first/background prose, mock interviews, goals and daily plans, company sightings, and a substantial regression suite. Those are relevant product improvements, not just cosmetic additions.

Issues addressed here:

- The question-report endpoint existed but its production table was missing. Applied the existing `question_report` migration.
- The old landing page said every question had been checked by an engineer. Replaced that with accurate pilot/review wording and updated the bank count.
- The frontend had no resource viewer for this archive and the engine had no explicit uncalibrated-content boundary; both are now implemented.

Remaining priorities / proposals, not a prescribed solution:

1. **Human content review:** validate each solution, circuit, translation, difficulty, primary skill, and question-specific rubric. Existing verification scripts are evidence to examine, not a replacement for human review. PREP-002's editorial answer particularly needs confirmation.
2. **One runtime content source:** practice loads full questions from the database; some interview/planning/enrichment paths use the bundled catalog plus database publication state. A database-only edit can diverge from the deployed catalog. Consider loading all runtime content from the database, or enforcing a versioned import + matching deploy as one release.
3. **Migration deployment check:** a passing build does not apply Supabase migrations. Add a release check for required migrations/tables; the missing report table demonstrates why.
4. **Representative evaluation set:** Shaked's 13-answer model comparison and five-answer latency sample are useful early evidence, not broad validation. Add hardware diagrams, valid alternative solutions, ambiguous questions, incorrect/confident answers, and Hebrew/English pairs with expert labels. Track correctness, latency and cost separately.
5. **Real capacity evidence:** the documented 10/50-user tests use simulated model latency. Run a small, budgeted real-provider concurrency test before a wider pilot. Do not present simulated load results as real-model capacity.
6. **Review hash for older content:** prepared-question hashing now includes diagrams/assets. The older example-bank hash still omits some assets such as shared code. Extend it with a controlled review migration rather than silently invalidating all reviewed questions.
7. **Content provenance before a public launch:** source company labels and pending reuse review should remain transparent. Keep this pilot gated while deciding which source material can be published.

## Design direction proposed, not applied as a wholesale redesign

Reference: https://voltagelearning.com . Borrow clear engineering positioning and direct routes into practice, not its black PCB background, teal typography, yellow calls to action, or assets.

Suggested direction: an engineering exercise notebook — warm off-white paper, white question sheets, charcoal text, thin rules, restrained terracotta actions, real circuit diagrams and generous readable typography. A light compact header would reduce the current navy dominance. Keep the working code/circuit editors central and avoid adding more dashboard decoration.

Independent public-landing critique: 23/36 on the applicable usability heuristics (signed-in practice was not part of that score). Main concerns were unclear invitation/access recovery, heavy navy dominance, equal-weight metric cards, and mixed decorative idioms. Automated design scan: 14 findings (13 warnings, 1 advisory), several useful/intentional status and progress treatments; these are review leads, not 14 confirmed defects. Existing design documentation predates the current Workbench visual system; no unrelated design-system rewrite was performed.

## Verification

- 805 offline backend tests passed; 56 frontend tests passed; TypeScript and production build passed.
- Added archive/asset fidelity, private-resource ownership/exposure, unsafe-path rejection, source-image separation, missing-image recovery, and study-only evidence tests.
- Live database read-back: 67 loadable questions, 37 imported, all 30 pre-existing rows unchanged.
- Signed all 120 stored assets successfully and verified source-image bytes through the production storage connection.
- Full long-running live suite and expert judgement of real-model feedback are separate from these checks; no claim that all 37 solutions are already technically approved.
