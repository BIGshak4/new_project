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
from app.services.duels import INVITE_TTL, MAX_OPEN_INVITES, DuelService, load_quiz
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
        # today at 09:00: 'accepted today' and 'won today' are counted against the real calendar day
        self.now = datetime.now(UTC).replace(hour=9, minute=0, second=0, microsecond=0)

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


QUIZ = load_quiz(SEEDS / "duel_quiz.json")


def service(catalog, provider=None, *, enabled=True) -> tuple[DuelService, InMemoryStore, Clock]:
    store = InMemoryStore(catalog)
    store.duels_enabled = enabled
    coins = CoinsService(store, RULES)
    svc = DuelService(store, catalog, provider or judge(), coins, reviewed_only=False, site_url="https://site.test",
                      quiz=QUIZ, approved_only=False)                 # drafts count in tests; production wants approved
    svc.clock = Clock()
    return svc, store, svc.clock


def rows(store, user):
    return [(r["kind"], r["delta"]) for r in store.coin_ledger if r["user_id"] == user]


async def balance(svc, user):
    return (await svc.coins.wallet(user)).balance


async def start_duel(svc, *, language="en", mode="judged"):
    duel = await svc.create(A, language=language, mode=mode)
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
        invite = await svc.create(A, language="en", mode="judged")
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
        invite = await svc.create(A, language="he", mode="judged")
        clock.advance(INVITE_TTL.total_seconds() + 1)
        with pytest.raises(ApiError) as gone:
            await svc.accept(B, invite.code)
        assert gone.value.code == "conflict"
        seen = await svc.get(A, invite.id)
        assert seen.status == "cancelled" and seen.outcome == "expired" and await balance(svc, A) == 50

    async def test_the_challenger_can_cancel_an_open_invite(self, catalog):
        svc, store, clock = service(catalog)
        invite = await svc.create(A, language="he", mode="judged")
        assert await balance(svc, A) == 45
        cancelled = await svc.cancel(A, invite.id)
        assert cancelled.status == "cancelled" and cancelled.outcome == "cancelled" and await balance(svc, A) == 50
        with pytest.raises(ApiError):
            await svc.cancel(A, invite.id)


class TestTheGuards:
    async def test_own_invite_wrong_code_and_not_a_player(self, catalog):
        svc, store, clock = service(catalog)
        invite = await svc.create(A, language="en", mode="judged")
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
            await svc.create(A, language="en", mode="judged")
        assert poor.value.status == 402 and poor.value.code == "usage_limit"

    async def test_the_pair_cooldown_and_the_open_invite_limit(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc)
        await svc.answer(A, duel.id, "x")
        await svc.answer(B, duel.id, "y")
        second = await svc.create(A, language="en", mode="judged")
        with pytest.raises(ApiError) as soon:
            await svc.accept(B, second.code)
        assert soon.value.code == "usage_limit" and "10 minutes" in soon.value.message
        assert (await svc.accept(C, second.code)).status == "active"      # someone else may accept
        for _ in range(MAX_OPEN_INVITES):
            await svc.create(A, language="en", mode="judged")
        with pytest.raises(ApiError) as many:
            await svc.create(A, language="en", mode="judged")
        assert many.value.code == "conflict"

    async def test_todays_winnings_have_a_ceiling(self, catalog):
        svc, store, clock = service(catalog)
        async with store.transaction() as tx:
            for n in range(20):                                            # twenty wins today: net 100
                await tx.coin_add(user_id=A, delta=10, kind="payout", reference=f"duel:{n}:payout", meta={"net": 5})
        with pytest.raises(ApiError) as capped:
            await svc.create(A, language="en", mode="judged")
        assert capped.value.code == "usage_limit" and "tomorrow" in capped.value.message
        assert (await svc.create(B, language="en", mode="judged")).status == "open"

    async def test_a_daily_duel_count_when_shaked_sets_one(self, catalog, monkeypatch):
        svc, store, clock = service(catalog)

        class StoreDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return clock.now.astimezone(tz) if tz is not None else clock.now.replace(tzinfo=None)

        # The service's accepted_at and the store's UTC day must use the same clock.
        monkeypatch.setattr("app.services.memory_store.datetime", StoreDateTime)
        svc.rules.duel_daily_cap = 1
        try:
            duel = await start_duel(svc)
            await svc.answer(A, duel.id, "x")
            await svc.answer(B, duel.id, "y")
            with pytest.raises(ApiError) as used:
                await svc.create(A, language="en", mode="judged")
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
            await svc.create(A, language="en", mode="judged")
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
    app.state.runtime.duels.approved_only = False
    monkeypatch.setattr(get_settings(), "require_pilot_membership", True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestOverHttp:
    async def test_two_members_duel(self, client):
        ha = {"Authorization": f"Bearer {make_token(email='a@example.com')[1]}"}
        hb = {"Authorization": f"Bearer {make_token(email='b@example.com')[1]}"}
        empty = (await client.get("/v1/duels", headers=ha)).json()
        assert empty["duels"] == [] and empty["rules"]["stake"] == 5 and empty["rules"]["no_monetary_value"] is True
        created = await client.post("/v1/duels", json={"language": "en", "mode": "judged"}, headers=ha)
        assert created.status_code == 201, created.text
        invite = created.json()
        assert invite["status"] == "open" and invite["role"] == "challenger" and invite["question"] is None and invite["mode"] == "judged"
        assert invite["share_path"] == f"/duel/{invite['code']}" and invite["opponent"] is None
        assert (await client.get("/v1/me/coins", headers=ha)).json()["balance"] == 45
        accepted = await client.post("/v1/duels/accept", json={"code": invite["code"]}, headers=hb)
        assert accepted.status_code == 200, accepted.text
        body = accepted.json()
        assert body["status"] == "active" and body["role"] == "opponent" and body["question"]["prompt"]
        assert 178 <= body["seconds_left"] <= 180 and body["pot"] == 10 and body["opponent"]["answered"] is False   # real clock
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


def answers_for(svc, duel, *, right: int):
    """The first `right` questions answered correctly, the rest wrong."""
    out = []
    for i, item in enumerate(duel.items):
        q = svc.quiz[item["key"]]
        out.append(q.correct if i < right else (q.correct + 1) % 4)
    return out


async def play(svc, user, duel, choices, clock, *, seconds_each=5):
    result = await svc.get(user, duel.id)
    start = len(result.players.get(str(user), {}).get("answers", []))
    for n, choice in enumerate(choices):
        clock.advance(seconds_each)
        result = await svc.answer(user, duel.id, choice=choice, item=start + n)
    return result


class TestTheQuizContent:
    def test_forty_questions_four_options_one_correct_both_languages(self):
        assert len(QUIZ) >= 40
        assert all(len(q.choices) == 4 and 0 <= q.correct < 4 for q in QUIZ)
        assert all(q.prompt["he"] and q.prompt["en"] and q.explanation["he"] and q.explanation["en"] for q in QUIZ)
        assert len({q.key for q in QUIZ}) == len(QUIZ)
        assert all(q.status == "draft" for q in QUIZ)                 # nothing enters production until approved

    def test_production_pool_is_only_the_approved_ones(self, catalog):
        svc, _, _ = service(catalog)
        svc.approved_only = True
        assert svc.quiz_pool() == []
        svc.approved_only = False
        assert len(svc.quiz_pool()) == len(QUIZ)


class TestAQuizDuel:
    async def test_more_correct_answers_win_and_nothing_leaks_before_the_end(self, catalog):
        svc, store, clock = service(catalog)
        invite = await svc.create(A, language="he")                   # the default mode is quiz
        assert invite.mode == "quiz" and invite.clock_seconds == 5 * 60
        duel = await svc.accept(B, invite.code)
        assert duel.status == "active" and len(duel.items) == 5 and len({i["key"] for i in duel.items}) == 5
        assert duel.deadline == clock.now + timedelta(seconds=300)
        a_choices, b_choices = answers_for(svc, duel, right=4), answers_for(svc, duel, right=2)
        after = await svc.answer(A, duel.id, choice=a_choices[0], item=0)
        assert after.status == "active" and after.player(A)["answers"][0]["correct"] is True
        with pytest.raises(ApiError) as stale:                         # a stale screen sends the old index
            await svc.answer(A, duel.id, choice=0, item=0)
        assert stale.value.code == "conflict"
        await play(svc, A, duel, a_choices[1:], clock)
        mid = await svc.get(B, duel.id)
        assert mid.status == "active" and mid.player(A)["status"] == "done"
        settled = await play(svc, B, duel, b_choices, clock)
        assert settled.status == "settled" and settled.outcome == "challenger" and settled.winner_id == A
        assert settled.player(A)["score"] == 4 and settled.player(B)["score"] == 2
        assert await balance(svc, A) == 55 and await balance(svc, B) == 45
        assert not any(k == "payout" for k, _ in rows(store, B))

    async def test_same_score_goes_to_the_faster_and_the_same_second_is_a_draw(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc, mode="quiz")
        choices = answers_for(svc, duel, right=3)
        # both clocks start at acceptance: B answers while A is still thinking about question 1
        await play(svc, B, duel, choices, clock, seconds_each=4)        # B: 20 s in total
        settled = await play(svc, A, duel, choices, clock, seconds_each=10)   # A: 20 + 10 on question 1, then 40 more
        assert settled.player(B)["seconds"] == 20 and settled.player(A)["seconds"] == 70
        assert settled.outcome == "opponent" and settled.winner_id == B
        clock.advance(15 * 60)
        duel2 = await start_duel(svc, mode="quiz")
        choices2 = answers_for(svc, duel2, right=5)
        for i, choice in enumerate(choices2):                            # answering together, to the second
            clock.advance(6)
            await svc.answer(A, duel2.id, choice=choice, item=i)
            settled2 = await svc.answer(B, duel2.id, choice=choice, item=i)
        assert settled2.outcome == "draw" and await balance(svc, A) == 45 and await balance(svc, B) == 55

    async def test_a_minute_is_the_ceiling_the_question_runs_out_and_counts_wrong(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc, mode="quiz")
        clock.advance(61)                                               # A sat on question 1 for over a minute
        seen = await svc.get(A, duel.id)
        a = seen.player(A)
        assert a["answers"][0]["timed_out"] is True and a["answers"][0]["seconds"] == 60 and len(a["answers"]) == 1
        clock.advance(5)
        after = await svc.answer(A, duel.id, choice=svc.quiz[duel.items[1]["key"]].correct, item=1)
        assert after.player(A)["answers"][1]["correct"] is True
        assert 5 <= after.player(A)["answers"][1]["seconds"] <= 7        # timed from the minute mark, not from the start

    async def test_never_pressing_anything_is_a_no_show(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc, mode="quiz")
        await play(svc, A, duel, answers_for(svc, duel, right=1), clock)
        clock.advance(6 * 60)                                           # B never touched it
        seen = await svc.get(A, duel.id)
        assert seen.status == "settled" and seen.outcome == "forfeit_opponent" and seen.winner_id == A
        clock.advance(15 * 60)
        duel2 = await start_duel(svc, mode="quiz")
        clock.advance(6 * 60)
        listed = await svc.list(B)
        assert listed[0].id == duel2.id and listed[0].outcome == "no_show"
        assert await balance(svc, A) == 55 and await balance(svc, B) == 45

    async def test_questions_both_players_met_are_avoided(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc, mode="quiz")
        await play(svc, A, duel, answers_for(svc, duel, right=5), clock)
        await play(svc, B, duel, answers_for(svc, duel, right=0), clock)
        clock.advance(15 * 60)
        duel2 = await start_duel(svc, mode="quiz")
        assert not {i["key"] for i in duel.items} & {i["key"] for i in duel2.items}

    async def test_a_quiz_needs_five_approved_questions(self, catalog):
        svc, store, clock = service(catalog)
        svc.approved_only = True
        with pytest.raises(ApiError) as none:
            await svc.create(A, language="he")
        assert none.value.code == "no_reviewed_questions"
        assert await balance(svc, A) == 50                             # nothing was staked

    async def test_bad_answers_are_refused(self, catalog):
        svc, store, clock = service(catalog)
        duel = await start_duel(svc, mode="quiz")
        with pytest.raises(ApiError) as no_choice:
            await svc.answer(A, duel.id, text="the majority")
        assert no_choice.value.code == "validation"
        await play(svc, A, duel, answers_for(svc, duel, right=5), clock)
        with pytest.raises(ApiError) as extra:
            await svc.answer(A, duel.id, choice=0)
        assert extra.value.code == "already_submitted"


class TestQuizOverHttp:
    async def test_two_members_play_a_quiz(self, client):
        ha = {"Authorization": f"Bearer {make_token(email='a@example.com')[1]}"}
        hb = {"Authorization": f"Bearer {make_token(email='b@example.com')[1]}"}
        rules = (await client.get("/v1/duels", headers=ha)).json()["rules"]
        assert rules["mode_default"] == "quiz" and rules["quiz_questions"] == 5 and rules["quiz_seconds_per_question"] == 60
        assert rules["quiz_available"] is True
        created = await client.post("/v1/duels", json={"language": "he"}, headers=ha)
        assert created.status_code == 201, created.text
        invite = created.json()
        assert invite["mode"] == "quiz" and invite["quiz"] is None
        accepted = await client.post("/v1/duels/accept", json={"code": invite["code"]}, headers=hb)
        assert accepted.status_code == 200, accepted.text
        body = accepted.json()
        quiz = body["quiz"]
        assert quiz["total"] == 5 and quiz["index"] == 0 and len(quiz["current"]["choices"]) == 4 and quiz["review"] == []
        assert 0 < quiz["seconds_left"] <= 60 and body["seconds_left"] <= 300
        assert "correct" not in quiz["current"] and body["opponent"]["score"] is None
        did = body["id"]
        svc = app.state.runtime.duels
        row = app.state.runtime.store.duels[uuid.UUID(did)]
        corrects = [svc.quiz[i["key"]].correct for i in row["items"]]
        # the challenger answers all five right, the opponent all five wrong
        for i, c in enumerate(corrects):
            r = await client.post(f"/v1/duels/{did}/answer", json={"choice": c, "item": i}, headers=ha)
            assert r.status_code == 200, r.text
            assert r.json()["quiz"]["answers"][-1]["correct"] is True and r.json()["quiz"]["score"] == i + 1
        a_done = r.json()
        assert a_done["quiz"]["finished"] is True and a_done["quiz"]["current"] is None and a_done["status"] == "active"
        b_mid = (await client.get(f"/v1/duels/{did}", headers=hb)).json()
        assert b_mid["opponent"]["answered"] is True and b_mid["opponent"]["score"] is None   # hidden until settled
        for i, c in enumerate(corrects):
            r = await client.post(f"/v1/duels/{did}/answer", json={"choice": (c + 1) % 4, "item": i}, headers=hb)
            assert r.status_code == 200, r.text
        result = r.json()
        assert result["status"] == "settled" and result["outcome"] == "challenger" and result["won"] is False
        assert result["coins_delta"] == -5 and result["opponent"]["score"] == 5 and result["me"]["score"] == 0
        assert len(result["quiz"]["review"]) == 5 and result["quiz"]["review"][0]["correct"] == corrects[0]
        assert result["quiz"]["review"][0]["explanation"] and result["quiz"]["review"][0]["theirs"] == corrects[0]
        assert (await client.get("/v1/me/coins", headers=ha)).json()["balance"] == 55
        assert (await client.post(f"/v1/duels/{did}/answer", json={"choice": 9}, headers=hb)).status_code == 422
        assert (await client.post("/v1/duels", json={"language": "he", "mode": "chess"}, headers=ha)).status_code == 422
