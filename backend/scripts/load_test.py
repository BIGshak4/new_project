"""Many users at once, over real HTTP, against a local API. No database, no model, no cost.

The API runs in its own process (uvicorn, one worker, as on Render) with the in-memory store and a scripted model
that answers like the real one in time: the evaluator ~8 s, each prose call ~5 s, with jitter. Virtual users sign in
with test tokens (tests/authtools.py: a test signing key and verifier put on app.state in the server process only;
nothing here touches production code paths) and each walks the real flow:

    list questions -> start an attempt -> a hint -> submit -> poll until the words are in -> the follow-up ->
    progress -> program -> start a mock interview -> answer two turns

A third of the users answer a Python question, so the code-test runner (a child interpreter per answer) is exercised.
Meanwhile /health is probed every 250 ms (is the event loop still answering?) and the server reports its own
event-loop lag, thread-pool queue and memory (/_load/stats, added in the server process only).

    uv run python scripts/load_test.py                         # 10, 50, 100 users
    uv run python scripts/load_test.py --users 50 --rate-limit 0.3   # 30% of evaluator calls answer 429
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WEAK_ANSWER = "alarm = A ^ B ^ C; XOR is 1 when more than one input is 1."
CODE_ANSWER = "def count_set_bits(x):\n    n = 0\n    while x:\n        x &= x - 1\n        n += 1\n    return n\n"
PROFILE_SPLIT = "\n--- by cumulative time, app code only\n"
APP_CODE = r"[\\/]app[\\/]"
SLOW_CODE = False
SLOW_CODE_ANSWER = "def count_set_bits(x):\n    while True:\n        pass\n"
QUESTIONS = [("example-sensor-majority", WEAK_ANSWER), ("example-nand-only-enable", "A NAND-only answer: invert with a "
             "NAND whose inputs are tied, then NAND the enable with the data."), ("example-count-set-bits", CODE_ANSWER)]


# ------------------------------------------------------------------------------------------------ the server


def serve(args) -> None:
    import uvicorn
    from fastapi import FastAPI

    from app.config import Settings
    from app.engine.catalog import load_catalog
    from app.engine.providers import LLMError, LLMRequest, ScriptedProvider
    from app.main import app
    from app.repo.users import Access
    from app.runtime import build_runtime
    from app.services.memory_store import InMemoryStore
    from tests.authtools import make_verifier
    from tests.conftest import make_evaluation

    good = make_evaluation(correctness=0.9, depth=0.8).model_dump()
    weak = make_evaluation(correctness=0.2, depth=0.2, misconceptions=["xor_confused_with_majority"]).model_dump()
    rng = random.Random(7)
    calls = defaultdict(int)

    def latency(mean: float) -> float:
        return max(0.2, rng.gauss(mean, mean * args.jitter))

    async def respond(request: LLMRequest):
        calls[request.role] += 1
        if request.role == "evaluator":
            await asyncio.sleep(latency(args.eval_latency))
            if args.rate_limit and rng.random() < args.rate_limit:
                calls["evaluator_429"] += 1
                raise LLMError("rate limited: 429 (simulated)", retryable=True)
            return weak if "^" in request.user else good
        await asyncio.sleep(latency(args.prose_latency))
        if request.role == "generator":
            return {"question_text": "What changes if one input is stuck at 1?", "question_archetype": "design",
                    "expected_answer_outline": "the stuck input", "rubric_focus": []}
        if request.role == "feedback":
            return {"what_happened": "w", "why_it_matters": "y", "next_step": "n", "your_reasoning_vs_reference": "c"}
        if request.role == "report":
            return "A short narrative."
        return "Next time, trace one more input."

    # the test signing key is generated per process on import: use the key the load-test client signs with
    from cryptography.hazmat.primitives.serialization import load_pem_private_key

    from tests import authtools
    authtools._private_key = load_pem_private_key(os.environ["LOAD_TEST_KEY_PEM"].encode(), password=None)

    catalog = load_catalog(ROOT / "seeds")
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True, suggest_reviewed_only=False,
                        interview_reviewed_only=False, interview_daily_limit=10_000, daily_attempt_limit=10_000,
                        feedback_in_background=not args.inline)
    provider = ScriptedProvider(respond)
    app.state.verifier = make_verifier()

    async def everyone(user) -> Access:                      # every load-test account is a pilot member
        return Access(user_id=user.id, email=user.email, is_member=True, can_manage_tasks=False, profile_created=False)
    app.state.access_resolver = everyone
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=provider, store=InMemoryStore(catalog))
    app.state.runtime.practice.config.polish_tips = True      # production polishes the tip: one more model call
    if args.legacy_threads:
        # before 2026-09-26: code tests in the default thread pool, and a thread hop per request for the signing key
        from app.auth import TokenVerifier
        from app.engine import checks

        async def shared_pool(check, answer):
            return await asyncio.to_thread(checks.run_check, check, answer) if check else None
        checks.run_check_async = shared_pool
        cached = TokenVerifier._signing_key

        async def every_time(self, token, kid):
            self._keys.clear()
            self._last_miss_fetch = -1e9
            return await cached(self, token, kid)
        TokenVerifier._signing_key = every_time
    provider.requests = _Discard()                            # the scripted provider keeps every request: not here

    lag = {"max_ms": 0.0, "samples": []}

    async def ticker():
        while True:
            started = time.perf_counter()
            await asyncio.sleep(0.05)
            late = (time.perf_counter() - started - 0.05) * 1000
            lag["samples"].append(late)
            lag["max_ms"] = max(lag["max_ms"], late)
            del lag["samples"][:-2000]

    stats = FastAPI()
    profiler = {"p": None}

    @stats.get("/")
    async def _stats():
        profile_text = None
        if profiler["p"] is not None:
            import cProfile  # noqa: F401 - the profiler object is cProfile.Profile
            import io
            import pstats
            profiler["p"].disable()
            out = io.StringIO()
            pstats.Stats(profiler["p"], stream=out).sort_stats("tottime").print_stats(18)
            out.write(PROFILE_SPLIT)
            pstats.Stats(profiler["p"], stream=out).sort_stats("cumulative").print_stats(APP_CODE, 22)
            profile_text = out.getvalue()
            profiler["p"] = None
        loop = asyncio.get_running_loop()
        executor = getattr(loop, "_default_executor", None)
        samples = sorted(lag["samples"]) or [0.0]
        return {"rss_mb": await asyncio.to_thread(_rss_mb, os.getpid()), "loop_lag_p50_ms": round(samples[len(samples) // 2], 1),
                "loop_lag_p99_ms": round(samples[int(len(samples) * 0.99)], 1), "loop_lag_max_ms": round(lag["max_ms"], 1),
                "threads": len(getattr(executor, "_threads", ())) if executor else 0,
                "thread_queue": executor._work_queue.qsize() if executor else 0,
                "feedback_tasks": len(getattr(app.state.runtime.practice, "_feedback_tasks", {})),
                "model_calls": dict(calls),
                "tasks": len(asyncio.all_tasks()), "profile": profile_text}

    @stats.post("/reset")
    async def _reset():
        lag["max_ms"], lag["samples"] = 0.0, []
        if getattr(app.state, "ticker", None) is None:      # the app's lifespan owns startup; start the ticker here
            app.state.ticker = asyncio.get_running_loop().create_task(ticker())
        if args.default_threads and not getattr(app.state, "sized_pool", False):
            from concurrent.futures import ThreadPoolExecutor
            asyncio.get_running_loop().set_default_executor(ThreadPoolExecutor(max_workers=args.default_threads))
            app.state.sized_pool = True                         # as on a small host: min(32, cpus + 4) threads
        if args.profile:
            import cProfile
            profiler["p"] = cProfile.Profile()
            profiler["p"].enable()                             # the event-loop thread: what holds the loop
        return {}

    app.mount("/_load", stats)

    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning", access_log=False)


class _Discard(list):
    def append(self, _item) -> None:
        return None


def _rss_mb(pid: int) -> float | None:
    try:
        if sys.platform == "win32":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True,
                                 timeout=5).stdout
            return round(int(out.strip().split('","')[-1].strip('"').replace(" K", "").replace(",", "").replace(".", "")) / 1024, 1)
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1024, 1)
    except Exception:                                          # noqa: BLE001 - memory is a nice-to-have
        return None
    return None


# ------------------------------------------------------------------------------------------------ the users


class Recorder:
    def __init__(self):
        self.times: dict[str, list[float]] = defaultdict(list)
        self.errors: dict[str, list[str]] = defaultdict(list)
        self.flows: list[float] = []
        self.notes: dict[str, int] = defaultdict(int)

    async def call(self, client, name: str, method: str, url: str, *, ok=(200, 201, 202), **kw):
        started = time.perf_counter()
        try:
            response = await client.request(method, url, **kw)
        except Exception as exc:                               # noqa: BLE001 - counted
            self.errors[name].append(type(exc).__name__)
            raise
        finally:
            self.times[name].append((time.perf_counter() - started) * 1000)
        if response.status_code not in ok:
            self.errors[name].append(str(response.status_code))
            raise RuntimeError(f"{name}: {response.status_code} {response.text[:200]}")
        return response.json()


async def one_user(client, rec: Recorder, index: int, language: str) -> None:
    from tests.authtools import make_token

    _, token = make_token(uuid.uuid4(), email=f"user{index}@load.test", expires_in=7200)
    h = {"Authorization": f"Bearer {token}"}
    key, answer = QUESTIONS[index % len(QUESTIONS)]
    if key == "example-count-set-bits" and SLOW_CODE:
        answer = SLOW_CODE_ANSWER                              # runs into the runner's 5 s timeout
    await asyncio.sleep(random.random() * 2)                   # people do not click on the same millisecond
    started = time.perf_counter()
    await rec.call(client, "GET questions", "GET", f"/v1/questions?language={language}", headers=h)
    attempt = await rec.call(client, "POST attempt", "POST", "/v1/practice/attempts", headers=h,
                             json={"question_key": key, "mode": "deep", "language": language})
    aid = attempt["id"]
    await rec.call(client, "POST hint", "POST", f"/v1/practice/attempts/{aid}/hints/next", headers=h)
    body = await rec.call(client, "POST submit", "POST", f"/v1/practice/attempts/{aid}/submissions", headers=h,
                          json={"answer": {"text": answer}, "idempotency_key": f"{aid}-m"})
    grade_at = time.perf_counter()
    for _ in range(4):                                         # 429 from the model: the answer is kept, retry scores it
        if body["submission"]["status"] != "failed":
            break
        rec.notes["answers kept after a model failure, retried"] += 1
        await asyncio.sleep(2)
        body = await rec.call(client, "POST retry", "POST",
                              f"/v1/practice/attempts/{aid}/submissions/{body['submission']['revision']}/retry",
                              headers=h, ok=(200, 202, 409))
    if body["submission"]["status"] == "failed":
        rec.notes["answers still unscored after 4 retries (kept)"] += 1
    view = await poll(client, rec, h, aid)
    rec.times["words after grade"].append((time.perf_counter() - grade_at) * 1000)
    if view.get("pending_follow_up"):
        turn = view["pending_follow_up"]["turn"]
        await rec.call(client, "POST follow-up", "POST", f"/v1/practice/attempts/{aid}/follow-ups/{turn}/submissions",
                       headers=h, json={"answer": {"text": "maybe an AND of each pair"}, "idempotency_key": f"{aid}-f"},
                       ok=(200, 202, 409))
        await poll(client, rec, h, aid)
    await rec.call(client, "GET progress", "GET", f"/v1/me/progress?language={language}", headers=h)
    await rec.call(client, "GET program", "GET", f"/v1/me/program?language={language}", headers=h)
    interview = await rec.call(client, "POST interview", "POST", "/v1/interviews", headers=h,
                               json={"duration_min": 20, "language": language})
    for turn in range(2):
        current = interview.get("current_turn") if "current_turn" in interview else interview["interview"].get("current_turn")
        if current is None:
            break
        interview = await rec.call(client, "POST interview answer", "POST",
                                   f"/v1/interviews/{interview.get('id') or interview['interview']['id']}/turns/{current['index']}/answer",
                                   headers=h, json={"answer": {"text": "I would reason step by step."},
                                                    "idempotency_key": f"{aid}-i{turn}"}, ok=(200, 202))
        if interview["turn"]["status"] == "failed":
            rec.notes["interview answers not scored after a model failure (kept; the turn can be answered again)"] += 1
        interview = interview["interview"]
    rec.flows.append((time.perf_counter() - started) * 1000)


async def poll(client, rec: Recorder, h: dict, aid: str) -> dict:
    for _ in range(200):
        view = await rec.call(client, "GET attempt (poll)", "GET", f"/v1/practice/attempts/{aid}", headers=h)
        if view["status"] != "evaluating" and not view.get("feedback_pending"):
            return view
        await asyncio.sleep(1.5)
    raise RuntimeError("the attempt never settled")


async def probe_health(client, rec: Recorder, stop: asyncio.Event) -> None:
    """Is the server still answering? /health (no sign-in) and /v1/me (a signed-in request: token verification)."""
    from tests.authtools import make_token

    _, token = make_token(uuid.uuid4(), email="probe@load.test", expires_in=7200)
    while not stop.is_set():
        for name, url, headers in (("/health (probe)", "/health", {}),
                                   ("GET /v1/me (probe, signed in)", "/v1/me", {"Authorization": f"Bearer {token}"})):
            started = time.perf_counter()
            try:
                response = await client.get(url, headers=headers)
                rec.times[name].append((time.perf_counter() - started) * 1000)
                if response.status_code != 200:
                    rec.errors[name].append(str(response.status_code))
            except Exception as exc:                           # noqa: BLE001
                rec.errors[name].append(type(exc).__name__)
        await asyncio.sleep(0.25)


async def run_level(args, users: int) -> dict:
    import httpx
    from cryptography.hazmat.primitives import serialization

    from tests import authtools

    port = args.port
    pem = authtools._private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()).decode()
    server = subprocess.Popen([sys.executable, __file__, "--serve", "--port", str(port), "--eval-latency", str(args.eval_latency),
                               "--prose-latency", str(args.prose_latency), "--jitter", str(args.jitter),
                               "--rate-limit", str(args.rate_limit)] + (["--inline"] if args.inline else [])
                              + (["--profile"] if args.profile else []) + (["--legacy-threads"] if args.legacy_threads else [])
                              + (["--slow-code"] if args.slow_code else [])
                              + (["--default-threads", str(args.default_threads)] if args.default_threads else []),
                              cwd=str(ROOT), env={**os.environ, "LOAD_TEST_KEY_PEM": pem})
    base = f"http://127.0.0.1:{port}"
    try:
        limits = httpx.Limits(max_connections=users * 2 + 10, max_keepalive_connections=users * 2 + 10)
        async with httpx.AsyncClient(base_url=base, timeout=120, limits=limits) as client:
            for _ in range(100):
                try:
                    if (await client.get("/health")).status_code == 200:
                        break
                except Exception:                              # noqa: BLE001 - not up yet
                    pass
                await asyncio.sleep(0.2)
            before = (await client.get("/_load/")).json()
            await client.post("/_load/reset")
            rec, stop = Recorder(), asyncio.Event()
            prober = asyncio.create_task(probe_health(client, rec, stop))
            started = time.perf_counter()
            results = await asyncio.gather(*[one_user(client, rec, i, "he" if i % 4 == 3 else "en") for i in range(users)],
                                           return_exceptions=True)
            wall = time.perf_counter() - started
            stop.set()
            await prober
            after = (await client.get("/_load/")).json()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
    failures = [repr(r)[:160] for r in results if isinstance(r, BaseException)]
    return {"users": users, "wall_s": round(wall, 1), "completed": users - len(failures), "failures": failures[:5],
            "rss_before_mb": before.get("rss_mb"), "server": after, "times": rec.times, "errors": rec.errors,
            "flows": rec.flows, "notes": dict(rec.notes)}


def pct(values: list[float], p: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(p * (len(ordered) - 1))))]


def report(result: dict) -> str:
    s = result["server"]
    lines = [f"### {result['users']} users at once: {result['completed']}/{result['users']} flows completed in {result['wall_s']} s",
             "",
             f"server: memory {result['rss_before_mb']} -> {s.get('rss_mb')} MB, event-loop lag p50 {s['loop_lag_p50_ms']} ms / "
             f"p99 {s['loop_lag_p99_ms']} ms / max {s['loop_lag_max_ms']} ms, default thread pool {s['threads']} threads, "
             f"model calls {s['model_calls']}", ""]
    if result["notes"]:
        lines.append("notes: " + "; ".join(f"{k}: {v}" for k, v in result["notes"].items()))
        lines.append("")
    if result["failures"]:
        lines.append("failed flows (first 5): " + " | ".join(result["failures"]))
        lines.append("")
    lines += ["| endpoint | n | p50 | p95 | max | errors |", "|---|---:|---:|---:|---:|---|"]
    for name in sorted(result["times"]):
        v = result["times"][name]
        errors = result["errors"].get(name, [])
        summary = ", ".join(f"{e}×{errors.count(e)}" for e in sorted(set(errors))) if errors else ""
        lines.append(f"| {name} | {len(v)} | {pct(v, .5):.0f} ms | {pct(v, .95):.0f} ms | {max(v):.0f} ms | {summary} |")
    if result["flows"]:
        f = result["flows"]
        lines.append(f"| whole flow (per user) | {len(f)} | {pct(f, .5) / 1000:.1f} s | {pct(f, .95) / 1000:.1f} s | "
                     f"{max(f) / 1000:.1f} s | |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--users", type=int, nargs="*", default=[10, 50, 100])
    parser.add_argument("--eval-latency", type=float, default=8.0)
    parser.add_argument("--prose-latency", type=float, default=5.0)
    parser.add_argument("--jitter", type=float, default=0.25, help="standard deviation as a share of the mean")
    parser.add_argument("--rate-limit", type=float, default=0.0, help="share of evaluator calls that answer 429")
    parser.add_argument("--inline", action="store_true", help="the words inside submit (the old way)")
    parser.add_argument("--slow-code", action="store_true", help="code answers loop until the runner's 5 s timeout")
    parser.add_argument("--profile", action="store_true", help="cProfile the server's event loop, print the top")
    parser.add_argument("--legacy-threads", action="store_true",
                        help="the thread use before 2026-09-26 (code tests and key lookups in the default pool)")
    parser.add_argument("--default-threads", type=int, default=0, help="size the default thread pool like a small host")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    global SLOW_CODE
    SLOW_CODE = args.slow_code
    if args.serve:
        serve(args)
        return
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    results = []
    for users in args.users:
        result = asyncio.run(run_level(args, users))
        results.append(result)
        print(report(result), flush=True)
        if result["server"].get("profile"):
            print(result["server"]["profile"], flush=True)
        print(flush=True)
    if args.json:
        args.json.write_text(json.dumps(results, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
