"""Offline regressions for request budgets and inexpensive liveness checks."""
from __future__ import annotations

import asyncio
import json
import shlex
from pathlib import Path
from types import SimpleNamespace

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import main


async def test_health_exposes_only_a_valid_public_deployment_revision(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "a" * 40)
    assert (await main.health())["source_revision"] == "a" * 40
    monkeypatch.setenv("RENDER_GIT_COMMIT", "not-a-public-commit")
    assert (await main.health())["source_revision"] is None


async def respond_ok(scope, receive, send):
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


async def request(limiter, *, token="same", path="/v1/me", query=b"", forwarded="203.0.113.1",
                  peer="192.0.2.10"):
    messages = []
    scope = {"type": "http", "method": "GET", "path": path, "query_string": query,
             "scheme": "http", "client": (peer, 50000),
             "headers": [(b"authorization", f"Bearer {token}".encode()),
                         (b"x-forwarded-for", forwarded.encode()), (b"x-forwarded-proto", b"https")]}

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await limiter(scope, receive, send)
    return next(message["status"] for message in messages if message["type"] == "http.response.start")


def deployed_proxy_allowlist():
    dockerfile = Path(__file__).resolve().parent.parent / "Dockerfile"
    command = next(json.loads(line.removeprefix("CMD ")) for line in dockerfile.read_text().splitlines()
                   if line.startswith("CMD ["))
    return next(argument.split("=", 1)[1] for argument in shlex.split(command[-1])
                if argument.startswith("--forwarded-allow-ips="))


async def test_deployed_proxy_policy_preserves_network_budget_with_prefixed_forwarding_chain(monkeypatch):
    monkeypatch.setattr(main, "NETWORK_RATE_LIMIT_PER_MINUTE", 3)

    async def statuses(trusted_hosts):
        middleware = ProxyHeadersMiddleware(main.StreamLimits(respond_ok), trusted_hosts=trusted_hosts)
        return [await request(middleware, token=f"rotated-{index}", peer="10.1.2.3",
                              forwarded=f"198.51.100.{index}, 203.0.113.50") for index in range(6)]

    # The historical wildcard chooses the injected leftmost address. Restricted
    # trust selects the fixed first untrusted hop, so token/header churn stays bounded.
    assert await statuses("*") == [204] * 6
    assert await statuses(deployed_proxy_allowlist()) == [204] * 3 + [429] * 3


async def test_public_direct_peer_cannot_supply_forwarded_identity_or_scheme():
    scopes = []

    async def capture(scope, receive, send):
        scopes.append((scope["client"], scope["scheme"]))
        await respond_ok(scope, receive, send)

    proxy = ProxyHeadersMiddleware(capture, trusted_hosts=deployed_proxy_allowlist())
    assert await request(proxy, peer="198.51.100.10", forwarded="203.0.113.99") == 204
    assert scopes == [(("198.51.100.10", 50000), "http")]


async def test_trusted_private_proxy_preserves_https_and_actual_public_client():
    scopes = []

    async def capture(scope, receive, send):
        scopes.append((scope["client"], scope["scheme"]))
        await respond_ok(scope, receive, send)

    proxy = ProxyHeadersMiddleware(capture, trusted_hosts=deployed_proxy_allowlist())
    assert await request(proxy, peer="10.1.2.3", forwarded="203.0.113.99") == 204
    assert scopes == [(("203.0.113.99", 0), "https")]


async def test_rotating_unverified_headers_cannot_reset_the_network_allowance(monkeypatch):
    monkeypatch.setattr(main, "RATE_LIMIT_PER_MINUTE", 3)
    monkeypatch.setattr(main, "NETWORK_RATE_LIMIT_PER_MINUTE", 5, raising=False)
    limiter = main.StreamLimits(respond_ok)
    statuses = [await request(limiter, token=f"not-a-jwt-{i}", forwarded=f"203.0.113.{i}") for i in range(8)]
    assert statuses == [204] * 5 + [429] * 3


def test_fresh_bucket_churn_has_a_hard_memory_bound(monkeypatch):
    monkeypatch.setattr(main, "MAX_RATE_LIMIT_BUCKETS", 4, raising=False)
    limiter = main.StreamLimits(respond_ok)
    for index in range(100):
        assert not limiter._over_limit(f"fresh-caller-{index}")
    assert len(limiter._buckets) <= 4


async def test_only_cheap_health_is_exempt_from_network_budget(monkeypatch):
    monkeypatch.setattr(main, "NETWORK_RATE_LIMIT_PER_MINUTE", 2, raising=False)
    limiter = main.StreamLimits(respond_ok)
    assert await request(limiter, token="one") == 204
    assert await request(limiter, token="two") == 204
    assert await request(limiter, token="three") == 429
    assert await request(limiter, path="/health") == 204
    assert await request(limiter, path="/health", query=b"db_check=true") == 429


class ProbeEngine:
    def __init__(self, *, block=False):
        self.started, self.release = asyncio.Event(), asyncio.Event()
        self.block = block
        self.opened, self.queries = 0, 0
        self.pool = SimpleNamespace(size=lambda: 5, checkedout=lambda: 0, overflow=lambda: 0)

    def connect(self):
        engine = self

        class Connection:
            async def __aenter__(self):
                engine.opened += 1
                engine.started.set()
                if engine.block:
                    await engine.release.wait()
                return self

            async def __aexit__(self, *args):
                return False

            async def execute(self, query):
                engine.queries += 1
                await asyncio.sleep(0)

        return Connection()


async def test_concurrent_health_database_cache_misses_share_one_probe(monkeypatch):
    engine = ProbeEngine(block=True)
    monkeypatch.setattr(main.db, "get_engine", lambda: engine)
    monkeypatch.setattr(main, "_db_probe", {})
    monkeypatch.setattr(main, "_db_probe_lock", asyncio.Lock(), raising=False)
    tasks = [asyncio.create_task(main._database_round_trip()) for _ in range(16)]
    await asyncio.wait_for(engine.started.wait(), 1)
    await asyncio.sleep(0)
    engine.release.set()
    results = await asyncio.wait_for(asyncio.gather(*tasks), 2)
    assert engine.opened == 1 and engine.queries == 3
    assert all(result == results[0] for result in results)


async def test_slow_database_probe_is_bounded_and_failure_is_briefly_cached(monkeypatch):
    engine = ProbeEngine(block=True)
    monkeypatch.setattr(main.db, "get_engine", lambda: engine)
    monkeypatch.setattr(main, "_db_probe", {})
    monkeypatch.setattr(main, "_db_probe_lock", asyncio.Lock(), raising=False)
    monkeypatch.setattr(main, "DB_PROBE_TIMEOUT_SECONDS", 0.01, raising=False)
    result = await asyncio.wait_for(main._database_round_trip(), 0.5)
    assert result == {"error": "TimeoutError"}
    assert await main._database_round_trip() == result
    assert engine.opened == 1
