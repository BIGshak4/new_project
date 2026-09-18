"""FastAPI application. Step 2 exposes health and a catalog summary; the practice,
plan and simulation routes arrive in step 4."""

from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.engine import ENGINE_VERSION
from app.engine.catalog import CatalogError, load_catalog

app = FastAPI(title="Interview Platform API", version=ENGINE_VERSION)


@app.get("/health")
async def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "engine_version": ENGINE_VERSION, "llm_provider": settings.llm_provider,
            "database_configured": bool(settings.database_url)}


@app.get("/catalog/summary")
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
