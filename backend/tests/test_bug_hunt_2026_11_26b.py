"""The second batch of fixes after the bug hunt of 2026-11-26.

1. A second attempt on a question already answered (or whose reference was shown) counted as new evidence.
2. Mock interview, a question of another skill than the one being scored: the profile took the wrong skill's state.
3. The coins an answer really earned were not stored: after a reload the answer showed the pure rule's amount.
4. One failed download of the sign-in keys answered every valid session with 401 for thirty seconds.
5. A full connection pool left as a 500; a text Postgres cannot store (the NUL character) left as a 500.
6. The NUL character in an answer or in a program's output failed the save.
7. A name in the user's own metadata that is not text failed every call of that user.
8. A follow-up answer sent again with the same key was refused instead of replayed.
9. The program item of a finished interview could be ticked twice.
"""
from __future__ import annotations

import json
import time
import uuid

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app import auth as auth_module
from app.api import errors
from app.api.errors import ApiError
from app.auth import AuthenticatedUser, TokenVerifier
from app.engine.catalog import load_catalog
from app.engine.practice import PracticeAttempt
from app.repo import attempts as attempts_repo
from app.schemas.execution import ExecutionResult
from app.services.interview_service import InterviewConfig, InterviewService
from app.services.memory_store import InMemoryStore
from app.services.practice_service import PracticeService, ServiceConfig
from tests import authtools
from tests.test_interview_service import Clock, interviewer
from tests.test_practice_hardening import GOOD, SEEDS, WEAK, scripted

Q = "example-sensor-majority"
MAJORITY = "alarm = (A & B) | (B & C) | (A & C)"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(SEEDS)


def practice(catalog, replies) -> tuple[PracticeService, InMemoryStore, object]:
    provider = scripted(replies)
    store = InMemoryStore(catalog)
    return PracticeService(store, catalog, provider, ServiceConfig()), store, provider


# ----------------------------------------------------------------------------- 1. a second attempt is not new


class TestASecondAttemptIsNotNewEvidence:
    async def test_the_first_attempt_is_new_and_the_one_after_an_answer_is_not(self, catalog):
        user = uuid.uuid4()
        svc, store, _ = practice(catalog, [GOOD, GOOD])
        first = uuid.UUID((await svc.start(user, question_key=Q)).id)
        assert store.attempts[first]["row"]["familiarity"] == "new"
        one, _ = await svc.submit(user, first, MAJORITY, idempotency_key="a")
        second = uuid.UUID((await svc.start(user, question_key=Q)).id)
        assert store.attempts[second]["row"]["familiarity"] == "seen_same"
        two, _ = await svc.submit(user, second, MAJORITY, idempotency_key="b")
        assert one.band == two.band == "STRONG"
        weights = [store.attempts[a]["row"]["submissions"][0]["evidence_weight"] for a in (first, second)]
        assert weights[0] > 0 and weights[1] == pytest.approx(weights[0] * 0.4, rel=1e-3)     # §2.9 seen_same

    async def test_a_reference_shown_on_an_attempt_that_was_never_answered_counts_too(self, catalog):
        user = uuid.uuid4()
        svc, store, _ = practice(catalog, [GOOD])
        first = uuid.UUID((await svc.start(user, question_key=Q)).id)
        await svc.reveal_reference(user, first)                    # read the solution, answer nothing
        second = uuid.UUID((await svc.start(user, question_key=Q)).id)
        assert store.attempts[second]["row"]["familiarity"] == "seen_same"

    async def test_another_user_and_another_question_stay_new(self, catalog):
        user, other = uuid.uuid4(), uuid.uuid4()
        svc, store, _ = practice(catalog, [GOOD])
        first = uuid.UUID((await svc.start(user, question_key=Q)).id)
        await svc.submit(user, first, MAJORITY, idempotency_key="a")
        theirs = uuid.UUID((await svc.start(other, question_key=Q)).id)
        assert store.attempts[theirs]["row"]["familiarity"] == "new"
        another = next(k for k, q in catalog.questions.items() if k != Q and q.assets.get("assessment_ready") is not False)
        mine = uuid.UUID((await svc.start(user, question_key=another)).id)
        assert store.attempts[mine]["row"]["familiarity"] == "new"

    async def test_a_lookup_that_fails_never_stops_a_question_from_opening(self, catalog, monkeypatch):
        from app.services.memory_store import _MemoryTx

        async def broken(self, user_id, question_id, *, except_attempt=None):
            raise RuntimeError("the attempts could not be read")
        monkeypatch.setattr(_MemoryTx, "answered_before", broken)
        user = uuid.uuid4()
        svc, store, _ = practice(catalog, [])
        opened = uuid.UUID((await svc.start(user, question_key=Q)).id)
        assert store.attempts[opened]["row"]["familiarity"] == "new"

    async def test_an_attempt_opened_and_left_does_not_mark_the_question(self, catalog):
        user = uuid.uuid4()
        svc, store, _ = practice(catalog, [])
        await svc.start(user, question_key=Q)
        second = uuid.UUID((await svc.start(user, question_key=Q)).id)
        assert store.attempts[second]["row"]["familiarity"] == "new"


# ----------------------------------------------------------------------------- 2. the interview's scored skill


class TestTheProfileTakesTheSkillTheEngineScored:
    async def test_a_question_of_another_skill_does_not_move_that_skill(self, catalog):
        """The shape of a step back to a prerequisite: the question belongs to one skill, the engine is scoring
        another. Staged by swapping the first turn's question, because the test bank is too thin to step back."""
        user = uuid.uuid4()
        store = InMemoryStore(catalog)
        svc = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False))
        svc.clock = Clock()
        view = await svc.start(user, duration_min=45, language="en")
        sid = uuid.UUID(view.id)
        turn = store.sessions[sid]["turns"][0]
        scored = turn["skill_key"]                                  # the skill the engine is on
        plan_skills = {p.skill for p in view.plan}
        other = next(q for q in catalog.questions.values()
                     if q.primary_skill != scored and q.primary_skill in plan_skills and q.deterministic_check is None)
        turn["question_key"] = other.key                            # as after STEP_BACK: another skill's question
        svc.clock.advance()
        await svc.answer(user, sid, 0, "a careful, correct answer", idempotency_key="t0")
        rows = {skill: row for (owner, skill), row in store.profiles.items() if owner == user}
        assert set(rows) == {scored}, "the turn went to the question's skill, not to the skill that was scored"
        assert len(rows[scored]["engine_state"]["history"]) == 1
        metric = next(m for m in store.metrics if m.get("session_id"))
        assert metric["skill_key"] == scored


# ----------------------------------------------------------------------------- 3. the coins an answer earned


class TestTheCoinsAnAnswerEarnedAreStored:
    def row(self):
        return {"evidence_mode": "deep", "submissions": [
            {"revision": 1, "coins_awarded": 0, "evaluating_since": None},
            {"revision": 2, "coins_awarded": None, "evaluating_since": "2026-11-26T10:00:00+00:00"},
            {"revision": 3, "coins_awarded": 2, "evaluating_since": None}]}

    def test_the_amount_is_written_by_revision_and_zero_counts(self):
        state = attempts_repo.engine_state(self.row())
        assert state["coins_awarded"] == {"1": 0, "3": 2}
        assert state["evaluating_since"] == {"2": "2026-11-26T10:00:00+00:00"}
        json.dumps(state)                                           # a jsonb column: it has to serialize

    def test_it_is_read_back_for_its_own_revision(self):
        state = json.loads(json.dumps(attempts_repo.engine_state(self.row())))
        assert attempts_repo.revision_extras(state, 1) == {"evaluating_since": None, "coins_awarded": 0}
        assert attempts_repo.revision_extras(state, 2)["coins_awarded"] is None
        assert attempts_repo.revision_extras(state, 3)["coins_awarded"] == 2

    def test_an_attempt_saved_before_the_amount_was_stored_reads_none(self):
        assert attempts_repo.revision_extras({}, 1) == {"evaluating_since": None, "coins_awarded": None}
        assert attempts_repo.revision_extras({"evaluating_since": {"1": "x"}}, 1)["coins_awarded"] is None

    def test_the_engine_reads_the_stored_amount_from_the_row(self, catalog):
        """The row the database returns is what `PracticeAttempt.restore` takes: the key has to be the model's."""
        from app.engine.practice import Submission
        assert "coins_awarded" in Submission.model_fields


# ----------------------------------------------------------------------------- 4. the sign-in keys


class Flaky(authtools.FakeJWKSClient):
    """The project's key set, which can be made unreachable."""

    def __init__(self, failure: Exception | None = None):
        self.down, self.downloads = True, 0
        self.failure = failure or jwt.PyJWKClientConnectionError("Fail to fetch data from the url, err: timed out")

    def get_signing_key_from_jwt(self, token):
        self.downloads += 1
        if self.down:
            raise self.failure
        return super().get_signing_key_from_jwt(token)

    def get_signing_keys(self):
        if self.down:
            raise self.failure
        return super().get_signing_keys()


def retry_window_passed(verifier) -> None:
    verifier._last_lookup -= auth_module.KEY_RETRY_SECONDS + 0.1


class TestAFailedKeyDownloadIsNotAnUnknownKey:
    async def test_a_valid_session_is_told_to_retry_not_that_it_ended(self):
        client = Flaky()
        verifier = TokenVerifier(supabase_url=authtools.SUPABASE_URL, jwks_client=client)
        _, token = authtools.make_token()
        with pytest.raises(ApiError) as refused:
            await verifier.verify(token)
        assert refused.value.status == 503 and refused.value.code == "temporarily_unavailable"
        assert refused.value.headers["Retry-After"] == str(auth_module.KEY_RETRY_SECONDS)

    async def test_the_next_download_comes_after_two_seconds_not_thirty(self):
        client = Flaky()
        verifier = TokenVerifier(supabase_url=authtools.SUPABASE_URL, jwks_client=client)
        user_id, token = authtools.make_token()
        with pytest.raises(ApiError):
            await verifier.verify(token)
        client.down = False                                        # the key set answers again
        with pytest.raises(ApiError) as still:                     # inside the two seconds: no second download yet
            await verifier.verify(token)
        assert still.value.status == 503 and client.downloads == 1
        retry_window_passed(verifier)
        assert (await verifier.verify(token)).id == user_id and client.downloads == 2
        assert auth_module.KEY_RETRY_SECONDS < auth_module.KEY_SET_FRESH_SECONDS

    async def test_a_key_seen_before_is_still_believed_while_the_set_is_unreachable(self):
        client = Flaky()
        client.down = False
        verifier = TokenVerifier(supabase_url=authtools.SUPABASE_URL, jwks_client=client)
        user_id, token = authtools.make_token()
        assert (await verifier.verify(token)).id == user_id
        kid, (seen, key) = next(iter(verifier._keys.items()))      # an hour later the cached key has expired...
        verifier._keys[kid] = (seen - auth_module.KEY_CACHE_SECONDS - auth_module.KEY_SET_FRESH_SECONDS - 1, key)
        verifier._last_lookup = time.monotonic() - auth_module.KEY_SET_FRESH_SECONDS - 1
        client.down = True                                          # ...and the refresh cannot reach the key set
        assert (await verifier.verify(token)).id == user_id
        verifier._keys[kid] = (time.monotonic() - auth_module.KEY_STALE_SECONDS - 1, key)   # but not for ever
        retry_window_passed(verifier)
        with pytest.raises(ApiError) as refused:
            await verifier.verify(token)
        assert refused.value.status == 503

    async def test_a_made_up_key_is_still_refused_when_the_set_was_reached(self):
        client = Flaky()
        client.down = False
        verifier = TokenVerifier(supabase_url=authtools.SUPABASE_URL, jwks_client=client)
        _, fake = authtools.make_token(kid="made-up")
        with pytest.raises(ApiError) as refused:
            await verifier.verify(fake)
        assert refused.value.status == 401 and refused.value.code == "unauthenticated"
        _, again = authtools.make_token(kid="made-up-2")           # and it does not buy a second download
        with pytest.raises(ApiError) as second:
            await verifier.verify(again)
        assert second.value.status == 401 and client.downloads == 1

    async def test_a_download_that_dies_of_anything_else_is_not_a_500(self):
        client = Flaky(failure=ValueError("Expecting value: line 1 column 1 (char 0)"))    # an HTML error page
        verifier = TokenVerifier(supabase_url=authtools.SUPABASE_URL, jwks_client=client)
        _, token = authtools.make_token()
        with pytest.raises(ApiError) as refused:
            await verifier.verify(token)
        assert refused.value.status == 503


# ----------------------------------------------------------------------------- 5. two database answers


class _Refused(Exception):
    """What the driver raises, with Postgres's code on it."""

    def __init__(self, sqlstate: str):
        super().__init__("refused")
        self.sqlstate = sqlstate


def failing_app(exc: Exception) -> FastAPI:
    app = FastAPI()
    errors.install(app)

    @app.get("/boom")
    async def boom():
        raise exc
    return app


async def get(app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
        return await client.get("/boom")


class TestTwoDatabaseAnswers:
    async def test_a_full_pool_is_503_with_retry_after(self):
        response = await get(failing_app(PoolTimeoutError("QueuePool limit of size 5 overflow 5 reached")))
        assert response.status_code == 503 and response.headers["Retry-After"] == "5"
        assert response.json()["error"]["code"] == "temporarily_unavailable"

    @pytest.mark.parametrize("sqlstate", ["22021", "22P05"])
    async def test_a_character_postgres_cannot_store_is_422(self, sqlstate):
        response = await get(failing_app(DBAPIError("insert ...", {}, _Refused(sqlstate))))
        assert response.status_code == 422 and response.json()["error"]["code"] == "validation"

    async def test_any_other_query_error_is_still_a_500(self):
        response = await get(failing_app(DBAPIError("insert ...", {}, _Refused("23505"))))
        assert response.status_code == 500


# ----------------------------------------------------------------------------- 6. the NUL character


class TestTheNulCharacter:
    def test_an_answer_loses_it(self):
        assert PracticeAttempt._answer_text({"text": "F = A\x00B "}) == "F = AB"
        assert PracticeAttempt._answer_text("\x00") == ""

    def test_a_program_output_keeps_its_place_but_can_be_stored(self):
        result = ExecutionResult.model_validate({
            "status": "completed", "language": "c", "executed": True, "stdout": "hi\x00", "stderr": "\x00",
            "cases": [{"index": 0, "passed": False, "actual": {"out": ["a\x00b"]}}]})
        stored = json.dumps(result.model_dump(mode="json"), ensure_ascii=False)
        assert "\x00" not in stored and "\\u0000" not in stored
        assert result.stdout == "hi�" and result.cases[0].actual == {"out": ["a�b"]}

    def test_an_output_without_it_is_untouched(self):
        result = ExecutionResult.model_validate({"status": "passed", "language": "python", "stdout": "42\n"})
        assert result.stdout == "42\n"


# ----------------------------------------------------------------------------- 7. the user's own name


class TestTheDisplayNameIsText:
    @pytest.mark.parametrize("metadata", [{"full_name": 5}, {"full_name": ["a"]}, {"full_name": {"a": 1}},
                                          {"full_name": "   "}, ["not", "a", "dict"], None, "text"])
    def test_anything_else_is_no_name(self, metadata):
        user = AuthenticatedUser(id=uuid.uuid4(), email="a@example.com", role="authenticated",
                                 claims={"user_metadata": metadata})
        assert user.display_name is None
        assert ((user.display_name or "")[:120] or None) is None      # what repo/users.py does with it

    def test_the_first_text_wins(self):
        user = AuthenticatedUser(id=uuid.uuid4(), email="a@example.com", role="authenticated",
                                 claims={"user_metadata": {"full_name": 7, "name": "Dana", "display_name": "D"}})
        assert user.display_name == "Dana"


# ----------------------------------------------------------------------------- 8. a follow-up sent again


class TestAFollowUpAnswerSentAgainIsReplayed:
    async def test_the_same_key_gets_the_stored_result_and_no_model_call(self, catalog):
        user = uuid.uuid4()
        svc, store, provider = practice(catalog, [WEAK, GOOD, GOOD])
        attempt_id = uuid.UUID((await svc.start(user, question_key=Q)).id)
        _, view = await svc.submit(user, attempt_id, "alarm = A ^ B ^ C", idempotency_key="main")
        turn = view.pending_follow_up.turn
        first, _ = await svc.submit(user, attempt_id, "at least two of the three", idempotency_key="f1", follow_up_turn=turn)
        calls = len(provider.requests)
        again, _ = await svc.submit(user, attempt_id, "at least two of the three", idempotency_key="f1", follow_up_turn=turn)
        assert again.revision == first.revision and again.status == "done" and again.band == first.band
        assert len(provider.requests) == calls

    async def test_another_key_on_an_answered_follow_up_is_still_refused(self, catalog):
        user = uuid.uuid4()
        svc, store, _ = practice(catalog, [WEAK, GOOD, GOOD])
        attempt_id = uuid.UUID((await svc.start(user, question_key=Q)).id)
        _, view = await svc.submit(user, attempt_id, "alarm = A ^ B ^ C", idempotency_key="main")
        turn = view.pending_follow_up.turn
        _, view = await svc.submit(user, attempt_id, "at least two of the three", idempotency_key="f1", follow_up_turn=turn)
        if view.pending_follow_up is None or view.pending_follow_up.turn != turn:
            with pytest.raises(ApiError) as refused:
                await svc.submit(user, attempt_id, "something else", idempotency_key="f2", follow_up_turn=turn)
            assert refused.value.code == "no_pending_follow_up"


# ----------------------------------------------------------------------------- 9. the program tick


class TestAFinishedInterviewTicksTheProgramOnce:
    async def test_a_later_save_of_the_finished_interview_does_not_tick_again(self, catalog):
        user, ticks = uuid.uuid4(), []

        async def finished(tx, user_id, session_id):
            ticks.append(session_id)

        store = InMemoryStore(catalog)
        svc = InterviewService(store, catalog, interviewer([GOOD]), InterviewConfig(reviewed_only=False),
                               on_finished=finished)
        svc.clock = Clock()
        view = await svc.start(user, duration_min=20, language="en")
        sid = uuid.UUID(view.id)
        await svc.end(user, sid)
        assert ticks == [sid]
        assert store.sessions[sid]["row"]["state"]["program_ticked"] is True      # stored, not only in memory
        await svc.report(user, sid)                                # generates the narrative and saves the row again
        await svc.report(user, sid)
        assert ticks == [sid]
