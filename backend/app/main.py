"""FastAPI application.

    /health              liveness, plus what is configured (never the values)
    /catalog/summary     seed validation summary
    /v1/me               the verified caller (step 4b, stage A)
    /v1/questions ...    step 4b, stages C-E
    /v1/practice ...     step 4b, stages C-E

The OpenAPI document at /docs is the contract the web app is written against.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.api import errors
from app.api.v1 import me
from app.auth import TokenVerifier
from app.config import get_settings
from app.engine import ENGINE_VERSION
from app.engine.catalog import CatalogError, load_catalog

log = logging.getLogger("app")


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
    yield
    await db.dispose()


app = FastAPI(title="JobRun practice API", version=ENGINE_VERSION, lifespan=lifespan)
errors.install(app)
app.add_middleware(
    CORSMiddleware, allow_origins=get_settings().allowed_origins, allow_credentials=False,
    allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])
app.include_router(me.router)


@app.get("/health", tags=["ops"])
async def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "engine_version": ENGINE_VERSION, "env": settings.env, "llm_provider": settings.llm_provider,
            "database_configured": bool(settings.database_url), "auth_configured": bool(settings.supabase_url),
            "allowed_origins": len(settings.allowed_origins)}


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
