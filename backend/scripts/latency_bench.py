"""Where an answer's time goes, stage by stage, on the REAL model and the REAL database. Zero residue.

Everything runs inside one database transaction that is rolled back at the end (RollbackStore), with production
rules (trial/published questions only, the coach suggests reviewed questions only, the tip is polished by the model).
Each answer is timed stage by stage by wrapping the functions the service calls, so the script measures the code as
it is, before or after a change, without the code knowing it is measured:

    load            PracticeService._load (attempt + question + profile + goal)
    accept+save     accepting the revision and the first save (the answer is durable)
    check           the deterministic check (truth table, numeric, code tests in a child interpreter)
    evaluator       the evaluator call (Opus)
    card / tip / follow-up      the prose calls (Sonnet)
    next question   the next-question suggestion (reads the servable list and the seen questions)
    outcome save    everything the evaluation produced, in one transaction
    prose save      (grade-first only) the card/tip/follow-up saved into the same revision afterwards
    grade known     what the candidate waits for: submit() returning with a band
    all feedback    until the card, the tip and the follow-up wording are there too
    progress        the progress() call the web app makes after every answer
    program         the program() call the Learn page makes

    uv run python scripts/latency_bench.py              # about $0.30 on the Opus/Sonnet mix
    uv run python scripts/latency_bench.py --label after --json out.json
"""

from __future__ import annotations

import argparse
import asyncio
import contextvars
import functools
import json
import statistics
import sys
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import event, text

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from livetools import RollbackStore  # noqa: E402

from app import db  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.engine import checks, evaluator, feedback, generator  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.practice import PracticeAttempt  # noqa: E402
from app.engine.providers import build_provider  # noqa: E402
from app.repo import cache  # noqa: E402
from app.services.practice_service import PracticeService, ServiceConfig  # noqa: E402

CURRENT: contextvars.ContextVar[str | None] = contextvars.ContextVar("bench_answer", default=None)
EVENTS: list[tuple[str | None, str, float, float]] = []            # (answer, stage, start, end)
STATEMENTS: dict[str | None, int] = {}

COUNT_SET_BITS = """def count_set_bits(x):
    count = 0
    while x:
        x &= x - 1      # clears the lowest set bit, so the loop runs once per 1 bit
        count += 1
    return count
# terminates: every step clears one set bit, at most 32 steps. Time O(k) <= O(W), space O(1).
# 0 -> 0, 0b10110100 -> 4, 0xFFFFFFFF -> 32
"""

ANSWERS = [
    # (name, question key, language, answer, answers the follow-up too)
    ("en weak (follow-up)", "example-sensor-majority", "en",
     "alarm = A ^ B ^ C; XOR gives 1 whenever more than one input is 1, so it is the majority.", True),
    ("en strong", "example-nand-only-enable", "en", None, False),
    ("he strong", "example-masked-equality", "he", None, False),
    ("code (python)", "example-count-set-bits", "en", COUNT_SET_BITS, False),
]
FOLLOW_UP_ANSWER = "I am not sure; maybe it needs an AND of each pair, then an OR of the three products."


def _record(stage: str, started: float) -> None:
    EVENTS.append((CURRENT.get(), stage, started, time.perf_counter()))


def wrap(owner, name: str, stage: str) -> None:
    original = getattr(owner, name)
    if asyncio.iscoroutinefunction(original):
        @functools.wraps(original)
        async def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return await original(*args, **kwargs)
            finally:
                _record(stage, started)
    else:
        @functools.wraps(original)
        def timed(*args, **kwargs):
            started = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                _record(stage, started)
    setattr(owner, name, timed)


class TimedStore(RollbackStore):
    """Records every unit of work, so 'the first save after accept' can be found on the timeline."""

    @asynccontextmanager
    async def transaction(self):
        started = time.perf_counter()
        async with super().transaction() as tx:
            yield tx
        _record("tx", started)


def instrument() -> None:
    wrap(PracticeService, "_load", "load")
    wrap(PracticeAttempt, "accept", "accept")
    wrap(checks, "run_check", "check")
    wrap(evaluator, "evaluate", "evaluator")
    wrap(feedback, "build_card", "card")
    wrap(PracticeAttempt, "_tip", "tip")
    wrap(generator, "generate", "follow-up")
    wrap(PracticeService, "_suggest_next", "next question")
    wrap(PracticeService, "_persist_outcome", "persist")
    for optional in ("_persist_feedback",):                   # the grade-first split, when present
        if hasattr(PracticeService, optional):
            wrap(PracticeService, optional, "prose save")


def stages_for(answer: str, submit_started: float) -> dict[str, float]:
    """Milliseconds per stage for one answer, derived from the timeline."""
    mine = [(stage, s, e) for a, stage, s, e in EVENTS if a == answer]
    out: dict[str, float] = {}

    def total(stage: str) -> float:
        return sum((e - s) * 1000 for st, s, e in mine if st == stage)

    loads = [(s, e) for st, s, e in mine if st == "load"]
    if loads:
        out["load"] = (loads[0][1] - loads[0][0]) * 1000
    accept = next(((s, e) for st, s, e in mine if st == "accept"), None)
    if accept:
        first_tx = next(((s, e) for st, s, e in mine if st == "tx" and s >= accept[1]), None)
        out["accept+save"] = ((first_tx[1] if first_tx else accept[1]) - accept[0]) * 1000
    for stage in ("check", "evaluator", "card", "tip", "follow-up", "next question", "prose save"):
        value = total(stage)
        if value:
            out[stage] = value
    if total("persist"):
        out["outcome save"] = total("persist") - total("next question")
    return out


async def wait_for_feedback(svc: PracticeService, user: uuid.UUID, attempt_id: uuid.UUID, revision: int,
                            timeout: float = 120.0) -> None:
    """Grade-first: the prose arrives in a background task. Wait for it (the web app polls instead)."""
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        tasks = getattr(svc, "_feedback_tasks", None)
        if tasks:
            await asyncio.gather(*list(tasks.values()), return_exceptions=True)
        view = await svc.get(user, attempt_id)
        subs = [view.submission, *[f.submission for f in view.follow_ups]]
        mine = next((s for s in subs if s is not None and s.revision == revision), None)
        if mine is None or not getattr(mine, "feedback_pending", False):
            return
        await asyncio.sleep(0.2)
    raise TimeoutError("the feedback never arrived")


async def run(args) -> dict:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    settings = get_settings()
    if not settings.anthropic_api_key or not settings.database_url:
        raise SystemExit("ANTHROPIC_API_KEY and DATABASE_URL are needed")
    provider = build_provider("anthropic", api_key=settings.anthropic_api_key, model=settings.anthropic_model,
                              enable_fallbacks=settings.anthropic_enable_fallbacks, role_models=settings.role_models)
    catalog = load_catalog(settings.seeds_dir)
    instrument()
    engine = db.get_engine()

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany):
        key = CURRENT.get()
        STATEMENTS[key] = STATEMENTS.get(key, 0) + 1

    rows: list[dict] = []
    async with engine.connect() as connection:
        outer = await connection.begin()
        try:
            await connection.execute(text("select 1"))
            user = (await connection.execute(text("select id from public.user_profile limit 1"))).scalar_one()
            store = TimedStore(connection, allow_in_review=False)
            svc = PracticeService(store, catalog, provider, ServiceConfig(polish_tips=True, daily_attempt_limit=10_000))
            cache.clear()
            await svc.list_questions(language="en")                # warm the reflected schema and id maps, as a live server is
            for name, key, language, answer, follow_up in ANSWERS:
                if args.only and args.only not in name:
                    continue
                question = catalog.questions[key]
                answer = answer or question.translations[language].reference_solution
                view = await svc.start(user, question_key=key, mode="deep", language=language)
                aid = uuid.UUID(view.id)
                turns = [(name, None, answer)]
                if follow_up:
                    turns.append((name + " → follow-up", "follow-up", FOLLOW_UP_ANSWER))
                for label, kind, text_ in turns:
                    token = CURRENT.set(label)
                    STATEMENTS[label] = 0
                    started = time.perf_counter()
                    if kind == "follow-up":
                        if view.pending_follow_up is None:
                            print(f"  ({label}: no follow-up was asked)")
                            CURRENT.reset(token)
                            continue
                        # the wording may still be on its way (grade first): wait for it like the app does
                        if getattr(view.pending_follow_up, "question", "x") in (None, ""):
                            await wait_for_feedback(svc, user, aid, view.submission.revision)
                            view = await svc.get(user, aid)
                            started = time.perf_counter()
                        submission, view = await svc.submit(user, aid, {"text": text_}, idempotency_key=f"{aid}-f",
                                                            follow_up_turn=view.pending_follow_up.turn)
                    else:
                        submission, view = await svc.submit(user, aid, {"text": text_}, idempotency_key=f"{aid}-m")
                    graded = time.perf_counter()
                    statements_submit = STATEMENTS[label]
                    if getattr(submission, "feedback_pending", False):
                        await wait_for_feedback(svc, user, aid, submission.revision)
                    all_done = time.perf_counter()
                    view = await svc.get(user, aid)
                    progress_key = label + " progress"
                    CURRENT.set(progress_key)
                    STATEMENTS[progress_key] = 0
                    p0 = time.perf_counter()
                    await svc.progress(user, language=language)
                    progress_ms = (time.perf_counter() - p0) * 1000
                    statements_progress = STATEMENTS[progress_key]
                    CURRENT.set(label + " program")
                    p0 = time.perf_counter()
                    await svc.program(user, language=language)
                    program_ms = (time.perf_counter() - p0) * 1000
                    CURRENT.reset(token)
                    row = {"answer": label, "band": submission.band, **stages_for(label, started),
                           "grade known": (graded - started) * 1000, "all feedback": (all_done - started) * 1000,
                           "progress": progress_ms, "program": program_ms,
                           "db statements (submit)": statements_submit, "db statements (progress)": statements_progress}
                    rows.append(row)
                    print(f"  {label:<32} band {submission.band or '-':<8} grade {row['grade known'] / 1000:5.1f} s   "
                          f"all {row['all feedback'] / 1000:5.1f} s   progress {progress_ms:5.0f} ms   "
                          f"({statements_submit} + {statements_progress} statements)")
        finally:
            await outer.rollback()
    await engine.dispose()
    return {"label": args.label, "rows": rows}


STAGES = ["load", "accept+save", "check", "evaluator", "card", "tip", "follow-up", "next question", "outcome save",
          "prose save", "grade known", "all feedback", "progress", "program", "db statements (submit)",
          "db statements (progress)"]


def table(result: dict) -> str:
    rows = result["rows"]
    lines = [f"### {result['label']}: {len(rows)} answers", "", "| stage | median | max | n |", "|---|---:|---:|---:|"]
    for stage in STAGES:
        values = [r[stage] for r in rows if stage in r]
        if not values:
            continue
        if stage.startswith("db statements"):
            lines.append(f"| {stage} | {statistics.median(values):.0f} | {max(values):.0f} | {len(values)} |")
        else:
            lines.append(f"| {stage} | {statistics.median(values) / 1000:.2f} s | {max(values) / 1000:.2f} s | {len(values)} |")
    lines.append("")
    lines.append("| answer | band | grade known | all feedback | evaluator | progress |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for r in rows:
        lines.append(f"| {r['answer']} | {r['band'] or '-'} | {r['grade known'] / 1000:.1f} s | {r['all feedback'] / 1000:.1f} s | "
                     f"{r.get('evaluator', 0) / 1000:.1f} s | {r['progress']:.0f} ms |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", default="run")
    parser.add_argument("--json", type=Path, help="also write the raw rows here")
    parser.add_argument("--only", help="run only the answers whose name contains this")
    args = parser.parse_args()
    result = asyncio.run(run(args))
    print()
    print(table(result))
    if args.json:
        args.json.write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
