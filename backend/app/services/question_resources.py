"""Authenticated question illustrations and explicitly revealed solution resources.

Storage has no public/anonymous policy. URLs expire; the server signs only manifest paths.
Neither a question key nor another learner's attempt grants access to its solution.
"""
from __future__ import annotations

import re
import asyncio
import hashlib

import httpx
from pydantic import BaseModel, Field

from app.api.errors import ApiError

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


async def sign_media(media: list[dict], base_url: str, service_key: str) -> list[ResourceMedia]:
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


async def fetch_question_images(question) -> list[tuple[str, bytes]] | None:
    """Only curated prompt images, never a user's URL. None means do not guess an assessment."""
    from app.config import get_settings
    from app.services.storage_images import sniff_image

    media = [m for m in question.assets.get("bank_media", []) if m.get("role") == "prompt" and m.get("kind") == "image"]
    if not media:
        return []
    settings = get_settings()
    if not settings.supabase_service_role_key or any(not PATH.fullmatch(m.get("path", "")) for m in media):
        return None
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
        images = await asyncio.gather(*(fetch(m) for m in media))
    return images if all(image is not None for image in images) else None
