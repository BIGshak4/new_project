# Backend

FastAPI backend and the adaptive AI engine for the interview preparation platform.
The specification is in `../src/` (start with `AI_Engine_Spec.md`); the database
schema is in `../supabase/migrations/`.

## Setup (Windows PowerShell)

```powershell
cd backend
uv sync                      # creates .venv and installs everything
uv run pytest -q             # 270 tests, about two seconds, no network
```

## Try the coaching loop in the terminal

No API key and no database are needed. With the `manual` provider every model call
is written to `workdir/manual_llm/NNN_<role>.request.md` and the program waits until
someone writes `NNN_<role>.response.json` (or `.md`) next to it. "Someone" can be you,
or Claude Code in another terminal.

```powershell
uv run python scripts/cli_practice.py --debug
uv run python scripts/cli_practice.py --language he
uv run python scripts/cli_practice.py --question fsm_seq_detect_1011_overlap --once
```

While answering: `:hint` (next hint level), `:reveal` (reference solution; before
submitting this means the attempt gives no evidence), `:skip`, `:quit`. End a
multi-line answer with a line containing only a dot.

With an API key in `.env`:

```powershell
uv run python scripts/cli_practice.py --provider anthropic --debug
```

Your progress is kept in `workdir/cli_profile.json`. Delete it to start over.

## Seeds

```powershell
uv run python scripts/seed_db.py --check     # validate the seed files only
uv run python scripts/seed_db.py             # validate, then upsert into Supabase (needs DATABASE_URL)
```

| Path | Contents |
|---|---|
| `seeds/skills/` | The skill catalog: 6 subjects, 35 skills, each with a 5-level rubric |
| `seeds/roles/` | Role skill sets: weights, importance, required level per seniority |
| `seeds/companies/` | Company profiles; every company skill row must cite dated evidence |
| `seeds/questions/` | The question bank, bilingual, with rubric, 3 hints, common errors, optional deterministic check |
| `seeds/tips.json` | Coaching tips with trigger rules |
| `seeds/glossary.json` | Technical terms and whether they stay in English inside Hebrew text |

The loader validates everything together and reports every problem at once: unknown
skill keys, weights that do not sum to 1.0, prerequisite cycles, a question whose
deterministic check rejects its own known-good answer, a company claim without evidence.

## Layout

```
app/
  main.py, config.py, db.py
  schemas/engine.py          typed objects the engine passes around; live session state
  schemas/bank.py            questions and tips
  engine/
    params.py                every threshold and weight, in one place
    checks.py                deterministic checks: truth table (safe Boolean parser), numeric
    scores.py                bands, k and c updates, evidence weight, levels, priors, calibration
    plan.py                  role + company + focus -> session skill plan
    skill_controller.py      layer 1: escalate, hold, hint, step back, resolve
    subject_router.py        layer 2: next subject, next skill, entry difficulty, rebalancing, bridges
    session.py               one simulation turn, end to end, no I/O
    practice.py              one deep or quick practice question, end to end
    plan_router.py           across days: next activity, weekly plan, retention checks, diagnostic
    scorecards.py            fit scores with core-gap caps, profile roll-up, target fit
    bank.py                  bank-first question selection
    catalog.py               load and validate the seed files
    providers.py             ScriptedProvider, ManualProvider, AnthropicProvider
    evaluator.py, generator.py, tips.py, feedback.py, reporter.py, i18n.py
    prompts/                 versioned prompt files, one per engine role, plus language blocks
scripts/                     cli_practice.py, seed_db.py
seeds/                       content, as JSON
tests/                       unit tests built from the worked examples in the specs, plus persona bots
```

## Rules of the house

- Decision logic is plain Python, never an LLM call. The model scores answers and words questions.
- A failed model call never breaks a session: the evaluator retries once and then the turn is saved
  without an evaluation; the generator and the feedback card fall back to templates.
- Candidate text is data. It is wrapped in `<candidate_answer>` and cannot close its own delimiter.
- A level is never reported without evidence: `not_assessed`, `insufficient_evidence` (provisional), `assessed`.
- Prompts are code: change a prompt file, bump its version in `engine/i18n.py`, run the golden set.
