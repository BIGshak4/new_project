"""Smoke-test a running API over real HTTP, without a login.

    uv run python scripts/smoke_http.py                       # starts uvicorn on a free port, tests it, stops it
    uv run python scripts/smoke_http.py --url https://...     # tests a deployed instance (stage G / Render)
    uv run python scripts/smoke_http.py --origin https://jobrun.netlify.app   # the origin to test CORS with

What is checked: /health, /docs, /openapi.json (every /v1 route present), CORS preflight from
the allowed origin (allowed) and from a stranger (refused), 401 error shape without a token,
404 and 405 error shapes, 413 for an oversized body, unknown-signature token is 401 not 500,
and that the project's JWKS is reachable and carries the signing key the verifier will use.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import jwt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402

V1_ROUTES = {
    ("GET", "/v1/me"), ("GET", "/v1/me/progress"), ("GET", "/v1/questions"), ("GET", "/v1/questions/{key_or_id}"),
    ("POST", "/v1/practice/attempts"), ("GET", "/v1/practice/attempts/{attempt_id}"),
    ("POST", "/v1/practice/attempts/{attempt_id}/hints/next"), ("POST", "/v1/practice/attempts/{attempt_id}/reference"),
    ("POST", "/v1/practice/attempts/{attempt_id}/submissions"),
    ("POST", "/v1/practice/attempts/{attempt_id}/follow-ups/{turn}/submissions"),
    ("POST", "/v1/practice/attempts/{attempt_id}/submissions/{revision}/retry"),
    # mock interviews
    ("POST", "/v1/interviews"), ("GET", "/v1/interviews"), ("GET", "/v1/interviews/{interview_id}"),
    ("POST", "/v1/interviews/{interview_id}/turns/{turn_index}/answer"),
    ("POST", "/v1/interviews/{interview_id}/hints/next"), ("POST", "/v1/interviews/{interview_id}/end"),
    ("GET", "/v1/interviews/{interview_id}/report"),
    # the goal, job types, company sightings (2026-09-23)
    ("GET", "/v1/me/goal"), ("POST", "/v1/me/goal"), ("GET", "/v1/job-types"), ("GET", "/v1/companies"),
    ("POST", "/v1/questions/{key_or_id}/sightings"),
}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int) -> subprocess.Popen:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port),
                             "--log-level", "warning"], cwd=Path(__file__).resolve().parent.parent, env=env)


async def wait_healthy(client: httpx.AsyncClient, seconds: float = 40) -> dict:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            response = await client.get("/health")
            if response.status_code == 200:
                return response.json()
        except httpx.HTTPError:
            pass
        await asyncio.sleep(0.5)
    raise SystemExit("the server did not become healthy in time")


async def run(base_url: str, origin: str) -> list[str]:
    failures: list[str] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if condition else 'FAIL'} {name}{(' - ' + detail) if detail and not condition else ''}")
        if not condition:
            failures.append(name)

    async with httpx.AsyncClient(base_url=base_url, timeout=30) as client:
        health = await wait_healthy(client)
        check("health", health.get("status") == "ok", str(health))
        check("auth configured", health.get("auth_configured") is True, str(health))
        print(f"       provider={health.get('llm_provider')} store={health.get('store')} env={health.get('env')}")

        docs = await client.get("/docs")
        check("docs page", docs.status_code == 200 and "swagger" in docs.text.lower())
        spec = (await client.get("/openapi.json")).json()
        routes = {(m.upper(), p) for p, ops in spec["paths"].items() if p.startswith("/v1") for m in ops}
        check(f"all {len(V1_ROUTES)} v1 routes", routes == V1_ROUTES, f"missing {V1_ROUTES - routes} extra {routes - V1_ROUTES}")

        preflight = await client.options("/v1/questions", headers={"Origin": origin, "Access-Control-Request-Method": "GET",
                                                                   "Access-Control-Request-Headers": "authorization"})
        check("CORS preflight from the allowed origin", preflight.status_code == 200
              and preflight.headers.get("access-control-allow-origin") == origin, f"{preflight.status_code} {dict(preflight.headers)}")
        stranger = await client.options("/v1/questions", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
        check("CORS preflight from a stranger is refused", "access-control-allow-origin" not in stranger.headers)

        no_token = await client.get("/v1/questions")
        check("401 without a token, error shape", no_token.status_code == 401
              and no_token.json().get("error", {}).get("code") == "unauthenticated"
              and no_token.headers.get("www-authenticate") == "Bearer", no_token.text[:200])
        check("request id header", bool(no_token.headers.get("x-request-id")))

        forged = jwt.encode({"sub": "00000000-0000-0000-0000-000000000000", "aud": "authenticated", "exp": int(time.time()) + 60,
                             "iss": (get_settings().supabase_url or "") + "/auth/v1"}, "not-the-key", algorithm="HS256")
        bad = await client.get("/v1/me", headers={"Authorization": f"Bearer {forged}"})
        check("forged token is 401 not 500", bad.status_code == 401, bad.text[:200])

        missing = await client.get("/v1/does-not-exist")
        check("404 error shape", missing.status_code == 404 and missing.json()["error"]["code"] == "not_found", missing.text[:200])
        wrong = await client.delete("/v1/questions")
        check("405 error shape", wrong.status_code == 405 and wrong.json()["error"]["code"] == "method_not_allowed", wrong.text[:200])
        huge = await client.post("/v1/practice/attempts", content=b"x" * (300 * 1024), headers={"Content-Type": "application/json"})
        check("413 for an oversized body", huge.status_code == 413, huge.text[:200])

        if get_settings().supabase_url:
            jwks = await client.get(get_settings().supabase_url.rstrip("/") + "/auth/v1/.well-known/jwks.json")
            keys = jwks.json().get("keys", []) if jwks.status_code == 200 else []
            check("project JWKS reachable with a signing key", any(k.get("use") == "sig" and k.get("kid") for k in keys),
                  f"{jwks.status_code} {jwks.text[:120]}")
            from app.auth import TokenVerifier
            verifier = TokenVerifier(supabase_url=get_settings().supabase_url)
            try:
                fetched = await asyncio.to_thread(verifier._jwks.get_jwk_set)
                check("verifier loads the JWKS", any(k.key_id for k in fetched.keys))
            except Exception as exc:                 # noqa: BLE001
                check("verifier loads the JWKS", False, repr(exc))
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="a running instance; without it uvicorn is started locally")
    parser.add_argument("--origin", default=None, help="browser origin to test CORS with (default: first ALLOWED_ORIGINS)")
    args = parser.parse_args()
    origin = args.origin or (get_settings().allowed_origins[0] if get_settings().allowed_origins else "http://localhost:3000")
    server = None
    base_url = args.url
    if base_url is None:
        port = free_port()
        server = start_server(port)
        base_url = f"http://127.0.0.1:{port}"
    print(f"smoke: {base_url} (origin {origin})")
    try:
        failures = asyncio.run(run(base_url, origin))
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=10)
    if failures:
        sys.exit(f"{len(failures)} check(s) failed: {', '.join(failures)}")
    print("all checks passed")


if __name__ == "__main__":
    main()
