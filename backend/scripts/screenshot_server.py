"""The local backend behind the screenshot harness (apps/web/tools/screenshots/run.mjs).

Two servers in one process, no database, no model, no cost:

* the JobRun API (uvicorn) with the in-memory store, a scripted model that answers instantly, and the TEST
  token verifier from tests/authtools.py (a signing key generated in this process; production code paths are
  untouched: the verifier is set on app.state exactly as the test-suite does);
* a stand-in for the few Supabase endpoints the web app calls in the browser (GoTrue `user`, `token`, `logout`;
  PostgREST `jr_members` and `jr_practice_entries`), with CORS, so the app believes it is signed in.

It writes a session file the harness injects into the browser's localStorage (the shape supabase-js stores):

    uv run python scripts/screenshot_server.py --api-port 8791 --stub-port 8792 --session-file <path>
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, Response          # module level: `from __future__ import annotations` turns the
from fastapi.middleware.cors import CORSMiddleware      # route signatures into strings FastAPI resolves from globals

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _harness_environment(web_origin: str) -> None:
    """Before app.main is imported: the app's CORS list and /health read the process settings, which would
    otherwise come from backend/.env (the real database and model). Environment variables win over the file."""
    os.environ["ALLOWED_ORIGINS"] = ",".join({web_origin, web_origin.replace("localhost", "127.0.0.1"),
                                              web_origin.replace("127.0.0.1", "localhost")})
    # /health reports the process settings and the web app switches to "demo mode" (hides XP, streak, grades) when the
    # provider is not anthropic; the runtime itself is built below with the scripted provider, so no model is called
    os.environ["LLM_PROVIDER"] = "anthropic"
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-screenshot-harness-no-calls"
    os.environ["DATABASE_URL"] = ""
    os.environ["ENV"] = "development"
    os.environ["REQUIRE_PILOT_MEMBERSHIP"] = "false"

SESSION_DAYS = 30


def build_api(user_id: uuid.UUID, email: str):
    from app.config import Settings
    from app.engine.catalog import load_catalog
    from app.engine.providers import LLMRequest, ScriptedProvider
    from app.main import app
    from app.repo.users import Access
    from app.runtime import build_runtime
    from app.services.memory_store import InMemoryStore
    from tests.authtools import make_verifier
    from tests.conftest import make_evaluation

    strong = make_evaluation(correctness=0.9, depth=0.8).model_dump()
    weak = make_evaluation(correctness=0.25, depth=0.2, misconceptions=["xor_confused_with_majority"]).model_dump()
    partial = make_evaluation(correctness=0.6, depth=0.5).model_dump()

    def respond(request: LLMRequest):
        if request.role == "evaluator":
            text = request.user.lower()
            return weak if "^" in text else partial if "partial" in text else strong
        if request.role == "generator":
            return {"question_text": "What changes if one sensor is stuck at 1? Write the new expression and say which "
                                     "rows of the truth table move.",
                    "question_archetype": "design", "expected_answer_outline": "the stuck input", "rubric_focus": []}
        if request.role == "feedback":
            return {"what_happened": "You built the alarm as an XOR of the three sensors, which fires on an odd count "
                                     "of ones, not on a majority.",
                    "why_it_matters": "Majority logic appears in voting circuits and fault-tolerant designs; "
                                      "an interviewer expects the sum-of-products form at once.",
                    "next_step": "Write the truth table for three inputs and read the rows with two or more ones.",
                    "your_reasoning_vs_reference": "You reasoned about 'more than one', but XOR is parity, not a count."}
        if request.role == "report":
            return ("## Summary\nA steady interview. Boolean algebra is solid; counters need one more pass on "
                    "synchronous reset.\n\n## Next\n- Counters with reset\n- Setup and hold arithmetic")
        return "Next time, write the truth table before the expression."

    catalog = load_catalog(ROOT / "seeds")
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True, suggest_reviewed_only=False,
                        interview_reviewed_only=False, interview_daily_limit=10_000, daily_attempt_limit=10_000)
    app.state.verifier = make_verifier()

    async def member(user) -> Access:
        return Access(user_id=user.id, email=user.email, is_member=True, can_manage_tasks=False, profile_created=False)
    app.state.access_resolver = member
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=ScriptedProvider(respond), store=InMemoryStore(catalog))
    return app


def build_stub(user_id: uuid.UUID, email: str, session: dict):
    """The Supabase endpoints the browser calls, answered the way supabase-js expects."""
    stub = FastAPI()
    stub.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], expose_headers=["*"])
    user = session["user"]

    @stub.get("/auth/v1/user")
    async def get_user():
        return user

    @stub.post("/auth/v1/token")
    async def token():
        return session

    @stub.post("/auth/v1/logout")
    async def logout():
        return Response(status_code=204)

    @stub.get("/rest/v1/jr_members")
    async def members():
        return [{"email": email, "can_manage_tasks": False}]

    @stub.api_route("/rest/v1/jr_practice_entries", methods=["GET", "POST", "PATCH", "DELETE"])
    async def entries(request: Request):
        if request.method == "GET":
            return []
        body = await request.json() if request.method in ("POST", "PATCH") else {}
        row = {"id": str(uuid.uuid4()), "user_id": str(user_id), "version": 1, **(body if isinstance(body, dict) else {})}
        return [row] if request.headers.get("prefer", "").startswith("return") else Response(status_code=201)

    @stub.get("/rest/v1/{table}")
    async def anything(table: str):
        return []

    @stub.get("/health")
    async def health():
        return {"status": "ok", "stub": True}

    return stub


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-port", type=int, default=8791)
    parser.add_argument("--stub-port", type=int, default=8792)
    parser.add_argument("--session-file", type=Path, required=True)
    parser.add_argument("--email", default="screenshots@example.com")
    parser.add_argument("--web-origin", default="http://localhost:3210")
    args = parser.parse_args()
    _harness_environment(args.web_origin)

    import uvicorn

    from tests.authtools import make_token

    user_id, token = make_token(email=args.email, expires_in=SESSION_DAYS * 86400)
    now = int(time.time())
    user = {"id": str(user_id), "aud": "authenticated", "role": "authenticated", "email": args.email,
            "email_confirmed_at": "2026-09-01T00:00:00Z", "app_metadata": {"provider": "email", "providers": ["email"]},
            "user_metadata": {"full_name": "Shaked"}, "identities": [], "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z", "is_anonymous": False}
    session = {"access_token": token, "token_type": "bearer", "expires_in": SESSION_DAYS * 86400,
               "expires_at": now + SESSION_DAYS * 86400, "refresh_token": "screenshot-refresh", "user": user}
    args.session_file.parent.mkdir(parents=True, exist_ok=True)
    args.session_file.write_text(json.dumps({"session": session, "api": f"http://127.0.0.1:{args.api_port}",
                                             "stub": f"http://127.0.0.1:{args.stub_port}"}), encoding="utf-8")

    api = uvicorn.Server(uvicorn.Config(build_api(user_id, args.email), host="127.0.0.1", port=args.api_port,
                                        log_level="warning", access_log=False))
    stub = uvicorn.Server(uvicorn.Config(build_stub(user_id, args.email, session), host="127.0.0.1", port=args.stub_port,
                                         log_level="warning", access_log=False))
    print(f"screenshot backend: api http://127.0.0.1:{args.api_port}  stub http://127.0.0.1:{args.stub_port}", flush=True)
    await asyncio.gather(api.serve(), stub.serve())


if __name__ == "__main__":
    asyncio.run(main())
