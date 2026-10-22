"""Coins and duels against the REAL database, with zero residue (2026-10-22).

The two migrations are not applied yet, so this runs them inside one transaction on one connection, reflects the
two new tables on that connection, drives the real services through a RollbackStore (savepoints on the same
connection: every unique index, check and cast runs as in production), and rolls the outer transaction back.
Afterwards it proves the tables are gone. Reads two user ids from user_profile (ids only, nothing personal).

    uv run python scripts/verify_coins_duels_db.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))

from livetools import RollbackStore  # noqa: E402

from app import db  # noqa: E402
from app.api.errors import ApiError  # noqa: E402
from app.engine.catalog import load_catalog  # noqa: E402
from app.engine.providers import ScriptedProvider  # noqa: E402
from app.repo.duels import StaleDuel  # noqa: E402
from app.services.coins import CoinsService, load_rules  # noqa: E402
from app.services.duels import DuelService, load_quiz  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = [ROOT.parent / "supabase/migrations/20261022090000_coins.sql",
              ROOT.parent / "supabase/migrations/20261022100000_duels.sql"]
PASSED: list[str] = []


def ok(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise SystemExit(f"FAIL {name} {detail}")
    PASSED.append(name)
    print(f"  ok   {name}")


def statements(sql: str) -> list[str]:
    out, current = [], []
    for line in sql.splitlines():
        stripped = line.split("--")[0] if not line.lstrip().startswith("--") else ""
        if not stripped.strip():
            continue
        current.append(stripped)
        if stripped.rstrip().endswith(";"):
            out.append("\n".join(current))
            current = []
    return out


class Clock:
    def __init__(self):
        self.now = datetime.now(UTC)

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


async def main() -> int:
    engine = db.get_engine()
    async with engine.connect() as connection:
        outer = await connection.begin()
        await connection.execute(text("select 1"))
        for path in MIGRATIONS:
            for statement in statements(path.read_text(encoding="utf-8")):
                await connection.execute(text(statement))
        print("migrations applied inside the transaction")
        metadata = await db.get_metadata()
        await connection.run_sync(lambda sync: metadata.reflect(bind=sync, schema="public", only=["coin_ledger", "duel"]))
        ok("tables visible to the app on this connection", await db.has_table("coin_ledger") and await db.has_table("duel"))
        users = [r[0] for r in (await connection.execute(text("select id from public.user_profile limit 2"))).all()]
        ok("two users to play with", len(users) == 2)
        a, b = users

        store = RollbackStore(connection)
        rules = load_rules(ROOT / "seeds/coins.json")
        catalog = load_catalog(ROOT / "seeds")
        coins = CoinsService(store, rules)
        duels = DuelService(store, catalog, ScriptedProvider(lambda r: "unused"), coins, reviewed_only=False,
                            quiz=load_quiz(ROOT / "seeds/duel_quiz.json"), approved_only=False, site_url="https://site.test")
        clock = Clock()
        duels.clock = clock

        # ---- the ledger
        wallet = await coins.wallet(a)
        ok("gift written once", wallet.balance == 50 and wallet.enabled and [m.kind for m in wallet.movements] == ["gift"])
        ok("gift idempotent across a second service", (await CoinsService(store, rules).wallet(a)).balance == 50)
        attempt = uuid.uuid4()
        async with store.transaction() as tx:
            first = await coins.award_for_answer(tx, user_id=a, attempt_id=attempt, revision=1, band="STRONG", difficulty=5,
                                                 hints_seen=0, reference_seen=False, related=True, turn=0)
            again = await coins.award_for_answer(tx, user_id=a, attempt_id=attempt, revision=1, band="STRONG", difficulty=5,
                                                 hints_seen=0, reference_seen=False, related=True, turn=0)
        ok("hard strong answer pays 20 once (partial unique index + on conflict)", (first, again) == (20, 0))
        ok("balance after", (await coins.wallet(a)).balance == 70)
        try:
            await coins.buy(a, "extra_questions_10")
            ok("buy refused when short", False)
        except ApiError as exc:
            ok("buy refused when short (402)", exc.status == 402)
        async with store.transaction() as tx:
            for n in range(3):
                await tx.coin_add(user_id=a, delta=10, kind="earn", reference=f"answer:{uuid.uuid4()}:{n}")
        bought = await coins.buy(a, "extra_questions_10")
        ok("buy: balance 0, top-up 10 (jsonb meta cast)", bought.balance == 0 and bought.extra_questions_today == 10)
        ok("extra_questions_today reads 10", await coins.extra_questions_today(a) == 10)
        ok("movements newest first", bought.movements[0].kind == "spend" and bought.movements[-1].kind == "gift")
        async with store.transaction() as tx:
            stale = await tx.coin_add(user_id=a, delta=-100, kind="spend", reference="buy:old", item="extra_questions_10",
                                      meta={"extra_questions_today": 10})
        await connection.execute(text("update public.coin_ledger set created_at = now() - interval '1 day 1 hour' where reference = 'buy:old'"))
        ok("yesterday's top-up does not count", stale and await coins.extra_questions_today(a) == 10)
        try:
            async with store.transaction() as tx:
                await tx.coin_add(user_id=a, delta=0, kind="earn", reference="zero")
            ok("delta 0 refused by the check", False)
        except Exception:
            ok("delta 0 refused by the check", True)
        try:
            async with store.transaction() as tx:
                await tx.coin_add(user_id=a, delta=1, kind="bonus", reference="bad-kind")
            ok("unknown kind refused by the check", False)
        except Exception:
            ok("unknown kind refused by the check", True)

        # ---- a quiz duel, both players, settled by score
        async with store.transaction() as tx:                       # the script's own back-dated spend above is repaid
            await tx.coin_add(user_id=a, delta=150, kind="earn", reference="top-up-for-duels")
        invite = await duels.create(a, language="he")
        ok("quiz invite open, stake taken", invite.status == "open" and invite.mode == "quiz" and (await coins.wallet(a)).balance == 45)
        duel = await duels.accept(b, invite.code)
        ok("accepted: five items, deadline 300 s, both staked", duel.status == "active" and len(duel.items) == 5
           and duel.deadline == clock.now + timedelta(seconds=300) and (await coins.wallet(b)).balance == 45)
        loaded = await duels.get(a, duel.id)
        ok("jsonb round trip: items and players", [i["key"] for i in loaded.items] == [i["key"] for i in duel.items]
           and loaded.players[str(a)]["opened_at"] == duel.players[str(a)]["opened_at"])
        corrects = [duels.quiz[i["key"]].correct for i in duel.items]
        for i, c in enumerate(corrects):
            clock.advance(4)
            await duels.answer(a, duel.id, choice=c, item=i)
        for i, c in enumerate(corrects):
            clock.advance(3)
            settled = await duels.answer(b, duel.id, choice=(c + 1) % 4 if i else c, item=i)
        ok("settled: challenger 5, opponent 1", settled.status == "settled" and settled.outcome == "challenger"
           and settled.player(a)["score"] == 5 and settled.player(b)["score"] == 1)
        ok("payout once, balances 55/45", (await coins.wallet(a)).balance == 55 and (await coins.wallet(b)).balance == 45)
        rows = (await connection.execute(text("select kind, delta from public.coin_ledger where duel_id = :d order by created_at"),
                                         {"d": duel.id})).all()
        ok("ledger rows for the duel: stake, stake, payout", [r[0] for r in rows] == ["stake", "stake", "payout"] and [r[1] for r in rows] == [-5, -5, 10])
        async with store.transaction() as tx:
            ok("duel_question_keys reads the items", {i["key"] for i in duel.items} <= await tx.duel_question_keys(a))
            ok("last_between / accepted_today", await tx.last_duel_between(a, b) == duel.accepted_at and await tx.duels_accepted_today(a) == 1)
            ok("today's winnings meta net", await tx.coin_sum_since(a, kinds=("payout",), since=clock.now - timedelta(hours=1), meta_key="net") == 5)
        again = await duels.get(b, duel.id)
        ok("a second read moves nothing", again.version == settled.version and (await coins.wallet(a)).balance == 55)

        # ---- optimistic version
        async with store.transaction() as tx:
            fresh = await tx.load_duel(duel.id)
            copy = await tx.load_duel(duel.id)
            fresh.meta["x"] = 1
            await tx.save_duel(fresh)
            try:
                copy.meta["y"] = 2
                await tx.save_duel(copy)
                ok("stale save refused", False)
            except StaleDuel:
                ok("stale save refused (version)", True)

        # ---- cooldown, a no-show, an expired invite, a judged invite cancelled
        try:
            inv2 = await duels.create(a, language="he")
            await duels.accept(b, inv2.code)
            ok("cooldown refuses the pair", False)
        except ApiError as exc:
            ok("cooldown refuses the pair (429)", exc.code == "usage_limit" and exc.status == 429)
        clock.advance(11 * 60)
        d2 = await duels.accept(b, inv2.code)
        clock.advance(6 * 60)
        listed = await duels.list(b)
        ok("nobody pressed anything: no_show, both refunded", listed[0].id == d2.id and listed[0].outcome == "no_show"
           and (await coins.wallet(a)).balance == 55 and (await coins.wallet(b)).balance == 45)
        judged = await duels.create(a, language="en", mode="judged")
        cancelled = await duels.cancel(a, judged.id)
        ok("judged invite cancelled and refunded", cancelled.outcome == "cancelled" and (await coins.wallet(a)).balance == 55)
        old = await duels.create(a, language="en")
        clock.advance(25 * 3600)
        try:
            await duels.accept(b, old.code)
            ok("expired invite refused", False)
        except ApiError as exc:
            ok("expired invite refused", exc.code == "conflict")
        seen = await duels.get(a, old.id)
        ok("expired invite refunded on read", seen.outcome == "expired" and (await coins.wallet(a)).balance == 55)

        # ---- RLS: the browser reads its own rows only, nothing on duel
        await connection.execute(text("select set_config('request.jwt.claims', :c, true)"),
                                 {"c": f'{{"sub": "{a}", "role": "authenticated", "aud": "authenticated"}}'})
        await connection.execute(text("set local role authenticated"))
        mine = (await connection.execute(text("select count(*) from public.coin_ledger"))).scalar_one()
        total_a = (await connection.execute(text("select count(*) from public.coin_ledger where user_id = :u"), {"u": a})).scalar_one()
        ok("RLS: the user sees only their own ledger rows", mine == total_a and mine > 0)
        try:
            await connection.execute(text("select count(*) from public.duel"))
            ok("RLS: duel is closed to the browser", False)
        except Exception:
            ok("RLS: duel is closed to the browser", True)
        await outer.rollback()
    async with engine.connect() as connection:
        gone = (await connection.execute(text("select to_regclass('public.coin_ledger') is null and to_regclass('public.duel') is null"))).scalar_one()
        ok("rolled back: no table left behind", bool(gone))
    await db.dispose()
    print(f"all {len(PASSED)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
