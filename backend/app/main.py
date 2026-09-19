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

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import db
from app.api import errors
from app.api.v1 import me, practice, questions
from app.auth import TokenVerifier
from app.config import get_settings
from app.engine import ENGINE_VERSION
from app.engine.catalog import CatalogError, load_catalog
from app.runtime import build_runtime

log = logging.getLogger("app")
access_log = logging.getLogger("app.access")


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
    yield
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


MAX_BODY_BYTES = 256 * 1024          # an answer is at most 20 000 characters; anything larger is not a request we serve


@app.middleware("http")
async def request_log(request: Request, call_next):
    """One line per request: id, route, user, status, duration. Never the body, never a token."""
    request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:12]
    request.state.request_id = request_id
    started = time.perf_counter()
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        return JSONResponse({"error": {"code": "payload_too_large", "message": f"the request body exceeds {MAX_BODY_BYTES} bytes"}},
                            status_code=413, headers={"X-Request-Id": request_id})
    try:
        response = await call_next(request)
    except Exception:
        access_log.exception("%s %s %s user=%s status=500 ms=%d", request_id, request.method, request.url.path,
                             getattr(request.state, "user_id", "-"), (time.perf_counter() - started) * 1000)
        return JSONResponse({"error": {"code": "internal", "message": "something went wrong on our side",
                                       "request_id": request_id}}, status_code=500, headers={"X-Request-Id": request_id})
    response.headers["X-Request-Id"] = request_id
    access_log.info("%s %s %s user=%s status=%d ms=%d", request_id, request.method, request.url.path,
                    getattr(request.state, "user_id", "-"), response.status_code, (time.perf_counter() - started) * 1000)
    return response


@app.get("/health", tags=["ops"])
async def health() -> dict:
    settings = get_settings()
    runtime = getattr(app.state, "runtime", None)
    return {"status": "ok", "engine_version": ENGINE_VERSION, "env": settings.env, "llm_provider": settings.llm_provider,
            "database_configured": bool(settings.database_url), "database_host": settings.database_host_kind,
            "auth_configured": bool(settings.supabase_url),
            "allowed_origins": len(settings.allowed_origins), "store": runtime.store_kind if runtime else None}


@app.get("/catalog/summary", tags=["ops"])
async def catalog_summary() -> dict:
    try:
        catalog = load_catalog(get_settings().seeds_dir)
    except CatalogError as exc:
        return {"valid": False, "problems": exc.problems}
    return {
        "valid": True, "subjects": sorted(catalog.domains), "skills": len(catalog.leaf_skills),
        "roles": sorted(catalog.roles), "companies": sorted(catalog.companies),
        "questions": len(catalog.questions), "tips": len(catalog.tips), "glossary_terms": len(catalog.glossary),
    }
