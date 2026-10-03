# The question drafts: what is in them and how to use them — 3 October 2026

Written for Shaked and Harel. The bank that students practise on today has 67 questions (the 30 originals and
Harel's 37 prepared ones). On 30 September Shaked asked for a large bank of hardware and software questions; on
1 October he decided the new questions stay **aside as an option**, not loaded. This document describes that set.

## What exists

`backend/seeds/question_drafts/generated_bank.json`: **242 draft questions** for 26 skills, drafted by Claude Opus 5.5
with `scripts/generate_questions.py` and checked automatically. They sit outside `seeds/questions`, which the loader
reads, so nothing reaches the database unless someone moves a reviewed question there and runs the loader.

Every draft has, in Hebrew and English: a title, a self-contained prompt, what a complete answer contains, a full
reference solution, three hint levels, two to four named common mistakes with explanations, other valid approaches,
and a rubric of three to five weighted criteria. Status `in_review`, origin `generated`, reuse `pending_review`.

| Measure | Value |
|---|---|
| Drafts | 242 (0 invalid by the loader's rules, 0 key clashes with the live bank) |
| With an automatic check | 151: 92 Python test cases, 43 truth tables, 16 numbers with units |
| Difficulty (1–10) | 2: 7 · 3: 48 · 4: 46 · 5: 68 · 6: 49 · 7: 16 · 8: 8 |
| Formats | code 93 · HDL 42 · truth table 33 · construct 23 · short answer 20 · explain 16 · waveform 15 |
| Flagged for a closer look | 3 (below) |
| Cost | about $55 of model time across the runs |

## Coverage per skill

| Skill | In the live bank | Drafts |
|---|---:|---:|
| Boolean algebra | 3 | 9 |
| MUX, decoders, encoders | 9 | 2 |
| Latches and flip-flops | 0 | 11 |
| Counters | 2 | 10 |
| State diagrams and tables | 2 | 10 |
| Sequence detectors | 1 | 11 |
| Moore and Mealy | 0 | 12 |
| Setup, hold, max frequency | 2 | 9 |
| Blocking / non-blocking | 1 | 11 |
| Truth tables | 1 | 11 |
| Binary arithmetic and overflow | 6 | 6 |
| Number representation | 0 | 10 |
| Registers and shifters | 1 | 11 |
| Reset strategies | 0 | 12 |
| Edge detection | 2 | 9 |
| Control FSMs and handshakes | 2 | 10 |
| Combinational HDL, latches | 1 | 10 |
| Sequential HDL | 0 | 12 |
| Bit manipulation | 5 | 7 |
| NAND/NOR-only | 1 | 11 |
| Clock domain crossing | 1 | 8 |
| State encoding | 0 | 9 |
| Testbench basics | 0 | 12 |
| Arrays and search (software) | 5 | 7 |
| Data structures (software) | 8 | 3 |
| Code debugging (software) | 1 | 9 |
| Debugging methodology, project walkthrough, structured explanation, trade-off reasoning | 1 | 0 (behavioural; not drafted on purpose) |

Seven skills that had **no question at all** in the live bank now have 9 to 12 drafts each: latches and flip-flops,
Moore and Mealy, number representation, reset strategies, sequential HDL, state encoding, testbench basics.

## How the drafts were checked

1. **The loader's rules** on every draft: the shape (rubric and skill weights sum to 1, three hints, one primary skill,
   every named mistake explained in both languages), the skills and tips exist, and the automatic check accepts its
   own correct answers and rejects its wrong ones. Code examples run in the sandbox with a time limit, since one draft's
   deliberately broken code really did loop forever.
2. **The judge** (Opus 5.5) graded each draft's own reference solution as if a student had written it. A reference
   that is not graded STRONG means the question or the reference is unclear; those are flagged, not dropped.
3. About one draft in five was rejected by step 1 during drafting (mostly checks whose own examples disagreed with
   the spec); `generated_bank.rejected.json` beside the file keeps them for inspection.

## The three flagged drafts

All three are the same kind of problem: the reference reasons correctly but the number or expression the automatic
check expects does not match what the reference states.

- `gen-number-representation-sign-extend-and-add-offset`: the check on `r` disagrees with the reference's own value.
- `gen-clock-domain-crossing-two-flop-synchronizer-mtbf-budget`: the MTBF in years (17 in the check vs 1493 in the text).
- `gen-fsm-state-encoding-gray-fsm-safe-next-state`: the checked expression for N1 differs from the safe one on the
  illegal codes 101 and 111.

Fix the check or the reference before using any of them.

## How to use them, when Shaked decides to

Nothing below happens without his decision.

1. **Review.** An engineer reads a draft with the checklist in `backend/seeds/questions/README.md` (technical
   correctness, rubric, hints, mistakes, the check, Hebrew/English parity, provenance) and sets `parity_checked`.
2. **Move** the reviewed questions into a file under `backend/seeds/questions/` (for example `generated_reviewed.json`).
3. **Load** with `uv run python scripts/seed_db.py --check`, then `seed_db.py`, which is a database write and needs
   Shaked's approval. Set them to `trial` with `scripts/question_status.py` to serve them to pilot users.

A review page would make step 1 a click instead of a JSON edit (item 12 of the backend roadmap).
