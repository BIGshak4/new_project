# Performance and multi-user night — 26 September 2026

For Shaked. Answers are now graded about twice as fast as the candidate sees it, the server was driven by 100
simultaneous users without an error, and the database connection limit that would break first under load is found
and has a one-line fix waiting for you (§5). `backend/STATUS.md` §5n has the summary; this file has the numbers.

## Decisions for Shaked

1. **Switch Render's `DATABASE_URL` to the Transaction pooler** (same host, port **6543** instead of 5432). The
   Session pooler refuses the project's ~10th simultaneous connection (`EMAXCONNSESSION`), and the API alone may open
   10. The Transaction pooler accepted 40 at once and ran every flow of this backend unchanged (rolled back).
   `/health` then shows `"database_pooler": "transaction"`.
2. **The Anthropic account is on the Evaluation tier** (read from the API's own response headers: 1,000 requests,
   500k input and 80k output tokens per minute, per model). That serves about 55–75 fully answered questions per
   minute, roughly 200–300 people answering at the same moment. The Start tier (2M / 400k) is about 5× that; it
   comes with usage history and has a $500/month spend cap (≈ 5,000–8,000 answered questions).
3. **Evaluator model: keep Opus 5.** Sonnet 5 as the judge agreed on 13/13 bands and is 62 % cheaper, but only
   ~1 s faster (4.0 s vs 5.0 s median), and it missed the key misconception in one answer and over-flagged two in
   another (§6). Tonight's speed-up came from not waiting for the words, not from the judge.
4. **Rotate the database password** as a precaution: during the night one diagnostic command printed part of the
   connection string to the agent's own console (not to any file, commit or published log).

## 1. Latency: before (commit a9d8643) and after (`scripts/latency_bench.py`)

Real model (Opus 5 evaluator, Sonnet 5 prose, tip polished), real database from Shaked's machine (Supabase
Session pooler, one connection, everything rolled back), production rules. Five answers: an English weak answer
that gets a follow-up, the follow-up answer, an English strong answer, a Hebrew strong answer, a Python answer
run against its code tests.

```
  en weak (follow-up)              band WEAK     grade  17.8 s   all  17.8 s   progress  4259 ms   (28 + 33 statements)
  en weak (follow-up) → follow-up  band WEAK     grade   7.9 s   all   7.9 s   progress  1813 ms   (24 + 20 statements)
  en strong                        band PARTIAL  grade  16.4 s   all  16.4 s   progress  1900 ms   (30 + 20 statements)
  he strong                        band STRONG   grade  37.0 s   all  37.0 s   progress  1922 ms   (29 + 20 statements)
  code (python)                    band STRONG   grade  16.8 s   all  16.8 s   progress  1893 ms   (27 + 20 statements)
```

### before: 5 answers

| stage | median | max | n |
|---|---:|---:|---:|
| load | 0.67 s | 1.15 s | 5 |
| accept+save | 0.45 s | 0.60 s | 5 |
| check | 0.07 s | 0.14 s | 2 |
| evaluator | 5.01 s | 5.96 s | 5 |
| card | 6.92 s | 12.19 s | 4 |
| tip | 0.00 s | 2.21 s | 5 |
| follow-up | 7.96 s | 27.80 s | 4 |
| next question | 1.11 s | 1.28 s | 5 |
| outcome save | 1.29 s | 2.58 s | 5 |
| grade known | 16.80 s | 36.97 s | 5 |
| all feedback | 16.80 s | 36.97 s | 5 |
| progress | 1.90 s | 4.26 s | 5 |
| program | 1.01 s | 1.09 s | 5 |
| db statements (submit) | 28 | 30 | 5 |
| db statements (progress) | 20 | 33 | 5 |

| answer | band | grade known | all feedback | evaluator | progress |
|---|---|---:|---:|---:|---:|
| en weak (follow-up) | WEAK | 17.8 s | 17.8 s | 5.0 s | 4259 ms |
| en weak (follow-up) → follow-up | WEAK | 7.9 s | 7.9 s | 4.7 s | 1813 ms |
| en strong | PARTIAL | 16.4 s | 16.4 s | 5.6 s | 1900 ms |
| he strong | STRONG | 37.0 s | 37.0 s | 6.0 s | 1922 ms |
| code (python) | STRONG | 16.8 s | 16.8 s | 4.6 s | 1893 ms |

### after: the same five answers (grade first, fewer round trips)

```
  en weak (follow-up)              band WEAK     grade  10.3 s   all  17.2 s   progress  4816 ms   (20 + 26 statements)
  en weak (follow-up) → follow-up  band WEAK     grade   6.8 s   all   9.0 s   progress  1545 ms   (18 + 12 statements)
  en strong                        band PARTIAL  grade   8.2 s   all  16.5 s   progress  2357 ms   (23 + 15 statements)
  he strong                        band STRONG   grade   8.1 s   all  28.9 s   progress  1699 ms   (23 + 12 statements)
  code (python)                    band STRONG   grade   7.7 s   all  17.2 s   progress  1432 ms   (21 + 12 statements)
```

| stage | before, median | after, median | after, max |
|---|---:|---:|---:|
| load | 0.67 s | 0.82 s | 1.43 s |
| accept + first save | 0.45 s | 0.61 s | 0.72 s |
| deterministic check | 0.07 s | 0.09 s | 0.17 s |
| evaluator (Opus 5) | 5.01 s | 4.67 s | 5.09 s |
| feedback card (Sonnet 5) | 6.92 s | 6.80 s (after the grade) | 15.37 s |
| tip | 0.00 s | 1.87 s (after the grade) | 1.90 s |
| follow-up wording | 7.96 s | 7.65 s (after the grade) | 20.07 s |
| next-question suggestion | 1.11 s | **0.12 s** | 0.21 s |
| outcome save | 1.29 s | 1.62 s | 2.90 s |
| words save (new) | — | 0.92 s | 1.64 s |
| **grade known (what the candidate waits for)** | **16.80 s** (max 36.97) | **8.09 s** (max 10.34) | |
| all words there | 16.80 s | 17.20 s | 28.91 s |
| progress() after the answer | 1.90 s | 1.70 s | 4.82 s |
| program() | 1.01 s | 0.92 s | 1.02 s |
| database statements per submit | 28 | 21 | 23 |
| database statements per progress | 20 | 12 | 26 |

Measured from Shaked's machine, where one database round trip is ~71 ms, so every answer here carries ~1.5 s of
network that production does not have: **from Render one round trip is 4 ms** (`GET /health?db_check=true`). In
production the grade should arrive about 5 s after sending (the evaluator plus ~0.2 s), the words about 7–15 s after
that. Stage times vary run to run with the model (the tip is polished only when a tip is chosen; the Hebrew
follow-up wording took 28 s before and 20 s after, both times in the generator call).

## 2. What changed

- **Grade first.** `submit` answers as soon as the answer is scored and saved: band, summary, key points, check,
  evidence, XP, the follow-up *decision* and the next question. The words (feedback card, polished tip, the
  follow-up's wording) start the moment the answer is scored, run while the grade is saved, and are stored into the
  same revision by a conditional update (only a `done` revision still flagged `feedback_pending`), so a replay never
  writes twice. The web app shows the grade at once and polls while `feedback_pending` is true; a follow-up whose
  words are not there yet shows "Writing your follow-up question…" and answering it is refused
  (`409 follow_up_not_ready`). After a restart between the two saves, the next read more than 30 s later writes the
  words and `retry` does it at once; neither ever scores again. `FEEDBACK_IN_BACKGROUND=false` restores the old way.
- **Proof nothing moved.** `tests/test_grade_first.py` replays a four-attempt scenario (hint + weak answer +
  follow-up, Python code tests + follow-up, Hebrew after the reference, strong + follow-up) and compares every stored
  result with a record written by the code *before* the split: bands, evaluations, evidence, XP, next question,
  every skill's `engine_state` and level history, metrics rows, usage rows, tips, card, tip and follow-up wording.
  Identical with the words inline and in the background. The evaluator, its prompts and effort, the scores, the
  evidence weights and the controller are untouched (`git diff a9d8643 -- backend/app/engine/evaluator.py
  backend/app/engine/scores.py backend/app/engine/skill_controller.py backend/app/engine/params.py
  backend/app/engine/prompts` is empty).
- **Round trips.** The servable question list and the question-skill links are cached like single questions already
  were; `progress()` reads recent attempts once and builds the program in the same transaction; the next-question
  reads ride in the outcome transaction; the seniority read with the goal is not read again. With the scripted model
  from this machine: warm submit 29 → 22 statements (4.3 → 3.0 s), start 12 → 7, library 6 → 3, progress 20 → 12.
  At 4 ms per round trip in production this saves tens of milliseconds; `progress()` itself is ~9 ms of CPU for a
  user with 200 answers.
- The web app no longer reloads the progress page after a hint or a reveal (they change nothing there).

## 3. Many users at once (`scripts/load_test.py`)

A local API process (uvicorn, one worker, as on Render), in-memory store, a scripted model with the real model's
timing (evaluator ~8 s, each prose call ~5 s, ±25 %), test sign-in tokens. Each virtual user: library → start →
hint → submit → poll until the words are in → follow-up → progress → program → mock interview with two answers.
A third answer a Python question (a child interpreter per answer). `/health` and a signed-in `/v1/me` are probed
every 250 ms.

| users | flows completed | submit p50 / p95 | words after the grade, p50 | progress p95 | signed-in probe p50 / p95 | event-loop lag p99 / max | memory |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 10/10 | 7.7 / 10.2 s | 6.1 s | 16 ms | 5 / 7 ms | 22 / 26 ms | 117 → 126 MB |
| 50 | 50/50 | 7.8 / 10.6 s | 6.1 s | 23 ms | 5 / 11 ms | 25 / 65 ms | 117 → 140 MB |
| 100 | 100/100 | 8.6 / 11.0 s | 6.8 s | 68 ms | 8 / 36 ms | 29 / 130 ms | 117 → 160 MB |

Same harness, 50 users, **the old way (`FEEDBACK_IN_BACKGROUND=false`): submit p50 14.1 s, p95 17.0 s**, against
7.8 / 10.6 s grade first. No errors at any level. One 100-user run froze for ~7 minutes while two unrelated model
runs on the same machine froze for the same 7 minutes (the machine paused, likely sleep); run again alone, it
passed. The first 100-user run showed loop stalls of up to 0.8 s: the in-memory test store deep-copied every user's
plan on every transaction (a harness problem, fixed: copy-on-write).

**What serialised users (fixed):**

| problem | measured before | after |
|---|---|---|
| every signed-in request took a thread from the default pool to look up the signing key | 20 code answers stuck in 5-s timeouts on a 6-thread host (small hosts size the pool that way): library p50 **3.8 s**, start / hint p95 **5.2 / 5.0 s**, signed-in probe max 4.5 s | known keys used from memory (0.34 ms on the loop): library p50 26 ms, start p95 37 ms, probe max 28 ms |
| code tests (a child interpreter, up to 5 s) ran in that same default pool | (the same run) | their own 4-thread pool: slow code answers wait for each other (their submit p95 29 s), nobody else does |
| tokens with made-up key ids forced a JWKS download per request and were remembered without bound | one download and one thread per request, for anyone on the internet | one refresh per 30 s, bounded memory (tests) |
| `/catalog/summary` reloaded and validated the seed files on the event loop for every request (~35 ms) | | the loaded catalog |

**Left as is:** one uvicorn worker per instance (every request is async; the loop stays under 130 ms of lag at 100
users); the per-attempt and per-interview locks serialise only one user's own clicks.

**When the model answers 429** (30 % of evaluator calls refused, 50 users): 50/50 flows completed, no errors, no
lost answers. The evaluator's own second attempt absorbed most refusals; 3 main answers ended "failed, your answer
is saved" and `retry` scored them; 8 interview turns stayed open to be answered again. With the real SDK each call is
also retried twice after the server's `retry-after` before the evaluator sees an error. A refused prose call is never
an error: the card, tip and follow-up fall back to their templates.

## 4. Model capacity

The account's limits, read from the response headers of two tiny calls: **1,000 requests, 500,000 input tokens and
80,000 output tokens per minute, for Opus 5 and separately for Sonnet 5** (the Evaluation tier; only uncached input
and cache writes count toward the input limit). Per call, from the last 30 days of real usage rows:

| call (model) | input counted (cold cache) | output | latency, average of stored rows |
|---|---:|---:|---:|
| evaluate (Opus 5) | 833 + 3,783 cache write | 397 | 9.6 s (4–6 s typical tonight) |
| feedback card (Sonnet 5) | 491 + 2,207 | 604 | 14 s (7 s typical tonight) |
| follow-up wording (Sonnet 5) | 1,286 + 2,661 | 654 | 15 s |
| tip polish (Sonnet 5) | 658 | 119 | 3 s |

- **Opus (the judge):** 80k / ~400 = 200 evaluations a minute by output; 500k / ~4.6k = ~108 a minute with cold
  caches (~500 warm, when many people answer the same question within 5 minutes). A question with its follow-up is
  two evaluations.
- **Sonnet (the words):** ~1,040 output tokens per main answer (card, follow-up in about half the answers, tip):
  ~77 answers a minute; ~95 by input with cold caches.
- **So about 55–75 fully answered questions per minute** before 429s; at one question per person every ~4 minutes,
  ~200–300 people answering at the same moment. Start tier: ×4–5. Priority Tier does not exist for Opus 5 / Sonnet 5.
- **Spend:** ~$0.06–0.09 per question with its follow-up on today's cold caches.

## 5. The database under many users (`scripts/db_concurrency.py`, everything rolled back)

| test | result |
|---|---|
| connections opened at once, **Session pooler** (5432, today) | 5 → 5 opened; 10 → **9** opened, then `EMAXCONNSESSION: max clients reached in session mode`; 15 / 20 / 30 → still 9 |
| connections opened at once, **Transaction pooler** (6543) | 10, 20, 40 → all opened, no errors (connect 4–13 s from here: queued handshakes) |
| a full service flow per user (start, get, submit, words, progress, program) through 6543 | 1 and 5 users: no errors, no prepared-statement problems |
| the API's pool (5 + 5) shared by 20 users reading the progress data, 100 separate transactions, through 6543 | no errors; each read holds a connection ~0.8 s from here (12 statements × 71 ms) |
| round trip from Render (production) | **4.15 ms** (`/health?db_check=true`) |
| Postgres | `max_connections` 60, 10 in use at night |

In production a progress read holds a connection ~12 × 4 ms ≈ 50–70 ms, so the API's 10 connections serve roughly
150–200 such reads a second: the pool is not the limit. **The Session pooler is**: its client slots are shared by
every session-mode client of the project, and the API alone may take 10. Recommendation for Render: port 6543 in
`DATABASE_URL`, pool as today (`DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=5`); if the Session pooler must stay, set
`DB_MAX_OVERFLOW=2`. A new connection costs 2–4 s from here (well under a second from Render), so the pool's reuse
stays, and so does `pool_pre_ping` (one extra round trip, 4 ms, per checkout).

## 6. The evaluator: Opus 5 (current) vs Sonnet 5, 13 review answers (`scripts/p2_review_set.py`)

| | Opus 5 | Sonnet 5 |
|---|---|---|
| bands as a careful human would judge | 13/13 | 13/13 |
| bands identical to each other | 13/13 | |
| evaluation time, median / mean (excluding case 08) | 5.0 s / 4.7 s | 4.0 s / 4.2 s |
| evaluator cost for the 13 | $0.25 | $0.09 |
| misconception keys | precise | case 09 (off-by-one loop bound): missed `off_by_one_count`, the point of the case; case 12: added `recovery_gated_by_enable` and `asynchronous_reset_used` to the real `hold_forgotten` |

Case 08 took ~420 s on both models at the same moment as the machine pause in §3: not the models. Recommendation:
keep Opus 5 as the judge; the misconception keys feed the "what was hard here" line and the core-misconception cap.
