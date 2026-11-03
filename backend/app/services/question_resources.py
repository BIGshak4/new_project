"""Authenticated question illustrations and explicitly revealed solution resources.

Storage has no public/anonymous policy. URLs expire; the server signs only manifest paths.
Neither a question key nor another learner's attempt grants access to its solution.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import time
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.api.errors import ApiError
from app.engine.solution_review import SolutionReview

BUCKET = "question-bank-media"
PATH = re.compile(r"^prep-\d{3}/[a-f0-9]{20}-[\w.-]+$")


class ResourceMedia(BaseModel):
    id: str
    filename: str
    kind: str
    role: str
    caption: str = ""
    url: str


class QuestionResources(BaseModel):
    media: list[ResourceMedia] = Field(default_factory=list)
    # Full technical material, only after an OWNED attempt records reference exposure.
    technical_material: dict | None = None
    solution_revealed: bool = False
    reference: str | None = None
    solution_review: SolutionReview = Field(default_factory=SolutionReview)
    language: Literal["en", "he"]


def learner_media(media: list[dict], language: Literal["en", "he"] | None = None) -> list[dict]:
    """Archive screenshots are internal source records, not learner-facing illustrations.

    Preserve their provenance and the authored diagrams/code. This also applies to
    existing database manifests, without reseeding or changing learner attempts.
    """
    return [m for m in media
            if not str(m.get("source_path", "")).replace("\\", "/").startswith("sources/")
            and (language is None or m.get("language") in (None, language))]


async def sign_media(media: list[dict], base_url: str, service_key: str) -> list[ResourceMedia]:
    media = learner_media(media)
    if not media:
        return []
    if not base_url or not service_key:
        raise ApiError("temporarily_unavailable", "question media is not configured", status=503)
    if any(not PATH.fullmatch(m.get("path", "")) for m in media):
        raise ApiError("temporarily_unavailable", "question media manifest is invalid", status=503)
    base_url = base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=20, headers={"Authorization": f"Bearer {service_key}",
                                                         "apikey": service_key}) as client:
            response = await client.post(f"{base_url}/storage/v1/object/sign/{BUCKET}",
                                         json={"expiresIn": 1800, "paths": [m["path"] for m in media]})
            response.raise_for_status()
            signed = {row.get("path"): row.get("signedURL") for row in response.json()}
    except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
        raise ApiError("temporarily_unavailable", "question media could not be loaded; retry", status=503) from exc
    out = []
    for m in media:
        url = signed.get(m["path"])
        if not isinstance(url, str) or not url.startswith(f"/object/sign/{BUCKET}/"):
            raise ApiError("temporarily_unavailable", "a question resource is missing; retry", status=503)
        out.append(ResourceMedia(id=m["id"], filename=m["filename"], kind=m["kind"], role=m["role"],
                                 caption=m.get("caption", ""), url=base_url + "/storage/v1" + url))
    return out


# The figures of a question, once fetched and shrunk, are kept for a while: the judge's warm-up fetches them when the
# question is opened and the verdict a minute later must not download them again (Shaked, 2026-11-02, "cut the time").
IMAGE_CACHE_SECONDS = 600
IMAGE_CACHE_MAX = 64
_image_cache: dict[str, tuple[float, list[tuple[str, bytes]]]] = {}


def _cache_key(question, media: list[dict]) -> str:
    return question.key + "|" + ",".join(str(m.get("sha256", "")) for m in media)


def cached_images(question) -> list[tuple[str, bytes]] | None:
    """The question's figures if they were fetched recently (tests and the warm-up look here)."""
    media = [m for m in question.assets.get("bank_media", []) if m.get("role") == "prompt" and m.get("kind") == "image"]
    hit = _image_cache.get(_cache_key(question, media)) if media else None
    return list(hit[1]) if hit and hit[0] > time.monotonic() else None


async def _download(settings, media: list[dict]) -> list[tuple[str, bytes] | None]:
    from app.services.storage_images import sniff_image

    async with httpx.AsyncClient(timeout=20, headers={"Authorization": f"Bearer {settings.supabase_service_role_key}",
                                                     "apikey": settings.supabase_service_role_key}) as client:
        async def fetch(m):
            try:
                r = await client.get(f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{BUCKET}/{m['path']}")
                if (r.status_code != 200 or len(r.content) > 10 * 1024 * 1024
                        or hashlib.sha256(r.content).hexdigest() != m.get("sha256")):
                    return None
                mime = sniff_image(r.content)
                return (mime, r.content) if mime else None
            except httpx.HTTPError:
                return None
        return list(await asyncio.gather(*(fetch(m) for m in media)))


async def fetch_question_images(question) -> list[tuple[str, bytes]] | None:
    """Only curated prompt images, never a user's URL. None means do not guess an assessment. The pictures go to the
    model bounded to 1024 px on their long side, and a question's set is cached for ten minutes."""
    from app.config import get_settings
    from app.services.storage_images import shrink_image

    media = [m for m in question.assets.get("bank_media", []) if m.get("role") == "prompt" and m.get("kind") == "image"]
    if not media:
        return []
    key = _cache_key(question, media)
    hit = _image_cache.get(key)
    if hit is not None and hit[0] > time.monotonic():
        return list(hit[1])
    settings = get_settings()
    if not settings.supabase_service_role_key or any(not PATH.fullmatch(m.get("path", "")) for m in media):
        return None
    images = await _download(settings, media)
    if not all(image is not None for image in images):
        return None
    shrunk = [shrink_image(mime, data) for mime, data in images]
    if len(_image_cache) >= IMAGE_CACHE_MAX:
        for old in sorted(_image_cache, key=lambda k: _image_cache[k][0])[: IMAGE_CACHE_MAX // 4]:
            del _image_cache[old]
    _image_cache[key] = (time.monotonic() + IMAGE_CACHE_SECONDS, shrunk)
    return list(shrunk)
