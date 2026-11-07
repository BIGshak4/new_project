"""Coins: a spendable currency next to XP (Shaked, 2026-10-22).

Earned by strong answers (10, 20 for a hard question, 10 per strong interview turn), given once as a starting gift
(50), spent in the shop (today's first item: ten more questions for 100) and staked in duels (5 each). XP is untouched:
it is recomputed on read and never spent; coins live in a ledger. Coins have no monetary value, cannot be bought and
cannot be cashed out — that line is what keeps a duel a game and not gambling; it is in the API's text as well.
The numbers come from seeds/coins.json.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.api.errors import ApiError
from app.repo.coins import CoinsUnavailable, Movement, start_of_today

log = logging.getLogger("app.coins")


@dataclass
class ShopItem:
    key: str
    label: dict[str, str]
    description: dict[str, str]
    price: int
    effect: dict

    def text(self, field_name: str, language: str) -> str:
        values = getattr(self, field_name)
        return values.get(language) or values.get("en") or next(iter(values.values()), "")


@dataclass
class CoinRules:
    starting_gift: int = 50
    strong_answer: int = 10
    strong_hard_answer: int = 20
    hard_difficulty_from: int = 5
    strong_interview_turn: int = 10
    max_hints_for_coins: int = 1
    interview_finished: int = 15                # for finishing an interview, whatever the result (Shaked, 2026-11-02)
    interview_finished_min_turns: int = 3       # ...once at least this many questions were answered
    duel_stake: int = 5
    duel_mode_default: str = "quiz"             # quiz (American questions) | judged (one bank question)
    duel_quiz_questions: int = 5
    duel_quiz_seconds: int = 60                 # per question, at most
    duel_clock_seconds: int = 180               # the judged mode's clock
    duel_cooldown_minutes: int = 10
    duel_daily_earning_cap: int | None = 100    # coins WON in duels per day (each win counts its net gain, 5)
    duel_daily_cap: int | None = None
    duel_pool: dict = field(default_factory=dict)
    shop: list[ShopItem] = field(default_factory=list)


def load_rules(path: Path) -> CoinRules:
    data = json.loads(path.read_text(encoding="utf-8"))
    duel = data.get("duel") or {}
    if duel.get("mode_default", "quiz") not in ("quiz", "judged"):
        raise ValueError(f"coins.json: duel.mode_default must be quiz or judged, not {duel.get('mode_default')!r}")
    return CoinRules(starting_gift=int(data.get("starting_gift", 50)), strong_answer=int(data.get("strong_answer", 10)),
                     strong_hard_answer=int(data.get("strong_hard_answer", 20)),
                     hard_difficulty_from=int(data.get("hard_difficulty_from", 5)),
                     strong_interview_turn=int(data.get("strong_interview_turn", 10)),
                     max_hints_for_coins=int(data.get("max_hints_for_coins", 1)),
                     interview_finished=int(data.get("interview_finished", 15)),
                     interview_finished_min_turns=int(data.get("interview_finished_min_turns", 3)),
                     duel_stake=int(duel.get("stake", 5)), duel_clock_seconds=int(duel.get("clock_seconds", 180)),
                     duel_mode_default=str(duel.get("mode_default", "quiz")),
                     duel_quiz_questions=int((duel.get("quiz") or {}).get("questions", 5)),
                     duel_quiz_seconds=int((duel.get("quiz") or {}).get("seconds_per_question", 60)),
                     duel_cooldown_minutes=int(duel.get("cooldown_minutes", 10)),
                     duel_daily_earning_cap=duel.get("daily_earning_cap", 100), duel_daily_cap=duel.get("daily_cap"),
                     duel_pool=dict(duel.get("pool") or {}),
                     shop=[ShopItem(key=i["key"], label=i["label"], description=i.get("description", {}), price=int(i["price"]),
                                    effect=dict(i.get("effect") or {})) for i in data.get("shop", [])])


def coins_for_answer(rules: CoinRules, *, band: str | None, difficulty: int, hints_seen: int = 0, reference_seen: bool = False,
                     related: bool = True, turn: int = 0) -> int:
    """The pure rule: a strong main answer earns, within the hint allowance, with the reference unseen, on topic."""
    if band != "STRONG" or turn != 0 or reference_seen or not related or hints_seen > rules.max_hints_for_coins:
        return 0
    return rules.strong_hard_answer if difficulty >= rules.hard_difficulty_from else rules.strong_answer


def coins_for_turn(rules: CoinRules, *, band: str | None, hints_seen: int = 0, related: bool = True) -> int:
    if band != "STRONG" or not related or hints_seen > rules.max_hints_for_coins:
        return 0
    return rules.strong_interview_turn


def coins_for_finish(rules: CoinRules, *, answered_turns: int) -> int:
    """Finishing an interview earns, whatever the bands, once enough questions were answered: the effort counts
    (Shaked, 2026-11-02, "i want him to try more"). Start-and-quit earns nothing."""
    return rules.interview_finished if answered_turns >= rules.interview_finished_min_turns else 0


@dataclass
class Wallet:
    balance: int
    earned_today: int
    movements: list[Movement]
    extra_questions_today: int
    rules: CoinRules
    enabled: bool


class CoinsService:
    def __init__(self, store, rules: CoinRules):
        self.store, self.rules = store, rules
        self._gifted: set[uuid.UUID] = set()           # users whose gift was written (or found) in this process
        self.known_enabled: bool | None = None         # whether the ledger table exists, once a transaction looked

    # ------------------------------------------------------------------ reading

    async def enabled(self, tx) -> bool:
        self.known_enabled = bool(await tx.coins_available())
        return self.known_enabled

    async def ensure_gift(self, tx, user_id: uuid.UUID) -> bool:
        """The starting gift, written once per user (idempotent by its reference)."""
        if user_id in self._gifted or not await self.enabled(tx):
            return False
        written = await tx.coin_add(user_id=user_id, delta=self.rules.starting_gift, kind="gift", reference="gift",
                                    meta={"note": "starting gift"})
        if not written:                     # found: certainly committed. A write is only remembered once the next
            self._gifted.add(user_id)       # transaction finds it (this one may still roll back after us)
        if len(self._gifted) > 50_000:
            self._gifted.clear()
        return written

    async def wallet(self, user_id: uuid.UUID) -> Wallet:
        async with self.store.transaction() as tx:
            enabled = await self.enabled(tx)
            if enabled:
                await self.ensure_gift(tx, user_id)
            balance = await tx.coin_balance(user_id)
            movements = await tx.coin_movements(user_id, limit=20)
            earned_today = await tx.coin_sum_since(user_id, kinds=("earn", "payout", "gift"), since=start_of_today())  # received today
            extra = await tx.coin_sum_since(user_id, kinds=("spend",), since=start_of_today(), meta_key="extra_questions_today")
        return Wallet(balance=balance, earned_today=earned_today, movements=movements, extra_questions_today=extra,
                      rules=self.rules, enabled=enabled)

    async def extra_questions_today(self, user_id: uuid.UUID) -> int:
        """What the shop added to today's cap (the practice service adds it to the plan's limit)."""
        async with self.store.transaction() as tx:
            if not await self.enabled(tx):
                return 0
            return await tx.coin_sum_since(user_id, kinds=("spend",), since=start_of_today(), meta_key="extra_questions_today")

    # ------------------------------------------------------------------ earning (inside the caller's transaction)

    @staticmethod
    def question_reference(question_id) -> str:
        """One earn per user per question (Shaked, 2026-11-06: "not if he got on the same question a strong answer"):
        practice answers and interview turns share this reference, so whichever comes first pays, once."""
        return f"question:{question_id}"

    async def award_for_answer(self, tx, *, user_id: uuid.UUID, attempt_id: uuid.UUID, revision: int, band: str | None,
                               difficulty: int, hints_seen: int, reference_seen: bool, related: bool, turn: int,
                               question_id=None) -> int:
        """The coins this answer earned and wrote: 0 when the rule gives nothing, and 0 when this user already earned
        on this question (any attempt, or an interview turn). The caller stores the amount on the answer."""
        amount = coins_for_answer(self.rules, band=band, difficulty=difficulty, hints_seen=hints_seen,
                                  reference_seen=reference_seen, related=related, turn=turn)
        if not await self.enabled(tx) or amount <= 0:        # look at the ledger first: the views promise only after
            return 0
        reference = self.question_reference(question_id) if question_id is not None else f"answer:{attempt_id}:{revision}"
        return await self._award(tx, user_id, amount, reference=reference,
                                 meta={"band": band, "difficulty": difficulty, "attempt_id": str(attempt_id), "revision": revision})

    async def _award(self, tx, user_id: uuid.UUID, amount: int, *, reference: str, meta: dict) -> int:
        """The earn row in a savepoint: a ledger error is logged and the caller's transaction (the answer, the
        interview turn) commits regardless (review finding, 2026-10-22). The reference keeps a retry from paying twice."""
        try:
            async with tx.savepoint():
                await self.ensure_gift(tx, user_id)
                written = await tx.coin_add(user_id=user_id, delta=amount, kind="earn", reference=reference, meta=meta)
        except Exception:                                   # noqa: BLE001 - coins must never cost an answer
            log.exception("coins: awarding %s for %s failed; the answer is saved without it", reference, user_id)
            return 0
        return amount if written else 0

    async def award_for_turn(self, tx, *, user_id: uuid.UUID, session_id: uuid.UUID, turn_index: int, band: str | None,
                             hints_seen: int = 0, related: bool = True, question_id=None) -> int:
        amount = coins_for_turn(self.rules, band=band, hints_seen=hints_seen, related=related)
        if not await self.enabled(tx) or amount <= 0:        # look at the ledger first: the views promise only after
            return 0
        reference = self.question_reference(question_id) if question_id is not None else f"turn:{session_id}:{turn_index}"
        return await self._award(tx, user_id, amount, reference=reference,
                                 meta={"band": band, "interview": True, "session_id": str(session_id), "turn": turn_index})

    async def balance(self, user_id: uuid.UUID) -> int | None:
        """The balance alone, for the header of every screen (Shaked, 2026-11-06: "coins shown all the time");
        None when coins are not enabled on this database. A first look still writes the starting gift."""
        async with self.store.transaction() as tx:
            if not await self.enabled(tx):
                return None
            await self.ensure_gift(tx, user_id)
            return await tx.coin_balance(user_id)

    async def award_for_finish(self, tx, *, user_id: uuid.UUID, session_id: uuid.UUID, answered_turns: int) -> int:
        """Once per interview (the reference dedups a re-save): coins for finishing, not for the score."""
        amount = coins_for_finish(self.rules, answered_turns=answered_turns)
        if not await self.enabled(tx) or amount <= 0:
            return 0
        return await self._award(tx, user_id, amount, reference=f"interview:{session_id}:finished",
                                 meta={"interview": True, "finished": True, "answered_turns": answered_turns})

    # ------------------------------------------------------------------ spending

    def item(self, key: str) -> ShopItem:
        for item in self.rules.shop:
            if item.key == key:
                return item
        raise ApiError("validation", f"unknown shop item {key!r}")

    async def buy(self, user_id: uuid.UUID, item_key: str) -> Wallet:
        item = self.item(item_key)
        async with self.store.transaction() as tx:
            if not await self.enabled(tx):
                raise ApiError("evaluation_unavailable", "coins are not enabled on this server yet", status=503)
            await tx.lock_usage(user_id, "coins")                      # one purchase at a time per user
            await self.ensure_gift(tx, user_id)
            balance = await tx.coin_balance(user_id)
            if balance < item.price:
                raise ApiError("usage_limit", f"not enough coins: this costs {item.price}, you have {balance}", status=402)
            reference = f"buy:{item.key}:{uuid.uuid4()}"
            try:
                await tx.coin_add(user_id=user_id, delta=-item.price, kind="spend", reference=reference, item=item.key,
                                  meta=dict(item.effect))
            except CoinsUnavailable as exc:
                raise ApiError("evaluation_unavailable", str(exc), status=503) from exc
        log.info("coins: %s bought %s for %d", user_id, item.key, item.price)
        return await self.wallet(user_id)
