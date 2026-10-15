"""FastAPI application.

    /health                          liveness, plus what is configured (never the values)
    /catalog/summary                 seed validation summary
    /v1/me, /v1/me/progress          the verified caller and their skill progress
    /v1/questions                    the catalog, safe shape
    /v1/practice/attempts ...        one practice question end to end

The OpenAPI document at /docs is the contract the web app is written against.

    LLM_PROVIDER=scripted   instant fake evaluations (default; for building the web app)
    DATABASE_URL unset      everything in memory, questions from the seed files
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import db
from app.api import errors
from app.api.v1 import interviews, me, meta, practice, questions
from app.auth import TokenVerifier
from app.config import get_settings
from app.engine import ENGINE_VERSION
from app.engine.catalog import CatalogError, load_catalog
from app.runtime import build_runtime

log = logging.getLogger("app")
access_log = logging.getLogger("app.access")
if not logging.getLogger().handlers:                 # plain `uvicorn` leaves the root logger silent: the access line was never emitted
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("app").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    problems = settings.production_problems()
    if settings.is_production and problems:
        raise RuntimeError("refusing to start in production: " + "; ".join(problems))
    for problem in problems:
        log.warning("configuration: %s", problem)
    if not hasattr(app.state, "verifier"):
        app.state.verifier = TokenVerifier(supabase_url=settings.supabase_url, jwt_secret=settings.supabase_jwt_secret)
    if not hasattr(app.state, "runtime"):
        app.state.runtime = build_runtime(settings)
        if app.state.runtime.store_kind == "database":
            try:
                await db.get_metadata()                   # reflect the schema now, not on the first user's request
            except Exception as exc:
                hints = settings.database_url_problems() or ["check DATABASE_URL: Supabase -> Connect -> Session pooler, "
                                                             "user postgres.<project-ref>, password percent-encoded"]
                raise RuntimeError(f"cannot reach the database ({type(exc).__name__}: {exc}). " + "; ".join(hints)) from exc
        log.info("runtime: provider=%s store=%s questions=%d", settings.llm_provider, app.state.runtime.store_kind,
                 len(app.state.runtime.catalog.questions))
        if settings.llm_provider != "anthropic" and app.state.runtime.store_kind == "database":
            log.warning("the %s provider is writing DEMO evaluations into the real database; every submission is "
                        "marked assessed_by=demo and must not be treated as real evidence", settings.llm_provider)
    yield
    runtime = getattr(app.state, "runtime", None)
    if runtime is not None:
        await runtime.aclose()
    await db.dispose()


app = FastAPI(title="JobRun practice API", version=ENGINE_VERSION, lifespan=lifespan,
              description="Sign in with Supabase, send the access token as a Bearer token. "
                          "Errors always look like {\"error\": {\"code\": ..., \"message\": ...}}.")
errors.install(app)
app.add_middleware(
    CORSMiddleware, allow_origins=get_settings().allowed_origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-Id"],
    expose_headers=["X-Request-Id"])
app.include_router(me.router)
app.include_router(questions.router)
app.include_router(practice.router)
app.include_router(interviews.router)
app.include_router(meta.router)


MAX_BODY_BYTES = 256 * 1024          # an answer is at most 20 000 characters; anything larger is not a request we serve
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
RATE_LIMIT_PER_MINUTE = 600          # per caller (token, else address); /health is exempt; 0 disables (review, 2026-10-15)


class BodyTooLarge(Exception):
    """Raised from the wrapped receive once more than MAX_BODY_BYTES arrived on the stream."""


def _too_large_response(request_id: str) -> JSONResponse:
    return JSONResponse({"error": {"code": "payload_too_large", "message": f"the request body exceeds {MAX_BODY_BYTES} bytes"}},
                        status_code=413, headers={"X-Request-Id": request_id})


class StreamLimits:
    """Pure ASGI middleware, outermost: counts the bytes that actually arrive (a chunked body has no Content-Length, so
    the header check alone let a 32 MiB anonymous body be buffered and parsed; review finding 2026-10-15), and keeps
    a small per-caller request budget so a single client cannot saturate the pool with rebuild-heavy reads."""

    def __init__(self, app):
        self.app = app
        self._buckets: dict[str, list[float]] = {}

    def _caller(self, scope) -> str:
        headers = {k.decode("latin-1").lower(): v for k, v in scope.get("headers", [])}
        token = headers.get(b"authorization".decode(), b"")
        if token:
            return "t:" + hashlib.sha256(token).hexdigest()[:16]
        client = scope.get("client") or ("?", 0)
        return "a:" + str(client[0])

    def _over_limit(self, caller: str) -> bool:
        if RATE_LIMIT_PER_MINUTE <= 0:
            return False
        now = time.monotonic()
        stamps = self._buckets.setdefault(caller, [])
        cutoff = now - 60
        while stamps and stamps[0] < cutoff:
            stamps.pop(0)
        if len(stamps) >= RATE_LIMIT_PER_MINUTE:
            return True
        stamps.append(now)
        if len(self._buckets) > 10_000:                                   # never grows without bound
            for key in [k for k, v in self._buckets.items() if not v or v[-1] < cutoff][:1000]:
                self._buckets.pop(key, None)
        return False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope.get("path") != "/health" and self._over_limit(self._caller(scope)):
            response = JSONResponse({"error": {"code": "usage_limit", "message": "too many requests; slow down for a minute"}},
                                    status_code=429, headers={"Retry-After": "60"})
            return await response(scope, receive, send)
        state = {"received": 0, "too_large": False, "started": False}
        body = json.dumps({"error": {"code": "payload_too_large",
                                     "message": f"the request body exceeds {MAX_BODY_BYTES} bytes"}}).encode()

        async def limited_receive():
            message = await receive()
            if message["type"] == "http.request":
                state["received"] += len(message.get("body", b""))
                if state["received"] > MAX_BODY_BYTES:
                    state["too_large"] = True
                    raise BodyTooLarge()                            # the framework turns this into its own 400 ...
            return message

        async def guarded_send(message):
            if state["too_large"]:                                  # ... which is replaced by the 413 here
                if message["type"] == "http.response.start":
                    state["started"] = True
                    await send({"type": "http.response.start", "status": 413,
                                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]})
                elif message["type"] == "http.response.body" and not state.get("sent"):
                    state["sent"] = True
                    await send({"type": "http.response.body", "body": body, "more_body": False})
                return
            if message["type"] == "http.response.start":
                state["started"] = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except BodyTooLarge:
            if not state["started"]:
                await _too_large_response(uuid.uuid4().hex[:12])(scope, receive, send)


app.add_middleware(StreamLimits)


@app.middleware("http")
async def request_log(request: Request, call_next):
    """One line per request: id, route, user, status, duration. Never the body, never a token."""
    offered = request.headers.get("X-Request-Id") or ""
    request_id = offered if REQUEST_ID_RE.match(offered) else uuid.uuid4().hex[:12]   # never reflected or logged raw
    request.state.request_id = request_id
    started = time.perf_counter()
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        return _too_large_response(request_id)
    path = request.url.path.replace("\n", " ").replace("\r", " ")
    try:
        response = await call_next(request)
    except BodyTooLarge:
        raise                                                   # answered by StreamLimits with a 413
    except Exception:
        access_log.exception("%s %s %s user=%s status=500 ms=%d", request_id, request.method, path,
                             getattr(request.state, "user_id", "-"), (time.perf_counter() - started) * 1000)
        return JSONResponse({"error": {"code": "internal", "message": "something went wrong on our side",
                                       "request_id": request_id}}, status_code=500, headers={"X-Request-Id": request_id})
    response.headers["X-Request-Id"] = request_id
    access_log.info("%s %s %s user=%s status=%d ms=%d", request_id, request.method, path,
                    getattr(request.state, "user_id", "-"), response.status_code, (time.perf_counter() - started) * 1000)
    return response


_db_probe: dict = {}


async def _database_round_trip() -> dict:
    """Median of three `select 1` round trips on a pooled connection, plus the pool's state. Kept for 10 s so an
    unauthenticated caller cannot turn /health into database load."""
    now = time.monotonic()
    if _db_probe.get("at", -1e9) > now - 10:
        return _db_probe["value"]
    from sqlalchemy import text

    engine = db.get_engine()
    timings = []
    async with engine.connect() as connection:
        for _ in range(3):
            started = time.perf_counter()
            await connection.execute(text("select 1"))
            timings.append((time.perf_counter() - started) * 1000)
    pool = engine.pool
    value = {"round_trip_ms": round(sorted(timings)[1], 2), "pool_size": pool.size(), "pool_checked_out": pool.checkedout(),
             "pool_overflow": pool.overflow()}
    _db_probe.update(at=now, value=value)
    return value


@app.get("/health", tags=["ops"])
async def health(db_check: bool = False) -> dict:
    """`?db_check=true` also measures one database round trip (cached 10 s)."""
    settings = get_settings()
    runtime = getattr(app.state, "runtime", None)
    body = {"status": "ok", "engine_version": ENGINE_VERSION, "env": settings.env, "llm_provider": settings.llm_provider,
            "database_configured": bool(settings.database_url), "database_host": settings.database_host_kind,
            "database_pooler": settings.database_pooler_mode,
            "auth_configured": bool(settings.supabase_url),
            "allowed_origins": len(settings.allowed_origins), "store": runtime.store_kind if runtime else None,
            "models": {"evaluator": settings.anthropic_model, **settings.role_models} if settings.llm_provider == "anthropic" else None,
            "answer_images": "assessed" if settings.supabase_service_role_key and settings.supabase_url else "stored_only"}
    if db_check and runtime is not None and runtime.store_kind == "database":
        try:
            body["database"] = await _database_round_trip()
        except Exception as exc:                                  # noqa: BLE001 - reported, never raised
            body["database"] = {"error": type(exc).__name__}
    return body


@app.get("/catalog/summary", tags=["ops"])
async def catalog_summary() -> dict:
    # the catalog the process serves, loaded and validated at startup (reloading it here cost ~35 ms of blocking
    # work on the event loop for every unauthenticated request)
    runtime = getattr(app.state, "runtime", None)
    if runtime is not None:
        catalog = runtime.catalog
    else:
        try:
            catalog = await asyncio.to_thread(load_catalog, get_settings().seeds_dir)
        except CatalogError as exc:
            return {"valid": False, "problems": exc.problems}
    return {
        "valid": True, "subjects": sorted(catalog.domains), "skills": len(catalog.leaf_skills),
        "roles": sorted(catalog.roles), "companies": sorted(catalog.companies),
        "questions": len(catalog.questions), "tips": len(catalog.tips), "glossary_terms": len(catalog.glossary),
    }
