# Scale and security review — 14 November 2026

Requested by Shaked: "a full verification ... for a large scale of users at least 5000 ... check what are the
weaknesses in the system (cyber and hacking ones) and fix them so we will keep the data safe".

## Scope, revision, method

- **Revision reviewed:** `master` at `6bc639c` plus the working tree of this pass. The branch `production` (head
  `01ef984`, seven commits not on `master`) was read for its deployment files only.
- **What is live, verified today:** `https://muxijobrun.com` and `https://api.muxijobrun.com` run the `production`
  branch on a DigitalOcean server (its `/health` reported `source_revision 01ef984`). Render and Netlify still run
  `master` against the same database. **The fixes below are on `master`. They reach the live site only when
  `master` is merged into `production`.**
- **Method:** five independent read-only reviews (authentication and the API; the database, secrets and
  deployment; untrusted input, cost and the judge; the web app; the database layer at scale), each verifying its
  findings by reading the full code path and, where cheap, by a local script on the in-memory store with a scripted
  model. Every fix was then written and tested separately from the review that found it.
- **Not done:** nothing was tested against production; no real model was attacked; hosted settings (Supabase Auth,
  GitHub branch protection, package visibility, the Render and DigitalOcean environments) could not be read.
- **Not verified on the real database:** two new reads (`attempts.reference_exposed` and
  `events.model_cost_since`) are covered by the in-memory tests only. Both run inside savepoints and fail safe (a
  failed lookup pays the coins; a failed budget read refuses nobody). The live suite was not run in this pass.
- **Two disclosed slips, both read-only:** a reviewer's first local script, and my first load-test runs, fetched
  question figures from the production storage bucket, because the in-memory runtime still reads the storage key
  from `backend/.env` (`fetch_question_images`). No user data, no database, no model call. Both harnesses now stub
  the fetcher.

## Finding register

Records are the sections of this report (one file per finding was not kept for this pass).

| ID | Finding | Severity | Status |
|---|---|---|---|
| SEC-022 | A 6 KB drawn circuit made the server build gigabytes of text | High | Fixed on master; tests pass |
| SEC-023 | Blanks after `<` in an answer froze the whole API for up to a minute | High | Fixed on master; timed test |
| SEC-024 | One 22 KB picture cost about 600 MB of memory (SEC-017 incomplete); padded pictures sent whole | High on a small host | Fixed on master; tests pass |
| SEC-025 | Coins paid for a question whose reference the member had already revealed | Medium (high once coins carry money) | Fixed for practice and interviews; judged duels open |
| SEC-026 | No limit on paid judge calls for one answer the model keeps failing on | Medium (cost) | Fixed for practice and interview turns; judged duels and the report narrative open |
| SEC-027 | The duel quiz's answer key could be collected through the practice rounds | Medium | Mitigated (150 rounds a member a day); separate pools and the public copies open |
| SEC-028 | Judge warm-up calls outside every allowance, repeatable for ever | Medium-low (cost) | Fixed on master; tests pass |
| SEC-029 | No ceiling on what one member's model calls cost | Hardening (cost) | Added: monthly budget, ₪15 by default |
| SEC-030 | The new deployment needs public container images, which carry the solution bank | High | Open: Harel and Shaked |
| SEC-031 | Browser roles can write rows without limit (`question_resume_visits`, `user_document`, `user_profile`) | Medium | Migration written and dry-run; **not applied**, waits for approval |
| SEC-032 | Founder rights sit on an allow-list row for a shared mailbox | Medium | Open: needs a check and a one-row change with approval |
| SEC-033 | One database, two live backends on two diverged branches; a push is a deploy | Medium | Open: operator |
| SEC-034 | Retiring Netlify would leave claimable sites in the login allow-list | Medium, conditional | Open: do before the sites are deleted |
| SEC-035 | The numeric and truth-table checkers are still quadratic on a crafted answer | Medium | Open: the fix changes a grading path, Shaked decides |
| SEC-036 | Web app: sign-in by a crafted link, drafts left after sign-out, unencoded ids, design pages in production | Low | Open: Harel |

## Fixed in the backend on master

### SEC-022 — a drawn circuit that derives gigabytes

`engine/circuit_text.py` derives a Boolean expression for every signal. A chain of gates whose inputs are all wired
to the previous gate multiplies the expression at every stage: 22 two-input gates in a 6,355-byte request derived
25 million characters, 30 gates about 6 GB, and the schema allows 100 parts. One request could kill the only API
process; tuned lower it produced a very large judge prompt on every answer.
**Change:** a derived signal longer than 2,000 characters (the length the checker reads anyway) is "not derived",
like any other circuit the deriver cannot follow. **Test:** `TestAdversarialInput.test_a_gate_chain_no_longer_derives_megabytes`.

### SEC-023 — the judge's tag filter was quadratic, on the event loop

`evaluator.neutralize` runs on every judged answer and again for the feedback card. Its pattern allowed any number of
blanks on both sides of the slash, so `<` followed by a few thousand blanks was tried every possible way: 4,000 blanks
3.3 s, the 20,000-character cap about a minute, twice per answer, with every other request waiting.
**Change:** the blanks are matched possessively (taken once, never given back), so any amount of padding is still
neutralised and the worst inputs take a few milliseconds. **Test:** `test_blanks_after_an_angle_bracket_do_not_stall_the_judges_prompt`.

### SEC-024 — pictures: memory and padding

The 60-megapixel cap of SEC-017 still cost about 600 MB for a 22 KB flat PNG and 490 MB for a JPEG, more than the
whole server had on the free host. A picture small in pixels but padded to 5 MB was sent to the model unchanged.
**Change (`services/storage_images.py`):** a JPEG up to 24 Mpx, decoded at reduced size by the decoder itself; other
formats up to 12 Mpx; one decode at a time on a thread of its own; a picture over 1 MB is always written again
(colours untouched when it is already small in pixels), and megabytes that cannot be decoded are dropped. **Tests:** `TestPictures`.

### SEC-025 — coins after the reference was revealed

The rule "reference seen, no coins" looked only at the attempt in hand. A member could reveal the solution on one
attempt and open a new one on the same question, or reveal it in practice for the question an interview was asking
(the interview view names the question), and be paid in full.
**Change:** `reference_exposed(user, question)` in the attempts repository; a strong practice answer and a strong
interview turn earn nothing when any other attempt of that member revealed the question's reference.
**Open:** judged duels (the default duel is the quiz); and the softer route, a throw-away weak attempt whose feedback
shows what was missing, then a new attempt. That one is a rule decision for Shaked: pay only for a member's first
scored answer on a question, or accept it. **Tests:** `TestAReferenceSeenOnAnotherAttempt`.

### SEC-026 — unlimited judge calls for one answer

A failed or declined evaluation could be retried, and the same answer re-sent, without limit: one unit of the daily
allowance bought any number of paid calls. **Change:** eight judge calls per practice attempt
(`MAX_JUDGE_CALLS_PER_ATTEMPT`), five per interview turn (`MAX_JUDGE_CALLS_PER_TURN`); after that 429 `usage_limit`,
the answer stays saved, and an interview can still be ended. **Open:** the judged duel's re-submission inside its
three-minute clock, and the interview report narrative, regenerated on every read while it fails.
**Tests:** `TestAnAnswerTheModelKeepsFailingOn`.

### SEC-027 — the quiz answer key through the practice rounds

`GET /v1/duels/practice` and its answer route (added 11 November) draw from the same pool as the duels, return the
correct option, and had no count: about 23,000 rounds cover all 2,500 variants, roughly an hour at the request
budget, after which a script wins every duel. **Change:** 150 practice rounds a member a day, per process
(`quiz_practice.DAILY_ROUNDS`); the key now takes months. **Open:** separate pools for practice and duels; the seed
file `seeds/duel_quiz.json` is in a public repository; the web app ships 50 real variants with their answers in
`apps/web/src/components/duels/quiz-demo-data.json` (Harel: those 50 must leave the duel pool or the demo).
**Tests:** `TestPracticeRoundsADay`.

### SEC-028 — warm-up calls nobody counted

Opening a hint that is not given, or the reference again, re-warmed the judge's cache: a model call outside every
allowance, repeatable every four minutes for every question a member ever opened. **Change:** a warm-up only when a
hint was really given, and on the first reveal while the answer is still to come. **Tests:** `TestWarmUpsOnlyForSomethingNew`.

### SEC-029 — one member's bill

The only budgets were counts (30 attempts and 5 interviews a day). **Change:** `MONTHLY_USER_BUDGET_ILS` (default 15,
with `USD_TO_ILS` 3.7): at the door of a new attempt and a new interview, the member's recorded model spend since
the first of the month is compared with the budget; at or above it nothing new opens until the month turns. What is
open is finished. **Tests:** `TestTheMonthlyBudget`.

### Smaller fixes

- `GET /v1/me/activity?timezone=America` answered 500; a folder name now falls back to UTC like any unknown zone.
- The health key is compared in constant time; `ENV=Production` (any capitalisation) is production for the start guard.
- `/health` now carries `request_budget`: how many addresses the server saw in the last minute, how many of them are
  private, and how many requests each budget refused. It answers the question SEC-010 left open: does the hosting
  proxy hand the API each client's own address, or one shared address whose 1,800 requests a minute every user
  draws on? Checked on Render after the deploy (see the status file).

## Open

### SEC-030 — public images carry the solution bank (Harel, Shaked)

The self-host pipeline on `production` reads the repository and both container packages anonymously
(`deploy/selfhost/PRODUCTION.md`, `autodeploy/pull_release.py`, `selfhost-publish.yml`), and the API image copies
`seeds/` (reference solutions, rubrics, the duel answers). Making the repository private, the open SEC-018 action,
would not hide the images and would break the updater. **Order:** make the two packages private; give the server a
read-only token for the registry and the branch reference; authenticate the two `git ls-remote` calls in the
workflow; then make the repository private. Not verified live (the images were not pulled).

### SEC-031 — unbounded browser writes (migration ready, not applied)

`supabase/migrations/20261114130000_scale_indexes_and_browser_write_limits.sql`, dry-run on 14 November and rolled
back (verified afterwards: nothing changed). It limits `question_resume_visits` to pilot members and 2,000 rows an
account, removes the browser's unused insert and delete on `user_document`, and removes the browser's unused update
on `user_profile` (whose `background` column holds the backend-validated goal). Harel confirms parts 1 and 3 first.

### SEC-032 — founder rights on a shared mailbox row

The pilot list gives the shared project mailbox `can_manage_tasks`. Founder rights follow whichever sign-in account
holds that address. If no such account exists, whoever registers the address (access to the inbox, or nothing at all
if e-mail confirmation is off) becomes a founder: every member's address, the support tickets, announcements.
**Do:** check that both founders' personal accounts carry the right, then set it to false on the shared row (one
approved statement on `jr_members`).

### SEC-033, SEC-034 — two backends, and the Netlify sites

Render (master) and the new server (production) run different code on the same data, and a push to either branch
deploys with the database owner's credentials and no human step. Until Render is retired every fix must land on
both branches; both branches should require a reviewed pull request. Before the Netlify sites are deleted, remove
their addresses and `localhost` from the Supabase redirect list and from `ALLOWED_ORIGINS`, or a stranger who
registers the freed site name receives sign-in tokens.

### SEC-035 — the checkers on a crafted answer

`checks.locate_named_value` rescans the rest of the answer for every mention of a quantity's name (13,200 characters
of `Tmin 1 ns, ` took 12.7 s), and `extract_expression` re-parses long lines up to 80 times each. Both run in a
worker thread, so the API keeps answering, but an answer can hold a CPU for tens of seconds. The proposed bounds
(the last 50 mentions and a 400-character clause; lines over 400 characters skipped) change what the checker can
find in unusual answers, so this waits for Shaked.

### SEC-036 — the web app (Harel; details in `docs/harel-todo-2026-11-14.md`)

Sign-in by a crafted link (the default implicit flow), answer drafts and account ids left in browser storage after
sign-out, ids from the address bar placed unencoded into API paths, and the design-lab pages shipped on the
production origin. None of the five items from the 8 November review is done on `master`; `production` already has
Next.js 16.4.6.

### Recorded, no change

- The e-mail-confirmed check in `auth.py` reads a field the user can edit; the real control is Supabase's "Confirm
  email" setting, still on the operator list.
- The starting gift can be moved between two accounts through duel forfeits, and the daily winnings ceiling is
  checked on entry only. A rule decision before coins carry any value.
- The request budget is per token, so a member with several live tokens is bounded by the address budget only.
- `.mcp.json` gives any assistant session a write-capable connection to the production database; `read_only=true`
  in the tracked file, with writes through `scripts/apply_sql.py`, would close it. A workflow decision.
- The publish job on `production` holds signing and registry rights while it runs `npm ci` and the tests.
- `deploy/selfhost/PRODUCTION.md` in a public repository names the server address and where secret exports are kept.
- `/docs` and `/openapi.json` are public in production. They describe routes, nothing secret.

## What held up

Token verification; a pilot gate on every route but the two deliberate ones; ownership enforced in the query on every
route that takes an id; the coin ledger under locks with idempotent credits; row-level security on all 53 tables;
no browser access to questions, solutions or tips; definer functions with pinned search paths; private storage
buckets with path rules; no string-built SQL; no secret in any commit on any branch; no submitted code run on the
API host; no server-side fetch to a caller-chosen address; request parsing bounded; no stored cross-site scripting,
open redirect or privileged key in the web app. `pip-audit` clean.

## Verification

- `backend/tests/test_scale_and_security_2026_11_14.py`: 38 tests, all pass.
- Full offline suite: 4,506 passed, 13 skipped, 1 failed (the web client contract test, failing before this pass).
- The fixes were reviewed independently before the commit. That review found eight defects in them, all corrected
  and covered by tests: the ceiling of SEC-026 did not cover a re-sent follow-up answer and counted interview
  tries that never reached the model; SEC-023's first form (at most eight blanks) let a closing tag padded with nine
  blanks through, so the pattern now matches any amount of blanks possessively; SEC-024's reduced-size decode did
  nothing for non-square photos, its lock could occupy the shared thread pool, and a small photograph saved as
  PNG was reduced to 256 colours; SEC-022's bound made an over-long carry-in read as 0; and the budgets on
  `/health` were computed for anonymous callers too.
- Full offline suite and the load test: recorded in `backend/STATUS.md` §5zzg.
- The migration: dry-run only.
