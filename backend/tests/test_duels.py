"""Duels (Shaked, 2026-10-22): invite, accept, answer on the clock, settle; stakes and payouts through the coin ledger;
the guards (own invite, coins, cooldown, daily winnings, open invites); overdue duels settled on read — on the
in-memory store with scripted judges, and over HTTP with two members."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.engine.providers import LLMError, LLMRequest, ScriptedProvider
from app.main import app
from app.runtime import build_runtime
from app.services.coins import CoinsService, load_rules
from app.services.duels import INVITE_TTL, MAX_OPEN_INVITES, DuelService
from app.services.memory_store import InMemoryStore
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_practice_hardening import GOOD, SEEDS, WEAK

A, B, C = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
RULES = load_rules(SEEDS / "coins.json")
MIDDLE = {**GOOD, "correctness": 0.6, "depth": 0.5}


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 22, 9, 0, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, seconds: float):
        self.now += timedelta(seconds=seconds)


def judge(by_answer: dict | None = None, *, fail_times: int = 0):
    """The judge's reply depends on the answer's text (so the two players can get different bands)."""
    state = {"fails": fail_times}

    def respond(request: LLMRequest):
        if request.role != "evaluator":
            return "unused"
        if state["fails"] > 0:
            state["fails"] -= 1
            raise LLMError("judge down", retryable=False)
        for needle, reply in (by_answer or {}).items():
            if needle in request.user:
                return reply
        return GOOD
    return ScriptedProvider(respond)


def service(catalog, provider=None, *, enabled=True) -> tuple[DuelService, InMemoryStore, Clock]:
    store = InMemoryStore(catalog)
    store.duels_enabled = enabled
    coins = CoinsService(store, RULES)
    svc = DuelService(store, catalog, provider or judge(), coins, reviewed_only=False, site_url="https://site.test")
    svc.clock = Clock()
    return svc, store, svc.clock


def rows(store, user):
    return [(r["kind"], r["delta"]) for r in store.coin_ledger if r["user_id"] == user]


async def balance(svc, user):
    return (await svc.coins.wallet(user)).balance


async def start_duel(svc, *, language="en"):
    duel = await svc.create(A, language=language)
    return await svc.accept(B, duel.code)


class TestThePool:
    def test_short_means_a_format_answered_in_a_few_sentences(self, catalog):
        svc, _, _ = service(catalog)
        keys = {q.key for q in svc.pool("en")}
        assert keys and all(q.format in ("explain", "short_answer", "truth_table") for q in svc.pool("en"))
        assert "example-sensor-majority" in keys
        assert all(q.format not in ("code", "hdl", "waveform", "construct") for q in svc.pool("he"))


class TestAWholeDuel:
    async def test_invite_accept_answer_settle_and_the_coins_move_once(self, catalog):
        svc, store, clock = service(catalog, judge({"xor": WEAK}))
        invite = await svc.create(A, language="en")
        assert invite.status == "open" and len(invite.code) == 8 and invite.question_key is None
        assert svc.share_url(invite) == f"https://site.test/duel/{invite.code}"
        assert await balance(svc, A) == 45 and ("stake", -5) in rows(store, A)
        duel = await svc.accept(B, invite.code)
        assert duel.status == "active" and duel.opponent_id == B and duel.question_key in {q.key for q in svc.pool("en")}
        assert duel.deadline == clock.now + timedelta(seconds=180) and await balance(svc, B) == 45
        clock.advance(20)
        after_a = await svc.answer(A, duel.id, "the majority of the three sensors")
        assert after_a.status == "active" and after_a.player(A)["band"] == "STRONG"
        clock.advance(20)
        settled = await svc.answer(B, duel.id, "alarm = A xor B xor C")
        assert settled.status == "settled" and settled.outcome == "challenger" and settled.winner_id == A
        assert settled.player(B)["band"] == "WEAK"
        assert await balance(svc, A) == 55 and await balance(svc, B) == 45
        assert ("payout", 10) in rows(store, A) and not any(k == "payout" for k, _ in rows(store, B))
        # reading it again moves nothing
        again = await svc.get(A, duel.id)
        assert again.status == "settled" and await balance(svc, A) == 55
        # the ledger knows the duel
        payout = next(r for r in store.coin_ledger if r["kind"] == "payout")
        assert payout["duel_id"] == duel.id and payout["meta"]["net"] == 5

    async def test_same_band_goes_to_the_faster_and_a_dead_heat_refunds(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc)
        clock.advance(30)
        await svc.answer(B, duel.id, "a careful answer")                   # B answers first
        clock.advance(30)
        settled = await svc.answer(A, duel.id, "a careful answer")
        assert settled.outcome == "opponent" and settled.winner_id == B
        assert await balance(svc, B) == 55 and await balance(svc, A) == 45
        # the same second: a draw, both stakes come back
        clock.advance(15 * 60)                                            # past the cooldown
        duel2 = await start_duel(svc)
        await svc.answer(A, duel2.id, "answer")
        settled2 = await svc.answer(B, duel2.id, "answer")
        assert settled2.outcome == "draw" and settled2.winner_id is None
        assert await balance(svc, A) == 45 and await balance(svc, B) == 55
        assert rows(store, A).count(("refund", 5)) == 1 and rows(store, B).count(("refund", 5)) == 1

    async def test_the_question_is_one_neither_player_has_seen(self, catalog):
        svc, store, clock = service(catalog)
        keys = [q.key for q in svc.pool("en")]
        # A practised every pool question but one; B met another one in an earlier duel
        for key in keys[:-1]:
            store.attempts[uuid.uuid4()] = {"user_id": A, "question_id": None, "started_at": clock.now,
                                            "row": {"question_key": key, "submissions": [], "practice_language": "en"}}
        duel = await start_duel(svc)
        assert duel.question_key == keys[-1]
        clock.advance(15 * 60)
        duel2 = await start_duel(svc)                                     # nothing unseen by both: A's duel history wins
        assert duel2.question_key != keys[-1] and duel2.question_key in keys


class TestTheClock:
    async def test_a_no_show_forfeits_and_the_reader_settles_it(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc)
        clock.advance(60)
        await svc.answer(A, duel.id, "an answer in time")
        clock.advance(200)                                                # B never answers
        with pytest.raises(ApiError) as late:
            await svc.answer(B, duel.id, "too late")
        assert late.value.code == "conflict"
        seen = await svc.get(B, duel.id)
        assert seen.status == "settled" and seen.outcome == "forfeit_opponent" and seen.winner_id == A
        assert await balance(svc, A) == 55 and await balance(svc, B) == 45

    async def test_nobody_answers_both_are_refunded_on_the_list(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc)
        clock.advance(400)
        mine = await svc.list(A)
        assert mine[0].id == duel.id and mine[0].status == "settled" and mine[0].outcome == "no_show"
        assert await balance(svc, A) == 50 and await balance(svc, B) == 50

    async def test_an_invite_nobody_took_is_refunded_after_a_day(self, catalog):
        svc, store, clock = service(catalog)
        invite = await svc.create(A, language="he")
        clock.advance(INVITE_TTL.total_seconds() + 1)
        with pytest.raises(ApiError) as gone:
            await svc.accept(B, invite.code)
        assert gone.value.code == "conflict"
        seen = await svc.get(A, invite.id)
        assert seen.status == "cancelled" and seen.outcome == "expired" and await balance(svc, A) == 50

    async def test_the_challenger_can_cancel_an_open_invite(self, catalog):
        svc, store, clock = service(catalog)
        invite = await svc.create(A, language="he")
        assert await balance(svc, A) == 45
        cancelled = await svc.cancel(A, invite.id)
        assert cancelled.status == "cancelled" and cancelled.outcome == "cancelled" and await balance(svc, A) == 50
        with pytest.raises(ApiError):
            await svc.cancel(A, invite.id)


class TestTheGuards:
    async def test_own_invite_wrong_code_and_not_a_player(self, catalog):
        svc, store, clock = service(catalog)
        invite = await svc.create(A, language="en")
        with pytest.raises(ApiError) as own:
            await svc.accept(A, invite.code)
        assert own.value.code == "conflict"
        with pytest.raises(ApiError) as missing:
            await svc.accept(B, "nope1234")
        assert missing.value.code == "not_found"
        duel = await svc.accept(B, invite.code)
        with pytest.raises(ApiError) as stranger:
            await svc.get(C, duel.id)
        assert stranger.value.code == "not_found"
        with pytest.raises(ApiError) as twice:
            await svc.answer(A, duel.id, "one") and await svc.answer(A, duel.id, "two")
        assert twice.value.code == "already_submitted"

    async def test_no_coins_no_duel(self, catalog):
        svc, store, clock = service(catalog)
        async with store.transaction() as tx:
            await tx.coin_add(user_id=A, delta=-48, kind="spend", reference="spent", meta={})
        await svc.coins.wallet(A)                                          # gift 50 - 48 = 2
        with pytest.raises(ApiError) as poor:
            await svc.create(A, language="en")
        assert poor.value.status == 402 and poor.value.code == "usage_limit"

    async def test_the_pair_cooldown_and_the_open_invite_limit(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc)
        await svc.answer(A, duel.id, "x")
        await svc.answer(B, duel.id, "y")
        second = await svc.create(A, language="en")
        with pytest.raises(ApiError) as soon:
            await svc.accept(B, second.code)
        assert soon.value.code == "usage_limit" and "10 minutes" in soon.value.message
        assert (await svc.accept(C, second.code)).status == "active"      # someone else may accept
        for _ in range(MAX_OPEN_INVITES):
            await svc.create(A, language="en")
        with pytest.raises(ApiError) as many:
            await svc.create(A, language="en")
        assert many.value.code == "conflict"

    async def test_todays_winnings_have_a_ceiling(self, catalog):
        svc, store, clock = service(catalog)
        async with store.transaction() as tx:
            for n in range(20):                                            # twenty wins today: net 100
                await tx.coin_add(user_id=A, delta=10, kind="payout", reference=f"duel:{n}:payout", meta={"net": 5})
        with pytest.raises(ApiError) as capped:
            await svc.create(A, language="en")
        assert capped.value.code == "usage_limit" and "tomorrow" in capped.value.message
        assert (await svc.create(B, language="en")).status == "open"

    async def test_a_daily_duel_count_when_shaked_sets_one(self, catalog):
        svc, store, clock = service(catalog)
        svc.rules.duel_daily_cap = 1
        try:
            duel = await start_duel(svc)
            await svc.answer(A, duel.id, "x")
            await svc.answer(B, duel.id, "y")
            with pytest.raises(ApiError) as used:
                await svc.create(A, language="en")
            assert used.value.code == "usage_limit"
        finally:
            svc.rules.duel_daily_cap = None


class TestTheJudge:
    async def test_a_failed_judgement_lets_the_player_answer_again(self, catalog):
        svc, store, clock = service(catalog, judge(fail_times=1))
        duel = await start_duel(svc)
        with pytest.raises(ApiError) as down:
            await svc.answer(A, duel.id, "first try")
        assert down.value.code == "evaluation_unavailable"
        seen = await svc.get(A, duel.id)
        assert seen.player(A).get("status") == "failed" and not seen.player(A).get("submitted_at")
        again = await svc.answer(A, duel.id, "second try")
        assert again.player(A)["band"] == "STRONG"

    async def test_an_unrelated_answer_counts_as_weak(self, catalog):
        unrelated = {**WEAK, "correctness": 0.0, "key_points_hit": [], "answered_different_question": True}
        svc, store, clock = service(catalog, judge({"pasta": unrelated}))
        duel = await start_duel(svc)
        await svc.answer(A, duel.id, "my favourite pasta recipe")
        settled = await svc.answer(B, duel.id, "a real answer")
        assert settled.player(A)["band"] == "WEAK" and settled.player(A)["related"] is False
        assert settled.winner_id == B

    async def test_without_the_table_duels_answer_503(self, catalog):
        svc, store, clock = service(catalog, enabled=False)
        with pytest.raises(ApiError) as off:
            await svc.create(A, language="en")
        assert off.value.status == 503
        assert await svc.list(A) == []


MEMBERS = {"a@example.com", "b@example.com"}


@pytest.fixture
async def client(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True,
                        interview_reviewed_only=False, suggest_reviewed_only=False)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver(MEMBERS)
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=judge({"xor": WEAK}), store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestOverHttp:
    async def test_two_members_duel(self, client):
        ha = {"Authorization": f"Bearer {make_token(email='a@example.com')[1]}"}
        hb = {"Authorization": f"Bearer {make_token(email='b@example.com')[1]}"}
        empty = (await client.get("/v1/duels", headers=ha)).json()
        assert empty["duels"] == [] and empty["rules"]["stake"] == 5 and empty["rules"]["no_monetary_value"] is True
        created = await client.post("/v1/duels", json={"language": "en"}, headers=ha)
        assert created.status_code == 201, created.text
        invite = created.json()
        assert invite["status"] == "open" and invite["role"] == "challenger" and invite["question"] is None
        assert invite["share_path"] == f"/duel/{invite['code']}" and invite["opponent"] is None
        assert (await client.get("/v1/me/coins", headers=ha)).json()["balance"] == 45
        accepted = await client.post("/v1/duels/accept", json={"code": invite["code"]}, headers=hb)
        assert accepted.status_code == 200, accepted.text
        body = accepted.json()
        assert body["status"] == "active" and body["role"] == "opponent" and body["question"]["prompt"]
        assert body["seconds_left"] == 180 and body["pot"] == 10 and body["opponent"]["answered"] is False
        did = body["id"]
        # the challenger sees the same question; a stranger to the duel does not exist here
        mine = (await client.get(f"/v1/duels/{did}", headers=ha)).json()
        assert mine["question"]["key"] == body["question"]["key"] and mine["role"] == "challenger"
        a_done = await client.post(f"/v1/duels/{did}/answer", json={"text": "the majority of the sensors"}, headers=ha)
        assert a_done.status_code == 200, a_done.text
        assert a_done.json()["me"]["band"] == "STRONG" and a_done.json()["opponent"]["band"] is None
        b_view = (await client.get(f"/v1/duels/{did}", headers=hb)).json()
        assert b_view["opponent"]["answered"] is True and b_view["opponent"]["band"] is None     # hidden until settled
        b_done = await client.post(f"/v1/duels/{did}/answer", json={"text": "alarm = A xor B xor C"}, headers=hb)
        assert b_done.status_code == 200, b_done.text
        result = b_done.json()
        assert result["status"] == "settled" and result["outcome"] == "challenger" and result["won"] is False
        assert result["coins_delta"] == -5 and result["opponent"]["band"] == "STRONG" and result["question"] is None
        a_result = (await client.get(f"/v1/duels/{did}", headers=ha)).json()
        assert a_result["won"] is True and a_result["coins_delta"] == 5
        assert (await client.get("/v1/me/coins", headers=ha)).json()["balance"] == 55
        assert (await client.get("/v1/me/coins", headers=hb)).json()["balance"] == 45
        listed = (await client.get("/v1/duels", headers=hb)).json()["duels"]
        assert [d["id"] for d in listed] == [did]
        assert (await client.post(f"/v1/duels/{did}/answer", json={"text": "late"}, headers=ha)).status_code == 409
        assert (await client.post("/v1/duels/accept", json={"code": "zzzz9999"}, headers=hb)).status_code == 404
        assert (await client.post("/v1/duels/accept", json={"code": "x"}, headers=hb)).status_code == 422
