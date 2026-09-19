# Hand-back to Harel: P0 and P1 done, real model live

- Date: 19 September 2026
- For: Harel Artman and Shaked Buzi
- Backend commit: see `git log` (P0 `07a2813`, P1 this commit); deployed on Render with `LLM_PROVIDER=anthropic`, `ENV=staging`
- Answers the checklist in `docs/shaked-human-review-handoff.md` §8

## 1. Demo-data separation (P0)

- Every answer revision now records `evaluator_model`; `SubmissionView.assessed_by` is `"demo"` for the scripted/manual stand-ins and `"model"` (with `model` = the model id) for a real assessment. The UI can trust the submission itself instead of `/health.llm_provider`.
- All demonstration assessment data was wiped with Shaked's approval before the switch: 8 attempts, 6 submissions, 9 metrics, 23 usage rows, 3 tips, 5 skill-profile rows. Accounts, `jr_practice_entries`, and the task board were untouched.
- The backend logs a warning at startup whenever a non-Anthropic provider writes into the real database.

## 2. Real provider (P1)

| Setting on Render | Value |
|---|---|
| `LLM_PROVIDER` | `anthropic` |
| `ANTHROPIC_MODEL` | `claude-opus-5` (returned model id matches) |
| `ANTHROPIC_ENABLE_FALLBACKS` | `true`, accepted by the account (the automatic downgrade path did not fire) |
| Structured output (`messages.parse`) | accepted by the account (the JSON-in-text fallback did not fire) |
| `ENV` | `staging` |

Verified: evaluator, feedback card and tip polish with the real model in **English and Hebrew**, locally and then through the service into production under Shaked's personal account (quick mode, no automatic follow-ups). Stored rows carry `evaluator_model = claude-opus-5`.

Measured per answer (quick flow = evaluate + card + tip):

| | wall time | cost |
|---|---|---|
| Hebrew, wrong answer (sensor majority) | 43 s | $0.076 |
| English, mostly-right answer (mod-6 counter) | 41 s | $0.076 |

Breakdown: evaluation 5–9 s / $0.010–0.041 (the higher figure writes the prompt cache; the next answer to the same question reads it at a tenth of the price), feedback card ~10 s at the new `low` effort ($0.016–0.026), tip ~5 s ($0.004). Budget guidance: **about $0.08 per answer on Opus alone; ≈ $0.05 cold / $0.025 warm on the Opus-judge + Sonnet-prose mix now deployed (20 Sept).** The Anthropic console's monthly limit is the hard stop; `DAILY_ATTEMPT_LIMIT` (30) bounds attempts per user per day.

Quality observations from the first two real answers: the evaluator found the `xor_confused_with_majority` misconception on the wrong answer and, on the "correct" counter, correctly pointed out that recovery from states 6/7 sat inside the enable branch and that the requested trace was missing. The Hebrew card was specific (named the exact truth-table rows), credited alternative approaches, and kept technical terms in English.

Two fixes from the run: the tip polish sometimes echoed the `<tip>` delimiter (stripped); feedback effort lowered from `medium` to `low` (same card quality, ~10 s instead of ~16 s).

## 3. What the UI should expect now

- `submission.assessed_by === "model"` on new answers; older rows do not exist any more.
- A full answer takes **35–45 s** end to end; the 202 path triggers only past 90 s. Show a waiting state with a hint that the assessment takes about half a minute.
- `evidence` is `"reduced"` on every quick-mode answer (base weight 0.3, `params.py`). To be revisited together after the review session; not a bug.
- `check` is present only for the three questions with a deterministic check; its `detail` string is English (e.g. "6 of 8 specified rows differ") — the Hebrew card re-explains it in Hebrew.

## 4. Failure and retry behaviour (P4 items already verified)

Duplicate click / network retry → replay, no second charge; evaluator down → answer saved, `status: failed`, retry works; refresh mid-evaluation → `status: evaluating`, retry refused until the 10-minute budget passes; two servers accepting the same revision → first wins, second gets 409 or the winner's result; lost database connection → 503 `temporarily_unavailable` with `Retry-After`. All covered by offline tests; the live suite (16 scenarios against Supabase) passed on the merged code.

## 5. Ready for the joint review session

Both personal accounts (`harel.artman@`, `shakedbu6@`) are on `jr_members`, confirmed, with a clean history. Suggested first set for §5 of the review handoff: `example-sensor-majority`, `example-mod-six-counter`, `example-nand-only-enable`, `example-setup-hold-calculation`, `example-count-set-bits` — one correct, one partial, one wrong answer each, in each language where the reviewer is comfortable. Export each attempt with **Export for review**; the backend commit, model id and prompt version are `claude-opus-5`, `evaluator.v1` / `feedback.v1` / `tip.v1` unless changed.

Open decisions for the session: the quick-mode evidence weight; whether the English `check.detail` should be localised; the first 10 questions to publish.
