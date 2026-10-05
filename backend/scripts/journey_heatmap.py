"""Where each pilot user enters questions from, when, and how it goes: a heat-map page per user, from the real
tables, read-only (Shaked, 2026-10-05: "a heat map for each user").

    uv run python scripts/journey_heatmap.py --out workdir/journey.html [--days 60]

Times are shown in Israel time. E-mails are never printed; users are named by their pilot-list name. The page is
plain HTML with inline styles and data, fit for the artifact viewer or any browser.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import sys
from collections import Counter
from datetime import date, timedelta, tzinfo
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.db import dispose, get_engine  # noqa: E402


class _Israel(tzinfo):
    """Israel time without the tz database (Windows machines lack it): UTC+3 from the Friday before the last Sunday of
    March until the last Sunday of October, UTC+2 otherwise."""

    @staticmethod
    def _last_sunday(year: int, month: int) -> date:
        day = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
        return day - timedelta(days=(day.weekday() + 1) % 7)

    def utcoffset(self, dt):
        if dt is None:
            return timedelta(hours=2)
        start = self._last_sunday(dt.year, 3) - timedelta(days=2)
        end = self._last_sunday(dt.year, 10)
        summer = start <= dt.date() < end
        return timedelta(hours=3 if summer else 2)

    def dst(self, dt):
        return self.utcoffset(dt) - timedelta(hours=2)

    def tzname(self, dt):
        return "IDT" if self.dst(dt) else "IST"


def _local_zone() -> tzinfo:
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Jerusalem")
    except Exception:                                   # noqa: BLE001 - no tz database on this machine
        return _Israel()


LOCAL = _local_zone()
WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
TESTERS = {"Shaked Bozi", "Harel Artman", "JobRun"}            # the team's own accounts: shown, marked as testing


async def load(days: int) -> list[dict]:
    engine = get_engine()
    try:
        async with engine.connect() as c:
            await c.execute(text("set transaction read only"))
            cols = [r[0] for r in (await c.execute(text(
                "select column_name from information_schema.columns where table_schema='public' and table_name='attempt_submission'"))).all()]
            vcol = next((col for col in cols if "visual" in col or "image" in col), None)
            visual_sql = f"(s.{vcol} is not null)" if vcol else "false"
            rows = (await c.execute(text(f"""
                select coalesce(m.display_name, p.display_name, 'user') as name, a.id, q.key, q.difficulty, a.mode,
                       a.practice_language as lang, a.started_at, a.plan_item_id, a.hints_used, a.reference_revealed,
                       a.band::text as band, a.follow_up_turns, a.engine_state,
                       (select min(s.accepted_at) from public.attempt_submission s where s.attempt_id = a.id and s.turn = 0) as answered_at,
                       (select bool_or({visual_sql}) from public.attempt_submission s where s.attempt_id = a.id and s.turn = 0) as visual,
                       (select count(*) from public.attempt_submission s where s.attempt_id = a.id and s.turn > 0 and s.status = 'done') as follow_ups_answered,
                       lag(a.engine_state->'next_question'->>'key') over (partition by a.user_id order by a.started_at) as previous_suggestion
                from public.attempt a join public.question q on q.id = a.question_id join auth.users u on u.id = a.user_id
                left join public.user_profile p on p.id = u.id left join public.jr_members m on lower(m.email) = lower(u.email)
                where a.started_at > now() - make_interval(days => :days)
                order by a.user_id, a.started_at"""), {"days": days})).all()
            await c.rollback()
    finally:
        await dispose()
    events = []
    for r in rows:
        stored = (r.engine_state or {}).get("entry") or {}
        if stored.get("source"):
            source, exact = stored["source"], True
        elif r.plan_item_id:
            source, exact = "plan", False
        elif r.previous_suggestion and r.previous_suggestion == r.key:
            source, exact = "suggestion", False
        else:
            source, exact = "library", False
        started = r.started_at.astimezone(LOCAL)
        turns = r.follow_up_turns or []
        events.append({
            "name": r.name, "when": started.strftime("%Y-%m-%d %H:%M"), "hour": started.hour,
            "weekday": (started.weekday() + 1) % 7, "question": r.key, "difficulty": r.difficulty, "mode": r.mode,
            "lang": r.lang, "source": source, "source_exact": exact, "device": stored.get("device"), "screen": stored.get("screen"),
            "answered": r.answered_at is not None,
            "minutes": round((r.answered_at - r.started_at).total_seconds() / 60, 1) if r.answered_at else None,
            "band": r.band, "form": ("photo" if r.visual else "text") if r.answered_at else None,
            "hints": r.hints_used or 0, "reference": bool(r.reference_revealed),
            "follow_ups": len(turns), "follow_ups_answered": r.follow_ups_answered,
            "follow_ups_skipped": sum(1 for t in turns if t.get("skipped_at")),
        })
    return events


def shade(count: int, top: int) -> str:
    if not count:
        return "var(--cell)"
    level = min(1.0, count / max(top, 1))
    return f"color-mix(in oklab, var(--heat) {int(25 + 75 * level)}%, var(--cell))"


def grid(events: list[dict]) -> str:
    counts = Counter((e["weekday"], e["hour"]) for e in events)
    answered = Counter((e["weekday"], e["hour"]) for e in events if e["answered"])
    top = max(counts.values(), default=1)
    cells = ['<div class="grid" role="img" aria-label="Questions opened by weekday and hour">']
    cells.append('<div class="corner"></div>' + "".join(f'<div class="h">{h:02d}</div>' for h in range(24)))
    for d in range(7):
        cells.append(f'<div class="d">{WEEKDAYS[d]}</div>')
        for h in range(24):
            n, a = counts.get((d, h), 0), answered.get((d, h), 0)
            title = f"{WEEKDAYS[d]} {h:02d}:00: {n} opened, {a} answered" if n else ""
            label = (f"{a}/{n}" if n else "")
            cells.append(f'<div class="c" style="background:{shade(n, top)}" title="{title}">{label}</div>')
    cells.append("</div>")
    return "".join(cells)


def bars(pairs: list[tuple[str, int, int]], unit: str) -> str:
    """label, total, answered -> stacked bars; the answered share is the darker part."""
    top = max((t for _, t, _ in pairs), default=1) or 1
    out = ['<div class="bars">']
    for label, total, done in pairs:
        w_total = 100 * total / top
        w_done = 100 * done / top
        out.append(f'<div class="bar"><span class="lbl">{html.escape(label)}</span>'
                   f'<span class="track"><span class="fill total" style="width:{w_total:.0f}%"></span>'
                   f'<span class="fill done" style="width:{w_done:.0f}%"></span></span>'
                   f'<span class="num">{done} of {total} {unit}</span></div>')
    out.append("</div>")
    return "".join(out)


def user_section(name: str, events: list[dict]) -> str:
    answered = [e for e in events if e["answered"]]
    by_source = Counter(e["source"] for e in events)
    done_source = Counter(e["source"] for e in events if e["answered"])
    forms = Counter(e["form"] for e in answered)
    devices = Counter(e["device"] or "unknown" for e in events)
    minutes = sorted(e["minutes"] for e in answered)
    median = minutes[len(minutes) // 2] if minutes else None
    fu_asked = sum(e["follow_ups"] for e in events)
    fu_done = sum(e["follow_ups_answered"] for e in events)
    fu_skipped = sum(e["follow_ups_skipped"] for e in events)
    bands = Counter(e["band"] for e in answered if e["band"])
    exact = any(e["source_exact"] for e in events)
    facts = [
        (f"{len(events)}", "opened"), (f"{len(answered)}", "answered"), (f"{len(events) - len(answered)}", "left unanswered"),
        (f"{median:g} min" if median is not None else "–", "median to answer"),
        (f"{fu_done} of {fu_asked}" if fu_asked else "–", "follow-ups answered"),
        (f"{fu_skipped}", "follow-ups skipped"),
    ]
    facts_html = "".join(f'<div class="fact"><b>{v}</b><span>{k}</span></div>' for v, k in facts)
    source_rows = [(s + ("" if exact else " (inferred)"), by_source[s], done_source.get(s, 0)) for s in sorted(by_source, key=lambda k: -by_source[k])]
    form_rows = [(f or "–", n, n) for f, n in forms.most_common()]
    device_rows = [(d, n, n) for d, n in devices.most_common()]
    band_rows = [(b.lower(), n, n) for b, n in bands.most_common()]
    rows_html = []
    for e in reversed(events):
        if e["answered"]:
            outcome = f"answered in {e['minutes']:g} min, {(e['band'] or 'not graded').lower()}, {e['form'] or ''}"
        else:
            outcome = "<em>left</em>"
        follow = "answered" if e["follow_ups_answered"] else "skipped" if e["follow_ups_skipped"] else "open" if e["follow_ups"] else ""
        device = f" · {e['device']}" if e["device"] else ""
        rows_html.append(f"<tr><td>{e['when']}</td><td>{html.escape(e['question'])}</td><td>d{e['difficulty']} {e['mode']} {e['lang']}</td>"
                         f"<td>{html.escape(e['source'])}{device}</td><td>{outcome}</td><td>{follow}</td></tr>")
    timeline = "".join(rows_html)
    tester = ' <span class="tag">testing account</span>' if name in TESTERS else ""
    return f'''
<section class="user">
  <h2>{html.escape(name)}{tester}</h2>
  <div class="facts">{facts_html}</div>
  <h3>When: questions opened by weekday and hour <span class="muted">(Israel time; answered/opened in each cell)</span></h3>
  <div class="scroll">{grid(events)}</div>
  <div class="two">
    <div><h3>Where from</h3>{bars(source_rows, "answered")}</div>
    <div><h3>How answered</h3>{bars(form_rows, "")}<h3>Device</h3>{bars(device_rows, "")}<h3>Bands</h3>{bars(band_rows, "")}</div>
  </div>
  <h3>Timeline, newest first</h3>
  <div class="scroll"><table><thead><tr><th>When</th><th>Question</th><th>Kind</th><th>From</th><th>Outcome</th><th>Follow-up</th></tr></thead><tbody>{timeline}</tbody></table></div>
</section>'''


def page(events: list[dict], days: int) -> str:
    by_user: dict[str, list[dict]] = {}
    for e in events:
        by_user.setdefault(e["name"], []).append(e)
    order = sorted(by_user, key=lambda n: (n in TESTERS, -len(by_user[n])))
    sections = "".join(user_section(n, by_user[n]) for n in order)
    total = len(events)
    note = ("Where a question was started from is exact when the site passed a source with the start; otherwise it is "
            "inferred: a plan link means the plan, a match with the previous suggestion means the suggested-next card, "
            "anything else counts as the library.")
    return f'''<title>Pilot Journeys</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Frank+Ruhl+Libre:wght@500;700&family=Assistant:wght@400;600&display=swap">
<style>
:root {{ --paper:#f3f5f4; --surface:#ffffff; --ink:#1f2a2e; --muted:#5f6f6d; --line:#d8dfdd; --cell:#e9eeec; --heat:#0f766e;
         --done:#0f766e; --total:#9fc3bf; --tag:#f0e6c8; --tag-ink:#6b4f00; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --paper:#141a1b; --surface:#1d2527; --ink:#e7ecea; --muted:#9fb0ad;
         --line:#2c3739; --cell:#243031; --heat:#2dd4bf; --done:#2dd4bf; --total:#2f5f5a; --tag:#4a3d12; --tag-ink:#f3e3b0; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --paper:#141a1b; --surface:#1d2527; --ink:#e7ecea; --muted:#9fb0ad; --line:#2c3739; --cell:#243031;
         --heat:#2dd4bf; --done:#2dd4bf; --total:#2f5f5a; --tag:#4a3d12; --tag-ink:#f3e3b0; color-scheme: dark; }}
body {{ background:var(--paper); color:var(--ink); font-family: Assistant, "Segoe UI", system-ui, sans-serif; font-size:15px; line-height:1.45;
       padding-inline:16px; padding-block:24px 48px; max-width:1100px; margin:0 auto; }}
h1, h2 {{ font-family: "Frank Ruhl Libre", Georgia, serif; text-wrap: balance; margin:0; }}
h1 {{ font-size:2rem; font-weight:700; }}
h2 {{ font-size:1.45rem; font-weight:500; margin-top:8px; }}
h3 {{ font-size:0.95rem; font-weight:600; margin:18px 0 8px; }}
.lede {{ color:var(--muted); max-width:62ch; margin:6px 0 0; }}
.user {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:18px 20px; margin-top:22px; }}
.facts {{ display:flex; flex-wrap:wrap; gap:18px 28px; margin-top:10px; }}
.fact b {{ display:block; font-size:1.5rem; font-weight:600; font-variant-numeric: tabular-nums; }}
.fact span {{ color:var(--muted); font-size:0.85rem; }}
.tag {{ font-family: Assistant, sans-serif; font-size:0.7rem; font-weight:600; background:var(--tag); color:var(--tag-ink); border-radius:999px; padding:2px 8px; vertical-align:middle; }}
.muted {{ color:var(--muted); font-weight:400; }}
.scroll {{ overflow-x:auto; }}
.grid {{ display:grid; grid-template-columns: 38px repeat(24, 30px); gap:3px; min-width: 780px; font-variant-numeric: tabular-nums; }}
.grid .h, .grid .d {{ font-size:0.7rem; color:var(--muted); display:flex; align-items:center; justify-content:center; }}
.grid .d {{ justify-content:flex-start; }}
.grid .c {{ height:26px; border-radius:4px; font-size:0.68rem; display:flex; align-items:center; justify-content:center; color:var(--ink); }}
.two {{ display:grid; grid-template-columns: 1fr 1fr; gap:0 28px; }}
@media (max-width: 720px) {{ .two {{ grid-template-columns: 1fr; }} }}
.bars {{ display:grid; gap:6px; }}
.bar {{ display:grid; grid-template-columns: 150px 1fr 110px; gap:10px; align-items:center; font-size:0.9rem; }}
.bar .lbl {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.track {{ position:relative; height:12px; background:var(--cell); border-radius:6px; overflow:hidden; display:block; }}
.fill {{ position:absolute; inset:0 auto 0 0; border-radius:6px; }}
.fill.total {{ background:var(--total); }}
.fill.done {{ background:var(--done); }}
.num {{ color:var(--muted); font-size:0.8rem; font-variant-numeric: tabular-nums; text-align:right; }}
table {{ border-collapse:collapse; width:100%; min-width:720px; font-size:0.86rem; }}
th, td {{ text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; }}
em {{ color:var(--muted); }}
.foot {{ color:var(--muted); font-size:0.85rem; margin-top:24px; max-width:70ch; }}
</style>
<h1>Pilot journeys</h1>
<p class="lede">Where each user enters questions from, when they work, how they answer and what they leave. {total} questions opened in the last {days} days. Darker cells are busier hours; the darker part of a bar is what was answered.</p>
{sections}
<p class="foot">{note} Nothing here identifies a user beyond the pilot-list name. Regenerate with <code>scripts/journey_heatmap.py</code>.</p>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--json", help="also write the events as JSON here")
    args = parser.parse_args()
    events = asyncio.run(load(args.days))
    Path(args.out).write_text(page(events, args.days), encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
    users = Counter(e["name"] for e in events)
    print(f"{len(events)} questions by {len(users)} users -> {args.out}")


if __name__ == "__main__":
    main()
