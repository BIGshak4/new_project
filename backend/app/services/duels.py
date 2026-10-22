"""Duels (Shaked, 2026-10-22): two players, five coins each, one short question neither has seen.

The challenger opens a duel and gets an invite code (a link, in Harel's screen). The opponent accepts: both stakes
leave their wallets into the duel (ledger rows of kind "stake"), a question is chosen that neither player has met in
practice or in a duel, and the clock starts (three minutes). Each player answers once; the same judge that scores
practice scores both answers; the better band wins the pot, a tie goes to the faster answer, a tie again refunds both.
A player who never answers forfeits; when nobody answers both are refunded. A duel changes nothing in the skill
profile and earns no XP: it is a game on coins, and coins have no monetary value.

Guards: a ten-minute cooldown per pair of players, a daily ceiling on duel winnings (net), an optional daily duel
count (off until Shaked decides), and never more than a few open invites per user. The numbers are in
seeds/coins.json.
"""

from __future__ import annotations

import dataclasses
import logging
import random
import secrets
import uuid
from datetime import UTC, datetime, timedelta

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

BAND_RANK = {"STRONG": 3, "PARTIAL": 2, "WEAK": 1}
MAX_OPEN_INVITES = 3
INVITE_TTL = timedelta(hours=24)                 # an invite nobody accepted is cancelled and refunded on the next read
CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"   # no 0/o, 1/l/i


def new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


class DuelService:
    def __init__(self, store, catalog: Catalog, provider: Provider, coins: CoinsService, *, reviewed_only: bool = True,
                 site_url: str = ""):
        self.store, self.catalog, self.provider, self.coins = store, catalog, provider, coins
        self.rules = coins.rules
        self.reviewed_only = reviewed_only
        self.site_url = site_url.rstrip("/")
        self.clock = lambda: datetime.now(UTC)   # tests move it

    # ------------------------------------------------------------------ the pool

    def pool(self, language: str) -> list[BankQuestion]:
        """Short questions a duel may ask: by the seed's pool rule (difficulty, formats, subjects), in this language.
        Nothing in the bank takes under three minutes by its own estimate and every live question is difficulty 5, so
        "short" is a format answered in a few sentences: explain, short answer, truth table (seeds/coins.json; the pool
        grows as Harel's short questions reach the bank)."""
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

    async def create(self, user_id: uuid.UUID, *, language: str) -> Duel:
        async with self.store.transaction() as tx:
            if not await tx.duels_available():
                raise ApiError("evaluation_unavailable", "duels are not enabled on this server yet", status=503)
            await self._guard_player(tx, user_id)
            mine = await tx.list_duels(user_id, limit=50)
            if sum(1 for d in mine if d.status == "open" and d.challenger_id == user_id) >= MAX_OPEN_INVITES:
                raise ApiError("conflict", f"you already have {MAX_OPEN_INVITES} open invites; cancel one first")
            duel = Duel(id=uuid.uuid4(), code=new_code(), status="open", challenger_id=user_id, opponent_id=None,
                        language=language, stake=self.rules.duel_stake, clock_seconds=self.rules.duel_clock_seconds,
                        created_at=self.clock())
            try:
                await tx.create_duel(duel)
            except DuelsUnavailable as exc:
                raise ApiError("evaluation_unavailable", str(exc), status=503) from exc
            await tx.coin_add(user_id=user_id, delta=-duel.stake, kind="stake", reference=f"duel:{duel.id}:stake:{user_id}",
                              duel_id=duel.id, meta={"role": "challenger"})
        log.info("duel %s opened by %s", duel.id, user_id)
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
            question = await self._choose(tx, duel.language, [duel.challenger_id, user_id])
            now = self.clock()
            duel.opponent_id, duel.question_key, duel.status = user_id, question.key, "active"
            duel.accepted_at, duel.deadline = now, now + timedelta(seconds=duel.clock_seconds)
            await tx.coin_add(user_id=user_id, delta=-duel.stake, kind="stake", reference=f"duel:{duel.id}:stake:{user_id}",
                              duel_id=duel.id, meta={"role": "opponent"})
            await self._save(tx, duel)
        log.info("duel %s accepted by %s: question %s", duel.id, user_id, duel.question_key)
        return duel

    async def cancel(self, user_id: uuid.UUID, duel_id: uuid.UUID) -> Duel:
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=True)
            if duel.status != "open" or duel.challenger_id != user_id:
                raise ApiError("conflict", "only an open invite of yours can be cancelled")
            await self._close(tx, duel, outcome="cancelled")
        return duel

    async def get(self, user_id: uuid.UUID, duel_id: uuid.UUID) -> Duel:
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=False)
            if self._due(duel):
                await tx.lock_usage(duel.id, "duel")
                duel = await tx.load_duel(duel.id)
                if self._due(duel):
                    await self._settle_overdue(tx, duel)
        return duel

    async def list(self, user_id: uuid.UUID, *, limit: int = 20) -> list[Duel]:
        async with self.store.transaction() as tx:
            duels = await tx.list_duels(user_id, limit=limit)
            for duel in duels:
                if self._due(duel):
                    await tx.lock_usage(duel.id, "duel")
                    fresh = await tx.load_duel(duel.id)
                    if self._due(fresh):
                        await self._settle_overdue(tx, fresh)
                    duel.__dict__.update(fresh.__dict__)
        return duels

    async def answer(self, user_id: uuid.UUID, duel_id: uuid.UUID, text: str) -> Duel:
        """Judge this player's answer (one model call, outside any transaction) and settle when both are in."""
        text = (text or "").strip()
        if not text:
            raise ApiError("validation", "an answer is needed")
        async with self.store.transaction() as tx:
            duel = await self._own(tx, user_id, duel_id, lock=True)
            if duel.status != "active":
                raise ApiError("conflict", "this duel is not running")
            if self.clock() > duel.deadline:
                await self._settle_overdue(tx, duel)
                raise ApiError("conflict", "the clock ran out before your answer arrived")
            me = duel.player(user_id)
            if me.get("submitted_at"):
                raise ApiError("already_submitted", "you already answered this duel")
            me.update(answer=text, submitted_at=self.clock().isoformat(), status="evaluating")
            await self._save(tx, duel)
        question = self.catalog.questions[duel.question_key]
        try:
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
        else:
            await self._save(tx, duel)

    # ------------------------------------------------------------------ settling

    def _due(self, duel: Duel) -> bool:
        now = self.clock()
        return ((duel.status == "active" and duel.deadline is not None and now > duel.deadline)
                or (duel.status == "open" and now - duel.created_at > INVITE_TTL))

    def _expire(self, duel: Duel) -> None:
        if duel.status == "open" and self.clock() - duel.created_at > INVITE_TTL:
            duel.status = "cancelled"                 # settled for real by _settle_overdue on the challenger's next read

    async def _settle_overdue(self, tx, duel: Duel) -> None:
        if duel.status == "open":
            await self._close(tx, duel, outcome="expired")
            return
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

    async def _close(self, tx, duel: Duel, *, outcome: str, winner: uuid.UUID | None = None) -> None:
        """The money moves exactly once per duel: every row carries the duel's reference."""
        duel.status = "settled" if outcome not in ("cancelled", "expired") else "cancelled"
        duel.outcome, duel.winner_id, duel.settled_at = outcome, winner, self.clock()
        players = [p for p in (duel.challenger_id, duel.opponent_id) if p is not None]
        if winner is not None:
            pot = duel.stake * len(players)
            await tx.coin_add(user_id=winner, delta=pot, kind="payout", reference=f"duel:{duel.id}:payout", duel_id=duel.id,
                              meta={"net": pot - duel.stake, "outcome": outcome})
        else:
            for p in players:
                await tx.coin_add(user_id=p, delta=duel.stake, kind="refund", reference=f"duel:{duel.id}:refund:{p}",
                                  duel_id=duel.id, meta={"outcome": outcome})
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
