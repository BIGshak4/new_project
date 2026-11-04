"""Permanent usernames/codes and explicit friendships: memory service and real authenticated HTTP routes."""

import asyncio
import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import ApiError
from app.api.v1.identity import SocialBudget, budget
from app.config import Settings
from app.engine.catalog import load_catalog
from app.main import app
from app.runtime import build_runtime
from app.services import memory_store
from app.services.usernames import display_username, username_key, username_reason
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, SEEDS, scripted


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


@pytest.fixture
def runtime(catalog):
    return build_runtime(Settings(_env_file=None, database_url="", llm_provider="scripted"),
                         catalog=catalog, provider=scripted([GOOD]))


@pytest.mark.parametrize("name", ["fuck", "f_u_c_k", "f4gg0t", "n1gg3r", "naz1", "kkk", "k_k_k", "kkkk",
                                 "fuuuck", "fuck123", "123fuck", "Ｆｕｃｋ", "בן_זונה", "שרמוטה", "מזדיין",
                                 "fuckHarel", "motherfucker42x", "בןזונהHarel", "f4gg0tFan", "super_שרמוטה"])
def test_common_abusive_words_leetspeak_separators_and_name_concatenations_are_rejected(name):
    assert username_reason(name) == "offensive"


@pytest.mark.parametrize("name", ["Scunthorpe", "assistant", "classroom", "analyst", "Dickinson", "Cockburn",
                                 "passion", "Harel_123", "שקד_בוזי", "as1", "FPGA_student", "ＦＰＧＡ"])
def test_ordinary_names_and_words_do_not_fail_on_ambiguous_short_substrings(name):
    assert username_reason(name) is None


@pytest.mark.parametrize("name", ["ab", "123456", "___", "first last", "user-name", "x<script>", "admin", "מוקסי",
                                 "x" * 25, "ab\u200fc", "מִשְׁתַּמֵּשׁ", "🙂user"])
def test_shape_and_reserved_names_are_invalid(name):
    assert username_reason(name) == "invalid"


def test_unicode_compatibility_and_case_define_one_canonical_name():
    assert display_username("  Ａlice  ") == "Alice"
    assert username_key("Ａlice") == username_key("ALICE") == "alice"


async def test_codes_are_random_format_unique_stable_and_retry_collisions(runtime, monkeypatch):
    identities = runtime.identities
    first, second = uuid.uuid4(), uuid.uuid4()
    candidates = iter(["abcdef01", "abcdef01", "01234567"])
    monkeypatch.setattr(memory_store.secrets, "token_hex", lambda count: next(candidates))
    a = await identities.get(first)
    b = await identities.get(second)
    assert a == {"username": None, "friend_code": "ABCDEF01", "can_claim_username": True}
    assert b["friend_code"] == "01234567" and a == await identities.get(first)
    assert all(re.fullmatch(r"[0-9A-F]{8}", row["friend_code"]) for row in (a, b))


async def test_claim_is_once_unique_case_insensitive_and_same_request_retry_is_safe(runtime):
    a, b = uuid.uuid4(), uuid.uuid4()
    result = await runtime.identities.claim(a, "  Ａlice  ")
    assert result["username"] == "Alice" and not result["can_claim_username"]
    assert result == await runtime.identities.claim(a, "Alice")
    with pytest.raises(ApiError) as immutable:
        await runtime.identities.claim(a, "ALICE")
    assert immutable.value.code == "username_immutable"
    with pytest.raises(ApiError) as taken:
        await runtime.identities.claim(b, "alice")
    assert taken.value.code == "username_taken"
    assert await runtime.identities.availability("ＡLICE") == {"available": False, "reason": "taken"}
    assert await runtime.identities.availability("f_u_c_k") == {"available": False, "reason": "offensive"}


async def named(runtime, username):
    user = uuid.uuid4()
    identity = await runtime.identities.claim(user, username)
    return user, identity["friend_code"]


async def test_friend_request_direction_confirmation_cleanup_and_actual_avatars(runtime):
    service = runtime.identities
    alice, alice_code = await named(runtime, "Alice")
    bob, bob_code = await named(runtime, "Bob")
    outsider, _ = await named(runtime, "Outsider")
    runtime.store.avatars[bob] = {"component": "and", "color": "coral", "skin": "classic", "owned_skins": ["classic"],
                                  "secret_balance": 9000, "email": "private@example.test"}
    outgoing = await service.request(alice, bob_code.lower())
    request_id = uuid.UUID(outgoing["outgoing"][0]["id"])
    assert outgoing["friends"] == [] and outgoing["incoming"] == []
    assert outgoing["outgoing"][0]["person"]["avatar"] == {"component": "and", "color": "coral", "skin": "classic"}
    assert "email" not in str(outgoing) and "owned_skins" not in str(outgoing) and "secret_balance" not in str(outgoing)
    assert await service.request(alice, bob_code) == outgoing
    with pytest.raises(ApiError) as received:
        await service.request(bob, alice_code)
    assert received.value.code == "friend_request_received"
    for user in (alice, outsider):
        with pytest.raises(ApiError):
            await service.accept(user, request_id)
    with pytest.raises(ApiError):
        await service.dismiss(alice, request_id, incoming=True)
    with pytest.raises(ApiError):
        await service.dismiss(bob, request_id, incoming=False)
    accepted = await service.accept(bob, request_id)
    assert len(accepted["friends"]) == 1 and accepted["friends"][0]["username"] == "Alice"
    assert accepted == await service.accept(bob, request_id)
    assert (await service.friends(outsider)) == {"friends": [], "incoming": [], "outgoing": []}
    runtime.store.avatars[bob] = {"component": "xor", "color": "mint", "skin": "classic", "owned_skins": ["classic"]}
    assert (await service.friends(alice))["friends"][0]["avatar"]["component"] == "xor"
    await service.remove(outsider, bob)
    assert len((await service.friends(alice))["friends"]) == 1
    assert await service.remove(alice, bob) == {"friends": [], "incoming": [], "outgoing": []}
    assert (await service.friends(bob))["friends"] == []
    again = await service.request(alice, bob_code)
    await service.dismiss(bob, uuid.UUID(again["outgoing"][0]["id"]), incoming=True)
    assert (await service.friends(alice))["outgoing"] == []
    again = await service.request(alice, bob_code)
    await service.dismiss(alice, uuid.UUID(again["outgoing"][0]["id"]), incoming=False)
    assert (await service.friends(bob))["incoming"] == []


async def test_request_needs_own_name_and_a_real_nonself_code(runtime):
    service = runtime.identities
    user = uuid.uuid4()
    other, code = await named(runtime, "Other")
    with pytest.raises(ApiError) as required:
        await service.request(user, code)
    assert required.value.code == "username_required"
    own = await service.claim(user, "Named")
    for code, expected in (("not-a-code", "friend_invalid_code"), (own["friend_code"], "friend_self"),
                            ("FFFFFFFF", "friend_not_found")):
        with pytest.raises(ApiError) as error:
            await service.request(user, code)
        assert error.value.code == expected
    legacy = uuid.uuid4()
    legacy_identity = await service.get(legacy)
    request = await service.request(other, legacy_identity["friend_code"])
    with pytest.raises(ApiError) as required:
        await service.accept(legacy, uuid.UUID(request["outgoing"][0]["id"]))
    assert required.value.code == "username_required"


async def test_concurrent_duplicate_requests_and_name_claims_do_not_duplicate_state(runtime):
    service = runtime.identities
    a, _ = await named(runtime, "Alice")
    _, code = await named(runtime, "Bob")
    await asyncio.gather(*(service.request(a, code) for _ in range(8)))
    assert len(runtime.store.friendships) == 1
    outcomes = await asyncio.gather(service.claim(uuid.uuid4(), "SameName"),
                                     service.claim(uuid.uuid4(), "samename"), return_exceptions=True)
    assert sum(isinstance(outcome, ApiError) and outcome.code == "username_taken" for outcome in outcomes) == 1


async def test_identity_unavailability_fails_without_fabricating_saved_state(runtime):
    runtime.store.identities_enabled = False
    with pytest.raises(ApiError) as error:
        await runtime.identities.get(uuid.uuid4())
    assert error.value.status == 503 and runtime.store.identities == {}


def test_public_and_mutation_rate_budgets_are_bounded_and_independent(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("app.api.v1.identity.time.monotonic", lambda: now[0])
    limiter = SocialBudget()
    limiter.check("username", "ip:one", 2)
    limiter.check("username", "ip:one", 2)
    with pytest.raises(ApiError) as error:
        limiter.check("username", "ip:one", 2)
    assert error.value.status == 429 and error.value.headers["Retry-After"] == "60"
    limiter.check("friends", "ip:one", 2)
    now[0] += 61
    limiter.check("username", "ip:one", 2)


@pytest.fixture
async def client(runtime, monkeypatch):
    budget.buckets.clear()
    monkeypatch.setattr(app.state, "runtime", runtime, raising=False)
    monkeypatch.setattr(app.state, "verifier", make_verifier(), raising=False)
    monkeypatch.setattr(app.state, "access_resolver", member_resolver({"friend@example.test"}), raising=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


async def test_http_routes_public_check_owner_identity_and_explicit_friend_acceptance(client):
    a, token_a = make_token(email="friend@example.test")
    b, token_b = make_token(email="friend@example.test")
    headers_a, headers_b = {"Authorization": f"Bearer {token_a}"}, {"Authorization": f"Bearer {token_b}"}
    public = await client.get("/v1/usernames/availability?username=GoodName")
    assert public.status_code == 200 and public.json() == {"available": True, "reason": None}
    assert public.headers["Cache-Control"] == "no-store"
    assert (await client.get("/v1/me/identity")).status_code == 401
    assert (await client.put("/v1/me/identity/username", headers=headers_a, json={"username": "Alice"})).status_code == 200
    bob = await client.put("/v1/me/identity/username", headers=headers_b, json={"username": "Bob"})
    assert bob.status_code == 200 and not bob.json()["can_claim_username"]
    forged = await client.put("/v1/me/identity/username", headers=headers_a, json={"username": "Hacker", "user_id": str(b)})
    assert forged.status_code == 422
    sent = await client.post("/v1/me/friends/requests", headers=headers_a, json={"friend_code": bob.json()["friend_code"]})
    assert sent.status_code == 200
    request_id = sent.json()["outgoing"][0]["id"]
    assert (await client.post(f"/v1/me/friends/requests/{request_id}/accept", headers=headers_a)).status_code == 404
    accepted = await client.post(f"/v1/me/friends/requests/{request_id}/accept", headers=headers_b)
    assert accepted.status_code == 200 and accepted.json()["friends"][0]["user_id"] == str(a)
    result = await client.get("/v1/me/friends", headers=headers_a)
    assert result.json()["friends"][0]["username"] == "Bob" and result.json()["friends"][0]["avatar"] is None
    assert (await client.delete(f"/v1/me/friends/{b}", headers=headers_a)).json()["friends"] == []
