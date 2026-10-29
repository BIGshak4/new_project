"""Two-stage quiz draw, immutable match content, and the server-controlled readiness lobby."""

from dataclasses import replace

import pytest

from app.api.errors import ApiError
from app.api.v1.duels import _rules, _view
from app.engine.catalog import load_catalog
from app.services.duels import LOBBY_TTL
from tests.test_duels import QUIZ, A, B, C, answers_for, play, service, start_duel
from tests.test_practice_hardening import SEEDS


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def source_bank(*, sources=6):
    return [replace(QUIZ[0], key=f"short-{source:04d}-v{variant}", source_key=f"short-{source:04d}",
                    variant=variant, status="approved")
            for source in range(sources) for variant in range(1, 6)]


async def test_the_draw_samples_sources_first_then_one_variant(catalog, monkeypatch):
    svc, _, _ = service(catalog)
    svc.quiz = {q.key: q for q in source_bank()}
    svc.approved_only = True

    def sample(population, wanted):
        assert len(population) == 6 and wanted == 5  # not a 30-variant draw that weights repeated sources
        return population[:wanted]

    monkeypatch.setattr("app.services.duels.random.sample", sample)
    monkeypatch.setattr("app.services.duels.random.choice", lambda variants: variants[-1])
    duel = await start_duel(svc, mode="quiz")
    chosen = [svc.quiz_item(item) for item in duel.items]
    assert len({q.source_key for q in chosen}) == 5
    assert {q.variant for q in chosen} == {5}
    assert _rules(svc)["quiz_source_count"] == 6 and _rules(svc)["quiz_variant_count"] == 30


async def test_partial_or_unreviewed_variant_groups_cannot_enable_a_game(catalog):
    svc, _, _ = service(catalog)
    bank = source_bank(sources=5)
    bank[-1] = replace(bank[-1], status="draft")
    svc.quiz = {q.key: q for q in bank}
    svc.approved_only = True
    assert not _rules(svc)["quiz_available"] and _rules(svc)["quiz_source_count"] == 4
    with pytest.raises(ApiError) as blocked:
        await svc.create(A, language="he")
    assert blocked.value.code == "no_reviewed_questions"


async def test_match_snapshot_survives_bank_edits_removal_and_rules_changes(catalog):
    svc, store, clock = service(catalog)
    duel = await start_duel(svc, mode="quiz")
    before = _view(svc, duel, A).model_dump(mode="json")
    corrects = answers_for(svc, duel, right=5)
    original = [svc.quiz_item(item) for item in duel.items]
    svc.quiz = {}  # emulates a later deployment removing every selected bank item
    svc.rules = replace(svc.rules, duel_quiz_seconds=10)
    reloaded = await svc.get(A, duel.id)
    after = _view(svc, reloaded, A).model_dump(mode="json")
    assert before["quiz"]["current"] == after["quiz"]["current"]
    assert after["quiz"]["seconds_per_question"] == 60
    assert "snapshot" not in str(after) and "correct" not in after["quiz"]["current"]
    await play(svc, A, duel, corrects, clock)
    settled = await play(svc, B, duel, corrects, clock)
    review = _view(svc, settled, A).quiz.review
    assert len(review) == 5
    assert [q.correct for q in review] == corrects
    assert [q.explanation for q in review] == [q.text(q.explanation, "en") for q in original]


async def test_waiting_room_never_exposes_a_question_or_runs_the_answer_clock(catalog):
    svc, _, clock = service(catalog)
    duel = await svc.accept(B, (await svc.create(A, language="he")).code)
    clock.advance(120)
    first = await svc.ready(A, duel.id)
    waiting = _view(svc, first, A)
    assert waiting.me.ready and not waiting.opponent.ready
    assert waiting.quiz.current is None and waiting.quiz.seconds_left is None and waiting.deadline is None
    assert waiting.lobby_expires_at is not None and waiting.started_at is None
    with pytest.raises(ApiError) as early:
        await svc.answer(A, duel.id, choice=0, item=0)
    assert early.value.code == "conflict"
    with pytest.raises(ApiError) as stranger:
        await svc.ready(C, duel.id)
    assert stranger.value.code == "not_found"
    clock.advance(50)
    started = await svc.ready(B, duel.id)
    assert started.player(A)["opened_at"] == started.player(B)["opened_at"] == clock.now.isoformat()
    assert _view(svc, started, B).quiz.seconds_left == 60


@pytest.mark.parametrize("cancel_by", [A, B])
async def test_either_player_can_leave_lobby_with_both_stakes_refunded(catalog, cancel_by):
    svc, _, _ = service(catalog)
    duel = await svc.accept(B, (await svc.create(A, language="en")).code)
    await svc.ready(A, duel.id)
    cancelled = await svc.cancel(cancel_by, duel.id)
    assert cancelled.status == "cancelled"
    assert (await svc.coins.wallet(A)).balance == (await svc.coins.wallet(B)).balance == 50


async def test_abandoned_lobby_expires_and_refunds_once(catalog):
    svc, store, clock = service(catalog)
    duel = await svc.accept(B, (await svc.create(A, language="en")).code)
    await svc.ready(A, duel.id)
    clock.advance(LOBBY_TTL.total_seconds() + 1)
    expired = await svc.get(B, duel.id)
    assert expired.status == "cancelled" and expired.outcome == "expired"
    await svc.get(A, duel.id)
    assert len([r for r in store.coin_ledger if r["kind"] == "refund"]) == 2
    assert (await svc.coins.wallet(A)).balance == (await svc.coins.wallet(B)).balance == 50
