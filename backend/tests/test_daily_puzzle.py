"""Daily calendar boundaries, answer isolation and stable rotation of alternate wording."""

from datetime import UTC, date, datetime, timedelta
from itertools import pairwise

import pytest

from app.api.errors import ApiError
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


async def test_real_daily_routes_share_the_question_across_accounts_and_reveal_only_on_request(client, monkeypatch):
    # Freeze calendar and still load today's question/solution through the actual dedicated bank.
    game = app.state.runtime.daily_puzzle
    monkeypatch.setattr(game, "clock", lambda: datetime(2026, 11, 15, 10, tzinfo=UTC))
    base = "/v1/games/daily-puzzle"
    assert (await client.get(base)).status_code == 401
    headers = [{"Authorization": "Bearer " + make_token(email=email)[1]} for email in ("a@example.com", "b@example.com")]
    first = await client.get(base, headers=headers[0])
    assert first.status_code == 200 and first.headers["cache-control"] == "private, no-store"
    he = first.json()
    assert set(he) == {"day", "id", "expires_at", "title", "prompt", "subject"}
    assert he["day"] == "2026-11-15"
    assert he["expires_at"] == "2026-11-16T00:00:00+02:00"
    en = (await client.get(base + "?language=en", headers=headers[1])).json()
    source = game.for_day(START)
    assert he["id"] == en["id"] == source.id
    assert he["prompt"] == source.prompt["he"] and en["prompt"] == source.prompt["en"]
    body = {"day": he["day"], "id": he["id"]}
    assert (await client.post(base + "/reveal", json=body)).status_code == 401
    for language in ("he", "en"):
        result = await client.post(base + "/reveal?language=" + language, json=body, headers=headers[1])
        assert result.status_code == 200 and result.headers["cache-control"] == "private, no-store"
        assert result.json() == {**body, "solution": source.solution[language]}
    for change in ({"day": "2026-11-14"}, {"id": "some-other-puzzle"}):
        assert (await client.post(base + "/reveal", json={**body, **change}, headers=headers[0])).status_code == 409
    assert (await client.get(base + "?language=fr", headers=headers[0])).status_code == 422
    assert app.state.runtime.store.attempts == {} and app.state.runtime.store.coin_ledger == []
