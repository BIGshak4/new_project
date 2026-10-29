"""Permanent cosmetics, server-owned entitlements and atomic coin spending."""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.runtime import build_runtime
from app.services.avatars import DEFAULT_AVATAR, AvatarsService
from app.services.avatars import load_catalog as load_avatars
from app.services.coins import CoinsService, load_rules
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import SEEDS


@pytest.fixture
def service():
    store = InMemoryStore(load_catalog(SEEDS))
    coins = CoinsService(store, load_rules(SEEDS / "coins.json"))
    return AvatarsService(store, coins, load_avatars(SEEDS / "avatar_cosmetics.json")), store


async def test_free_customization_preserves_balance_and_owned_skins(service):
    svc, store = service
    user = uuid.uuid4()
    initial = await svc.get(user)
    assert initial["avatar"] == DEFAULT_AVATAR and initial["balance"] == 50
    assert initial["shirt_text"] == "Job_Run" and initial["owned_skins"] == ["classic"]
    wanted = {"component": "xor", "color": "mint", "skin": "classic"}
    result = await svc.save(user, wanted)
    assert result["avatar"] == wanted and result["balance"] == 50
    assert (await svc.get(user))["avatar"] == wanted
    assert len(store.coin_ledger) == 1


async def test_buy_debits_once_and_skin_must_be_owned_before_equipping(service):
    svc, store = service
    user, other = uuid.uuid4(), uuid.uuid4()
    wanted = {**DEFAULT_AVATAR, "skin": "aurora"}
    with pytest.raises(ApiError) as denied:
        await svc.save(user, wanted)
    assert denied.value.code == "forbidden"
    one, two = await asyncio.gather(svc.buy(user, "aurora"), svc.buy(user, "aurora"))
    assert one["balance"] == two["balance"] == 30
    assert one["owned_skins"] == ["aurora", "classic"]
    assert (await svc.save(user, wanted))["avatar"] == wanted
    assert (await svc.get(other))["owned_skins"] == ["classic"]
    assert len([r for r in store.coin_ledger if r["kind"] == "spend"]) == 1
    assert await svc.public_configs([user, other]) == {str(user): wanted, str(other): DEFAULT_AVATAR}


async def test_competing_spends_cannot_overdraw_and_failures_do_not_grant_a_skin(service):
    svc, store = service
    user = uuid.uuid4()
    await svc.get(user)
    results = await asyncio.gather(svc.buy(user, "negative_feedback"), svc.buy(user, "binary_people"), return_exceptions=True)
    assert sum(isinstance(r, ApiError) and r.status == 402 for r in results) == 1
    view = await svc.get(user)
    assert view["balance"] == 10 and len(view["owned_skins"]) == 2
    assert len([r for r in store.coin_ledger if r["kind"] == "spend"]) == 1
    another = uuid.uuid4()
    await svc.get(another)
    store.failures.add("save_avatar")
    with pytest.raises(RuntimeError):
        await svc.buy(another, "aurora")
    store.failures.clear()
    assert (await svc.get(another))["balance"] == 50
    assert (await svc.get(another))["owned_skins"] == ["classic"]


async def test_unavailable_schema_is_readonly_and_every_catalog_value_is_validated(service):
    svc, store = service
    user = uuid.uuid4()
    for field in DEFAULT_AVATAR:
        with pytest.raises(ApiError) as invalid:
            await svc.save(user, {**DEFAULT_AVATAR, field: "https://unsafe.example/avatar"})
        assert invalid.value.code == "validation"
    with pytest.raises(ApiError):
        await svc.buy(user, "nonexistent")
    store.avatars_enabled = False
    view = await svc.get(user)
    assert view["enabled"] is False and view["shop_enabled"] is False and view["balance"] == 0
    assert not store.coin_ledger
    for operation in (svc.save(user, DEFAULT_AVATAR), svc.buy(user, "aurora")):
        with pytest.raises(ApiError) as missing:
            await operation
        assert missing.value.status == 503


async def test_http_identity_validation_and_opponent_cosmetics(monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True)
    catalog = load_catalog(SEEDS)
    runtime = build_runtime(settings, catalog=catalog, store=InMemoryStore(catalog))
    monkeypatch.setattr(app.state, "runtime", runtime, raising=False)
    monkeypatch.setattr(app.state, "verifier", make_verifier(), raising=False)
    monkeypatch.setattr(app.state, "access_resolver", member_resolver({"avatar-a@example.com", "avatar-b@example.com"}), raising=False)
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    _, token_a = make_token(email="avatar-a@example.com")
    _, token_b = make_token(email="avatar-b@example.com")
    a, b = {"Authorization": f"Bearer {token_a}"}, {"Authorization": f"Bearer {token_b}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        base = "/v1/me/avatar"
        assert (await client.get(base)).status_code == 401
        assert (await client.put(base, json=DEFAULT_AVATAR)).status_code == 401
        assert (await client.post(base + "/buy", json={"skin": "aurora"})).status_code == 401
        assert (await client.get(base, headers=a)).json()["balance"] == 50
        assert (await client.post(base + "/buy", headers=a, json={"skin": "aurora", "price": 0})).status_code == 422
        assert (await client.put(base, headers=a, json={**DEFAULT_AVATAR, "user_id": str(uuid.uuid4())})).status_code == 422
        assert (await client.put(base, headers=b, json={**DEFAULT_AVATAR, "skin": "gold"})).status_code == 403
        purchased = await client.post(base + "/buy", headers=a, json={"skin": "aurora"})
        assert purchased.status_code == 200 and purchased.json()["balance"] == 30
        wanted = {"component": "and", "color": "sky", "skin": "aurora"}
        assert (await client.put(base, headers=a, json=wanted)).json()["avatar"] == wanted
        assert (await client.get(base, headers=b)).json()["owned_skins"] == ["classic"]
        invite = (await client.post("/v1/duels", headers=a, json={"language": "he", "mode": "judged"})).json()
        assert invite["me"]["avatar"] == wanted
        joined = (await client.post("/v1/duels/accept", headers=b, json={"code": invite["code"]})).json()
        assert joined["opponent"]["avatar"] == wanted
        assert "owned_skins" not in joined["opponent"]


def test_migration_has_owner_read_but_no_browser_write_grants():
    migrations = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    sql = next(migrations.glob("*_game_avatars.sql")).read_text(encoding="utf-8").lower()
    assert "enable row level security" in sql
    assert "revoke all on public.game_avatar from public, anon, authenticated" in sql
    assert "user_id = (select auth.uid())" in sql
    assert "grant select on public.game_avatar to authenticated" in sql
    assert "for update to authenticated" not in sql and "for insert to authenticated" not in sql


async def test_onboarding_is_free_durable_and_preserves_owned_skin_on_skip(service):
    svc, store = service
    user = uuid.uuid4()
    assert (await svc.get(user))["onboarding_completed"] is False
    chosen = await svc.complete_onboarding(user, component="dff", color="sky")
    assert chosen["onboarding_completed"] is True
    assert chosen["avatar"] == {"component": "dff", "color": "sky", "skin": "classic"}
    assert chosen["balance"] == 50
    assert all(row["kind"] != "spend" for row in store.coin_ledger)
    await svc.buy(user, "gold")
    await svc.save(user, {"component": "xor", "color": "rose", "skin": "gold"})
    skipped = await svc.complete_onboarding(user)
    assert skipped["avatar"] == {"component": "xor", "color": "rose", "skin": "gold"}
    assert skipped["onboarding_completed"] is True and skipped["balance"] == 30
    assert (await svc.get(user))["onboarding_completed"] is True
    another = uuid.uuid4()
    assert (await svc.complete_onboarding(another))["avatar"] == DEFAULT_AVATAR
    with pytest.raises(ApiError):
        await svc.complete_onboarding(another, color="not-a-catalog-color")


async def test_generic_and_meme_prices_are_authoritative_and_legacy_ownership_survives(service):
    svc, store = service
    prices = {item["key"]: item["price"] for item in svc.catalog["skins"]}
    assert prices["classic"] == 0
    assert all(prices[key] == 20 for key in ("aurora", "circuit", "cosmic", "gold"))
    memes = {"negative_feedback", "works_on_my_machine", "binary_people", "gate_keeper", "sleep_not_found", "resistance_futile"}
    assert all(prices[key] == 40 for key in memes)
    user = uuid.uuid4()
    # An old purchase remains owned and is never repurchased/refunded just because prices changed.
    store.avatars[user] = {**DEFAULT_AVATAR, "skin": "cosmic", "owned_skins": ["classic", "cosmic"], "onboarding_completed": True}
    original = await svc.get(user)
    again = await svc.buy(user, "cosmic")
    assert again["balance"] == original["balance"] == 50
    assert again["avatar"]["skin"] == "cosmic" and again["onboarding_completed"] is True
    assert not any(row["kind"] == "spend" for row in store.coin_ledger)


async def test_onboarding_http_allows_only_free_fields_and_is_account_bound(monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True)
    catalog = load_catalog(SEEDS)
    runtime = build_runtime(settings, catalog=catalog, store=InMemoryStore(catalog))
    monkeypatch.setattr(app.state, "runtime", runtime, raising=False)
    monkeypatch.setattr(app.state, "verifier", make_verifier(), raising=False)
    monkeypatch.setattr(app.state, "access_resolver", member_resolver({"setup-a@example.com", "setup-b@example.com"}), raising=False)
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    a = {"Authorization": f"Bearer {make_token(email='setup-a@example.com')[1]}"}
    b = {"Authorization": f"Bearer {make_token(email='setup-b@example.com')[1]}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        base = "/v1/me/avatar"
        assert (await client.post(base + "/onboarding", json={})).status_code == 401
        assert (await client.post(base + "/onboarding", headers=a, json={"skin": "gold"})).status_code == 422
        assert (await client.post(base + "/onboarding", headers=a, json={"user_id": "other"})).status_code == 422
        assert (await client.post(base + "/onboarding", headers=a, json={"component": "unsafe"})).status_code == 422
        result = (await client.post(base + "/onboarding", headers=a, json={"component": "and", "color": "amber"})).json()
        assert result["onboarding_completed"] and result["balance"] == 50
        assert (await client.get(base, headers=b)).json()["onboarding_completed"] is False
        assert (await client.post(base + "/onboarding", headers=a, json={})).json()["avatar"] == result["avatar"]


def test_catalog_migration_preserves_security_and_existing_rows():
    migrations = Path(__file__).resolve().parents[2] / "supabase" / "migrations"
    sql = next(migrations.glob("*_avatar_shirt_catalog_and_onboarding.sql")).read_text(encoding="utf-8").lower()
    assert "drop constraint if exists game_avatar_check" in sql
    assert "negative_feedback" in sql and "resistance_futile" in sql
    assert "onboarding_completed boolean not null default true" in sql
    assert "onboarding_completed set default false" in sql
    assert "delete from" not in sql and "disable row level security" not in sql and "grant" not in sql
