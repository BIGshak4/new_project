"""Duels (Shaked, 2026-10-22): two players, five coins each, decided on the clock.

Two modes on the same routes:

* **quiz** (the default; Shaked: "American questions with specific answers, a minute each max"): five
  multiple-choice questions from `seeds/duel_quiz.json`, the same five in the same order for both players, one
  minute per question at most. One point per correct answer; more points wins the ten coins, the same points goes to
  the lower total answering time, the same second is a draw. No model call: a quiz duel costs nothing to run and
  the result is never a judgement. The correct option is sent to nobody until the duel is settled.
  Sample five distinct source questions, then one variant each, without consulting player exposure history.
  Acceptance joins a waiting room; both players must mark themselves ready before the clocks start.
* **judged**: one short bank question neither player has met, three minutes, both answers scored by the same judge
  as practice; the better band wins, a tie goes to the faster answer.

In both: the challenger opens a duel and gets an invite code (a link, in Harel's screen); the opponent accepts and
both stakes leave the wallets into the duel (ledger rows of kind "stake"). A player who never answers forfeits;
when nobody answers both are refunded. A duel changes nothing in the skill profile and earns no XP: it is a game on
coins, and coins have no monetary value.

Guards: a ten-minute cooldown per pair of players, a daily ceiling on duel winnings (net), an optional daily duel
count (off until Shaked decides), and never more than a few open invites per user. The numbers are in
seeds/coins.json.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import random
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.api.errors import ApiError
from app.engine import checks, evaluator, scores
from app.engine.catalog import Catalog
from app.engine.providers import Provider
from app.repo.coins import start_of_today
from app.repo.duels import Duel, DuelsUnavailable, StaleDuel
from app.repo.questions import DEVELOPMENT_STATUSES, SERVABLE_STATUSES
from app.schemas.bank import BankQuestion
from app.services.coins import CoinsService

log = logging.getLogger("app.duels")

MODES = ("quiz", "judged")
BAND_RANK = {"STRONG": 3, "PARTIAL": 2, "WEAK": 1}
MAX_OPEN_INVITES = 3
INVITE_TTL = timedelta(hours=24)                 # an invite nobody accepted is cancelled and refunded on the next read
LOBBY_TTL = timedelta(minutes=10)                # both stakes refunded if the players never become ready
JUDGE_GRACE = timedelta(seconds=120)             # judged: an answer sent in time may still be with the judge past the deadline
CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"   # no 0/o, 1/l/i


def new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


# ---------------------------------------------------------------------- the quiz content


@dataclass(frozen=True)
class QuizQuestion:
    key: str
    topic: str
    status: str                                  # draft | approved: only approved ones enter the pool
    prompt: dict[str, str]
    choices: list[dict[str, str]]
    correct: int
    explanation: dict[str, str]
    source_key: str = ""                         # stable short-question ID; legacy entries use their own key
    variant: int | None = None

    @staticmethod
    def text(values: dict[str, str], language: str) -> str:
        return values.get(language) or values.get("en") or next(iter(values.values()), "")


def load_quiz(path: Path) -> list[QuizQuestion]:
    """The American questions, validated: four options, one correct index, both languages, unique keys."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out, keys, variants = [], set(), set()
    for raw in data.get("questions", []):
        choices = list(raw.get("choices") or [])
        if len(choices) != 4 or not (0 <= int(raw["correct"]) < 4):
            raise ValueError(f"quiz question {raw.get('key')!r} needs four choices and a correct index 0-3")
        for field_name in ("prompt", "explanation"):
            if not raw.get(field_name, {}).get("he") or not raw.get(field_name, {}).get("en"):
                raise ValueError(f"quiz question {raw.get('key')!r} needs {field_name} in both languages")
        if any(not c.get("he") or not c.get("en") for c in choices):
            raise ValueError(f"quiz question {raw.get('key')!r} needs every choice in both languages")
        if raw["key"] in keys:
            raise ValueError(f"duplicate quiz key {raw['key']!r}")
        keys.add(raw["key"])
        source_key = str(raw.get("source_key") or raw["key"])
        variant = raw.get("variant")
        if variant is not None:
            if type(variant) is not int or variant not in range(1, 6) or not raw.get("source_key"):
                raise ValueError(f"quiz question {raw['key']!r} needs a source_key and variant 1-5")
            if (source_key, variant) in variants:
                raise ValueError(f"duplicate quiz variant {(source_key, variant)!r}")
            variants.add((source_key, variant))
        out.append(QuizQuestion(key=raw["key"], topic=raw.get("topic", ""), status=raw.get("status", "draft"),
                                prompt=dict(raw["prompt"]), choices=[dict(c) for c in choices], correct=int(raw["correct"]),
                                explanation=dict(raw["explanation"]), source_key=source_key, variant=variant))
    return out


class DuelService:
    def __init__(self, store, catalog: Catalog, provider: Provider, coins: CoinsService, *, reviewed_only: bool = True,
                 site_url: str = "", quiz: list[QuizQuestion] | None = None, approved_only: bool = True):
        self.store, self.catalog, self.provider, self.coins = store, catalog, provider, coins
        self.rules = coins.rules
        self.reviewed_only = reviewed_only
        self.approved_only = approved_only       # quiz questions still in draft stay out of production duels
        self.quiz = {q.key: q for q in (quiz or [])}
        self.site_url = site_url.rstrip("/")
        self.clock = lambda: datetime.now(UTC)   # tests move it

    # ------------------------------------------------------------------ the pools

    def quiz_pool(self) -> list[QuizQuestion]:
        return [q for q in self.quiz.values() if q.status == "approved" or not self.approved_only]

    def quiz_groups(self) -> dict[str, list[QuizQuestion]]:
        """Equal-weight source questions. New sources need all five reviewed variants; legacy singles still work."""
        groups: dict[str, list[QuizQuestion]] = {}
        for q in self.quiz_pool():
            groups.setdefault(q.source_key or q.key, []).append(q)
        return {key: items for key, items in groups.items()
                if all(q.variant is None for q in items) or {q.variant for q in items} == set(range(1, 6))}

    def quiz_item(self, item: dict) -> QuizQuestion | None:
        """A match keeps its own content version even if the bank is edited or an entry is removed."""
        snapshot = item.get("snapshot")
        return QuizQuestion(**snapshot) if snapshot else self.quiz.get(item["key"])

    def quiz_seconds(self, duel: Duel) -> int:
        return int(duel.meta.get("quiz_seconds_per_question", self.rules.duel_quiz_seconds))

    def pool(self, language: str) -> list[BankQuestion]:
        """Short bank questions a judged duel may ask: by the seed's pool rule (difficulty, formats, subjects), in this
        language. Nothing in the bank takes under three minutes by its own estimate and every live question is
        difficulty 5, so "short" is a format answered in a few sentences: explain, short answer, truth table."""
        rule = self.rules.duel_pool
        max_difficulty = int(rule.get("max_difficulty", 3))
        formats = set(rule.get("formats") or [])
        excluded = set(rule.get("exclude_formats") or [])
        subjects = set(rule.get("subjects") or [])
        out = []
        for q in self.catalog.questions.values():
            if q.status not in (SERVABLE_STATUSES if self.reviewed_only else DEVELOPMENT_STATUSES):
                continue
            if q.difficulty > max_difficulty or q.format in excluded or (formats and q.format not in formats):
                continue
            if subjects and q.subject not in subjects:
                continue
            if language not in q.translations and "en" not in q.translations:
                continue
            # study-only questions (assessment_ready false) are fine here: the judge scores them the same, and a duel
            # never touches the skill profile, which is what that flag protects
            out.append(q)
        return out

    async def _choose(self, tx, language: str, players: list[uuid.UUID]) -> BankQuestion:
        seen: set[str] = set()
        for user_id in players:
            seen |= await tx.seen_question_keys(user_id)
            seen |= await tx.duel_question_keys(user_id)
        candidates = [q for q in self.pool(language) if q.key not in seen]
        if not candidates:
            candidates = [q for q in self.pool(language) if q.key not in await tx.duel_question_keys(players[0])]
        if not candidates:
            raise ApiError("no_reviewed_questions", "no short question is left that neither of you has seen")
        return random.choice(candidates)

    async def _choose_quiz(self, tx, players: list[uuid.UUID]) -> list[QuizQuestion]:
        """Sample distinct sources, then one variant each. Deliberately no exposure-history reads or writes."""
        wanted = self.rules.duel_quiz_questions
        groups = self.quiz_groups()
        if len(groups) < wanted:
            raise ApiError("no_reviewed_questions", "not enough approved quiz questions yet; ask the founders to approve some")
        return [random.choice(groups[key]) for key in random.sample(list(groups), wanted)]

    # ------------------------------------------------------------------ guards

    async def _guard_player(self, tx, user_id: uuid.UUID, *, other: uuid.UUID | None = None) -> None:
        if not await self.coins.enabled(tx):
            raise ApiError("evaluation_unavailable", "duels are not enabled on this server yet", status=503)
        await tx.lock_usage(user_id, "coins")
        await self.coins.ensure_gift(tx, user_id)
        balance = await tx.coin_balance(user_id)
        if balance < self.rules.duel_stake:
            raise ApiError("usage_limit", f"a duel costs {self.rules.duel_stake} coins to enter; you have {balance}", status=402)
        cap = self.rules.duel_daily_earning_cap
        if cap is not None:
            won = await tx.coin_sum_since(user_id, kinds=("payout",), since=start_of_today(), meta_key="net")
            if won >= cap:
                raise ApiError("usage_limit", "you reached today's duel winnings; duels open again tomorrow")
        if self.rules.duel_daily_cap is not None and await tx.duels_accepted_today(user_id) >= self.rules.duel_daily_cap:
            raise ApiError("usage_limit", "today's duels are used up; more tomorrow")
        if other is not None:
            last = await tx.last_duel_between(user_id, other)
            if last is not None and self.clock() - last < timedelta(minutes=self.rules.duel_cooldown_minutes):
                wait = self.rules.duel_cooldown_minutes
                raise ApiError("usage_limit", f"you two just duelled; wait {wait} minutes before the next one")

    # ------------------------------------------------------------------ actions

    async def create(self, user_id: uuid.UUID, *, language: str, mode: str | None = None) -> Duel:
        mode = mode or self.rules.duel_mode_default
        if mode not in MODES:
            raise ApiError("validation", f"unknown duel mode {mode!r}")
        if mode == "quiz" and len(self.quiz_groups()) < self.rules.duel_quiz_questions:
            raise ApiError("no_reviewed_questions", "not enough approved quiz questions yet; ask the founders to approve some")
        async with self.store.transaction() as tx:
            if not await tx.duels_available():
                raise ApiError("evaluation_unavailable", "duels are not enabled on this server yet", status=503)
            await self._guard_player(tx, user_id)
            mine = await tx.list_duels(user_id, limit=50)
            if sum(1 for d in mine if d.status == "open" and d.challenger_id == user_id) >= MAX_OPEN_INVITES:
                raise ApiError("conflict", f"you already have {MAX_OPEN_INVITES} open invites; cancel one first")
            clock = (self.rules.duel_quiz_questions * self.rules.duel_quiz_seconds if mode == "quiz"
                     else self.rules.duel_clock_seconds)
            duel = Duel(id=uuid.uuid4(), code=new_code(), status="open", challenger_id=user_id, opponent_id=None,
                        language=language, stake=self.rules.duel_stake, clock_seconds=clock, mode=mode,
                        created_at=self.clock())
            try:
                await tx.create_duel(duel)
            except DuelsUnavailable as exc:
                raise ApiError("evaluation_unavailable", str(exc), status=503) from exc
            await tx.coin_add(user_id=user_id, delta=-duel.stake, kind="stake", reference=f"duel:{duel.id}:stake:{user_id}",
                              duel_id=duel.id, meta={"role": "challenger", "mode": mode})
        log.info("duel %s (%s) opened by %s", duel.id, mode, user_id)
        return duel

    async def accept(self, user_id: uuid.UUID, code: str) -> Duel:
        async with self.store.transaction() as tx:
            duel = await tx.duel_by_code(code.strip().lower())
            if duel is None:
                raise ApiError("not_found", "no duel with this code")
            await tx.lock_usage(duel.id, "duel")
            duel = await tx.load_duel(duel.id)
            self._expire(duel)
            if duel.status != "open":
                raise ApiError("conflict", "this duel is no longer open")
            if duel.challenger_id == user_id:
                raise ApiError("conflict", "you cannot accept your own duel; send the link to someone else")
            await self._guard_player(tx, user_id, other=duel.challenger_id)
            now = self.clock()
            if duel.mode == "quiz":
                questions = await self._choose_quiz(tx, [duel.challenger_id, user_id])
                duel.items = [{"key": q.key, "snapshot": dataclasses.asdict(q)} for q in questions]
                duel.meta["quiz_seconds_per_question"] = self.rules.duel_quiz_seconds
                for p in (duel.challenger_id, user_id):
                    duel.players[str(p)] = {"ready": False, "answers": []}
            else:
                question = await self._choose(tx, duel.language, [duel.challenger_id, user_id])
                duel.question_key = question.key
            duel.opponent_id, duel.status = user_id, "active"
            duel.accepted_at = now
            duel.deadline = None if duel.mode == "quiz" else now + timedelta(seconds=duel.clock_seconds)
            await tx.coin_add(user_id=user_id, delta=-duel.stake, kind="stake", reference=f"duel:{duel.id}:stake:{user_id}",
                              duel_id=duel.id, meta={"role": "opponent", "mode": duel.mode})
            await self._save(tx, duel)
        log.info("duel %s accepted by %s: %s", duel.id, user_id,
                 duel.question_key or ",".join(i["key"] for i in duel.items))
        return duel

    async def ready(self, user_id: uuid.UUID, duel_id: uuid.UUID) -> Duel:
        """Start only once, under the duel lock, after both players explicitly become ready."""
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=True)
            if duel.mode != "quiz" or duel.status != "active":
                raise ApiError("conflict", "this duel has no waiting room")
            if self._due(duel):
                await self._settle_overdue(tx, duel)
                return duel
            if duel.deadline is not None:
                return duel
            duel.player(user_id)["ready"] = True
            if all(duel.player(p).get("ready") for p in (duel.challenger_id, duel.opponent_id)):
                now = self.clock()
                duel.meta["started_at"] = now.isoformat()
                duel.deadline = now + timedelta(seconds=duel.clock_seconds)
                for p in (duel.challenger_id, duel.opponent_id):
                    duel.player(p)["opened_at"] = now.isoformat()
            await self._save(tx, duel)
        return duel

    async def cancel(self, user_id: uuid.UUID, duel_id: uuid.UUID) -> Duel:
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=True)
            lobby = duel.status == "active" and duel.mode == "quiz" and duel.deadline is None
            if not lobby and (duel.status != "open" or duel.challenger_id != user_id):
                raise ApiError("conflict", "only an open invite or a waiting room can be cancelled")
            await self._close(tx, duel, outcome="cancelled")
        return duel

    async def get(self, user_id: uuid.UUID, duel_id: uuid.UUID) -> Duel:
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=False)
            if self._due(duel) or self._quiz_moves(duel):
                await tx.lock_usage(duel.id, "duel")
                duel = await tx.load_duel(duel.id)
                await self._catch_up(tx, duel)
        return duel

    async def list(self, user_id: uuid.UUID, *, limit: int = 20) -> list[Duel]:
        async with self.store.transaction() as tx:
            duels = await tx.list_duels(user_id, limit=limit)
            for duel in duels:
                if self._due(duel) or self._quiz_moves(duel):
                    await tx.lock_usage(duel.id, "duel")
                    fresh = await tx.load_duel(duel.id)
                    await self._catch_up(tx, fresh)
                    duel.__dict__.update(fresh.__dict__)
        return duels

    async def _catch_up(self, tx, duel: Duel) -> None:
        """What the clock did since the last write: quiz questions that timed out, a duel past its deadline."""
        if duel.status == "active" and duel.mode == "quiz" and duel.deadline is not None:
            changed = [self._advance_quiz(duel, p) for p in (duel.challenger_id, duel.opponent_id)]
            if any(changed) and self._quiz_finished(duel):
                await self._settle(tx, duel)
                return
            if any(changed):
                await self._save(tx, duel)
        if self._due(duel):
            await self._settle_overdue(tx, duel)

    # ------------------------------------------------------------------ answering

    async def answer(self, user_id: uuid.UUID, duel_id: uuid.UUID, text: str | None = None, *,
                     choice: int | None = None, item: int | None = None) -> Duel:
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=True)
            if duel.mode == "quiz":
                return await self._answer_quiz(tx, duel, user_id, choice=choice, item=item)
        return await self._answer_judged(user_id, duel_id, text)

    async def _answer_quiz(self, tx, duel: Duel, user_id: uuid.UUID, *, choice: int | None, item: int | None) -> Duel:
        """One option for the question in front of this player, timed server side; settles when both have finished."""
        if choice is None or not (0 <= int(choice) < 4):
            raise ApiError("validation", "a quiz answer is the index of one of the four options")
        if duel.status != "active":
            raise ApiError("conflict", "this duel is not running")
        if duel.deadline is None:
            raise ApiError("conflict", "both players must be ready before answering")
        now = self.clock()
        self._advance_quiz(duel, user_id)                            # questions that ran out while the screen was idle
        me = duel.player(user_id)
        index = len(me.get("answers", []))
        if index >= len(duel.items):
            raise ApiError("already_submitted", "this duel has no question left for you: answered or timed out")
        if item is not None and int(item) != index:
            raise ApiError("conflict", f"question {index + 1} is the one in front of you now")
        opened = datetime.fromisoformat(me["opened_at"])
        seconds = round((now - opened).total_seconds(), 3)
        question = self.quiz_item(duel.items[index])
        correct = question is not None and int(choice) == question.correct
        me["answers"].append({"choice": int(choice), "correct": correct, "seconds": seconds,
                              "timed_out": False})
        me["opened_at"] = now.isoformat()
        self._finish_quiz_player(duel, me)
        if self._quiz_finished(duel):
            await self._settle(tx, duel)
        else:
            await self._save(tx, duel)
        return duel

    def _advance_quiz(self, duel: Duel, user_id: uuid.UUID) -> bool:
        """Mark the questions this player let run out (one minute each). True when anything changed."""
        me = duel.player(user_id)
        if me.get("status") in ("done", "absent") or "opened_at" not in me:
            return False
        limit = self.quiz_seconds(duel)
        now = self.clock()
        changed = False
        while len(me["answers"]) < len(duel.items):
            opened = datetime.fromisoformat(me["opened_at"])
            if now <= opened + timedelta(seconds=limit):
                break
            me["answers"].append({"choice": None, "correct": False, "seconds": limit, "timed_out": True})
            me["opened_at"] = (opened + timedelta(seconds=limit)).isoformat()
            changed = True
        if self._finish_quiz_player(duel, me):
            changed = True
        return changed

    @staticmethod
    def _finish_quiz_player(duel: Duel, me: dict) -> bool:
        if len(me.get("answers", [])) < len(duel.items) or me.get("status") in ("done", "absent"):
            return False
        answered = [a for a in me["answers"] if not a["timed_out"]]
        me["score"] = sum(1 for a in me["answers"] if a["correct"])
        me["seconds"] = round(sum(a["seconds"] for a in me["answers"]), 3)
        me["status"] = "done" if answered else "absent"               # absent: never pressed anything = a no-show
        return True

    @staticmethod
    def _quiz_finished(duel: Duel) -> bool:
        return all(duel.players.get(str(p), {}).get("status") in ("done", "absent")
                   for p in (duel.challenger_id, duel.opponent_id))

    def _quiz_moves(self, duel: Duel) -> bool:
        """Whether the clock has moved a quiz duel since its last write (so a read must catch up under the lock)."""
        if duel.status != "active" or duel.mode != "quiz":
            return False
        limit = timedelta(seconds=self.quiz_seconds(duel))
        now = self.clock()
        for p in (duel.challenger_id, duel.opponent_id):
            me = duel.players.get(str(p), {})
            if me.get("status") in ("done", "absent") or "opened_at" not in me:
                continue
            if now > datetime.fromisoformat(me["opened_at"]) + limit:
                return True
        return False

    async def _answer_judged(self, user_id: uuid.UUID, duel_id: uuid.UUID, text: str | None) -> Duel:
        """Judge this player's answer (one model call, outside any transaction) and settle when both are in."""
        text = (text or "").strip()
        if not text:
            raise ApiError("validation", "an answer is needed")
        late = False
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=True)
            if duel.status != "active":
                raise ApiError("conflict", "this duel is not running")
            if self.clock() > duel.deadline:
                late = True                       # settled here, raised after the commit (a raise would roll it back)
                if self._due(duel):
                    await self._settle_overdue(tx, duel)
            else:
                me = duel.player(user_id)
                if me.get("submitted_at"):
                    raise ApiError("already_submitted", "you already answered this duel")
                me.update(answer=text, submitted_at=self.clock().isoformat(), status="evaluating")
                await self._save(tx, duel)
        if late:
            raise ApiError("conflict", "the clock ran out before your answer arrived")
        question = self.catalog.questions[duel.question_key]
        try:
            runner = getattr(self, "code_execution", None)
            check = (await runner.check_answer(user_id, f"duel:{duel.id}", question, text) if runner is not None else None)
            if check is None:
                check = (await checks.run_check_async(question.deterministic_check, text) if question.deterministic_check else None)
            result = await evaluator.evaluate(
                self.provider, question_context=evaluator.question_block(question, duel.language, self.catalog.skills.get(question.primary_skill)),
                known_error_keys={e.key for e in question.common_errors}, language=duel.language,
                difficulty=question.difficulty, answer=text, check=check, glossary=self.catalog.glossary)
        except Exception:                                  # noqa: BLE001 - the duel must not stay "evaluating"
            log.exception("judging duel %s for %s failed", duel.id, user_id)
            result = None
        async with self.store.transaction() as tx:
            await tx.lock_usage(duel.id, "duel")
            duel = await tx.load_duel(duel.id)
            me = duel.player(user_id)
            if result is None or not result.ok:
                me.update(status="failed", flags=list(result.flags) if result else ["judge_unavailable"])
                me.pop("submitted_at", None)                # the player may try again while the clock runs
                await self._save(tx, duel)
                judged = False
            else:
                judged = True
                await self._record(tx, duel, user_id, question, result, check)
        if not judged:                                      # raised outside the transaction, so the reset is kept
            raise ApiError("evaluation_unavailable", "the judge could not score your answer; send it again")
        return duel

    async def _record(self, tx, duel: Duel, user_id: uuid.UUID, question: BankQuestion, result, check) -> None:
        """This player's band from the judge's output; settle when both are in."""
        me = duel.player(user_id)
        evaluation = result.evaluation
        core = any(k in question.core_misconception_keys for k in (evaluation.misconceptions or []))
        band = scores.classify_band(evaluation, core).value
        related = scores.related_to_question(evaluation, flags=result.flags)
        me.update(status="done", band=band if related else "WEAK", related=related,
                  summary=evaluation.one_line_summary, flags=list(result.flags), model=result.model,
                  judge_ms=result.latency_ms, check=check.model_dump(mode="json") if check else None,
                  usage=dataclasses.asdict(result.usage))
        if duel.status == "active" and all(duel.players.get(str(p), {}).get("status") == "done"
                                           for p in (duel.challenger_id, duel.opponent_id)):
            await self._settle(tx, duel)
        elif duel.status == "active" and self.clock() > duel.deadline and not any(
                p.get("status") == "evaluating" for p in duel.players.values()):
            await self._settle_overdue(tx, duel)        # the clock ran out while the judge worked: forfeit or settle
        else:
            await self._save(tx, duel)

    # ------------------------------------------------------------------ settling

    def _due(self, duel: Duel) -> bool:
        now = self.clock()
        if duel.status == "open":
            return now - duel.created_at > INVITE_TTL
        if duel.status == "active" and duel.mode == "quiz" and duel.deadline is None:
            return duel.accepted_at is not None and now - duel.accepted_at > LOBBY_TTL
        if duel.status != "active" or duel.deadline is None or now <= duel.deadline:
            return False
        # judged: an answer sent in time may still be with the judge; not a no-show yet (review, 2026-10-22)
        with_judge = duel.mode == "judged" and now <= duel.deadline + JUDGE_GRACE and any(
            p.get("status") == "evaluating" for p in duel.players.values())
        return not with_judge

    def _expire(self, duel: Duel) -> None:
        if duel.status == "open" and self.clock() - duel.created_at > INVITE_TTL:
            duel.status = "cancelled"                 # settled for real by _settle_overdue on the challenger's next read

    async def _settle_overdue(self, tx, duel: Duel) -> None:
        if duel.status == "open":
            await self._close(tx, duel, outcome="expired")
            return
        if duel.status != "active":
            return
        if duel.mode == "quiz" and duel.deadline is None:
            await self._close(tx, duel, outcome="expired")
            return
        if duel.mode == "quiz":
            for p in (duel.challenger_id, duel.opponent_id):
                self._advance_quiz(duel, p)
        done = {p for p in (duel.challenger_id, duel.opponent_id) if duel.players.get(str(p), {}).get("status") == "done"}
        if not done:
            await self._close(tx, duel, outcome="no_show")
        elif len(done) == 1:
            winner = done.pop()
            outcome = "forfeit_opponent" if winner == duel.challenger_id else "forfeit_challenger"
            await self._close(tx, duel, outcome=outcome, winner=winner)
        else:
            await self._settle(tx, duel)

    async def _settle(self, tx, duel: Duel) -> None:
        a, b = duel.challenger_id, duel.opponent_id
        pa, pb = duel.players[str(a)], duel.players[str(b)]
        if duel.mode == "quiz":
            if pa.get("status") == "absent" or pb.get("status") == "absent":
                await self._settle_absent_quiz(tx, duel, pa, pb)
                return
            sa, sb = int(pa.get("score", 0)), int(pb.get("score", 0))
            if sa != sb:
                winner = a if sa > sb else b
            else:
                ta, tb = int(pa.get("seconds", 0)), int(pb.get("seconds", 0))     # whole seconds: a dead heat is a draw
                winner = None if ta == tb else (a if ta < tb else b)
        else:
            ra, rb = BAND_RANK.get(pa.get("band"), 0), BAND_RANK.get(pb.get("band"), 0)
            if ra != rb:
                winner = a if ra > rb else b
            else:
                ta, tb = pa.get("submitted_at"), pb.get("submitted_at")
                winner = None if ta == tb else (a if ta < tb else b)
        if winner is None:
            await self._close(tx, duel, outcome="draw")
        else:
            await self._close(tx, duel, outcome="challenger" if winner == a else "opponent", winner=winner)

    async def _settle_absent_quiz(self, tx, duel: Duel, pa: dict, pb: dict) -> None:
        """A quiz where somebody never pressed anything: the one who played wins; nobody played, both refunded."""
        if pa.get("status") == "absent" and pb.get("status") == "absent":
            await self._close(tx, duel, outcome="no_show")
        elif pa.get("status") == "absent":
            await self._close(tx, duel, outcome="forfeit_challenger", winner=duel.opponent_id)
        else:
            await self._close(tx, duel, outcome="forfeit_opponent", winner=duel.challenger_id)

    async def _close(self, tx, duel: Duel, *, outcome: str, winner: uuid.UUID | None = None) -> None:
        """The money moves exactly once per duel: every row carries the duel's reference."""
        duel.status = "settled" if outcome not in ("cancelled", "expired") else "cancelled"
        duel.outcome, duel.winner_id, duel.settled_at = outcome, winner, self.clock()
        players = [p for p in (duel.challenger_id, duel.opponent_id) if p is not None]
        if winner is not None:
            pot = duel.stake * len(players)
            await tx.coin_add(user_id=winner, delta=pot, kind="payout", reference=f"duel:{duel.id}:payout", duel_id=duel.id,
                              meta={"net": pot - duel.stake, "outcome": outcome, "mode": duel.mode})
        else:
            for p in players:
                await tx.coin_add(user_id=p, delta=duel.stake, kind="refund", reference=f"duel:{duel.id}:refund:{p}",
                                  duel_id=duel.id, meta={"outcome": outcome, "mode": duel.mode})
        await self._save(tx, duel)
        log.info("duel %s closed: %s", duel.id, outcome)

    # ------------------------------------------------------------------ helpers

    async def _own(self, tx, user_id: uuid.UUID, duel_id: uuid.UUID, *, lock: bool) -> Duel:
        if not await tx.duels_available():
            raise ApiError("evaluation_unavailable", "duels are not enabled on this server yet", status=503)
        if lock:
            await tx.lock_usage(duel_id, "duel")
        duel = await tx.load_duel(duel_id)
        if duel is None or not duel.is_player(user_id):
            raise ApiError("not_found", "no such duel")
        return duel

    async def _save(self, tx, duel: Duel) -> None:
        try:
            await tx.save_duel(duel)
        except StaleDuel as exc:
            raise ApiError("conflict", "the duel changed meanwhile; read it again") from exc

    def share_path(self, duel: Duel) -> str:
        return f"/duel/{duel.code}"

    def share_url(self, duel: Duel) -> str:
        return f"{self.site_url}{self.share_path(duel)}" if self.site_url else self.share_path(duel)
