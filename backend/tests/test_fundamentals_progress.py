"""Short-card completion is authenticated, owner-scoped, revision-aware and ungraded."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column, DateTime, MetaData, String, Table, Uuid
from sqlalchemy.dialects import postgresql

from app import db
from app.api.errors import ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.repo.fundamentals import DbFundamentalsRepository, MemoryFundamentalsRepository
from app.runtime import build_runtime
from app.services.fundamentals import FundamentalsService, load_fundamentals_catalog
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver

BACKEND = Path(__file__).resolve().parents[1]
SEEDS = BACKEND / "seeds"
MEMBER = "tester@example.com"
KEY = "quick-sw-01"


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(monkeypatch):
    settings = Settings(_env_file=None, database_url=None, llm_provider="scripted", seeds_dir=SEEDS,
                        supabase_url=None, supabase_service_role_key=None)
    catalog = load_catalog(SEEDS)
    runtime = build_runtime(settings, catalog=catalog, store=InMemoryStore(catalog))
    monkeypatch.setattr(app.state, "runtime", runtime, raising=False)
    monkeypatch.setattr(app.state, "verifier", make_verifier(), raising=False)
    monkeypatch.setattr(app.state, "access_resolver", member_resolver({MEMBER}), raising=False)
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value, runtime


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/v1/fundamentals/progress", None),
    ("PUT", f"/v1/fundamentals/progress/{KEY}", {"content_revision": "a" * 64}),
    ("DELETE", f"/v1/fundamentals/progress/{KEY}", None),
])
async def test_every_progress_operation_requires_authentication(client, method, path, body):
    http, _ = client
    response = await http.request(method, path, json=body)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


async def test_authenticated_non_member_has_no_progress_access(client):
    http, _ = client
    _, token = make_token(email="not-in-pilot@example.com")
    response = await http.get("/v1/fundamentals/progress", headers=headers(token))
    assert response.status_code == 403


async def test_complete_is_idempotent_and_only_owner_can_read_or_remove_it(client):
    http, runtime = client
    user_a, token_a = make_token()
    user_b, token_b = make_token()
    revision = runtime.fundamentals.revisions[KEY]
    url = f"/v1/fundamentals/progress/{KEY}"
    first = await http.put(url, headers=headers(token_a), json={"content_revision": revision})
    assert first.status_code == 200
    record = first.json()
    assert set(record) == {"question_key", "content_revision", "completed_at"}
    assert record["question_key"] == KEY and record["content_revision"] == revision
    again = await http.put(url, headers=headers(token_a), json={"content_revision": revision})
    assert again.json() == record
    assert (await http.get("/v1/fundamentals/progress", headers=headers(token_a))).json() == {"completed": [record]}
    assert (await http.get("/v1/fundamentals/progress", headers=headers(token_b),
                           params={"user_id": str(user_a)})).json() == {"completed": []}
    assert (await http.delete(url, headers=headers(token_b))).json() == {"removed": False}
    assert len(await runtime.fundamentals.repository.list_completed(user_a)) == 1
    await http.put(url, headers=headers(token_b), json={"content_revision": revision})
    assert (await http.delete(url, headers=headers(token_a))).json() == {"removed": True}
    assert (await http.delete(url, headers=headers(token_a))).json() == {"removed": False}
    assert not await runtime.fundamentals.repository.list_completed(user_a)
    assert len(await runtime.fundamentals.repository.list_completed(user_b)) == 1


async def test_user_ids_and_extra_properties_cannot_be_injected(client):
    http, runtime = client
    _, token = make_token()
    response = await http.put(f"/v1/fundamentals/progress/{KEY}", headers=headers(token), json={
        "content_revision": runtime.fundamentals.revisions[KEY], "user_id": str(uuid.uuid4())})
    assert response.status_code == 422
    assert runtime.fundamentals.repository.rows == {}


async def test_unknown_keys_stale_revisions_and_malformed_hashes_do_not_write(client):
    http, runtime = client
    _, token = make_token()
    auth = headers(token)
    unknown = await http.put("/v1/fundamentals/progress/invented-question", headers=auth,
                             json={"content_revision": "a" * 64})
    assert unknown.status_code == 404
    assert (await http.delete("/v1/fundamentals/progress/invented-question", headers=auth)).status_code == 404
    stale = await http.put(f"/v1/fundamentals/progress/{KEY}", headers=auth, json={"content_revision": "a" * 64})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "stale_version"
    for revision in ("invalid", "A" * 64, "a" * 63, None):
        invalid = await http.put(f"/v1/fundamentals/progress/{KEY}", headers=auth, json={"content_revision": revision})
        assert invalid.status_code == 422
    assert runtime.fundamentals.repository.rows == {}


async def test_completion_changes_no_attempts_grades_metrics_profiles_or_xp(client):
    http, runtime = client
    _, token = make_token()
    before = (dict(runtime.store.attempts), dict(runtime.store.profiles), list(runtime.store.metrics),
              list(runtime.store.usage))
    response = await http.put(f"/v1/fundamentals/progress/{KEY}", headers=headers(token),
                              json={"content_revision": runtime.fundamentals.revisions[KEY]})
    assert response.status_code == 200
    assert (runtime.store.attempts, runtime.store.profiles, runtime.store.metrics, runtime.store.usage) == before


@pytest.mark.parametrize("key", ["quick-hw-61", "quick-hw-100", "quick-sw-61", "quick-sw-88", "quick-sw-89", "quick-sw-100"])
async def test_expansion_cards_use_the_same_authenticated_completion_flow(client, key):
    http, runtime = client
    _, token = make_token()
    revision = runtime.fundamentals.revisions[key]
    url = f"/v1/fundamentals/progress/{key}"
    response = await http.put(url, headers=headers(token), json={"content_revision": revision})
    assert response.status_code == 200
    record = response.json()
    assert record["question_key"] == key and record["content_revision"] == revision
    assert (await http.get("/v1/fundamentals/progress", headers=headers(token))).json() == {"completed": [record]}
    assert (await http.delete(url, headers=headers(token))).json() == {"removed": True}


async def test_concurrent_repeat_completion_has_one_unchanged_record():
    repository = MemoryFundamentalsRepository()
    service = FundamentalsService(repository, {KEY: "a" * 64})
    owner = uuid.uuid4()
    rows = await asyncio.gather(*(service.complete(owner, KEY, "a" * 64) for _ in range(12)))
    assert len(repository.rows) == 1 and all(row == rows[0] for row in rows)


async def test_old_revision_remains_identifiable_until_the_new_revision_is_finished():
    repository = MemoryFundamentalsRepository()
    owner = uuid.uuid4()
    old_service = FundamentalsService(repository, {KEY: "a" * 64})
    old = await old_service.complete(owner, KEY, "a" * 64)
    updated_service = FundamentalsService(repository, {KEY: "b" * 64})
    assert (await updated_service.progress(owner)).completed == [old]
    with pytest.raises(ApiError) as stale:
        await updated_service.complete(owner, KEY, "a" * 64)
    assert stale.value.code == "stale_version"
    current = await updated_service.complete(owner, KEY, "b" * 64)
    assert current.content_revision == "b" * 64 and current.completed_at >= old.completed_at
    assert (await updated_service.progress(owner)).completed == [current]
    assert len(repository.rows) == 1


async def test_database_completion_returns_the_atomic_upsert_without_a_separate_reread(monkeypatch):
    table = Table("fundamentals_completion", MetaData(), Column("user_id", Uuid, primary_key=True),
                  Column("question_key", String, primary_key=True), Column("content_revision", String),
                  Column("completed_at", DateTime(timezone=True)))
    owner = uuid.uuid4()
    at = datetime(2026, 10, 21, tzinfo=UTC)
    statements = []

    class Connection:
        async def execute(self, statement):
            statements.append(statement)
            assert len(statements) == 1, "Completion must not depend on a later row read"
            row = SimpleNamespace(_mapping={"question_key": KEY, "content_revision": "a" * 64,
                                            "completed_at": at})
            return SimpleNamespace(one=lambda: row)

    @asynccontextmanager
    async def begin():
        yield Connection()

    async def has_table(_):
        return True

    async def reflected_table(_):
        return table

    monkeypatch.setattr(db, "has_table", has_table)
    monkeypatch.setattr(db, "table", reflected_table)
    monkeypatch.setattr(db, "get_engine", lambda: SimpleNamespace(begin=begin))
    row = await DbFundamentalsRepository().complete(owner, KEY, "a" * 64)
    assert row.completed_at == at and row.content_revision == "a" * 64
    compiled = statements[0].compile(dialect=postgresql.dialect())
    sql = str(compiled)
    assert "ON CONFLICT (user_id, question_key) DO UPDATE" in sql
    assert "CASE WHEN" in sql and "THEN now() ELSE fundamentals_completion.completed_at END" in sql
    assert "RETURNING" in sql and " WHERE " not in sql
    assert compiled.params["user_id"] == owner and compiled.params["content_revision"] == "a" * 64


def generator():
    spec = importlib.util.spec_from_file_location("fundamentals_builder", BACKEND / "scripts/build_fundamentals_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_and_web_revision_manifests_match_actual_authored_cards():
    module = generator()
    expected = module.build()
    assert load_fundamentals_catalog(module.BACKEND_OUTPUT) == expected
    assert json.loads(module.WEB_OUTPUT.read_text(encoding="utf-8")) == expected
    for path, text in module.outputs().items():
        assert path.read_text(encoding="utf-8") == text, "Rebuild manifests after changing short-card content"


def test_card_revision_tracks_nested_content_but_ignores_object_order_and_revision_field():
    module = generator()
    first = {"id": KEY, "prompt": {"he": "א", "en": "A"}, "answer": {"en": "yes", "he": "כן"}}
    reordered = {"answer": {"he": "כן", "en": "yes"}, "prompt": {"en": "A", "he": "א"}, "id": KEY,
                 "revision": "old-ignored"}
    assert module.revision_for(first) == module.revision_for(reordered)
    reordered["answer"]["he"] = "לא"
    assert module.revision_for(first) != module.revision_for(reordered)
