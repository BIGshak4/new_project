"""What the model calls cost and how long they take, from the real `usage_event` table, read-only (Shaked,
2026-11-14: "check what is the cost and the answer time").

    uv run python scripts/cost_report.py [--days 30] [--usd-to-ils 3.7] [--monthly-budget-ils 15]

Prints, for the window: every kind of call (count, total and average cost, median and 95th-percentile time, tokens
and the cached share), the cost of one practice attempt and of one mock interview from start to finish, the spend per
day, and each user's spend per calendar month next to the budget. Users are numbered, never named; nothing is written.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.db import dispose, get_engine  # noqa: E402

CALLS = """
select action, coalesce(model, '-') as model, coalesce(mode::text, '-') as mode, count(*) as n,
       sum(cost_usd) as cost, avg(cost_usd) as avg_cost,
       percentile_cont(0.5) within group (order by latency_ms) as p50, percentile_cont(0.95) within group (order by latency_ms) as p95,
       avg(tokens_in) as tokens_in, avg(tokens_out) as tokens_out, avg(cache_read_tokens) as cached
from usage_event where created_at >= now() - make_interval(days => :days)
group by 1, 2, 3 order by sum(cost_usd) desc, count(*) desc"""

PER_UNIT = """
with unit as (
  select {column} as id, sum(cost_usd) as cost, count(*) as calls,
         sum(latency_ms) filter (where action = 'evaluate') as judge_ms, count(*) filter (where action = 'evaluate') as judged
  from usage_event where created_at >= now() - make_interval(days => :days) and {column} is not null {extra}
  group by 1 having sum(cost_usd) > 0)
select count(*) as n, avg(cost) as avg, percentile_cont(0.5) within group (order by cost) as p50,
       percentile_cont(0.95) within group (order by cost) as p95, max(cost) as max, avg(calls) as calls,
       avg(judged) as judged from unit"""

PER_DAY = """
select date_trunc('day', created_at)::date as day, count(*) as n, sum(cost_usd) as cost,
       count(distinct user_id) as users, count(distinct attempt_id) as attempts, count(distinct session_id) as interviews
from usage_event where created_at >= now() - make_interval(days => :days) group by 1 order by 1"""

PER_USER_MONTH = """
select to_char(date_trunc('month', created_at), 'YYYY-MM') as month, user_id, sum(cost_usd) as cost, count(*) as calls,
       count(distinct attempt_id) as attempts, count(distinct session_id) as interviews,
       count(distinct date_trunc('day', created_at)) as days
from usage_event where user_id is not null and created_at >= now() - make_interval(days => :days)
group by 1, 2 order by 1 desc, sum(cost_usd) desc"""

JUDGE_BY_WEEK = """
select to_char(date_trunc('week', created_at), 'YYYY-MM-DD') as week, coalesce(model, '-') as model, count(*) as n,
       percentile_cont(0.5) within group (order by latency_ms) as p50, percentile_cont(0.95) within group (order by latency_ms) as p95,
       avg(cost_usd) as avg_cost
from usage_event where action = 'evaluate' and latency_ms is not null and created_at >= now() - make_interval(days => :days)
group by 1, 2 order by 1, 2"""


def money(value) -> str:
    return "-" if value is None else f"${float(value):.4f}"


def ms(value) -> str:
    return "-" if value is None else f"{float(value) / 1000:.1f} s"


async def report(days: int, usd_to_ils: float, budget_ils: float) -> None:
    engine = get_engine()
    try:
        async with engine.connect() as c:
            await c.execute(text("set transaction read only"))
            calls = (await c.execute(text(CALLS), {"days": days})).mappings().all()
            attempt = (await c.execute(text(PER_UNIT.format(column="attempt_id", extra="and session_id is null")),
                                       {"days": days})).mappings().one()
            interview = (await c.execute(text(PER_UNIT.format(column="session_id", extra="")), {"days": days})).mappings().one()
            per_day = (await c.execute(text(PER_DAY), {"days": days})).mappings().all()
            per_user = (await c.execute(text(PER_USER_MONTH), {"days": days})).mappings().all()
            judge = (await c.execute(text(JUDGE_BY_WEEK), {"days": days})).mappings().all()
    finally:
        await dispose()

    total = sum(float(r["cost"] or 0) for r in calls)
    print(f"# Model calls in the last {days} days: {sum(r['n'] for r in calls)} calls, ${total:.2f} "
          f"(₪{total * usd_to_ils:.2f} at {usd_to_ils})\n")
    print("| call | model | mode | calls | total | each | median time | 95% time | tokens in | cached | tokens out |")
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in calls:
        cached = (float(r["cached"] or 0) / float(r["tokens_in"])) if r["tokens_in"] else 0.0
        print(f"| {r['action']} | {r['model']} | {r['mode']} | {r['n']} | {money(r['cost'])} | {money(r['avg_cost'])} | "
              f"{ms(r['p50'])} | {ms(r['p95'])} | {float(r['tokens_in'] or 0):.0f} | {cached:.0%} | {float(r['tokens_out'] or 0):.0f} |")

    print("\n## One practice attempt and one mock interview, all their calls together\n")
    print("| unit | counted | average | median | 95% | highest | calls each | judged answers each |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, r in (("practice attempt", attempt), ("mock interview", interview)):
        if not r["n"]:
            print(f"| {name} | 0 | - | - | - | - | - | - |")
            continue
        print(f"| {name} | {r['n']} | {money(r['avg'])} | {money(r['p50'])} | {money(r['p95'])} | {money(r['max'])} | "
              f"{float(r['calls']):.1f} | {float(r['judged'] or 0):.1f} |")

    print("\n## The judge's time, week by week\n")
    print("| week of | model | answers judged | median | 95% | cost each |")
    print("|---|---|---:|---:|---:|---:|")
    for r in judge:
        print(f"| {r['week']} | {r['model']} | {r['n']} | {ms(r['p50'])} | {ms(r['p95'])} | {money(r['avg_cost'])} |")

    print("\n## Spend per day\n")
    print("| day | calls | cost | users | attempts | interviews |")
    print("|---|---:|---:|---:|---:|---:|")
    for r in per_day:
        print(f"| {r['day']} | {r['n']} | {money(r['cost'])} | {r['users']} | {r['attempts']} | {r['interviews']} |")

    print(f"\n## Each user's spend per calendar month (budget ₪{budget_ils:g} = ${budget_ils / usd_to_ils:.2f})\n")
    print("| month | user | cost | in shekels | of budget | calls | attempts | interviews | active days |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    numbers: dict[str, int] = {}
    for r in per_user:
        user = numbers.setdefault(str(r["user_id"]), len(numbers) + 1)
        ils = float(r["cost"] or 0) * usd_to_ils
        print(f"| {r['month']} | #{user} | {money(r['cost'])} | ₪{ils:.2f} | {ils / budget_ils:.0%} | {r['calls']} | "
              f"{r['attempts']} | {r['interviews']} | {r['days']} |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--usd-to-ils", type=float, default=3.7)
    parser.add_argument("--monthly-budget-ils", type=float, default=15.0)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(report(args.days, args.usd_to_ils, args.monthly_budget_ils))


if __name__ == "__main__":
    main()
