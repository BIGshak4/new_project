# The pilot's users: what they did, how the system rates them, and role fit — 3 October 2026

Written for Shaked and Harel. Shaked asked, as part of the night check: look at what the users did, how we can rate
them, and how we can tell, for each one, which role fits them best. Everything below comes from a read-only pass over
the production tables (rolled back, e-mails not printed) and the engine's own fit calculation.

## 1. What the users did

| User | Answers graded | Days active | Follow-ups answered | Interviews | Model cost |
|---|---:|---:|---:|---:|---:|
| Shaked (own testing) | 21 of 39 started | 10 | 6 of 10 | 2 | $1.57 |
| Or | 3 of 3 | 1 (3 Oct) | 0 of 3 | 0 | $0.24 |
| Raz | 0 of 3 started | 1 (3 Oct) | 0 | 0 | $0.00 |
| Harel | 0 of 3 started | 2 | 0 | 0 | $0.00 |
| oryosef (TAU address, not on the list) | 0 | 0 | 0 | 0 | $0.00 |

- **Or** answered three questions on 3 October (priority encoder, decoder with enable, masked equality), all PARTIAL
  under the grader of that morning. He skipped all three follow-ups; they were the "compute all the examples" kind
  that is now gone. He also flagged a question as unclear, without a note.
- **Raz** opened three questions on 3 October (16:47, 19:45, 19:46) and left each without answering: no submission,
  no model call. Worth asking him why: the question, the length, or the page.
- **Shaked's** account holds test runs with deliberately weak answers (0 strong, 8 partial, 13 weak). It is not a
  user signal and is left out of the rating below.
- Itay and Or H. are on the list without accounts.

## 2. How the system rates a user today

Per skill, each graded answer updates a knowledge score and a confidence score; from those come a **level 1 to 5**,
a **status** (assessed, insufficient evidence, not assessed) and a **trend**. The progress page shows the level in
words (First steps … Expert), never a percentage. A skill is "assessed" after enough evidence, and evidence ages:
after three days without an answer the skill is scheduled for a refresh.

What that gives for Or after three answers:

| Skill | Level | Needed | Status |
|---|---:|---:|---|
| Multiplexers, decoders and encoders | 2 | 2 | assessed (3 answers, improving) |
| Boolean algebra and simplification | 2 | 2 | insufficient evidence (1 answer) |
| Combinational HDL and unintended latches | 1 | 2 | insufficient evidence |
| Truth tables and logic functions | 1 | 2 | insufficient evidence |

Overall: "Foundational", 1 skill assessed of the 25 in his plan, 35 XP. That is an honest rating of three answers:
it says what it has seen and no more.

## 3. Role fit: the machinery exists, the evidence does not yet

The engine already computes a **fit per job type** (`scorecards.target_fit`): for each of the six job types it takes
the role's skills re-weighted for that job, compares the user's assessed levels with the required levels, and gives
a fit score plus `known_coverage`, the share of the job's weight that has been assessed at all.

| User | Best fit today | Fit score | Coverage of the job's weight |
|---|---|---:|---:|
| Or | all six job types tie | 100 | 4 % to 7 % |
| Shaked (test data) | all six tie | 50 | 19 % to 23 % |

The scores tie across job types and mean nothing yet: Or has one assessed skill that every job type wants at
level 2, so every fit is 100 on 6 % of the evidence. The engine knows this: the interview report marks a fit
"partial" below 60 % coverage, and the number must not be shown as a verdict below that.

**So the rule for "which role fits this user" is:** show the fit per job type only once the assessed skills carry
at least 60 % of that job's weight; until then show what to answer next to find out. Both numbers come from the same
function, so this is a display rule, not new engine work.

## 4. How to get to a verdict quickly: the skills that carry the weight

The six job types share most of their heaviest skills. For a student, eight skills carry 44 % to 53 % of every job
type's weight:

| Skill | Weight share, by job type | Live questions that test it |
|---|---|---:|
| Combinational blocks (mux, decoder, encoder) | 5.6 % to 6.6 % | 9 |
| FSM state tables and diagrams | 6.0 % to 6.7 % | 2 |
| Boolean algebra | 5.1 % to 6.3 % | 3 |
| Latches and flip-flops | 5.1 % to 6.6 % | **0** |
| Setup, hold, max frequency | 5.9 % to 6.0 % (design, FPGA) | 2 |
| Moore and Mealy | 5.0 % to 5.5 % | **0** |
| Sequence detectors | 5.0 % to 5.5 % | 1 |
| Blocking and non-blocking | 5.0 % to 6.0 % | 1 |
| Debugging methodology (verification, embedded, software) | 5.6 % to 9.2 % | 1 |

What separates the job types is the tail: verification and FPGA lean on HDL coding and testbenches, embedded on
bit manipulation and binary arithmetic, software on debugging methodology, arrays and data structures, and on the
two behavioural skills (project walkthrough, structured communication) that have no bank question by design.

Two consequences:

1. **A ten-question diagnostic** across the shared heavy skills (one question each, plus one from each job type's
   tail) would take a new user to roughly half of every job type's weight in one sitting of 40 to 60 minutes. Then
   the fit per job type starts to separate. The weekly plan already leans toward the chosen job type; the diagnostic
   would be the first day of the plan rather than a new feature.
2. **Two of the heaviest skills cannot be assessed at all today**: latches and flip-flops, and Moore versus Mealy
   have no live question. Sequential HDL coding and state encoding are in the same situation further down. The 242
   generated drafts (`docs/question-bank-drafts.md`) hold 11 to 12 reviewed-shape drafts for each of them; loading
   even two per skill, after a review, removes the blind spots. That is Shaked's decision (the drafts stay aside until
   he says otherwise).

## 5. What I suggest, in order

1. **Ask Raz** what stopped him (two minutes, no code).
2. **A display rule for Harel**: on the progress page, a "which role suits you" card that shows the fit per job type
   only above 60 % coverage, and otherwise the three skills to answer next. A small backend route can return exactly
   that (`GET /v1/me/fit`: fit, coverage, meets-requirement share, core gaps and the next skills, per job type). About
   four hours on the backend, including tests; the card is Harel's.
3. **The ten-question diagnostic** as day one of the plan for a new user: the router already knows the weights, so
   this is a change to how the first day is filled, about half a day with tests.
4. **Load two reviewed drafts for each of the four blind skills**, when Shaked decides: review, move, load with the
   seed script (a data write that needs his approval).

Nothing in this document changes code; the per-user numbers are in the scratch output of the read-only pass and are
not stored anywhere.
