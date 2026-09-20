"""Answer images from the private Supabase Storage bucket, fetched server-side for the evaluator.

The browser uploads to `practice-answer-images/<user>/<attempt>/<file>.<ext>` under Storage RLS;
the backend verifies the locator belongs to the same user and attempt before it is stored
(Harel's visual-answer handoff). Reading the bytes needs the project's service-role key, which
never leaves the server. The bytes are sniffed again here: whatever the upload said, only a
real PNG, JPEG or WebP goes to the model.
"""

from __future__ import annotations

import logging

import httpx

log = logging.getLogger("app.images")

BUCKET = "practice-answer-images"
MAX_BYTES = 5 * 1024 * 1024


def sniff_image(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


class StorageImageFetcher:
    """Callable: path -> (mime, bytes) or None. Never raises into the evaluation."""

    def __init__(self, supabase_url: str, service_role_key: str, *, timeout_seconds: float = 15.0,
                 client: httpx.AsyncClient | None = None):
        self.base_url = supabase_url.rstrip("/")
        self.client = client or httpx.AsyncClient(
            timeout=timeout_seconds, headers={"Authorization": f"Bearer {service_role_key}", "apikey": service_role_key})

    async def __call__(self, path: str) -> tuple[str, bytes] | None:
        url = f"{self.base_url}/storage/v1/object/{BUCKET}/{path}"
        try:
            response = await self.client.get(url)
        except httpx.HTTPError as exc:
            log.warning("image fetch failed path=%s error=%s", path, exc)
            return None
        if response.status_code != 200:
            log.warning("image fetch refused path=%s status=%s", path, response.status_code)
            return None
        data = response.content
        if not data or len(data) > MAX_BYTES:
            log.warning("image rejected path=%s bytes=%s", path, len(data))
            return None
        mime = sniff_image(data)
        if mime is None:
            log.warning("image rejected path=%s reason=not an image", path)
            return None
        return mime, data

    async def aclose(self) -> None:
        await self.client.aclose()
