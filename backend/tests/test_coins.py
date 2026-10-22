"""Coins (Shaked, 2026-10-22): the starting gift, coins for strong answers and strong interview turns, the shop's
first item (ten more questions today), the ledger's idempotency — on the in-memory store, and over HTTP."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.errors import ApiError
from app.config import Settings, get_settings
from app.engine.catalog import load_catalog
from app.main import app
from app.runtime import build_runtime
from app.services.coins import CoinsService, coins_for_answer, coins_for_turn, load_rules
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests.authtools import make_token, make_verifier, member_resolver
from tests.test_interview_service import interviewer
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

USER = uuid.uuid4()
RULES = load_rules(SEEDS / "coins.json")


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def ledger(store, user=USER):
    return [(r["kind"], r["delta"], r["reference"]) for r in store.coin_ledger if r["user_id"] == user]


class TestTheRules:
    def test_the_seed_carries_shakeds_numbers(self):
        assert (RULES.starting_gift, RULES.strong_answer, RULES.strong_hard_answer, RULES.hard_difficulty_from) == (50, 10, 20, 5)
        assert (RULES.strong_interview_turn, RULES.duel_stake, RULES.duel_clock_seconds) == (10, 5, 180)
        assert RULES.duel_daily_cap is None and RULES.duel_daily_earning_cap == 100       # "not sure about the daily cap yet"
        assert [i.key for i in RULES.shop] == ["extra_questions_10"]
        item = RULES.shop[0]
        assert item.price == 100 and item.effect == {"extra_questions_today": 10}
        assert item.text("label", "he").startswith("עוד") and item.text("label", "en") == "10 more questions today"

    def test_only_a_strong_main_answer_earns_and_a_hard_one_earns_double(self):
        assert coins_for_answer(RULES, band="STRONG", difficulty=2) == 10
        assert coins_for_answer(RULES, band="STRONG", difficulty=5) == 20
        assert coins_for_answer(RULES, band="STRONG", difficulty=4) == 10
        assert coins_for_answer(RULES, band="PARTIAL", difficulty=5) == 0
        assert coins_for_answer(RULES, band="STRONG", difficulty=2, turn=1) == 0            # follow-ups earn nothing
        assert coins_for_answer(RULES, band="STRONG", difficulty=2, reference_seen=True) == 0
        assert coins_for_answer(RULES, band="STRONG", difficulty=2, hints_seen=1) == 10      # one hint is allowed
        assert coins_for_answer(RULES, band="STRONG", difficulty=2, hints_seen=2) == 0
        assert coins_for_answer(RULES, band="STRONG", difficulty=2, related=False) == 0      # the unrelated rule, as for XP
        assert coins_for_answer(RULES, band=None, difficulty=2) == 0

    def test_a_strong_interview_turn_earns_ten(self):
        assert coins_for_turn(RULES, band="STRONG") == 10
        assert coins_for_turn(RULES, band="STRONG", hints_seen=2) == 0
        assert coins_for_turn(RULES, band="STRONG", related=False) == 0
        assert coins_for_turn(RULES, band="WEAK") == 0


class TestTheWallet:
    async def test_the_gift_is_written_once_and_a_second_instance_finds_it(self, catalog):
        store = InMemoryStore(catalog)
        svc = CoinsService(store, RULES)
        first = await svc.wallet(USER)
        assert first.enabled and first.balance == 50 and first.earned_today == 50
        assert [m.kind for m in first.movements] == ["gift"]
        assert (await svc.wallet(USER)).balance == 50
        other = CoinsService(store, RULES)                        # another server: the reference stops a second gift
        assert (await other.wallet(USER)).balance == 50 and ledger(store) == [("gift", 50, "gift")]

    async def test_buying_needs_the_price_and_tops_up_today(self, catalog):
        store = InMemoryStore(catalog)
        svc = CoinsService(store, RULES)
        with pytest.raises(ApiError) as short:
            await svc.buy(USER, "extra_questions_10")
        assert short.value.status == 402 and short.value.code == "usage_limit" and "100" in short.value.message
        assert await svc.extra_questions_today(USER) == 0
        async with store.transaction() as tx:                       # five strong answers later
            for n in range(5):
                await tx.coin_add(user_id=USER, delta=10, kind="earn", reference=f"answer:{n}:1")
        wallet = await svc.buy(USER, "extra_questions_10")
        assert wallet.balance == 0 and wallet.extra_questions_today == 10
        assert await svc.extra_questions_today(USER) == 10
        assert wallet.movements[0].kind == "spend" and wallet.movements[0].item == "extra_questions_10"
        with pytest.raises(ApiError) as unknown:
            await svc.buy(USER, "golden-hat")
        assert unknown.value.code == "validation"

    async def test_yesterdays_top_up_does_not_count_today(self, catalog):
        store = InMemoryStore(catalog)
        svc = CoinsService(store, RULES)
        async with store.transaction() as tx:
            await tx.coin_add(user_id=USER, delta=-100, kind="spend", reference="buy:old", item="extra_questions_10",
                              meta={"extra_questions_today": 10})
        store.coin_ledger[-1]["created_at"] = datetime.now(UTC) - timedelta(days=1, hours=1)
        assert await svc.extra_questions_today(USER) == 0

    async def test_without_the_table_everything_reads_zero_and_nothing_is_promised(self, catalog):
        store = InMemoryStore(catalog)
        store.coins_enabled = False
        svc = CoinsService(store, RULES)
        wallet = await svc.wallet(USER)
        assert wallet.enabled is False and wallet.balance == 0 and wallet.movements == []
        assert svc.known_enabled is False
        with pytest.raises(ApiError) as refused:
            await svc.buy(USER, "extra_questions_10")
        assert refused.value.status == 503
        async with store.transaction() as tx:
            assert await svc.award_for_answer(tx, user_id=USER, attempt_id=uuid.uuid4(), revision=1, band="STRONG",
                                              difficulty=2, hints_seen=0, reference_seen=False, related=True, turn=0) == 0
        assert store.coin_ledger == []


def practice(catalog, evaluations, *, coins=True):
    store = InMemoryStore(catalog)
    config = ServiceConfig(suggest_reviewed_only=False, daily_attempt_limit=3, feedback_in_background=False)
    svc = PracticeService(store, catalog, scripted(evaluations), config)
    svc.coins = CoinsService(store, RULES) if coins else None
    return svc, store


class TestPracticeEarns:
    async def test_a_strong_main_answer_pays_once_and_the_view_says_so(self, catalog):
        svc, store = practice(catalog, [GOOD, GOOD, GOOD])
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en", self_confidence=3)
        aid = uuid.UUID(view.id)
        sub, _ = await svc.submit(USER, aid, {"text": "a majority: (A&B)|(B&C)|(A&C)"}, idempotency_key="k1")
        assert sub.band == "STRONG" and sub.coins_earned == 10 and sub.xp_earned and sub.xp_earned > 0
        rows = ledger(store)
        assert ("gift", 50, "gift") in rows and ("earn", 10, f"answer:{aid}:{sub.revision}") in rows
        replay, _ = await svc.submit(USER, aid, {"text": "a majority: (A&B)|(B&C)|(A&C)"}, idempotency_key="k1")
        assert replay.replayed and replay.coins_earned == 10 and ledger(store) == rows      # paid once
        assert (await svc.coins.wallet(USER)).balance == 60
        again = await svc.get(USER, aid)
        assert again.submission.coins_earned == 10

    async def test_a_weak_answer_and_a_follow_up_earn_nothing(self, catalog):
        svc, store = practice(catalog, [WEAK, GOOD, GOOD])
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en", self_confidence=3)
        aid = uuid.UUID(view.id)
        sub, view = await svc.submit(USER, aid, {"text": "alarm = A ^ B ^ C"}, idempotency_key="k1")
        assert sub.band == "WEAK" and sub.coins_earned == 0
        assert [k for k, _, _ in ledger(store) if k == "earn"] == []
        if view.pending_follow_up is not None:
            follow, _ = await svc.submit(USER, aid, {"text": "a careful second answer"}, idempotency_key="k2",
                                         follow_up_turn=view.pending_follow_up.turn)
            assert follow.coins_earned == 0
            assert [k for k, _, _ in ledger(store) if k == "earn"] == []

    async def test_without_coins_the_view_promises_nothing(self, catalog):
        svc, store = practice(catalog, [GOOD], coins=False)
        view = await svc.start(USER, question_key="example-sensor-majority", mode="deep", language="en", self_confidence=3)
        sub, _ = await svc.submit(USER, uuid.UUID(view.id), {"text": "a majority"}, idempotency_key="k1")
        assert sub.band == "STRONG" and sub.coins_earned is None and store.coin_ledger == []

    async def test_the_shop_raises_todays_limit(self, catalog):
        svc, store = practice(catalog, [GOOD] * 6)
        coins = svc.coins

        async def limit(user_id):
            return 3 + await coins.extra_questions_today(user_id)
        svc.daily_limit_for = limit
        assert await svc._daily_limit(USER) == 3
        async with store.transaction() as tx:
            await tx.coin_add(user_id=USER, delta=100, kind="earn", reference="seed")
        await coins.buy(USER, "extra_questions_10")
        assert await svc._daily_limit(USER) == 13


class TestInterviewEarns:
    async def test_a_strong_turn_pays_ten_once(self, catalog):
        store = InMemoryStore(catalog)
        coins = CoinsService(store, RULES)
        svc = InterviewService(store, catalog, interviewer([GOOD, WEAK]), InterviewConfig(reviewed_only=False), coins=coins)
        view = await svc.start(USER, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        turn, view = await svc.answer(USER, sid, 0, "a careful, correct answer", idempotency_key="t0")
        assert turn.status == "done" and turn.coins_earned is None                 # hidden until the end, like the band
        rows = ledger(store)
        assert ("earn", 10, f"turn:{sid}:0") in rows
        turn, view = await svc.answer(USER, sid, 1, "alarm = A ^ B ^ C", idempotency_key="t1")
        assert [r for r in ledger(store) if r[0] == "earn"] == [("earn", 10, f"turn:{sid}:0")]   # the weak turn: nothing
        ended = await svc.end(USER, sid)
        assert [t.coins_earned for t in ended.turns[:2]] == [10, 0]
        assert [r for r in ledger(store) if r[0] == "earn"] == [("earn", 10, f"turn:{sid}:0")]   # the end's re-save: once


MEMBER = "member@example.com"


@pytest.fixture
async def client(catalog, monkeypatch):
    settings = Settings(_env_file=None, llm_provider="scripted", allow_in_review_content=True,
                        interview_reviewed_only=False, suggest_reviewed_only=False)
    app.state.verifier = make_verifier()
    app.state.access_resolver = member_resolver({MEMBER})
    app.state.runtime = build_runtime(settings, catalog=catalog, provider=scripted([GOOD, GOOD, GOOD]),
                                      store=InMemoryStore(catalog))
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestOverHttp:
    async def test_wallet_shop_and_an_answer_that_earns(self, client):
        _, token = make_token(email=MEMBER)
        headers = {"Authorization": f"Bearer {token}"}
        body = (await client.get("/v1/me/coins?language=he", headers=headers)).json()
        assert body["balance"] == 50 and body["enabled"] is True and body["no_monetary_value"] is True
        assert body["movements"][0]["kind"] == "gift" and body["movements"][0]["delta"] == 50
        assert body["shop"][0]["key"] == "extra_questions_10" and body["shop"][0]["affordable"] is False
        assert body["shop"][0]["label"].startswith("עוד") and body["rules"]["strong_answer"] == 10
        assert body["daily_limit"] == get_settings().daily_attempt_limit and body["extra_questions_today"] == 0
        short = await client.post("/v1/me/coins/buy", json={"item": "extra_questions_10"}, headers=headers)
        assert short.status_code == 402 and short.json()["error"]["code"] == "usage_limit"
        assert (await client.post("/v1/me/coins/buy", json={"item": "nope"}, headers=headers)).status_code == 422
        started = await client.post("/v1/practice/attempts", json={"question_key": "example-sensor-majority"}, headers=headers)
        assert started.status_code == 201, started.text
        aid = started.json()["id"]
        answered = await client.post(f"/v1/practice/attempts/{aid}/submissions", json={"answer": {"text": "a majority of the three"}},
                                     headers={**headers, "Idempotency-Key": "k1"})
        assert answered.status_code == 200, answered.text
        assert answered.json()["submission"]["coins_earned"] == 10
        assert (await client.get("/v1/me/coins", headers=headers)).json()["balance"] == 60

    async def test_a_bought_top_up_shows_in_the_limit(self, client):
        _, token = make_token(email=MEMBER)
        headers = {"Authorization": f"Bearer {token}"}
        store = app.state.runtime.store
        user = (await client.get("/v1/me/coins", headers=headers)).json()   # writes the gift; now find the user's id
        assert user["balance"] == 50
        uid = store.coin_ledger[-1]["user_id"]
        async with store.transaction() as tx:
            await tx.coin_add(user_id=uid, delta=50, kind="earn", reference="seed")
        bought = await client.post("/v1/me/coins/buy?language=en", json={"item": "extra_questions_10"}, headers=headers)
        assert bought.status_code == 200, bought.text
        body = bought.json()
        assert body["balance"] == 0 and body["extra_questions_today"] == 10
        assert body["daily_limit"] == get_settings().daily_attempt_limit + 10
