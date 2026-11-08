"""Regression tests for the security review of 2026-11-08 (security/runs/2026-11-08-full-review.md).

SEC-015 the payment webhook without payment keys, SEC-016 a padded answer against the numeric checker,
SEC-017 a picture that declares more pixels than we decode, SEC-019 the production start guard and its warnings,
SEC-021 the code runner's running-slot count per member, and the API's security headers.
"""

from __future__ import annotations

import struct
import time
import zlib

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.engine.checks import locate_named_value
from app.main import app
from app.repo.executions import MemoryExecutionLedger
from app.services.billing import FakeStripe
from app.services.storage_images import MAX_IMAGE_PIXELS, shrink_image
from tests.test_judge_warm import png_bytes


class TestWebhookWithoutKeys:
    def test_the_fake_gateway_has_no_secret_unless_one_is_injected(self):
        assert FakeStripe().secret is None
        assert FakeStripe(secret="whsec_test").secret == "whsec_test"

    def test_verify_is_a_404_without_a_secret_whatever_the_signature(self):
        payload = b'{"id": "evt_1", "type": "checkout.session.completed"}'
        forged = FakeStripe(secret="whsec_test").sign(payload)
        with pytest.raises(Exception) as caught:
            FakeStripe().verify(payload, forged)
        assert getattr(caught.value, "code", None) == "not_found"
        with pytest.raises(RuntimeError):
            FakeStripe().sign(payload)


class TestPaddedAnswerAgainstTheNumericChecker:
    def test_a_long_run_of_blanks_costs_milliseconds_and_the_value_is_still_found(self):
        answer = "Tmin = 1.40 ns" + " " * 19_000 + ", and that is all"
        started = time.perf_counter()
        found = locate_named_value(answer, ["Tmin", "T_min", "T min", "minimum clock period"], expected_base="s",
                                   base_units={"s"})
        assert time.perf_counter() - started < 0.5
        assert found == "1.40 ns"

    def test_blank_runs_with_newlines_keep_the_clause_break(self):
        answer = "Tmin = 1.40 ns" + " \n" * 9_000 + "fmax = 714 MHz"
        started = time.perf_counter()
        assert locate_named_value(answer, ["Tmin"]) == "1.40 ns"
        assert time.perf_counter() - started < 0.5


def png_declaring(width: int, height: int) -> bytes:
    """A valid PNG whose header declares `width x height` but whose data is one grey pixel: what a decompression
    bomb looks like to a header read."""
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    idat = zlib.compress(b"\x00\x80")
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


class TestPixelCap:
    def test_a_picture_above_the_cap_is_dropped_before_any_decode(self):
        bomb = png_declaring(13_000, 13_000)
        assert MAX_IMAGE_PIXELS < 13_000 * 13_000
        started = time.perf_counter()
        assert shrink_image("image/png", bomb) is None
        assert time.perf_counter() - started < 0.5

    def test_an_ordinary_picture_still_shrinks(self):
        mime, data = shrink_image("image/png", png_bytes(1600, 400))
        assert mime == "image/png" and len(data) > 0


class TestProductionGuard:
    def _ready(self, **over) -> Settings:
        base = dict(_env_file=None, env="production", llm_provider="openai", openai_api_key="k",
                    supabase_url="https://abc.supabase.co", allowed_origins="https://site.test",
                    database_url="postgresql://postgres.abc:pw@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
                    require_pilot_membership=True)
        base.update(over)
        return Settings(**base)

    def test_in_review_content_is_a_warning_not_a_refusal(self):
        s = self._ready(allow_in_review_content=True)
        assert s.production_problems() == []
        assert any("ALLOW_IN_REVIEW_CONTENT" in w for w in s.production_warnings())

    def test_wildcard_origins_and_payment_without_keys_refuse(self):
        assert any("*" in p for p in self._ready(allowed_origins="*").production_problems())
        assert any("REQUIRE_PAYMENT" in p for p in self._ready(require_payment=True).production_problems())
        assert self._ready(require_payment=True, stripe_secret_key="sk_test_x").production_problems() == []

    def test_the_open_operator_items_are_warned_about(self):
        words = "\n".join(self._ready().production_warnings())
        assert "HEALTH_KEY" in words
        assert "HEALTH_KEY" not in "\n".join(self._ready(health_key="h").production_warnings())

    def test_health_key_is_stripped_like_the_other_pasted_values(self):
        assert self._ready(health_key=" h\n").health_key == "h"


class TestCodeRunnerSlotsPerMember:
    async def test_one_member_cannot_hold_another_members_slots(self):
        ledger = MemoryExecutionLedger(daily=10, per_minute=5, concurrent=2)
        await ledger.reserve("user-a", "practice", "k1", "d1")
        await ledger.reserve("user-a", "practice", "k2", "d2")
        with pytest.raises(Exception) as caught:
            await ledger.reserve("user-a", "practice", "k3", "d3")
        assert getattr(caught.value, "code", None) == "usage_limit"
        run_id, _ = await ledger.reserve("user-b", "practice", "k1", "d1")        # b's own slots are free
        assert run_id


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestSecurityHeaders:
    async def test_every_response_carries_them(self, client):
        health = await client.get("/health")
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert health.headers["strict-transport-security"].startswith("max-age=")
        assert health.headers["referrer-policy"] == "no-referrer"
        missing = await client.get("/v1/does-not-exist")
        assert missing.status_code in (401, 404) and missing.headers["cache-control"] == "no-store"
