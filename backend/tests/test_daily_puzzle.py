"""Daily calendar boundaries, answer isolation and stable rotation of alternate wording."""

import asyncio

from datetime import UTC, date, datetime, timedelta
from itertools import pairwise

import pytest

from app.api.errors import ApiError
from app.engine.providers import LLMError, ScriptedProvider
from app.services.daily_puzzle_grading import DailyPuzzleGrading
from tests.test_practice_hardening import GOOD
from app.main import app
from app.services.daily_puzzle import DailyPuzzleService
from app.services.daily_puzzle_bank import DailyPuzzleEntry
from tests import test_duels
from tests.authtools import make_token

catalog = test_duels.catalog
client = test_duels.client

START = date(2026, 11, 15)


def entry(source: str, wording: str, starts: date = START):
    return DailyPuzzleEntry(
        id=f"{source}-{wording}", source_question_key=source, subject="hardware", available_from=starts,
        title={"he": "כותרת", "en": "Title"}, prompt={"he": "חידה", "en": "Puzzle"},
        solution={"he": "פתרון", "en": "Solution"},
    )


def test_shuffle_visits_each_family_then_its_other_phrasing_and_keeps_the_day_on_deploy():
    bank = tuple(entry(source, wording) for source in ("logic", "array", "signal") for wording in ("first", "second"))
    game = DailyPuzzleService(lambda: bank)
    expanded = DailyPuzzleService(lambda: (*reversed(bank), entry("tree", "first", START + timedelta(days=2))))
    days = [START + timedelta(days=n) for n in range(30)]
    first_week = [game.for_day(day) for day in days[:6]]
    assert len({p.id for p in first_week}) == 6
    assert len({p.source_question_key for p in first_week[:3]}) == 3
    assert [expanded.for_day(d) for d in days[:3]] == first_week[:3]
    assert {expanded.for_day(d).source_question_key for d in days[3:7]} == {"logic", "array", "signal", "tree"}
    for yesterday, today in pairwise(days):
        assert expanded.for_day(today).source_question_key != expanded.for_day(yesterday).source_question_key
    reordered = DailyPuzzleService(lambda: tuple(reversed(bank)))
    assert [reordered.for_day(d).id for d in days] == [game.for_day(d).id for d in days]


@pytest.mark.parametrize(("utc_at_midnight", "day_length"), [
    (datetime(2027, 3, 25, 22, tzinfo=UTC), 23),   # Jerusalem springs forward during March 26
    (datetime(2027, 10, 30, 21, tzinfo=UTC), 25),  # Jerusalem falls back during October 31
])
def test_reset_uses_local_midnight_even_when_a_day_is_not_24_hours(utc_at_midnight, day_length):
    now = utc_at_midnight - timedelta(microseconds=1)
    game = DailyPuzzleService(lambda: (entry("a", "1"), entry("b", "1")), lambda: now)
    yesterday = game.today("he")
    assert yesterday["expires_at"].astimezone(UTC) == utc_at_midnight
    now = utc_at_midnight
    today = game.today("en")
    assert today["id"] != yesterday["id"]
    assert today["day"] == yesterday["day"] + timedelta(days=1)
    assert today["expires_at"].astimezone(UTC) == now + timedelta(hours=day_length)
    with pytest.raises(ApiError) as stale:
        game.reveal(yesterday["day"], yesterday["id"], "he")
    assert stale.value.status == 409


def test_no_eligible_puzzle_does_not_leak_other_bank_content():
    game = DailyPuzzleService(lambda: (entry("future", "1"),))
    with pytest.raises(ApiError) as exc:
        game.for_day(START - timedelta(days=1))
    assert exc.value.status == 503


BASE = "/v1/games/daily-puzzle"
NOW = datetime(2026, 11, 15, 10, tzinfo=UTC)
CARD = dict(what_happened="You identified the boundary.", why_it_matters="It keeps the scan linear.",
            next_step="Check both ends.", your_reasoning_vs_reference="Both preserve the invariant.")


def member(email):
    return {"Authorization": "Bearer " + make_token(email=email)[1]}


def judge(response):
    provider = ScriptedProvider(response)
    provider.model = "test-model"
    return provider


async def graded(client, headers):
    await asyncio.wait_for(asyncio.gather(*list(app.state.runtime.daily_grading.tasks)), 6)
    return (await client.get(BASE, headers=headers)).json()


async def test_real_daily_routes_keep_answer_private_until_graded(client, monkeypatch):
    calendar = app.state.runtime.daily_puzzle
    monkeypatch.setattr(calendar, "clock", lambda: NOW)
    assert (await client.get(BASE)).status_code == 401
    a, b = member("a@example.com"), member("b@example.com")
    first = await client.get(BASE, headers=a)
    assert first.status_code == 200 and first.headers["cache-control"] == "private, no-store"
    he = first.json()
    assert he["status"] == "open" and he["submission"] is None and he["score"] is None and he["passed"] is None
    assert he["day"] == "2026-11-15" and he["expires_at"] == "2026-11-16T00:00:00+02:00"
    source = calendar.for_day(START)
    en = (await client.get(BASE + "?language=en", headers=b)).json()
    assert source.id == he["id"] == en["id"] and en["attempt_id"] != he["attempt_id"]
    assert he["prompt"] == source.prompt["he"] and en["prompt"] == source.prompt["en"]
    body = {"day": he["day"], "id": he["id"]}
    assert (await client.post(BASE + "/reveal", json=body)).status_code == 401
    for change in ({}, {"day": "2026-11-14"}, {"id": "some-other-puzzle"}):
        assert (await client.post(BASE + "/reveal", json={**body, **change}, headers=a)).status_code == 409
    assert (await client.get(BASE + "?language=fr", headers=a)).status_code == 422
    assert not app.state.runtime.store.feedback_allowance


@pytest.mark.parametrize(("correctness", "won"), [(0.89, False), (0.90, True), (0.91, True)])
async def test_one_monthly_charge_and_one_variant_verdict_on_concurrent_submits(client, monkeypatch, correctness, won):
    runtime = app.state.runtime
    monkeypatch.setattr(runtime.daily_puzzle, "clock", lambda: NOW)
    gate = asyncio.Event()
    async def respond(request):
        if request.role == "evaluator":
            await gate.wait()
            return {**GOOD, "correctness": correctness}
        return CARD
    provider = judge(respond)
    monkeypatch.setattr(runtime.practice, "provider", provider)
    a, b = member("a@example.com"), member("b@example.com")
    puzzle = (await client.get(BASE + "?language=en", headers=a)).json()
    ids = {k: puzzle[k] for k in ("day", "id")}
    answer = {**ids, "answer": {"text": "I keep the zeros at the beginning."}}
    submissions = await asyncio.gather(*(client.post(BASE + "/submit?language=en", json=answer, headers=a) for _ in range(2)))
    assert all(r.status_code == 202 and r.json()["status"] == "evaluating" for r in submissions)
    assert len(runtime.store.feedback_allowance) == 1
    assert (await client.post(BASE + "/submit", json={**ids, "answer": {"text": "change"}}, headers=a)).status_code == 409
    assert (await client.post(BASE + "/reveal", json=ids, headers=a)).status_code == 409
    gate.set()
    result = await graded(client, a)
    assert result["score"] == correctness * 100 and result["passed"] is won
    assert result["submission"]["card"] == CARD and result["submission"]["assessed_by"] == "model"
    assert [r.role for r in provider.requests] == ["evaluator", "feedback"]
    entry = runtime.daily_puzzle.for_day(START)
    assert entry.prompt["en"] in provider.requests[0].system[1] and entry.solution["en"] in provider.requests[0].system[1]
    main = runtime.catalog.questions[entry.source_question_key].text("en").prompt
    assert main not in provider.requests[0].system[1]
    replay = (await client.post(BASE + "/submit", json=answer, headers=a)).json()
    assert replay["passed"] is won and len(runtime.store.feedback_allowance) == 1 and len(provider.requests) == 2
    assert (await client.post(BASE + "/reveal", json=ids, headers=a)).json()["solution"] == entry.solution["he"]
    assert (await client.post(BASE + "/reveal", json=ids, headers=b)).status_code == 409
    assert len(runtime.store.usage) == 2 and all(event["user_id"] for event in runtime.store.usage)
    assert runtime.store.attempts == {} and runtime.store.coin_ledger == []


async def test_failure_preserves_answer_refunds_retries_and_quota_denial_stays_open(client, monkeypatch):
    runtime = app.state.runtime
    monkeypatch.setattr(runtime.daily_puzzle, "clock", lambda: NOW)
    monkeypatch.setattr(runtime.practice, "provider", judge([LLMError("unavailable"), {**GOOD, "correctness": 1}, CARD]))
    a = member("a@example.com")
    p = (await client.get(BASE, headers=a)).json()
    ids = {k: p[k] for k in ("day", "id")}
    answer = {**ids, "answer": {"text": "My saved answer"}}
    assert (await client.post(BASE + "/submit", json={**ids, "answer": {"text": "  "}}, headers=a)).status_code == 422
    monkeypatch.setattr(runtime.practice.config, "monthly_feedback_limit", 0)
    denied = await client.post(BASE + "/submit", json=answer, headers=a)
    assert denied.status_code == 429 and denied.json()["error"]["code"] == "monthly_feedback_limit"
    assert (await client.get(BASE, headers=a)).json()["status"] == "open"
    monkeypatch.setattr(runtime.practice.config, "monthly_feedback_limit", 1)
    assert (await client.post(BASE + "/submit", json=answer, headers=a)).status_code == 202
    failed = await graded(client, a)
    assert failed["status"] == "failed" and failed["feedback_remaining"] == 1 and not runtime.store.feedback_allowance
    assert failed["submission"]["answer"] == "My saved answer"
    assert (await client.post(BASE + "/submit", json={**ids, "answer": {"text": "new answer"}}, headers=a)).status_code == 409
    assert (await client.post(BASE + "/retry", json=ids, headers=a)).status_code == 202
    done = await graded(client, a)
    assert done["score"] == 100 and done["passed"] and done["feedback_remaining"] == 0
    assert done["submission"]["answer"] == failed["submission"]["answer"]


async def test_unfinished_lease_is_recovered_across_service_instances(client, monkeypatch):
    runtime = app.state.runtime
    now = NOW
    monkeypatch.setattr(runtime.daily_puzzle, "clock", lambda: now)
    a = member("a@example.com")
    p = (await client.get(BASE, headers=a)).json()
    payload = {k: p[k] for k in ("day", "id")}
    # Simulate a hard process stop after the DB commit, before the model request.
    async def stopped(*_):
        return
    monkeypatch.setattr(runtime.daily_grading, "_grade", stopped)
    await client.post(BASE + "/submit", json={**payload, "answer": {"text": "unchanged"}}, headers=a)
    now += timedelta(minutes=11)
    monkeypatch.setattr(runtime, "daily_grading", DailyPuzzleGrading(runtime.daily_puzzle, runtime.practice))
    recovered = (await client.get(BASE, headers=a)).json()
    assert recovered["status"] == "failed" and recovered["submission"]["answer"] == "unchanged"
    assert not runtime.store.feedback_allowance
async def test_circuit_code_truth_table_and_owned_photo_reach_the_shared_evaluator(client, monkeypatch):
    import uuid
    from tests.test_visual_answers import visual as circuit_answer

    runtime = app.state.runtime
    monkeypatch.setattr(runtime.daily_puzzle, "clock", lambda: NOW)
    provider = judge([GOOD, CARD])
    monkeypatch.setattr(runtime.practice, "provider", provider)
    user_id, token = make_token(email="a@example.com")
    headers = {"Authorization": "Bearer " + token}
    p = (await client.get(BASE, headers=headers)).json()
    ids = {k: p[k] for k in ("day", "id")}
    img = {"name": "answer.jpg", "mime": "image/jpeg", "path": f"{user_id}/{p['attempt_id']}/{uuid.uuid4()}.jpg", "size": 100}
    visual = circuit_answer()
    visual["images"] = [img]
    answer = {"text": "Truth table:\nA Y\n0 0\n1 1\n\n```python\nreturn a\n```", "visual": visual}
    # Nonexistent photo is rejected before consuming anything.
    assert (await client.post(BASE + "/submit", headers=headers, json={**ids, "answer": answer})).status_code == 422
    runtime.store.answer_images[img["path"]] = {"mime": img["mime"], "size": img["size"]}
    async def fetch(path):
        return ("image/jpeg", b"photo") if path == img["path"] else None
    monkeypatch.setattr(runtime.practice, "image_fetcher", fetch)
    assert (await client.post(BASE + "/submit", headers=headers, json={**ids, "answer": answer})).status_code == 202
    done = await graded(client, headers)
    request = provider.requests[0]
    assert done["status"] == "done" and done["submission"]["visual"] == visual
    assert "Truth table:" in request.user and "return a" in request.user
    assert 'AND "AND"' in request.user and request.images == [("image/jpeg", b"photo")]

async def test_finish_and_retry_after_midnight_without_opening_historical_attempts(client, monkeypatch):
    runtime = app.state.runtime
    now = NOW
    monkeypatch.setattr(runtime.daily_puzzle, "clock", lambda: now)
    monkeypatch.setattr(runtime.practice, "provider", judge([LLMError("temporarily offline"), GOOD, CARD]))
    a, b = member("a@example.com"), member("b@example.com")
    puzzle = (await client.get(BASE, headers=a)).json()
    ids = {k: puzzle[k] for k in ("day", "id")}
    body = {**ids, "answer": {"text": "An answer submitted before midnight."}}
    assert (await client.post(BASE + "/submit", json=body, headers=a)).status_code == 202
    await graded(client, a)
    now += timedelta(days=1)
    assert (await client.get(BASE, headers=a)).json()["day"] != puzzle["day"]
    history = BASE + "?day=" + puzzle["day"]
    assert (await client.get(history, headers=a)).json()["status"] == "failed"
    assert (await client.get(history, headers=b)).status_code == 409
    assert (await client.post(BASE + "/submit", json=body, headers=b)).status_code == 409
    assert (await client.post(BASE + "/retry", json=ids, headers=a)).status_code == 202
    await graded(client, a)
    assert (await client.get(history, headers=a)).json()["status"] == "done"
    assert (await client.post(BASE + "/reveal", json=ids, headers=a)).status_code == 200
    assert (await client.get(BASE, headers=a)).json()["status"] == "open"
    assert len(runtime.store.feedback_allowance) == 1 and len(runtime.store.daily_attempts) == 2
