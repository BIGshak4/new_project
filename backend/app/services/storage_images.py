"""Answer images from the private Supabase Storage bucket, fetched server-side for the evaluator.

The browser uploads to `practice-answer-images/<user>/<attempt>/<file>.<ext>` under Storage RLS;
the backend verifies the locator belongs to the same user and attempt before it is stored
(Harel's visual-answer handoff). Reading the bytes needs the project's service-role key, which
never leaves the server. The bytes are sniffed again here: whatever the upload said, only a
real PNG, JPEG or WebP goes to the model.
"""

from __future__ import annotations

import asyncio
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
        shrunk = await asyncio.to_thread(shrink_image, mime, data)     # bounded size for the model (2026-11-02)
        if shrunk is None:
            log.warning("image rejected path=%s reason=too many pixels", path)
        return shrunk

    async def aclose(self) -> None:
        await self.client.aclose()


# Shaked, 2026-11-02 ("cut the time"): the judge read every figure and photo at full size. A diagram or a waveform
# is as readable at this size, and the model's image tokens and vision time shrink with the pixels. Applied to
# question figures and to answer photos (phone photos are usually 3,000-4,000 px wide).
MAX_IMAGE_SIDE = 1024
JPEG_QUALITY = 85
# A 5 MB flat PNG can declare 13,000 x 13,000 pixels and decode to 700 MB; Pillow only refuses above twice its own
# default (~179 Mpx). The header is read before any decode and a picture above this is dropped, never sent as is
# (security review SEC-017, 2026-11-08). Phone photos are 12-50 Mpx.
MAX_IMAGE_PIXELS = 60_000_000


def shrink_image(mime: str, data: bytes, *, max_side: int = MAX_IMAGE_SIDE) -> tuple[str, bytes] | None:
    """The same picture bounded to `max_side` pixels on its long side; unchanged when already small enough or when
    it cannot be decoded (the original bytes then go to the model as before). Never raises."""
    try:
        import io

        from PIL import Image, ImageOps

        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS                 # Pillow refuses above twice this at open()
        with Image.open(io.BytesIO(data)) as image:
            declared_w, declared_h = image.size                # the header only; nothing is decoded yet
            if declared_w * declared_h > MAX_IMAGE_PIXELS:
                log.warning("image dropped: %dx%d px declared, above %d (%s, %d bytes)",
                            declared_w, declared_h, MAX_IMAGE_PIXELS, mime, len(data))
                return None
            image = ImageOps.exif_transpose(image)            # phone photos carry their rotation in EXIF
            width, height = image.size
            longest = max(width, height)
            if longest <= max_side:
                return mime, data
            scale = max_side / longest
            work = image.convert("RGBA") if image.mode in ("P", "1", "LA", "PA") else image
            resized = work.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.LANCZOS)
            out = io.BytesIO()
            if mime == "image/jpeg":
                if resized.mode not in ("RGB", "L"):
                    resized = resized.convert("RGB")
                resized.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
                return "image/jpeg", out.getvalue()
            # PNG and WebP are diagrams, waveforms, screenshots: resampling smears their few colours into thousands
            # of shades and a bigger file, so transparency goes onto white and the picture is quantised back to 256
            # colours without dithering (lines and text stay crisp)
            if "A" in resized.mode:
                white = Image.new("RGBA", resized.size, (255, 255, 255, 255))
                resized = Image.alpha_composite(white, resized.convert("RGBA"))
            resized = resized.convert("RGB").quantize(colors=256, dither=Image.Dither.NONE)
            resized.save(out, format="PNG", optimize=True)
            return "image/png", out.getvalue()
    except Exception as exc:                                   # noqa: BLE001 - a picture must never cost an answer
        if type(exc).__name__ == "DecompressionBombError":     # Pillow's own refusal, raised inside open()
            log.warning("image dropped: %s (%s, %d bytes)", exc, mime, len(data))
            return None
        log.warning("image could not be shrunk; sent as is (%s, %d bytes)", mime, len(data))
        return mime, data
